#!/usr/bin/env python3
"""
Test script for MCP Service functionality.
"""

import asyncio
import json
import sys
from datetime import datetime

# Set the base URL for the API
BASE_URL = "http://localhost:8000/api"

async def test_mcp_service():
    """Test the MCP service functionality."""
    print("=" * 50)
    print("Testing MCP Service...")
    print("=" * 50)
    
    try:
        # Import httpx inside the function to catch any import errors
        import httpx
        
        # 1. Check health endpoint
        async with httpx.AsyncClient() as client:
            print("\n1. Testing health endpoint...")
            print("-" * 30)
            response = await client.get(f"{BASE_URL}/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code != 200:
                print("❌ Health check failed!")
                return False
            
            print("✅ Health check passed!")
            
            # 1.5 Authenticate to get a token
            print("\n1.5. Authenticating...")
            print("-" * 30)
            response = await client.post(
                f"{BASE_URL}/auth/token",
                data={"username": "admin", "password": "adminpassword"},
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
            
            # Continue with other tests...
            # 2. Create a new conversation
            print("\n2. Creating new conversation...")
            print("-" * 30)
            response = await client.post(
                f"{BASE_URL}/conversations",
                json={"message": "Please search for information about artificial intelligence."},
                headers=auth_header
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code != 200:
                print("❌ Conversation creation failed!")
                return False
            
            conversation_id = response.json()["conversation_id"]
            print(f"✅ Conversation created with ID: {conversation_id}")
            
            # 3. Get the conversation
            print(f"\n3. Getting conversation {conversation_id}...")
            print("-" * 30)
            response = await client.get(f"{BASE_URL}/conversations/{conversation_id}")
            print(f"Status: {response.status_code}")
            print(f"Response (truncated): {response.json()['id']}")
            
            if response.status_code != 200:
                print("❌ Conversation retrieval failed!")
                return False
            
            print("✅ Conversation retrieved successfully!")
            
            # 4. Add a message to the conversation
            print(f"\n4. Adding message to conversation {conversation_id}...")
            print("-" * 30)
            response = await client.post(
                f"{BASE_URL}/conversations/{conversation_id}/messages",
                json={"message": "What can you tell me about machine learning?"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()['conversation_id']}")
            
            if response.status_code != 200:
                print("❌ Message addition failed!")
                return False
            
            print("✅ Message added successfully!")
            
            # 5. List all conversations
            print("\n5. Listing all conversations...")
            print("-" * 30)
            response = await client.get(f"{BASE_URL}/conversations")
            print(f"Status: {response.status_code}")
            print(f"Response: {len(response.json()['conversations'])} conversations found")
            
            if response.status_code != 200:
                print("❌ Conversation listing failed!")
                return False
            
            print("✅ Conversations listed successfully!")
            
            # 6. Delete the conversation
            print(f"\n6. Deleting conversation {conversation_id}...")
            print("-" * 30)
            response = await client.delete(f"{BASE_URL}/conversations/{conversation_id}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code != 200:
                print("❌ Conversation deletion failed!")
                return False
            
            print("✅ Conversation deleted successfully!")
            
            print("\n" + "=" * 50)
            print("All tests completed successfully! ✅")
            print("=" * 50)
            return True
            
    except Exception as e:
        print(f"Error during test: {e}")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_mcp_service())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"Error during test: {e}")
        sys.exit(1)
