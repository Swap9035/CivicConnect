from shared.firebase_client import get_firestore_client
import os

DATABASE_NAME = os.getenv("DATABASE_NAME", "grievance_db")

client = None

async def connect_to_mongo():
    global client
    client = get_firestore_client()
    print("Connected to Firestore (AIFormFilling)")

async def close_mongo_connection():
    global client
    print("Closed Firestore connection (No-op)")

def get_database():
    # If not connected yet (async calls vs sync), grab global shared client
    if client is None:
        return get_firestore_client()
    return client

def get_collection(collection_name: str):
    return get_database().collection(collection_name)

def get_grievance_collection():
    """Get the grievance forms collection"""
    return get_collection("grievance_forms")
