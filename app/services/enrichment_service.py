import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
import httpx
from ..database import get_database
from ..models.product import Product, ProductCreate
from ..models.catalog import Catalog
from ..config import settings
from ..services.aws_service import aws_service
import json

logger = logging.getLogger(__name__)


class EnrichmentProvider:
    """Base class for enrichment providers."""
    
    def __init__(self, name: str):
        self.name = name
    
    async def enrich_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single item. Override in subclasses."""
        raise NotImplementedError


class AmazonAPIProvider(EnrichmentProvider):
    """Amazon API enrichment provider."""
    
    def __init__(self):
        super().__init__("amazon_api")
        self.api_key = settings.amazon_api_key
        self.api_secret = settings.amazon_api_secret
        self.base_url = "https://api.amazon.com"  # Replace with actual Amazon API endpoint
    
    async def enrich_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich item using Amazon API."""
        try:
            # Extract searchable fields from item data
            search_term = self._extract_search_term(item_data)
            
            # Simulate Amazon API call (replace with actual implementation)
            enriched_data = await self._call_amazon_api(search_term)
            
            return {
                "enrichment_source": self.name,
                "enrichment_status": "completed",
                "enriched_data": enriched_data,
                "enriched_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Amazon API enrichment failed: {e}")
            return {
                "enrichment_source": self.name,
                "enrichment_status": "failed",
                "enrichment_errors": [str(e)],
                "enriched_at": datetime.utcnow()
            }
    
    def _extract_search_term(self, item_data: Dict[str, Any]) -> str:
        """Extract search term from item data."""
        # Try to find the best search term from available fields
        # Common catalog field names
        name_fields = ["name", "product_name", "item_name", "title", "product_title"]
        desc_fields = ["description", "product_description", "item_description", "details"]
        sku_fields = ["sku", "product_sku", "item_sku", "product_code", "item_code"]
        
        # Try name fields first
        for field in name_fields:
            if item_data.get(field):
                return str(item_data[field])
        
        # Try description fields
        for field in desc_fields:
            if item_data.get(field):
                desc = str(item_data[field])
                return desc[:100] if len(desc) > 100 else desc
        
        # Try SKU fields
        for field in sku_fields:
            if item_data.get(field):
                return str(item_data[field])
        
        # Fallback to concatenating available fields
        available_fields = []
        for key, value in item_data.items():
            if value and key not in ['id', 'price', 'quantity', 'currency', 'unit']:
                available_fields.append(str(value))
        
        if available_fields:
            return " ".join(available_fields[:3])  # Use first 3 meaningful fields
        
        # Last resort
        return f"Product {hash(str(item_data)) % 1000000}"
    
    async def _call_amazon_api(self, search_term: str) -> Dict[str, Any]:
        """Call Amazon API (simulated for now)."""
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        # Mock response - replace with actual Amazon API call
        return {
            "amazon_product_id": f"AMZ_{hash(search_term) % 1000000}",
            "amazon_price": 99.99,
            "amazon_rating": 4.5,
            "amazon_review_count": 1250,
            "amazon_category": "Electronics",
            "amazon_brand": "Generic Brand",
            "amazon_features": ["Wireless", "Bluetooth", "Noise Cancelling"],
            "amazon_images": ["https://example.com/image1.jpg"],
            "amazon_url": f"https://amazon.com/product/{hash(search_term) % 1000000}"
        }


