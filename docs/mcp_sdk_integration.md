# MCP SDK Integration Guide

This document provides details about the integration of the official Model Context Protocol (MCP) Python SDK into the RussellDemo project.

## Overview

The project previously used a custom implementation of the MCP protocol. It has now been updated to use the official MCP Python SDK (`mcp>=1.9.0`), which provides standardized interfaces for connecting to MCP servers via various transport methods including HTTP, which is required for the Scheduler service.

## Key Components

### 1. MCP Client

The new `MCPSdkClient` class (`app/host/mcp_client.py`) wraps the official MCP SDK client and provides:

- Support for all transport types (STDIO, SSE, HTTP)
- Authentication support for HTTP transport using JWT tokens
- Methods for calling resources and tools
- Methods for listing available resources and tools

### 2. MCP Host

The new `MCPSdkHost` class (`app/host/mcp_host.py`) uses the `MCPSdkClient` to:

- Connect to multiple MCP servers
- Process model messages
- Handle MCP requests from the model
- Format results for the model's consumption

### 3. Configuration Updates

The configuration module (`app/config/config.py`) has been updated to support HTTP transport and authentication:

- Added `HTTP = "http"` to the `TransportType` enum
- Updated URL validators to validate HTTP transport URLs
- Added authentication support via the `auth` field in `TransportConfig`

### 4. API Integration

The API router (`app/api/router.py`) has been updated to use the new MCP SDK Host:

```python
# Use the new MCP SDK Host implementation
mcp_host = MCPSdkHost(config, model_service)
# Legacy host is kept for backward compatibility if needed
legacy_mcp_host = MCPHost(config, model_service)
```

## Scheduler Integration

The project now supports connection to the Scheduler service, which runs on port 5146 via HTTP transport.

### Scheduler Service Wrapper

A dedicated `SchedulerService` wrapper (`app/scheduler/scheduler_service.py`) has been created to simplify interactions with the Scheduler service:

```python
from app.scheduler.scheduler_service import SchedulerService

# Initialize the service
scheduler = SchedulerService()
await scheduler.initialize()

# Schedule a conversation
conversation_id = await scheduler.schedule_conversation(
    conversation_text="This is a scheduled message",
    scheduled_time=datetime.now() + timedelta(minutes=5),
    endpoint="https://example.com/callback"
)

# Check the status
status = await scheduler.get_conversation_status(conversation_id)

# Cancel the conversation
cancelled = await scheduler.cancel_conversation(conversation_id)
```

### Authentication

The Scheduler service requires JWT authentication. The integration supports this via:

1. Configuration in `config.json`:

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

2. Automatic token acquisition in the `MCPSdkClient` when using HTTP transport with auth information.

### Utility Scripts

The following scripts have been created to facilitate working with the Scheduler service:

1. **update_scheduler_config.py**: Updates the config.json file to include the Scheduler service configuration with authentication details.
2. **start_scheduler.py**: Starts the Scheduler service as a subprocess.
3. **test_scheduler_mcp.py**: Tests the connection to the Scheduler MCP service and lists its tools.
4. **test_scheduler_auth.py**: Tests authentication with the Scheduler service and JWT token handling.
5. **test_mcp_sdk_integration.py**: Comprehensive test for all MCP servers including the Scheduler.
6. **scheduler_example.py**: Example script demonstrating how to use the SchedulerService wrapper.

## How to Use

### Setup

1. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Update the Scheduler configuration:

   ```
   python scripts/update_scheduler_config.py
   ```

3. Start the Scheduler service:
   ```
   python scripts/start_scheduler.py
   ```

### Testing

1. Test connectivity to the Scheduler service:

   ```
   python scripts/test_scheduler_mcp.py
   ```

2. Test authentication with the Scheduler service:

   ```
   python scripts/test_scheduler_auth.py --client-id your_client_id --api-key your_api_key
   ```

3. Test the full integration with all MCP servers:

   ```
   python scripts/test_mcp_sdk_integration.py
   ```

4. Try the scheduler example:
   ```
   python scripts/scheduler_example.py --schedule --minutes 5
   ```

## Scheduler Service API

The `SchedulerService` wrapper provides the following methods:

1. **initialize()**: Initialize the service and authenticate with the Scheduler
2. **schedule_conversation()**: Schedule a conversation for future delivery
3. **get_conversation_status()**: Get the status of a scheduled conversation
4. **cancel_conversation()**: Cancel a scheduled conversation
5. **close()**: Close the connection to the Scheduler service

## Backward Compatibility

The original MCP implementation is still available for backward compatibility:

- The original client implementation is in `app/host/client.py`
- The original host implementation is in `app/host/host.py`

## Transport Types

The MCP SDK supports the following transport types:

1. **STDIO**: Communication via standard input/output with a subprocess
2. **SSE**: Communication via Server-Sent Events over HTTP
3. **HTTP**: Communication via standard HTTP requests (with JWT authentication support)

## Additional Notes

- The MCP SDK client automatically handles different transport types based on the URL or command provided.
- For HTTP transport with authentication, ensure the client_id and api_key are correctly configured.
- The Scheduler service must be running on port 5146 for the integration to work correctly.

## Environment Variables

For security, you can set these environment variables instead of hardcoding values in config.json:

- `SCHEDULER_CLIENT_ID`: Client ID for Scheduler service authentication
- `SCHEDULER_API_KEY`: API key for Scheduler service authentication

## Troubleshooting

If you encounter issues:

1. Verify the Scheduler service is running:

   ```
   curl http://localhost:5146/mcp/tools
   ```

2. Check authentication credentials:

   ```
   python scripts/test_scheduler_auth.py --client-id your_client_id --api-key your_api_key
   ```

3. Check the logs for detailed error messages.

4. Use the test scripts to diagnose connectivity issues.

5. Ensure all dependencies are properly installed:
   ```
   pip install -r requirements.txt
   ```
