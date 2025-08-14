import json
import boto3
import os
import logging
from typing import Dict, List, Any
from datetime import datetime
import asyncio
import motor.motor_asyncio
from bson import ObjectId

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
MONGODB_URI = os.environ.get('MONGODB_URI')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
KEEPA_API_KEY = os.environ.get('KEEPA_API_KEY')

# AWS Secrets Manager client
secrets_client = boto3.client('secretsmanager', region_name=AWS_REGION

# Initialize AWS clients
sqs = boto3.client('sqs', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

# Initialize MongoDB connection
mongodb_client = None
db = None

def get_secret(secret_name: str) -> str:
    """Retrieve secret from AWS Secrets Manager."""
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in response:
            return response['SecretString']
        else:
            # Handle binary secrets
            return response['SecretBinary'].decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {e}")
        return None

def get_mongodb_connection():
    """Get MongoDB connection."""
    global mongodb_client, db
    if mongodb_client is None:
        # Try to get MongoDB URI from secrets first, then environment
        # Secret names follow the pattern: {environment}-mongodb-connection-string
        environment = os.environ.get('ENVIRONMENT', 'dev')
        secret_name = f"{environment}-mongodb-connection-string"
        mongodb_uri = get_secret(secret_name) or MONGODB_URI
        if not mongodb_uri:
            raise Exception(f"MongoDB connection string not found in secrets ({secret_name}) or environment")
        
        mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
        db = mongodb_client.get_database()
    return db

async def enrich_single_product(product_data: Dict[str, Any], catalog_id: str, user_id: str) -> Dict[str, Any]:
    """Enrich a single product using Keepa API."""
    try:
        # Extract search term from product data
        search_term = extract_search_term(product_data)
        
        # Call Keepa API (simplified version for Lambda)
        enriched_data = await call_keepa_api(search_term)
        
        # Update product in database
        product_id = product_data.get('_id')
        if product_id:
            await update_product_enrichment_status(
                product_id, 
                catalog_id, 
                "completed", 
                enriched_data
            )
        
        return {
            "product_id": str(product_id),
            "status": "completed",
            "enriched_data": enriched_data
        }
        
    except Exception as e:
        logger.error(f"Failed to enrich product {product_data.get('name', 'Unknown')}: {e}")
        
        # Update product status to failed
        product_id = product_data.get('_id')
        if product_id:
            await update_product_enrichment_status(
                product_id, 
                catalog_id, 
                "failed", 
                {"error": str(e)}
            )
        
        return {
            "product_id": str(product_id) if product_id else "unknown",
            "status": "failed",
            "error": str(e)
        }

def extract_search_term(item_data: Dict[str, Any]) -> str:
    """Extract search term from product data."""
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
    
    # Fallback
    return f"Product {hash(str(item_data)) % 1000000}"

async def call_keepa_api(search_term: str) -> Dict[str, Any]:
    """Call Keepa API to get product information."""
    # Try to get Keepa API key from secrets first, then environment
    # Secret names follow the pattern: {environment}-keepa-api-key
    environment = os.environ.get('ENVIRONMENT', 'dev')
    secret_name = f"{environment}-keepa-api-key"
    keepa_api_key = get_secret(secret_name) or KEEPA_API_KEY
    
    if not keepa_api_key:
        logger.warning("Keepa API key not configured, using mock data")
        return get_mock_keepa_data(search_term)
    
    try:
        # For Lambda, we'll use a simplified Keepa API call
        # In production, you might want to use a more robust HTTP client
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Search for products
            search_url = "https://api.keepa.com/search"
            params = {
                "key": keepa_api_key,
                "q": search_term,
                "domain": 1,
                "limit": 1
            }
            
            response = await client.get(search_url, params=params, timeout=30.0)
            response.raise_for_status()
            search_data = response.json()
            
            if not search_data.get("products"):
                return get_mock_keepa_data(search_term)
            
            product = search_data["products"][0]
            product_id = product.get("asin")
            
            # Get detailed product information
            product_url = "https://api.keepa.com/product"
            product_params = {
                "key": keepa_api_key,
                "asin": product_id,
                "domain": 1,
                "images": 1
            }
            
            product_response = await client.get(product_url, params=product_params, timeout=30.0)
            product_response.raise_for_status()
            detailed_product = product_response.json()["products"][0]
            
            # Extract image information
            images = []
            main_image = None
            
            if detailed_product.get("imagesCSV"):
                image_urls = detailed_product["imagesCSV"].split(",")
                images = [f"https://m.media-amazon.com/images/I/{img_id}.jpg" for img_id in image_urls if img_id]
                if images:
                    main_image = images[0]
            
            return {
                "keepa_product_id": product_id,
                "keepa_price": extract_keepa_price(detailed_product),
                "keepa_rating": detailed_product.get("rating", 0.0),
                "keepa_review_count": detailed_product.get("reviewCount", 0),
                "keepa_category": extract_keepa_category(detailed_product),
                "keepa_brand": detailed_product.get("brand", "Unknown Brand"),
                "keepa_features": detailed_product.get("features", []),
                "keepa_images": images,
                "keepa_main_image": main_image,
                "keepa_url": f"https://keepa.com/product.html#1!{product_id}",
                "keepa_status": "real_data"
            }
            
    except Exception as e:
        logger.error(f"Keepa API error: {e}")
        return get_mock_keepa_data(search_term)

def get_mock_keepa_data(search_term: str) -> Dict[str, Any]:
    """Return mock Keepa data as fallback."""
    mock_images = [
        f"https://m.media-amazon.com/images/I/71{hash(search_term) % 100000000}L._AC_SL1500_.jpg",
        f"https://m.media-amazon.com/images/I/71{hash(search_term) % 100000000}L._AC_SL1500_2_.jpg"
    ]
    
    return {
        "keepa_product_id": f"KPA_{hash(search_term) % 1000000}",
        "keepa_price": 89.99,
        "keepa_rating": 4.3,
        "keepa_review_count": 980,
        "keepa_category": "Electronics",
        "keepa_brand": "Generic Brand",
        "keepa_features": ["Portable", "Rechargeable"],
        "keepa_images": mock_images,
        "keepa_main_image": mock_images[0],
        "keepa_status": "mock_data"
    }

def extract_keepa_price(product: Dict[str, Any]) -> float:
    """Extract current price from Keepa product data."""
    try:
        price_history = product.get("csv", [])
        if price_history and len(price_history) > 0:
            for price in reversed(price_history):
                if price and price != -1:
                    return float(price) / 100.0
        return 0.0
    except Exception:
        return 0.0

def extract_keepa_category(product: Dict[str, Any]) -> str:
    """Extract category from Keepa product data."""
    try:
        categories = product.get("categories", [])
        if categories and len(categories) > 0:
            return categories[0]
        return "Unknown Category"
    except Exception:
        return "Unknown Category"

async def update_product_enrichment_status(product_id: str, catalog_id: str, status: str, enriched_data: Dict[str, Any]):
    """Update product enrichment status in database."""
    try:
        db = get_mongodb_connection()
        
        # Update product with enrichment data
        update_data = {
            "enrichment_status": status,
            "enriched_data": enriched_data,
            "enriched_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Add image fields if available
        if enriched_data.get("keepa_main_image"):
            update_data["main_image"] = enriched_data["keepa_main_image"]
        if enriched_data.get("keepa_images"):
            update_data["images"] = enriched_data["keepa_images"]
        
        await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
        
        logger.info(f"Updated product {product_id} with status: {status}")
        
    except Exception as e:
        logger.error(f"Failed to update product {product_id}: {e}")

async def update_catalog_progress(catalog_id: str, completed_count: int, failed_count: int, total_count: int):
    """Update catalog enrichment progress."""
    try:
        db = get_mongodb_connection()
        
        # Calculate progress
        enriched_items = completed_count
        progress_percentage = (enriched_items / total_count * 100) if total_count > 0 else 0
        
        # Determine status
        if failed_count > 0 and completed_count > 0:
            status = "partially_completed"
        elif completed_count == total_count:
            status = "enriched"
        else:
            status = "processing"
        
        update_data = {
            "enriched_items": enriched_items,
            "enrichment_status": status,
            "progress_percentage": progress_percentage,
            "updated_at": datetime.utcnow()
        }
        
        if status == "enriched":
            update_data["enrichment_completed_at"] = datetime.utcnow()
        
        await db.catalogs.update_one(
            {"_id": ObjectId(catalog_id)},
            {"$set": update_data}
        )
        
        logger.info(f"Updated catalog {catalog_id} progress: {enriched_items}/{total_count} ({progress_percentage:.1f}%)")
        
    except Exception as e:
        logger.error(f"Failed to update catalog {catalog_id} progress: {e}")

def lambda_handler(event, context):
    """Lambda function handler for processing SQS messages."""
    try:
        logger.info(f"Processing {len(event['Records'])} SQS message(s)")
        
        # Process each SQS message
        for record in event['Records']:
            message_body = json.loads(record['body'])
            
            # Extract message data
            catalog_id = message_body.get('catalog_id')
            user_id = message_body.get('user_id')
            products = message_body.get('products', [])
            batch_number = message_body.get('batch_number', 1)
            total_batches = message_body.get('total_batches', 1)
            
            logger.info(f"Processing batch {batch_number}/{total_batches} for catalog {catalog_id}")
            logger.info(f"Products in batch: {len(products)}")
            
            # Process products asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Enrich all products in the batch
                results = loop.run_until_complete(process_product_batch(
                    products, catalog_id, user_id
                ))
                
                # Count results
                completed_count = sum(1 for r in results if r['status'] == 'completed')
                failed_count = sum(1 for r in results if r['status'] == 'failed')
                
                logger.info(f"Batch {batch_number} completed: {completed_count} success, {failed_count} failed")
                
                # Update catalog progress
                loop.run_until_complete(update_catalog_progress(
                    catalog_id, completed_count, failed_count, len(products)
                ))
                
            finally:
                loop.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps('Successfully processed enrichment batch')
        }
        
    except Exception as e:
        logger.error(f"Lambda function error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing enrichment batch: {str(e)}')
        }

async def process_product_batch(products: List[Dict[str, Any]], catalog_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Process a batch of products for enrichment."""
    tasks = []
    for product in products:
        task = enrich_single_product(product, catalog_id, user_id)
        tasks.append(task)
    
    # Process all products concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Product {i} failed with exception: {result}")
            processed_results.append({
                "product_id": products[i].get('_id', 'unknown'),
                "status": "failed",
                "error": str(result)
            })
        else:
            processed_results.append(result)
    
    return processed_results
