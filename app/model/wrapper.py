"""Model wrapper class for unified model provider access."""

import logging
from typing import Any, Dict, List, Optional

from app.config.config import ModelConfig, ModelProviderType
from app.model.provider import ModelProvider, get_provider

logger = logging.getLogger(__name__)


class ModelWrapper:
    """Unified wrapper for all model providers."""

    def __init__(self, providers_config: Dict[str, ModelConfig]):
        """Initialize multiple model providers.
        
        Args:
            providers_config: Dictionary of provider name to configuration
        """
        self.providers_config = providers_config
        self.providers: Dict[str, ModelProvider] = {}
        self.default_provider_name = next(iter(providers_config)) if providers_config else None
        
        logger.info(f"Initialized model wrapper with {len(providers_config)} providers")
        logger.info(f"Default provider: {self.default_provider_name}")
    
    async def initialize(self) -> None:
        """Initialize all model providers."""
        for name, config in self.providers_config.items():
            logger.info(f"Initializing provider {name} ({config.provider}:{config.model_id})")
            provider = get_provider(config)
            await provider.initialize()
            self.providers[name] = provider
        
        logger.info(f"All providers initialized: {', '.join(self.providers.keys())}")
    
    async def generate_response(
        self, 
        messages: List[Dict[str, Any]], 
        provider_name: Optional[str] = None
    ) -> str:
        """Generate a response using the specified provider.
        
        Args:
            messages: List of message dictionaries with role and content
            provider_name: Name of the provider to use (defaults to default provider)
            
        Returns:
            Generated response text
            
        Raises:
            ValueError: If the specified provider is not available
        """
        # Use the specified provider or default
        provider_name = provider_name or self.default_provider_name
        
        if not provider_name or provider_name not in self.providers:
            available = ", ".join(self.providers.keys())
            raise ValueError(f"Provider '{provider_name}' not available. Available providers: {available}")
        
        provider = self.providers[provider_name]
        logger.info(f"Generating response using provider {provider_name}")
        
        return await provider.generate_response(messages)
    
    def get_available_providers(self) -> List[str]:
        """Get a list of available provider names.
        
        Returns:
            List of provider names
        """
        return list(self.providers.keys())
    
    def get_provider_info(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Dictionary of provider information or None if not found
        """
        if provider_name not in self.providers_config:
            return None
        
        config = self.providers_config[provider_name]
        return {
            "name": provider_name,
            "provider_type": config.provider.value,
            "model_id": config.model_id,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "max_sequence_length": config.max_sequence_length,
        }
