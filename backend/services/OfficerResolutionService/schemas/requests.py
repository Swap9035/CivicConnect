from pydantic import BaseModel
from typing import Optional, List
from ..models.resolution import TicketStatus

class UpdateStatusRequest(BaseModel):
    grievance_id: str
    new_status: TicketStatus
    progress_note: Optional[str] = None

class ClarificationRequest(BaseModel):
    grievance_id: str
    message: str

class ResolveTicketRequest(BaseModel):
    grievance_id: str
    action_taken: str
    closing_remark: str
    resolution_photos: List[str]  # File paths after upload

class ProgressUpdateRequest(BaseModel):
    grievance_id: str
    update_message: str
