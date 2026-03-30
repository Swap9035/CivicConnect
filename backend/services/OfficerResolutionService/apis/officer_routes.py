from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional
from ..services.officer_service import OfficerService
from ..schemas.requests import UpdateStatusRequest, ClarificationRequest, ResolveTicketRequest
from ..schemas.responses import DashboardView, StatusUpdateResponse, ClarificationResponse, ResolutionResponse, ClarificationsListResponse, TicketCountsResponse
from ..utils.file_handler import file_handler
from ..utils.notifications import officer_notification_service
from ...superuser_services.utils.auth import get_current_user, require_role
import logging
import os
import asyncio
import pymongo
from bson import ObjectId

router = APIRouter(prefix="/officer", tags=["Officer Resolution"])

# Define officer role requirement
get_current_officer = require_role(["NODAL_OFFICER", "SUPER_ADMIN", "DEPT_ADMIN"])  # Use actual roles: NODAL_OFFICER for officers

logger = logging.getLogger(__name__)

@router.get("/dashboard", response_model=List[DashboardView])
async def get_officer_dashboard(current_officer: dict = Depends(get_current_officer)):
    """Get officer's dashboard with all assigned tickets"""
    officer_service = OfficerService()  # Instantiate here
    try:
        dashboard_data = await officer_service.get_officer_dashboard(current_officer["sub"])  # Use "sub" for user ID
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/update-status", response_model=StatusUpdateResponse)
async def update_ticket_status(
    request: UpdateStatusRequest,
    current_officer: dict = Depends(get_current_officer)
):
    """Update ticket status (Assigned -> In Progress, etc.)"""
    officer_service = OfficerService()  # Instantiate here
    try:
        result = await officer_service.update_ticket_status(
            officer_id=current_officer["sub"],  # Use "sub" for user ID
            grievance_id=request.grievance_id,
            new_status=request.new_status,
            progress_note=request.progress_note
        )
        
        return StatusUpdateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/resolved", response_model=List[DashboardView])
