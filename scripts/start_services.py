#!/usr/bin/env python
"""
Start script for the MCP service and sample MCP servers.

This script starts:
1. The MCP service
2. The WebScraper MCP server (if --webscraper is specified)
3. The SearchEngine MCP server (if --searchengine is specified)
"""

import argparse
import asyncio
import os
import signal
import subprocess
import sys
from pathlib import Path


async def start_services(start_webscraper: bool, start_searchengine: bool):
    """Start the MCP service and servers.
    
    Args:
        start_webscraper: Whether to start the WebScraper server
        start_searchengine: Whether to start the SearchEngine server
    """
    processes = []
    
    try:
        # Start the MCP service
        mcp_service = subprocess.Popen(
            ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        processes.append(("MCP Service", mcp_service))
        print("MCP Service started on http://localhost:8000")
        
        # Start the WebScraper server if requested
        if start_webscraper:
            webscraper = subprocess.Popen(
                ["python", "scripts/webscraper_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(("WebScraper", webscraper))
            print("WebScraper server started")
        
        # Start the SearchEngine server if requested
        if start_searchengine:
            searchengine = subprocess.Popen(
                ["uvicorn", "scripts.search_server:app", "--host", "0.0.0.0", "--port", "8001"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(("SearchEngine", searchengine))
            print("SearchEngine server started on http://localhost:8001")
        
        print("\nPress Ctrl+C to stop all services\n")
        
        # Wait indefinitely
        while True:
            await asyncio.sleep(1)
            
            # Check if any process has terminated
            for name, process in processes:
                if process.poll() is not None:
                    print(f"{name} terminated unexpectedly with code {process.returncode}")
                    
                    # Print stderr
                    stderr = process.stderr.read().decode()
                    if stderr:
                        print(f"{name} stderr:")
                        print(stderr)
                    
                    # Terminate all processes
                    for _, p in processes:
                        if p.poll() is None:
                            p.terminate()
                    
                    return
    
    except KeyboardInterrupt:
        print("\nStopping services...")
    
    finally:
        # Terminate all processes
        for name, process in processes:
            if process.poll() is None:
                print(f"Terminating {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"Force killing {name}...")
                    process.kill()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Start MCP Service and Servers")
    parser.add_argument(
        "--webscraper", 
        action="store_true", 
        help="Start the WebScraper server"
    )
    parser.add_argument(
        "--searchengine", 
        action="store_true",
        help="Start the SearchEngine server"
    )
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Start all servers"
    )
    
    args = parser.parse_args()
    
    # If --all is specified, start all servers
    if args.all:
        args.webscraper = True
        args.searchengine = True
    
    # If no servers specified, provide a warning
    if not (args.webscraper or args.searchengine):
        print("Warning: No MCP servers specified. Only the MCP service will be started.")
        print("Use --webscraper, --searchengine, or --all to start MCP servers.\n")
    
    asyncio.run(start_services(args.webscraper, args.searchengine))


if __name__ == "__main__":
    main()
