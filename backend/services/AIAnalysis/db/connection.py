from shared.firebase_client import get_firestore_client
from services.AIAnalysis.utils.config import settings

class Database:
    client = None
    
db = Database()

def get_database():
    if db.client is None:
        connect_to_mongo()  # Kept name for compatibility
    return db.client

def connect_to_mongo():
    db.client = get_firestore_client()
    print("Connected to Firestore (AIAnalysis)")

def close_mongo_connection():
    print("Closed Firestore connection (No-op)")

