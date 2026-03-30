from fastapi import APIRouter, HTTPException, Depends
from ..services.user_service import UserService
from ..models.user import UserCreate, UserResponse, UserLogin, Token
from shared.utils.auth_middleware import get_current_user

router = APIRouter()
user_service = UserService()

@router.post("/signup", response_model=str)
async def signup_endpoint(user: UserCreate):
    try:
        return await user_service.signup(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Token)
async def login_endpoint(user: UserLogin):
    try:
        print("Login endpoint called")
        user1 = await user_service.login(user)
        print("Login successful")
        return user1
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(current_user: str = Depends(get_current_user)):
    user = await user_service.get_user(current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
