"""Initialize an admin user for the MCP service."""

import logging
import os
from typing import Optional

from app.auth.models import UserInDB
from app.auth.store import create_user, get_user
from app.auth.utils import get_password_hash

logger = logging.getLogger(__name__)

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "adminpassword"


def init_admin_user() -> Optional[UserInDB]:
    """Initialize an admin user if one doesn't exist."""
    # Check for existing admin
    admin = get_user(DEFAULT_ADMIN_USERNAME)
    
    if admin:
        logger.info(f"Admin user {DEFAULT_ADMIN_USERNAME} already exists")
        return admin
    
    # Get admin password from environment or use default
    admin_password = os.environ.get("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    
    # Create admin user
    admin_data = UserInDB(
        username=DEFAULT_ADMIN_USERNAME,
        email="admin@example.com",
        full_name="Administrator",
        roles=["admin"],
        hashed_password=get_password_hash(admin_password),
    )
    
    try:
        admin = create_user(admin_data)
        logger.info(f"Created admin user: {admin.username}")
        logger.warning(
            f"Using default admin password, please change it in production or set "
            f"ADMIN_PASSWORD environment variable"
        )
        return admin
    
    except Exception as e:
        logger.error(f"Failed to create admin user: {str(e)}")
        return None
