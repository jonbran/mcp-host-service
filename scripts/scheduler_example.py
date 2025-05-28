#!/usr/bin/env python3
"""
Example script demonstrating how to use the Scheduler service in the RussellDemo project.

This script shows how to:
1. Schedule a conversation for future delivery
2. List scheduled conversations and their statuses
3. Cancel a scheduled conversation
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from app.scheduler.scheduler_service import SchedulerService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def schedule_demo_conversation(service: SchedulerService, minutes_from_now: int = 5) -> Optional[str]:
    """Schedule a demo conversation.
    
    Args:
        service: Scheduler service instance
        minutes_from_now: Minutes from now to schedule the conversation
        
    Returns:
        Conversation ID if successful, None otherwise
    """
    scheduled_time = datetime.now() + timedelta(minutes=minutes_from_now)
    
    logger.info(f"Scheduling a demo conversation for {scheduled_time.isoformat()}")
    
    return await service.schedule_conversation(
        conversation_text="This is a demonstration of the Scheduler service integration with RussellDemo.",
        scheduled_time=scheduled_time,
        endpoint="https://example.com/demo-callback",
        additional_info="Scheduled from the example script"
    )


async def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Scheduler service example")
    parser.add_argument(
        "--schedule", 
        action="store_true",
        help="Schedule a demo conversation"
    )
    parser.add_argument(
        "--check", 
        type=str,
        metavar="CONVERSATION_ID",
        help="Check the status of a conversation"
    )
    parser.add_argument(
        "--cancel", 
        type=str,
        metavar="CONVERSATION_ID",
        help="Cancel a scheduled conversation"
    )
    parser.add_argument(
        "--minutes", 
        type=int,
        default=5,
        help="Minutes from now to schedule the conversation (default: 5)"
    )
    
    args = parser.parse_args()
    
    if not any([args.schedule, args.check, args.cancel]):
        parser.print_help()
        return 0
    
    # Initialize the scheduler service
    service = SchedulerService()
    if not await service.initialize():
        logger.error("Failed to initialize scheduler service")
        return 1
    
    try:
        # Schedule a demo conversation
        if args.schedule:
            conversation_id = await schedule_demo_conversation(service, args.minutes)
            if conversation_id:
                logger.info(f"Successfully scheduled conversation: {conversation_id}")
                
                # Check the status immediately
                status = await service.get_conversation_status(conversation_id)
                logger.info(f"Current status: {status}")
                
                # Print command to check status later
                print(f"\nTo check status later, run:")
                print(f"python scripts/scheduler_example.py --check {conversation_id}")
                
                # Print command to cancel the conversation
                print(f"\nTo cancel this conversation, run:")
                print(f"python scripts/scheduler_example.py --cancel {conversation_id}")
            else:
                logger.error("Failed to schedule conversation")
                return 1
        
        # Check conversation status
        if args.check:
            status = await service.get_conversation_status(args.check)
            if status:
                logger.info(f"Conversation status for {args.check}: {status}")
            else:
                logger.error(f"Failed to get status for conversation {args.check}")
                return 1
        
        # Cancel conversation
        if args.cancel:
            cancelled = await service.cancel_conversation(args.cancel)
            if cancelled:
                logger.info(f"Successfully cancelled conversation {args.cancel}")
                
                # Check the status after cancellation
                status = await service.get_conversation_status(args.cancel)
                logger.info(f"Current status: {status}")
            else:
                logger.error(f"Failed to cancel conversation {args.cancel}")
                return 1
        
        return 0
    
    finally:
        # Close the service
        await service.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
