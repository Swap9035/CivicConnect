from fastapi import APIRouter, HTTPException, status, Depends
from services.superuser_services.schemas.user_schemas import LoginRequest, LoginResponse, ChangePasswordRequest, UserResponse
from services.superuser_services.db.repositories.user_repository import user_repository
from services.superuser_services.utils.auth import auth_utils, get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Employee Authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and return JWT token"""
    try:
        # Get user by email
        user = await user_repository.get_user_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if account is active
        if not user.account_status.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Verify password
        if not auth_utils.verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create JWT token
        token_data = {
            "sub": user.staff_id,
            "email": user.email,
            "role": user.role,
            "metadata": user.metadata.model_dump()
        }
        
        access_token = auth_utils.create_access_token(token_data)
        
        logger.info(f"User {user.staff_id} logged in successfully")
        
        return LoginResponse(
            access_token=access_token,
            user=UserResponse(**user.model_dump()),
            is_first_login=user.account_status.is_first_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    """Change user password (first login or regular change)"""
    try:
        # Get current user from database
        user = await user_repository.get_user_by_id(current_user["sub"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not auth_utils.verify_password(password_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_password_hash = auth_utils.hash_password(password_data.new_password)
        
        # Update password and first login status
        update_data = {
            "password_hash": new_password_hash,
            "account_status.is_first_login": False
        }
        
        success = await user_repository.update_user(current_user["sub"], update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update password"
            )
        
        logger.info(f"Password changed for user {current_user['sub']}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    try:
        user = await user_repository.get_user_by_id(current_user["sub"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**user.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (token invalidation would be handled client-side)"""
    try:
        logger.info(f"User {current_user['sub']} logged out")
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )
