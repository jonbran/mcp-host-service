"""Configuration module for MCP service."""

import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, RootModel, validator

logger = logging.getLogger(__name__)


class TransportType(str, Enum):
    """Transport types for MCP server connections."""
    
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"


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
    auth: Optional[Dict[str, str]] = None  # Authentication details like client_id and api_key
    
    @validator("url")
    def validate_url(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Validate that URL is present for SSE and HTTP transport."""
        if values.get("type") in [TransportType.SSE, TransportType.HTTP] and not v:
            raise ValueError(f"URL is required for {values.get('type')} transport")
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
    config: Optional[Dict[str, Any]] = None


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
    
    @validator("api_key")
    def validate_api_key(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Check for environment variables if api_key contains a placeholder."""
        if v and v.startswith("${") and v.endswith("}"):
            env_var = v[2:-1]  # Remove ${ and }
            env_value = os.environ.get(env_var)
            if env_value:
                return env_value
            else:
                logger.warning(f"Environment variable {env_var} not found for API key")
        return v


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


class ModelsConfig(RootModel):
    """Configuration for multiple model providers."""
    
    root: Dict[str, ModelConfig] = Field(default_factory=dict)
    
    def __getitem__(self, key: str) -> ModelConfig:
        """Get model config by name."""
        return self.root[key]
    
    def __iter__(self):
        """Iterate over model configs."""
        return iter(self.root)
    
    def __len__(self) -> int:
        """Get number of model configs."""
        return len(self.root)
    
    def items(self):
        """Get items from model configs."""
        return self.root.items()
    
    def keys(self):
        """Get keys from model configs."""
        return self.root.keys()


class AppConfig(BaseModel):
    """Application configuration."""
    
    mcp: MCPConfig
    model: ModelConfig  # Default model configuration
    models: Optional[ModelsConfig] = None  # Multiple model configurations
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
