#!/usr/bin/env python3
"""
Test script for local enrichment functionality
"""
import asyncio
import httpx
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

async def test_enrichment_flow():
    """Test the complete enrichment flow."""
    
    async with httpx.AsyncClient() as client:
        print("🚀 Testing Perfect PO API Local Enrichment")
        print("=" * 50)
        
        # 1. Register a test user
        print("\n1. Registering test user...")
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "testpassword123"
        }
        
        response = await client.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code == 200:
            print("✅ User registered successfully")
        else:
            print(f"❌ User registration failed: {response.text}")
            return
        
        # 2. Login to get JWT token
        print("\n2. Logging in...")
        login_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        
        response = await client.post(f"{BASE_URL}/auth/login", data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {response.text}")
            return
        
        # Set authorization header
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 3. Get available enrichment providers
        print("\n3. Getting available enrichment providers...")
        response = await client.get(f"{BASE_URL}/catalogs/providers", headers=headers)
        if response.status_code == 200:
            providers = response.json()
            print(f"✅ Available providers: {providers['providers']}")
        else:
            print(f"❌ Failed to get providers: {response.text}")
            return
        
        # 4. Upload a test catalog
        print("\n4. Uploading test catalog...")
        catalog_data = {
            "name": "Test Electronics Catalog",
            "description": "Test catalog for enrichment",
            "category": "Electronics"
        }
        
        # Create a more realistic catalog file content based on your Excel examples
        csv_content = """Product Name,Description,Category,Brand,SKU,Price,Currency,Quantity,Unit,UPC
Wireless Bluetooth Headphones,High-quality wireless headphones with noise cancellation,Electronics,AudioTech,ATH-BT001,99.99,USD,1,piece,123456789012
Smartphone Case,Protective case for smartphones with kickstand,Accessories,CasePro,CP-SC001,19.99,USD,1,piece,234567890123
USB-C Cable,Fast charging USB-C cable 3.1 Gen 2,Cables,CableMax,CM-UC001,12.99,USD,2,piece,345678901234
Gaming Mouse,RGB gaming mouse with adjustable DPI,Gaming,GameTech,GT-GM001,79.99,USD,1,piece,456789012345
Mechanical Keyboard,Cherry MX Blue switches mechanical keyboard,Gaming,GameTech,GT-MK001,149.99,USD,1,piece,567890123456"""
        
        files = {
            "file": ("test_catalog.csv", csv_content, "text/csv"),
            "name": (None, catalog_data["name"]),
            "description": (None, catalog_data["description"]),
            "category": (None, catalog_data["category"])
        }
        
        response = await client.post(f"{BASE_URL}/catalogs/upload", files=files, headers=headers)
        if response.status_code == 200:
            catalog = response.json()
            catalog_id = catalog["id"]
            print(f"✅ Catalog uploaded successfully: {catalog_id}")
        else:
            print(f"❌ Catalog upload failed: {response.text}")
            return
        
        # 5. Test enrichment with Amazon provider
        print("\n5. Testing enrichment with Amazon provider...")
        response = await client.post(
            f"{BASE_URL}/catalogs/{catalog_id}/enrich?provider=amazon",
            headers=headers
        )
        if response.status_code == 200:
            enrichment_result = response.json()
            print(f"✅ Amazon enrichment completed:")
            print(f"   - Total items: {enrichment_result['total_items']}")
            print(f"   - Enriched items: {enrichment_result['enriched_items']}")
            print(f"   - Failed items: {enrichment_result['failed_items']}")
            print(f"   - Status: {enrichment_result['status']}")
        else:
            print(f"❌ Amazon enrichment failed: {response.text}")
            return
        
        # 6. Test enrichment with Keepa provider
        print("\n6. Testing enrichment with Keepa provider...")
        response = await client.post(
            f"{BASE_URL}/catalogs/{catalog_id}/enrich?provider=keepa",
            headers=headers
        )
        if response.status_code == 200:
            enrichment_result = response.json()
            print(f"✅ Keepa enrichment completed:")
            print(f"   - Total items: {enrichment_result['total_items']}")
            print(f"   - Enriched items: {enrichment_result['enriched_items']}")
            print(f"   - Failed items: {enrichment_result['failed_items']}")
            print(f"   - Status: {enrichment_result['status']}")
        else:
            print(f"❌ Keepa enrichment failed: {response.text}")
        
        # 7. Get enriched products
        print("\n7. Getting enriched products...")
        response = await client.get(f"{BASE_URL}/products?catalog_id={catalog_id}", headers=headers)
        if response.status_code == 200:
            products = response.json()
            print(f"✅ Found {len(products)} products")
            for i, product in enumerate(products[:3]):  # Show first 3 products
                print(f"   Product {i+1}: {product['name']} - {product['enrichment_status']}")
        else:
            print(f"❌ Failed to get products: {response.text}")
        
        # 8. Get catalog products summary
        print("\n8. Getting catalog products summary...")
        response = await client.get(f"{BASE_URL}/products/catalog/{catalog_id}/summary", headers=headers)
        if response.status_code == 200:
            summary = response.json()
            print(f"✅ Catalog summary:")
            print(f"   - Total products: {summary['total_products']}")
            print(f"   - Status summary: {summary['status_summary']}")
        else:
            print(f"❌ Failed to get summary: {response.text}")
        
        # 9. Generate offers for the catalog
        print("\n9. Generating offers for the catalog...")
        response = await client.post(
            f"{BASE_URL}/offers/generate?catalog_id={catalog_id}&offer_type=all&max_offers=3",
            headers=headers
        )
        if response.status_code == 200:
            offer_result = response.json()
            print(f"✅ Offers generated successfully:")
            print(f"   - Total offers: {len(offer_result['offers'])}")
            print(f"   - Offer types: {offer_result['offer_type']}")
            for i, offer in enumerate(offer_result['offers'][:3]):  # Show first 3 offers
                print(f"   - Offer {i+1}: {offer['name']} - {offer['total_discount']}% off")
        else:
            print(f"❌ Failed to generate offers: {response.text}")
        
        # 10. Get offers summary
        print("\n10. Getting offers summary...")
        response = await client.get(f"{BASE_URL}/offers/catalog/{catalog_id}/summary", headers=headers)
        if response.status_code == 200:
            offers_summary = response.json()
            print(f"✅ Offers summary:")
            print(f"   - Total offers: {offers_summary['total_offers']}")
            print(f"   - Total savings: ${offers_summary['total_savings']}")
            print(f"   - Average discount: {offers_summary['average_discount']}%")
            print(f"   - Best offer score: {offers_summary['best_offer_score']}")
        else:
            print(f"❌ Failed to get offers summary: {response.text}")
        
        print("\n" + "=" * 50)
        print("🎉 Complete testing completed!")
        print(f"📊 Check the API docs at: {BASE_URL}/docs")
        print(f"🔍 View products at: {BASE_URL}/products")
        print(f"💰 View offers at: {BASE_URL}/offers")

if __name__ == "__main__":
    print("Make sure the API is running on http://localhost:8000")
    print("Run: python run.py")
    print()
    
    try:
        asyncio.run(test_enrichment_flow())
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Make sure the API is running and accessible")
