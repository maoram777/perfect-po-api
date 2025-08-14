from fastapi import APIRouter, HTTPException, status
from ..services.enrichment_service import local_enrichment_service
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
            "default_provider": "amazon"
        }
    except Exception as e:
        logger.error(f"Error getting enrichment providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get enrichment providers"
        )
