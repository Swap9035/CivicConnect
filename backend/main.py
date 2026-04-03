import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from shared.firebase_client import get_firestore_client
from services.user_service.src.api.user_routes import router as user_router
from services.AIFormFilling.src.apis.routes import router as grievance_router
from services.AIAnalysis.apis.routes import router as analysis_router, monitor_grievance_submissions

# Import SuperUser service components
from services.superuser_services.utils.seed_data import create_initial_superadmin
from services.superuser_services.apis.auth_apis import router as auth_router
from services.superuser_services.apis.admin_apis import router as admin_router

# Import OfficerResolutionService components
from services.OfficerResolutionService import resolution_router

# Import ClarificationService router
from services.clarification_service.apis.routes import router as clarification_router

# Import FeedbackService router
from services.feedback_service.apis.feedback_routes import router as feedback_router

# Import Nagpur Data Service routers
from services.nagpur_data_service.apis.ward_routes import router as nagpur_ward_router
from services.nagpur_data_service.apis.analytics_routes import router as nagpur_analytics_router
from services.nagpur_data_service.apis.dataset_routes import router as nagpur_dataset_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Firebase client will be initialized on first use via shared.firebase_client
    # Seed initial roles/admins
    try:
        await create_initial_superadmin()
    except Exception as e:
        print(f"Warning: Failed to create initial superadmin: {e}")

    # Start background worker to monitor grievance submissions
    asyncio.create_task(monitor_grievance_submissions())
    yield
    # Shutdown: No explicit cleanup required for Firestore client
    pass

app = FastAPI(
    title="CivicConnect Backend (Firebase)",
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

# Include Nagpur Data Service routers
app.include_router(nagpur_ward_router, prefix="/nagpur", tags=["nagpur"])
app.include_router(nagpur_analytics_router, prefix="/nagpur/analytics", tags=["nagpur-analytics"])
app.include_router(nagpur_dataset_router, prefix="/nagpur", tags=["nagpur-datasets"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
