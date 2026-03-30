from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PriorityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class DepartmentCategory(str, Enum):
    SANITATION = "Sanitation"
    WATER_SUPPLY = "Water Supply"
    ELECTRICITY = "Electricity"
    ROADS = "Roads"
    PUBLIC_SAFETY = "Public Safety"
    OTHER = "Other"

class ImpactedPopulation(str, Enum):
    SINGLE_HOUSEHOLD = "Single Household"
    STREET = "Street"
    ENTIRE_COLONY = "Entire Colony"

class GrievanceForm(BaseModel):
    user_id: str  # Reference to user from user service
    # Category 1: Core Identification
    title: Optional[str] = Field(None, description="5-10 word summary")
    category: Optional[DepartmentCategory] = None
    priority: Optional[PriorityLevel] = None
    urgency_reason: Optional[str] = None
    
    # Category 2: Spatial Data
    landmark: Optional[str] = None
    geo_coordinates: Optional[dict] = None  # {"lat": float, "lng": float}
    area_ward_name: Optional[str] = None
    location_hint: Optional[str] = None
    
    # Category 3: Evidence & Description
    full_description: Optional[str] = None
    multimedia_urls: Optional[List[str]] = []  # Keep for future S3 URLs
    document_paths: Optional[List[str]] = []  # Local file paths
    incident_datetime: Optional[datetime] = None
    
    # Category 4: Actionable Metadata
    is_recurring: Optional[bool] = False
    impacted_population: Optional[ImpactedPopulation] = None
    
    # System fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "draft"

class FormSession(BaseModel):
    session_id: str
    user_id: str  # Reference to user from user service
    original_text: str
    extracted_data: dict = {}
    missing_info: List[str] = []
    clarification_questions: List[str] = []
    conversation_history: List[dict] = []
    is_complete: bool = False
    final_form: Optional[str] = None  # form_id
    document_paths: Optional[List[str]] = []  # Local file paths
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AgentResponse(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    urgency_reason: Optional[str] = None
    landmark: Optional[str] = None
    location_hint: Optional[str] = None
    area_ward_name: Optional[str] = None
    full_description: Optional[str] = None
    incident_datetime: Optional[str] = None
    is_recurring: Optional[bool] = None
    impacted_population: Optional[str] = None
    missing_info: List[str] = []
    clarification_questions: List[str] = []
