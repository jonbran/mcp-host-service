"""User store for the MCP service."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.auth.models import User, UserInDB

logger = logging.getLogger(__name__)

# In a production application, this would be a proper database
# For demonstration, we'll use a simple file-based store
USER_DB_PATH = Path("data/users.json")


def _ensure_user_dir_exists():
    """Ensure the user data directory exists."""
    os.makedirs(USER_DB_PATH.parent, exist_ok=True)


def _load_users() -> Dict[str, Dict]:
    """Load users from the user store."""
    _ensure_user_dir_exists()
    
    if not USER_DB_PATH.exists():
        return {}
    
    try:
        with open(USER_DB_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        return {}


def _save_users(users: Dict[str, Dict]):
    """Save users to the user store."""
    _ensure_user_dir_exists()
    
    try:
        with open(USER_DB_PATH, "w") as f:
            json.dump(users, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving users: {str(e)}")


def get_user(username: str) -> Optional[UserInDB]:
    """Get a user by username."""
    users = _load_users()
    user_dict = users.get(username)
    
    if not user_dict:
        return None
    
    # Convert ISO format string back to datetime if needed
    if isinstance(user_dict.get("created_at"), str):
        user_dict["created_at"] = datetime.fromisoformat(user_dict["created_at"])
    
    return UserInDB(**user_dict)


def get_users(skip: int = 0, limit: int = 100) -> List[User]:
    """Get a list of users with pagination."""
    users = _load_users()
    
    # Convert to User objects (without password)
    user_list = []
    for username, user_dict in list(users.items())[skip:skip + limit]:
        # Convert ISO format string back to datetime if needed
        if isinstance(user_dict.get("created_at"), str):
            user_dict["created_at"] = datetime.fromisoformat(user_dict["created_at"])
        
        # Create User object (without hashed_password)
        user_data = {k: v for k, v in user_dict.items() if k != "hashed_password"}
        user_list.append(User(**user_data))
    
    return user_list


def create_user(user: UserInDB) -> UserInDB:
    """Create a new user."""
    users = _load_users()
    
    # Check if username already exists
    if user.username in users:
        raise ValueError(f"Username {user.username} already exists")
    
    # Add the new user
    users[user.username] = user.model_dump()
    _save_users(users)
    
    return user


def delete_user(username: str) -> bool:
    """Delete a user by username."""
    users = _load_users()
    
    if username not in users:
        return False
    
    del users[username]
    _save_users(users)
    
    return True


def update_user(username: str, user_data: Dict) -> Optional[UserInDB]:
    """Update a user's data."""
    users = _load_users()
    
    if username not in users:
        return None
    
    # Update the user data
    users[username].update(user_data)
    _save_users(users)
    
    return UserInDB(**users[username])
