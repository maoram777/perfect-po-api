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
        """Extract UPC from item data."""
        # Common UPC field names from CSV
        upc_fields = ["UPC", "upc", "UPC Code", "upc_code", "product_upc", "item_upc", "barcode"]
        
        for field in upc_fields:
            upc_value = item_data.get(field)
            if upc_value:
                # Clean the UPC value (remove spaces, ensure it's a string)
                upc_str = str(upc_value).strip()
                # Remove any non-digit characters if present
                upc_clean = ''.join(filter(str.isdigit, upc_str))
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
        if not images and detailed_product.get("imag    to esCSV"):
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
        
        # Build response data
        response_data = {
            "keepa_product_id": detailed_product.get("asin", ""),
            "keepa_price": self._extract_keepa_price(detailed_product),
            "keepa_rating": rating,
            "keepa_review_count": review_count,
            "keepa_category": category,
            "keepa_brand": detailed_product.get("brand", "Unknown Brand"),
            "keepa_color": detailed_product.get("color", ""),
            "keepa_features": detailed_product.get("features", []),
            "keepa_images": images,
            "keepa_main_image": main_image,
            "keepa_url": f"https://keepa.com/product.html#1!{detailed_product.get('asin', '')}",
            "keepa_status": "real_data",
            "keepa_title": detailed_product.get("title", ""),
            "keepa_description": detailed_product.get("description", ""),
            "keepa_manufacturer": detailed_product.get("manufacturer", "Unknown Manufacturer"),
            "keepa_model": detailed_product.get("model", ""),
            "keepa_part_number": detailed_product.get("partNumber", ""),
            "keepa_size": detailed_product.get("size", ""),
            "keepa_style": detailed_product.get("style", ""),
            "keepa_upc_list": detailed_product.get("upcList", []),
            "keepa_ean_list": detailed_product.get("eanList", [])
        }
        
        # Add identifier-specific fields
        if identifier_type == "upc":
            response_data["keepa_upc"] = identifier
        elif identifier_type == "asin":
            response_data["keepa_asin"] = identifier
        elif identifier_type == "search":
            response_data["keepa_search_term"] = identifier
        
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
                    "images": 1,  # Include image data (per docs)
                    "history": 0,  # Don't include price history (per docs)
                    "offers": 0   # Don't include offer data (per docs)
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
            "keepa_product_id": f"KPA_{hash(upc) % 1000000}",
            "keepa_price": 89.99,
            "keepa_rating": 4.3,
            "keepa_review_count": 980,
            "keepa_category": "Electronics",
            "keepa_brand": "Generic Brand",
            "keepa_color": "Black",
            "keepa_features": ["Portable", "Rechargeable", "Fast Charging"],
            "keepa_images": mock_images,
            "keepa_main_image": mock_images[0],
            "keepa_url": f"https://keepa.com/product.html#1!{hash(upc) % 1000000}",
            "keepa_upc": upc,
            "keepa_status": "mock_data",
            "keepa_title": f"Mock Product {upc}",
            "keepa_manufacturer": "Mock Manufacturer",
            "keepa_model": f"MODEL_{hash(upc) % 10000}",
            "keepa_part_number": f"PN_{hash(upc) % 10000}",
            "keepa_upc_list": [upc]
        }
    
    def _extract_keepa_price(self, product: Dict[str, Any]) -> Optional[float]:
        """Extract current price from Keepa product data.
        
        According to Keepa API documentation and actual response structure:
        - The csv array contains multiple arrays, each representing different data types
        - Index 0: Amazon price history as [timestamp, price, timestamp, price, ...]
        - Index 1: New price history (same format)
        - Prices are stored in cents, -1 means no data available
        - We want the most recent price from the Amazon price history (index 0)
        """
        try:
            # Keepa stores price history in csv array
            # csv[0] = Amazon price history: [timestamp1, price1, timestamp2, price2, ...]
            # csv[1] = New price history: [timestamp1, price1, timestamp2, price2, ...]
            # Prices are in cents, -1 means no data
            price_history = product.get("csv", [])
            
            if not price_history or len(price_history) == 0:
                return None
            
            # Get Amazon price history (first array, index 0)
            amazon_price_array = price_history[0] if len(price_history) > 0 else None
            
            if not amazon_price_array or not isinstance(amazon_price_array, list):
                return None
            
            # The array contains pairs: [timestamp, price, timestamp, price, ...]
            # We want the most recent (last) price, so iterate backwards
            # Start from the end and look for the last valid price
            for i in range(len(amazon_price_array) - 1, 0, -2):  # Step by 2, starting from last price
                if i >= 1:  # Ensure we have both timestamp and price
                    price = amazon_price_array[i]
                    if price is not None and price != -1 and price > 0:
                        # Keepa prices are in cents, convert to dollars
                        return float(price) / 100.0
            
            # If no Amazon price found, try New price history (index 1)
            if len(price_history) > 1:
                new_price_array = price_history[1]
                if isinstance(new_price_array, list) and len(new_price_array) >= 2:
                    for i in range(len(new_price_array) - 1, 0, -2):
                        if i >= 1:
                            price = new_price_array[i]
                            if price is not None and price != -1 and price > 0:
                                return float(price) / 100.0
            
            return None
        except Exception as e:
            logger.warning(f"Error extracting price from Keepa product: {e}")
            return None
    
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
                logger.info(f"Debug: Looking for keepa_main_image: {enrichment_result['enriched_data'].get('keepa_main_image')}")
                logger.info(f"Debug: Looking for keepa_images: {enrichment_result['enriched_data'].get('keepa_images')}")
            
            # Extract image fields from enrichment based on provider
            enrichment_source = enrichment_result.get("enrichment_source", "")
            enriched_data = enrichment_result.get("enriched_data", {})
            
            if "keepa" in enrichment_source.lower():
                # Keepa provider
                main_image = self._extract_image_from_enrichment(enrichment_result, "keepa_main_image")
                images = self._extract_images_from_enrichment(enrichment_result, "keepa_images")
                # Use Keepa color if available, otherwise fall back to Excel
                color = self._extract_single_color(enriched_data.get("keepa_color") or self._extract_colors_from_excel(item_data))
            elif "amazon" in enrichment_source.lower():
                # Amazon provider
                main_image = self._extract_image_from_enrichment(enrichment_result, "amazon_images")
                images = self._extract_images_from_enrichment(enrichment_result, "amazon_images")
                color = self._extract_single_color(self._extract_colors_from_excel(item_data))
            else:
                # Unknown provider, try both
                main_image = self._extract_image_from_enrichment(enrichment_result, "keepa_main_image") or self._extract_image_from_enrichment(enrichment_result, "amazon_images")
                images = self._extract_images_from_enrichment(enrichment_result, "keepa_images") or self._extract_images_from_enrichment(enrichment_result, "amazon_images")
                color = self._extract_single_color(enriched_data.get("keepa_color") or self._extract_colors_from_excel(item_data))
            
            # Extract size from Index column or other sources
            size = self._extract_size_from_item_data(item_data)
            
            # Extract pricing fields for PO score calculation
            whs = self._extract_numeric_field(item_data, ["WHS", "whs", "Warehouse Price", "warehouse_price", "warehouse", "cost_price"])
            msrp = self._extract_numeric_field(item_data, ["MSRP", "msrp", "Manufacturer Recommended Retail Price", "RRP", "rrp", "Retail Price", "retail_price", "list_price"])
            offer = self._extract_numeric_field(item_data, ["Offer Price", "offer_price", "offer", "Offer", "Price", "price", "selling_price"])
            
            # Calculate PO score if we have the required fields
            po_score = self.calculate_po_score(whs, msrp, offer)
            
            # Validate MSRP against enriched price from external API
            # Get enriched price from Keepa or Amazon
            enriched_price = None
            if "keepa" in enrichment_source.lower():
                enriched_price = enriched_data.get("keepa_price")
            elif "amazon" in enrichment_source.lower():
                enriched_price = enriched_data.get("amazon_price")
            else:
                # Try both if source is unknown
                enriched_price = enriched_data.get("keepa_price") or enriched_data.get("amazon_price")
            
            # Validate MSRP (within 5% delta)
            msrp_validated = self.validate_msrp(msrp, enriched_price, delta_percent=5.0)
            
            product_data = {
                "catalog_id": ObjectId(catalog_id),
                "user_id": ObjectId(user_id),
                "line_item_id": f"item_{index}",
                "name": self._extract_field_value(item_data, ["Article Name", "Style Name", "name", "product_name", "item_name", "title", "product_title"], f"Item {index}"),
                "description": self._create_description_from_excel(item_data),
                "category": self._extract_field_value(item_data, ["Category", "Subcategory", "Division", "category", "product_category", "item_category", "type", "product_type"]),
                "brand": self._extract_field_value(item_data, ["brand", "product_brand", "item_brand", "manufacturer", "make"]),
                "sku": self._extract_field_value(item_data, ["Article Number", "SKU", "sku", "product_sku", "item_sku", "product_code", "item_code"]),
                "upc": self._extract_field_value(item_data, ["UPC", "upc", "product_upc", "item_upc", "barcode", "ean"]),
                "price": self._extract_numeric_field(item_data, ["Offer Price", "Wholesale", "RRP", "price", "product_price", "item_price", "cost", "unit_price"]),
                "currency": self._extract_field_value(item_data, ["Currency", "currency", "product_currency", "item_currency"], "USD"),
                "quantity": self._extract_numeric_field(item_data, ["Inventory", "Quantity Available", "quantity", "product_quantity", "item_quantity", "qty", "stock"]),
                "unit": self._extract_field_value(item_data, ["unit", "product_unit", "item_unit", "uom", "measurement_unit"], "piece"),
                "color": color,  # Single color (not array)
                "size": size,  # Size - can be number (shoes) or dimensions (clothing)
                "original_data": item_data,
                # Add image fields from enrichment
                "main_image": main_image,
                "images": images,
                "enriched_data": enriched_data,
                "enrichment_source": enrichment_result.get("enrichment_source"),
                "enrichment_status": enrichment_result.get("enrichment_status"),
                "enrichment_errors": enrichment_result.get("enrichment_errors", []),
                "enriched_at": enrichment_result.get("enriched_at"),
                "po_score": po_score,  # Purchase Order score (calculated from whs, msrp, offer)
                "msrp_validated": msrp_validated,  # True if source MSRP is within 5% of enriched price
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
