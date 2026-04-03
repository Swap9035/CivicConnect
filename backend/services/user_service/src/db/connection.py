from shared.firebase_client import get_firestore_client
import os
from dotenv import load_dotenv

load_dotenv()

db = get_firestore_client()
user_collection = db.collection("users")

def get_users_collection():
    return user_collection

