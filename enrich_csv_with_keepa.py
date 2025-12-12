#!/usr/bin/env python3
"""
Script to enrich CSV file with Keepa API data.
Iterates through CSV, calls Keepa API for each row using the Index column value,
and adds EAN and ASIN columns.
"""

import csv
import asyncio
import httpx
import os
import sys
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Keepa API configuration
KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")
KEEPA_BASE_URL = "https://api.keepa.com"


async def call_keepa_search(term: str) -> Optional[list]:
    """Call Keepa search API with a search term.
    
    Returns list of all products found, not just the first one.
    """
    if not KEEPA_API_KEY:
        print("ERROR: KEEPA_API_KEY not found in environment variables")
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            url = f"{KEEPA_BASE_URL}/search"
            params = {
                "key": KEEPA_API_KEY,
                "domain": 1,
                "type": "product",
                "term": term
            }
            
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("products") and len(data["products"]) > 0:
                return data["products"]  # Return all products
            else:
                print(f"  ⚠️  No products found for term: {term}")
                return None
                
    except httpx.HTTPStatusError as e:
        print(f"  ❌ HTTP error for term '{term}': {e.response.status_code} - {e.response.text[:200]}")
        return None
    except Exception as e:
        print(f"  ❌ Error calling Keepa API for term '{term}': {e}")
        return None


def extract_model_number(index_value: str) -> str:
    """Extract model number from Index column value.
    
    Example: "3MD30090914 M 8.5" -> "3MD30090914"
    """
    if not index_value:
        return ""
    
    # Split by space and take the first part (model number)
    parts = index_value.strip().split()
    if parts:
        return parts[0]
    return index_value.strip()


def extract_size_from_index(index_value: str) -> Optional[str]:
    """Extract size from Index column value.
    
    Example: "3MD30090914 M 8.5" -> "8.5"
    Example: "3MD30091197 M 9" -> "9"
    """
    if not index_value:
        return None
    
    parts = index_value.strip().split()
    if len(parts) >= 3:
        # Format: "MODEL GENDER SIZE" - size is the last part
        return parts[-1]
    return None


def extract_gender_from_index(index_value: str) -> Optional[str]:
    """Extract gender from Index column value.
    
    Example: "3MD30090914 M 8.5" -> "M"
    Example: "3WD30090914 W 6" -> "W"
    """
    if not index_value:
        return None
    
    parts = index_value.strip().split()
    if len(parts) >= 2:
        # Format: "MODEL GENDER SIZE" - gender is the second part
        return parts[1]
    return None


