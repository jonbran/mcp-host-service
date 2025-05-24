#!/usr/bin/env python
"""
Script to update MCP server configurations.

This script ensures that the Playwright MCP server is properly configured
in the MCP host configuration file.
"""

import argparse
import json
import sys
from pathlib import Path

CONFIG_PATH = Path("config/config.json")


def update_playwright_config(config_path: Path = CONFIG_PATH):
    """Update the Playwright MCP server configuration.
    
    Args:
        config_path: Path to the config file
    
    Returns:
        True if the configuration was updated, False otherwise
    """
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        return False
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse configuration file at {config_path}")
        return False
    
    # Check if MCP configuration exists
    if "mcp" not in config:
        config["mcp"] = {}
    
    # Check if MCP servers list exists
    if "mcp_servers" not in config["mcp"]:
        config["mcp"]["mcp_servers"] = []
    
    # Check if Playwright configuration already exists
    playwright_exists = False
    for server in config["mcp"]["mcp_servers"]:
        if server.get("name") == "Playwright":
            playwright_exists = True
            break
    
    # Add Playwright configuration if it doesn't exist
    if not playwright_exists:
        print("Adding Playwright MCP server configuration...")
        playwright_config = {
            "name": "Playwright",
            "transport": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@executeautomation/playwright-mcp-server"]
            }
        }
        config["mcp"]["mcp_servers"].append(playwright_config)
        
        # Write updated configuration
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"Updated configuration file at {config_path}")
        return True
    else:
        print("Playwright MCP server is already configured")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Update MCP server configurations")
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help="Path to the config file (default: config/config.json)"
    )
    
    args = parser.parse_args()
    
    result = update_playwright_config(args.config)
    
    # Exit with status code
    sys.exit(0 if result or result is False else 1)


if __name__ == "__main__":
    main()
