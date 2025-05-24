"""API models for models information and settings."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ModelProviderInfo(BaseModel):
    """Information about a model provider."""
    
    name: str
    provider_type: str = ""  # Can be empty for MCP servers
    model_id: str = ""  # Can be empty for MCP servers
    max_sequence_length: int = 0  # Can be 0 for MCP servers
    temperature: float = 0.0  # Can be 0 for MCP servers
    top_p: float = 0.0  # Can be 0 for MCP servers
    is_mcp_server: bool = False  # Whether this is an MCP server


class ModelsListResponse(BaseModel):
    """Response model for listing available model providers."""
    
    default_provider: str
    providers: List[ModelProviderInfo]
