"""Conversation persistence module."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.utils.cache import timed_lru_cache

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Message model for conversation."""
    
    role: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class Conversation(BaseModel):
    """Conversation model for persistence."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ConversationStore:
    """Store for conversation persistence."""
    
    def __init__(self, data_dir: Path):
        """Initialize the conversation store.
        
        Args:
            data_dir: Data directory for storing conversations
        """
        self.conversations_dir = data_dir / "conversations"
        self.conversations_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"Initialized conversation store at {self.conversations_dir}")
    
    def create_conversation(self, initial_message: Optional[str] = None) -> Conversation:
        """Create a new conversation.
        
        Args:
            initial_message: Optional initial user message
            
        Returns:
            Created conversation
        """
        conversation = Conversation()
        
        if initial_message:
            conversation.messages.append(
                Message(role="user", content=initial_message)
            )
        
        self._save_conversation(conversation)
        
        logger.info(f"Created new conversation: {conversation.id}")
        
        return conversation
    
    @timed_lru_cache(maxsize=100, ttl=60)  # Cache for 1 minute
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation if found, None otherwise
        """
        conversation_path = self.conversations_dir / f"{conversation_id}.json"
        
        if not conversation_path.exists():
            logger.warning(f"Conversation not found: {conversation_id}")
            return None
        
        try:
            with open(conversation_path, "r") as f:
                data = json.load(f)
                return Conversation(**data)
        except Exception as e:
            logger.exception(f"Error loading conversation {conversation_id}: {e}")
            return None
    
    def add_message(
        self, conversation_id: str, role: str, content: str
    ) -> Optional[Conversation]:
        """Add a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            role: Message role (user/assistant/system)
            content: Message content
            
        Returns:
            Updated conversation if successful, None otherwise
        """
        conversation = self.get_conversation(conversation_id)
        
        if not conversation:
            return None
        
        message = Message(role=role, content=content)
        conversation.messages.append(message)
        conversation.updated_at = datetime.now().isoformat()
        
        self._save_conversation(conversation)
        
        # Clear the cache for this conversation
        self.get_conversation.clear_key(conversation_id)
        
        logger.info(f"Added {role} message to conversation {conversation_id}")
        
        return conversation
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if successful, False otherwise
        """
        conversation_path = self.conversations_dir / f"{conversation_id}.json"
        
        if not conversation_path.exists():
            logger.warning(f"Cannot delete: Conversation not found: {conversation_id}")
            return False
        
        try:
            conversation_path.unlink()
            
            # Clear the cache for this conversation
            self.get_conversation.clear_key(conversation_id)
            
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        except Exception as e:
            logger.exception(f"Error deleting conversation {conversation_id}: {e}")
            return False
    
    @timed_lru_cache(maxsize=10, ttl=30)  # Cache for 30 seconds
    def list_conversations(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List conversations with pagination.
        
        Args:
            limit: Maximum number of conversations to return
            offset: Offset for pagination
            
        Returns:
            List of conversation summaries
        """
        conversation_files = list(self.conversations_dir.glob("*.json"))
        # Sort by modification time, newest first
        conversation_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        # Apply pagination
        conversation_files = conversation_files[offset:offset + limit]
        
        conversations = []
        for path in conversation_files:
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    # Create a summary with limited information
                    summary = {
                        "id": data["id"],
                        "created_at": data["created_at"],
                        "updated_at": data["updated_at"],
                        "message_count": len(data["messages"]),
                    }
                    conversations.append(summary)
            except Exception as e:
                logger.exception(f"Error reading conversation file {path}: {e}")
        
        return conversations
    
    def _save_conversation(self, conversation: Conversation) -> None:
        """Save a conversation to disk.
        
        Args:
            conversation: Conversation to save
        """
        conversation_path = self.conversations_dir / f"{conversation.id}.json"
        
        with open(conversation_path, "w") as f:
            f.write(conversation.model_dump_json(indent=2))
