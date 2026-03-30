from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel
from ..db.connection import get_grievance_forms_collection, get_clarifications_collection, get_collection
from ..models.clarification import Clarification
from ..schema.clarification import ClarificationResponse, RespondToClarificationRequest
from shared.utils.auth_middleware import get_current_user
from ..utils.notifications import clarification_notification_service
import logging

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
    
    # Get grievances for the current user (assuming 'user_id' field matches current_user)
    grievances = await grievance_col.find({"user_id": current_user}).to_list(None)
    if not grievances:
        return ClarificationResponse(clarifications=[])
    
    # Extract form_ids (assuming grievances have a 'form_id' field matching grievance_id in clarifications)
    grievance_ids = [g["form_id"] for g in grievances if "form_id" in g]
    
    # Get clarifications matching grievance_ids
    clarifications_cursor = clarification_col.find({"grievance_id": {"$in": grievance_ids}})
    clarifications = []
    async for doc in clarifications_cursor:
        clarifications.append(Clarification(
            id=str(doc["_id"]),
            resolution_id=doc["resolution_id"],
            grievance_id=doc["grievance_id"],
            officer_id=doc["officer_id"],
            message=doc["message"],
            requested_at=doc["requested_at"],
            citizen_response=doc.get("citizen_response"),
            responded_at=doc.get("responded_at")
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
    
    # Verify the clarification belongs to the user's grievances
    clarification = await clarification_col.find_one({"_id": ObjectId(clarification_id)})
    if not clarification:
        raise HTTPException(status_code=404, detail="Clarification not found")
    
    # Check if grievance_id belongs to user's grievances (match form_id with grievance_id)
    grievance = await grievance_col.find_one({"form_id": clarification["grievance_id"], "user_id": current_user})
    if not grievance:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update the clarification
    await clarification_col.update_one(
        {"_id": ObjectId(clarification_id)},
        {"$set": {"citizen_response": request.citizen_response, "responded_at": datetime.utcnow()}}
    )
    
    return {"message": "Response submitted successfully"}

async def _fetch_user_email_by_id(user_id: str):
	"""Try to find user email by common id fields across common user collections."""
	for col_name in ("users", "user_profiles", "citizens"):
		users_col = get_collection(col_name)
		queries = [{"sub": user_id}, {"user_id": user_id}, {"id": user_id}]
		try:
			queries.append({"_id": ObjectId(user_id)})
		except Exception:
			pass
		for q in queries:
			try:
				u = await users_col.find_one(q)
				if u:
					for f in ("email", "user_email", "email_primary"):
						if u.get(f):
							return u.get(f)
			except Exception:
				continue
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
    grievance = await grievance_col.find_one({"form_id": request.grievance_id})
    if not grievance:
        raise HTTPException(status_code=404, detail="Grievance not found")

    # Build clarification document
    doc = {
        "resolution_id": request.resolution_id,
        "grievance_id": request.grievance_id,
        "officer_id": current_user,
        "message": request.message,
        "requested_at": datetime.utcnow(),
        "citizen_response": None,
        "responded_at": None
    }

    try:
        await clarification_col.insert_one(doc)
    except Exception as e:
        logger.error(f"Failed to create clarification: {e}")
        raise HTTPException(status_code=500, detail="Failed to create clarification")

    # Try to find citizen email from grievance document
    citizen_email = grievance.get("user_email") or grievance.get("email")
    if not citizen_email:
        # try to fetch from userdb using grievance.user_id
        gr_user_id = grievance.get("user_id")
        if gr_user_id:
            try:
                found = await _fetch_user_email_by_id(gr_user_id)
                if found:
                    citizen_email = found
                    logger.info(f"Found citizen email from userdb for grievance {request.grievance_id}")
                else:
                    logger.warning(f"No citizen email found on grievance {request.grievance_id} or userdb; skipping email notification")
                    return {"message": "Clarification created (no email found to notify citizen)"}
            except Exception as e:
                logger.exception(f"Error fetching citizen email for grievance {request.grievance_id}: {e}")
                return {"message": "Clarification created but error occurred fetching email"}
        else:
            logger.warning(f"No citizen email or user_id present on grievance {request.grievance_id}; skipping email notification")
            return {"message": "Clarification created (no email found to notify citizen)"}

    # Send email notification (do not fail the request if email send fails; just log)
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
            logger.error(f"Clarification created but failed to send email to {citizen_email}")
            return {"message": "Clarification created but failed to send email"}
    except Exception as e:
        logger.error(f"Error sending clarification email for grievance {request.grievance_id}: {e}")
        return {"message": "Clarification created but error occurred sending email"}
