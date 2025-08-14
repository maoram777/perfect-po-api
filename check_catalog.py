import asyncio
from app.database import connect_to_mongo, get_database
from bson import ObjectId

async def check_catalogs():
    await connect_to_mongo()
    db = get_database()
    catalogs = await db.catalogs.find().to_list(None)
    print(f'Found {len(catalogs)} catalogs')
    for catalog in catalogs:
        print(f'\nCatalog ID: {catalog.get("_id")}')
        print(f'Name: {catalog.get("name")}')
        print(f'User ID: {catalog.get("user_id")}')
        print(f'File Path: {catalog.get("file_path", "MISSING")}')
        print(f'File Name: {catalog.get("file_name", "MISSING")}')
        print(f'File Size: {catalog.get("file_size", "MISSING")}')
        print(f'Total Items: {catalog.get("total_items", "MISSING")}')
        print(f'Status: {catalog.get("status", "MISSING")}')
        print(f'Enriched Items: {catalog.get("enriched_items", "MISSING")}')
        print(f'All fields: {list(catalog.keys())}')

if __name__ == "__main__":
    asyncio.run(check_catalogs())
