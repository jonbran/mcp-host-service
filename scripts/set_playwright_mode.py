#!/usr/bin/env python
"""
Script to set the Playwright MCP server mode.

This script updates the config.json file to switch the Playwright MCP server
between Snapshot mode and Vision mode.
"""

import argparse
import json
import sys
from pathlib import Path

CONFIG_PATH = Path("config/config.json")


def set_playwright_mode(mode: str, config_path: Path = CONFIG_PATH):
    """Set the mode for the Playwright MCP server.
    
    Args:
        mode: The mode to set ('snapshot' or 'vision')
        config_path: Path to the config file
    
    Returns:
        True if the configuration was updated, False otherwise
    """
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        return False
    
    if mode not in ("snapshot", "vision"):
        print(f"Error: Invalid mode '{mode}'. Must be 'snapshot' or 'vision'.")
        return False
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse configuration file at {config_path}")
        return False
    
    # Check if MCP configuration exists
    if "mcp" not in config:
        print("Error: MCP configuration not found in config file.")
        return False
    
    # Check if MCP servers list exists
    if "mcp_servers" not in config["mcp"]:
        print("Error: MCP servers list not found in config file.")
        return False
    
    # Find Playwright configuration
    playwright_found = False
    for server in config["mcp"]["mcp_servers"]:
        if server.get("name") == "Playwright":
            playwright_found = True
            
            # Initialize config section if it doesn't exist
            if "config" not in server:
                server["config"] = {}
                
            # Update mode
            current_mode = server.get("config", {}).get("mode")
            server["config"]["mode"] = mode
            
            if current_mode == mode:
                print(f"Playwright MCP server mode is already set to '{mode}'")
                return False
            else:
                print(f"Updated Playwright MCP server mode from '{current_mode if current_mode else 'snapshot (default)'}' to '{mode}'")
                break
    
    if not playwright_found:
        print("Error: Playwright MCP server configuration not found.")
        return False
    
    # Write updated configuration
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Set Playwright MCP server mode")
    parser.add_argument(
        "mode",
        choices=["snapshot", "vision"],
        help="The mode to set ('snapshot' or 'vision')"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help="Path to the config file (default: config/config.json)"
    )
    
    args = parser.parse_args()
    
    result = set_playwright_mode(args.mode, args.config)
    
    # Exit with status code
    sys.exit(0 if result or result is False else 1)


if __name__ == "__main__":
    main()
