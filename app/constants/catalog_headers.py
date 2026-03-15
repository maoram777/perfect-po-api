"""
Canonical definition of CSV/Excel catalog input file headers.

Use this module as the single source of truth for:
- Which columns are required vs optional
- Accepted column names (aliases) for each field
- Extracting values from a row by canonical name

Required headers (upload is rejected if any are missing):
- sku: Stock Keeping Unit / product code
- upc: Universal Product Code / barcode / EAN
- quantity: Available quantity / inventory
- offer_price: Selling/offer price (used for profit and PO score)

Optional headers (used when present):
- whs: Warehouse/cost price (for PO score reference)
- msrp: Manufacturer Suggested Retail Price / RRP / list price
- name: Product name / title
- description: Product description
- brand: Brand / manufacturer
- category: Category / subcategory / division
- color: Color
- size: Size
- currency: Currency code (default USD)
- unit: Unit of measure (e.g. piece, case)
"""

from typing import Dict, Any, List, Optional, Tuple

# --- Required (CSV/Excel must have at least one column matching an alias for each) ---
REQUIRED_CATALOG_HEADERS = ["sku", "upc", "quantity", "offer_price"]

# --- Optional (accepted column names per canonical field) ---
OPTIONAL_CATALOG_HEADERS = ["whs", "msrp", "name", "description", "brand", "category", "color", "size", "currency", "unit"]

# Canonical name -> list of accepted column names in file (case-sensitive as in file; normalization is done when comparing)
HEADER_ALIASES: Dict[str, List[str]] = {
    # Required
    "sku": [
        "sku", "SKU", "Article Number", "product_sku", "item_sku", "product_code", "item_code",
    ],
    "upc": [
        "upc", "UPC", "UPC Code", "upc_code", "product_upc", "item_upc", "barcode", "ean",
    ],
    "quantity": [
        "quantity", "Quantity", "Inventory", "Quantity Available", "product_quantity", "item_quantity", "qty", "stock",
    ],
    "offer_price": [
        "offer_price", "Offer Price", "offer", "Offer", "Price", "price", "selling_price",
    ],
    # Optional
    "whs": [
        "WHS", "whs", "Warehouse Price", "warehouse_price", "warehouse", "cost_price",
    ],
    "msrp": [
        "MSRP", "msrp", "Manufacturer Recommended Retail Price", "RRP", "rrp", "Retail Price", "retail_price", "list_price", "Original Price",
    ],
    "name": [
        "Article Name", "Style Name", "name", "product_name", "item_name", "title", "product_title",
    ],
    "description": [
        "description", "Description", "product_description", "item_description",
    ],
    "brand": [
        "brand", "Brand", "product_brand", "item_brand", "manufacturer", "make",
    ],
    "category": [
        "Category", "Subcategory", "Division", "category", "product_category", "item_category", "type", "product_type",
    ],
    "color": [
        "color", "Color", "Colour", "product_color", "item_color",
    ],
    "size": [
        "size", "Size", "product_size", "item_size",
    ],
    "currency": [
        "Currency", "currency", "product_currency", "item_currency",
    ],
    "unit": [
        "unit", "Unit", "product_unit", "item_unit", "uom", "measurement_unit",
    ],
}


def get_aliases(canonical: str) -> List[str]:
    """Return the list of accepted column names for a canonical field name."""
    return HEADER_ALIASES.get(canonical, [])


def _normalize_header(header: str) -> str:
    """Normalize a header for comparison: lowercase, strip, remove spaces and underscores."""
    if not header:
        return ""
    h = (header or "").strip().lower()
    return h.replace(" ", "").replace("_", "")


def file_has_required_headers(header_names: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if the file has at least one column for each required canonical header.
    header_names: list of column names as they appear in the file.
    Returns (all_present, missing_canonical_headers).
    """
    normalized_file_headers = {_normalize_header(h) for h in (header_names or [])}
    missing = []
    for canonical in REQUIRED_CATALOG_HEADERS:
        aliases = get_aliases(canonical)
        found = any(_normalize_header(a) in normalized_file_headers for a in aliases)
        if not found:
            missing.append(canonical)
    return (len(missing) == 0, missing)


def get_value(row: Dict[str, Any], canonical: str, default: Any = None) -> Any:
    """Get the first non-empty value from row for the given canonical field (checks all aliases, case-insensitive)."""
    # Normalize row keys once so header matching is case-insensitive and ignores spaces/underscores
    normalized_row: Dict[str, Any] = {_normalize_header(k): v for k, v in row.items()}
    for col in get_aliases(canonical):
        norm_col = _normalize_header(col)
        val = normalized_row.get(norm_col)
        if val is not None and (val != "" if isinstance(val, str) else True):
            return val
    return default


def get_numeric_value(row: Dict[str, Any], canonical: str) -> Optional[float]:
    """Get numeric value from row for the given canonical field. Returns None if missing or not parseable."""
    val = get_value(row, canonical)
    if val is None:
        return None
    try:
        if isinstance(val, str):
            cleaned = val.replace("$", "").replace("€", "").replace(",", "").replace(" ", "").strip()
            return float(cleaned) if cleaned else None
        return float(val)
    except (ValueError, TypeError):
        return None
