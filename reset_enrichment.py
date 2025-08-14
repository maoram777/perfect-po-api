import asyncio
from app.database import connect_to_mongo, get_database
from bson import ObjectId

async def reset_enrichment():
    """Reset catalog status and remove all products to allow re-enrichment."""
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
    
    print("\nReset completed! You can now re-run enrichment.")

if __name__ == "__main__":
    asyncio.run(reset_enrichment())
