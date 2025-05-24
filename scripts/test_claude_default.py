#!/usr/bin/env python3
"""
Test script to verify that Claude Sonnet 4 is the default provider
for all clients in the MCP Host service.
"""

import argparse
import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any

import aiohttp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_HOST = "http://localhost:8000"
API_ENDPOINTS = {
    "health": "/health",
    "models": "/api/models",
    "conversations": "/api/conversations",
    "messages": lambda conv_id: f"/api/conversations/{conv_id}/messages",
}

# Default credentials
DEFAULT_USERNAME = "admin@example.com"
DEFAULT_PASSWORD = "password"


async def get_token(host: str, username: str, password: str) -> str:
    """Get the authorization token."""
    url = f"{host}/api/token"
    
    async with aiohttp.ClientSession() as session:
        data = {
            "username": username,
            "password": password,
        }
        async with session.post(url, data=data) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"Failed to get token: {text}")
            
            result = await response.json()
            return result["access_token"]


async def check_health(host: str) -> bool:
    """Check if the service is healthy."""
    url = f"{host}{API_ENDPOINTS['health']}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return False
            
            result = await response.json()
            return result.get("status") == "ok"


async def get_available_models(host: str, token: str) -> Dict[str, Any]:
    """Get available models."""
    url = f"{host}{API_ENDPOINTS['models']}"
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"Failed to get models: {text}")
            
            return await response.json()


async def create_conversation(
    host: str, token: str, message: Optional[str] = None, provider_name: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new conversation."""
    url = f"{host}{API_ENDPOINTS['conversations']}"
    
    data = {}
    if message:
        data["message"] = message
    if provider_name:
        data["provider_name"] = provider_name
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        async with session.post(url, json=data, headers=headers) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"Failed to create conversation: {text}")
            
            return await response.json()


async def add_message(
    host: str, token: str, conversation_id: str, message: str, provider_name: Optional[str] = None
) -> Dict[str, Any]:
    """Add a message to a conversation."""
    url = f"{host}{API_ENDPOINTS['messages'](conversation_id)}"
    
    data = {"message": message}
    if provider_name:
        data["provider_name"] = provider_name
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        async with session.post(url, json=data, headers=headers) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"Failed to add message: {text}")
            
            return await response.json()


async def test_default_provider(host: str, username: str, password: str) -> None:
    """Test that Claude Sonnet 4 is the default provider."""
    logger.info("Getting token...")
    token = await get_token(host, username, password)
    
    logger.info("Checking health...")
    health = await check_health(host)
    logger.info(f"Health check: {'OK' if health else 'FAILED'}")
    
    if not health:
        logger.error("Service is not healthy, exiting.")
        return
    
    logger.info("Getting available models...")
    models = await get_available_models(host, token)
    logger.info(f"Available models: {json.dumps(models, indent=2)}")
    
    # Check default provider
    default_provider = models.get("default_provider")
    logger.info(f"Default provider: {default_provider}")
    
    # Find provider info for the default provider
    default_provider_info = None
    for provider in models.get("providers", []):
        if provider.get("name") == default_provider:
            default_provider_info = provider
            break
    
    if default_provider_info:
        logger.info(f"Default provider info: {json.dumps(default_provider_info, indent=2)}")
        
        # Check if it's Anthropic Claude Sonnet 4
        is_claude_sonnet = (
            default_provider_info.get("provider_type") == "anthropic" and
            "claude-sonnet" in default_provider_info.get("model_id", "").lower()
        )
        
        if is_claude_sonnet:
            logger.info("✅ SUCCESS: Default provider is Claude Sonnet 4!")
        else:
            logger.warning("❌ WARNING: Default provider is not Claude Sonnet 4!")
    else:
        logger.warning(f"Could not find info for default provider: {default_provider}")
    
    # Test conversation without specifying provider
    logger.info("Creating conversation without specifying provider...")
    conversation = await create_conversation(
        host, token, message="What provider are you using?"
    )
    
    logger.info(f"Conversation created with ID: {conversation.get('conversation_id')}")
    logger.info(f"Response: {conversation.get('message')}")
    logger.info(f"Provider used: {conversation.get('provider_used')}")
    
    # Check if the provider used is anthropic
    if conversation.get("provider_used") == "anthropic":
        logger.info("✅ SUCCESS: Conversation used Anthropic provider by default!")
    else:
        logger.warning(f"❌ WARNING: Conversation used {conversation.get('provider_used')} instead of Anthropic!")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test MCP Host provider selection")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host URL")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help="Username")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password")
    
    args = parser.parse_args()
    
    logger.info(f"Testing MCP Host at {args.host}")
    
    try:
        await test_default_provider(args.host, args.username, args.password)
    except Exception as e:
        logger.exception(f"Error during test: {e}")


if __name__ == "__main__":
    asyncio.run(main())
