from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from ..auth.dependencies import get_current_active_user
from ..models.user import User
from ..models.offer import OfferResponse, OfferUpdate
from ..services.offer_service import offer_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/offers", tags=["offers"])


@router.post("/generate")
async def generate_offers(
    catalog_id: str = Query(..., description="Catalog ID to generate offers for"),
    offer_type: str = Query("all", description="Type of offers to generate: standard, bundle, flash, or all"),
    max_offers: int = Query(5, ge=1, le=20, description="Maximum number of offers to generate per type"),
    current_user: User = Depends(get_current_active_user)
):
    """Generate offers for a specific catalog based on enriched products."""
    try:
        offers = await offer_service.generate_offers_for_catalog(
            catalog_id=catalog_id,
            user_id=str(current_user.id),
            offer_type=offer_type,
            max_offers=max_offers
        )
        
        # Convert to response models
        offer_responses = []
        for offer in offers:
            # Convert OfferItem to OfferItemResponse
            items_response = []
            for item in offer.items:
                item_response = {
                    "product_id": str(item.product_id),  # Convert PyObjectId to string
                    "original_price": item.original_price,
                    "offer_price": item.offer_price,
                    "discount_percentage": item.discount_percentage,
                    "quantity_required": item.quantity_required,
                    "max_quantity": item.max_quantity,
                    "notes": item.notes
                }
                items_response.append(item_response)
            
            offer_response = OfferResponse(
                id=str(offer.id),
                catalog_id=str(offer.catalog_id),
                name=offer.name,
                description=offer.description,
                offer_type=offer.offer_type,
                valid_from=offer.valid_from,
                valid_until=offer.valid_until,
                is_active=offer.is_active,
                items=items_response,
                rules=offer.rules,
                total_discount=offer.total_discount,
                total_savings=offer.total_savings,
                offer_score=offer.offer_score,
                generation_method=offer.generation_method,
                created_at=offer.created_at,
                updated_at=offer.updated_at
            )
            offer_responses.append(offer_response)
        
        return {
            "message": f"Successfully generated {len(offer_responses)} offers",
            "catalog_id": catalog_id,
            "offer_type": offer_type,
            "offers": offer_responses
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating offers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate offers"
        )


@router.get("/", response_model=List[OfferResponse])
async def get_offers(
    catalog_id: Optional[str] = Query(None, description="Filter by catalog ID"),
    offer_type: Optional[str] = Query(None, description="Filter by offer type"),
    limit: int = Query(100, ge=1, le=1000, description="Number of offers to return"),
    skip: int = Query(0, ge=0, description="Number of offers to skip"),
    current_user: User = Depends(get_current_active_user)
):
    """Get all offers for the current user."""
    try:
        offers = await offer_service.get_user_offers(
            user_id=str(current_user.id),
            catalog_id=catalog_id,
            offer_type=offer_type,
            limit=limit,
            skip=skip
        )
        
        # Convert to response models
        offer_responses = []
        for offer in offers:
            # Convert OfferItem to OfferItemResponse
            items_response = []
            for item in offer.items:
                item_response = {
                    "product_id": str(item.product_id),  # Convert PyObjectId to string
                    "original_price": item.original_price,
                    "offer_price": item.offer_price,
                    "discount_percentage": item.discount_percentage,
                    "quantity_required": item.quantity_required,
                    "max_quantity": item.max_quantity,
                    "notes": item.notes
                }
                items_response.append(item_response)
            
            offer_response = OfferResponse(
                id=str(offer.id),
                catalog_id=str(offer.catalog_id),
                name=offer.name,
                description=offer.description,
                offer_type=offer.offer_type,
                valid_from=offer.valid_from,
                valid_until=offer.valid_until,
                is_active=offer.is_active,
                items=items_response,
                rules=offer.rules,
                total_discount=offer.total_discount,
                total_savings=offer.total_savings,
                offer_score=offer.offer_score,
                generation_method=offer.generation_method,
                created_at=offer.created_at,
                updated_at=offer.updated_at
            )
            offer_responses.append(offer_response)
        
        return offer_responses
        
    except Exception as e:
        logger.error(f"Error fetching offers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch offers"
        )


