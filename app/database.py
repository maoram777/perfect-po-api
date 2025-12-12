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
        
        # Extract database name from URL or use configured default
        # Parse MongoDB connection string properly
        from urllib.parse import urlparse, parse_qs
        
        parsed_url = urlparse(settings.mongodb_url)
        
        # Get database name from path (remove leading slash)
        db_name = parsed_url.path.lstrip('/')
        
        # If no database name in path, check if it's in the query string or use configured default
        if not db_name or db_name == '':
            # Check query parameters for database name
            query_params = parse_qs(parsed_url.query)
            if 'database' in query_params:
                db_name = query_params['database'][0]
            elif 'db' in query_params:
                db_name = query_params['db'][0]
            else:
                # Use configured database name from settings (defaults to AllShoes-Dev)
                db_name = settings.mongodb_database_name
        
        # Remove any query parameters that might be in the db_name
        if '?' in db_name:
            db_name = db_name.split('?')[0]
        
        logger.info(f"Using MongoDB database: {db_name}")
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
