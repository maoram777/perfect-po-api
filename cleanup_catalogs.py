import asyncio
from app.database import connect_to_mongo, get_database
from bson import ObjectId

async def cleanup_catalogs():
    await connect_to_mongo()
    db = get_database()
    
    # The catalog ID to keep
    keep_catalog_id = "689bb0651c68fbba607bc43b"
    
    # Find all catalogs
    all_catalogs = await db.catalogs.find().to_list(None)
    print(f'Found {len(all_catalogs)} catalogs in database')
    
    # Show which ones will be deleted
    for catalog in all_catalogs:
        catalog_id = str(catalog["_id"])
        if catalog_id == keep_catalog_id:
            print(f'KEEPING: {catalog_id} - {catalog.get("name", "No name")}')
        else:
            print(f'DELETING: {catalog_id} - {catalog.get("name", "No name")}')
    
    # Delete all catalogs except the one to keep
    result = await db.catalogs.delete_many({
        "_id": {"$ne": ObjectId(keep_catalog_id)}
    })
    
    print(f'\nDeleted {result.deleted_count} catalogs')
    
    # Verify only the target catalog remains
    remaining_catalogs = await db.catalogs.find().to_list(None)
    print(f'Remaining catalogs: {len(remaining_catalogs)}')
    
    for catalog in remaining_catalogs:
        print(f'Remaining: {catalog["_id"]} - {catalog.get("name", "No name")}')
    
    print('\nCleanup completed!')

if __name__ == "__main__":
    asyncio.run(cleanup_catalogs())
