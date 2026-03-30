from motor.motor_asyncio import AsyncIOMotorClient
from services.AIAnalysis.utils.config import settings

class Database:
    client: AsyncIOMotorClient = None
    
db = Database()

def get_database():
    if db.client is None:
        connect_to_mongo()  # Synchronous call
    return db.client[settings.DATABASE_NAME]

def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.MONGO_URI)
    print("Connected to MongoDB")

def close_mongo_connection():
    db.client.close()
    print("Closed MongoDB connection")
