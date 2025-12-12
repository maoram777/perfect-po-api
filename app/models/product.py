from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId


class ProductBase(BaseModel):
    catalog_id: PyObjectId
    line_item_id: str  # Original line item identifier
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    upc: Optional[str] = None
    price: Optional[float] = None
    currency: str = "USD"
    quantity: Optional[int] = None
    unit: Optional[str] = None
    # Image fields for enriched products
    main_image: Optional[str] = None  # Primary product image URL
    images: Optional[List[str]] = None  # Additional product images
    color: Optional[str] = None  # Product color (single color, not array)
    size: Optional[str] = None  # Product size - can be number (e.g., "8.5" for shoes) or dimensions (e.g., "M" or "10x12" for clothing)


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    original_data: Dict[str, Any] = {}  # Raw catalog data
    enriched_data: Dict[str, Any] = {}  # Data from external APIs
    enrichment_source: Optional[str] = None  # e.g., "amazon_api"
    enrichment_status: str = "pending"  # pending, processing, completed, failed
    enrichment_errors: List[str] = []
    po_score: Optional[float] = None  # Purchase Order score - represents opportunity/deal quality (calculated later)
    msrp_validated: Optional[bool] = None  # True if source MSRP is within 5% delta of enriched price from external API
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    enriched_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Wireless Bluetooth Headphones",
                "description": "High-quality wireless headphones with noise cancellation",
                "category": "Electronics",
                "brand": "AudioTech",
                "sku": "ATH-BT001",
                "price": 99.99,
                "currency": "USD",
                "enrichment_status": "completed"
            }
        }


class ProductResponse(BaseModel):
    id: str
    catalog_id: str
    line_item_id: str
    name: str
    description: Optional[str]
    category: Optional[str]
    brand: Optional[str]
    sku: Optional[str]
    upc: Optional[str]
    price: Optional[float]
    currency: str
    quantity: Optional[int]
    unit: Optional[str]
    main_image: Optional[str]  # Primary product image URL
    images: Optional[List[str]]  # Additional product images
    color: Optional[str]  # Product color (single color)
    size: Optional[str]  # Product size
    enrichment_status: str
    po_score: Optional[float]  # Purchase Order score
    msrp: Optional[float] = None  # MSRP value from original data
    msrp_validated: Optional[bool]  # MSRP validation status
    enriched_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {ObjectId: str}


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    upc: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    main_image: Optional[str] = None  # Primary product image URL
    images: Optional[List[str]] = None  # Additional product images
    color: Optional[str] = None  # Product color (single color)
    size: Optional[str] = None  # Product size
    po_score: Optional[float] = None  # Purchase Order score
    msrp_validated: Optional[bool] = None  # MSRP validation status

