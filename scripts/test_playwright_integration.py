#!/usr/bin/env python
"""
Test script for Playwright MCP server integration.

This script:
1. Starts the MCP host service (if not already running)
2. Runs the Playwright MCP server test
3. Reports results
"""

import argparse
import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest


async def wait_for_service(url: str, max_retries: int = 10, retry_delay: int = 2):
    """Wait for the service to be available.
    
    Args:
        url: URL to check
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds
        
    Returns:
        True if service is available, False otherwise
    """
    for i in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    print(f"Service is available at {url}")
                    return True
        except Exception as e:
            print(f"Service not yet available (attempt {i+1}/{max_retries}): {e}")
        
        await asyncio.sleep(retry_delay)
    
    print(f"Service not available after {max_retries} attempts")
    return False


async def test_playwright_integration():
    """Test Playwright MCP server integration."""
    # Define the base URL for the API
    base_url = "http://localhost:8001"
    
    # Wait for the service to be available
    if not await wait_for_service(base_url):
        print("MCP host service is not available. Please start it first.")
        sys.exit(1)
    
    # Run the test
    result = pytest.main(["-v", "tests/test_playwright_mcp_server.py"])
    
    if result == pytest.ExitCode.OK:
        print("\n✅ Playwright MCP server integration test passed!")
        print("\nYou can now use the Playwright MCP server with the MCP host.")
        print("For more information, see docs/playwright_mcp.md")
    else:
        print("\n❌ Playwright MCP server integration test failed.")
        print("Please check the error messages above and troubleshoot accordingly.")
        print("\nCommon issues:")
        print("1. Make sure the Playwright MCP server is installed: npm install -g @executeautomation/playwright-mcp-server")
        print("2. Verify that the MCP host service is running correctly")
        print("3. Check that the Playwright MCP server configuration in config/config.json is correct")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Playwright MCP server integration")
    parser.add_argument(
        "--start-service",
        action="store_true",
        help="Start the MCP host service if not already running",
    )
    
    args = parser.parse_args()
    
    if args.start_service:
        print("Starting MCP host service...")
        service_process = subprocess.Popen(
            ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        # Give the service some time to start
        time.sleep(5)
    
    try:
        asyncio.run(test_playwright_integration())
    finally:
        if args.start_service and 'service_process' in locals():
            print("Stopping MCP host service...")
            service_process.terminate()
            service_process.wait()
