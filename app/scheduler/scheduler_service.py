#!/usr/bin/env python3
"""
Scheduler service wrapper for the RussellDemo project.

This module provides a simple Python wrapper for interacting with the Scheduler MCP service.
It includes functionality to:
1. Schedule conversations for future delivery
2. Check the status of scheduled conversations
3. Cancel scheduled conversations
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.config.config import load_config
from app.host.mcp_client import MCPSdkClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SchedulerService:
    """Wrapper for the Scheduler MCP service."""
    
    def __init__(self, config_path: Path = Path("config/config.json")):
        """Initialize the scheduler service.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = load_config(config_path)
        self.client = None
    
    async def initialize(self) -> bool:
        """Initialize the scheduler service.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Find the Scheduler configuration
            scheduler_config = None
            for server_config in self.config.mcp.mcp_servers:
                if server_config.name == "Scheduler":
                    scheduler_config = server_config
                    break
            
            if not scheduler_config:
                logger.error("Scheduler configuration not found")
                return False
            
            # Initialize the client
            self.client = MCPSdkClient(scheduler_config)
            await self.client.initialize()
            
            logger.info("Scheduler service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing scheduler service: {e}", exc_info=True)
            return False
    
    async def close(self) -> None:
        """Close the scheduler service."""
        if self.client:
            await self.client.close()
            self.client = None
    
    async def schedule_conversation(
        self,
        conversation_text: str,
        scheduled_time: Union[datetime, str],
        endpoint: str,
        method: str = "POST",
        additional_info: Optional[str] = None
    ) -> Optional[str]:
        """Schedule a conversation for future delivery.
        
        Args:
            conversation_text: The text content to be sent
            scheduled_time: When the conversation should be delivered (datetime or ISO 8601 string)
            endpoint: The endpoint where the conversation should be sent
            method: The HTTP method to use (default: "POST")
            additional_info: Additional context information
            
        Returns:
            Conversation ID if successful, None otherwise
        """
        if not self.client:
            logger.error("Client not initialized, call initialize() first")
            return None
        
        # Convert datetime to ISO 8601 string if needed
        if isinstance(scheduled_time, datetime):
            scheduled_time_str = scheduled_time.isoformat()
        else:
            scheduled_time_str = scheduled_time
        
        # Prepare tool parameters
        params = {
            "conversationText": conversation_text,
            "scheduledTime": scheduled_time_str,
            "endpoint": endpoint,
            "method": method
        }
        
        # Add additional info if provided
        if additional_info:
            params["additionalInfo"] = additional_info
        
        try:
            # Call the scheduleConversation tool
            result = await self.client.call_tool("scheduleConversation", params)
            
            # Check if the call was successful
            if "error" in result:
                logger.error(f"Error scheduling conversation: {result['error']}")
                return None
            
            conversation_id = result.get("text")
            logger.info(f"Scheduled conversation with ID: {conversation_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error scheduling conversation: {e}", exc_info=True)
            return None
    
    async def get_conversation_status(self, conversation_id: str) -> Optional[str]:
        """Get the status of a scheduled conversation.
        
        Args:
            conversation_id: The ID of the conversation to check
            
        Returns:
            Status as string ("Scheduled", "InProgress", "Completed", "Failed", "Cancelled")
            or None if the call failed
        """
        if not self.client:
            logger.error("Client not initialized, call initialize() first")
            return None
        
        try:
            # Call the getConversationStatus tool
            result = await self.client.call_tool(
                "getConversationStatus", 
                {"conversationId": conversation_id}
            )
            
            # Check if the call was successful
            if "error" in result:
                logger.error(f"Error getting conversation status: {result['error']}")
                return None
            
            status = result.get("text")
            logger.info(f"Conversation status for {conversation_id}: {status}")
            return status
            
        except Exception as e:
            logger.error(f"Error getting conversation status: {e}", exc_info=True)
            return None
    
    async def cancel_conversation(self, conversation_id: str) -> bool:
        """Cancel a scheduled conversation.
        
        Args:
            conversation_id: The ID of the conversation to cancel
            
        Returns:
            Boolean indicating success or failure
        """
        if not self.client:
            logger.error("Client not initialized, call initialize() first")
            return False
        
        try:
            # Call the cancelConversation tool
            result = await self.client.call_tool(
                "cancelConversation", 
                {"conversationId": conversation_id}
            )
            
            # Check if the call was successful
            if "error" in result:
                logger.error(f"Error cancelling conversation: {result['error']}")
                return False
            
            success = result.get("text", "").lower() == "true"
            if success:
                logger.info(f"Successfully cancelled conversation {conversation_id}")
            else:
                logger.warning(f"Failed to cancel conversation {conversation_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error cancelling conversation: {e}", exc_info=True)
            return False


async def test_scheduler_service():
    """Test the scheduler service functionality."""
    logger.info("Testing scheduler service functionality")
    
    service = SchedulerService()
    if not await service.initialize():
        logger.error("Failed to initialize scheduler service")
        return
    
    try:
        # Schedule a test conversation for 5 minutes from now
        scheduled_time = datetime.now() + timedelta(minutes=5)
        conversation_id = await service.schedule_conversation(
            conversation_text="This is a test scheduled message from the SchedulerService wrapper",
            scheduled_time=scheduled_time,
            endpoint="https://example.com/callback",
            additional_info="Test from SchedulerService wrapper"
        )
        
        if conversation_id:
            # Check the conversation status
            status = await service.get_conversation_status(conversation_id)
            if status:
                logger.info(f"Conversation status: {status}")
            
            # Cancel the conversation
            cancelled = await service.cancel_conversation(conversation_id)
            logger.info(f"Conversation cancelled: {cancelled}")
            
            if cancelled:
                # Check the status again to verify cancellation
                status = await service.get_conversation_status(conversation_id)
                logger.info(f"Conversation status after cancellation: {status}")
        
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(test_scheduler_service())