class KeepaAPIProvider(EnrichmentProvider):
    """Keepa API enrichment provider."""
    
    def __init__(self):
        super().__init__("keepa_api")
        self.api_key = getattr(settings, 'keepa_api_key', None)
        self.base_url = "https://api.keepa.com"
    
    async def enrich_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich item using Keepa API."""
        try:
            # Extract searchable fields from item data
            search_term = self._extract_search_term(item_data)
            
            # Simulate Keepa API call (replace with actual implementation)
            enriched_data = await self._call_keepa_api(search_term)
            
            return {
                "enrichment_source": self.name,
                "enrichment_status": "completed",
                "enriched_data": enriched_data,
                "enriched_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Keepa API enrichment failed: {e}")
            return {
                "enrichment_source": self.name,
                "enrichment_status": "failed",
                "enrichment_errors": [str(e)],
                "enriched_at": datetime.utcnow()
            }
    
    def _extract_search_term(self, item_data: Dict[str, Any]) -> str:
        """Extract search term from item data."""
        # Common catalog field names
        name_fields = ["name", "product_name", "item_name", "title", "product_title"]
        desc_fields = ["description", "product_description", "item_description", "details"]
        sku_fields = ["sku", "product_sku", "item_sku", "product_code", "item_code"]
        
        # Try name fields first
        for field in name_fields:
            if item_data.get(field):
                return str(item_data[field])
        
        # Try description fields
        for field in desc_fields:
            if item_data.get(field):
                desc = str(item_data[field])
                return desc[:100] if len(desc) > 100 else desc
        
        # Try SKU fields
        for field in sku_fields:
            if item_data.get(field):
                return str(item_data[field])
        
        # Fallback to concatenating available fields
        available_fields = []
        for key, value in item_data.items():
            if value and key not in ['id', 'price', 'quantity', 'currency', 'unit']:
                available_fields.append(str(value))
        
        if available_fields:
            return " ".join(available_fields[:3])  # Use first 3 meaningful fields
        
        # Last resort
        return f"Product {hash(str(item_data)) % 1000000}"
    
    async def _call_keepa_api(self, search_term: str) -> Dict[str, Any]:
        """Call Keepa API to get product information including images."""
        logger.info(f"Keepa API - Starting API call for search term: '{search_term}'")
        logger.info(f"Keepa API - API key configured: {'Yes' if self.api_key else 'No'}")
        
        if not self.api_key:
            logger.error("Keepa API - No API key configured, falling back to mock data")
            raise Exception("Keepa API key not configured")
        
        try:
            # Make real Keepa API call
            async with httpx.AsyncClient() as client:
                # Search for products using the search term
                search_url = f"{self.base_url}/search"
                params = {
                    "key": self.api_key,
                    "q": search_term,
                    "domain": 1,  # 1 = US, 2 = UK, 3 = DE, etc.
                    "excludeCategories": "0",  # Include all categories
                    "titleSearch": 1,  # Search in titles
                    "productType": 1,  # All product types
                    "limit": 5  # Limit results for better performance
                }
                
                logger.info(f"Keepa API - Making search request to: {search_url}")
                logger.info(f"Keepa API - Search params: {params}")
                
                response = await client.get(search_url, params=params, timeout=30.0)
                response.raise_for_status()
                
                search_data = response.json()
                logger.info(f"Keepa API - Search response status: {response.status_code}")
                logger.info(f"Keepa API - Search response keys: {list(search_data.keys())}")
                logger.info(f"Keepa API - Products found: {len(search_data.get('products', []))}")
                
                if not search_data.get("products") or len(search_data["products"]) == 0:
                    # Fallback to mock data if no results
                    logger.warning(f"Keepa API - No search results for '{search_term}', using mock data")
                    return self._get_mock_keepa_data(search_term)
                
                # Get the first (most relevant) product
                product = search_data["products"][0]
                product_id = product.get("asin")
                
                # Get detailed product information including images
                product_url = f"{self.base_url}/product"
                product_params = {
                    "key": self.api_key,
                    "asin": product_id,
                    "domain": 1,
                    "history": 0,  # No price history needed for images
                    "offers": 0,  # No offers needed for images
                    "update": 0,  # No updates needed for images
                    "rating": 1,  # Include rating
                    "review": 1,  # Include review count
                    "images": 1   # Include images
                }
                
                logger.info(f"Keepa API - Making product detail request to: {product_url}")
                logger.info(f"Keepa API - Product params: {product_params}")
                
                product_response = await client.get(product_url, params=product_params, timeout=30.0)
                product_response.raise_for_status()
                
                product_data = product_response.json()
                logger.info(f"Keepa API - Product detail response status: {product_response.status_code}")
                logger.info(f"Keepa API - Product detail response keys: {list(product_data.keys())}")
                logger.info(f"Keepa API - Products in detail response: {len(product_data.get('products', []))}")
                
                if not product_data.get("products") or len(product_data["products"]) == 0:
                    logger.warning(f"Keepa API - No product detail results for ASIN {product_id}, using mock data")
                    return self._get_mock_keepa_data(search_term)
                
                detailed_product = product_data["products"][0]
                
                # Extract image information
                images = []
                main_image = None
                
                # Log the raw Keepa product data for debugging
                logger.info(f"Keepa API - Raw product data keys: {list(detailed_product.keys())}")
                logger.info(f"Keepa API - imagesCSV field: {detailed_product.get('imagesCSV')}")
                logger.info(f"Keepa API - title: {detailed_product.get('title')}")
                logger.info(f"Keepa API - brand: {detailed_product.get('brand')}")
                
                if detailed_product.get("imagesCSV"):
                    image_urls = detailed_product["imagesCSV"].split(",")
                    images = [f"https://m.media-amazon.com/images/I/{img_id}.jpg" for img_id in image_urls if img_id]
                    if images:
                        main_image = images[0]  # First image is usually the main one
                        logger.info(f"Keepa API - Extracted {len(images)} images, main: {main_image[:50]}...")
                    else:
                        logger.warning(f"Keepa API - No valid image IDs found in imagesCSV: {detailed_product['imagesCSV']}")
                else:
                    logger.warning(f"Keepa API - No imagesCSV field found in product data")
                
                # Build the response data
                response_data = {
                    "keepa_product_id": product_id,
                    "keepa_price": self._extract_keepa_price(detailed_product),
                    "keepa_rating": detailed_product.get("rating", 0.0),
                    "keepa_review_count": detailed_product.get("reviewCount", 0),
                    "keepa_category": self._extract_keepa_category(detailed_product),
                    "keepa_brand": detailed_product.get("brand", "Unknown Brand"),
                    "keepa_features": detailed_product.get("features", []),
                    "keepa_images": images,
                    "keepa_main_image": main_image,
                    "keepa_url": f"https://keepa.com/product.html#1!{product_id}",
                    "keepa_search_term": search_term,
                    "keepa_status": "real_data",
                    "keepa_title": detailed_product.get("title", search_term),
                    "keepa_manufacturer": detailed_product.get("manufacturer", "Unknown Manufacturer"),
                    "keepa_mpn": detailed_product.get("mpn", ""),
                    "keepa_upc": detailed_product.get("upc", ""),
                    "keepa_ean": detailed_product.get("ean", "")
                }
                
                logger.info(f"Keepa API - Final response data keys: {list(response_data.keys())}")
                logger.info(f"Keepa API - keepa_main_image: {response_data['keepa_main_image']}")
                logger.info(f"Keepa API - keepa_images count: {len(response_data['keepa_images']) if response_data['keepa_images'] else 0}")
                
                return response_data
                
        except httpx.RequestError as e:
            logger.error(f"Keepa API request error for '{search_term}': {e}")
            return self._get_mock_keepa_data(search_term)
        except httpx.HTTPStatusError as e:
            logger.error(f"Keepa API HTTP error for '{search_term}': {e.response.status_code}")
            return self._get_mock_keepa_data(search_term)
        except Exception as e:
            logger.error(f"Keepa API error for search term '{search_term}': {e}")
            return self._get_mock_keepa_data(search_term)
    
    def _get_mock_keepa_data(self, search_term: str) -> Dict[str, Any]:
        """Return mock Keepa data as fallback."""
        logger.info(f"Using mock Keepa data for: {search_term}")
        
        # Generate realistic mock images based on search term
        mock_images = [
            f"https://m.media-amazon.com/images/I/71{hash(search_term) % 100000000}L._AC_SL1500_.jpg",
            f"https://m.media-amazon.com/images/I/71{hash(search_term) % 100000000}L._AC_SL1500_2_.jpg",
            f"https://m.media-amazon.com/images/I/71{hash(search_term) % 100000000}L._AC_SL1500_3_.jpg"
        ]
        
        return {
            "keepa_product_id": f"KPA_{hash(search_term) % 1000000}",
            "keepa_price": 89.99,
            "keepa_rating": 4.3,
            "keepa_review_count": 980,
            "keepa_category": "Electronics",
            "keepa_brand": "Generic Brand",
            "keepa_features": ["Portable", "Rechargeable", "Fast Charging"],
            "keepa_images": mock_images,
            "keepa_main_image": mock_images[0],
            "keepa_url": f"https://keepa.com/product/{hash(search_term) % 1000000}",
            "keepa_search_term": search_term,
            "keepa_status": "mock_data",
            "keepa_title": f"Mock {search_term}",
            "keepa_manufacturer": "Mock Manufacturer",
            "keepa_mpn": f"MPN_{hash(search_term) % 10000}",
            "keepa_upc": f"UPC_{hash(search_term) % 100000000000}",
            "keepa_ean": f"EAN_{hash(search_term) % 1000000000000}"
        }
    
    def _extract_keepa_price(self, product: Dict[str, Any]) -> Optional[float]:
        """Extract current price from Keepa product data."""
        try:
            # Keepa stores price history in arrays
            # Current price is usually the last non-null value in the price array
            price_history = product.get("csv", [])
            if price_history and len(price_history) > 0:
                # Find the last non-null price (excluding -1 which means no data)
                for price in reversed(price_history):
                    if price and price != -1:
                        # Keepa prices are in cents, convert to dollars
                        return float(price) / 100.0
            return None
        except Exception:
            return None
    
    def _extract_keepa_category(self, product: Dict[str, Any]) -> Optional[str]:
        """Extract category from Keepa product data."""
        try:
            # Keepa stores category information in the categories array
            categories = product.get("categories", [])
            if categories and len(categories) > 0:
                # Return the first (most specific) category
                return categories[0]
            return None
        except Exception:
            return None


class LocalEnrichmentService:
    """Local enrichment service for testing and debugging."""
    
    def __init__(self):
        self._db = None
        self.providers = {
            "amazon": AmazonAPIProvider(),
            "keepa": KeepaAPIProvider()
        }

    @property
    def db(self):
        if self._db is None:
            self._db = get_database()
        return self._db
    
    async def enrich_catalog(
        self, 
        catalog_id: str, 
        user_id: str, 
        provider: str = "amazon",
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """Enrich all items in a catalog using the specified provider."""
        try:
            # Validate provider
            if provider not in self.providers:
                raise ValueError(f"Unknown provider: {provider}. Available: {list(self.providers.keys())}")
            
            # Get catalog
            catalog = await self.db.catalogs.find_one({
                "_id": ObjectId(catalog_id),
                "user_id": ObjectId(user_id)
            })
            
            if not catalog:
                raise ValueError("Catalog not found")
            
            # Get catalog file from S3 or local storage
            # For now, we'll simulate line items
            line_items = await self._get_catalog_line_items(catalog)
            
            if not line_items:
                raise ValueError("No line items found in catalog")
            
            # Update catalog status
            await self.db.catalogs.update_one(
                {"_id": ObjectId(catalog_id)},
                {
                    "$set": {
                        "status": "processing",
                        "enrichment_started_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Process items in batches
            total_items = len(line_items)
            enriched_count = 0
            failed_count = 0
            
            for i in range(0, total_items, batch_size):
                batch = line_items[i:i + batch_size]
                
                # Process batch concurrently
                tasks = [
                    self._enrich_single_item(
                        item, 
                        catalog_id, 
                        user_id, 
                        provider,
                        index=i + j
                    )
                    for j, item in enumerate(batch)
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count results
                for result in results:
                    if isinstance(result, Exception):
                        failed_count += 1
                        logger.error(f"Item enrichment failed: {result}")
                    else:
                        if result.get("enrichment_status") == "completed":
                            enriched_count += 1
                        else:
                            failed_count += 1
                
                # Update progress
                await self.db.catalogs.update_one(
                    {"_id": ObjectId(catalog_id)},
                    {
                        "$set": {
                            "enriched_items": enriched_count,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                logger.info(f"Processed batch {i//batch_size + 1}, enriched: {enriched_count}, failed: {failed_count}")
            
            # Update final status
            final_status = "completed" if failed_count == 0 else "partially_completed"
            await self.db.catalogs.update_one(
                {"_id": ObjectId(catalog_id)},
                {
                    "$set": {
                        "status": final_status,
                        "enriched_items": enriched_count,
                        "enrichment_completed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return {
                "catalog_id": catalog_id,
                "total_items": total_items,
                "enriched_items": enriched_count,
                "failed_items": failed_count,
                "status": final_status,
                "provider": provider
            }
            
        except Exception as e:
            logger.error(f"Catalog enrichment failed: {e}")
            # Update catalog status to error
            await self.db.catalogs.update_one(
                {"_id": ObjectId(catalog_id)},
                {
                    "$set": {
                        "status": "error",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            raise
    
    async def _enrich_single_item(
        self, 
        item_data: Dict[str, Any], 
        catalog_id: str, 
        user_id: str, 
        provider: str,
        index: int
    ) -> Dict[str, Any]:
        """Enrich a single item and save to database."""
        try:
            # Get the provider
            enrichment_provider = self.providers[provider]
            
            # Enrich the item
            enrichment_result = await enrichment_provider.enrich_item(item_data)
            
            # Create product record with flexible field mapping
            # Map Excel columns to product fields
            
            # Debug logging for enrichment result
            logger.info(f"Debug: Enrichment result structure: {enrichment_result}")
            logger.info(f"Debug: Enrichment result keys: {list(enrichment_result.keys())}")
            if 'enriched_data' in enrichment_result:
                logger.info(f"Debug: Enriched data keys: {list(enrichment_result['enriched_data'].keys())}")
                logger.info(f"Debug: Looking for keepa_main_image: {enrichment_result['enriched_data'].get('keepa_main_image')}")
                logger.info(f"Debug: Looking for keepa_images: {enrichment_result['enriched_data'].get('keepa_images')}")
            
            # Extract image fields from enrichment based on provider
            enrichment_source = enrichment_result.get("enrichment_source", "")
            if "keepa" in enrichment_source.lower():
                # Keepa provider
                main_image = self._extract_image_from_enrichment(enrichment_result, "keepa_main_image")
                images = self._extract_images_from_enrichment(enrichment_result, "keepa_images")
            elif "amazon" in enrichment_source.lower():
                # Amazon provider
                main_image = self._extract_image_from_enrichment(enrichment_result, "amazon_images")
                images = self._extract_images_from_enrichment(enrichment_result, "amazon_images")
            else:
                # Unknown provider, try both
                main_image = self._extract_image_from_enrichment(enrichment_result, "keepa_main_image") or self._extract_image_from_enrichment(enrichment_result, "amazon_images")
                images = self._extract_images_from_enrichment(enrichment_result, "keepa_images") or self._extract_images_from_enrichment(enrichment_result, "amazon_images")
            
            product_data = {
                "catalog_id": ObjectId(catalog_id),
                "user_id": ObjectId(user_id),
                "line_item_id": f"item_{index}",
                "name": self._extract_field_value(item_data, ["Style Name", "name", "product_name", "item_name", "title", "product_title"], f"Item {index}"),
                "description": self._create_description_from_excel(item_data),
                "category": self._extract_field_value(item_data, ["Category", "Subcategory", "Division", "category", "product_category", "item_category", "type", "product_type"]),
                "brand": self._extract_field_value(item_data, ["brand", "product_brand", "item_brand", "manufacturer", "make"]),
                "sku": self._extract_field_value(item_data, ["SKU", "sku", "product_sku", "item_sku", "product_code", "item_code"]),
                "upc": self._extract_field_value(item_data, ["UPC", "upc", "product_upc", "item_upc", "barcode", "ean"]),
                "price": self._extract_numeric_field(item_data, ["Offer Price", "Wholesale", "RRP", "price", "product_price", "item_price", "cost", "unit_price"]),
                "currency": self._extract_field_value(item_data, ["Currency", "currency", "product_currency", "item_currency"], "USD"),
                "quantity": self._extract_numeric_field(item_data, ["Quantity Available", "quantity", "product_quantity", "item_quantity", "qty", "stock"]),
                "unit": self._extract_field_value(item_data, ["unit", "product_unit", "item_unit", "uom", "measurement_unit"], "piece"),
                "original_data": item_data,
                # Add image fields from enrichment
                "main_image": main_image,
                "images": images,
                "enriched_data": enrichment_result.get("enriched_data", {}),
                "enrichment_source": enrichment_result.get("enrichment_source"),
                "enrichment_status": enrichment_result.get("enrichment_status"),
                "enrichment_errors": enrichment_result.get("enrichment_errors", []),
                "enriched_at": enrichment_result.get("enriched_at"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Save to database
            await self.db.products.insert_one(product_data)
            
            return enrichment_result
            
        except Exception as e:
            logger.error(f"Failed to enrich item {index}: {e}")
            return {
                "enrichment_status": "failed",
                "enrichment_errors": [str(e)]
            }
    
    async def _get_catalog_line_items(self, catalog: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get line items from catalog file."""
        try:
            # Get the file from S3
            file_data = await aws_service.get_file_from_s3(catalog["file_path"])
            if not file_data:
                raise Exception("Failed to retrieve catalog file from S3")
            
            # Parse the file based on its type
            file_name = catalog["file_name"]
            
            if file_name.lower().endswith('.csv'):
                return await self._parse_csv_file(file_data)
            elif file_name.lower().endswith('.json'):
                return await self._parse_json_file(file_data)
            elif file_name.lower().endswith('.xlsx') or file_name.lower().endswith('.xls'):
                return await self._parse_excel_file(file_data)
            else:
                raise ValueError(f"Unsupported file format: {file_name}")
                
        except Exception as e:
            logger.error(f"Error getting catalog line items: {e}")
            # Fallback to mock data for testing
            logger.warning("Falling back to mock data due to file parsing error")
            return self._get_mock_line_items()
    
    def _get_mock_line_items(self) -> List[Dict[str, Any]]:
        """Fallback mock data for testing."""
        return [
            {
                "name": "Wireless Bluetooth Headphones",
                "description": "High-quality wireless headphones",
                "category": "Electronics",
                "brand": "AudioTech",
                "sku": "ATH-BT001",
                "price": 99.99,
                "currency": "USD",
                "quantity": 1,
                "unit": "piece"
            },
            {
                "name": "Smartphone Case",
                "description": "Protective case for smartphones",
                "category": "Accessories",
                "brand": "CasePro",
                "sku": "CP-SC001",
                "price": 19.99,
                "currency": "USD",
                "quantity": 1,
                "unit": "piece"
            },
            {
                "name": "USB-C Cable",
                "description": "Fast charging USB-C cable",
                "category": "Cables",
                "brand": "CableMax",
                "sku": "CM-UC001",
                "price": 12.99,
                "currency": "USD",
                "quantity": 2,
                "unit": "piece"
            }
        ]
    
    async def _parse_csv_file(self, file_data: bytes) -> List[Dict[str, Any]]:
        """Parse CSV file and return line items."""
        try:
            import csv
            import io
            
            text = file_data.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(text))
            return [dict(row) for row in csv_reader]
        except Exception as e:
            logger.error(f"Error parsing CSV file: {e}")
            raise Exception(f"Failed to parse CSV file: {e}")
    
    async def _parse_json_file(self, file_data: bytes) -> List[Dict[str, Any]]:
        """Parse JSON file and return line items."""
        try:
            import json
            
            text = file_data.decode('utf-8')
            data = json.loads(text)
            # Assume JSON is an array of line items or has a 'items' key
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'items' in data:
                return data['items']
            else:
                raise ValueError("Invalid JSON format: expected array or object with 'items' key")
        except Exception as e:
            logger.error(f"Error parsing JSON file: {e}")
            raise Exception(f"Failed to parse JSON file: {e}")
    
    async def _parse_excel_file(self, file_data: bytes) -> List[Dict[str, Any]]:
        """Parse Excel file and return line items."""
        try:
            import pandas as pd
            import io
            
            # Read Excel file using pandas
            excel_data = io.BytesIO(file_data)
            
            # Try to read the first sheet
            df = pd.read_excel(excel_data, sheet_name=0)
            
            # Convert DataFrame to list of dictionaries
            line_items = []
            for _, row in df.iterrows():
                # Convert pandas Series to dict, handling NaN values
                item = {}
                for column, value in row.items():
                    if pd.isna(value):
                        item[column] = None
                    else:
                        # Convert numpy types to Python types
                        if hasattr(value, 'item'):
                            item[column] = value.item()
                        else:
                            item[column] = value
                line_items.append(item)
            
            logger.info(f"Successfully parsed Excel file with {len(line_items)} items")
            return line_items
            
        except Exception as e:
            logger.error(f"Error parsing Excel file: {e}")
            raise Exception(f"Failed to parse Excel file: {e}")
    
    def _extract_field_value(self, item_data: Dict[str, Any], field_names: List[str], default: Any = None) -> Any:
        """Extract field value from item data using multiple possible field names."""
        for field in field_names:
            if item_data.get(field):
                return item_data[field]
        return default
    
    def _extract_numeric_field(self, item_data: Dict[str, Any], field_names: List[str]) -> Optional[float]:
        """Extract numeric field value from item data."""
        for field in field_names:
            value = item_data.get(field)
            if value is not None:
                try:
                    # Convert to float, handling various numeric formats
                    if isinstance(value, str):
                        # Remove currency symbols and commas
                        cleaned_value = value.replace('$', '').replace(',', '').strip()
                        return float(cleaned_value)
                    else:
                        return float(value)
                except (ValueError, TypeError):
                    continue
        return None
    
    def _create_description_from_excel(self, item_data: Dict[str, Any]) -> str:
        """Create a description from multiple Excel columns."""
        description_parts = []
        
        # Add color if available
        color = item_data.get("Color Name")
        if color and str(color).lower() != "nan":
            description_parts.append(f"Color: {color}")
        
        # Add size if available
        size = item_data.get("Size")
        if size and str(size).lower() != "nan":
            description_parts.append(f"Size: {size}")
        
        # Add alt size if available
        alt_size = item_data.get("Alt Size")
        if alt_size and str(alt_size).lower() != "nan":
            description_parts.append(f"Alt Size: {alt_size}")
        
        # Add category info if available
        category = item_data.get("Category")
        if category and str(category).lower() != "nan":
            description_parts.append(f"Category: {category}")
        
        subcategory = item_data.get("Subcategory")
        if subcategory and str(subcategory).lower() != "nan":
            description_parts.append(f"Subcategory: {subcategory}")
        
        division = item_data.get("Division")
        if division and str(division).lower() != "nan":
            description_parts.append(f"Division: {division}")
        
        if description_parts:
            return " | ".join(description_parts)
        else:
            return "Product from catalog"
    
    def _extract_image_from_enrichment(self, enrichment_result: Dict[str, Any], field_name: str) -> Optional[str]:
        """Extract main image URL from enrichment result."""
        try:
            enriched_data = enrichment_result.get("enriched_data", {})
            image_url = enriched_data.get(field_name)
            
            # Debug logging
            if image_url:
                logger.info(f"Found main image: {image_url[:50]}...")
            else:
                logger.warning(f"No main image found for field: {field_name}")
                logger.debug(f"Available fields in enriched_data: {list(enriched_data.keys())}")
            
            return image_url
        except Exception as e:
            logger.error(f"Error extracting main image: {e}")
            return None
    
    def _extract_images_from_enrichment(self, enrichment_result: Dict[str, Any], field_name: str) -> Optional[List[str]]:
        """Extract list of image URLs from enrichment result."""
        try:
            enriched_data = enrichment_result.get("enriched_data", {})
            images = enriched_data.get(field_name, [])
            
            # Debug logging
            if images and isinstance(images, list):
                logger.info(f"Found {len(images)} images")
                logger.debug(f"First image: {images[0][:50] if images[0] else 'None'}...")
            else:
                logger.warning(f"No images found for field: {field_name}")
                logger.debug(f"Available fields in enriched_data: {list(enriched_data.keys())}")
            
            if isinstance(images, list) and images:
                return images
            return None
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return None
    
    async def get_enrichment_providers(self) -> List[str]:
        """Get list of available enrichment providers."""
        return list(self.providers.keys())


# Global instance
local_enrichment_service = LocalEnrichmentService()
