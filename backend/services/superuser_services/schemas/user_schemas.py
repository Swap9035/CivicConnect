from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from services.superuser_services.models.staff_user import UserRole, Department, StaffMetadata, AccountStatus

class CreateUserRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    employee_id: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    phone_number: str = Field(..., pattern=r'^\+?1?\d{9,15}$')
    role: UserRole
    dept: Department
    ward: str = Field(..., min_length=2, max_length=50)
    designation: str = Field(..., min_length=2, max_length=100)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

class UpdateJurisdictionRequest(BaseModel):
    staff_id: str
    new_ward: str
    new_dept: Optional[Department] = None

class UserResponse(BaseModel):
    staff_id: str
    full_name: str
    employee_id: str
    email: str
    phone_number: str
    role: UserRole
    metadata: StaffMetadata
    account_status: AccountStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    is_first_login: bool

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total_count: int
    page: int
    page_size: int
