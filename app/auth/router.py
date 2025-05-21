"""Authentication router for the MCP service."""

import logging
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.models import Token, User, UserCreate, UserInDB
from app.auth.store import create_user, get_user, get_users
from app.auth.utils import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    check_role,
    create_access_token,
    get_current_active_user,
    get_password_hash,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint that returns a JWT token."""
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    # Create access token with user information
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": user.roles},
        expires_delta=access_token_expires,
    )
    
    return Token(
        access_token=access_token, 
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/users", response_model=User)
async def register_user(user: UserCreate, current_user: User = Depends(check_role(["admin"]))):
    """Create a new user. Requires admin role."""
    # Check if user already exists
    if get_user(user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with username {user.username} already exists",
        )
    
    # Create the user with hashed password
    user_in_db = UserInDB(
        **user.model_dump(exclude={"password"}),
        hashed_password=get_password_hash(user.password),
    )
    
    created_user = create_user(user_in_db)
    
    # Return user without hashed_password
    return User(**created_user.model_dump(exclude={"hashed_password"}))


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get the current user's information."""
    return current_user


@router.get("/users", response_model=List[User])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(check_role(["admin"])),
):
    """List all users. Requires admin role."""
    users = get_users(skip=skip, limit=limit)
    return users
