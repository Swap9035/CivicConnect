from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel
from ..db.connection import get_grievance_forms_collection, get_clarifications_collection, get_collection
from ..models.clarification import Clarification
from ..schema.clarification import ClarificationResponse, RespondToClarificationRequest
from shared.utils.auth_middleware import get_current_user
from ..utils.notifications import clarification_notification_service
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()

# New request model for officers creating a clarification
class CreateClarificationRequest(BaseModel):
    grievance_id: str
    resolution_id: Optional[str] = None
    message: str

# expose both "/clarifications" (current) and root "/" so GET /clarifications works
@router.get("/", response_model=ClarificationResponse)
@router.get("/clarifications", response_model=ClarificationResponse)
async def get_clarifications(current_user: str = Depends(get_current_user)):
    grievance_col = get_grievance_forms_collection()
    clarification_col = get_clarifications_collection()
    
    # Get grievances for the current user
    docs = grievance_col.where("user_id", "==", current_user).stream()
    grievance_ids = []
    async for doc in docs:
        data = doc.to_dict()
        fid = data.get("form_id") or doc.id
        grievance_ids.append(fid)

    if not grievance_ids:
        return ClarificationResponse(clarifications=[])
    
    # Get clarifications matching grievance_ids
    # Note: Firestore 'in' limit is 30. For simplicity, we assume < 30.
    clarifications = []
    # If more than 30, we'd need to chunk.
    for i in range(0, len(grievance_ids), 30):
        chunk = grievance_ids[i:i + 30]
        docs = clarification_col.where("grievance_id", "in", chunk).stream()
        async for doc in docs:
            data = doc.to_dict()
            clarifications.append(Clarification(
                id=doc.id,
                resolution_id=data.get("resolution_id") or "",
                grievance_id=data.get("grievance_id"),
                officer_id=data.get("officer_id"),
                message=data.get("message"),
                requested_at=data.get("requested_at"),
                citizen_response=data.get("citizen_response"),
                responded_at=data.get("responded_at")
            ))
    
    return ClarificationResponse(clarifications=clarifications)

# expose both "/{id}/respond" (root) and "/clarifications/{id}/respond" for compatibility
@router.post("/{clarification_id}/respond")
@router.post("/clarifications/{clarification_id}/respond")
async def respond_to_clarification(
    clarification_id: str,
    request: RespondToClarificationRequest,
    current_user: str = Depends(get_current_user)
):
    grievance_col = get_grievance_forms_collection()
    clarification_col = get_clarifications_collection()
    
    # Verify the clarification exists
    doc_ref = clarification_col.document(clarification_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Clarification not found")
    
    clarification = doc.to_dict()
    
    # Check if grievance_id belongs to user's grievances
    docs = grievance_col.where("form_id", "==", clarification["grievance_id"])\
                        .where("user_id", "==", current_user).limit(1).stream()
    
    grievance_found = False
    async for _ in docs:
        grievance_found = True
        break
        
    if not grievance_found:
        # Try doc ID if form_id didn't match
        doc = await grievance_col.document(clarification["grievance_id"]).get()
        if doc.exists and doc.to_dict().get("user_id") == current_user:
            grievance_found = True

    if not grievance_found:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update the clarification
    await doc_ref.update({
        "citizen_response": request.citizen_response, 
        "responded_at": datetime.now(timezone.utc)
    })
    
    return {"message": "Response submitted successfully"}

async def _fetch_user_email_by_id(user_id: str):
    """Try to find user email in Firestore 'users' collection."""
    users_col = get_collection("users")
    
    # Try doc ID
    doc_ref = users_col.document(user_id)
    doc = await doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        return data.get("email") or data.get("user_email")
        
    # Try field searches
    for field in ("sub", "user_id", "id"):
        docs = users_col.where(field, "==", user_id).limit(1).stream()
        async for doc in docs:
            data = doc.to_dict()
            return data.get("email") or data.get("user_email")
            
    return None

# expose both "/" (current) and "/clarifications" so POST /clarifications works for creation
@router.post("/", status_code=201)
@router.post("/clarifications", status_code=201)
async def create_clarification(
    request: CreateClarificationRequest,
    current_user: str = Depends(get_current_user)
):
    """Officer creates a clarification for a grievance; citizen is emailed the clarification."""
    grievance_col = get_grievance_forms_collection()
    clarification_col = get_clarifications_collection()

    # Verify grievance exists
    doc_ref = grievance_col.document(request.grievance_id)
    doc = await doc_ref.get()
    grievance = doc.to_dict() if doc.exists else None
    
    if not grievance:
        docs = grievance_col.where("form_id", "==", request.grievance_id).limit(1).stream()
        async for d in docs:
            grievance = d.to_dict()
            break
            
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found")

    # Build clarification document
    clarification_id = f"CLR_{uuid.uuid4().hex[:8].upper()}"
    doc_data = {
        "resolution_id": request.resolution_id,
        "grievance_id": request.grievance_id,
        "officer_id": current_user,
        "message": request.message,
        "requested_at": datetime.now(timezone.utc),
        "citizen_response": None,
        "responded_at": None
    }

    try:
        await clarification_col.document(clarification_id).set(doc_data)
    except Exception as e:
        logger.error(f"Failed to create clarification: {e}")
        raise HTTPException(status_code=500, detail="Failed to create clarification")

    # Try to find citizen email
    citizen_email = grievance.get("user_email") or grievance.get("email")
    if not citizen_email:
        gr_user_id = grievance.get("user_id")
        if gr_user_id:
            try:
                found = await _fetch_user_email_by_id(gr_user_id)
                if found:
                    citizen_email = found
                else:
                    return {"message": "Clarification created (no email found to notify citizen)"}
            except Exception as e:
                logger.exception(f"Error fetching citizen email: {e}")
                return {"message": "Clarification created but error occurred fetching email"}
        else:
            return {"message": "Clarification created (no email found to notify citizen)"}

    # Send email notification
    try:
        sent = await clarification_notification_service.send_clarification_email(
            to_email=citizen_email,
            grievance_id=request.grievance_id,
            officer_id=current_user,
            message=request.message,
            resolution_id=request.resolution_id
        )
        if sent:
            return {"message": "Clarification created and citizen notified via email"}
        else:
            return {"message": "Clarification created but failed to send email"}
    except Exception as e:
        logger.error(f"Error sending clarification email: {e}")
        return {"message": "Clarification created but error occurred sending email"}

