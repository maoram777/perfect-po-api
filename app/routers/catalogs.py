from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from typing import List, Optional
import asyncio
from ..auth.dependencies import get_current_active_user
from ..models.user import User
from ..models.catalog import CatalogResponse, CatalogCreate, CatalogUpdate
from ..services.catalog_service import catalog_service
from ..services.aws_service import aws_service
from ..services.enrichment_service import local_enrichment_service
from ..database import get_database
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


# This endpoint is removed since we have the upload endpoint that handles file uploads
# If you need a simple catalog creation without file upload, you can uncomment and modify this


@router.post("/upload")
async def upload_catalog_file(
    file: UploadFile = File(...),
    name: str = Form(..., description="Catalog name"),
    description: Optional[str] = Form(None, description="Catalog description"),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a catalog file and create catalog."""
    try:
        # Log incoming request data for debugging
        logger.info(f"Upload request received - User: {current_user.email}, Name: {name}, Description: {description}")
        logger.info(f"File details - Filename: {file.filename}, Content-Type: {file.content_type}, Size: {file.size if hasattr(file, 'size') else 'Unknown'}")
        
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            logger.warning(f"Invalid file type attempted: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only Excel (.xlsx, .xls) and CSV files are supported"
            )
        
        # Validate required fields
        if not name or name.strip() == "":
            logger.error("Catalog name is missing or empty")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Catalog name is required and cannot be empty"
            )
        
        logger.info(f"File validation passed, proceeding with catalog creation...")
        
        # Read file content
        file_content = await file.read()
        
        # Create catalog data
        catalog_data = CatalogCreate(
            name=name,
            description=description
        )
        
        # Create catalog with file
        catalog = await catalog_service.create_catalog(
            catalog_data=catalog_data,
            user_id=str(current_user.id),
            file_data=file_content,
            file_name=file.filename
        )
        
        logger.info(f"Catalog created successfully: {catalog.id} with {catalog.total_items} items")
        
        return {
            "message": "Catalog file uploaded successfully",
            "catalog_id": str(catalog.id),
            "filename": file.filename,
            "total_items": catalog.total_items
        }
        
    except ValueError as e:
        error_message = str(e)
        # Check if error is about missing required headers
        if "Missing required" in error_message and "headers" in error_message:
            logger.error(f"Missing required CSV headers: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail=error_message
            )
        logger.error(f"Validation error: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading catalog file: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload catalog file"
        )


@router.get("/", response_model=List[CatalogResponse])
async def get_catalogs(
    limit: int = Query(100, ge=1, le=1000, description="Number of catalogs to return"),
    skip: int = Query(0, ge=0, description="Number of catalogs to skip"),
    status_filter: Optional[str] = Query(None, description="Filter by catalog status"),
    current_user: User = Depends(get_current_active_user)
):
    """Get all catalogs for the current user."""
    try:
        catalogs = await catalog_service.get_user_catalogs(
            user_id=str(current_user.id),
            limit=limit,
            skip=skip,
            status=status_filter
        )
        
        catalog_responses = []
        for catalog in catalogs:
            catalog_response = CatalogResponse(
                id=str(catalog.id),
                name=catalog.name,
                description=catalog.description,
                category=catalog.category,
                file_name=catalog.file_name,
                file_size=catalog.file_size,
                total_items=catalog.total_items,
                enriched_items=catalog.enriched_items,
                status=catalog.status,
                created_at=catalog.created_at,
                updated_at=catalog.updated_at,
                enrichment_started_at=catalog.enrichment_started_at,
                enrichment_completed_at=catalog.enrichment_completed_at
            )
            catalog_responses.append(catalog_response)
        
        return catalog_responses
        
    except Exception as e:
        logger.error(f"Error fetching catalogs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch catalogs"
        )


@router.get("/{catalog_id}", response_model=CatalogResponse)
async def get_catalog(
    catalog_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific catalog by ID."""
    try:
        catalog = await catalog_service.get_catalog_by_id(catalog_id, str(current_user.id))
        
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Catalog not found"
            )
        
        return CatalogResponse(
            id=str(catalog.id),
            name=catalog.name,
            description=catalog.description,
            category=catalog.category,
            file_name=catalog.file_name,
            file_size=catalog.file_size,
            total_items=catalog.total_items,
            enriched_items=catalog.enriched_items,
            status=catalog.status,
            created_at=catalog.created_at,
            updated_at=catalog.updated_at,
            enrichment_started_at=catalog.enrichment_started_at,
            enrichment_completed_at=catalog.enrichment_completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching catalog: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch catalog"
        )


