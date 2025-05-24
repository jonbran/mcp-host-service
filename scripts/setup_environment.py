#!/usr/bin/env python
"""
Script to set up the MCP Host environment.

This script:
1. Creates a .env file if it doesn't exist
2. Ensures config.json uses environment variables for API keys
"""

import json
import os
import sys
from pathlib import Path
from shutil import copyfile

# Paths
ENV_EXAMPLE_PATH = Path(".env.example")
ENV_PATH = Path(".env")
CONFIG_TEMPLATE_PATH = Path("config/config.template.json")
CONFIG_PATH = Path("config/config.json")


def ensure_env_file():
    """Ensure that a .env file exists."""
    if not ENV_PATH.exists():
        if ENV_EXAMPLE_PATH.exists():
            print(f"Creating .env file from {ENV_EXAMPLE_PATH}")
            copyfile(ENV_EXAMPLE_PATH, ENV_PATH)
            print(f"Please edit {ENV_PATH} to add your API keys")
            return True
        else:
            print(f"Error: {ENV_EXAMPLE_PATH} not found")
            return False
    else:
        print(f"{ENV_PATH} already exists")
        return True


def ensure_config_uses_env_vars():
    """Ensure that config.json uses environment variables for API keys."""
    if not CONFIG_PATH.exists() and CONFIG_TEMPLATE_PATH.exists():
        print(f"Creating {CONFIG_PATH} from {CONFIG_TEMPLATE_PATH}")
        copyfile(CONFIG_TEMPLATE_PATH, CONFIG_PATH)
        print(f"Created {CONFIG_PATH} with environment variable placeholders")
        return True
    
    elif CONFIG_PATH.exists():
        # Check if config.json already uses environment variables
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
            
            # Check if API keys are using environment variables
            anthropic_key = config.get("models", {}).get("anthropic", {}).get("api_key", "")
            openai_key = config.get("models", {}).get("openai", {}).get("api_key", "")
            main_key = config.get("model", {}).get("api_key", "")
            
            needs_update = False
            
            # Check if any API key looks like an actual key (not an env var placeholder)
            if anthropic_key and not anthropic_key.startswith("${") and anthropic_key != "your_anthropic_api_key_here":
                needs_update = True
            
            if openai_key and not openai_key.startswith("${") and openai_key != "your_openai_api_key_here":
                needs_update = True
            
            if main_key and not main_key.startswith("${") and main_key != "your_anthropic_api_key_here":
                needs_update = True
            
            if needs_update:
                print(f"Updating {CONFIG_PATH} to use environment variables for API keys")
                
                # Update API keys to use environment variables
                if anthropic_key and not anthropic_key.startswith("${"):
                    config["models"]["anthropic"]["api_key"] = "${ANTHROPIC_API_KEY}"
                
                if openai_key and not openai_key.startswith("${"):
                    config["models"]["openai"]["api_key"] = "${OPENAI_API_KEY}"
                
                if main_key and not main_key.startswith("${"):
                    config["model"]["api_key"] = "${ANTHROPIC_API_KEY}"
                
                # Create a backup of the original config
                backup_path = CONFIG_PATH.with_suffix(".backup.json")
                print(f"Creating backup of original config at {backup_path}")
                copyfile(CONFIG_PATH, backup_path)
                
                # Write the updated config
                with open(CONFIG_PATH, "w") as f:
                    json.dump(config, f, indent=2)
                
                print(f"Updated {CONFIG_PATH} to use environment variables")
                return True
            else:
                print(f"{CONFIG_PATH} already uses environment variables for API keys")
                return True
        
        except Exception as e:
            print(f"Error processing {CONFIG_PATH}: {e}")
            return False
    else:
        print(f"Error: Neither {CONFIG_PATH} nor {CONFIG_TEMPLATE_PATH} found")
        return False


def main():
    """Main entry point."""
    print("Setting up MCP Host environment...")
    
    # Ensure .env file exists
    env_result = ensure_env_file()
    
    # Ensure config.json uses environment variables
    config_result = ensure_config_uses_env_vars()
    
    if env_result and config_result:
        print("\nEnvironment setup complete!")
        print("\nTo use this configuration:")
        print("1. Edit the .env file to add your API keys")
        print("2. Restart the MCP Host service")
        print("\nYou can now safely commit your code without exposing API keys")
        return 0
    else:
        print("\nEnvironment setup failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
