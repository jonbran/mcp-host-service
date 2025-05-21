"""Authentication utilities for the MCP service."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.auth.models import TokenData, User, UserInDB
from app.auth.store import get_user

logger = logging.getLogger(__name__)

# Security configuration - these should be in environment variables in production
SECRET_KEY = "1ce3e53c59fe49a5a1e3349a72734e36c3fd9c0e5a1c41d99fd2fa8cb60d2d5a"  # This is just a demo key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security utils
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> Union[UserInDB, bool]:
    """Authenticate a user with username and password."""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(
    data: Dict[str, Union[str, List[str]]], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current user from a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
        roles = payload.get("roles", [])
        token_data = TokenData(username=username, roles=roles)
    
    except JWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise credentials_exception
    
    user = get_user(token_data.username)
    
    if user is None:
        raise credentials_exception
    
    return User(**user.dict())


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Check if the current user is active (not disabled)."""
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Inactive user"
        )
    return current_user


def check_role(required_roles: List[str]):
    """Generate a dependency to check if the user has required roles."""
    
    async def has_role(current_user: User = Depends(get_current_active_user)) -> User:
        """Check if the user has any of the required roles."""
        # Admin role is always sufficient
        if "admin" in current_user.roles:
            return current_user
        
        # Check if user has any of the required roles
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        
        return current_user
    
    return has_role
