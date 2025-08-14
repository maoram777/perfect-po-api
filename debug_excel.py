import asyncio
import pandas as pd
import io
from app.services.aws_service import aws_service
from app.database import connect_to_mongo, get_database

async def debug_excel_file():
    """Debug the Excel file parsing to see what's actually in the file."""
    await connect_to_mongo()
    db = get_database()
    
    # Get the catalog
    from bson import ObjectId
    catalog = await db.catalogs.find_one({"_id": ObjectId("689bb0651c68fbba607bc43b")})
    if not catalog:
        print("Catalog not found")
        return
    
    print(f"Catalog: {catalog['name']}")
    print(f"File path: {catalog.get('file_path')}")
    print(f"File name: {catalog.get('file_name')}")
    
    try:
        # Get the file from S3
        print("Retrieving file from S3...")
        file_data = await aws_service.get_file_from_s3(catalog["file_path"])
        if not file_data:
            print("Failed to retrieve file from S3")
            return
        
        print(f"File size: {len(file_data)} bytes")
        
        # Try to parse the Excel file
        print("Parsing Excel file...")
        excel_data = io.BytesIO(file_data)
        
        # Read all sheets
        excel_file = pd.ExcelFile(excel_data)
        print(f"Excel sheets: {excel_file.sheet_names}")
        
        # Read the first sheet
        df = pd.read_excel(excel_data, sheet_name=0)
        print(f"DataFrame shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Show first few rows
        print("\nFirst 5 rows:")
        print(df.head())
        
        # Show data types
        print("\nData types:")
        print(df.dtypes)
        
        # Check for null values
        print("\nNull values per column:")
        print(df.isnull().sum())
        
        # Show sample data
        print("\nSample data from first row:")
        first_row = df.iloc[0]
        for col in df.columns:
            print(f"{col}: {first_row[col]} (type: {type(first_row[col])})")
        
    except Exception as e:
        print(f"Error parsing Excel file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_excel_file())
