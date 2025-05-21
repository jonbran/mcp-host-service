#!/usr/bin/env python
"""Test script for the MCP host."""

import argparse
import json
import sys
import time
from urllib.parse import urljoin

import httpx

def login(base_url, username="admin", password="adminpassword"):
    """Login to get access token."""
    print(f"Authenticating as {username}...")
    try:
        response = httpx.post(
            f"{base_url}/api/auth/token",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10.0
        )
        response.raise_for_status()
        token_data = response.json()
        return token_data["access_token"]
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

def main(args):
    """Main entry point for the test script."""
    base_url = f"http://{args.host}:{args.port}"
    
    # Wait a moment for server to fully initialize
    print(f"Waiting for server to initialize at {base_url}...")
    time.sleep(2)
    
    # Test the health endpoint
    print(f"Testing health endpoint at {base_url}/health...")
    try:
        response = httpx.get(f"{base_url}/health", timeout=10.0)
        response.raise_for_status()
        print(f"✅ Health endpoint response: {response.json()}")
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return 1
    
    # Test the API health endpoint
    print(f"Testing API health endpoint at {base_url}/api/health...")
    try:
        response = httpx.get(f"{base_url}/api/health", timeout=10.0)
        response.raise_for_status()
        print(f"✅ API health endpoint response: {response.json()}")
    except Exception as e:
        print(f"❌ Error testing API health endpoint: {e}")
        return 1
    
    if not args.create_conversation:
        print("Skipping conversation creation test.")
        print("✅ All health checks passed!")
        return 0
    
    # Login to get access token for protected endpoints
    token = login(base_url)
    if not token:
        return 1
        
    # Test creating a conversation
    print(f"Testing conversation creation at {base_url}/api/conversations...")
    try:
        response = httpx.post(
            f"{base_url}/api/conversations",
            json={"message": "Hello, how are you?"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0
        )
        response.raise_for_status()
        print(f"✅ Conversation created successfully: {response.json()}")
    except Exception as e:
        print(f"❌ Error creating conversation: {e}")
        return 1
    
    print("✅ All tests passed!")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the MCP host")
    parser.add_argument("--host", default="localhost", help="Host address")
    parser.add_argument("--port", default=8000, type=int, help="Port number")
    parser.add_argument("--create-conversation", action="store_true", 
                        help="Test conversation creation (requires auth)")
    
    args = parser.parse_args()
    sys.exit(main(args))
