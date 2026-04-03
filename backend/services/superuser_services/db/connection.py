from shared.firebase_client import get_firestore_client
from services.superuser_services.config import settings
import logging

logger = logging.getLogger(__name__)

class FirestoreDB:
    client = None
    database = None

mongodb = FirestoreDB()

async def connect_to_mongo():
    """Create database connection (Using Firestore instead)"""
    try:
        # Load from shared firebase client
        db = get_firestore_client()
        mongodb.database = db
        mongodb.client = db
        
        logger.info(f"Connected to Firestore instead of MongoDB")
        
    except Exception as e:
        logger.error(f"Failed to connect to Firestore: {e}")
        raise

async def close_mongo_connection():
    """Close database connection (No-op in Firestore)"""
    logger.info("Disconnected from Firestore (No-op)")

def get_database():
    if mongodb.database is None:
        mongodb.database = get_firestore_client()
    return mongodb.database