@router.get("/{offer_id}", response_model=OfferResponse)
async def get_offer(
    offer_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific offer by ID."""
    try:
        offer = await offer_service.get_offer_by_id(offer_id, str(current_user.id))
        
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offer not found"
            )
        
        # Convert OfferItem to OfferItemResponse
        items_response = []
        for item in offer.items:
            item_response = {
                "product_id": str(item.product_id),  # Convert PyObjectId to string
                "original_price": item.original_price,
                "offer_price": item.offer_price,
                "discount_percentage": item.discount_percentage,
                "quantity_required": item.quantity_required,
                "max_quantity": item.max_quantity,
                "notes": item.notes
            }
            items_response.append(item_response)
        
        offer_response = OfferResponse(
            id=str(offer.id),
            catalog_id=str(offer.catalog_id),
            name=offer.name,
            description=offer.description,
            offer_type=offer.offer_type,
            valid_from=offer.valid_from,
            valid_until=offer.valid_until,
            is_active=offer.is_active,
            items=items_response,
            rules=offer.rules,
            total_discount=offer.total_discount,
            total_savings=offer.total_savings,
            offer_score=offer.offer_score,
            generation_method=offer.generation_method,
            created_at=offer.created_at,
            updated_at=offer.updated_at
        )
        
        return offer_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching offer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch offer"
        )


@router.put("/{offer_id}", response_model=OfferResponse)
async def update_offer(
    offer_id: str,
    offer_update: OfferUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update an offer."""
    try:
        updated_offer = await offer_service.update_offer(
            offer_id, str(current_user.id), offer_update.dict(exclude_unset=True)
        )
        
        if not updated_offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offer not found"
            )
        
        # Convert OfferItem to OfferItemResponse
        items_response = []
        for item in updated_offer.items:
            item_response = {
                "product_id": str(item.product_id),  # Convert PyObjectId to string
                "original_price": item.original_price,
                "offer_price": item.offer_price,
                "discount_percentage": item.discount_percentage,
                "quantity_required": item.quantity_required,
                "max_quantity": item.max_quantity,
                "notes": item.notes
            }
            items_response.append(item_response)
        
        offer_response = OfferResponse(
            id=str(updated_offer.id),
            catalog_id=str(updated_offer.catalog_id),
            name=updated_offer.name,
            description=updated_offer.description,
            offer_type=updated_offer.offer_type,
            valid_from=updated_offer.valid_from,
            valid_until=updated_offer.valid_until,
            is_active=updated_offer.is_active,
            items=items_response,
            rules=updated_offer.rules,
            total_discount=updated_offer.total_discount,
            total_savings=updated_offer.total_savings,
            offer_score=updated_offer.offer_score,
            generation_method=updated_offer.generation_method,
            created_at=updated_offer.created_at,
            updated_at=updated_offer.updated_at
        )
        
        return offer_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating offer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update offer"
        )


@router.delete("/{offer_id}")
async def delete_offer(
    offer_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete an offer."""
    try:
        success = await offer_service.delete_offer(offer_id, str(current_user.id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offer not found"
            )
        
        return {"message": "Offer deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting offer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete offer"
        )


@router.get("/catalog/{catalog_id}/summary")
async def get_catalog_offers_summary(
    catalog_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get summary statistics for offers in a catalog."""
    try:
        # Get all offers for the catalog
        offers = await offer_service.get_user_offers(
            user_id=str(current_user.id),
            catalog_id=catalog_id
        )
        
        if not offers:
            return {
                "catalog_id": catalog_id,
                "total_offers": 0,
                "offer_types": {},
                "total_savings": 0,
                "average_discount": 0,
                "best_offer_score": 0
            }
        
        # Calculate summary statistics
        total_offers = len(offers)
        offer_types = {}
        total_savings = 0
        total_discounts = 0
        offer_scores = []
        
        for offer in offers:
            # Count offer types
            offer_type = offer.offer_type
            offer_types[offer_type] = offer_types.get(offer_type, 0) + 1
            
            # Calculate savings and discounts
            total_savings += offer.total_savings
            total_discounts += offer.total_discount
            offer_scores.append(offer.offer_score)
        
        average_discount = round(total_discounts / total_offers, 2) if total_offers > 0 else 0
        best_offer_score = max(offer_scores) if offer_scores else 0
        
        return {
            "catalog_id": catalog_id,
            "total_offers": total_offers,
            "offer_types": offer_types,
            "total_savings": round(total_savings, 2),
            "average_discount": average_discount,
            "best_offer_score": best_offer_score,
            "offer_distribution": {
                "standard": offer_types.get("standard", 0),
                "bundle": offer_types.get("bundle", 0),
                "flash": offer_types.get("flash", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting catalog offers summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get catalog offers summary"
        )

