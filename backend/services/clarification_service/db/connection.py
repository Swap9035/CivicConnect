from typing import Any
from shared.firebase_client import get_firestore_client
import logging

logger = logging.getLogger(__name__)

def _get_db():
    return get_firestore_client()

def get_collection(name: str) -> Any:
    """Return a Firestore collection by name."""
    db = _get_db()
    name = (name or "").lower()
    
    # Map legacy names to Firestore collections
    if name in ("grievance_forms", "grievances", "forms"):
        return db.collection("grievance_forms")
    if name in ("clarifications", "clarification"):
        return db.collection("clarifications")
    if name in ("users", "user_profiles", "citizens"):
        return db.collection("users")
        
    return db.collection(name)

def get_grievance_forms_collection():
    return _get_db().collection("grievance_forms")

def get_clarifications_collection():
    return _get_db().collection("clarifications")
