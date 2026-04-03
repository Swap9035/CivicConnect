import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore_async

# Determine the path to the firebase-key.json
FIREBASE_KEY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "firebase-key.json")

def _initialize_firebase():
    if not firebase_admin._apps:
        try:
            # Use the provided service account key
            cred = credentials.Certificate(FIREBASE_KEY_PATH)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Error initializing Firebase Admin SDK: {str(e)}")
            raise e

_initialize_firebase()
db = firestore_async.client()

def get_firestore_client():
    return db

