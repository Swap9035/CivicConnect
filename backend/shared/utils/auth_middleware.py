from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth_utils import verify_token
from services.user_service.src.db.connection import get_users_collection

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    mobile = verify_token(token)
    if mobile is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    users_col = get_users_collection()
    user = await users_col.find_one({"mobile_number": mobile})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return str(user["_id"])
