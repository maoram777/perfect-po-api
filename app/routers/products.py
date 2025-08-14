from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from ..auth.dependencies import get_current_active_user
from ..models.user import User
from ..models.product import ProductResponse
from ..database import get_database
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    catalog_id: Optional[str] = Query(None, description="Filter by catalog ID"),
    enrichment_status: Optional[str] = Query(None, description="Filter by enrichment status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of products to return"),
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    current_user: User = Depends(get_current_active_user)
):
    """Get enriched products for the current user."""
    try:
        db = get_database()
        
        # Build filter query
        filter_query = {"user_id": ObjectId(current_user.id)}
        
        if catalog_id:
            filter_query["catalog_id"] = ObjectId(catalog_id)
        
        if enrichment_status:
            filter_query["enrichment_status"] = enrichment_status
        
        # Get products with pagination
        cursor = db.products.find(filter_query).skip(skip).limit(limit)
        
        products = []
        async for product in cursor:
            product_response = ProductResponse(
                id=str(product["_id"]),
                catalog_id=str(product["catalog_id"]),
                line_item_id=product["line_item_id"],
                name=product["name"],
                description=product.get("description"),
                category=product.get("category"),
                brand=product.get("brand"),
                sku=product.get("sku"),
                upc=product.get("upc"),
                price=product.get("price"),
                currency=product.get("currency", "USD"),
                quantity=product.get("quantity"),
                unit=product.get("unit"),
                enrichment_status=product.get("enrichment_status", "pending"),
                enriched_at=product.get("enriched_at"),
                created_at=product["created_at"],
                updated_at=product["updated_at"]
            )
            products.append(product_response)
        
        return products
        
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch products"
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific product by ID."""
    try:
        db = get_database()
        
        product = await db.products.find_one({
            "_id": ObjectId(product_id),
            "user_id": ObjectId(current_user.id)
        })
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        product_response = ProductResponse(
            id=str(product["_id"]),
            catalog_id=str(product["catalog_id"]),
            line_item_id=product["line_item_id"],
            name=product["name"],
            description=product.get("description"),
            category=product.get("category"),
            brand=product.get("brand"),
            sku=product.get("sku"),
            upc=product.get("upc"),
            price=product.get("price"),
            currency=product.get("currency", "USD"),
            quantity=product.get("quantity"),
            unit=product.get("unit"),
            enrichment_status=product.get("enrichment_status", "pending"),
            enriched_at=product.get("enriched_at"),
            created_at=product["created_at"],
            updated_at=product["updated_at"]
        )
        
        return product_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch product"
        )


@router.get("/catalog/{catalog_id}/summary")
async def get_catalog_products_summary(
    catalog_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get summary statistics for products in a catalog."""
    try:
        db = get_database()
        
        # Verify catalog ownership
        catalog = await db.catalogs.find_one({
            "_id": ObjectId(catalog_id),
            "user_id": ObjectId(current_user.id)
        })
        
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Catalog not found"
            )
        
        # Get product statistics
        pipeline = [
            {"$match": {"catalog_id": ObjectId(catalog_id), "user_id": ObjectId(current_user.id)}},
            {"$group": {
                "_id": "$enrichment_status",
                "count": {"$sum": 1}
            }}
        ]
        
        status_counts = await db.products.aggregate(pipeline).to_list(None)
        
        # Get total count
        total_products = await db.products.count_documents({
            "catalog_id": ObjectId(catalog_id),
            "user_id": ObjectId(current_user.id)
        })
        
        # Format response
        status_summary = {}
        for status_count in status_counts:
            status_summary[status_count["_id"]] = status_count["count"]
        
        return {
            "catalog_id": catalog_id,
            "total_products": total_products,
            "status_summary": status_summary,
            "enrichment_progress": {
                "completed": status_summary.get("completed", 0),
                "failed": status_summary.get("failed", 0),
                "pending": status_summary.get("pending", 0),
                "processing": status_summary.get("processing", 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting catalog products summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get catalog products summary"
        )

