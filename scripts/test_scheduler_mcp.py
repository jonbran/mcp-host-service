#!/usr/bin/env python3
"""
Test script for the new MCP SDK integration with the Scheduler service.

This script tests connecting to the Scheduler MCP service and listing its tools.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from mcp import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_scheduler_connection(url: str) -> None:
    """Test connecting to the Scheduler MCP service.
    
    Args:
        url: URL of the Scheduler MCP service
    """
    logger.info(f"Testing connection to Scheduler MCP service at {url}")
    
    try:
        # Connect to the Scheduler using the MCP SDK Client
        async with Client(url) as client:
            logger.info("Connected to Scheduler service")
            
            # Try to initialize the client
            logger.info("Initializing client...")
            await client.initialize()
            logger.info("Client initialized")
            
            # List available tools
            logger.info("Listing tools...")
            tools = await client.list_tools()
            logger.info(f"Found {len(tools)} tools:")
            for tool in tools:
                logger.info(f"  - {tool.name}: {tool.description}")
                if tool.parameters:
                    logger.info(f"    Parameters:")
                    for param in tool.parameters:
                        required = "required" if param.required else "optional"
                        logger.info(f"      - {param.name}: {param.description} ({required})")
            
            # List available resources
            logger.info("Listing resources...")
            resources = await client.list_resources()
            logger.info(f"Found {len(resources)} resources:")
            for resource in resources:
                logger.info(f"  - {resource.name}: {resource.description}")
                logger.info(f"    URI template: {resource.uri_template}")
            
    except Exception as e:
        logger.error(f"Error connecting to Scheduler service: {e}", exc_info=True)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test MCP SDK with Scheduler service")
    parser.add_argument(
        "--url", 
        type=str, 
        default="http://localhost:5146/mcp",
        help="URL of the Scheduler MCP service (default: http://localhost:5146/mcp)"
    )
    args = parser.parse_args()
    
    try:
        asyncio.run(test_scheduler_connection(args.url))
        return 0
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
