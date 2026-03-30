from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from services.superuser_services.schemas.user_schemas import (
    CreateUserRequest, UserResponse, UpdateJurisdictionRequest, 
    UserListResponse
)
from services.superuser_services.models.staff_user import StaffUser, UserRole, Department, StaffMetadata, AccountStatus
from services.superuser_services.db.repositories.user_repository import user_repository
from services.superuser_services.utils.auth import auth_utils, require_role
from services.superuser_services.utils.notifications import notification_service
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/create-user", response_model=UserResponse)
async def create_user(
    user_data: CreateUserRequest,
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.DEPT_ADMIN]))
):
    """Create a new staff user (Admin access only)"""
    try:
        # Check if email already exists
        existing_user = await user_repository.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if employee ID already exists
        if await user_repository.check_employee_id_exists(user_data.employee_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already exists"
            )
        
        # Department Admin can only create users in their department
        if current_user["role"] == UserRole.DEPT_ADMIN:
            admin_dept = current_user.get("metadata", {}).get("dept")
            if user_data.dept != admin_dept:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Department Admin can only create users in their department"
                )
        
        # Generate temporary password
        temp_password = auth_utils.generate_temp_password()
        hashed_password = auth_utils.hash_password(temp_password)
        print("temp_password:", temp_password)
        # Create staff user object
        staff_id = f"STF_{uuid.uuid4().hex[:6].upper()}"
        
        new_user = StaffUser(
            staff_id=staff_id,
            full_name=user_data.full_name,
            employee_id=user_data.employee_id,
            email=user_data.email,
            phone_number=user_data.phone_number,
            password_hash=hashed_password,
            role=user_data.role,
            metadata=StaffMetadata(
                dept=user_data.dept,
                ward=user_data.ward,
                designation=user_data.designation
            ),
            account_status=AccountStatus(
                is_active=True,
                is_first_login=True,
                created_by=current_user["sub"]
            )
        )
        
        # Save to database
        await user_repository.create_user(new_user)
        
        # Send credentials
        notification_result = await notification_service.send_credentials(
            user_data.model_dump(), temp_password
        )
        
        logger.info(f"User {staff_id} created successfully. Notifications: {notification_result}")
        
        return UserResponse(**new_user.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.get("/users", response_model=UserListResponse)
async def get_users(
    dept: Optional[Department] = Query(None),
    ward: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.DEPT_ADMIN]))
):
    """Get list of users with filters"""
    try:
        # Department Admin can only see users in their department
        if current_user["role"] == UserRole.DEPT_ADMIN:
            admin_dept = current_user.get("metadata", {}).get("dept")
            dept = Department(admin_dept) if admin_dept else dept
        
        users, total_count = await user_repository.get_users_by_filters(
            dept=dept, ward=ward, role=role, page=page, page_size=page_size
        )
        
        user_responses = [UserResponse(**user.model_dump()) for user in users]
        
        return UserListResponse(
            users=user_responses,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.put("/update-jurisdiction")
async def update_jurisdiction(
    update_data: UpdateJurisdictionRequest,
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.DEPT_ADMIN]))
):
    """Update user's jurisdiction (ward and optionally department)"""
    try:
        # Get the user to update
        user = await user_repository.get_user_by_id(update_data.staff_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Department Admin can only update users in their department
        if current_user["role"] == UserRole.DEPT_ADMIN:
            admin_dept = current_user.get("metadata", {}).get("dept")
            if user.metadata.dept != admin_dept:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot update user from different department"
                )
        
        # Prepare update data
        update_fields = {
            "metadata.ward": update_data.new_ward
        }
        
        if update_data.new_dept:
            update_fields["metadata.dept"] = update_data.new_dept
        
        # Update user
        success = await user_repository.update_user(update_data.staff_id, update_fields)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user jurisdiction"
            )
        
        return {"message": "Jurisdiction updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating jurisdiction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update jurisdiction"
        )

@router.get("/users/{staff_id}", response_model=UserResponse)
async def get_user_details(
    staff_id: str,
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.DEPT_ADMIN]))
):
    """Get specific user details"""
    try:
        user = await user_repository.get_user_by_id(staff_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Department Admin can only see users in their department
        if current_user["role"] == UserRole.DEPT_ADMIN:
            admin_dept = current_user.get("metadata", {}).get("dept")
            if user.metadata.dept != admin_dept:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot view user from different department"
                )
        
        return UserResponse(**user.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user details"
        )
