"""Model integration for various model providers."""

import logging
import os
from typing import Any, Dict, List, Optional

from app.config.config import ModelConfig, ModelProviderType
from app.model.provider import ModelProvider, get_provider

logger = logging.getLogger(__name__)


class ModelService:
    """Service for interacting with model providers."""

    def __init__(self, config: ModelConfig, model_wrapper: Optional['ModelWrapper'] = None):
        """Initialize the model service.
        
        Args:
            config: Default model configuration
            model_wrapper: Optional model wrapper for multiple providers
        """
        self.config = config
        self.provider: Optional[ModelProvider] = None
        self.model_wrapper = model_wrapper
        self.using_wrapper = model_wrapper is not None
        
        # Override API keys from environment if available
        if not self.config.api_key:
            if self.config.provider == ModelProviderType.OPENAI and os.environ.get("OPENAI_API_KEY"):
                self.config.api_key = os.environ.get("OPENAI_API_KEY")
            elif self.config.provider == ModelProviderType.ANTHROPIC and os.environ.get("ANTHROPIC_API_KEY"):
                self.config.api_key = os.environ.get("ANTHROPIC_API_KEY")
                
        # If using wrapper, apply environment variables to all providers in the wrapper
        if self.using_wrapper and self.model_wrapper:
            for name, provider_config in self.model_wrapper.providers_config.items():
                if not provider_config.api_key:
                    if provider_config.provider == ModelProviderType.OPENAI and os.environ.get("OPENAI_API_KEY"):
                        provider_config.api_key = os.environ.get("OPENAI_API_KEY")
                    elif provider_config.provider == ModelProviderType.ANTHROPIC and os.environ.get("ANTHROPIC_API_KEY"):
                        provider_config.api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if self.using_wrapper:
            logger.info(f"Initialized model service with wrapper (default: {config.provider}:{config.model_id})")
        else:
            logger.info(f"Initialized model service for {config.provider}:{config.model_id}")
    
    async def initialize(self) -> None:
        """Initialize the model provider(s)."""
        if self.using_wrapper:
            logger.info("Initializing model wrapper with multiple providers")
            await self.model_wrapper.initialize()
            logger.info("Model wrapper initialized successfully")
        else:
            logger.info(f"Initializing {self.config.provider} provider for model {self.config.model_id}")
            # Use the factory function to get the appropriate provider
            self.provider = get_provider(self.config)
            await self.provider.initialize()
            logger.info(f"Provider initialized for {self.config.model_id}")
    
    async def generate_response(
        self, messages: List[Dict[str, Any]], provider_name: Optional[str] = None
    ) -> str:
        """Generate a response based on conversation history.
        
        Args:
            messages: List of message dictionaries with role and content
            provider_name: Optional provider name to use (only for wrapper mode)
            
        Returns:
            Generated response text
        """
        if self.using_wrapper:
            # Use the model wrapper
            if not provider_name:
                logger.info("Using default provider from wrapper")
            else:
                logger.info(f"Using specified provider: {provider_name}")
            return await self.model_wrapper.generate_response(messages, provider_name)
        else:
            # Use the single provider
            if not self.provider:
                await self.initialize()
            
            # Delegate to the provider for response generation
            return await self.provider.generate_response(messages)
