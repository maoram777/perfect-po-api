import asyncio
from app.database import connect_to_mongo, get_database

async def verify_catalog():
    await connect_to_mongo()
    db = get_database()
    
    catalogs = await db.catalogs.find().to_list(None)
    print(f'Found {len(catalogs)} catalogs in database')
    
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
        
        # Check if all required fields are present
        required_fields = ['file_path', 'file_name', 'file_size', 'total_items', 'status', 'enriched_items']
        missing_fields = [field for field in required_fields if field not in catalog]
        
        if missing_fields:
            print(f'❌ MISSING FIELDS: {missing_fields}')
        else:
            print(f'✅ ALL REQUIRED FIELDS PRESENT')

if __name__ == "__main__":
    asyncio.run(verify_catalog())
