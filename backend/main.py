import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import asyncio

from services.user_service.src.api.user_routes import router as user_router
from services.AIFormFilling.src.apis.routes import router as grievance_router
from services.AIFormFilling.src.db.connection import connect_to_mongo, close_mongo_connection
from services.AIAnalysis.apis.routes import router as analysis_router, monitor_grievance_submissions
from services.AIAnalysis.db.connection import connect_to_mongo as connect_analysis_mongo, close_mongo_connection as close_analysis_mongo

# Import SuperUser service components
from services.superuser_services.config import settings as superuser_settings
from services.superuser_services.db.connection import connect_to_mongo as connect_superuser_mongo, close_mongo_connection as close_superuser_mongo
from services.superuser_services.utils.seed_data import create_initial_superadmin, seed_sample_data
from services.superuser_services.apis.auth_apis import router as auth_router
from services.superuser_services.apis.admin_apis import router as admin_router

# Import OfficerResolutionService components
from services.OfficerResolutionService import resolution_router, init_officer_resolution_service, cleanup_officer_resolution_service

# Import ClarificationService router
from services.clarification_service.apis.routes import router as clarification_router

# Import FeedbackService router
from services.feedback_service.apis.feedback_routes import router as feedback_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()  # For grievance service
    connect_analysis_mongo()  # For analysis service (synchronous)
    await connect_superuser_mongo()  # For SuperUser service
    await init_officer_resolution_service()  # For OfficerResolutionService
    await create_initial_superadmin()

    # Start background worker to monitor grievance submissions
    asyncio.create_task(monitor_grievance_submissions())
    yield
    # Shutdown
    await close_mongo_connection()  # For grievance service
    close_analysis_mongo()  # For analysis service (synchronous)
    await close_superuser_mongo()  # For SuperUser service
    await cleanup_officer_resolution_service()  # For OfficerResolutionService

app = FastAPI(
    title="GFG Backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(grievance_router, prefix="/grievance")
app.include_router(analysis_router, prefix="/analysis", tags=["analysis"])

# Include SuperUser routers
app.include_router(auth_router, prefix="/superuser/auth")
app.include_router(admin_router, prefix="/superuser/admin")

# Include OfficerResolutionService router
app.include_router(resolution_router)

# Include ClarificationService router
app.include_router(clarification_router, prefix="/clarifications", tags=["clarifications"])

# Include FeedbackService router
app.include_router(feedback_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
