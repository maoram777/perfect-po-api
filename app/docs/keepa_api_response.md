# Keepa API Response Documentation

## Overview
This document describes the Keepa API response structure and how it's processed in the Perfect PO API.

## Response Structure

### Search Response
```json
{
  "products": [
    {
      "asin": "B07B421VFF",
      "title": "Product Title",
      "brand": "Brand Name",
      "imagesCSV": "image1.jpg,image2.jpg,image3.jpg",
      "rating": 4.5,
      "reviewCount": 1234,
      "category": "Electronics",
      "features": ["Feature 1", "Feature 2"],
      "csv": [price_history_array],
      "lastUpdate": 1640995200000
    }
  ],
  "lastUpdate": 1640995200000
}
```

### Product Details Response
```json
{
  "products": [
    {
      "asin": "B07B421VFF",
      "title": "New Balance Men's 608 V5 Casual Comfort Cross Trainer",
      "brand": "New Balance",
      "imagesCSV": "61p6oqRqYQL.jpg,51DdRtBcpJL.jpg,71yf0AzQiAL.jpg",
      "rating": 4.3,
      "reviewCount": 2156,
      "category": "Shoes",
      "features": ["Comfortable", "Durable", "Breathable"],
      "csv": [price_history_data],
      "lastUpdate": 1640995200000,
      "availability": 1,
      "isPrime": true,
      "isAmazon": true
    }
  ],
  "lastUpdate": 1640995200000
}
```

## Field Descriptions

### Core Product Fields
- `asin` (string): Amazon Standard Identification Number
- `title` (string): Product title/name
- `brand` (string): Product brand
- `category` (string): Product category
- `rating` (float): Average customer rating (0-5)
- `reviewCount` (integer): Number of customer reviews
- `features` (array): List of product features
- `lastUpdate` (integer): Last update timestamp (Unix milliseconds)

### Image Fields
- `imagesCSV` (string): Comma-separated list of image IDs
- Image URLs are constructed as: `https://m.media-amazon.com/images/I/{image_id}.jpg`

### Price and Availability
- `csv` (array): Price history data
- `availability` (integer): Product availability status
- `isPrime` (boolean): Amazon Prime availability
- `isAmazon` (boolean): Sold by Amazon

## Data Processing in Perfect PO API

### Image Processing
```python
def process_keepa_images(images_csv: str) -> dict:
    """Process Keepa imagesCSV into usable image URLs."""
    if not images_csv:
        return {"images": [], "main_image": None}
    
    image_ids = [img.strip() for img in images_csv.split(",") if img.strip()]
    images = [f"https://m.media-amazon.com/images/I/{img_id}.jpg" for img_id in image_ids]
    
    return {
        "images": images,
        "main_image": images[0] if images else None
    }
```

### Price Extraction
```python
def extract_keepa_price(product: dict) -> float:
    """Extract current price from Keepa product data."""
    price_history = product.get("csv", [])
    if price_history and len(price_history) > 0:
        # Get the most recent non-zero price
        for price in reversed(price_history):
            if price and price > 0:
                return price / 100.0  # Keepa prices are in cents
    return 0.0
```

### Category Mapping
```python
def extract_keepa_category(product: dict) -> str:
    """Extract and map Keepa category to our system."""
    category = product.get("category", "Unknown")
    # Map Keepa categories to our internal categories
    category_mapping = {
        "Shoes": "Footwear",
        "Electronics": "Electronics",
        "Clothing": "Apparel",
        # Add more mappings as needed
    }
    return category_mapping.get(category, category)
```

## Enriched Data Structure
The Keepa response is transformed into our enriched data format:

```json
{
  "enrichment_source": "keepa_api",
  "enrichment_status": "completed",
  "enriched_data": {
    "keepa_product_id": "B07B421VFF",
    "keepa_price": 89.99,
    "keepa_rating": 4.3,
    "keepa_review_count": 2156,
    "keepa_category": "Footwear",
    "keepa_brand": "New Balance",
    "keepa_features": ["Comfortable", "Durable"],
    "keepa_images": [
      "https://m.media-amazon.com/images/I/61p6oqRqYQL.jpg",
      "https://m.media-amazon.com/images/I/51DdRtBcpJL.jpg"
    ],
    "keepa_main_image": "https://m.media-amazon.com/images/I/61p6oqRqYQL.jpg",
    "keepa_url": "https://keepa.com/product.html#1!B07B421VFF",
    "keepa_status": "real_data"
  },
  "enriched_at": "2024-01-15T10:30:00Z"
}
```

## Error Response Format
```json
{
  "error": "Invalid API key",
  "code": 401,
  "message": "Unauthorized access"
}
```

## Mock Data Fallback
When Keepa API is unavailable, the system uses mock data:

```json
{
  "keepa_product_id": "KPA_123456",
  "keepa_price": 89.99,
  "keepa_rating": 4.3,
  "keepa_review_count": 980,
  "keepa_category": "Electronics",
  "keepa_brand": "Generic Brand",
  "keepa_features": ["Portable", "Rechargeable"],
  "keepa_images": ["https://m.media-amazon.com/images/I/71ABC123L._AC_SL1500_.jpg"],
  "keepa_main_image": "https://m.media-amazon.com/images/I/71ABC123L._AC_SL1500_.jpg",
  "keepa_status": "mock_data"
}
```

## Integration Notes
1. **Domain**: All responses are from domain=1 (Amazon.com)
2. **Image URLs**: Constructed from Keepa's image IDs
3. **Price Format**: Prices are converted from cents to dollars
4. **Error Handling**: Graceful fallback to mock data
5. **Caching**: Responses can be cached for performance
6. **Rate Limiting**: Respects Keepa's rate limits




