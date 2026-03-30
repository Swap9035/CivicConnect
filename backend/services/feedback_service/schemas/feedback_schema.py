from pydantic import BaseModel, Field
from typing import Optional
from services.feedback_service.models.feedback_model import RatingModel, ResolutionStatus

class SentimentSchema(BaseModel):
    label: str
    score: float
    explanation: Optional[str] = None

class FeedbackSubmissionSchema(BaseModel):
    form_id: str
    ratings: RatingModel
    is_resolved_by_user: bool
    user_comment: Optional[str] = None

class FeedbackResponseSchema(BaseModel):
    feedback_id: str
    form_id: str
    citizen_id: str
    officer_id: str
    ratings: RatingModel
    is_resolved_by_user: bool
    user_comment: Optional[str]
    conflict_detected: bool
    escalated: bool
    created_at: str
    sentiment: Optional[SentimentSchema] = None  # new field

class PendingFeedbackSchema(BaseModel):
    form_id: str
    grievance_title: str
    officer_name: str
    resolved_date: str
    officer_evidence_path: Optional[str]

class OfficerStatsSchema(BaseModel):
    officer_id: str
    officer_name: str
    total_feedbacks: int
    average_rating: float
    conflict_rate: float
    escalation_rate: float
    performance_score: float
