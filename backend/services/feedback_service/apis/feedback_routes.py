from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import List, Optional
import json
import os
import uuid
from datetime import datetime
import logging
from bson import ObjectId, Decimal128
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
from ..utils.sentiment_analyzer import analyze_sentiment  # new import

# Import get_current_user for authentication
from services.user_service.src.api.user_routes import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"])

UPLOAD_DIR = "uploads/feedback"
os.makedirs(UPLOAD_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

def _sanitize_obj(obj):
    """Recursive sanitizer: ObjectId -> str, datetime -> isoformat, convert dicts/lists.
    Be defensive and always return a JSON-safe value (fallback to str(obj))."""
    try:
        if obj is None:
            return None
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, Decimal128):
            return str(obj.to_decimal())
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
        # Fallback for any other types (e.g., DBRef, custom types)
        return str(obj)
    except Exception:
        # Last-resort fallback to avoid raising during response building
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
        
        citizen_id = current_user  # Assuming current_user is the user ID string

        # Extract officer id safely from several possible field names
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

        # Analyze sentiment of the user comment (run in thread if analyzer is sync)
        if feedback_schema.user_comment:
            sentiment = await asyncio.to_thread(analyze_sentiment, feedback_schema.user_comment)
        else:
            sentiment = {"label": "neutral", "score": 0.5, "explanation": "no comment provided"}

        # attach sentiment to data
        feedback_data_dict["sentiment"] = sentiment

        # Process conflict resolution (pass sentiment)
        resolution_result = await conflict_resolver.process_feedback(
            feedback_data_dict, 
            evidence_path,
            sentiment=sentiment
        )
        
        if "error" in resolution_result:
            raise HTTPException(status_code=400, detail=resolution_result["error"])
        
        # Update feedback data with conflict resolution
        feedback_data_dict.update({
            "conflict_detected": resolution_result["conflict_detected"],
            "escalated": resolution_result["escalated"]
        })
        
        # Save feedback to database
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
        
        # Get officer name from superuser db (you may need to adjust this based on your schema)
        # For now, using placeholder
        stats["officer_name"] = f"Officer {officer_id}"
        
        return OfficerStatsSchema(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching officer stats: {str(e)}")

@router.get("/id/{feedback_id}", response_model=FeedbackResponseSchema)
async def get_feedback_details(feedback_id: str):
    """Get detailed feedback information (use /feedback/id/{feedback_id})"""
    try:
        feedback = await feedback_db.get_feedback_by_id(feedback_id)
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        # Convert datetime to string for response
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
        pipeline = [
            {"$match": {"conflict_detected": True}},
            {"$sort": {"created_at": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]

        cursor = feedback_db.feedback_collection.aggregate(pipeline)
        conflicts = await cursor.to_list(length=limit)

        total = await feedback_db.feedback_collection.count_documents({"conflict_detected": True})

        # sanitize documents defensively and log any failures
        sanitized = []
        for i, c in enumerate(conflicts):
            try:
                sanitized.append(_sanitize_obj(c))
            except Exception as ex:
                logger.exception("Sanitization failed for conflict index %s (id=%s)", i, c.get("feedback_id", c.get("_id")))
                sanitized.append({"_raw": str(c)})

        return {"conflicts": sanitized, "total": total}

    except Exception as e:
        logger.exception("Error fetching conflicts")
        raise HTTPException(status_code=500, detail=f"Internal server error (see server logs): {str(e)}")

@router.get("/list")
async def list_feedbacks(skip: int = 0, limit: int = 50):
    """Paginated list of all feedbacks (admin use)"""
    try:
        cursor = feedback_db.feedback_collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
        items = await cursor.to_list(length=limit)
        total = await feedback_db.feedback_collection.count_documents({})

        sanitized_items = []
        for i, it in enumerate(items):
            try:
                sanitized_items.append(_sanitize_obj(it))
            except Exception as ex:
                logger.exception("Sanitization failed for feedback index %s (id=%s)", i, it.get("feedback_id", it.get("_id")))
                sanitized_items.append({"_raw": str(it)})

        return {"feedbacks": sanitized_items, "total": total}
    except Exception as e:
        logger.exception("Error listing feedbacks")
        raise HTTPException(status_code=500, detail=f"Internal server error (see server logs): {str(e)}")
