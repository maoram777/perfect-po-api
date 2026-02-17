from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId


class Enrichment(BaseModel):
    """Enrichment information nested in product."""
    source: Optional[str] = None  # e.g., "amazon_api", "keepa_api"
    status: str = "pending"  # pending, processing, completed, failed
    errors: List[str] = []  # List of enrichment errors
    data: Dict[str, Any] = {}  # Data from external APIs


class ProductBase(BaseModel):
    catalog_id: PyObjectId
    line_item_id: str  # Original line item identifier
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None  # Required field from CSV, saved at product level
    upc: Optional[str] = None  # Required field from CSV, saved at product level
    price: Optional[float] = None
    currency: str = "USD"
    quantity: Optional[int] = None  # Required field from CSV, saved at product level
    offer_price: Optional[float] = None  # Required field from CSV, saved at product level
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
    raw_data: Dict[str, Any] = {}  # Raw catalog data
    enrichment: Enrichment = Field(default_factory=lambda: Enrichment())  # Enrichment information
    po_score: Optional[float] = None  # Purchase Order score - represents opportunity/deal quality (calculated later)
    profit: Optional[float] = None  # Profit percentage = (product_price - cogs - offer_price) / product_price (where cogs = product_price * 35%)
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
                "enrichment": {
                    "status": "completed",
                    "source": "keepa_api",
                    "errors": [],
                    "data": {}
                }
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
    sku: Optional[str]  # Required field from CSV
    upc: Optional[str]  # Required field from CSV
    price: Optional[float]
    currency: str
    quantity: Optional[int]  # Required field from CSV
    offer_price: Optional[float] = None  # Required field from CSV
    unit: Optional[str]
    main_image: Optional[str]  # Primary product image URL
    images: Optional[List[str]]  # Additional product images
    color: Optional[str]  # Product color (single color)
    size: Optional[str]  # Product size
    enrichment: Enrichment  # Enrichment information
    po_score: Optional[float]  # Purchase Order score
    msrp: Optional[float] = None  # MSRP value from raw_data
    profit: Optional[float] = None  # Profit percentage = (product_price - cogs - offer_price) / product_price (where cogs = product_price * 35%)
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
    offer_price: Optional[float] = None
    unit: Optional[str] = None
    main_image: Optional[str] = None  # Primary product image URL
    images: Optional[List[str]] = None  # Additional product images
    color: Optional[str] = None  # Product color (single color)
    size: Optional[str] = None  # Product size
    po_score: Optional[float] = None  # Purchase Order score
    profit: Optional[float] = None  # Profit percentage = (product_price - cogs - offer_price) / product_price (where cogs = product_price * 35%)

