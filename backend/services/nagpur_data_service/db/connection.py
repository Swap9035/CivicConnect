import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

_client = None
_db = None

async def connect_nagpur_db():
    global _client, _db
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    _client = AsyncIOMotorClient(mongo_uri)
    _db = _client["nagpur_civic_db"]
    
    # Create indexes for performance
    await _db.wards.create_index("ward_number", unique=True)
    await _db.wards.create_index("zone_id")
    await _db.water_supply_data.create_index("ward_id")
    await _db.sanitation_data.create_index("ward_id")
    await _db.civic_metrics.create_index("ward_id")
    
    print("✅ Connected to nagpur_civic_db")
    return _db

async def close_nagpur_db():
    global _client
    if _client:
        _client.close()
        print("🔌 Disconnected from nagpur_civic_db")

def get_nagpur_db():
    return _db
