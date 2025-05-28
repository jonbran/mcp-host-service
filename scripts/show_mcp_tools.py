#!/usr/bin/env python3
"""
Script to show available MCP tools and their capabilities.

This script queries the MCP Host service to get information about:
1. All available model providers and MCP servers
2. Tool capabilities of MCP servers

Usage:
    python show_mcp_tools.py [--port PORT]

Options:
    --port PORT    Port to use for the MCP Host service (default: 8001)
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import httpx


async def get_auth_token(base_url: str) -> Optional[str]:
    """Get authentication token from the API.
    
    Args:
        base_url: Base URL of the API
        
    Returns:
        Bearer token string if successful, None otherwise
    """
    print("Authenticating...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/auth/token",
                data={"username": "admin", "password": "adminpassword"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                print(f"Authentication failed: {response.text}")
                return None
                
            token_data = response.json()
            token = token_data.get("access_token")
            token_type = token_data.get("token_type", "bearer")
            
            return f"{token_type} {token}"
    except Exception as e:
        print(f"Authentication error: {e}")
        return None


async def get_model_providers(base_url: str, auth_header: Dict[str, str]) -> Dict:
    """Get all model providers including MCP servers.
    
    Args:
        base_url: Base URL of the API
        auth_header: Authentication header
        
    Returns:
        Dict with model providers data
    """
    print("\nGetting model providers...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/models", headers=auth_header)
        
        if response.status_code != 200:
            print(f"Failed to get model providers: {response.text}")
            return {}
            
        providers_data = response.json()
        return providers_data





async def test_mcp_server_tools(base_url: str, server_name: str, auth_header: Dict[str, str]) -> Dict:
    """Test for available tools on an MCP server.
    
    Args:
        base_url: Base URL of the API
        server_name: Name of the MCP server
        auth_header: Authentication header
        
    Returns:
        Dict with MCP tools data
    """
    # This is a best effort - we'll try common introspection methods
    # that might be implemented by the MCP servers
    print(f"\nTesting tools for {server_name} MCP server...")
    try:
        # Try a generic approach
        # First approach: Try direct introspection via dedicated endpoint if it exists
        endpoint = f"{base_url}/{server_name.lower()}"
        
        async with httpx.AsyncClient() as client:
            try:
                # Try for available tools
                response = await client.post(
                    endpoint,
                    json={
                        "type": "tool",
                        "name": "available_tools",
                        "params": {}
                    },
                    headers=auth_header,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
            except Exception:
                pass  # Silently continue if this fails
                
            try:
                # Try for available resources
                response = await client.post(
                    endpoint,
                    json={
                        "type": "resource",
                        "name": "available_resources",
                        "params": {}
                    },
                    headers=auth_header,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
            except Exception:
                pass  # Silently continue if this fails
        
        return {"error": f"Could not introspect tools for {server_name}"}
                
    except Exception as e:
        print(f"Error testing {server_name}: {e}")
        return {"error": str(e)}


async def pretty_print_json(data: Dict) -> None:
    """Print JSON data in a nicely formatted way.
    
    Args:
        data: Dictionary to print
    """
    print(json.dumps(data, indent=2))


def load_mcp_config() -> Dict[str, Any]:
    """Load MCP configuration from config file.
    
    Returns:
        Dict containing MCP server configurations
    """
    try:
        config_path = Path('/Users/jonbrandon/code/AI/RussellDemo/host/config/config.json')
        if not config_path.exists():
            return {}
            
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        return config.get('mcp', {})
    except Exception as e:
        print(f"Error loading MCP config: {e}")
        return {}


async def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Show available MCP tools")
    parser.add_argument("--port", type=int, default=8000, help="Port for the API (default: 8000)")
    args = parser.parse_args()
    
    # Set up base URL
    base_url = f"http://localhost:{args.port}/api"
    
    # Load MCP configuration
    print("\n=== MCP Configuration ===")
    mcp_config = load_mcp_config()
    if mcp_config:
        mcp_servers_config = mcp_config.get('mcp_servers', [])
        print(f"Found {len(mcp_servers_config)} MCP servers in configuration")
        for i, server in enumerate(mcp_servers_config):
            print(f"\n{i+1}. {server['name']}")
            print(f"   Transport type: {server['transport']['type']}")
            
            if server['transport']['type'] == "stdio":
                cmd = server['transport'].get('command', '')
                cmd_args = " ".join(server['transport'].get('args', []))
                print(f"   Command: {cmd} {cmd_args}")
            elif server['transport']['type'] == "sse":
                url = server['transport'].get('url', '')
                print(f"   URL: {url}")
                
            if 'config' in server:
                print(f"   Configuration: {json.dumps(server['config'], indent=2)}")
    else:
        print("No MCP configuration found")
    
    # Get auth token
    auth_token = await get_auth_token(base_url)
    if not auth_token:
        print("Could not authenticate. Make sure the MCP Host service is running.")
        sys.exit(1)
        
    auth_header = {"Authorization": auth_token}
    
    # Get all providers
    providers_data = await get_model_providers(base_url, auth_header)
    if not providers_data:
        print("Could not get providers data. Make sure the MCP Host service is running.")
        sys.exit(1)
        
    print("\n=== All Providers (Including MCP Servers) ===")
    await pretty_print_json(providers_data)
    
    # Extract MCP servers
    mcp_servers = [p for p in providers_data.get("providers", []) 
                  if p.get("is_mcp_server", False)]
    
    if not mcp_servers:
        print("\nNo MCP servers found.")
        sys.exit(0)
        
    print(f"\nFound {len(mcp_servers)} MCP servers:")
    for server in mcp_servers:
        print(f"  - {server['name']}")
    
    # Test each MCP server
    for server in mcp_servers:
        server_name = server["name"]
        server_tools = await test_mcp_server_tools(base_url, server_name, auth_header)
        
        print(f"\n=== {server_name} MCP Server Tools ===")
        await pretty_print_json(server_tools)
        
    # Show documentation info
    print("\n=== Documentation ===")
    print("For detailed information about available tools, check the documentation:")
    print("- WebScraper: See scripts/README.md")
    print("- SearchEngine: See scripts/README.md")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
