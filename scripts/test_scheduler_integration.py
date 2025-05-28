#!/usr/bin/env python3
"""
Integration test script for the MCP SDK with the Scheduler service.

This script tests the full integration flow:
1. Start the API server with the MCP SDK integration
2. Schedule a conversation using the SchedulerService wrapper
3. Verify the conversation is scheduled correctly
4. Cancel the conversation
5. Verify the cancellation was successful
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin

import httpx

sys.path.append(str(Path(__file__).parent.parent))

from app.scheduler.scheduler_service import SchedulerService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default API server configuration
DEFAULT_API_HOST = "localhost"
DEFAULT_API_PORT = 8000
DEFAULT_API_URL = f"http://{DEFAULT_API_HOST}:{DEFAULT_API_PORT}"

# Default Scheduler service configuration
DEFAULT_SCHEDULER_HOST = "localhost"
DEFAULT_SCHEDULER_PORT = 5146
DEFAULT_SCHEDULER_URL = f"http://{DEFAULT_SCHEDULER_HOST}:{DEFAULT_SCHEDULER_PORT}"


async def wait_for_server(url: str, timeout: int = 60, interval: int = 1) -> bool:
    """Wait for a server to become available.
    
    Args:
        url: Server URL to check
        timeout: Timeout in seconds
        interval: Check interval in seconds
    
    Returns:
        True if server is available, False otherwise
    """
    start_time = time.time()
    logger.info(f"Waiting for server at {url} to become available...")
    
    while time.time() - start_time < timeout:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    logger.info(f"Server at {url} is available")
                    return True
        except Exception:
            pass
        
        await asyncio.sleep(interval)
    
    logger.error(f"Timeout waiting for server at {url}")
    return False


async def start_api_server(
    host: str = DEFAULT_API_HOST, 
    port: int = DEFAULT_API_PORT
) -> Optional[subprocess.Popen]:
    """Start the API server as a subprocess.
    
    Args:
        host: API server host
        port: API server port
    
    Returns:
        Process handle if started successfully, None otherwise
    """
    logger.info(f"Starting API server on {host}:{port}")
    
    try:
        # Start the API server using uvicorn
        process = subprocess.Popen(
            [
                "uvicorn", 
                "app.main:app", 
                "--host", host, 
                "--port", str(port),
                "--log-level", "info"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        logger.info(f"API server started with PID {process.pid}")
        
        # Wait for the server to become available
        server_url = f"http://{host}:{port}"
        if await wait_for_server(server_url):
            return process
        else:
            # Kill the process if the server doesn't become available
            process.terminate()
            process.wait(timeout=5)
            return None
    
    except Exception as e:
        logger.error(f"Error starting API server: {e}", exc_info=True)
        return None


async def start_scheduler_service(
    host: str = DEFAULT_SCHEDULER_HOST, 
    port: int = DEFAULT_SCHEDULER_PORT,
    scheduler_path: Optional[str] = None
) -> Optional[subprocess.Popen]:
    """Start the Scheduler service as a subprocess.
    
    Args:
        host: Scheduler service host
        port: Scheduler service port
        scheduler_path: Path to the Scheduler service executable
    
    Returns:
        Process handle if started successfully, None otherwise
    """
    logger.info(f"Starting Scheduler service on {host}:{port}")
    
    # Check if running from the scripts directory and adjust path
    if Path(__file__).parent.name == "scripts":
        scheduler_script = Path(__file__).parent / "start_scheduler.py"
    else:
        scheduler_script = Path(__file__).parent / "scripts" / "start_scheduler.py"
    
    if not scheduler_script.exists():
        logger.error(f"Scheduler script not found at {scheduler_script}")
        return None
    
    try:
        # Prepare the command
        command = [
            sys.executable,
            str(scheduler_script),
            "--port", str(port)
        ]
        
        # Add scheduler path if provided
        if scheduler_path:
            command.extend(["--path", scheduler_path])
        
        # Start the Scheduler service
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        logger.info(f"Scheduler service started with PID {process.pid}")
        
        # Wait for the Scheduler service to become available
        server_url = f"http://{host}:{port}"
        if await wait_for_server(server_url, timeout=30):
            return process
        else:
            # Kill the process if the service doesn't become available
            process.terminate()
            process.wait(timeout=5)
            return None
    
    except Exception as e:
        logger.error(f"Error starting Scheduler service: {e}", exc_info=True)
        return None


async def test_scheduler_integration(
    api_url: str = DEFAULT_API_URL,
    scheduler_url: str = DEFAULT_SCHEDULER_URL
) -> bool:
    """Test the Scheduler service integration.
    
    Args:
        api_url: API server URL
        scheduler_url: Scheduler service URL
    
    Returns:
        True if all tests pass, False otherwise
    """
    logger.info("Testing Scheduler service integration")
    
    # Initialize the Scheduler service wrapper
    scheduler = SchedulerService()
    if not await scheduler.initialize():
        logger.error("Failed to initialize scheduler service")
        return False
    
    try:
        # Schedule a test conversation for 5 minutes from now
        scheduled_time = datetime.now() + timedelta(minutes=5)
        conversation_text = "This is a test scheduled message from the integration test"
        
        logger.info(f"Scheduling a conversation for {scheduled_time}")
        conversation_id = await scheduler.schedule_conversation(
            conversation_text=conversation_text,
            scheduled_time=scheduled_time,
            endpoint=f"{api_url}/api/receive",
            additional_info="Test from integration test"
        )
        
        if not conversation_id:
            logger.error("Failed to schedule conversation")
            return False
        
        logger.info(f"Scheduled conversation with ID: {conversation_id}")
        
        # Check the conversation status
        status = await scheduler.get_conversation_status(conversation_id)
        if not status:
            logger.error("Failed to get conversation status")
            return False
        
        logger.info(f"Conversation status: {status}")
        
        # Verify the status is "Scheduled"
        if status.lower() != "scheduled":
            logger.error(f"Unexpected conversation status: {status}")
            return False
        
        # Cancel the conversation
        logger.info(f"Cancelling conversation {conversation_id}")
        cancelled = await scheduler.cancel_conversation(conversation_id)
        if not cancelled:
            logger.error("Failed to cancel conversation")
            return False
        
        logger.info(f"Successfully cancelled conversation {conversation_id}")
        
        # Check the status again to verify cancellation
        status = await scheduler.get_conversation_status(conversation_id)
        if not status:
            logger.error("Failed to get conversation status after cancellation")
            return False
        
        logger.info(f"Conversation status after cancellation: {status}")
        
        # Verify the status is "Cancelled"
        if status.lower() != "cancelled":
            logger.error(f"Unexpected conversation status after cancellation: {status}")
            return False
        
        logger.info("Scheduler service integration test completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error during Scheduler integration test: {e}", exc_info=True)
        return False
    
    finally:
        # Close the scheduler service
        await scheduler.close()


async def run_integration_test(
    start_servers: bool = True,
    api_host: str = DEFAULT_API_HOST,
    api_port: int = DEFAULT_API_PORT,
    scheduler_host: str = DEFAULT_SCHEDULER_HOST,
    scheduler_port: int = DEFAULT_SCHEDULER_PORT,
    scheduler_path: Optional[str] = None
) -> bool:
    """Run the full integration test.
    
    Args:
        start_servers: Whether to start the servers or assume they're already running
        api_host: API server host
        api_port: API server port
        scheduler_host: Scheduler service host
        scheduler_port: Scheduler service port
        scheduler_path: Path to the Scheduler service executable
    
    Returns:
        True if the test passes, False otherwise
    """
    api_process = None
    scheduler_process = None
    
    try:
        # Start the servers if requested
        if start_servers:
            # Start the API server
            api_process = await start_api_server(api_host, api_port)
            if not api_process:
                logger.error("Failed to start API server")
                return False
            
            # Start the Scheduler service
            scheduler_process = await start_scheduler_service(
                scheduler_host, scheduler_port, scheduler_path
            )
            if not scheduler_process:
                logger.error("Failed to start Scheduler service")
                return False
        
        # Run the integration test
        api_url = f"http://{api_host}:{api_port}"
        scheduler_url = f"http://{scheduler_host}:{scheduler_port}"
        
        return await test_scheduler_integration(api_url, scheduler_url)
    
    finally:
        # Clean up
        if api_process:
            logger.info("Stopping API server")
            api_process.terminate()
            api_process.wait(timeout=5)
        
        if scheduler_process:
            logger.info("Stopping Scheduler service")
            scheduler_process.terminate()
            scheduler_process.wait(timeout=5)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test MCP SDK integration with Scheduler service")
    parser.add_argument(
        "--no-start-servers",
        action="store_true",
        help="Don't start the servers, assume they're already running"
    )
    parser.add_argument(
        "--api-host",
        type=str,
        default=DEFAULT_API_HOST,
        help=f"API server host (default: {DEFAULT_API_HOST})"
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=DEFAULT_API_PORT,
        help=f"API server port (default: {DEFAULT_API_PORT})"
    )
    parser.add_argument(
        "--scheduler-host",
        type=str,
        default=DEFAULT_SCHEDULER_HOST,
        help=f"Scheduler service host (default: {DEFAULT_SCHEDULER_HOST})"
    )
    parser.add_argument(
        "--scheduler-port",
        type=int,
        default=DEFAULT_SCHEDULER_PORT,
        help=f"Scheduler service port (default: {DEFAULT_SCHEDULER_PORT})"
    )
    parser.add_argument(
        "--scheduler-path",
        type=str,
        help="Path to the Scheduler service executable"
    )
    
    args = parser.parse_args()
    
    try:
        success = asyncio.run(run_integration_test(
            start_servers=not args.no_start_servers,
            api_host=args.api_host,
            api_port=args.api_port,
            scheduler_host=args.scheduler_host,
            scheduler_port=args.scheduler_port,
            scheduler_path=args.scheduler_path
        ))
        
        if success:
            logger.info("Integration test passed")
            return 0
        else:
            logger.error("Integration test failed")
            return 1
    
    except Exception as e:
        logger.error(f"Error during integration test: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
