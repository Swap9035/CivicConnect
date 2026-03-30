from fastapi import APIRouter
from .apis.officer_routes import router as officer_router
from .config.database import officer_resolution_db

# Main router for the service
resolution_router = APIRouter(prefix="/resolution")
resolution_router.include_router(officer_router)

# Database lifecycle management
async def init_officer_resolution_service():
    """Initialize the officer resolution service"""
    await officer_resolution_db.connect_db()
    print("✅ Officer Resolution Service initialized")

async def cleanup_officer_resolution_service():
    """Cleanup the officer resolution service"""
    await officer_resolution_db.close_db()
    print("✅ Officer Resolution Service cleaned up")

__all__ = ["resolution_router", "init_officer_resolution_service", "cleanup_officer_resolution_service"]
