from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId


class CatalogBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)


class CatalogCreate(CatalogBase):
    pass


class Catalog(CatalogBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    file_path: str  # S3 path
    file_name: str
    file_size: int
    total_items: int = 0
    enriched_items: int = 0
    status: str = "uploaded"  # uploaded, processing, enriched, completed, error
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    enrichment_started_at: Optional[datetime] = None
    enrichment_completed_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Electronics Catalog 2024",
                "description": "Latest electronics products",
                "category": "Electronics",
                "total_items": 150,
                "enriched_items": 0,
                "status": "uploaded"
            }
        }


class CatalogResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    category: Optional[str]
    file_name: str
    file_size: int
    total_items: int
    enriched_items: int
    status: str
    created_at: datetime
    updated_at: datetime
    enrichment_started_at: Optional[datetime]
    enrichment_completed_at: Optional[datetime]

    class Config:
        json_encoders = {ObjectId: str}


class CatalogUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)

