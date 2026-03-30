from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class ResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    NOT_RESOLVED = "not_resolved"

class RatingModel(BaseModel):
    overall: int = Field(..., ge=1, le=5, description="Overall satisfaction (1-5 stars)")
    speed: int = Field(..., ge=1, le=5, description="Speed rating (1-5 stars)")
    quality: int = Field(..., ge=1, le=5, description="Quality rating (1-5 stars)")

class FeedbackModel(BaseModel):
    feedback_id: str
    form_id: str = Field(..., description="Reference to original grievance")
    citizen_id: str
    officer_id: str
    ratings: RatingModel
    is_resolved_by_user: bool
    user_comment: Optional[str] = None
    citizen_evidence_path: Optional[str] = None
    conflict_detected: bool = False
    escalated: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
