"""API router for MCP service."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.models import (
    ConversationCreateRequest,
    ConversationCreateResponse,
    ConversationDeleteResponse,
    ConversationListResponse,
    ConversationMessageRequest,
    ConversationMessageResponse,
    ConversationResponse,
)
from app.auth.models import User
from app.auth.utils import get_current_active_user
from app.config.config import load_config
from app.host.host import MCPHost
from app.model.model import ModelService
from app.persistence.conversation import ConversationStore

logger = logging.getLogger(__name__)

# Load configuration
config = load_config(Path("config/config.json"))

# Initialize services
model_service = ModelService(config.model)
conversation_store = ConversationStore(Path(config.data_dir))
mcp_host = MCPHost(config, model_service)

@asynccontextmanager
async def router_lifespan(app):
    """Lifespan for router dependencies."""
    # Initialize services on startup
    await model_service.initialize()
    await mcp_host.initialize()
    
    yield
    
    # Clean up on shutdown
    await mcp_host.close()

# Create router with lifespan
router = APIRouter(lifespan=router_lifespan)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.post(
    "/conversations",
    response_model=ConversationCreateResponse,
    summary="Create a new conversation",
    description="Create a new conversation with an optional initial message",
)
async def create_conversation(
    request: ConversationCreateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Create a new conversation."""
    # Create the conversation
    conversation = conversation_store.create_conversation()
    
    # If there's an initial message, process it
    response_text = None
    if request.message:
        # Add the user message
        conversation = conversation_store.add_message(
            conversation.id, "user", request.message
        )
        
        # Process with MCP host
        response_text, updated_history = await mcp_host.process_message(
            request.message
        )
        
        # Add the assistant response
        conversation = conversation_store.add_message(
            conversation.id, "assistant", response_text
        )
    
    return ConversationCreateResponse(
        conversation_id=conversation.id,
        message=response_text,
    )


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List conversations",
    description="List all conversations with pagination",
)
def list_conversations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
):
    """List all conversations."""
    conversations = conversation_store.list_conversations(limit, offset)
    return ConversationListResponse(conversations=conversations)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation",
    description="Get a conversation by ID",
)
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get a conversation by ID."""
    conversation = conversation_store.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation not found: {conversation_id}",
        )
    
    return ConversationResponse(
        id=conversation.id,
        messages=[
            {
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp,
            }
            for message in conversation.messages
        ],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationMessageResponse,
    summary="Add message to conversation",
    description="Add a message to an existing conversation",
)
async def add_message(
    conversation_id: str, 
    request: ConversationMessageRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Add a message to a conversation."""
    # Check if conversation exists
    conversation = conversation_store.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation not found: {conversation_id}",
        )
    
    # Add the user message
    conversation = conversation_store.add_message(
        conversation_id, "user", request.message
    )
    
    # Process with MCP host
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in conversation.messages
    ]
    
    response_text, updated_history = await mcp_host.process_message(
        request.message, history
    )
    
    # Add the assistant response
    conversation = conversation_store.add_message(
        conversation_id, "assistant", response_text
    )
    
    return ConversationMessageResponse(
        conversation_id=conversation_id,
        message=response_text,
    )


@router.delete(
    "/conversations/{conversation_id}",
    response_model=ConversationDeleteResponse,
    summary="Delete conversation",
    description="Delete a conversation by ID",
)
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Delete a conversation."""
    success = conversation_store.delete_conversation(conversation_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation not found: {conversation_id}",
        )
    
    return ConversationDeleteResponse(
        success=True,
        message=f"Conversation {conversation_id} deleted successfully",
    )
