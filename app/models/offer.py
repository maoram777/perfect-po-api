from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId


class OfferRule(BaseModel):
    rule_id: str
    rule_name: str
    rule_type: str  # pricing, quantity, timing, etc.
    rule_parameters: Dict[str, Any] = {}
    priority: int = 1
    is_active: bool = True


class OfferItem(BaseModel):
    product_id: PyObjectId
    original_price: float
    offer_price: float
    discount_percentage: float
    quantity_required: Optional[int] = None
    max_quantity: Optional[int] = None
    notes: Optional[str] = None


class OfferItemResponse(BaseModel):
    product_id: str  # Convert PyObjectId to string for API responses
    original_price: float
    offer_price: float
    discount_percentage: float
    quantity_required: Optional[int] = None
    max_quantity: Optional[int] = None
    notes: Optional[str] = None


class OfferBase(BaseModel):
    catalog_id: PyObjectId
    name: str
    description: Optional[str] = None
    offer_type: str = "standard"  # standard, flash, bundle, etc.
    valid_from: datetime
    valid_until: datetime
    is_active: bool = True


class OfferCreate(OfferBase):
    items: List[OfferItem]
    rules: List[OfferRule] = []


class Offer(OfferBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    items: List[OfferItem]
    rules: List[OfferRule] = []
    total_discount: float = 0.0
    total_savings: float = 0.0
    offer_score: Optional[float] = None  # AI-generated score
    generation_method: str = "rule_based"  # rule_based, ai_generated, hybrid
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Electronics Bundle Deal",
                "description": "Special pricing on electronics bundle",
                "offer_type": "bundle",
                "total_discount": 25.0,
                "total_savings": 150.00,
                "offer_score": 8.5
            }
        }


class OfferResponse(BaseModel):
    id: str
    catalog_id: str
    name: str
    description: Optional[str]
    offer_type: str
    valid_from: datetime
    valid_until: datetime
    is_active: bool
    items: List[OfferItemResponse]  # Use OfferItemResponse instead of OfferItem
    total_discount: float
    total_savings: float
    offer_score: Optional[float]
    generation_method: str
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {ObjectId: str}


class OfferUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    offer_type: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None
    items: Optional[List[OfferItemResponse]] = None  # Use OfferItemResponse for consistency
    rules: Optional[List[OfferRule]] = None