def match_product_by_size(products: list, target_size: Optional[str], target_gender: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Match a product from the list based on size and optionally gender.
    
    Checks product variations and size field to find matching product.
    Returns the product (or variation) that matches the target size.
    """
    if not products or not target_size:
        return None
    
    # Normalize target size (remove any extra formatting)
    target_size_clean = target_size.strip().lower()
    
    for product in products:
        # First, check if this product itself matches the size
        product_size = product.get("size", "")
        if product_size and str(product_size).strip().lower() == target_size_clean:
            # Size matches, check gender if provided
            if target_gender:
                title = product.get("title", "").upper()
                # Check if gender is in title (M/W) or in the index value
                if target_gender.upper() in title or (target_gender.upper() == "M" and "MEN" in title) or (target_gender.upper() == "W" and ("WOMEN" in title or "WOMAN" in title)):
                    return product
            else:
                return product
        
        # Check variations for size match
        # Variations contain child ASINs with different sizes/colors
        variations = product.get("variations", [])
        if variations:
            for variation in variations:
                if not isinstance(variation, dict):
                    continue
                
                # Check variation attributes for size match
                attributes = variation.get("attributes", [])
                size_match = False
                gender_match = True  # Default to True if no gender specified
                
                for attr in attributes:
                    if not isinstance(attr, dict):
                        continue
                    
                    dimension = attr.get("dimension", "").lower()
                    value = attr.get("value", "")
                    
                    if dimension == "size":
                        if str(value).strip().lower() == target_size_clean:
                            size_match = True
                    
                    # Check gender match if provided
                    if target_gender and dimension in ["color", "style"]:
                        # Gender might be in the title or we can infer from model number
                        # For now, we'll be lenient with gender matching
                        pass
                
                # If size matches, we found our variation
                # Note: We return the parent product, but the variation ASIN is in variation["asin"]
                if size_match:
                    # Create a modified product dict with the variation ASIN
                    matched_product = product.copy()
                    variation_asin = variation.get("asin")
                    if variation_asin:
                        matched_product["asin"] = variation_asin
                        matched_product["matched_variation"] = variation
                        matched_product["_is_variation_match"] = True
                    return matched_product
        
        # Check variationCSV - this contains comma-separated ASINs of variations
        # We can't match by size from CSV alone, but if size matches the product itself, use it
        variation_csv = product.get("variationCSV", "")
        if variation_csv and product_size and str(product_size).strip().lower() == target_size_clean:
            return product
    
    # If no exact match found, return None (not first product)
    # This allows the caller to decide what to do (use first product as fallback)
    return None


def extract_ean(product_data: Dict[str, Any]) -> str:
    """Extract EAN from Keepa product data.
    
    If product has a matched variation, we still use the parent's EAN
    as variations share the same EAN/UPC.
    """
    if not product_data:
        return ""
    
    ean_list = product_data.get("eanList", [])
    if ean_list and len(ean_list) > 0:
        return str(ean_list[0])  # Return first EAN
    return ""


def extract_asin(product_data: Dict[str, Any]) -> str:
    """Extract ASIN from Keepa product data."""
    if not product_data:
        return ""
    
    return product_data.get("asin", "")


async def process_csv(input_file: str, output_file: Optional[str] = None, limit_rows: Optional[int] = None):
    """Process CSV file and enrich with Keepa API data.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (optional, auto-generated if not provided)
        limit_rows: Limit number of rows to process (for testing)
    """
    if not output_file:
        # Create output filename by adding _enriched before .csv
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_enriched.csv"
    
    print(f"📖 Reading CSV file: {input_file}")
    print(f"💾 Output file: {output_file}")
    if limit_rows:
        print(f"🧪 TEST MODE: Processing only first {limit_rows} rows")
    print()
    
    # Read the CSV file
    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    if len(rows) < 2:
        print("❌ CSV file is empty or has no data rows")
        return
    
    # Get header row
    header = rows[0]
    
    # Find the Index column (column 2, index 1)
    index_col_idx = 1  # "Index / Gender / Size" is the second column
    
    # Add new column for ASIN only (EAN removed per user request)
    header.append("ASIN")
    
    # Limit rows if specified (for testing)
    total_rows = len(rows) - 1  # Exclude header
    if limit_rows:
        # Keep header + limit_rows data rows
        rows = rows[:limit_rows + 1]
        print(f"📊 Processing {limit_rows} of {total_rows} data rows (excluding header)")
    else:
        print(f"📊 Found {total_rows} data rows (excluding header)")
    print(f"🔍 Using column {index_col_idx + 1} ('{header[index_col_idx]}') for search terms")
    print()
    
    # Cache for model numbers to avoid duplicate API calls
    # Structure: {model_number: {"products": [...], "size_map": {size: {asin}}}}
    model_cache: Dict[str, Dict[str, Any]] = {}
    
    # Process each row (skip header row)
    processed_count = 0
    success_count = 0
    failed_count = 0
    cached_count = 0
    
    for i, row in enumerate(rows[1:], start=2):  # Start from row 2 (skip header)
        if len(row) <= index_col_idx:
            # Row doesn't have enough columns, add empty ASIN
            row.append("")
            rows[i - 1] = row
            continue
        
        index_value = row[index_col_idx].strip()
        
        if not index_value:
            # Empty index, add empty ASIN
            row.append("")
            rows[i - 1] = row
            continue
        
        # Extract model number and size from index
        model_number = extract_model_number(index_value)
        size = extract_size_from_index(index_value)
        gender = extract_gender_from_index(index_value)
        
        if not model_number:
            print(f"Row {i}: ⚠️  Could not extract model number from '{index_value}'")
            row.append("")
            rows[i - 1] = row
            failed_count += 1
            continue
        
        # Check cache first
        if model_number in model_cache:
            cache_entry = model_cache[model_number]
            
            # If we have a size, try to match it from cached products
            if size and "size_map" in cache_entry and size in cache_entry["size_map"]:
                size_match = cache_entry["size_map"][size]
                asin = size_match.get("asin", "")
                row.append(asin)
                print(f"Row {i}: 💾 Using cached size match for '{model_number}' size '{size}' - ASIN: {asin}")
                cached_count += 1
                if asin:
                    success_count += 1
                else:
                    failed_count += 1
            elif "products" in cache_entry and cache_entry["products"]:
                # We have cached products but no size match yet
                # Try to match by size from cached products
                matched_product = match_product_by_size(cache_entry["products"], size, gender)
                if matched_product:
                    asin = extract_asin(matched_product)
                    # Update size map cache
                    if "size_map" not in cache_entry:
                        cache_entry["size_map"] = {}
                    cache_entry["size_map"][size] = {"asin": asin}
                    row.append(asin)
                    print(f"Row {i}: 💾 Matched size '{size}' from cached products for '{model_number}' - ASIN: {asin}")
                    cached_count += 1
                    if asin:
                        success_count += 1
                    else:
                        failed_count += 1
                else:
                    # No size match, use first product as fallback
                    first_product = cache_entry["products"][0]
                    asin = extract_asin(first_product)
                    row.append(asin)
                    print(f"Row {i}: 💾 Using first cached product for '{model_number}' (no size match) - ASIN: {asin}")
                    cached_count += 1
                    if asin:
                        success_count += 1
                    else:
                        failed_count += 1
            else:
                # Old cache format (single product)
                asin = cache_entry.get("asin", "")
                row.append(asin)
                print(f"Row {i}: 💾 Using cached data for '{model_number}' - ASIN: {asin}")
                cached_count += 1
                if asin:
                    success_count += 1
                else:
                    failed_count += 1
        else:
            print(f"Row {i}: 🔍 Searching for '{model_number}' (from '{index_value}')...", end=" ")
            
            # Call Keepa API - returns list of products
            products = await call_keepa_search(model_number)
            
            if products and len(products) > 0:
                # Try to match by size if we have one
                matched_product = None
                size_matched = False
                if size:
                    matched_product = match_product_by_size(products, size, gender)
                    size_matched = matched_product is not None
                
                # If no size match or no size provided, use first product
                if not matched_product:
                    matched_product = products[0]
                
                asin = extract_asin(matched_product)
                is_variation_match = matched_product.get("_is_variation_match", False)
                
                # Cache all products and size mapping
                cache_entry = {
                    "products": products,
                    "size_map": {}
                }
                
                # If we matched by size, cache that mapping
                if size and size_matched:
                    cache_entry["size_map"][size] = {"asin": asin}
                
                model_cache[model_number] = cache_entry
                
                row.append(asin)
                if len(products) > 1:
                    if size_matched:
                        match_type = "variation" if is_variation_match else "product"
                        print(f"✅ Found {len(products)} products, matched size '{size}' ({match_type}) - ASIN: {asin}")
                    else:
                        print(f"⚠️  Found {len(products)} products, using first (size '{size}' not matched) - ASIN: {asin}")
                else:
                    match_type = "variation" if is_variation_match else "product"
                    print(f"✅ Found - ASIN: {asin} ({match_type})")
                success_count += 1
            else:
                # Cache empty result to avoid retrying
                model_cache[model_number] = {"products": [], "size_map": {}}
                row.append("")
                print(f"❌ Not found")
                failed_count += 1
        
        processed_count += 1
        
        # Add a small delay to respect rate limits (optional)
        await asyncio.sleep(0.1)
    
    # Write the enriched CSV
    print()
    print(f"💾 Writing enriched data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    print()
    print("=" * 60)
    print("✅ Processing complete!")
    print(f"   Total rows processed: {processed_count}")
    print(f"   ✅ Successfully enriched: {success_count}")
    print(f"   💾 Cached lookups: {cached_count}")
    print(f"   ❌ Failed/Not found: {failed_count}")
    print(f"   🔑 Unique model numbers: {len(model_cache)}")
    print(f"   📄 Output saved to: {output_file}")
    print("=" * 60)


async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python enrich_csv_with_keepa.py <input_csv_file> [output_csv_file] [--limit N]")
        print()
        print("Example:")
        print("  python enrich_csv_with_keepa.py data.csv")
        print("  python enrich_csv_with_keepa.py data.csv output.csv")
        print("  python enrich_csv_with_keepa.py data.csv output.csv --limit 5")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = None
    limit_rows = None
    
    # Parse arguments
    for i, arg in enumerate(sys.argv[2:], start=2):
        if arg == "--limit" and i + 1 < len(sys.argv):
            try:
                limit_rows = int(sys.argv[i + 1])
            except ValueError:
                print(f"❌ Error: Invalid limit value: {sys.argv[i + 1]}")
                sys.exit(1)
        elif not arg.startswith("--") and not output_file:
            output_file = arg
    
    if not os.path.exists(input_file):
        print(f"❌ Error: File not found: {input_file}")
        sys.exit(1)
    
    if not KEEPA_API_KEY:
        print("❌ Error: KEEPA_API_KEY environment variable not set")
        print("   Please set it in your .env file or environment")
        sys.exit(1)
    
    await process_csv(input_file, output_file, limit_rows)


if __name__ == "__main__":
    asyncio.run(main())

