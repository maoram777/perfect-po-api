import asyncio
import copy
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
from ..constants.catalog_headers import get_value, get_numeric_value
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
            "product_id": f"AMZ_{hash(search_term) % 1000000}",
            "price": 99.99,
            "rating": 4.5,
            "review_count": 1250,
            "category": "Electronics",
            "brand": "Generic Brand",
            "features": ["Wireless", "Bluetooth", "Noise Cancelling"],
            "images": ["https://example.com/image1.jpg"],
            "url": f"https://amazon.com/product/{hash(search_term) % 1000000}"
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
            # Extract UPC from item data
            upc = self._extract_upc(item_data)
            
            if not upc:
                logger.warning(f"Keepa API - No UPC found in item data, cannot enrich")
                return {
                    "enrichment_source": self.name,
                    "enrichment_status": "failed",
                    "enrichment_errors": ["UPC not found in item data"],
                    "enriched_at": datetime.utcnow()
                }
            
            # Call Keepa API with UPC
            enriched_data = await self._call_keepa_api(upc)
            
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
    
    def _extract_upc(self, item_data: Dict[str, Any]) -> Optional[str]:
        """Extract UPC from item data using canonical catalog headers."""
        upc_value = get_value(item_data, "upc")
        if upc_value:
            upc_str = str(upc_value).strip()
            upc_clean = "".join(filter(str.isdigit, upc_str))
            if upc_clean:
                return upc_clean
        return None
    
    async def enrich_by_identifier(
        self,
        asin: Optional[str] = None,
        upc: Optional[str] = None,
        model: Optional[str] = None,
        title: Optional[str] = None,
        part: Optional[str] = None,
        brand: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enrich product using Keepa API with ASIN, UPC, or product finder (model/title/part/brand).
        
        Priority:
        1. If ASIN provided -> use direct product lookup
        2. If UPC provided -> use direct product lookup
        3. If model/title/part/brand provided -> use product finder (search endpoint)
        """
        try:
            # Priority 1: Direct lookup by ASIN
            if asin:
                logger.info(f"Keepa API - Enriching by ASIN: {asin}")
                enriched_data = await self._call_keepa_api_by_asin(asin)
                return {
                    "enrichment_source": self.name,
                    "enrichment_status": "completed",
                    "enriched_data": enriched_data,
                    "enriched_at": datetime.utcnow()
                }
            
            # Priority 2: Direct lookup by UPC
            if upc:
                logger.info(f"Keepa API - Enriching by UPC: {upc}")
                enriched_data = await self._call_keepa_api(upc)
                return {
                    "enrichment_source": self.name,
                    "enrichment_status": "completed",
                    "enriched_data": enriched_data,
                    "enriched_at": datetime.utcnow()
                }
            
            # Priority 3: Product finder using model/title/part/brand
            if model or title or part or brand:
                logger.info(f"Keepa API - Using product finder with model={model}, title={title}, part={part}, brand={brand}")
                enriched_data = await self._call_keepa_product_finder(
                    model=model,
                    title=title,
                    part=part,
                    brand=brand
                )
                return {
                    "enrichment_source": self.name,
                    "enrichment_status": "completed",
                    "enriched_data": enriched_data,
                    "enriched_at": datetime.utcnow()
                }
            
            # No valid identifier provided
            return {
                "enrichment_source": self.name,
                "enrichment_status": "failed",
                "enrichment_errors": ["No valid identifier provided. Provide ASIN, UPC, or model/title/part/brand"],
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
    
    def _normalize_upc(self, upc: str) -> str:
        """Return digits-only UPC for matching."""
        if not upc:
            return ""
        return "".join(filter(str.isdigit, str(upc)))

    async def _call_keepa_api_bulk_codes(self, codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """Call Keepa API with up to 50 UPC/EAN codes in a single request.
        
        Args:
            codes: List of UPC/EAN strings (up to 50).
        
        Returns:
            Dict mapping request UPC (digits-only) to standardized enriched data.
        """
        if not self.api_key:
            logger.error("Keepa API - No API key configured, cannot make bulk call")
            return {}
        codes = [c for c in codes if c]
        if not codes:
            return {}
        if len(codes) > 50:
            logger.warning(f"Keepa API - Bulk codes limited to 50, got {len(codes)}, using first 50")
            codes = codes[:50]
        code_string = ",".join(codes)
        try:
            async with httpx.AsyncClient() as client:
                product_url = f"{self.base_url}/product"
                params = {
                    "key": self.api_key,
                    "domain": 1,
                    "code": code_string,
                }
                headers = {"User-Agent": "Perfect-PO-API/1.0"}
                response = await client.get(product_url, params=params, headers=headers, timeout=90.0)
                response.raise_for_status()
                product_data = response.json()
                raw_products = product_data.get("products", [])
                # Map response products back to request UPCs by matching upcList/eanList
                result = {}
                assigned_request_upcs = set()
                for detailed in raw_products:
                    upc_list = detailed.get("upcList") or []
                    ean_list = detailed.get("eanList") or []
                    product_codes = {self._normalize_upc(str(x)) for x in upc_list + ean_list if x}
                    matched_request_upc = None
                    for req in codes:
                        n = self._normalize_upc(req)
                        if not n or n in assigned_request_upcs:
                            continue
                        if n in product_codes:
                            matched_request_upc = n
                            break
                        if any(n == c or n.endswith(c) or c.endswith(n) for c in product_codes):
                            matched_request_upc = n
                            break
                    if not matched_request_upc:
                        for n in (self._normalize_upc(c) for c in codes):
                            if n and n not in assigned_request_upcs:
                                matched_request_upc = n
                                break
                    if matched_request_upc:
                        assigned_request_upcs.add(matched_request_upc)
                        processed = self._process_keepa_product_response(
                            detailed, identifier=matched_request_upc, identifier_type="upc"
                        )
                        result[matched_request_upc] = processed
                logger.info(f"Keepa API - Bulk codes returned {len(result)} products for {len(codes)} request codes")
                return result
        except Exception as e:
            logger.error(f"Keepa API bulk codes error: {e}")
            return {}

    async def _call_keepa_api_bulk_by_asin(self, asins: List[str]) -> Dict[str, Dict[str, Any]]:
        """Call Keepa API to get product information for multiple ASINs in bulk.
        
        Args:
            asins: List of ASINs (up to 50)
        
        Returns:
            Dictionary mapping ASIN to enriched data dict, or empty dict if failed
        """
        logger.info(f"Keepa API - Bulk call for {len(asins)} ASINs")
        
        if not self.api_key:
            logger.error("Keepa API - No API key configured, cannot make bulk call")
            return {}
        
        if len(asins) > 50:
            logger.warning(f"Keepa API - Bulk call limited to 50 ASINs, got {len(asins)}, using first 50")
            asins = asins[:50]
        
        try:
            async with httpx.AsyncClient() as client:
                product_url = f"{self.base_url}/product"
                # Keepa API accepts comma-separated ASINs
                asin_string = ",".join(asins)
                params = {
                    "key": self.api_key,
                    "domain": 1,
                    "asin": asin_string,
                    "images": 1,
                    "history": 0,
                    "offers": 0
                }
                
                headers = {"User-Agent": "Perfect-PO-API/1.0"}
                
                response = await client.get(product_url, params=params, headers=headers, timeout=60.0)
                response.raise_for_status()
                
                product_data = response.json()
                products = product_data.get("products", [])
                
                # Map products by ASIN
                result = {}
                for product in products:
                    asin = product.get("asin")
                    if asin:
                        result[asin] = self._process_keepa_product_response(product, identifier=asin, identifier_type="asin")
                
                logger.info(f"Keepa API - Bulk call returned {len(result)} products")
                return result
                
        except Exception as e:
            logger.error(f"Keepa API bulk call error: {e}")
            return {}
    
    async def _call_keepa_api_by_asin(self, asin: str) -> Dict[str, Any]:
        """Call Keepa API to get product information using ASIN."""
        logger.info(f"Keepa API - Starting API call for ASIN: '{asin}'")
        
        if not self.api_key:
            logger.error("Keepa API - No API key configured, falling back to mock data")
            return self._get_mock_keepa_data(asin)
        
        try:
            async with httpx.AsyncClient() as client:
                product_url = f"{self.base_url}/product"
                params = {
                    "key": self.api_key,
                    "domain": 1,
                    "asin": asin,
                    "images": 1,
                    "history": 0,
                    "offers": 0
                }
                
                headers = {"User-Agent": "Perfect-PO-API/1.0"}
                
                response = await client.get(product_url, params=params, headers=headers, timeout=30.0)
                response.raise_for_status()
                
                product_data = response.json()
                
                if not product_data.get("products") or len(product_data["products"]) == 0:
                    logger.warning(f"Keepa API - No products found for ASIN '{asin}', using mock data")
                    return self._get_mock_keepa_data(asin)
                
                detailed_product = product_data["products"][0]
                return self._process_keepa_product_response(detailed_product, identifier=asin, identifier_type="asin")
                
        except httpx.RequestError as e:
            logger.error(f"Keepa API request error for ASIN '{asin}': {e}")
            return self._get_mock_keepa_data(asin)
        except httpx.HTTPStatusError as e:
            logger.error(f"Keepa API HTTP error for ASIN '{asin}': {e.response.status_code} - {e.response.text}")
            return self._get_mock_keepa_data(asin)
        except Exception as e:
            logger.error(f"Keepa API error for ASIN '{asin}': {e}")
            return self._get_mock_keepa_data(asin)
    
    async def _call_keepa_product_finder(
        self,
        model: Optional[str] = None,
        title: Optional[str] = None,
        part: Optional[str] = None,
        brand: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call Keepa Product Finder API using search endpoint with filters.
        
        Uses the /search endpoint with title and brand parameters to find products
        matching the provided model, title, part number, or brand.
        """
        logger.info(f"Keepa API - Product finder: model={model}, title={title}, part={part}, brand={brand}")
        
        if not self.api_key:
            logger.error("Keepa API - No API key configured, falling back to mock data")
            return self._get_mock_keepa_data(f"{model or title or part or 'unknown'}")
        
        try:
            # Build search term from available parameters
            # Priority: title > model > part > brand
            search_term_base = title or model or part or brand or ""
            
            if not search_term_base:
                raise ValueError("At least one of model, title, part, or brand must be provided")
            
            async with httpx.AsyncClient() as client:
                # Use search endpoint for product finder
                # Based on actual Keepa API: uses 'term' parameter and 'type=product'
                search_url = f"{self.base_url}/search"
                
                # Build search term from available parameters
                # If brand is provided separately, combine with search term for better results
                search_term = search_term_base
                if brand and brand not in search_term and search_term != brand:
                    search_term = f"{search_term} {brand}".strip()
                
                params = {
                    "key": self.api_key,
                    "domain": 1,
                    "type": "product",  # Required: type=product for product search
                    "term": search_term   # Use 'term' parameter (not 'q')
                }
                
                headers = {"User-Agent": "Perfect-PO-API/1.0"}
                
                logger.info(f"Keepa API - Product finder search URL: {search_url}")
                logger.info(f"Keepa API - Product finder search term: {search_term}")
                logger.info(f"Keepa API - Product finder params: {dict((k, v if k != 'key' else '***') for k, v in params.items())}")
                
                try:
                    response = await client.get(search_url, params=params, headers=headers, timeout=30.0)
                    logger.info(f"Keepa API - Search response status: {response.status_code}")
                    logger.info(f"Keepa API - Search response headers: {dict(response.headers)}")
                    
                    # Log raw response text for debugging
                    response_text = response.text
                    logger.info(f"Keepa API - Search response text (first 1000 chars): {response_text[:1000]}")
                    
                    response.raise_for_status()
                except httpx.HTTPStatusError as http_err:
                    # Log detailed error information
                    logger.error(f"Keepa API - HTTP error during search: {http_err.response.status_code}")
                    logger.error(f"Keepa API - Error response text: {http_err.response.text[:1000]}")
                    raise
                
                search_data = response.json()
                logger.info(f"Keepa API - Search response keys: {list(search_data.keys())}")
                logger.info(f"Keepa API - Search response type: {type(search_data)}")
                
                # Log the full response structure for debugging
                if "products" in search_data:
                    logger.info(f"Keepa API - Products array length: {len(search_data.get('products', []))}")
                    if len(search_data.get('products', [])) > 0:
                        logger.info(f"Keepa API - First product keys: {list(search_data['products'][0].keys())}")
                        logger.info(f"Keepa API - First product ASIN: {search_data['products'][0].get('asin', 'NOT FOUND')}")
                else:
                    logger.warning(f"Keepa API - No 'products' key in response. Response keys: {list(search_data.keys())}")
                    logger.warning(f"Keepa API - Full response: {str(search_data)[:500]}")
                
                if not search_data.get("products") or len(search_data["products"]) == 0:
                    logger.warning(f"Keepa API - No products found for search term '{search_term}'")
                    logger.warning(f"Keepa API - Response data: {str(search_data)[:500]}")
                    logger.warning(f"Keepa API - Using mock data as fallback")
                    return self._get_mock_keepa_data(search_term)
                
                # Get the first result - search API already returns full product details
                first_product = search_data["products"][0]
                product_asin = first_product.get("asin")
                
                logger.info(f"Keepa API - First product from search: ASIN={product_asin}, Title={first_product.get('title', 'N/A')[:50]}")
                
                if not product_asin:
                    logger.warning(f"Keepa API - No ASIN found in search result")
                    logger.warning(f"Keepa API - First product data: {str(first_product)[:500]}")
                    logger.warning(f"Keepa API - Using mock data as fallback")
                    return self._get_mock_keepa_data(search_term)
                
                # The search API already returns full product details, so process directly
                # No need to make a second API call to /product endpoint
                logger.info(f"Keepa API - Processing search result directly (search API returns full product data)")
                processed_data = self._process_keepa_product_response(
                    first_product, 
                    identifier=search_term, 
                    identifier_type="search"
                )
                logger.info(f"Keepa API - Successfully processed product data from search result")
                return processed_data
                
        except httpx.RequestError as e:
            logger.error(f"Keepa API product finder request error: {e}")
            logger.error(f"Keepa API - Request error type: {type(e).__name__}")
            import traceback
            logger.error(f"Keepa API - Request error traceback: {traceback.format_exc()}")
            return self._get_mock_keepa_data(f"{model or title or part or 'unknown'}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Keepa API product finder HTTP error: {e.response.status_code}")
            logger.error(f"Keepa API - HTTP error response text: {e.response.text[:500]}")
            try:
                error_data = e.response.json()
                logger.error(f"Keepa API - HTTP error JSON: {error_data}")
            except:
                pass
            return self._get_mock_keepa_data(f"{model or title or part or 'unknown'}")
        except Exception as e:
            logger.error(f"Keepa API product finder error: {e}")
            logger.error(f"Keepa API - Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Keepa API - Error traceback: {traceback.format_exc()}")
            return self._get_mock_keepa_data(f"{model or title or part or 'unknown'}")
    
    def _process_keepa_product_response(
        self,
        detailed_product: Dict[str, Any],
        identifier: str,
        identifier_type: str = "upc"
    ) -> Dict[str, Any]:
        """Process Keepa API product response into standardized format."""
        # Extract image information
        images = []
        main_image = None
        
        # Extract images from images array (preferred method)
        images_array = detailed_product.get("images", [])
        if images_array and len(images_array) > 0:
            for img_obj in images_array:
                if isinstance(img_obj, dict):
                    img_id = img_obj.get("l") or img_obj.get("m")
                    if img_id:
                        if not img_id.startswith("http"):
                            if not img_id.endswith('.jpg') and not img_id.endswith('.png'):
                                img_id = f"{img_id}.jpg"
                            img_url = f"{img_id}"
                        else:
                            img_url = img_id
                        images.append(img_url)
                elif isinstance(img_obj, str):
                    if not img_obj.startswith("http"):
                        if not img_obj.endswith('.jpg') and not img_obj.endswith('.png'):
                            img_obj = f"{img_obj}.jpg"
                        images.append(img_obj)
                    else:
                        images.append(img_obj)
            
            if images:
                main_image = images[0]
        
        # Fallback to imagesCSV
        if not images and detailed_product.get("imagesCSV"):
            image_ids = [img_id.strip() for img_id in detailed_product["imagesCSV"].split(",") if img_id.strip()]
            for img_id in image_ids:
                if not img_id.endswith('.jpg') and not img_id.endswith('.png'):
                    img_id = f"{img_id}.jpg"
                images.append(f"https://m.media-amazon.com/images/I/{img_id}")
            if images:
                main_image = images[0]
        
        # Extract category
        category = self._extract_keepa_category(detailed_product)
        
        # Extract rating and review count
        rating = None
        review_count = 0
        if detailed_product.get("hasReviews", False):
            rating = detailed_product.get("rating")
            review_count = detailed_product.get("reviewCount", 0)
        
        # Price from csv[0]: array of [timestamp, price, timestamp, price, ...]; last pair = most updated
        # price_updated_at = that timestamp converted to Unix epoch (see app/docs/keep_epoch.py)
        price, price_updated_at = self._extract_keepa_price_and_timestamp(detailed_product)
        
        # availabilityAmazon: -1 = not available, 0 = available (Keepa convention)
        availability_amazon_raw = detailed_product.get("availabilityAmazon")
        available_amazon = availability_amazon_raw == 0 if availability_amazon_raw is not None else None
        
        # Build response data with standardized keys (no source prefix)
        response_data = {
            "product_id": detailed_product.get("asin", ""),
            "price": price,
            "price_updated_at": price_updated_at,
            "available_amazon": available_amazon,
            "rating": rating,
            "review_count": review_count,
            "category": category,
            "brand": detailed_product.get("brand", "Unknown Brand"),
            "color": detailed_product.get("color", ""),
            "features": detailed_product.get("features", []),
            "images": images,
            "main_image": main_image,
            "url": f"https://keepa.com/product.html#1!{detailed_product.get('asin', '')}",
            "status": "real_data",
            "title": detailed_product.get("title", ""),
            "description": detailed_product.get("description", ""),
            "manufacturer": detailed_product.get("manufacturer", "Unknown Manufacturer"),
            "model": detailed_product.get("model", ""),
            "part_number": detailed_product.get("partNumber", ""),
            "size": detailed_product.get("size", ""),
            "style": detailed_product.get("style", ""),
            "upc_list": detailed_product.get("upcList", []),
            "ean_list": detailed_product.get("eanList", [])
        }
        
        # Add identifier-specific fields
        if identifier_type == "upc":
            response_data["upc"] = identifier
        elif identifier_type == "asin":
            response_data["asin"] = identifier
        elif identifier_type == "search":
            response_data["search_term"] = identifier
        
        return response_data
    
    async def _call_keepa_api(self, upc: str) -> Dict[str, Any]:
        """Call Keepa API to get product information using UPC.
        
        According to Keepa API documentation:
        - Endpoint: /product
        - Parameters: key (required), domain (required, 1 = Amazon.com), code (UPC/EAN)
        - Optional: images (default: 1), history (default: 0), offers (default: 0)
        """
        logger.info(f"Keepa API - Starting API call for UPC: '{upc}'")
        logger.info(f"Keepa API - API key configured: {'Yes' if self.api_key else 'No'}")
        
        if not self.api_key:
            logger.error("Keepa API - No API key configured, falling back to mock data")
            return self._get_mock_keepa_data(upc)
        
        try:
            # Make real Keepa API call using UPC
            async with httpx.AsyncClient() as client:
                # Call product endpoint with UPC code
                # According to docs: images=1 (include images), history=0 (no price history), offers=0 (no offer data)
                product_url = f"{self.base_url}/product"
                params = {
                    "key": self.api_key,
                    "domain": 1,  # Hardcoded to Amazon.com (US marketplace) per docs
                    "code": upc,  # UPC/EAN code from CSV
                    # "images": 1,  # Include image data (per docs)
                    # "history": 0,  # Don't include price history (per docs)
                    # "offers": 0   # Don't include offer data (per docs)
                }
                
                logger.info(f"Keepa API - Making product request to: {product_url}")
                logger.info(f"Keepa API - Request params: key=***, domain=1, code={upc}, images=1, history=0, offers=0")
                
                # Add User-Agent header per docs
                headers = {
                    "User-Agent": "Perfect-PO-API/1.0"
                }
                
                response = await client.get(product_url, params=params, headers=headers, timeout=30.0)
                response.raise_for_status()
                
                product_data = response.json()
                logger.info(f"Keepa API - Response status: {response.status_code}")
                logger.info(f"Keepa API - Response keys: {list(product_data.keys())}")
                logger.info(f"Keepa API - Products found: {len(product_data.get('products', []))}")
                
                if not product_data.get("products") or len(product_data["products"]) == 0:
                    logger.warning(f"Keepa API - No products found for UPC '{upc}', using mock data")
                    return self._get_mock_keepa_data(upc)
                
                detailed_product = product_data["products"][0]
                
                # Log the raw Keepa product data for debugging
                logger.info(f"Keepa API - Raw product data keys: {list(detailed_product.keys())}")
                logger.info(f"Keepa API - ASIN: {detailed_product.get('asin')}")
                logger.info(f"Keepa API - Title: {detailed_product.get('title', 'N/A')[:50]}...")
                logger.info(f"Keepa API - Brand: {detailed_product.get('brand', 'N/A')}")
                
                # Use the shared processing method
                return self._process_keepa_product_response(detailed_product, identifier=upc, identifier_type="upc")
                
        except httpx.RequestError as e:
            logger.error(f"Keepa API request error for UPC '{upc}': {e}")
            return self._get_mock_keepa_data(upc)
        except httpx.HTTPStatusError as e:
            logger.error(f"Keepa API HTTP error for UPC '{upc}': {e.response.status_code} - {e.response.text}")
            # Handle specific error codes per docs
            if e.response.status_code == 401:
                logger.error("Keepa API - Unauthorized: Invalid API key")
            elif e.response.status_code == 429:
                logger.error("Keepa API - Rate limit exceeded")
            return self._get_mock_keepa_data(upc)
        except Exception as e:
            logger.error(f"Keepa API error for UPC '{upc}': {e}")
            return self._get_mock_keepa_data(upc)
    
    def _get_mock_keepa_data(self, upc: str) -> Dict[str, Any]:
        """Return mock Keepa data as fallback."""
        logger.info(f"Using mock Keepa data for UPC: {upc}")
        
        # Generate realistic mock images based on UPC
        mock_images = [
            f"https://m.media-amazon.com/images/I/71{hash(upc) % 100000000}L._AC_SL1500_.jpg",
            f"https://m.media-amazon.com/images/I/71{hash(upc) % 100000000}L._AC_SL1500_2_.jpg",
            f"https://m.media-amazon.com/images/I/71{hash(upc) % 100000000}L._AC_SL1500_3_.jpg"
        ]
        
        return {
            "product_id": f"KPA_{hash(upc) % 1000000}",
            "price": 89.99,
            "price_updated_at": int(datetime.utcnow().timestamp()),
            "available_amazon": True,
            "rating": 4.3,
            "review_count": 980,
            "category": "Electronics",
            "brand": "Generic Brand",
            "color": "Black",
            "features": ["Portable", "Rechargeable", "Fast Charging"],
            "images": mock_images,
            "main_image": mock_images[0],
            "url": f"https://keepa.com/product.html#1!{hash(upc) % 1000000}",
            "upc": upc,
            "status": "mock_data",
            "title": f"Mock Product {upc}",
            "manufacturer": "Mock Manufacturer",
            "model": f"MODEL_{hash(upc) % 10000}",
            "part_number": f"PN_{hash(upc) % 10000}",
            "upc_list": [upc]
        }
    
    @staticmethod
    def _keepa_minutes_to_epoch_seconds(keepa_minutes: Optional[int]) -> Optional[int]:
        """Convert Keepa time (minutes since 2011-01-01 UTC) to Unix epoch seconds.
        See app/docs/keep_epoch.py for the formula explanation.
        """
        if keepa_minutes is None:
            return None
        return (int(keepa_minutes) + 21564000) * 60

    def _extract_keepa_price_and_timestamp(
        self, product: Dict[str, Any]
    ) -> tuple:
        """Extract the most updated price and its timestamp from Keepa csv field.
        csv is array of arrays; csv[0] = Amazon price history: [ts0, price0, ts1, price1, ...]
        where ts = minutes since 2011-01-01 UTC, price = cents (-1 = no data).
        We use the last valid (timestamp, price) pair in csv[0]; timestamp is converted
        to Unix epoch seconds via app/docs/keep_epoch.py.
        Returns (price_in_dollars_or_none, price_updated_at_epoch_seconds_or_none).
        """
        try:
            price_history = product.get("csv", [])
            if not price_history or len(price_history) == 0:
                return (None, None)
            amazon_price_array = price_history[0] if len(price_history) > 0 else None
            if not amazon_price_array or not isinstance(amazon_price_array, list):
                return (None, None)
            # Pairs: [timestamp, price, timestamp, price, ...]; last pair is most recent
            for i in range(len(amazon_price_array) - 1, 0, -2):
                if i >= 1:
                    price = amazon_price_array[i]
                    if price is not None and price != -1 and price > 0:
                        keepa_ts = amazon_price_array[i - 1]
                        epoch_ts = self._keepa_minutes_to_epoch_seconds(
                            keepa_ts if isinstance(keepa_ts, (int, float)) else None
                        )
                        return (float(price) / 100.0, epoch_ts)
            if len(price_history) > 1:
                new_price_array = price_history[1]
                if isinstance(new_price_array, list) and len(new_price_array) >= 2:
                    for i in range(len(new_price_array) - 1, 0, -2):
                        if i >= 1:
                            price = new_price_array[i]
                            if price is not None and price != -1 and price > 0:
                                keepa_ts = new_price_array[i - 1]
                                epoch_ts = self._keepa_minutes_to_epoch_seconds(
                                    keepa_ts if isinstance(keepa_ts, (int, float)) else None
                                )
                                return (float(price) / 100.0, epoch_ts)
            return (None, None)
        except Exception as e:
            logger.warning(f"Error extracting price/timestamp from Keepa product: {e}")
            return (None, None)

    def _extract_keepa_price(self, product: Dict[str, Any]) -> Optional[float]:
        """Extract current price from Keepa product data (most recent from csv[0])."""
        price, _ = self._extract_keepa_price_and_timestamp(product)
        return price
    
    def _extract_keepa_category(self, product: Dict[str, Any]) -> Optional[str]:
        """Extract category from Keepa product data."""
        try:
            # Keepa stores category information in categoryTree array
            category_tree = product.get("categoryTree", [])
            if category_tree and len(category_tree) > 0:
                # Get the last (most specific) category from the tree
                # Category tree is ordered from general to specific
                last_category = category_tree[-1]
                if isinstance(last_category, dict):
                    return last_category.get("name", "")
                elif isinstance(last_category, str):
                    return last_category
            return None
        except Exception as e:
            logger.warning(f"Error extracting category from Keepa product: {e}")
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
    
    async def enrich_catalog_products_background(
        self,
        catalog_id: str,
        user_id: str,
        provider: str = "keepa",
        bulk_size: int = 50
    ) -> None:
        """Background task to enrich existing products in a catalog using bulk Keepa API calls.
        
        This method runs asynchronously and updates catalog enriched_items progressively.
        It processes products in batches of 50 and uses Keepa API bulk calls.
        """
        try:
            logger.info(f"🚀 Starting background enrichment for catalog {catalog_id}")
            logger.debug(f"enrich_catalog_products_background: params catalog_id={catalog_id}, user_id={user_id}, provider={provider}, bulk_size={bulk_size}")
            
            # Validate provider
            if provider not in self.providers:
                logger.error(f"Unknown provider: {provider}")
                await self.db.catalogs.update_one(
                    {"_id": ObjectId(catalog_id)},
                    {"$set": {"status": "failed", "updated_at": datetime.utcnow()}}
                )
                return
            
            # Update catalog status to processing
            await self.db.catalogs.update_one(
                {"_id": ObjectId(catalog_id)},
                {
                    "$set": {
                        "status": "processing",
                        "enrichment_started_at": datetime.utcnow(),
                        "enriched_items": 0,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Ensure products exist: create stubs from catalog file if none found
            catalog = await self.db.catalogs.find_one({
                "_id": ObjectId(catalog_id),
                "user_id": ObjectId(user_id)
            })
            if not catalog:
                logger.error(f"Catalog {catalog_id} not found for user {user_id}")
                await self.db.catalogs.update_one(
                    {"_id": ObjectId(catalog_id)},
                    {"$set": {"status": "failed", "updated_at": datetime.utcnow()}}
                )
                return
            
            existing_count = await self.db.products.count_documents({
                "catalog_id": ObjectId(catalog_id),
                "user_id": ObjectId(user_id)
            })
            
            logger.debug(f"enrich_catalog_products_background: existing products count={existing_count} for catalog {catalog_id}")

            if existing_count == 0:
                try:
                    logger.debug("enrich_catalog_products_background: no existing products, loading line items from catalog file")
                    line_items = await self._get_catalog_line_items(catalog)
                    if not line_items:
                        logger.warning(f"Catalog file has no line items: {catalog_id}")
                        await self.db.catalogs.update_one(
                            {"_id": ObjectId(catalog_id)},
                            {"$set": {"status": "completed", "enrichment_completed_at": datetime.utcnow(), "updated_at": datetime.utcnow()}}
                        )
                        return
                    logger.info(f"Creating {len(line_items)} product stubs from catalog file for catalog {catalog_id}")
                    for i, row in enumerate(line_items):
                        try:
                            sku = get_value(row, "sku")
                            upc = get_value(row, "upc")
                            if upc and isinstance(upc, str):
                                upc = "".join(filter(str.isdigit, upc.strip())) or None
                            qty = get_numeric_value(row, "quantity")
                            quantity = int(qty) if qty is not None else None
                            offer_price = get_numeric_value(row, "offer_price")
                            logger.debug(
                                f"Stub product {i}: sku={sku}, upc={upc}, quantity={quantity}, offer_price={offer_price}"
                            )
                            stub = {
                                "catalog_id": ObjectId(catalog_id),
                                "user_id": ObjectId(user_id),
                                "line_item_id": f"item_{i}",
                                "name": get_value(row, "name") or f"Item {i}",
                                "description": get_value(row, "description"),
                                "category": get_value(row, "category"),
                                "brand": get_value(row, "brand"),
                                "sku": sku,
                                "upc": upc,
                                "quantity": quantity,
                                "offer_price": offer_price,
                                "raw_data": row,
                                "currency": get_value(row, "currency") or "USD",
                                "unit": get_value(row, "unit") or "piece",
                                "enrichment": {
                                    "source": None,
                                    "status": "pending",
                                    "errors": [],
                                    "data": {}
                                },
                                "created_at": datetime.utcnow(),
                                "updated_at": datetime.utcnow(),
                            }
                            await self.db.products.insert_one(stub)
                        except Exception as row_err:
                            logger.exception(
                                f"Failed to create product stub for row {i} (catalog_id={catalog_id}): {row_err}"
                            )
                            raise
                except Exception as create_err:
                    logger.exception(
                        f"Failed to create product stubs from catalog file (catalog_id={catalog_id}): {create_err}"
                    )
                    await self.db.catalogs.update_one(
                        {"_id": ObjectId(catalog_id)},
                        {"$set": {"status": "failed", "updated_at": datetime.utcnow()}}
                    )
                    return

            # Get all products for this catalog that need enrichment
            products_cursor = self.db.products.find({
                "catalog_id": ObjectId(catalog_id),
                "user_id": ObjectId(user_id),
                "$or": [
                    {"enrichment.status": {"$ne": "completed"}},
                    {"enrichment.status": {"$exists": False}},
                    {"enrichment": {"$exists": False}}
                ]
            })
            
            products = await products_cursor.to_list(None)
            total_products = len(products)
            logger.debug(f"enrich_catalog_products_background: total products needing enrichment={total_products}")
            
            if total_products == 0:
                logger.info(f"No products to enrich for catalog {catalog_id}")
                await self.db.catalogs.update_one(
                    {"_id": ObjectId(catalog_id)},
                    {
                        "$set": {
                            "status": "completed",
                            "enrichment_completed_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                return
            
            logger.info(f"📦 Found {total_products} products to enrich")
            
            enriched_count = 0
            failed_count = 0
            keepa_provider = self.providers.get("keepa")
            
            # Process products in batches of bulk_size (50)
            for batch_start in range(0, total_products, bulk_size):
                batch = products[batch_start:batch_start + bulk_size]
                batch_num = (batch_start // bulk_size) + 1
                total_batches = (total_products + bulk_size - 1) // bulk_size
                
                logger.info(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} products)")
                
                # Single bulk Keepa API call for up to 50 UPCs
                upcs = []
                for p in batch:
                    u = p.get("upc")
                    if u:
                        upcs.append(str(u).strip())
                    else:
                        logger.warning(f"Product {p.get('_id')} has no UPC, skipping")
                
                bulk_enriched = await keepa_provider._call_keepa_api_bulk_codes(upcs) if upcs else {}
                
                for product in batch:
                    product_id = product["_id"]
                    upc = product.get("upc")
                    if not upc:
                        failed_count += 1
                        await self.db.products.update_one(
                            {"_id": product_id},
                            {"$set": {"enrichment": {"source": provider, "status": "failed", "errors": ["No UPC"], "data": {}}, "updated_at": datetime.utcnow()}}
                        )
                        continue
                    normalized_upc = keepa_provider._normalize_upc(upc)
                    enriched_data = bulk_enriched.get(normalized_upc) if bulk_enriched else None
                    
                    if not enriched_data:
                        failed_count += 1
                        await self.db.products.update_one(
                            {"_id": product_id},
                            {"$set": {"enrichment": {"source": provider, "status": "failed", "errors": ["No data from Keepa for this UPC"], "data": {}}, "updated_at": datetime.utcnow()}}
                        )
                        continue
                    
                    # BSON-safe copy so enrichment.data is stored correctly
                    data_to_store = copy.deepcopy(enriched_data)
                    product_price = data_to_store.get("price")
                    offer_price = product.get("offer_price")
                    profit = None
                    if offer_price is not None and product_price is not None:
                        profit = self.calculate_profit(offer_price, product_price, cogs_percentage=0.35)
                    
                    enrichment_payload = {
                        "source": keepa_provider.name,
                        "status": "completed",
                        "errors": [],
                        "data": data_to_store,
                    }
                    await self.db.products.update_one(
                        {"_id": product_id},
                        {
                            "$set": {
                                "enrichment": enrichment_payload,
                                "profit": profit,
                                "enriched_at": datetime.utcnow(),
                                "updated_at": datetime.utcnow(),
                            }
                        }
                    )
                    enriched_count += 1
                
                # Update catalog enriched_items after each batch
                await self.db.catalogs.update_one(
                    {"_id": ObjectId(catalog_id)},
                    {
                        "$set": {
                            "enriched_items": enriched_count,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                logger.info(f"✅ Batch {batch_num}/{total_batches} completed. Total enriched: {enriched_count}, failed: {failed_count}")
            
            # Update final catalog status
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
            
            logger.info(f"🎉 Background enrichment completed for catalog {catalog_id}. Enriched: {enriched_count}, Failed: {failed_count}")
            
        except Exception as e:
            logger.error(f"❌ Background enrichment failed for catalog {catalog_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Update catalog status to failed
            try:
                await self.db.catalogs.update_one(
                    {"_id": ObjectId(catalog_id)},
                    {
                        "$set": {
                            "status": "failed",
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            except Exception as update_error:
                logger.error(f"Failed to update catalog status: {update_error}")
    
    async def enrich_catalog(
        self, 
        catalog_id: str, 
        user_id: str, 
        provider: str = "keepa",
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
                logger.info(f"Debug: Looking for main_image: {enrichment_result['enriched_data'].get('main_image')}")
                logger.info(f"Debug: Looking for images: {enrichment_result['enriched_data'].get('images')}")
            
            # Extract enrichment data from result
            enrichment_source = enrichment_result.get("enrichment_source", "")
            enriched_data = enrichment_result.get("enriched_data", {})
            
            # Extract images and color using standardized keys (no source prefix)
            main_image = self._extract_image_from_enrichment(enrichment_result, "main_image")
            images = self._extract_images_from_enrichment(enrichment_result, "images")
            # Use enriched color if available, otherwise fall back to Excel
            color = self._extract_single_color(enriched_data.get("color") or self._extract_colors_from_excel(item_data))
            
            # Extract size from Index column or other sources
            size = self._extract_size_from_item_data(item_data)
            
            # Extract required fields from raw_data (must exist due to CSV validation)
            # These are saved at product level for easy access (see constants.catalog_headers)
            sku = get_value(item_data, "sku")
            upc = get_value(item_data, "upc")
            if upc and isinstance(upc, str):
                upc = "".join(filter(str.isdigit, upc.strip())) or None
            quantity = get_numeric_value(item_data, "quantity")
            if quantity is not None:
                quantity = int(quantity)
            offer_price = get_numeric_value(item_data, "offer_price")
            
            # Extract optional pricing fields for PO score calculation
            whs = get_numeric_value(item_data, "whs")
            msrp = get_numeric_value(item_data, "msrp")
            offer = offer_price  # Use the extracted offer_price for PO score calculation
            
            # Calculate PO score if we have the required fields
            po_score = self.calculate_po_score(whs, msrp, offer)
            
            # Calculate profit percentage: (product_price - cogs - offer_price) / product_price
            # Get product_price from enrichment using standardized key
            product_price = enriched_data.get("price")
            
            # Calculate profit percentage: (product_price - cogs - offer_price) / product_price
            # COGS = product_price * 0.35 (35%)
            profit = self.calculate_profit(offer, product_price, cogs_percentage=0.35)
            
            product_data = {
                "catalog_id": ObjectId(catalog_id),
                "user_id": ObjectId(user_id),
                "line_item_id": f"item_{index}",
                "name": get_value(item_data, "name") or f"Item {index}",
                "description": self._create_description_from_excel(item_data),
                "category": get_value(item_data, "category"),
                "brand": get_value(item_data, "brand"),
                "sku": sku,  # Required (catalog_headers)
                "upc": upc,  # Required (catalog_headers)
                "price": get_numeric_value(item_data, "offer_price"),  # fallback from offer_price aliases
                "currency": get_value(item_data, "currency") or "USD",
                "quantity": quantity,  # Required (catalog_headers)
                "offer_price": offer_price,  # Required (catalog_headers)
                "unit": get_value(item_data, "unit") or "piece",
                "color": color,  # Single color (not array)
                "size": size,  # Size - can be number (shoes) or dimensions (clothing)
                "raw_data": item_data,
                # Add image fields from enrichment
                "main_image": main_image,
                "images": images,
                "enrichment": {
                    "source": enrichment_result.get("enrichment_source"),
                    "status": enrichment_result.get("enrichment_status", "pending"),
                    "errors": enrichment_result.get("enrichment_errors", []),
                    "data": enriched_data
                },
                "enriched_at": enrichment_result.get("enriched_at"),
                "po_score": po_score,  # Purchase Order score (calculated from whs, msrp, offer)
                "profit": profit,  # Profit percentage = (product_price - cogs - offer_price) / product_price (where cogs = product_price * 35%)
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
            file_path = catalog.get("file_path")
            file_name = catalog.get("file_name")
            logger.debug(f"_get_catalog_line_items: fetching file_path={file_path}, file_name={file_name}")
            # Get the file from S3
            file_data = await aws_service.get_file_from_s3(file_path)
            if not file_data:
                raise Exception("Failed to retrieve catalog file from S3")
            logger.debug(f"_get_catalog_line_items: got {len(file_data)} bytes from S3, parsing by type")
            # Parse the file based on its type
            if file_name and file_name.lower().endswith('.csv'):
                items = await self._parse_csv_file(file_data)
                logger.debug(f"_get_catalog_line_items: parsed {len(items)} CSV line items")
                return items
            elif file_name and file_name.lower().endswith('.json'):
                items = await self._parse_json_file(file_data)
                logger.debug(f"_get_catalog_line_items: parsed {len(items)} JSON line items")
                return items
            elif file_name.lower().endswith('.xlsx') or file_name.lower().endswith('.xls'):
                items = await self._parse_excel_file(file_data)
                logger.debug(f"_get_catalog_line_items: parsed {len(items)} Excel line items")
                return items
            else:
                raise ValueError(f"Unsupported file format: {file_name}")
                
        except Exception as e:
            logger.error(f"Error getting catalog line items: {e}", exc_info=True)
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
                        cleaned_value = value.replace('$', '').replace('€', '').replace(',', '').replace(' ', '').strip()
                        return float(cleaned_value)
                    else:
                        return float(value)
                except (ValueError, TypeError):
                    continue
        return None
    
    def calculate_po_score(self, whs: Optional[float], msrp: Optional[float], offer: Optional[float]) -> Optional[float]:
        """Calculate Purchase Order score based on warehouse price, MSRP, and offer price.
        
        Formula:
        - Higher discount (lower offer relative to MSRP) = higher score (1-100)
        - If offer >= MSRP: score = 0 (no discount)
        - If offer < MSRP: score = ((MSRP - offer) / MSRP) * 100, capped at 100
        - If offer < 0 or MSRP <= 0: return None (invalid data)
        
        Args:
            whs: Warehouse price (optional, for reference)
            msrp: Manufacturer Recommended Retail Price
            offer: Offer price (often written as "offer price")
        
        Returns:
            PO score between 0-100, or None if calculation is not possible
        """
        # Need at least MSRP and offer to calculate
        if msrp is None or offer is None:
            return None
        
        # Validate values
        if msrp <= 0:
            return None
        
        # Calculate discount percentage
        # If offer is higher than MSRP, no discount (score = 0)
        if offer >= msrp:
            return 0.0
        
        # If offer is negative, treat as invalid
        if offer < 0:
            return None
        
        # Calculate discount: (MSRP - offer) / MSRP
        discount_ratio = (msrp - offer) / msrp
        
        # Convert to score (0-100 scale)
        # discount_ratio of 0 = 0 score, discount_ratio of 1 (100% off) = 100 score
        score = discount_ratio * 100
        
        # Cap at 100 (in case of negative MSRP or other edge cases)
        score = max(0.0, min(100.0, score))
        
        return round(score, 2)
    
    def calculate_profit(self, offer_price: Optional[float], product_price: Optional[float], cogs_percentage: float = 0.35) -> Optional[float]:
        """Calculate profit percentage based on product price, COGS, and offer price.
        
        Profit (as percentage) = (product_price - cogs - offer_price) / product_price
        COGS = product_price * cogs_percentage (default 35%)
        
        Args:
            offer_price: Offer price from input file (columns: "Offer" or "Offer Price")
            product_price: Product price from enrichment provider (Keepa/Amazon)
            cogs_percentage: Percentage of product_price to use for COGS calculation (default: 0.35 = 35%)
        
        Returns:
            Profit as percentage (decimal, e.g., 0.15 = 15%), can be negative, or None if calculation cannot be performed
        """
        # Need both values to calculate profit
        if offer_price is None or product_price is None:
            return None
        
        # Both must be positive
        if offer_price < 0 or product_price <= 0:
            return None
        
        # Calculate COGS: product_price * percentage
        cogs = product_price * cogs_percentage
        
        # Calculate profit percentage: (product_price - cogs - offer_price) / product_price
        profit = (product_price - cogs - offer_price) / product_price
        
        logger.debug(
            f"Profit calculation: offer_price={offer_price}, product_price={product_price}, "
            f"cogs_percentage={cogs_percentage}, cogs={cogs:.2f}, profit={profit:.4f} ({profit*100:.2f}%)"
        )
        
        return round(profit, 4)
    
    def validate_msrp(self, source_msrp: Optional[float], enriched_price: Optional[float], delta_percent: float = 5.0) -> Optional[bool]:
        """Validate that source MSRP is within delta_percent of enriched price from external API.
        
        Args:
            source_msrp: MSRP from source data (CSV/Excel)
            enriched_price: Price from external API (Keepa/Amazon)
            delta_percent: Allowed percentage difference (default: 5%)
        
        Returns:
            True if MSRP is within delta, False if outside delta, None if validation cannot be performed
        """
        # Need both values to validate
        if source_msrp is None or enriched_price is None:
            return None
        
        # Both must be positive
        if source_msrp <= 0 or enriched_price <= 0:
            return None
        
        # Calculate the percentage difference
        # Use the enriched price as the reference
        difference = abs(source_msrp - enriched_price)
        percentage_diff = (difference / enriched_price) * 100
        
        # Check if within delta
        is_valid = percentage_diff <= delta_percent
        
        logger.debug(
            f"MSRP validation: source_msrp={source_msrp}, enriched_price={enriched_price}, "
            f"difference={difference:.2f}, percentage_diff={percentage_diff:.2f}%, "
            f"delta={delta_percent}%, valid={is_valid}"
        )
        
        return is_valid
    
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
    
    def _extract_colors_from_excel(self, item_data: Dict[str, Any]) -> Optional[str]:
        """Extract colors from Excel data and return as string (may be comma-separated)."""
        color_fields = ["Color Name", "Color", "Colors", "Available Colors", "color_name", "color", "colors"]
        
        for field in color_fields:
            color_value = item_data.get(field)
            if color_value and str(color_value).lower() not in ["nan", "none", "null", ""]:
                return str(color_value).strip()
        
        return None
    
    def _extract_single_color(self, color_value: Optional[str]) -> Optional[str]:
        """Extract single color from color value (takes first if comma-separated)."""
        if not color_value:
            return None
        
        color_str = str(color_value).strip()
        if "," in color_str:
            # If comma-separated, take the first color
            return color_str.split(",")[0].strip()
        
        return color_str
    
    def _extract_size_from_item_data(self, item_data: Dict[str, Any]) -> Optional[str]:
        """Extract size from item data.
        
        Size can be:
        - A number (e.g., "8.5" for shoes)
        - Dimensions (e.g., "M", "L", "10x12" for clothing)
        - From Index column (e.g., "3MD30090914 M 8.5" -> "8.5")
        """
        # First, try to extract from Index column if it exists
        index_fields = ["Index / Gender / Size", "Index", "index"]
        for field in index_fields:
            index_value = item_data.get(field)
            if index_value:
                # Extract size from index (format: "MODEL GENDER SIZE")
                parts = str(index_value).strip().split()
                if len(parts) >= 3:
                    # Size is the last part
                    return parts[-1]
        
        # Try dedicated size fields
        size_fields = ["Size", "size", "Product Size", "Item Size", "Alt Size"]
        for field in size_fields:
            size_value = item_data.get(field)
            if size_value and str(size_value).lower() not in ["nan", "none", "null", ""]:
                return str(size_value).strip()
        
        return None
    
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
