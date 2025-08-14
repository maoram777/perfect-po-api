import asyncio
from app.database import connect_to_mongo, get_database
from bson import ObjectId

async def reset_for_image_enrichment():
    """Clear old products and reset catalog status for new image enrichment."""
    await connect_to_mongo()
    db = get_database()
    
    # Reset catalog status back to "uploaded"
    catalog_id = "689bb0651c68fbba607bc43b"
    result = await db.catalogs.update_one(
        {"_id": ObjectId(catalog_id)},
        {
            "$set": {
                "status": "uploaded",
                "enriched_items": 0,
                "enrichment_started_at": None,
                "enrichment_completed_at": None,
                "updated_at": asyncio.get_event_loop().time()
            }
        }
    )
    
    print(f"Catalog status reset: {result.modified_count} fields updated")
    
    # Remove all products from the products collection
    products_result = await db.products.delete_many({})
    print(f"Products removed: {products_result.deleted_count} products deleted")
    
    # Verify the reset
    catalog = await db.catalogs.find_one({"_id": ObjectId(catalog_id)})
    if catalog:
        print(f"\nCatalog status: {catalog.get('status')}")
        print(f"Enriched items: {catalog.get('enriched_items')}")
        print(f"Total items: {catalog.get('total_items')}")
    
    # Check products collection
    product_count = await db.products.count_documents({})
    print(f"Remaining products: {product_count}")
    
    print("\n✅ Reset completed! You can now run new enrichment with image support.")
    print("\n📸 New enrichment will include:")
    print("   - main_image field (primary product image)")
    print("   - images field (list of all product images)")
    print("   - Real Keepa API images (if API key configured)")
    print("   - Fallback mock images (if no API key)")

if __name__ == "__main__":
    asyncio.run(reset_for_image_enrichment())
