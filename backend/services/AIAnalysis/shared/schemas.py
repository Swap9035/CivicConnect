from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class GrievanceData(BaseModel):
    form_id: str
    user_id: str
    title: str
    full_description: str
    category: str
    area_ward_name: Optional[str] = None  # Changed to optional to allow None
    impacted_population: str
    is_recurring: bool
    document_paths: List[str] = []

class VectorCheckResult(BaseModel):
    is_duplicate: bool
    parent_form_id: Optional[str] = None
    similarity_score: Optional[float] = None

class PriorityScore(BaseModel):
    score: int
    reasoning: str
    urgency_level: str

class RoutingResult(BaseModel):
    department: str
    officer_id: str
    officer_name: str
    estimated_response_time: str

class AnalysisResult(BaseModel):
    form_id: str
    vector_check: VectorCheckResult
    priority_score: PriorityScore
    routing: RoutingResult
    status: str
    analyzed_at: datetime
    document_insights: Optional[str] = None  # Added for extracted document content
