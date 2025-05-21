#!/usr/bin/env python
"""
Test script for the MCP service.

This script allows testing the MCP service from the command line.
It creates a conversation and interacts with the model.
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import httpx


async def create_conversation(
    base_url: str, initial_message: Optional[str] = None
) -> Dict:
    """Create a new conversation.
    
    Args:
        base_url: Base URL of the MCP service
        initial_message: Optional initial message
        
    Returns:
        Conversation data
    """
    url = f"{base_url}/assistant/conversations"
    
    data = {}
    if initial_message:
        data["message"] = initial_message
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        response.raise_for_status()
        
        return response.json()


async def add_message(
    base_url: str, conversation_id: str, message: str
) -> Dict:
    """Add a message to a conversation.
    
    Args:
        base_url: Base URL of the MCP service
        conversation_id: Conversation ID
        message: Message content
        
    Returns:
        Response data
    """
    url = f"{base_url}/assistant/conversations/{conversation_id}/messages"
    
    data = {"message": message}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        response.raise_for_status()
        
        return response.json()


async def get_conversation(base_url: str, conversation_id: str) -> Dict:
    """Get a conversation.
    
    Args:
        base_url: Base URL of the MCP service
        conversation_id: Conversation ID
        
    Returns:
        Conversation data
    """
    url = f"{base_url}/assistant/conversations/{conversation_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        
        return response.json()


async def interactive_session(base_url: str):
    """Start an interactive session with the MCP service.
    
    Args:
        base_url: Base URL of the MCP service
    """
    print("MCP Service Interactive Session")
    print("-" * 40)
    print("Type 'exit' to quit")
    print("-" * 40)
    
    # Create a new conversation
    initial_message = input("You: ")
    
    if initial_message.lower() == "exit":
        return
    
    print("Creating conversation...")
    conversation = await create_conversation(base_url, initial_message)
    
    conversation_id = conversation["conversation_id"]
    print(f"Conversation ID: {conversation_id}")
    
    if "message" in conversation:
        print(f"Assistant: {conversation['message']}")
    
    # Interactive loop
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == "exit":
            break
        
        print("Sending message...")
        response = await add_message(base_url, conversation_id, user_input)
        
        print(f"Assistant: {response['message']}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Service Test Client")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000", 
        help="Base URL of the MCP service"
    )
    
    args = parser.parse_args()
    
    try:
        await interactive_session(args.url)
    except httpx.RequestError as e:
        print(f"Error connecting to the MCP service: {e}")
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
