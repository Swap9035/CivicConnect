import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "grievance_db")

client: AsyncIOMotorClient = None

async def connect_to_mongo():
    global client
    client = AsyncIOMotorClient(MONGO_URI)
    print("Connected to MongoDB")

async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("Closed MongoDB connection")

def get_database():
    return client[DATABASE_NAME]

def get_collection(collection_name: str):
    return get_database()[collection_name]

def get_grievance_collection():
    """Get the grievance forms collection"""
    return get_collection("grievance_forms")  # Assuming the collection is named "grievance_forms"
