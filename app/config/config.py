"""Configuration module for MCP service."""

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class TransportType(str, Enum):
    """Transport types for MCP server connections."""
    
    STDIO = "stdio"
    SSE = "sse"


class ModelProviderType(str, Enum):
    """Model provider types."""
    
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class TransportConfig(BaseModel):
    """Configuration for MCP server transport."""
    
    type: TransportType
    url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None
    
    @validator("url")
    def validate_url(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Validate that URL is present for SSE transport."""
        if values.get("type") == TransportType.SSE and not v:
            raise ValueError("URL is required for SSE transport")
        return v
    
    @validator("command")
    def validate_command(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Validate that command is present for STDIO transport."""
        if values.get("type") == TransportType.STDIO and not v:
            raise ValueError("Command is required for STDIO transport")
        return v


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""
    
    name: str
    transport: TransportConfig
    params: Optional[Dict[str, Any]] = None


class MCPConfig(BaseModel):
    """Configuration for MCP servers."""
    
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list)


class ModelConfig(BaseModel):
    """Configuration for model providers."""
    
    provider: ModelProviderType = ModelProviderType.HUGGINGFACE
    model_id: str = "deepseek-ai/DeepSeek-R1"
    max_sequence_length: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    
    # API credentials for external providers
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    
    # Inference parameters
    batch_size: int = 1
    device: str = "cuda" if os.environ.get("USE_GPU", "0") == "1" else "cpu"
    optimize: bool = True


class APIConfig(BaseModel):
    """Configuration for the REST API."""
    
    host: str = "0.0.0.0"
    port: int = 8000
    timeout: int = 60
    max_request_size: int = 1024 * 1024  # 1MB
    
    # Response settings
    default_format: str = "json"
    
    # Rate limiting (future)
    rate_limit_enabled: bool = False
    rate_limit: int = 100  # requests per minute


class AppConfig(BaseModel):
    """Application configuration."""
    
    mcp: MCPConfig
    model: ModelConfig
    api: APIConfig
    data_dir: str = "./data"
    
    @validator("data_dir")
    def validate_data_dir(cls, v: str) -> str:
        """Ensure data directory exists."""
        data_path = Path(v)
        data_path.mkdir(exist_ok=True, parents=True)
        
        # Also ensure conversations directory exists
        conversations_path = data_path / "conversations"
        conversations_path.mkdir(exist_ok=True, parents=True)
        
        return v


def load_config(config_path: Union[str, Path] = "config/config.json") -> AppConfig:
    """Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Application configuration object
    """
    try:
        with open(config_path, "r") as f:
            config_data = json.load(f)
            return AppConfig(**config_data)
    except FileNotFoundError:
        # Create default config
        mcp_config = MCPConfig()
        model_config = ModelConfig()
        api_config = APIConfig()
        
        app_config = AppConfig(
            mcp=mcp_config,
            model=model_config,
            api=api_config,
        )
        
        # Ensure config directory exists
        Path(config_path).parent.mkdir(exist_ok=True, parents=True)
        
        # Save default config
        with open(config_path, "w") as f:
            f.write(app_config.json(indent=2))
            
        return app_config
