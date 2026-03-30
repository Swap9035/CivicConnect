from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field
from enum import Enum

class TicketStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress" 
    SEEKING_INFO = "seeking_info"
    RESOLVED = "resolved"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ResolutionRecord(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    grievance_id: str
    officer_id: str
    officer_name: str
    status: TicketStatus = TicketStatus.ASSIGNED
    priority_level: Priority
    priority_reasoning: str
    cluster_info: Optional[Dict[str, Any]] = None
    
    # Progress tracking
    assigned_at: datetime
    started_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Media and documentation
    original_documents: List[str] = []
    resolution_photos: List[str] = []
    
    # Communication
    clarification_requests: List[Dict[str, Any]] = []
    progress_updates: List[Dict[str, Any]] = []
    
    # Resolution details
    action_taken: Optional[str] = None
    closing_remark: Optional[str] = None
    completion_time_hours: Optional[float] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class ClarificationRequest(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    resolution_id: str
    grievance_id: str
    officer_id: str
    message: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    citizen_response: Optional[str] = None
    responded_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
