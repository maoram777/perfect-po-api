from fastapi import APIRouter, HTTPException, status, Depends
from ..services.enrichment_service import local_enrichment_service
from ..models.enrichment import EnrichRequest, EnrichResponse
from ..auth.dependencies import get_current_active_user
from ..models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.get("/providers")
async def get_enrichment_providers():
    """Get available enrichment providers."""
    try:
        providers = await local_enrichment_service.get_enrichment_providers()
        return {
            "providers": providers,
            "default_provider": "keepa"
        }
    except Exception as e:
        logger.error(f"Error getting enrichment providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get enrichment providers"
        )


@router.post("/enrich", response_model=EnrichResponse)
async def enrich_product(
    request: EnrichRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Enrich a product using Keepa API.
    
    Accepts ASIN, UPC, or product details (model, title, part, brand) in the payload.
    
    Priority:
    1. If ASIN provided -> direct product lookup
    2. If UPC provided -> direct product lookup  
    3. If model/title/part/brand provided -> product finder (search API)
    
    Example requests:
    - By ASIN: {"asin": "B07B421VFF"}
    - By UPC: {"upc": "196479131670"}
    - By model/title: {"model": "JI0954", "brand": "adidas"}
    - By title: {"title": "wireless headphones", "brand": "Sony"}
    """
    try:
        # Validate that at least one identifier is provided
        if not any([request.asin, request.upc, request.model, request.title, request.part, request.brand]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one identifier must be provided: ASIN, UPC, model, title, part, or brand"
            )
        
        # Get Keepa provider
        keepa_provider = local_enrichment_service.providers.get("keepa")
        if not keepa_provider:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Keepa provider not available"
            )
        
        # Call enrichment
        enrichment_result = await keepa_provider.enrich_by_identifier(
            asin=request.asin,
            upc=request.upc,
            model=request.model,
            title=request.title,
            part=request.part,
            brand=request.brand
        )
        
        # Check if enrichment was successful
        if enrichment_result.get("enrichment_status") == "failed":
            errors = enrichment_result.get("enrichment_errors", ["Unknown error"])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Enrichment failed: {', '.join(errors)}"
            )
        
        return EnrichResponse(
            success=True,
            enrichment_source=enrichment_result.get("enrichment_source", "keepa_api"),
            enriched_data=enrichment_result.get("enriched_data", {}),
            message="Product enriched successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enriching product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enrich product: {str(e)}"
        )
