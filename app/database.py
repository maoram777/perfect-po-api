from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None


async def connect_to_mongo():
    """Create database connection."""
    try:
        logger.info(f"Attempting to connect to MongoDB at: {settings.mongodb_url}")
        Database.client = AsyncIOMotorClient(settings.mongodb_url)
        
        # Test the connection
        await Database.client.admin.command('ping')
        logger.info("MongoDB connection test successful")
        
        # Extract database name from URL or use default
        if "/" in settings.mongodb_url:
            db_name = settings.mongodb_url.split("/")[-1]
        else:
            db_name = "perfect_po_db"
        
        Database.db = Database.client[db_name]
        logger.info(f"Connected to MongoDB database: {Database.db.name}")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        logger.error(f"Connection error type: {type(e).__name__}")
        import traceback
        logger.error(f"Connection traceback: {traceback.format_exc()}")
        raise


async def close_mongo_connection():
    """Close database connection."""
    if Database.client is not None:
        logger.info("Closing MongoDB connection...")
        Database.client.close()
        logger.info("MongoDB connection closed successfully.")
    else:
        logger.info("No MongoDB connection to close.")


def get_database():
    """Get database instance."""
    if Database.db is None:
        logger.error("Database connection not established. Call connect_to_mongo() first.")
        raise RuntimeError("Database connection not established")
    return Database.db
