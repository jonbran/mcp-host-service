# MCP Scheduler Integration Guide for AI Agents

## Introduction

The MCP Scheduler Service is a .NET Core service implementing the Model Context Protocol (MCP) for scheduling future conversations. This guide provides comprehensive information for AI agents to integrate with the scheduler service, focusing on practical implementation aspects.

## Table of Contents

1. [Authentication](#authentication)
2. [Integration Patterns](#integration-patterns)
3. [MCP Tool Integration](#mcp-tool-integration)
4. [REST API Integration](#rest-api-integration)
5. [Conversation Lifecycle](#conversation-lifecycle)
6. [Error Handling](#error-handling)
7. [Sample Implementation](#sample-implementation)

## Authentication

### Overview

The MCP Scheduler service uses JWT (JSON Web Token) authentication to secure all endpoints. To access the service, your agent must first obtain a token.

### Authentication Flow

1. **Request a token**:

   ```http
   POST /api/auth/token
   Content-Type: application/json

   {
     "clientId": "your-client-id",
     "apiKey": "your-api-key"
   }
   ```

2. **Response**:

   ```json
   {
     "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "expiresIn": 7200
   }
   ```

3. **Using the token**:

   ```http
   POST /mcp/execute
   Content-Type: application/json
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

   {
     "toolId": "scheduleConversation",
     ...
   }
   ```

### Managing Token Expiration

- Store the token and expiry time in your agent's state
- Check if the token is about to expire before making requests
- Implement token refresh logic (request a new token before expiration)
- Include error handling for authentication failures

## Integration Patterns

There are two primary integration patterns available:

### 1. MCP Tool Integration

Use this approach when your agent implements the Model Context Protocol and wants to integrate through the MCP endpoints.

**Benefits:**

- Native MCP integration
- Standardized tool execution
- Simplified parameter passing

### 2. REST API Integration

Use this approach when your agent doesn't implement MCP or requires direct control of the conversation lifecycle.

**Benefits:**

- More granular control over conversation management
- Direct access to full conversation details
- Standard RESTful interaction

## MCP Tool Integration

### Available Tools

#### 1. scheduleConversation

Schedules a future conversation for delivery.

**Parameters:**

- `conversationText` (string, required): The text content to be sent
- `scheduledTime` (string, required): When the conversation should be delivered (ISO 8601 format)
- `endpoint` (string, required): The endpoint where the conversation should be sent
- `method` (string, optional): The HTTP method to use (default: "POST")
- `additionalInfo` (string, optional): Additional context information

**Returns:** A conversation ID (GUID) as a string

#### 2. getConversationStatus

Retrieves the status of a scheduled conversation.

**Parameters:**

- `conversationId` (string, required): The ID of the conversation to check

**Returns:** Status as string ("Scheduled", "InProgress", "Completed", "Failed", "Cancelled")

#### 3. cancelConversation

Cancels a scheduled conversation.

**Parameters:**

- `conversationId` (string, required): The ID of the conversation to cancel

**Returns:** Boolean indicating success or failure

### MCP Integration Example

```http
# Get MCP tools definition
GET /mcp/tools
Authorization: Bearer {{token}}

# Execute scheduleConversation tool
POST /mcp/execute
Content-Type: application/json
Authorization: Bearer {{token}}

{
  "toolId": "scheduleConversation",
  "toolParameters": {
    "conversationText": "This is a scheduled message",
    "scheduledTime": "2023-05-01T15:00:00Z",
    "endpoint": "https://your-agent-callback-url/api/receive",
    "method": "POST",
    "additionalInfo": "Context information for this conversation"
  }
}

# Response
{
  "toolId": "scheduleConversation",
  "toolResult": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

### State Management for MCP Integration

1. **Store conversation IDs**: Maintain a mapping of conversation IDs to your internal context/session IDs
2. **Track scheduled times**: Store the expected execution time to follow up if needed
3. **Maintain status information**: Periodically check conversation status for important conversations

## REST API Integration

### Core Endpoints

#### 1. Create a Conversation

```http
POST /api/conversations
Content-Type: application/json
Authorization: Bearer {{token}}

{
  "conversationText": "This is a scheduled message",
  "scheduledTime": "2023-05-01T15:00:00Z",
  "target": {
    "endpoint": "https://your-agent-callback-url/api/receive",
    "method": "POST",
    "headers": {
      "X-Api-Key": "your-callback-api-key",
      "Content-Type": "application/json"
    }
  }
}

# Response (201 Created)
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "scheduledTime": "2023-05-01T15:00:00Z",
  "conversationText": "This is a scheduled message",
  "target": {
    "id": "8f7e6d5c-4b3a-2c1d-0e9f-8a7b6c5d4e3f",
    "conversationId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "endpoint": "https://your-agent-callback-url/api/receive",
    "method": "POST",
    "headers": {
      "X-Api-Key": "your-callback-api-key",
      "Content-Type": "application/json"
    },
    "additionalInfo": null
  },
  "createdAt": "2023-04-28T12:30:15Z",
  "updatedAt": "2023-04-28T12:30:15Z",
  "status": "Scheduled"
}
```

#### 2. Get Conversation Status

```http
GET /api/conversations/3fa85f64-5717-4562-b3fc-2c963f66afa6
Authorization: Bearer {{token}}

# Response
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "scheduledTime": "2023-05-01T15:00:00Z",
  "conversationText": "This is a scheduled message",
  "target": {
    "id": "8f7e6d5c-4b3a-2c1d-0e9f-8a7b6c5d4e3f",
    "conversationId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "endpoint": "https://your-agent-callback-url/api/receive",
    "method": "POST",
    "headers": {
      "X-Api-Key": "your-callback-api-key",
      "Content-Type": "application/json"
    },
    "additionalInfo": null
  },
  "createdAt": "2023-04-28T12:30:15Z",
  "updatedAt": "2023-04-28T12:30:15Z",
  "status": "Scheduled"
}
```

#### 3. Cancel Conversation

```http
DELETE /api/conversations/3fa85f64-5717-4562-b3fc-2c963f66afa6
Authorization: Bearer {{token}}

# Response (204 No Content on success)
```

### State Management for REST API Integration

Keep track of the following in your agent's state:

1. **Conversation IDs**: Map these to your internal sessions
2. **Scheduled times**: For follow-up and verification
3. **Current status**: To avoid re-querying frequently
4. **Callback URL info**: Ensure callbacks are properly routed to the right context

## Conversation Lifecycle

Understanding the conversation lifecycle is crucial for effective integration:

1. **Creation**: Initiated by agent with future `scheduledTime`
2. **Scheduling**: System creates Hangfire job for execution
3. **Waiting**: Conversation remains in `Scheduled` status
4. **Execution**: Status changes to `InProgress` when execution time is reached
5. **Completion**: Status becomes:
   - `Completed`: Successful delivery
   - `Failed`: Error in delivery process
   - `Cancelled`: Explicitly cancelled before execution

### Status Transitions

```
[Creation] -> Scheduled -> InProgress -> Completed
                      |              \-> Failed
                      \-> Cancelled
```

## Error Handling

### Common Error Scenarios

1. **Authentication Failures**

   - Invalid API key or client ID
   - Expired JWT token
   - Missing Authorization header

   **Solution**: Implement token refresh and retry logic

2. **Validation Errors**

   - `scheduledTime` in the past
   - Missing required parameters
   - Invalid conversation ID format

   **Solution**: Validate inputs before sending and handle 400 responses

3. **Execution Failures**

   - Target endpoint unreachable
   - Target endpoint returns error
   - Invalid request format

   **Solution**: Implement callback endpoint error handling

4. **Service Availability**

   - Service temporarily unavailable
   - Database connectivity issues
   - Rate limiting

   **Solution**: Implement exponential backoff retry logic

### Retry Strategy

Implement a graduated retry strategy:

1. Initial retry after 1 second
2. Second retry after 5 seconds
3. Third retry after 15 seconds
4. Final retry after 30 seconds

For critical messages, consider setting up a monitoring process to check conversation status after the scheduled time.

## Callback Handling

When the MCP Scheduler executes a conversation, it will send the scheduled message to the specified endpoint using the specified method. Your agent needs to implement an endpoint to handle these callbacks.

### Callback Endpoint Implementation

1. Authenticate incoming requests if needed
2. Parse the received conversation text
3. Process based on additionalInfo context
4. Return success (2xx) status to indicate proper receipt

### Sample Callback Endpoint (Pseudocode)

```javascript
app.post("/api/receive", (req, res) => {
  // Authenticate if needed
  const apiKey = req.headers["x-api-key"];
  if (!validateApiKey(apiKey)) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  // Process the conversation
  const conversationText = req.body;

  // Execute your agent's logic here
  // ...

  // Return success
  return res.status(200).json({ status: "received" });
});
```

## Sample Implementation

### Complete MCP Integration Flow

The following code demonstrates a complete implementation for an AI agent integrating with the MCP Scheduler service:

```javascript
class McpSchedulerClient {
  constructor(baseUrl, clientId, apiKey) {
    this.baseUrl = baseUrl;
    this.clientId = clientId;
    this.apiKey = apiKey;
    this.token = null;
    this.tokenExpiry = null;
  }

  // Authenticate and get token
  async authenticate() {
    if (this.token && this.tokenExpiry > Date.now()) {
      return this.token; // Use existing token
    }

    const response = await fetch(`${this.baseUrl}/api/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        clientId: this.clientId,
        apiKey: this.apiKey,
      }),
    });

    if (!response.ok) {
      throw new Error(`Authentication failed: ${response.statusText}`);
    }

    const data = await response.json();
    this.token = data.token;
    this.tokenExpiry = Date.now() + data.expiresIn * 1000 - 60000; // Buffer of 1 minute
    return this.token;
  }

  // Execute MCP tool
  async executeTool(toolId, parameters) {
    const token = await this.authenticate();

    const response = await fetch(`${this.baseUrl}/mcp/execute`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        toolId,
        toolParameters: parameters,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Tool execution failed: ${response.statusText} - ${errorText}`
      );
    }

    return response.json();
  }

  // Schedule a conversation
  async scheduleConversation(
    text,
    scheduledTime,
    endpoint,
    method = "POST",
    additionalInfo = null
  ) {
    const result = await this.executeTool("scheduleConversation", {
      conversationText: text,
      scheduledTime: scheduledTime.toISOString(),
      endpoint,
      method,
      additionalInfo,
    });

    return result.toolResult; // This is the conversation ID
  }

  // Get conversation status
  async getConversationStatus(conversationId) {
    const result = await this.executeTool("getConversationStatus", {
      conversationId,
    });

    return result.toolResult; // This is the status string
  }

  // Cancel conversation
  async cancelConversation(conversationId) {
    const result = await this.executeTool("cancelConversation", {
      conversationId,
    });

    return result.toolResult; // This is a boolean success value
  }
}

// Usage example
async function scheduleFollowUp(userId, reminderText) {
  const client = new McpSchedulerClient(
    "https://scheduler-api.example.com",
    "ai-agent-client",
    "your-api-key-here"
  );

  try {
    // Schedule for 24 hours in the future
    const scheduledTime = new Date();
    scheduledTime.setHours(scheduledTime.getHours() + 24);

    const conversationId = await client.scheduleConversation(
      reminderText,
      scheduledTime,
      `https://your-agent-api.example.com/callback/${userId}`,
      "POST",
      JSON.stringify({ userId, contextType: "reminder" })
    );

    console.log(
      `Scheduled conversation ${conversationId} for ${scheduledTime}`
    );

    // Store the conversation ID for future reference
    saveToUserState(userId, {
      reminderConversationId: conversationId,
      scheduledTime: scheduledTime.toISOString(),
    });

    return conversationId;
  } catch (error) {
    console.error("Failed to schedule conversation:", error);
    // Implement retry logic or fallback
    return null;
  }
}
```

### Callback Handler Implementation

```javascript
// Express.js example of a callback handler

app.post("/callback/:userId", async (req, res) => {
  try {
    const { userId } = req.params;
    const conversationText = req.body;

    // Get user state
    const userState = getUserState(userId);

    // Process the conversation
    await processReminderCallback(userId, conversationText, userState);

    // Acknowledge receipt
    res.status(200).json({ success: true });
  } catch (error) {
    console.error("Error processing callback:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

async function processReminderCallback(userId, text, state) {
  // Your agent's logic for handling the reminder
  // ...

  // Clear the reminder from state
  clearReminderFromState(userId);

  // Log completion
  console.log(`Processed reminder for user ${userId}: ${text}`);
}
```

## Implementation Considerations

### Minimal State Requirements

At minimum, your agent should store:

1. **Authentication token**: JWT token for making requests
2. **Token expiry**: When the token needs to be refreshed
3. **Conversation mapping**: Link conversation IDs to your agent's context

### Performance Optimization

1. **Batch scheduling**: For multiple reminders at similar times
2. **Status polling**: Only check status when necessary, not constantly
3. **Token management**: Cache token until near expiry

### Security Best Practices

1. **Secure API keys**: Never expose client ID or API key in client-side code
2. **Validate callbacks**: Implement signature verification for callbacks
3. **Use HTTPS**: Always use secure connections for all communication
4. **Implement rate limiting**: On your callback endpoint to prevent abuse

### Monitoring and Debugging

1. Track all scheduled conversations in your logs
2. Add correlation IDs to link your internal processes with MCP conversation IDs
3. Implement logging for all API interactions and callbacks
4. Track status transitions to detect anomalies

## Conclusion

The MCP Scheduler service provides a robust and flexible way for AI agents to schedule future conversations. By following this guide, you can implement a reliable integration that handles the complete conversation lifecycle, manages state appropriately, and implements proper error handling.

For any questions or issues with integration, please contact the service administrators or refer to the API documentation available at the `/swagger` endpoint of the service.
