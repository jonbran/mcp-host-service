#!/usr/bin/env python
"""Test script for model provider integrations."""

import asyncio
import json
import os
import sys
from typing import Dict, List, Any

# Add parent directory to path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.config import ModelConfig, ModelProviderType
from app.model.provider import get_provider


async def test_provider(config: ModelConfig, messages: List[Dict[str, Any]]) -> None:
    """Test a model provider with sample messages.
    
    Args:
        config: Model configuration
        messages: List of message dictionaries
    """
    print(f"\n--- Testing {config.provider}:{config.model_id} ---")
    
    try:
        # Get the provider
        provider = get_provider(config)
        
        # Initialize the provider
        print("Initializing provider...")
        await provider.initialize()
        
        # Generate a response
        print("Generating response...")
        response = await provider.generate_response(messages)
        
        print("\nResponse:")
        print(f"{response}")
        
        print("\nTest completed successfully.")
        
    except Exception as e:
        print(f"\nError testing provider: {str(e)}")


async def main():
    """Run tests for different providers."""
    # Sample conversation
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "What's the capital of France?"}
    ]
    
    # Test providers based on environment variables
    # HuggingFace (always test)
    huggingface_config = ModelConfig(
        provider=ModelProviderType.HUGGINGFACE,
        model_id="gpt2",  # Small model for quick testing
        device="cpu",
        optimize=False
    )
    await test_provider(huggingface_config, messages)
    
    # OpenAI (test if API key is available)
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        openai_config = ModelConfig(
            provider=ModelProviderType.OPENAI,
            model_id="gpt-3.5-turbo",
            api_key=openai_api_key
        )
        await test_provider(openai_config, messages)
    else:
        print("\n--- Skipping OpenAI test (no API key) ---")
    
    # Anthropic (test if API key is available)
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        anthropic_config = ModelConfig(
            provider=ModelProviderType.ANTHROPIC,
            model_id="claude-3-haiku-20240307",
            api_key=anthropic_api_key
        )
        await test_provider(anthropic_config, messages)
    else:
        print("\n--- Skipping Anthropic test (no API key) ---")


if __name__ == "__main__":
    asyncio.run(main())
