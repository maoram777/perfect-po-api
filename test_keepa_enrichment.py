import asyncio
import logging
from app.services.enrichment_service import local_enrichment_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_keepa_enrichment():
    """Test the Keepa API enrichment functionality."""
    try:
        print("Testing Keepa API enrichment...")
        
        # Test with a sample product
        test_item = {
            "name": "Wireless Bluetooth Headphones",
            "description": "High-quality wireless headphones with noise cancellation",
            "category": "Electronics",
            "brand": "AudioTech",
            "sku": "ATH-BT001",
            "price": 99.99,
            "currency": "USD",
            "quantity": 1,
            "unit": "piece"
        }
        
        print(f"Testing enrichment for: {test_item['name']}")
        
        # Test the Keepa provider directly
        keepa_provider = local_enrichment_service.providers["keepa"]
        enrichment_result = await keepa_provider.enrich_item(test_item)
        
        print(f"\nEnrichment Result:")
        print(f"Status: {enrichment_result.get('enrichment_status')}")
        print(f"Source: {enrichment_result.get('enrichment_source')}")
        
        if enrichment_result.get('enrichment_status') == 'completed':
            enriched_data = enrichment_result.get('enriched_data', {})
            print(f"\nEnriched Data:")
            print(f"Product ID: {enriched_data.get('keepa_product_id')}")
            print(f"Title: {enriched_data.get('keepa_title')}")
            print(f"Price: ${enriched_data.get('keepa_price')}")
            print(f"Rating: {enriched_data.get('keepa_rating')}")
            print(f"Review Count: {enriched_data.get('keepa_review_count')}")
            print(f"Category: {enriched_data.get('keepa_category')}")
            print(f"Brand: {enriched_data.get('keepa_brand')}")
            print(f"Features: {enriched_data.get('keepa_features')}")
            print(f"Amazon URL: {enriched_data.get('keepa_url')}")
            print(f"Status: {enriched_data.get('keepa_status')}")
        else:
            print(f"Enrichment failed: {enrichment_result.get('enrichment_errors')}")
        
        # Test with another product
        test_item2 = {
            "name": "iPhone 13 Case",
            "description": "Protective case for iPhone 13",
            "category": "Accessories",
            "brand": "CasePro",
            "sku": "CP-IP13-001",
            "price": 19.99,
            "currency": "USD",
            "quantity": 1,
            "unit": "piece"
        }
        
        print(f"\n\nTesting enrichment for: {test_item2['name']}")
        enrichment_result2 = await keepa_provider.enrich_item(test_item2)
        
        print(f"Status: {enrichment_result2.get('enrichment_status')}")
        if enrichment_result2.get('enrichment_status') == 'completed':
            enriched_data2 = enrichment_result2.get('enriched_data', {})
            print(f"Product ID: {enriched_data2.get('keepa_product_id')}")
            print(f"Title: {enriched_data2.get('keepa_title')}")
            print(f"Price: ${enriched_data2.get('keepa_price')}")
            print(f"Status: {enriched_data2.get('keepa_status')}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_keepa_enrichment())
