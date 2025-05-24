#!/usr/bin/env python3
"""
Test script for MCP Service API with provider-based architecture.
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional
import pytest

# Set the base URL for the API
BASE_URL = "http://localhost:8001/api"

# Auth credentials
AUTH = {
    "username": "admin",
    "password": "adminpassword"
}


@pytest.mark.asyncio
async def test_provider_api():
    """Test the provider-based architecture API for the MCP service."""
    print("=" * 50)
    print("Testing MCP Service Provider API...")
    print("=" * 50)
    
    try:
        # Import httpx inside the function to catch any import errors
        import httpx
        
        async with httpx.AsyncClient() as client:
            # 1. Authenticate to get a token
            print("\n1. Authenticating...")
            print("-" * 30)
            response = await client.post(
                f"{BASE_URL}/auth/token",
                data=AUTH,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Authentication failed! {response.text}")
                return False
            
            token_data = response.json()
            token = token_data.get("access_token")
            token_type = token_data.get("token_type", "bearer")
            
            print(f"✅ Authentication successful! Got token.")
            
            # Add authorization header for subsequent requests
            auth_header = {"Authorization": f"{token_type} {token}"}
            
            # 2. List available model providers
            print("\n2. Listing available model providers...")
            print("-" * 30)
            response = await client.get(
                f"{BASE_URL}/models",
                headers=auth_header
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Failed to list model providers! {response.text}")
                return False
            
            models_data = response.json()
            print(f"Default provider: {models_data.get('default_provider')}")
            print("Available providers:")
            for provider in models_data.get("providers", []):
                print(f"  - {provider.get('name')}: {provider.get('model_id')} ({provider.get('provider_type')})")
            
            print("✅ Successfully listed model providers!")
            
            providers = [p.get("name") for p in models_data.get("providers", [])]
            if not providers:
                print("⚠️ No providers available, stopping tests.")
                return False
            
            # 3. Create conversations with different providers
            print("\n3. Creating conversations with different providers...")
            print("-" * 30)
            
            for provider in providers:
                print(f"\nTesting provider: {provider}")
                response = await client.post(
                    f"{BASE_URL}/conversations",
                    json={
                        "message": f"Hello, I am testing the {provider} provider. What model are you?",
                        "provider_name": provider
                    },
                    headers=auth_header
                )
                
                if response.status_code != 200:
                    print(f"❌ Failed to create conversation with provider {provider}! {response.text}")
                    continue
                
                result = response.json()
                conversation_id = result.get("conversation_id")
                message = result.get("message")
                provider_used = result.get("provider_used")
                
                print(f"Created conversation: {conversation_id}")
                print(f"Provider used: {provider_used}")
                print(f"Response preview: {message[:100]}..." if message and len(message) > 100 else f"Response: {message}")
                
                print(f"✅ Successfully tested provider {provider}")
            
            print("\n✅ All provider tests completed!")
            return True
            
    except Exception as e:
        print(f"Error during test: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_provider_api())
    sys.exit(0 if result else 1)
