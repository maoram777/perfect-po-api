import asyncio
from app.database import connect_to_mongo, get_database
from bson import ObjectId
from datetime import datetime

async def fix_catalogs():
    await connect_to_mongo()
    db = get_database()
    
    # Find all catalogs that are missing required fields
    catalogs_to_fix = await db.catalogs.find({
        "$or": [
            {"status": {"$exists": False}},
            {"enriched_items": {"$exists": False}},
            {"total_items": {"$exists": False}}
        ]
    }).to_list(None)
    
    print(f'Found {len(catalogs_to_fix)} catalogs that need fixing')
    
    for catalog in catalogs_to_fix:
        catalog_id = catalog["_id"]
        print(f'Fixing catalog: {catalog_id}')
        
        # Prepare update data
        update_data = {}
        
        if "status" not in catalog:
            update_data["status"] = "uploaded"
            print(f'  - Adding status: uploaded')
        
        if "enriched_items" not in catalog:
            update_data["enriched_items"] = 0
            print(f'  - Adding enriched_items: 0')
        
        if "total_items" not in catalog:
            # Try to parse the file to get item count
            try:
                from app.services.aws_service import aws_service
                file_data = await aws_service.get_file_from_s3(catalog.get("file_path", ""))
                if file_data:
                    from app.services.catalog_service import catalog_service
                    line_items = await catalog_service._parse_catalog_file(file_data, catalog.get("file_name", ""))
                    update_data["total_items"] = len(line_items)
                    print(f'  - Adding total_items: {len(line_items)}')
                else:
                    update_data["total_items"] = 0
                    print(f'  - Adding total_items: 0 (file not accessible)')
            except Exception as e:
                update_data["total_items"] = 0
                print(f'  - Adding total_items: 0 (error parsing: {e})')
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            result = await db.catalogs.update_one(
                {"_id": catalog_id},
                {"$set": update_data}
            )
            print(f'  - Updated: {result.modified_count} fields')
        else:
            print(f'  - No updates needed')
    
    print('\nFix completed!')

if __name__ == "__main__":
    asyncio.run(fix_catalogs())
