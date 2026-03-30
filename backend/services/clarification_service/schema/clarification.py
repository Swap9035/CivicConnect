from pydantic import BaseModel
from typing import List, Optional
from services.clarification_service.models.clarification import Clarification

class ClarificationResponse(BaseModel):
    clarifications: List[Clarification]

class RespondToClarificationRequest(BaseModel):
    citizen_response: str
