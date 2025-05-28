#!/usr/bin/env python
"""
Start script for the MCP service and sample MCP servers.

This script starts:
1. The MCP service
2. The WebScraper MCP server (if --webscraper is specified)
3. The SearchEngine MCP server (if --searchengine is specified)
4. The Scheduler MCP server (if --scheduler is specified)
"""

import argparse
import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


async def start_scheduler(port=5146, scheduler_path=None):
    """Start the Scheduler MCP server.
    
    Args:
        port: Port for the Scheduler service
        scheduler_path: Path to the Scheduler service executable
    
    Returns:
        Tuple of (name, process) or None if failed
    """
    # Find the Scheduler script
    if Path("scripts/start_scheduler.py").exists():
        scheduler_script = "scripts/start_scheduler.py"
    else:
        # Try to find it in the current directory
        if Path("start_scheduler.py").exists():
            scheduler_script = "start_scheduler.py"
        else:
            print("Error: start_scheduler.py not found")
            return None
    
    command = [sys.executable, scheduler_script, "--port", str(port)]
    
    if scheduler_path:
        command.extend(["--path", scheduler_path])
    
    # Start the Scheduler service
    try:
        # First, update the config
        if Path("scripts/update_scheduler_config.py").exists():
            update_script = "scripts/update_scheduler_config.py"
        else:
            update_script = "update_scheduler_config.py"
        
        if Path(update_script).exists():
            print("Updating Scheduler configuration...")
            update_process = subprocess.run(
                [sys.executable, update_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        
        # Now start the Scheduler
        print(f"Starting Scheduler service on port {port}...")
        
        # Use a log file for the Scheduler output
        log_file = open("scheduler_service.log", "w")
        
        scheduler = subprocess.Popen(
            command,
            stdout=log_file,
            stderr=log_file,
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if the process is still running
        if scheduler.poll() is not None:
            print(f"Error: Scheduler service failed to start. Check scheduler_service.log for details.")
            return None
        
        print(f"Scheduler service started. MCP endpoint: http://localhost:{port}/mcp")
        return ("Scheduler", scheduler)
    
    except Exception as e:
        print(f"Error starting Scheduler service: {e}")
        return None


async def start_services(start_webscraper: bool, start_searchengine: bool, start_scheduler: bool, scheduler_port: int = 5146, scheduler_path: str = None):
    """Start the MCP service and servers.
    
    Args:
        start_webscraper: Whether to start the WebScraper server
        start_searchengine: Whether to start the SearchEngine server
        start_scheduler: Whether to start the Scheduler server
        scheduler_port: Port for the Scheduler service
        scheduler_path: Path to the Scheduler service executable
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
                ["uvicorn", "scripts.search_server:app", "--host", "0.0.0.0", "--port", "8002"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(("SearchEngine", searchengine))
            print("SearchEngine server started on http://localhost:8002")
        
        # Start the Scheduler service if requested
        if start_scheduler:
            scheduler_result = await start_scheduler(scheduler_port, scheduler_path)
            if scheduler_result:
                processes.append(scheduler_result)
        
        print("\nPress Ctrl+C to stop all services\n")
        
        # Wait indefinitely
        while True:
            await asyncio.sleep(1)
            
            # Check if any process has terminated
            for name, process in processes:
                if process.poll() is not None:
                    print(f"{name} terminated unexpectedly with code {process.returncode}")
                    
                    # Print stderr if available
                    if hasattr(process, 'stderr') and process.stderr:
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
        "--scheduler", 
        action="store_true",
        help="Start the Scheduler server"
    )
    parser.add_argument(
        "--scheduler-port", 
        type=int, 
        default=5146,
        help="Port for the Scheduler service (default: 5146)"
    )
    parser.add_argument(
        "--scheduler-path", 
        type=str,
        help="Path to the Scheduler service executable"
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
        args.scheduler = True
    
    # If no servers specified, provide a warning
    if not (args.webscraper or args.searchengine or args.scheduler):
        print("Warning: No MCP servers specified. Only the MCP service will be started.")
        print("Use --webscraper, --searchengine, --scheduler, or --all to start MCP servers.\n")
    
    asyncio.run(start_services(
        args.webscraper, 
        args.searchengine, 
        args.scheduler,
        args.scheduler_port,
        args.scheduler_path
    ))


if __name__ == "__main__":
    main()
