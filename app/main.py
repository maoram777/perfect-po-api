from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from .database import connect_to_mongo, close_mongo_connection
from .routers import auth, catalogs, enrichment, products, offers
from .config import settings
from app.services.catalog_service import CatalogService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)

# Create FastAPI app
app = FastAPI(
    title="Perfect PO API",
    description="Catalog Management System with Enrichment and Offer Generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(catalogs.router)
app.include_router(enrichment.router)
app.include_router(products.router)
app.include_router(offers.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    try:
        logging.info("Starting Perfect PO API...")
        logging.info(f"Connecting to MongoDB at: {settings.mongodb_url}")
        await connect_to_mongo()
        logging.info("MongoDB connection established successfully")
        logging.info("Application started successfully")
        logging.info(f"API will be available at: http://{settings.api_host}:{settings.api_port}")
        logging.info(f"API Documentation available at: http://{settings.api_host}:{settings.api_port}/docs")
    except Exception as e:
        logging.error(f"Failed to start application: {str(e)}")
        logging.error(f"Startup error type: {type(e).__name__}")
        import traceback
        logging.error(f"Startup traceback: {traceback.format_exc()}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    await close_mongo_connection()
    logging.info("Application shutdown successfully")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Perfect PO API - Catalog Management System",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Perfect PO API"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logging.error(f"Unhandled exception in {request.method} {request.url}: {str(exc)}")
    logging.error(f"Exception type: {type(exc).__name__}")
    import traceback
    logging.error(f"Full traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_type": type(exc).__name__,
            "error_message": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
