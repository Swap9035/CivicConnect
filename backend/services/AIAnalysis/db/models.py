from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class AnalysisRecord(BaseModel):
    form_id: str
    user_id: str
    is_duplicate: bool
    parent_form_id: Optional[str] = None
    similarity_score: Optional[float] = None
    priority_score: int
    priority_reasoning: str
    urgency_level: str
    assigned_department: str
    assigned_officer_id: str
    assigned_officer_name: str
    estimated_response_time: str
    status: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    document_insights: Optional[str] = None  # Added for extracted document content
    
    class Config:
        json_schema_extra = {
            "example": {
                "form_id": "E40E",
                "user_id": "user123",
                "is_duplicate": False,
                "priority_score": 85,
                "urgency_level": "high",
                "document_insights": "PDF Content: [extracted text]\n\nImage Insight: [vision analysis]"
            }
        }
