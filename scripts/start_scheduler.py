#!/usr/bin/env python3
"""
Script to start the Scheduler MCP service.

This script provides a simple interface to start/stop the Scheduler service
based on the configuration details in the Scheduler-host-integration.md file.
"""

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default path to the Scheduler service executable
# This path needs to be updated based on the actual location of the Scheduler service
DEFAULT_SCHEDULER_PATH = "/Users/jonbrandon/code/AI/RussellDemo/scheduler/McpScheduler.dll"


def start_scheduler(scheduler_path: str, port: int = 5146, debug: bool = False) -> subprocess.Popen:
    """Start the Scheduler MCP service.
    
    Args:
        scheduler_path: Path to the Scheduler service executable
        port: Port to run the service on
        debug: Enable debug output
        
    Returns:
        Process handle to the started service
    """
    logger.info(f"Starting Scheduler service from {scheduler_path} on port {port}")
    
    # Check if the scheduler executable exists
    if not Path(scheduler_path).exists():
        logger.error(f"Scheduler executable not found at {scheduler_path}")
        logger.error("Please update the script with the correct path to the Scheduler service.")
        sys.exit(1)
    
    # Prepare the command to start the .NET service
    # For a .NET application, we need to use 'dotnet' to run the DLL
    command = [
        "dotnet",
        scheduler_path,
        "--urls", f"http://localhost:{port}"
    ]
    
    if debug:
        command.append("--debug")
        logger.info("Debug mode enabled")
    
    # Start the process
    try:
        # Start the process and redirect output to a log file
        log_path = Path("scheduler_service.log")
        log_file = open(log_path, "w")
        
        process = subprocess.Popen(
            command,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )
        
        logger.info(f"Scheduler service started with PID {process.pid}")
        logger.info(f"Output is being logged to {log_path}")
        
        # Give the service a moment to start up
        time.sleep(2)
        
        # Check if the process is still running
        if process.poll() is not None:
            logger.error(f"Scheduler service failed to start: exit code {process.poll()}")
            logger.error(f"Check the log file for details: {log_path}")
            sys.exit(1)
        
        logger.info(f"Scheduler service is running at http://localhost:{port}/mcp")
        return process
    
    except Exception as e:
        logger.error(f"Error starting Scheduler service: {e}", exc_info=True)
        sys.exit(1)


def stop_scheduler(process: subprocess.Popen) -> None:
    """Stop the Scheduler MCP service.
    
    Args:
        process: Process handle to the running service
    """
    logger.info(f"Stopping Scheduler service (PID {process.pid})")
    
    try:
        # First try to gracefully terminate the process
        process.terminate()
        
        # Wait for up to 5 seconds for the process to terminate
        try:
            process.wait(timeout=5)
            logger.info("Scheduler service stopped gracefully")
        except subprocess.TimeoutExpired:
            # If it doesn't terminate, kill it
            logger.warning("Scheduler service did not terminate gracefully, killing...")
            process.kill()
            process.wait()
            logger.info("Scheduler service killed")
    
    except Exception as e:
        logger.error(f"Error stopping Scheduler service: {e}", exc_info=True)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Start the Scheduler MCP service")
    parser.add_argument(
        "--path", 
        type=str, 
        default=DEFAULT_SCHEDULER_PATH,
        help=f"Path to the Scheduler service executable (default: {DEFAULT_SCHEDULER_PATH})"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=5146,
        help="Port to run the service on (default: 5146)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug output"
    )
    args = parser.parse_args()
    
    # Start the scheduler service
    process = start_scheduler(args.path, args.port, args.debug)
    
    try:
        # Keep the script running until interrupted
        logger.info("Press Ctrl+C to stop the Scheduler service")
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        # Stop the service on keyboard interrupt
        stop_scheduler(process)
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        stop_scheduler(process)
        sys.exit(1)


if __name__ == "__main__":
    main()
