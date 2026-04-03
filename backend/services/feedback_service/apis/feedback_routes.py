from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import List, Optional
import json
import os
import uuid
from datetime import datetime, timezone
import logging
import base64
import asyncio

from ..schemas.feedback_schema import (
    FeedbackSubmissionSchema, 
    FeedbackResponseSchema,
    PendingFeedbackSchema,
    OfficerStatsSchema
)
from ..db.feedback_db import feedback_db
from ..utils.conflict_resolver import conflict_resolver
from ..utils.sentiment_analyzer import analyze_sentiment
from shared.firebase_client import get_firestore_client

# Import get_current_user for authentication
from services.user_service.src.api.user_routes import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"])

UPLOAD_DIR = "uploads/feedback"
os.makedirs(UPLOAD_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

def _sanitize_obj(obj):
    """Recursive sanitizer: datetime -> isoformat, convert dicts/lists.
    Be defensive and always return a JSON-safe value (fallback to str(obj))."""
    try:
        if obj is None:
            return None
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode("ascii")
        if isinstance(obj, (list, tuple, set)):
            return [_sanitize_obj(v) for v in obj]
        if isinstance(obj, dict):
            return {k: _sanitize_obj(v) for k, v in obj.items()}
        # Fallback for any other types
        return str(obj)
    except Exception:
        try:
            return str(obj)
        except Exception:
            return "<unserializable>"

@router.get("/pending", response_model=List[PendingFeedbackSchema])
async def get_pending_feedbacks(current_user = Depends(get_current_user)):
    """Get all resolved grievances that haven't been rated by the current authenticated user"""
    try:
        citizen_id = current_user  # Assuming current_user is the user ID string
        pending = await feedback_db.get_pending_feedbacks(citizen_id)
        return pending
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pending feedbacks: {str(e)}")

@router.post("/submit", response_model=dict)
async def submit_feedback(
    feedback_data: str = Form(...),
    evidence: Optional[UploadFile] = File(None),
    current_user = Depends(get_current_user)
):
    """Submit feedback with optional evidence image for the current authenticated user"""
    try:
        # Parse feedback data
        feedback_json = json.loads(feedback_data)
        feedback_schema = FeedbackSubmissionSchema(**feedback_json)
        
        # Get grievance details to find officer_id
        grievance = await feedback_db.get_grievance_details(feedback_schema.form_id)
        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")
        
        citizen_id = current_user
        officer_id = (
            grievance.get("officer_id") or grievance.get("officerId") or
            grievance.get("assigned_officer_id") or grievance.get("assigned_officer") or
            grievance.get("officer") or None
        )
        
        # Handle evidence upload
        evidence_path = None
        if evidence:
            filename = f"fb_{uuid.uuid4().hex[:8]}_{evidence.filename}"
            evidence_path = os.path.join(UPLOAD_DIR, filename)
            
            with open(evidence_path, "wb") as buffer:
                content = await evidence.read()
                buffer.write(content)
        
        # Prepare feedback data
        feedback_data_dict = {
            "form_id": feedback_schema.form_id,
            "citizen_id": citizen_id,
            "officer_id": officer_id,
            "ratings": feedback_schema.ratings.dict(),
            "is_resolved_by_user": feedback_schema.is_resolved_by_user,
            "user_comment": feedback_schema.user_comment,
            "citizen_evidence_path": evidence_path
        }

        # Analyze sentiment
        if feedback_schema.user_comment:
            sentiment = await asyncio.to_thread(analyze_sentiment, feedback_schema.user_comment)
        else:
            sentiment = {"label": "neutral", "score": 0.5, "explanation": "no comment provided"}

        feedback_data_dict["sentiment"] = sentiment

        # Process conflict resolution
        resolution_result = await conflict_resolver.process_feedback(
            feedback_data_dict, 
            evidence_path,
            sentiment=sentiment
        )
        
        if "error" in resolution_result:
            raise HTTPException(status_code=400, detail=resolution_result["error"])
        
        feedback_data_dict.update({
            "conflict_detected": resolution_result["conflict_detected"],
            "escalated": resolution_result["escalated"]
        })
        
        # Save feedback
        feedback_id = await feedback_db.create_feedback(feedback_data_dict)
        
        return {
            "feedback_id": feedback_id,
            "status": "success",
            "action": resolution_result["action"],
            "conflict_detected": resolution_result["conflict_detected"],
            "escalated": resolution_result["escalated"],
            "message": resolution_result.get("message", "Feedback submitted successfully"),
            "sentiment": sentiment
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid feedback data format")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error submitting feedback")
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

@router.get("/stats/{officer_id}", response_model=OfficerStatsSchema)
async def get_officer_stats(officer_id: str):
    """Get performance statistics for a specific officer"""
    try:
        stats = await feedback_db.get_officer_stats(officer_id)
        stats["officer_name"] = f"Officer {officer_id}"
        return OfficerStatsSchema(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching officer stats: {str(e)}")

@router.get("/id/{feedback_id}", response_model=FeedbackResponseSchema)
async def get_feedback_details(feedback_id: str):
    """Get detailed feedback information"""
    try:
        feedback = await feedback_db.get_feedback_by_id(feedback_id)
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        if isinstance(feedback["created_at"], datetime):
            feedback["created_at"] = feedback["created_at"].isoformat()
        
        return FeedbackResponseSchema(**feedback)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching feedback details")
        raise HTTPException(status_code=500, detail=f"Error fetching feedback: {str(e)}")

@router.get("/conflicts/list")
async def get_conflicts(skip: int = 0, limit: int = 20):
    """Get list of all conflicts for admin review"""
    try:
        db = get_firestore_client()
        query = db.collection("feedback").where("conflict_detected", "==", True)\
                  .order_by("created_at", direction="DESCENDING")\
                  .offset(skip).limit(limit)
        
        docs = query.stream()
        conflicts = []
        async for doc in docs:
            conflicts.append(doc.to_dict())

        # Total count
        total_snap = await db.collection("feedback").where("conflict_detected", "==", True).count().get()
        total = total_snap[0].value

        sanitized = [_sanitize_obj(c) for c in conflicts]
        return {"conflicts": sanitized, "total": total}

    except Exception as e:
        logger.exception("Error fetching conflicts")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/list")
async def list_feedbacks(skip: int = 0, limit: int = 50):
    """Paginated list of all feedbacks (admin use)"""
    try:
        db = get_firestore_client()
        query = db.collection("feedback").order_by("created_at", direction="DESCENDING")\
                  .offset(skip).limit(limit)
        
        docs = query.stream()
        items = []
        async for doc in docs:
            items.append(doc.to_dict())
            
        total_snap = await db.collection("feedback").count().get()
        total = total_snap[0].value

        sanitized_items = [_sanitize_obj(it) for it in items]
        return {"feedbacks": sanitized_items, "total": total}
    except Exception as e:
        logger.exception("Error listing feedbacks")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

