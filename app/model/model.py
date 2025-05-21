"""Model integration for various model providers."""

import logging
import os
from typing import Any, Dict, List, Optional

from app.config.config import ModelConfig, ModelProviderType
from app.model.provider import ModelProvider, get_provider

logger = logging.getLogger(__name__)


class ModelService:
    """Service for interacting with model providers."""

    def __init__(self, config: ModelConfig):
        """Initialize the model service.
        
        Args:
            config: Model configuration
        """
        self.config = config
        self.provider: Optional[ModelProvider] = None
        
        # Override API keys from environment if available
        if not self.config.api_key:
            if self.config.provider == ModelProviderType.OPENAI and os.environ.get("OPENAI_API_KEY"):
                self.config.api_key = os.environ.get("OPENAI_API_KEY")
            elif self.config.provider == ModelProviderType.ANTHROPIC and os.environ.get("ANTHROPIC_API_KEY"):
                self.config.api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        logger.info(f"Initialized model service for {config.provider}:{config.model_id}")
    
    async def initialize(self) -> None:
        """Initialize the model provider."""
        logger.info(f"Initializing {self.config.provider} provider for model {self.config.model_id}")
        
        # Use the factory function to get the appropriate provider
        self.provider = get_provider(self.config)
        await self.provider.initialize()
        
        logger.info(f"Provider initialized for {self.config.model_id}")
    
    async def generate_response(
        self, messages: List[Dict[str, Any]]
    ) -> str:
        """Generate a response based on conversation history.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            Generated response text
        """
        if not self.provider:
            await self.initialize()
        
        # Delegate to the provider for response generation
        return await self.provider.generate_response(messages)
