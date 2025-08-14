import csv
import io
import json
from typing import List, Dict, Any, Optional
from bson import ObjectId
from datetime import datetime
from ..database import get_database
from ..models.catalog import Catalog, CatalogCreate, CatalogUpdate
from ..models.product import Product, ProductCreate
from ..services.aws_service import aws_service
import logging

logger = logging.getLogger(__name__)


class CatalogService:
    def __init__(self):
        self._db = None

    @property
    def db(self):
        if self._db is None:
            self._db = get_database()
        return self._db

    async def create_catalog(
        self, 
        catalog_data: CatalogCreate, 
        user_id: str,
        file_data: bytes,
        file_name: str
    ) -> Catalog:
        """Create a new catalog and upload file to S3."""
        try:
            # Create catalog document
            # Handle both Pydantic v1 and v2
            try:
                catalog_dict = catalog_data.model_dump()
            except AttributeError:
                catalog_dict = catalog_data.dict()
            catalog_dict["user_id"] = ObjectId(user_id)
            catalog_dict["file_name"] = file_name
            catalog_dict["file_size"] = len(file_data)
            catalog_dict["status"] = "uploaded"  # Set default status
            catalog_dict["enriched_items"] = 0   # Set default enriched items
            catalog_dict["created_at"] = datetime.utcnow()
            catalog_dict["updated_at"] = datetime.utcnow()
            
            # Insert catalog into database
            result = await self.db.catalogs.insert_one(catalog_dict)
            catalog_dict["_id"] = result.inserted_id
            
            # Upload file to S3
            file_path = await aws_service.upload_file_to_s3(
                file_data, file_name, user_id, str(result.inserted_id)
            )
            
            # Update catalog with S3 file path
            await self.db.catalogs.update_one(
                {"_id": result.inserted_id},
                {"$set": {"file_path": file_path}}
            )
            
            # Process file to count line items
            line_items = await self._parse_catalog_file(file_data, file_name)
            total_items = len(line_items)
            
            # Update catalog with item count
            await self.db.catalogs.update_one(
                {"_id": result.inserted_id},
                {"$set": {"total_items": total_items}}
            )
            
            # Fetch the updated catalog from database to ensure all fields are present
            updated_catalog = await self.db.catalogs.find_one({"_id": result.inserted_id})
            if updated_catalog:
                return Catalog(**updated_catalog)
            else:
                raise Exception("Failed to retrieve created catalog from database")
            
        except Exception as e:
            logger.error(f"Error creating catalog: {e}")
            raise Exception(f"Failed to create catalog: {e}")
    
    async def get_user_catalogs(self, user_id: str, limit: int = 100, skip: int = 0, status: Optional[str] = None) -> List[Catalog]:
        """Get all catalogs for a specific user with optional filtering and pagination."""
        try:
            # Build filter query
            filter_query = {"user_id": ObjectId(user_id)}
            if status:
                filter_query["status"] = status
            
            # Apply pagination and filtering
            cursor = self.db.catalogs.find(filter_query).skip(skip).limit(limit)
            catalogs = []
            async for catalog in cursor:
                catalogs.append(Catalog(**catalog))
            return catalogs
        except Exception as e:
            logger.error(f"Error fetching user catalogs: {e}")
            raise Exception(f"Failed to fetch catalogs: {e}")
    
    async def get_catalog_by_id(self, catalog_id: str, user_id: str) -> Optional[Catalog]:
        """Get a specific catalog by ID for a user."""
        try:
            catalog = await self.db.catalogs.find_one({
                "_id": ObjectId(catalog_id),
                "user_id": ObjectId(user_id)
            })
            return Catalog(**catalog) if catalog else None
        except Exception as e:
            logger.error(f"Error fetching catalog: {e}")
            raise Exception(f"Failed to fetch catalog: {e}")
    
    async def update_catalog(
        self, 
        catalog_id: str, 
        user_id: str, 
        update_data: CatalogUpdate
    ) -> Optional[Catalog]:
        """Update catalog information."""
        try:
            # Handle both Pydantic v1 and v2
            try:
                update_dict = update_data.model_dump(exclude_unset=True)
            except AttributeError:
                update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()
            
            result = await self.db.catalogs.update_one(
                {"_id": ObjectId(catalog_id), "user_id": ObjectId(user_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                return await self.get_catalog_by_id(catalog_id, user_id)
            return None
            
        except Exception as e:
            logger.error(f"Error updating catalog: {e}")
            raise Exception(f"Failed to update catalog: {e}")
    
    async def delete_catalog(self, catalog_id: str, user_id: str) -> bool:
        """Delete a catalog and its associated file."""
        try:
            # Get catalog to find file path
            catalog = await self.get_catalog_by_id(catalog_id, user_id)
            if not catalog:
                return False
            
            # Delete file from S3
            if catalog.file_path:
                await aws_service.delete_file_from_s3(catalog.file_path)
            
            # Delete catalog from database
            result = await self.db.catalogs.delete_one({
                "_id": ObjectId(catalog_id),
                "user_id": ObjectId(user_id)
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting catalog: {e}")
            raise Exception(f"Failed to delete catalog: {e}")
    
    async def _parse_catalog_file(self, file_data: bytes, file_name: str) -> List[Dict[str, Any]]:
        """Parse catalog file and extract line items."""
        try:
            # Determine file type and parse accordingly
            if file_name.lower().endswith('.csv'):
                return await self._parse_csv_file(file_data)
            elif file_name.lower().endswith('.json'):
                return await self._parse_json_file(file_data)
            elif file_name.lower().endswith('.xlsx'):
                return await self._parse_excel_file(file_data)
            else:
                raise ValueError(f"Unsupported file format: {file_name}")
                
        except Exception as e:
            logger.error(f"Error parsing catalog file: {e}")
            raise Exception(f"Failed to parse catalog file: {e}")
    
    async def _parse_csv_file(self, file_data: bytes) -> List[Dict[str, Any]]:
        """Parse CSV file and return line items."""
        try:
            text = file_data.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(text))
            return [dict(row) for row in csv_reader]
        except Exception as e:
            logger.error(f"Error parsing CSV file: {e}")
            raise Exception(f"Failed to parse CSV file: {e}")
    
    async def _parse_json_file(self, file_data: bytes) -> List[Dict[str, Any]]:
        """Parse JSON file and return line items."""
        try:
            text = file_data.decode('utf-8')
            data = json.loads(text)
            # Assume JSON is an array of line items or has a 'items' key
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'items' in data:
                return data['items']
            else:
                raise ValueError("Invalid JSON format: expected array or object with 'items' key")
        except Exception as e:
            logger.error(f"Error parsing JSON file: {e}")
            raise Exception(f"Failed to parse JSON file: {e}")
    
    async def _parse_excel_file(self, file_data: bytes) -> List[Dict[str, Any]]:
        """Parse Excel file and return line items."""
        try:
            import pandas as pd
            import io
            
            # Read Excel file using pandas
            excel_data = io.BytesIO(file_data)
            
            # Try to read the first sheet
            df = pd.read_excel(excel_data, sheet_name=0)
            
            # Convert DataFrame to list of dictionaries
            line_items = []
            for _, row in df.iterrows():
                # Convert pandas Series to dict, handling NaN values
                item = {}
                for column, value in row.items():
                    if pd.isna(value):
                        item[column] = None
                    else:
                        # Convert numpy types to Python types
                        if hasattr(value, 'item'):
                            item[column] = value.item()
                        else:
                            item[column] = value
                line_items.append(item)
            
            logger.info(f"Successfully parsed Excel file with {len(line_items)} items")
            return line_items
            
        except Exception as e:
            logger.error(f"Error parsing Excel file: {e}")
            raise Exception(f"Failed to parse Excel file: {e}")

# Create a shared instance for routes
catalog_service = CatalogService()