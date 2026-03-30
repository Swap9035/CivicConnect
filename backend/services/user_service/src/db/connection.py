from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
database = client["user_db"]
user_collection = database["users"]

def get_users_collection():
    return user_collection
