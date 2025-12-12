from pydantic import BaseModel, Field
from typing import Optional


class EnrichRequest(BaseModel):
    """Request model for product enrichment endpoint."""
    asin: Optional[str] = Field(None, description="Amazon Standard Identification Number")
    upc: Optional[str] = Field(None, description="Universal Product Code")
    model: Optional[str] = Field(None, description="Product model number")
    title: Optional[str] = Field(None, description="Product title or name")
    part: Optional[str] = Field(None, description="Part number")
    brand: Optional[str] = Field(None, description="Product brand")
    
    class Config:
        schema_extra = {
            "example": {
                "asin": "B07B421VFF",
                "upc": None,
                "model": None,
                "title": None,
                "part": None,
                "brand": None
            }
        }


class EnrichResponse(BaseModel):
    """Response model for product enrichment endpoint."""
    success: bool
    enrichment_source: str
    enriched_data: dict
    message: Optional[str] = None




