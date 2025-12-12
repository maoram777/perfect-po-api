# Keepa API Request Documentation

## Overview
This document describes the Keepa API request structure used in the Perfect PO API for product enrichment.

## Base URL
```
https://api.keepa.com
```

## Authentication
All requests require a Keepa API key passed as the `key` parameter.

## Domain Configuration
The domain is hardcoded to `1` which represents Amazon.com (US marketplace).

### Domain Values Reference
- `1` = Amazon.com (US) - **Used in this implementation**
- `2` = Amazon.co.uk (UK)
- `3` = Amazon.de (Germany)
- `4` = Amazon.fr (France)
- `5` = Amazon.it (Italy)
- `6` = Amazon.es (Spain)
- `7` = Amazon.ca (Canada)
- `8` = Amazon.com.mx (Mexico)
- `9` = Amazon.in (India)
- `10` = Amazon.co.jp (Japan)

## API Endpoints

### 1. Product Search
**Endpoint:** `/search`

**Method:** `GET`

**Parameters:**
- `key` (string, required): Your Keepa API key
- `domain` (integer, required): Marketplace domain (hardcoded to 1)
- `type` (string, required): Search type - must be `"product"` for product search
- `term` (string, required): Search term (model number, part number, title, etc.)

**Example Request:**
```bash
curl --location 'https://api.keepa.com/search?key=YOUR_API_KEY&domain=1&type=product&term=3MD30090914'
```

**Python Example:**
```python
import httpx

async def search_products(search_term: str, api_key: str):
    async with httpx.AsyncClient() as client:
        search_url = "https://api.keepa.com/search"
        params = {
            "key": api_key,
            "domain": 1,  # Hardcoded to Amazon.com
            "type": "product",  # Required: type=product for product search
            "term": search_term  # Use 'term' parameter
        }
        
        response = await client.get(search_url, params=params, timeout=30.0)
        return response.json()
```

### 2. Product Details
**Endpoint:** `/product`

**Method:** `GET`

**Parameters:**
- `key` (string, required): Your Keepa API key
- `asin` (string, required): Amazon Standard Identification Number(s) (comma-separated for multiple)
- `domain` (integer, required): Marketplace domain (hardcoded to 1)
- `images` (integer, optional): Include image data (default: 1)
- `history` (integer, optional): Include price history (default: 0)
- `offers` (integer, optional): Include offer data (default: 0)

**Example Request:**
```bash
curl --location 'https://api.keepa.com/product?key=YOUR_API_KEY&domain=1&asin=B07B421VFF&images=1&history=0&offers=0'
```

**Python Example:**
```python
async def get_product_details(asin: str, api_key: str):
    async with httpx.AsyncClient() as client:
        product_url = "https://api.keepa.com/product"
        params = {
            "key": api_key,
            "asin": asin,
            "domain": 1,  # Hardcoded to Amazon.com
            "images": 1,
            "history": 0,
            "offers": 0
        }
        
        response = await client.get(product_url, params=params, timeout=30.0)
        return response.json()
```

## Request Headers
```
Content-Type: application/json
User-Agent: Perfect-PO-API/1.0
```

## Rate Limits
- Free tier: 100 requests per month
- Paid tiers: Varies by plan
- Rate limit headers are included in responses

## Error Handling
Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (invalid API key)
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error

## Implementation Notes
1. **Domain Hardcoding**: The domain parameter is hardcoded to `1` (Amazon.com) in all requests
2. **Timeout**: All requests use a 30-second timeout
3. **Error Fallback**: If Keepa API fails, the system falls back to mock data
4. **Image Processing**: Image URLs are constructed from Keepa's `imagesCSV` field
5. **Search Optimization**: Search is limited to 5 results for better performance

## Environment Variables
```bash
KEEPA_API_KEY=your_keepa_api_key_here
```

## Integration in Perfect PO API
The Keepa integration is implemented in:
- `app/services/enrichment_service.py` - Main Keepa API provider
- `app/config.py` - Configuration management
- Product enrichment workflow - Automatic product data enhancement

