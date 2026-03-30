from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    DEPT_ADMIN = "DEPT_ADMIN"
    NODAL_OFFICER = "NODAL_OFFICER"

class Department(str, Enum):
    ELECTRICITY = "Electricity"
    WATER = "Water"
    SANITATION = "Sanitation"
    ROADS = "Roads"
    HEALTH = "Health"
    EDUCATION = "Education"

class StaffMetadata(BaseModel):
    dept: Department
    ward: str
    designation: str

class AccountStatus(BaseModel):
    is_active: bool = True
    is_first_login: bool = True
    created_by: str

class StaffUser(BaseModel):
    staff_id: str = Field(..., alias="_id")
    full_name: str
    employee_id: str
    email: str
    phone_number: str
    password_hash: str
    role: UserRole
    metadata: StaffMetadata
    account_status: AccountStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
