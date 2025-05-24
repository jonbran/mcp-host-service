"""Environment variable utilities."""

import logging
import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_env(env_file: Optional[str] = None) -> Dict[str, str]:
    """Load environment variables from .env file.
    
    Args:
        env_file: Path to the .env file
        
    Returns:
        Dictionary of environment variables
    """
    # Try to find .env file if not specified
    if not env_file:
        locations = [
            ".env",
            "../.env",
            "../../.env",
        ]
        
        for location in locations:
            if Path(location).exists():
                env_file = location
                break
    
    # Load environment variables
    if env_file and Path(env_file).exists():
        logger.info(f"Loading environment variables from {env_file}")
        load_dotenv(env_file)
    else:
        logger.warning("No .env file found, using default environment variables")
    
    # Return a dictionary of relevant environment variables
    return {
        "MODEL_ID": os.environ.get("MODEL_ID", "deepseek-ai/DeepSeek-R1"),
        "USE_GPU": os.environ.get("USE_GPU", "0"),
        "API_HOST": os.environ.get("API_HOST", "0.0.0.0"),
        "API_PORT": os.environ.get("API_PORT", "8000"),
        "DATA_DIR": os.environ.get("DATA_DIR", "./data"),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
    }