@router.put("/{catalog_id}", response_model=CatalogResponse)
async def update_catalog(
    catalog_id: str,
    catalog_update: CatalogUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update a catalog."""
    try:
        updated_catalog = await catalog_service.update_catalog(
            catalog_id, str(current_user.id), catalog_update
        )
        
        if not updated_catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Catalog not found"
            )
        
        return CatalogResponse(
            id=str(updated_catalog.id),
            name=updated_catalog.name,
            description=updated_catalog.description,
            category=updated_catalog.category,
            file_name=updated_catalog.file_name,
            file_size=updated_catalog.file_size,
            total_items=updated_catalog.total_items,
            enriched_items=updated_catalog.enriched_items,
            status=updated_catalog.status,
            created_at=updated_catalog.created_at,
            updated_at=updated_catalog.updated_at,
            enrichment_started_at=updated_catalog.enrichment_started_at,
            enrichment_completed_at=updated_catalog.enrichment_completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating catalog: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update catalog"
        )


@router.delete("/{catalog_id}")
async def delete_catalog(
    catalog_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a catalog."""
    try:
        success = await catalog_service.delete_catalog(catalog_id, str(current_user.id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Catalog not found"
            )
        
        return {"message": "Catalog deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting catalog: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete catalog"
        )


@router.get("/{catalog_id}/summary")
async def get_catalog_summary(
    catalog_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get summary statistics for a catalog."""
    try:
        catalog = await catalog_service.get_catalog_by_id(catalog_id, str(current_user.id))
        
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Catalog not found"
            )
        
        # Get product statistics from database
        db = get_database()
        pipeline = [
            {"$match": {"catalog_id": ObjectId(catalog_id), "user_id": ObjectId(current_user.id)}},
            {"$group": {
                "_id": "$enrichment.status",
                "count": {"$sum": 1}
            }}
        ]
        
        status_counts = await db.products.aggregate(pipeline).to_list(None)
        
        # Format status summary
        status_summary = {}
        for status_count in status_counts:
            status_summary[status_count["_id"]] = status_count["count"]
        
        return {
            "catalog_id": catalog_id,
            "name": catalog.name,
            "status": catalog.status,
            "total_items": catalog.total_items,
            "enriched_items": catalog.enriched_items,
            "enrichment_progress": {
                "completed": status_summary.get("completed", 0),
                "failed": status_summary.get("failed", 0),
                "pending": status_summary.get("pending", 0),
                "processing": status_summary.get("processing", 0)
            },
            "progress_percentage": (
                (catalog.enriched_items / catalog.total_items * 100) 
                if catalog.total_items > 0 else 0
            ),
            "created_at": catalog.created_at,
            "updated_at": catalog.updated_at,
            "enrichment_started_at": catalog.enrichment_started_at,
            "enrichment_completed_at": catalog.enrichment_completed_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting catalog summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get catalog summary"
        )



@router.post("/{catalog_id}/enrich")
async def trigger_enrichment(
    catalog_id: str,
    provider: str = "keepa",  # Default to Amazon API
    current_user: User = Depends(get_current_active_user)
):
    """Trigger enrichment for a specific catalog."""
    try:
        # Get catalog to verify ownership and status
        catalog = await catalog_service.get_catalog_by_id(catalog_id, str(current_user.id))
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Catalog not found"
            )
        
        # Check if catalog is already being processed or completed
        if catalog.status in ["processing", "enriched", "completed", "partially_completed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot enrich catalog with status: {catalog.status}"
            )
        
        # Validate provider
        available_providers = await local_enrichment_service.get_enrichment_providers()
        if provider not in available_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider: {provider}. Available providers: {', '.join(available_providers)}"
            )
        
        # Spawn background task for enrichment (runs after HTTP response)
        try:
            # Create background task that will continue after HTTP response closes
            background_task = asyncio.create_task(
                local_enrichment_service.enrich_catalog_products_background(
                    catalog_id=catalog_id,
                    user_id=str(current_user.id),
                    provider=provider,
                    bulk_size=50
                )
            )
            
            # Don't await the task - let it run in background
            logger.info(f"🚀 Background enrichment task spawned for catalog {catalog_id}")
            
            return {
                "message": "Enrichment process started in background",
                "catalog_id": catalog_id,
                "status": "processing",
                "provider": provider,
                "note": "Enrichment is running asynchronously. Check enrichment status using GET /catalogs/{catalog_id}/enrichment-status"
            }
            
        except Exception as e:
            logger.error(f"Failed to start background enrichment: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start enrichment: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering enrichment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger enrichment"
        )


@router.get("/{catalog_id}/enrichment-status")
async def get_enrichment_status(
    catalog_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get the current enrichment status for a catalog."""
    try:
        catalog = await catalog_service.get_catalog_by_id(catalog_id, str(current_user.id))
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Catalog not found"
            )
        
        return {
            "catalog_id": catalog_id,
            "status": catalog.status,
            "total_items": catalog.total_items,
            "enriched_items": catalog.enriched_items,
            "enrichment_started_at": catalog.enrichment_started_at,
            "enrichment_completed_at": catalog.enrichment_completed_at,
            "progress_percentage": (
                (catalog.enriched_items / catalog.total_items * 100) 
                if catalog.total_items > 0 else 0
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting enrichment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get enrichment status"
        )
