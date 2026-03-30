from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..models.resolution import TicketStatus, Priority

class TicketOverview(BaseModel):
    grievance_id: str
    status: TicketStatus
    priority_level: Priority
    priority_reasoning: str
    cluster_info: Optional[Dict[str, Any]] = None
    assigned_at: datetime
    started_at: Optional[datetime] = None  # Ensure this is Optional
    resolved_at: Optional[datetime] = None
    original_documents: List[str] = []

class DashboardView(BaseModel):
    ticket: TicketOverview
    urgency_banner: str
    context_panel: str
    cluster_summary: str
    media_gallery: List[str]

class StatusUpdateResponse(BaseModel):
    success: bool
    message: str
    new_status: TicketStatus
    updated_at: datetime

class ClarificationResponse(BaseModel):
    success: bool
    message: str
    clarification_id: str
    sent_at: datetime

class ClarificationItem(BaseModel):
    clarification_id: str
    grievance_id: str
    officer_id: str
    message: str
    requested_at: datetime
    citizen_response: Optional[str] = None
    responded_at: Optional[datetime] = None

class ClarificationsListResponse(BaseModel):
    clarifications: List[ClarificationItem]

class ResolutionResponse(BaseModel):
    success: bool
    message: str
    resolved_at: datetime
    completion_time_hours: float

class TicketCountsResponse(BaseModel):
    assigned: int
    in_progress: int
    completed: int  # Removed "resolved" as it's same as "completed"
    clarifications: int
