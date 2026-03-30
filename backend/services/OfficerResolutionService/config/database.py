import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import asyncio

class OfficerResolutionDatabase:
    def __init__(self):
        self.client = None
        self.database = None
        self.sync_client = None
        self.sync_database = None
        # Add AI Analysis DB connection
        self.ai_client = None
        self.ai_database = None
        self.ai_sync_client = None
        self.ai_sync_database = None

    async def connect_db(self):
        mongo_uri = os.getenv("MONGO_URI")  # Use MONGO_URI from .env
        self.client = AsyncIOMotorClient(mongo_uri)
        self.database = self.client.officer_resolution_db
        
        # Sync client for non-async operations
        self.sync_client = MongoClient(mongo_uri)
        self.sync_database = self.sync_client.officer_resolution_db
        
        # Connect to AI Analysis DB
        self.ai_client = AsyncIOMotorClient(mongo_uri)
        self.ai_database = self.ai_client.ai_analysis_db
        
        self.ai_sync_client = MongoClient(mongo_uri)
        self.ai_sync_database = self.ai_sync_client.ai_analysis_db
        
        print("✅ Connected to Officer Resolution Database and AI Analysis Database")

    async def close_db(self):
        if self.client:
            self.client.close()
        if self.sync_client:
            self.sync_client.close()
        if self.ai_client:
            self.ai_client.close()
        if self.ai_sync_client:
            self.ai_sync_client.close()
        print("✅ Officer Resolution Database and AI Analysis Database connections closed")

# Global instance
officer_resolution_db = OfficerResolutionDatabase()
