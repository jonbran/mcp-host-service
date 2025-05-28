# Scheduler Service Integration Guide

This guide will help you understand and use the Scheduler service integration in the RussellDemo project. The Scheduler service allows you to schedule conversations for future delivery using the Model Context Protocol (MCP).

## Overview

The Scheduler service is a separate .NET Core service that implements the MCP protocol and provides tools for scheduling future conversations. It has been integrated with the RussellDemo project using the official MCP Python SDK.

## Prerequisites

- Python 3.8 or higher
- .NET Core 6.0 or higher (for running the Scheduler service)
- RussellDemo project dependencies (see requirements.txt)

## Quick Start

1. Update your configuration and install dependencies:

   ```bash
   python scripts/update_scheduler_config.py
   pip install -r requirements.txt
   ```

2. Start the services:

   ```bash
   python scripts/start_services.py --scheduler
   ```

3. Test the integration:
   ```bash
   python scripts/scheduler_example.py --schedule
   ```

## Scheduler Service

### Starting the Scheduler Service

You can start the Scheduler service in several ways:

1. **Using start_services.py (recommended)**:

   ```bash
   python scripts/start_services.py --scheduler
   ```

2. **Directly using start_scheduler.py**:

   ```bash
   python scripts/start_scheduler.py
   ```

3. **Custom path**:
   ```bash
   python scripts/start_scheduler.py --path /path/to/McpScheduler.dll
   ```

### Configuration

The Scheduler service configuration is stored in `config/config.json` as part of the MCP servers array:

```json
{
  "mcp": {
    "mcp_servers": [
      {
        "name": "Scheduler",
        "transport": {
          "type": "http",
          "url": "http://localhost:5146/mcp",
          "auth": {
            "client_id": "your_client_id",
            "api_key": "your_api_key"
          }
        }
      }
    ]
  }
}
```

You can update this configuration using:

```bash
python scripts/update_scheduler_config.py
```

### Authentication

The Scheduler service uses JWT authentication. You can set your credentials via environment variables:

```bash
export SCHEDULER_CLIENT_ID=your_client_id
export SCHEDULER_API_KEY=your_api_key
```

## Programming with the Scheduler Service

### Using the SchedulerService Wrapper

The project includes a convenient `SchedulerService` wrapper that simplifies interacting with the Scheduler service:

```python
from app.scheduler.scheduler_service import SchedulerService
import asyncio
from datetime import datetime, timedelta

async def schedule_example():
    # Initialize the service
    scheduler = SchedulerService()
    await scheduler.initialize()

    try:
        # Schedule a conversation for 5 minutes from now
        scheduled_time = datetime.now() + timedelta(minutes=5)
        conversation_id = await scheduler.schedule_conversation(
            conversation_text="This is a test scheduled message",
            scheduled_time=scheduled_time,
            endpoint="https://example.com/callback"
        )

        if conversation_id:
            print(f"Scheduled conversation: {conversation_id}")

            # Check the status
            status = await scheduler.get_conversation_status(conversation_id)
            print(f"Status: {status}")

            # Cancel the conversation
            cancelled = await scheduler.cancel_conversation(conversation_id)
            print(f"Cancelled: {cancelled}")

    finally:
        # Always close the service when done
        await scheduler.close()

# Run the example
asyncio.run(schedule_example())
```

### Available Methods

The `SchedulerService` wrapper provides the following methods:

1. **initialize()**

   - Initializes the connection to the Scheduler service
   - Returns: `bool` - True if successful

2. **schedule_conversation(conversation_text, scheduled_time, endpoint, method, additional_info)**

   - Schedules a conversation for future delivery
   - Parameters:
     - `conversation_text` (str): The text content to be sent
     - `scheduled_time` (datetime or str): When to deliver the conversation
     - `endpoint` (str): The endpoint to send the conversation to
     - `method` (str, optional): HTTP method to use (default: "POST")
     - `additional_info` (str, optional): Additional context information
   - Returns: `str` - Conversation ID or None if failed

3. **get_conversation_status(conversation_id)**

   - Gets the status of a scheduled conversation
   - Parameters:
     - `conversation_id` (str): The ID of the conversation
   - Returns: `str` - Status ("Scheduled", "InProgress", "Completed", "Failed", "Cancelled") or None if failed

4. **cancel_conversation(conversation_id)**

   - Cancels a scheduled conversation
   - Parameters:
     - `conversation_id` (str): The ID of the conversation
   - Returns: `bool` - True if successfully cancelled

5. **close()**
   - Closes the connection to the Scheduler service
   - No return value

## Testing the Integration

Several test scripts are provided to verify the integration:

1. **Testing connectivity to the Scheduler**:

   ```bash
   python scripts/test_scheduler_mcp.py
   ```

2. **Testing authentication**:

   ```bash
   python scripts/test_scheduler_auth.py --client-id your_client_id --api-key your_api_key
   ```

3. **Testing the full integration**:

   ```bash
   python scripts/test_scheduler_integration.py
   ```

4. **Example usage**:
   ```bash
   python scripts/scheduler_example.py --schedule
   ```

## Troubleshooting

If you encounter issues with the Scheduler integration, try the following:

1. **Check the Scheduler service is running**:

   ```bash
   curl http://localhost:5146/mcp/tools
   ```

2. **Verify authentication credentials**:

   ```bash
   python scripts/test_scheduler_auth.py --client-id your_client_id --api-key your_api_key
   ```

3. **Check log files**:

   - API server logs: `api_server.log`
   - Scheduler service logs: `scheduler_service.log`

4. **Update configuration**:

   ```bash
   python scripts/update_scheduler_config.py
   ```

5. **Restart services**:
   ```bash
   python scripts/start_services.py --scheduler
   ```

## References

- [MCP SDK Integration Guide](mcp_sdk_integration.md)
- [MCP SDK Integration Summary](mcp_sdk_integration_summary.md)
- [Scheduler-host-integration.md](../MCP_requirements/Scheduler-host-integration.md)
