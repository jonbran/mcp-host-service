#!/usr/bin/env python3
"""
Script to update the Scheduler service configuration in config.json.

This script ensures the Scheduler service is properly configured to use the HTTP transport type.
"""

import json
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

CONFIG_FILE = Path("config/config.json")


def update_scheduler_config() -> None:
    """Update the Scheduler configuration in config.json."""
    logger.info(f"Updating Scheduler configuration in {CONFIG_FILE}")
    
    try:
        # Load the current configuration
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        
        # Check if mcp section exists
        if "mcp" not in config:
            config["mcp"] = {"mcp_servers": []}
        
        # Check if mcp_servers exists
        if "mcp_servers" not in config["mcp"]:
            config["mcp"]["mcp_servers"] = []
        
        # Get client_id and api_key from environment variables or use defaults for testing
        client_id = os.environ.get("SCHEDULER_CLIENT_ID", "default_client_id")
        api_key = os.environ.get("SCHEDULER_API_KEY", "default_api_key")
        
        # Look for Scheduler configuration
        scheduler_found = False
        for i, server in enumerate(config["mcp"]["mcp_servers"]):
            if server.get("name") == "Scheduler":
                scheduler_found = True
                # Update Scheduler configuration
                logger.info("Updating existing Scheduler configuration")
                config["mcp"]["mcp_servers"][i] = {
                    "name": "Scheduler",
                    "transport": {
                        "type": "http",
                        "url": "http://localhost:5146/mcp",
                        "auth": {
                            "client_id": client_id,
                            "api_key": api_key
                        }
                    }
                }
                break
        
        # Add Scheduler configuration if not found
        if not scheduler_found:
            logger.info("Adding new Scheduler configuration")
            config["mcp"]["mcp_servers"].append({
                "name": "Scheduler",
                "transport": {
                    "type": "http",
                    "url": "http://localhost:5146/mcp",
                    "auth": {
                        "client_id": client_id,
                        "api_key": api_key
                    }
                }
            })
        
        # Save the updated configuration
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Scheduler configuration updated successfully in {CONFIG_FILE}")
    
    except Exception as e:
        logger.error(f"Error updating Scheduler configuration: {e}", exc_info=True)
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    update_scheduler_config()


if __name__ == "__main__":
    main()
