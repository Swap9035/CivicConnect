from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Clarification(BaseModel):
    id: str
    resolution_id: str
    grievance_id: str
    officer_id: str
    message: str
    requested_at: datetime
    citizen_response: Optional[str] = None
    responded_at: Optional[datetime] = None
