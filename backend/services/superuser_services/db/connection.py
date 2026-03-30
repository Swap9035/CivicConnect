from motor.motor_asyncio import AsyncIOMotorClient
from services.superuser_services.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection"""
    try:
        mongodb.client = AsyncIOMotorClient(settings.mongo_uri)
        mongodb.database = mongodb.client[settings.database_name]
        
        # Test connection
        await mongodb.client.admin.command('ping')
        logger.info(f"Connected to MongoDB at {settings.mongo_uri}")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if mongodb.client:
        mongodb.client.close()
        logger.info("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes for better performance"""
    staff_collection = mongodb.database.staff_users
    
    # Create unique indexes
    await staff_collection.create_index("email", unique=True)
    await staff_collection.create_index("employee_id", unique=True)
    
    # Create compound indexes
    await staff_collection.create_index([("metadata.dept", 1), ("metadata.ward", 1)])
    await staff_collection.create_index("role")
    
    logger.info("Database indexes created successfully")

def get_database():
    return mongodb.database
