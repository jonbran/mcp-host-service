#!/usr/bin/env python3
"""
Script to test authentication with the Scheduler MCP service.

This script demonstrates how to:
1. Authenticate with the Scheduler service
2. Use the obtained JWT token for subsequent MCP requests
3. Test MCP tool calls with proper authentication
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Any

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SchedulerClient:
    """Client for interacting with the Scheduler MCP service."""
    
    def __init__(self, base_url: str, client_id: str, api_key: str):
        """Initialize the client.
        
        Args:
            base_url: Base URL of the Scheduler service
            client_id: Client ID for authentication
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.api_key = api_key
        self.token = None
        self.token_expires_at = None
    
    async def authenticate(self) -> bool:
        """Authenticate with the Scheduler service.
        
        Returns:
            True if authentication was successful, False otherwise
        """
        auth_url = f"{self.base_url}/api/auth/token"
        payload = {
            "clientId": self.client_id,
            "apiKey": self.api_key
        }
        
        try:
            logger.info(f"Authenticating with {auth_url}")
            async with httpx.AsyncClient() as client:
                response = await client.post(auth_url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    self.token = data["token"]
                    self.token_expires_at = data.get("expiresIn")  # in seconds
                    logger.info(f"Authentication successful, token expires in {self.token_expires_at} seconds")
                    return True
                else:
                    logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                    return False
        
        except Exception as e:
            logger.error(f"Error during authentication: {e}", exc_info=True)
            return False
    
    async def get_mcp_tools(self) -> Optional[Dict[str, Any]]:
        """Get MCP tools from the service.
        
        Returns:
            Dictionary of MCP tools or None if failed
        """
        if not self.token:
            logger.error("Not authenticated, call authenticate() first")
            return None
        
        tools_url = f"{self.base_url}/mcp/tools"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            logger.info(f"Getting MCP tools from {tools_url}")
            async with httpx.AsyncClient() as client:
                response = await client.get(tools_url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return data
                else:
                    logger.error(f"Failed to get tools: {response.status_code} - {response.text}")
                    return None
        
        except Exception as e:
            logger.error(f"Error getting MCP tools: {e}", exc_info=True)
            return None
    
    async def execute_tool(self, tool_id: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute an MCP tool.
        
        Args:
            tool_id: ID of the tool to execute
            parameters: Tool parameters
        
        Returns:
            Tool execution result or None if failed
        """
        if not self.token:
            logger.error("Not authenticated, call authenticate() first")
            return None
        
        execute_url = f"{self.base_url}/mcp/execute"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "toolId": tool_id,
            "toolParameters": parameters
        }
        
        try:
            logger.info(f"Executing tool {tool_id} with parameters {parameters}")
            async with httpx.AsyncClient() as client:
                response = await client.post(execute_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return data
                else:
                    logger.error(f"Tool execution failed: {response.status_code} - {response.text}")
                    return None
        
        except Exception as e:
            logger.error(f"Error executing tool: {e}", exc_info=True)
            return None


async def test_scheduler_auth(
    base_url: str, client_id: str, api_key: str, test_schedule: bool = False
) -> None:
    """Test authentication and tool execution with the Scheduler service.
    
    Args:
        base_url: Base URL of the Scheduler service
        client_id: Client ID for authentication
        api_key: API key for authentication
        test_schedule: Whether to test scheduling a conversation
    """
    # Create and authenticate the client
    client = SchedulerClient(base_url, client_id, api_key)
    if not await client.authenticate():
        logger.error("Authentication failed, exiting")
        return
    
    # Get MCP tools
    tools = await client.get_mcp_tools()
    if not tools:
        logger.error("Failed to get MCP tools, exiting")
        return
    
    logger.info(f"MCP tools: {json.dumps(tools, indent=2)}")
    
    # Test scheduling a conversation if requested
    if test_schedule:
        # Schedule a simple test conversation
        schedule_params = {
            "conversationText": "This is a test scheduled message from the RussellDemo integration",
            "scheduledTime": "2025-05-28T12:00:00Z",  # Tomorrow
            "endpoint": "https://example.com/callback",
            "method": "POST",
            "additionalInfo": "Test from RussellDemo MCP SDK integration"
        }
        
        result = await client.execute_tool("scheduleConversation", schedule_params)
        if result:
            conversation_id = result.get("toolResult")
            logger.info(f"Scheduled conversation with ID: {conversation_id}")
            
            # Check conversation status
            if conversation_id:
                status_result = await client.execute_tool(
                    "getConversationStatus", 
                    {"conversationId": conversation_id}
                )
                
                if status_result:
                    status = status_result.get("toolResult")
                    logger.info(f"Conversation status: {status}")
                else:
                    logger.error("Failed to get conversation status")
        else:
            logger.error("Failed to schedule conversation")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test Scheduler MCP authentication")
    parser.add_argument("--url", type=str, default="http://localhost:5146", help="Base URL of the Scheduler service")
    parser.add_argument("--client-id", type=str, required=True, help="Client ID for authentication")
    parser.add_argument("--api-key", type=str, required=True, help="API key for authentication")
    parser.add_argument("--test-schedule", action="store_true", help="Test scheduling a conversation")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(test_scheduler_auth(args.url, args.client_id, args.api_key, args.test_schedule))
        return 0
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
