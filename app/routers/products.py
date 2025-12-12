from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from ..auth.dependencies import get_current_active_user
from ..models.user import User
from ..models.product import ProductResponse
from ..database import get_database
from ..services.enrichment_service import local_enrichment_service
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
            # Handle migration from old 'colors' field to new 'color' field
            color = product.get("color")
            if not color and product.get("colors"):
                # If old 'colors' field exists, extract first color
                colors_str = product.get("colors", "")
                if colors_str and "," in str(colors_str):
                    color = str(colors_str).split(",")[0].strip()
                elif colors_str:
                    color = str(colors_str).strip()
            
            # Ensure main_image is a string or None
            main_image = product.get("main_image")
            if main_image is not None:
                if isinstance(main_image, list) and len(main_image) > 0:
                    main_image = str(main_image[0]) if main_image[0] else None
                elif not isinstance(main_image, str):
                    main_image = str(main_image) if main_image else None
            
            # Ensure images is a list of strings or None
            images = product.get("images")
            if images is not None:
                if isinstance(images, str):
                    # If it's a string, try to parse it as a list
                    images = [img.strip() for img in images.split(",") if img.strip()]
                elif isinstance(images, list):
                    # Ensure all items are strings
                    images = [str(img) for img in images if img]
                else:
                    images = None
            
            # Extract MSRP from original_data
            original_data = product.get("original_data", {})
            msrp = local_enrichment_service._extract_numeric_field(
                original_data,
                ["MSRP", "msrp", "Manufacturer Recommended Retail Price", "RRP", "rrp", "Retail Price", "retail_price", "list_price", "Original Price"]
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
                main_image=main_image,
                images=images,
                color=color,  # Single color (with fallback from old 'colors' field)
                size=product.get("size"),  # Size field
                enrichment_status=product.get("enrichment_status", "pending"),
                po_score=product.get("po_score"),  # Purchase Order score
                msrp=msrp,  # MSRP value from original data
                msrp_validated=product.get("msrp_validated"),  # MSRP validation status
                enriched_at=product.get("enriched_at"),
                created_at=product.get("created_at", datetime.utcnow()),
                updated_at=product.get("updated_at", datetime.utcnow())
            )
            products.append(product_response)
        
        return products
        
    except Exception as e:
        import traceback
        logger.error(f"Error fetching products: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch products: {str(e)}"
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
        
        # Handle migration from old 'colors' field to new 'color' field
        color = product.get("color")
        if not color and product.get("colors"):
            # If old 'colors' field exists, extract first color
            colors_str = product.get("colors", "")
            if colors_str and "," in str(colors_str):
                color = str(colors_str).split(",")[0].strip()
            elif colors_str:
                color = str(colors_str).strip()
        
        # Ensure main_image is a string or None
        main_image = product.get("main_image")
        if main_image is not None:
            if isinstance(main_image, list) and len(main_image) > 0:
                main_image = str(main_image[0]) if main_image[0] else None
            elif not isinstance(main_image, str):
                main_image = str(main_image) if main_image else None
        
        # Ensure images is a list of strings or None
        images = product.get("images")
        if images is not None:
            if isinstance(images, str):
                # If it's a string, try to parse it as a list
                images = [img.strip() for img in images.split(",") if img.strip()]
            elif isinstance(images, list):
                # Ensure all items are strings
                images = [str(img) for img in images if img]
            else:
                images = None
        
        # Extract MSRP from original_data
        original_data = product.get("original_data", {})
        msrp = local_enrichment_service._extract_numeric_field(
            original_data,
            ["MSRP", "msrp", "Manufacturer Recommended Retail Price", "RRP", "rrp", "Retail Price", "retail_price", "list_price", "Original Price"]
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
            main_image=main_image,
            images=images,
            color=color,  # Single color (with fallback from old 'colors' field)
            size=product.get("size"),  # Size field
            enrichment_status=product.get("enrichment_status", "pending"),
            po_score=product.get("po_score"),  # Purchase Order score
            msrp=msrp,  # MSRP value from original data
            msrp_validated=product.get("msrp_validated"),  # MSRP validation status
            enriched_at=product.get("enriched_at"),
            created_at=product.get("created_at", datetime.utcnow()),
            updated_at=product.get("updated_at", datetime.utcnow())
        )
        
        return product_response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error fetching product: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch product: {str(e)}"
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


@router.post("/calculate-po-scores")
async def calculate_po_scores(
    catalog_id: Optional[str] = Query(None, description="Calculate scores for products in a specific catalog"),
    current_user: User = Depends(get_current_active_user)
):
    """Calculate and update PO scores for products.
    
    This endpoint recalculates PO scores for products based on their whs, msrp, and offer prices
    from the original_data. Can be run independently of the enrichment process.
    """
    try:
        db = get_database()
        
        # Build filter query
        filter_query = {"user_id": ObjectId(current_user.id)}
        
        if catalog_id:
            filter_query["catalog_id"] = ObjectId(catalog_id)
        
        # Get all products matching the filter
        cursor = db.products.find(filter_query)
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        async for product in cursor:
            try:
                # Extract pricing fields from original_data
                original_data = product.get("original_data", {})
                
                # Extract numeric fields using the enrichment service method
                whs = local_enrichment_service._extract_numeric_field(
                    original_data, 
                    ["WHS", "whs", "Warehouse Price", "warehouse_price", "warehouse", "cost_price"]
                )
                msrp = local_enrichment_service._extract_numeric_field(
                    original_data, 
                    ["MSRP", "msrp", "Manufacturer Recommended Retail Price", "RRP", "rrp", "Retail Price", "retail_price", "list_price"]
                )
                offer = local_enrichment_service._extract_numeric_field(
                    original_data, 
                    ["Offer Price", "offer_price", "offer", "Offer", "Price", "price", "selling_price"]
                )
                
                # Calculate PO score
                po_score = local_enrichment_service.calculate_po_score(whs, msrp, offer)
                
                # Update product with new PO score
                await db.products.update_one(
                    {"_id": product["_id"]},
                    {
                        "$set": {
                            "po_score": po_score,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                if po_score is not None:
                    updated_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                logger.error(f"Error calculating PO score for product {product.get('_id')}: {e}")
                error_count += 1
                continue
        
        return {
            "message": "PO score calculation completed",
            "updated": updated_count,
            "skipped": skipped_count,
            "errors": error_count,
            "total_processed": updated_count + skipped_count + error_count
        }
        
    except Exception as e:
        logger.error(f"Error calculating PO scores: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate PO scores: {str(e)}"
        )


@router.post("/{product_id}/calculate-po-score")
async def calculate_product_po_score(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Calculate and update PO score for a specific product."""
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
        
        # Extract pricing fields from original_data
        original_data = product.get("original_data", {})
        
        # Extract numeric fields using the enrichment service method
        whs = local_enrichment_service._extract_numeric_field(
            original_data, 
            ["WHS", "whs", "Warehouse Price", "warehouse_price", "warehouse", "cost_price"]
        )
        msrp = local_enrichment_service._extract_numeric_field(
            original_data, 
            ["MSRP", "msrp", "Manufacturer Recommended Retail Price", "RRP", "rrp", "Retail Price", "retail_price", "list_price"]
        )
        offer = local_enrichment_service._extract_numeric_field(
            original_data, 
            ["Offer Price", "offer_price", "offer", "Offer", "Price", "price", "selling_price"]
        )
        
        # Calculate PO score
        po_score = local_enrichment_service.calculate_po_score(whs, msrp, offer)
        
        # Update product with new PO score
        await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$set": {
                    "po_score": po_score,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "product_id": product_id,
            "po_score": po_score,
            "calculation_details": {
                "whs": whs,
                "msrp": msrp,
                "offer": offer
            },
            "message": "PO score calculated and updated" if po_score is not None else "PO score could not be calculated (missing required fields)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating PO score for product {product_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate PO score: {str(e)}"
        )


@router.post("/validate-msrp")
async def validate_msrp_scores(
    catalog_id: Optional[str] = Query(None, description="Validate MSRP for products in a specific catalog"),
    current_user: User = Depends(get_current_active_user)
):
    """Re-validate MSRP for products against enriched prices.
    
    This endpoint re-validates MSRP for products based on their source MSRP and enriched prices
    from the enriched_data. Can be run independently to update validation status.
    """
    try:
        db = get_database()
        
        # Build filter query
        filter_query = {"user_id": ObjectId(current_user.id)}
        
        if catalog_id:
            filter_query["catalog_id"] = ObjectId(catalog_id)
        
        # Get all products matching the filter
        cursor = db.products.find(filter_query)
        
        validated_count = 0
        invalidated_count = 0
        skipped_count = 0
        error_count = 0
        
        async for product in cursor:
            try:
                # Extract MSRP from original_data
                original_data = product.get("original_data", {})
                msrp = local_enrichment_service._extract_numeric_field(
                    original_data, 
                    ["MSRP", "msrp", "Manufacturer Recommended Retail Price", "RRP", "rrp", "Retail Price", "retail_price", "list_price"]
                )
                
                # Get enriched price from enriched_data
                enriched_data = product.get("enriched_data", {})
                enrichment_source = product.get("enrichment_source", "")
                
                enriched_price = None
                if "keepa" in enrichment_source.lower():
                    enriched_price = enriched_data.get("keepa_price")
                elif "amazon" in enrichment_source.lower():
                    enriched_price = enriched_data.get("amazon_price")
                else:
                    # Try both if source is unknown
                    enriched_price = enriched_data.get("keepa_price") or enriched_data.get("amazon_price")
                
                # Validate MSRP (within 5% delta)
                msrp_validated = local_enrichment_service.validate_msrp(msrp, enriched_price, delta_percent=5.0)
                
                # Update product with validation result
                await db.products.update_one(
                    {"_id": product["_id"]},
                    {
                        "$set": {
                            "msrp_validated": msrp_validated,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                if msrp_validated is True:
                    validated_count += 1
                elif msrp_validated is False:
                    invalidated_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                logger.error(f"Error validating MSRP for product {product.get('_id')}: {e}")
                error_count += 1
                continue
        
        return {
            "message": "MSRP validation completed",
            "validated": validated_count,
            "invalidated": invalidated_count,
            "skipped": skipped_count,
            "errors": error_count,
            "total_processed": validated_count + invalidated_count + skipped_count + error_count
        }
        
    except Exception as e:
        logger.error(f"Error validating MSRP: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate MSRP: {str(e)}"
        )


@router.post("/{product_id}/validate-msrp")
async def validate_product_msrp(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Re-validate MSRP for a specific product."""
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
        
        # Extract MSRP from original_data
        original_data = product.get("original_data", {})
        msrp = local_enrichment_service._extract_numeric_field(
            original_data, 
            ["MSRP", "msrp", "Manufacturer Recommended Retail Price", "RRP", "rrp", "Retail Price", "retail_price", "list_price"]
        )
        
        # Get enriched price from enriched_data
        enriched_data = product.get("enriched_data", {})
        enrichment_source = product.get("enrichment_source", "")
        
        enriched_price = None
        if "keepa" in enrichment_source.lower():
            enriched_price = enriched_data.get("keepa_price")
        elif "amazon" in enrichment_source.lower():
            enriched_price = enriched_data.get("amazon_price")
        else:
            # Try both if source is unknown
            enriched_price = enriched_data.get("keepa_price") or enriched_data.get("amazon_price")
        
        # Validate MSRP (within 5% delta)
        msrp_validated = local_enrichment_service.validate_msrp(msrp, enriched_price, delta_percent=5.0)
        
        # Update product with validation result
        await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$set": {
                    "msrp_validated": msrp_validated,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "product_id": product_id,
            "msrp_validated": msrp_validated,
            "validation_details": {
                "source_msrp": msrp,
                "enriched_price": enriched_price,
                "delta_percent": 5.0,
                "difference": abs(msrp - enriched_price) if msrp and enriched_price else None,
                "percentage_diff": (abs(msrp - enriched_price) / enriched_price * 100) if msrp and enriched_price and enriched_price > 0 else None
            },
            "message": "MSRP validated" if msrp_validated is not None else "MSRP validation could not be performed (missing required fields)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating MSRP for product {product_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate MSRP: {str(e)}"
        )


