from shared.firebase_client import get_firestore_client
import logging

logger = logging.getLogger(__name__)

def get_nagpur_db():
    """Return the Firestore client for nagpur_civic_db."""
    return get_firestore_client()

async def connect_nagpur_db():
    """Firestore doesn't require explicit connection like Motor, but we return the client for consistency."""
    db = get_nagpur_db()
    print("✅ Firestore client initialized for nagpur_civic_db")
    return db

async def close_nagpur_db():
    print("🔌 Firestore client doesn't need explicit closing here")
    pass
