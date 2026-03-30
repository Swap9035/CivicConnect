from motor.motor_asyncio import AsyncIOMotorClient
from typing import Any
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = AsyncIOMotorClient(MONGO_URI)

_GLOBAL_CLIENT: AsyncIOMotorClient | None = None

def _get_db():
	"""Return the configured motor database instance."""
	global _GLOBAL_CLIENT
	if _GLOBAL_CLIENT is None:
		mongo_uri = os.getenv("MONGO_URI") or os.getenv("MONGO_CONNECTION_STRING")
		if not mongo_uri:
			raise RuntimeError("MONGO_URI (or MONGO_CONNECTION_STRING) not configured")
		_GLOBAL_CLIENT = AsyncIOMotorClient(mongo_uri)
	db_name = os.getenv("MONGO_DB", "admin")
	return _GLOBAL_CLIENT[db_name]

def get_collection(name: str) -> Any:
	"""Return a collection by name.
	Known names map to existing helper functions (backwards-compatible).
	Falls back to the generic DB collection if not one of the known names.
	"""
	name = (name or "").lower()
	# Known explicit collections using existing helpers
	if name in ("grievance_forms", "grievances", "forms"):
		return get_grievance_forms_collection()
	if name in ("clarifications", "clarification"):
		return get_clarifications_collection()
	# Generic fallback
	db = _get_db()
	return db[name]

def get_grievance_db():
    return client.grievance_db

def get_grievance_forms_collection():
    return get_grievance_db().grievance_forms

def get_officer_resolution_db():
    return client.officer_resolution_db

def get_clarifications_collection():
    return get_officer_resolution_db().clarifications
