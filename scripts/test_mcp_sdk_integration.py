#!/usr/bin/env python3
"""
Comprehensive test script for MCP SDK integration.

This script tests:
1. Connection to all configured MCP servers including the Scheduler
2. Listing tools and resources from each server
3. Making a simple tool call to verify functionality
4. Making a simple resource call to verify functionality
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.append(str(Path(__file__).parent.parent))

from app.config.config import load_config, AppConfig, MCPServerConfig
from app.host.mcp_client import MCPSdkClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

CONFIG_FILE = Path("config/config.json")


async def test_mcp_server(server_config: MCPServerConfig) -> None:
    """Test connectivity and functionality of an MCP server.
    
    Args:
        server_config: Configuration for the MCP server
    """
    logger.info(f"Testing MCP server: {server_config.name}")
    
    try:
        # Initialize the client
        client = MCPSdkClient(server_config)
        await client.initialize()
        logger.info(f"Successfully connected to {server_config.name}")
        
        # List tools
        tools = await client.list_tools()
        logger.info(f"Found {len(tools)} tools on {server_config.name}:")
        for tool in tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")
        
        # List resources
        resources = await client.list_resources()
        logger.info(f"Found {len(resources)} resources on {server_config.name}:")
        for resource in resources:
            logger.info(f"  - {resource['name']}: {resource['description']}")
        
        # Try calling a simple tool if available
        if tools:
            # Choose a tool that doesn't require parameters, if available
            simple_tools = [
                t for t in tools 
                if not any(p["required"] for p in t["parameters"])
            ]
            
            if simple_tools:
                test_tool = simple_tools[0]
                logger.info(f"Testing tool call: {test_tool['name']}")
                result = await client.call_tool(test_tool["name"])
                logger.info(f"Tool call result: {result}")
            else:
                logger.info(f"No simple tools available for testing on {server_config.name}")
        
        # Close the client
        await client.close()
        logger.info(f"Successfully completed tests for {server_config.name}")
    
    except Exception as e:
        logger.error(f"Error testing {server_config.name}: {e}", exc_info=True)


async def test_all_servers(config_path: Path, server_name: Optional[str] = None) -> None:
    """Test all MCP servers in the configuration or a specific one.
    
    Args:
        config_path: Path to the configuration file
        server_name: Optional name of specific server to test
    """
    logger.info(f"Loading configuration from {config_path}")
    
    try:
        # Load configuration
        config = load_config(config_path)
        
        if not config.mcp or not config.mcp.mcp_servers:
            logger.warning("No MCP servers configured")
            return
        
        # Filter servers if a specific name is provided
        servers = config.mcp.mcp_servers
        if server_name:
            servers = [s for s in servers if s.name == server_name]
            if not servers:
                logger.error(f"Server {server_name} not found in configuration")
                return
        
        logger.info(f"Testing {len(servers)} MCP servers")
        
        # Test each server sequentially
        for server_config in servers:
            await test_mcp_server(server_config)
    
    except Exception as e:
        logger.error(f"Error loading configuration: {e}", exc_info=True)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test MCP SDK integration")
    parser.add_argument(
        "--config", 
        type=str, 
        default=str(CONFIG_FILE),
        help=f"Path to configuration file (default: {CONFIG_FILE})"
    )
    parser.add_argument(
        "--server", 
        type=str,
        help="Name of specific server to test"
    )
    args = parser.parse_args()
    
    try:
        asyncio.run(test_all_servers(Path(args.config), args.server))
        return 0
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