async def get_resolved_tickets(current_officer: dict = Depends(get_current_officer)):
    """Get all resolved tickets for the officer"""
    officer_service = OfficerService()  # Instantiate here
    try:
        result = await officer_service.get_resolved_tickets(current_officer["sub"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/request-clarification", response_model=ClarificationResponse)
async def request_clarification(
    request: ClarificationRequest,
    current_officer: dict = Depends(get_current_officer)
):
    """Send clarification request to citizen"""
    officer_service = OfficerService()  # Instantiate here
    try:
        result = await officer_service.request_clarification(
            officer_id=current_officer["sub"],  # Use "sub" for user ID
            grievance_id=request.grievance_id,
            message=request.message
        )

        # Try to notify citizen by email; do not fail if email send fails
        citizen_email = None
        if isinstance(result, dict):
            citizen_email = result.get("citizen_email") or result.get("email") or result.get("user_email")
        # If still missing, try to locate user_id from the officer dashboard and fetch from userdb
        if not citizen_email:
            try:
                # try to find the ticket in the officer dashboard
                tickets = await officer_service.get_officer_dashboard(current_officer["sub"])
                ticket = next((t for t in tickets if getattr(t.ticket, "grievance_id", None) == request.grievance_id), None)
                found_user_id = None
                if ticket:
                    tdata = getattr(ticket, "ticket", None)
                    if isinstance(tdata, dict):
                        found_user_id = tdata.get("user_id") or tdata.get("owner_id") or tdata.get("citizen_id")
                    else:
                        found_user_id = getattr(tdata, "user_id", None) or getattr(tdata, "owner_id", None) or getattr(tdata, "citizen_id", None)
                if found_user_id:
                    fetched = await _fetch_user_email_by_id(found_user_id)
                    if fetched:
                        citizen_email = fetched
                        logger.info(f"Found citizen email from userdb for grievance {request.grievance_id}")
            except Exception as e:
                logger.exception(f"Error while attempting to find citizen email for grievance {request.grievance_id}: {e}")
        if citizen_email:
             try:
                 sent = await officer_notification_service.send_clarification_email(
                     to_email=citizen_email,
                     grievance_id=request.grievance_id,
                     officer_id=current_officer["sub"],
                     message=request.message
                 )
                 if sent:
                     logger.info(f"Clarification email sent to {citizen_email} for {request.grievance_id}")
                 else:
                     logger.error(f"Failed to send clarification email to {citizen_email} for {request.grievance_id}")
             except Exception as e:
                 logger.exception(f"Error sending clarification email for {request.grievance_id}: {e}")
        else:
            logger.warning(f"No citizen email found for grievance {request.grievance_id}; skipping clarification email")

        return ClarificationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resolve", response_model=ResolutionResponse)
async def resolve_ticket(
    grievance_id: str = Form(...),
    action_taken: str = Form(...),
    closing_remark: str = Form(...),
    resolution_photos: List[UploadFile] = File(...),
    current_officer: dict = Depends(get_current_officer)
):
    """Resolve ticket with mandatory proof photos"""
    officer_service = OfficerService()  # Instantiate here
    try:
        # Validate files
        if not resolution_photos:
            raise HTTPException(status_code=400, detail="Resolution photos are mandatory")
        
        # Save uploaded photos
        photo_paths = await file_handler.save_resolution_photos(
            files=resolution_photos,
            officer_id=current_officer["sub"],  # Use "sub" for user ID
            grievance_id=grievance_id
        )
        
        # Resolve ticket
        result = await officer_service.resolve_ticket(
            officer_id=current_officer["sub"],  # Use "sub" for user ID
            grievance_id=grievance_id,
            action_taken=action_taken,
            closing_remark=closing_remark,
            resolution_photos=photo_paths
        )

        # Try to notify citizen by email; do not fail if email send fails
        citizen_email = None
        if isinstance(result, dict):
            citizen_email = result.get("citizen_email") or result.get("email") or result.get("user_email")
        # If missing, try to find user_id via officer dashboard and fetch email from userdb
        if not citizen_email:
            try:
                tickets = await officer_service.get_officer_dashboard(current_officer["sub"])
                ticket = next((t for t in tickets if getattr(t.ticket, "grievance_id", None) == grievance_id), None)
                found_user_id = None
                if ticket:
                    tdata = getattr(ticket, "ticket", None)
                    if isinstance(tdata, dict):
                        found_user_id = tdata.get("user_id") or tdata.get("owner_id") or tdata.get("citizen_id")
                    else:
                        found_user_id = getattr(tdata, "user_id", None) or getattr(tdata, "owner_id", None) or getattr(tdata, "citizen_id", None)
                if found_user_id:
                    fetched = await _fetch_user_email_by_id(found_user_id)
                    if fetched:
                        citizen_email = fetched
                        logger.info(f"Found citizen email from userdb for grievance {grievance_id}")
            except Exception as e:
                logger.exception(f"Error while attempting to find citizen email for grievance {grievance_id}: {e}")
        if citizen_email:
             try:
                 sent = await officer_notification_service.send_resolution_email(
                     to_email=citizen_email,
                     grievance_id=grievance_id,
                     officer_id=current_officer["sub"],
                     action_taken=action_taken,
                     closing_remark=closing_remark
                 )
                 if sent:
                     logger.info(f"Resolution email sent to {citizen_email} for {grievance_id}")
                 else:
                     logger.error(f"Failed to send resolution email to {citizen_email} for {grievance_id}")
             except Exception as e:
                 logger.exception(f"Error sending resolution email for {grievance_id}: {e}")
        else:
            logger.warning(f"No citizen email found for grievance {grievance_id}; skipping resolution email")
        
        return ResolutionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ticket/{grievance_id}", response_model=DashboardView)
async def get_ticket_details(
    grievance_id: str,
    current_officer: dict = Depends(get_current_officer)
):
    """Get detailed view of a specific ticket"""
    officer_service = OfficerService()  # Instantiate here
    try:
        tickets = await officer_service.get_officer_dashboard(current_officer["sub"])  # Use "sub" for user ID
        ticket = next((t for t in tickets if t.ticket.grievance_id == grievance_id), None)
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return ticket
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clarifications", response_model=ClarificationsListResponse)
async def get_clarifications(current_officer: dict = Depends(get_current_officer)):
    """Get all clarifications requested by the officer"""
    officer_service = OfficerService()  # Instantiate here
    try:
        result = await officer_service.get_clarifications(current_officer["sub"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/total", response_model=TicketCountsResponse)
async def get_ticket_counts(current_officer: dict = Depends(get_current_officer)):
    """Get total counts of tickets by status for the officer"""
    officer_service = OfficerService()  # Instantiate here
    try:
        # Workaround: Fetch dashboard data and count statuses manually
        dashboard_data = await officer_service.get_officer_dashboard(current_officer["sub"])
        
        # Initialize counts
        counts = {
            "assigned": 0,
            "in_progress": 0,
            "completed": 0,
            "clarifications": 0
        }
        
        # Count statuses from dashboard tickets
        for item in dashboard_data:
            ticket = getattr(item, 'ticket', None)
            if ticket:
                status = getattr(ticket, 'status', '').lower()
                if status in counts:
                    counts[status] += 1
        
        return TicketCountsResponse(**counts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/start", response_model=StatusUpdateResponse)
async def start_ticket_work(
    request: UpdateStatusRequest,
    current_officer: dict = Depends(get_current_officer)
):
    """Convenience endpoint to mark a ticket as in_progress (start work)"""
    officer_service = OfficerService()
    try:
        result = await officer_service.update_ticket_status(
            officer_id=current_officer["sub"],
            grievance_id=request.grievance_id,
            new_status="in_progress",
            progress_note=request.progress_note
        )
        return StatusUpdateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/pause", response_model=StatusUpdateResponse)
async def pause_ticket_work(
    request: UpdateStatusRequest,
    current_officer: dict = Depends(get_current_officer)
):
    """Convenience endpoint to mark a ticket as paused"""
    officer_service = OfficerService()
    try:
        result = await officer_service.update_ticket_status(
            officer_id=current_officer["sub"],
            grievance_id=request.grievance_id,
            new_status="paused",
            progress_note=request.progress_note
        )
        return StatusUpdateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/resume", response_model=StatusUpdateResponse)
async def resume_ticket_work(
    request: UpdateStatusRequest,
    current_officer: dict = Depends(get_current_officer)
):
    """Convenience endpoint to resume work (set to in_progress)"""
    officer_service = OfficerService()
    try:
        result = await officer_service.update_ticket_status(
            officer_id=current_officer["sub"],
            grievance_id=request.grievance_id,
            new_status="in_progress",
            progress_note=request.progress_note
        )
        return StatusUpdateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "OfficerResolutionService"}

def _sync_find_user_email(user_id: str):
    """Synchronous DB lookup for a user's email; run in a thread via asyncio.to_thread."""
    mongo_uri = os.getenv("MONGO_URI") or os.getenv("MONGO_CONNECTION_STRING")
    mongo_db = os.getenv("MONGO_DB", "admin")
    if not mongo_uri:
        raise RuntimeError("MONGO_URI not configured")

    client = pymongo.MongoClient(mongo_uri)
    try:
        db = client[mongo_db]
        # try common collections and id fields
        for col_name in ("users", "user_profiles", "citizens"):
            col = db.get_collection(col_name)
            queries = [{"sub": user_id}, {"user_id": user_id}, {"id": user_id}]
            try:
                queries.append({"_id": ObjectId(user_id)})
            except Exception:
                pass
            for q in queries:
                doc = col.find_one(q)
                if doc:
                    for f in ("email", "user_email", "email_primary", "contact_email"):
                        if doc.get(f):
                            return doc.get(f)
        return None
    finally:
        client.close()

async def _fetch_user_email_by_id(user_id: str):
    try:
        return await asyncio.to_thread(_sync_find_user_email, user_id)
    except Exception as e:
        logger.exception(f"Error fetching user email from userdb for {user_id}: {e}")
        return None
