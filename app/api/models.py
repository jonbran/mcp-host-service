"""API models for MCP service."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ConversationCreateRequest(BaseModel):
    """Request model for creating a new conversation."""
    
    message: Optional[str] = None
    provider_name: Optional[str] = None


class ConversationCreateResponse(BaseModel):
    """Response model for creating a new conversation."""
    
    conversation_id: str
    message: Optional[str] = None
    provider_used: Optional[str] = None


class ConversationMessageRequest(BaseModel):
    """Request model for adding a message to a conversation."""
    
    message: str
    provider_name: Optional[str] = None


class ConversationMessageResponse(BaseModel):
    """Response model for adding a message to a conversation."""
    
    conversation_id: str
    message: str
    provider_used: Optional[str] = None


class MessageModel(BaseModel):
    """Model for a message in a conversation."""
    
    role: str
    content: str
    timestamp: str


class ConversationResponse(BaseModel):
    """Response model for getting a conversation."""
    
    id: str
    messages: List[MessageModel]
    created_at: str
    updated_at: str


class ConversationSummary(BaseModel):
    """Summary model for a conversation."""
    
    id: str
    created_at: str
    updated_at: str
    message_count: int


class ConversationListResponse(BaseModel):
    """Response model for listing conversations."""
    
    conversations: List[ConversationSummary]


class ConversationDeleteResponse(BaseModel):
    """Response model for deleting a conversation."""
    
    success: bool
    message: str
