from shared.firebase_client import get_firestore_client
import os

class OfficerResolutionDatabase:
    def __init__(self):
        self.db = None
        self.ai_db = None

    def get_db(self):
        if self.db is None:
            self.db = get_firestore_client()
        return self.db

    def get_ai_db(self):
        if self.ai_db is None:
            self.ai_db = get_firestore_client()
        return self.ai_db

    async def connect_db(self):
        # Use the shared firestore client
        self.db = get_firestore_client()
        self.ai_db = self.db
        print("✅ Connected to Firestore (Officer Resolution and AI Analysis)")

    async def close_db(self):
        # Firestore client doesn't need explicit closing in the same way
        print("✅ Firestore connections closed (No-op)")

# Global instance
officer_resolution_db = OfficerResolutionDatabase()
