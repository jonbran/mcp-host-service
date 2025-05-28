#!/usr/bin/env python
"""
Configuration script for MCP servers.

This script helps to configure MCP servers in the config.json file.
It provides a command-line interface for adding, removing, and listing MCP servers.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from app.config.config import AppConfig, MCPServerConfig, TransportConfig, TransportType


def load_config(config_path: Path) -> Dict:
    """Load configuration from file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        return create_default_config()
    
    with open(config_path, "r") as f:
        return json.load(f)


def save_config(config: Dict, config_path: Path) -> None:
    """Save configuration to file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to the configuration file
    """
    config_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"Configuration saved to {config_path}")


def create_default_config() -> Dict:
    """Create default configuration.
    
    Returns:
        Default configuration dictionary
    """
    return {
        "mcp": {
            "mcp_servers": []
        },
        "model": {
            "model_id": "deepseek-ai/DeepSeek-R1",
            "max_sequence_length": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
            "batch_size": 1,
            "device": "cpu",
            "optimize": True
        },
        "api": {
            "host": "0.0.0.0",
            "port": 8000,
            "timeout": 60,
            "max_request_size": 1048576,
            "default_format": "json",
            "rate_limit_enabled": False,
            "rate_limit": 100
        },
        "data_dir": "./data"
    }


def list_servers(config: Dict) -> None:
    """List configured MCP servers.
    
    Args:
        config: Configuration dictionary
    """
    servers = config.get("mcp", {}).get("mcp_servers", [])
    
    if not servers:
        print("No MCP servers configured")
        return
    
    print(f"Found {len(servers)} MCP servers:")
    
    for i, server in enumerate(servers):
        print(f"\n{i+1}. {server['name']}")
        print(f"   Transport: {server['transport']['type']}")
        
        if server['transport']['type'] == "stdio":
            command = server['transport'].get('command', 'N/A')
            args = " ".join(server['transport'].get('args', []))
            print(f"   Command: {command} {args}")
        elif server['transport']['type'] == "sse":
            url = server['transport'].get('url', 'N/A')
            print(f"   URL: {url}")
        
        if server.get('params'):
            print(f"   Params: {server['params']}")


def add_server(config: Dict, name: str, transport_type: str, url: Optional[str] = None,
               command: Optional[str] = None, args: Optional[List[str]] = None) -> Dict:
    """Add an MCP server to the configuration.
    
    Args:
        config: Configuration dictionary
        name: Server name
        transport_type: Transport type (stdio/sse)
        url: URL for SSE transport
        command: Command for STDIO transport
        args: Arguments for STDIO transport
        
    Returns:
        Updated configuration dictionary
    """
    # Ensure mcp and mcp_servers exist
    if "mcp" not in config:
        config["mcp"] = {}
    
    if "mcp_servers" not in config["mcp"]:
        config["mcp"]["mcp_servers"] = []
    
    # Check if server already exists
    for server in config["mcp"]["mcp_servers"]:
        if server["name"] == name:
            print(f"Server '{name}' already exists, updating configuration")
            config["mcp"]["mcp_servers"].remove(server)
            break
    
    # Create transport configuration
    transport = {"type": transport_type}
    
    if transport_type == "stdio":
        if not command:
            print("Error: Command is required for STDIO transport")
            return config
        
        transport["command"] = command
        if args:
            transport["args"] = args
    
    elif transport_type == "sse":
        if not url:
            print("Error: URL is required for SSE transport")
            return config
        
        transport["url"] = url
    
    else:
        print(f"Error: Unsupported transport type: {transport_type}")
        return config
    
    # Create server configuration
    server = {
        "name": name,
        "transport": transport
    }
    
    # Add to configuration
    config["mcp"]["mcp_servers"].append(server)
    
    print(f"Added MCP server '{name}' with {transport_type} transport")
    
    return config


def remove_server(config: Dict, name: str) -> Dict:
    """Remove an MCP server from the configuration.
    
    Args:
        config: Configuration dictionary
        name: Server name
        
    Returns:
        Updated configuration dictionary
    """
    if "mcp" not in config or "mcp_servers" not in config["mcp"]:
        print("No MCP servers configured")
        return config
    
    # Find server by name
    for server in config["mcp"]["mcp_servers"]:
        if server["name"] == name:
            config["mcp"]["mcp_servers"].remove(server)
            print(f"Removed MCP server '{name}'")
            return config
    
    print(f"MCP server '{name}' not found")
    return config


def add_sample_servers(config: Dict) -> Dict:
    """Add sample MCP servers to the configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Updated configuration dictionary
    """
    # Add WebScraper server
    config = add_server(
        config,
        name="WebScraper",
        transport_type="stdio",
        command="python",
        args=["scripts/webscraper_server.py"]
    )
    
    # Add SearchEngine server
    config = add_server(
        config,
        name="SearchEngine",
        transport_type="sse",
        url="http://localhost:8002/search-mcp"
    )
    
    return config


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Server Configuration Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List configured MCP servers")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add an MCP server")
    add_parser.add_argument("--name", required=True, help="Server name")
    add_parser.add_argument("--type", required=True, choices=["stdio", "sse"], help="Transport type")
    add_parser.add_argument("--url", help="URL for SSE transport")
    add_parser.add_argument("--command", help="Command for STDIO transport")
    add_parser.add_argument("--args", nargs="*", help="Arguments for STDIO transport")
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove an MCP server")
    remove_parser.add_argument("--name", required=True, help="Server name")
    
    # Add sample servers command
    sample_parser = subparsers.add_parser("add-samples", help="Add sample MCP servers")
    
    # Config file option
    parser.add_argument("--config", default="config/config.json", help="Path to config file")
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(args.config)
    config = load_config(config_path)
    
    # Execute command
    if args.command == "list":
        list_servers(config)
    
    elif args.command == "add":
        config = add_server(
            config,
            name=args.name,
            transport_type=args.type,
            url=args.url,
            command=args.command,
            args=args.args
        )
        save_config(config, config_path)
    
    elif args.command == "remove":
        config = remove_server(config, args.name)
        save_config(config, config_path)
    
    elif args.command == "add-samples":
        config = add_sample_servers(config)
        save_config(config, config_path)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
