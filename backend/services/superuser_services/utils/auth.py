from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.superuser_services.config import settings
import secrets
import string

security = HTTPBearer()

class AuthUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def generate_temp_password(length: int = 12) -> str:
        """Generate a temporary secure password"""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(characters) for _ in range(length))
        return password
    
    @staticmethod
    def create_access_token(data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.jwt_secret_key, 
            algorithm=settings.jwt_algorithm
        )
        return encoded_jwt
    
    @staticmethod
    def decode_access_token(token: str) -> Dict[str, Any]:
        """Decode JWT access token"""
        try:
            payload = jwt.decode(
                token, 
                settings.jwt_secret_key, 
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    try:
        token = credentials.credentials
        payload = AuthUtils.decode_access_token(token)
        
        if payload.get("sub") is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(allowed_roles: list):
    """Decorator to require specific roles"""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

auth_utils = AuthUtils()
