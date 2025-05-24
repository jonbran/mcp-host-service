# MCP Host UI Client Integration Guide

## Overview

This document provides detailed requirements and guidelines for developing a UI client application that connects to the MCP Host service. The MCP Host service provides access to language models with Model Context Protocol (MCP) capabilities, allowing integration with various AI models including HuggingFace, OpenAI, and Anthropic.

## UI Client Architecture

The UI client should follow a modern frontend architecture that communicates with the MCP Host service via its REST API. The following diagram illustrates the high-level architecture:

```
┌───────────────────────────────────────────────────────────┐
│                       UI Client                           │
│                                                           │
│  ┌─────────────┐    ┌───────────────┐    ┌─────────────┐  │
│  │             │    │               │    │             │  │
│  │  Auth       │    │ Conversation  │    │  Settings   │  │
│  │  Management │    │ Interface     │    │  Management │  │
│  │             │    │               │    │             │  │
│  └─────────────┘    └───────────────┘    └─────────────┘  │
│         │                  │                   │          │
│         └──────────────────┼───────────────────┘          │
│                            │                              │
│                     ┌──────────────┐                      │
│                     │              │                      │
│                     │   API Layer  │                      │
│                     │              │                      │
│                     └──────────────┘                      │
└──────────────────────────┬────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                                                          │
│                     MCP Host Service                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## API Integration

### Base URL and Configuration

The UI client should allow configuration of the MCP Host service URL and authentication settings. Default settings should be:

```
Base URL: http://localhost:8000
API Prefix: /
```

### Authentication

The MCP Host service uses OAuth2 Password flow for authentication. The UI client should implement:

1. Login screen with username and password fields
2. Token storage and management
3. Token refresh mechanism
4. Logout functionality

#### Authentication Endpoints

| Endpoint          | Method | Description            |
| ----------------- | ------ | ---------------------- |
| `/api/auth/token` | POST   | Obtain an access token |

#### Authentication Flow

1. Collect username and password from the user
2. Make a POST request to `/api/auth/token` with form data:
   - grant_type: "password"
   - username: user's username
   - password: user's password
3. Store the returned access token securely
4. Include the token in all API requests using the Authorization header:
   - `Authorization: Bearer {access_token}`

#### Example Authentication Request

```
POST /api/auth/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

grant_type=password&username=user@example.com&password=userpassword
```

#### Example Authentication Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Conversation Management

The UI client should provide a complete interface for managing conversations with the MCP Host service, including creating, retrieving, sending messages, and deleting conversations.

#### Conversation Endpoints

| Endpoint                                    | Method | Description                     |
| ------------------------------------------- | ------ | ------------------------------- |
| `/conversations`                            | POST   | Create a new conversation       |
| `/conversations`                            | GET    | List existing conversations     |
| `/conversations/{conversation_id}`          | GET    | Get a specific conversation     |
| `/conversations/{conversation_id}/messages` | POST   | Add a message to a conversation |
| `/conversations/{conversation_id}`          | DELETE | Delete a conversation           |

#### Creating a New Conversation

The UI should provide a way to start a new conversation, optionally with an initial message.

**Request:**

```json
POST /conversations HTTP/1.1
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "message": "Hello, how can you help me today?"
}
```

**Response:**

```json
{
  "conversation_id": "6bc898b1-4c08-469e-8e33-25a1db2d1729",
  "message": "I'm an AI assistant that can help you with various tasks. How can I assist you today?"
}
```

#### Listing Conversations

The UI should display a list of existing conversations with pagination support.

**Request:**

```
GET /conversations?limit=20&offset=0 HTTP/1.1
Authorization: Bearer {access_token}
```

**Response:**

```json
{
  "conversations": [
    {
      "id": "6bc898b1-4c08-469e-8e33-25a1db2d1729",
      "created_at": "2025-05-15T14:30:45Z",
      "updated_at": "2025-05-15T14:35:22Z",
      "message_count": 5
    },
    {
      "id": "72f87e2a-8573-4242-adda-3da48a792057",
      "created_at": "2025-05-14T09:12:33Z",
      "updated_at": "2025-05-14T09:20:11Z",
      "message_count": 8
    }
  ]
}
```

#### Retrieving a Conversation

The UI should allow users to view the full history of a conversation.

**Request:**

```
GET /conversations/6bc898b1-4c08-469e-8e33-25a1db2d1729 HTTP/1.1
Authorization: Bearer {access_token}
```

**Response:**

```json
{
  "id": "6bc898b1-4c08-469e-8e33-25a1db2d1729",
  "messages": [
    {
      "role": "user",
      "content": "Hello, how can you help me today?",
      "timestamp": "2025-05-15T14:30:45Z"
    },
    {
      "role": "assistant",
      "content": "I'm an AI assistant that can help you with various tasks. How can I assist you today?",
      "timestamp": "2025-05-15T14:30:48Z"
    }
  ],
  "created_at": "2025-05-15T14:30:45Z",
  "updated_at": "2025-05-15T14:30:48Z"
}
```

#### Adding a Message to a Conversation

The UI should provide a message input field and send button for adding messages to a conversation.

**Request:**

```json
POST /conversations/6bc898b1-4c08-469e-8e33-25a1db2d1729/messages HTTP/1.1
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "message": "Can you help me find information about machine learning?"
}
```

**Response:**

```json
{
  "conversation_id": "6bc898b1-4c08-469e-8e33-25a1db2d1729",
  "message": "Of course! Machine learning is a branch of artificial intelligence..."
}
```

#### Deleting a Conversation

The UI should provide a way to delete conversations.

**Request:**

```
DELETE /conversations/6bc898b1-4c08-469e-8e33-25a1db2d1729 HTTP/1.1
Authorization: Bearer {access_token}
```

**Response:**

```json
{
  "success": true,
  "message": "Conversation 6bc898b1-4c08-469e-8e33-25a1db2d1729 deleted successfully"
}
```

### Health Check

The UI client should implement a health check feature to verify the MCP Host service is available.

**Request:**

```
GET /health HTTP/1.1
```

**Response:**

```json
{
  "status": "ok"
}
```

### Playwright MCP Server Integration

The UI client should support integration with the Playwright MCP server for web automation capabilities. This integration enables users to perform web-based tasks directly through the UI.

#### Playwright Endpoint

| Endpoint          | Method | Description                                |
| ----------------- | ------ | ------------------------------------------ |
| `/api/playwright` | POST   | Send requests to the Playwright MCP server |

#### Playwright Modes

The client should be aware that the Playwright MCP server can operate in two modes:

- **Snapshot Mode (Default)**: For one-off, stateless interactions with web pages
- **Vision Mode**: For interactive, stateful browser automation sequences

#### Example Playwright API Request

**Screenshot in Snapshot Mode:**

```json
POST /api/playwright HTTP/1.1
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "type": "tool",
  "name": "screenshot",
  "params": {
    "url": "https://example.com",
    "output_path": "example_screenshot.png"
  }
}
```

**Browser Automation in Vision Mode:**

```json
POST /api/playwright HTTP/1.1
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "type": "tool",
  "name": "launch_browser",
  "params": {
    "headless": false
  }
}
```

#### UI Elements for Playwright Integration

The UI client should include:

1. **Web Automation Panel**:

   - Controls to take screenshots of URLs
   - Form extraction capabilities
   - Browser automation options (when in Vision mode)

2. **Screenshot Display**:

   - Ability to display screenshots taken by Playwright
   - Option to download screenshots

3. **Web Data Visualization**:
   - Display extracted text, links, or other web content
   - Formatting for different types of extracted content

### Default Provider and Model Selection

The UI client must support displaying and selecting the default provider and model. The following requirements should be implemented:

1. **Default Provider Display**:

   - Display the name of the default provider (e.g., "Anthropic Claude Sonnet 4") in the settings or dashboard.

2. **Provider Info Retrieval**:

   - Fetch and display detailed information about the default provider, including `provider_type` and `model_id`.

3. **Conversation Default Provider**:

   - Ensure that conversations created without specifying a provider use the default provider.
   - Display the provider used for each conversation in the conversation history.

4. **Error Handling**:
   - Display user-friendly error messages if the default provider is unavailable or misconfigured.

#### Example Default Provider API Response

```json
{
  "default_provider": "anthropic",
  "providers": [
    {
      "name": "anthropic",
      "provider_type": "anthropic",
      "model_id": "claude-sonnet-4-20250514"
    },
    {
      "name": "openai",
      "provider_type": "openai",
      "model_id": "gpt-4o-mini"
    },
    {
      "name": "Playwright",
      "is_mcp_server": true
    },
    {
      "name": "WebScraper",
      "is_mcp_server": true
    },
    {
      "name": "SearchEngine",
      "is_mcp_server": true
    }
  ]
}
```

## UI Components and Features

### Required Components

1. **Login Screen**

   - Username and password fields
   - Login button
   - Error messaging for failed login attempts

2. **Conversation List**

   - List of existing conversations with timestamps
   - Preview of the last message
   - Create new conversation button
   - Delete conversation option
   - Pagination controls

3. **Conversation View**

   - Message history display
   - Clear visual distinction between user and assistant messages
   - Message timestamp display
   - Auto-scrolling to the latest message
   - Message input field
   - Send button

4. **Settings Panel**
   - Service URL configuration
   - Theme settings (light/dark mode)
   - Optional: Model selection if supported by the server

### Optional Advanced Features

1. **Typing Indicators**

   - Display a typing indicator while waiting for the assistant's response

2. **Message Formatting**

   - Support for Markdown rendering in messages
   - Code syntax highlighting
   - Support for displaying images if the model provides image URLs

3. **MCP Capability Visualization**

   - Visual indication when the model is using MCP features
   - Display of which MCP servers are being used
   - Show Playwright actions and results when the Playwright MCP server is used

4. **Playwright Integration Features**

   - Interactive web browsing interface for Vision mode
   - Screenshot viewer for displaying captured web pages
   - Web content extraction visualization
   - Visual feedback for browser automation actions

5. **Export Functionality**
   - Option to export conversations as text or JSON
   - Ability to export screenshots and extracted web content

## Error Handling

The UI client should implement comprehensive error handling for all API interactions:

### Common Error Scenarios

1. **Authentication Errors**

   - Invalid credentials
   - Expired tokens
   - Unauthorized access

2. **Network Errors**

   - Service unavailable
   - Request timeout
   - Connection issues

3. **Application Errors**
   - Invalid requests
   - Server-side errors
   - Resource not found

### Error Response Format

The MCP Host service returns errors in this format:

```json
{
  "detail": "Error message describing the issue"
}
```

The UI should parse and display these error messages appropriately.

## Response Time Considerations

The MCP Host service may take time to process messages, especially when using complex models or MCP servers. The UI should:

1. Display loading indicators during requests
2. Implement timeouts with appropriate retry logic
3. Provide feedback to users during long-running operations

## Multi-Provider Support

The MCP Host supports multiple model providers (HuggingFace, OpenAI, Anthropic) and MCP servers (Playwright, WebScraper, SearchEngine). If the server configuration exposes provider selection to clients, the UI should:

1. Display available provider options including both model providers and MCP servers
2. Allow switching between providers
3. Adapt the interface based on provider capabilities
4. Show appropriate UI elements for interacting with MCP servers

## Implementation Guidelines

### Recommended Technologies

- **Frontend Framework**: React, Vue.js, or Angular
- **State Management**: Redux, Vuex, or Context API
- **HTTP Client**: Axios or Fetch API
- **UI Components**: Material-UI, Ant Design, or Bootstrap
- **Authentication**: JWT handling library

### Security Considerations

1. Store authentication tokens securely:

   - Use HTTP-only cookies or secure storage mechanisms
   - Clear tokens on logout

2. Implement CSRF protection where applicable

3. Validate all user inputs

4. Implement proper error handling without exposing sensitive information

### Performance Optimization

1. Implement pagination for conversation lists
2. Lazy load conversation history
3. Optimize rendering of long conversations
4. Use virtualized lists for better performance with large message histories

## Example Code Snippets

### Authentication Service

```javascript
class AuthService {
  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append("grant_type", "password");
    formData.append("username", username);
    formData.append("password", password);

    const response = await fetch("http://localhost:8000/api/auth/token", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Authentication failed");
    }

    const data = await response.json();
    localStorage.setItem("access_token", data.access_token);
    return data;
  }

  logout() {
    localStorage.removeItem("access_token");
  }

  getToken() {
    return localStorage.getItem("access_token");
  }

  isAuthenticated() {
    return !!this.getToken();
  }
}
```

### Conversation Service

```javascript
class ConversationService {
  constructor() {
    this.baseUrl = "http://localhost:8000";
    this.authService = new AuthService();
  }

  async getHeaders() {
    const token = this.authService.getToken();
    return {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  }

  async createConversation(initialMessage = null) {
    const headers = await this.getHeaders();
    const body = initialMessage
      ? JSON.stringify({ message: initialMessage })
      : "{}";

    const response = await fetch(`${this.baseUrl}/conversations`, {
      method: "POST",
      headers,
      body,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to create conversation");
    }

    return response.json();
  }

  async getConversations(limit = 20, offset = 0) {
    const headers = await this.getHeaders();

    const response = await fetch(
      `${this.baseUrl}/conversations?limit=${limit}&offset=${offset}`,
      {
        method: "GET",
        headers,
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to get conversations");
    }

    return response.json();
  }

  async getConversation(conversationId) {
    const headers = await this.getHeaders();

    const response = await fetch(
      `${this.baseUrl}/conversations/${conversationId}`,
      {
        method: "GET",
        headers,
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to get conversation");
    }

    return response.json();
  }

  async sendMessage(conversationId, message) {
    const headers = await this.getHeaders();

    const response = await fetch(
      `${this.baseUrl}/conversations/${conversationId}/messages`,
      {
        method: "POST",
        headers,
        body: JSON.stringify({ message }),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to send message");
    }

    return response.json();
  }

  async deleteConversation(conversationId) {
    const headers = await this.getHeaders();

    const response = await fetch(
      `${this.baseUrl}/conversations/${conversationId}`,
      {
        method: "DELETE",
        headers,
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to delete conversation");
    }

    return response.json();
  }
}
```

### Playwright Service

```javascript
class PlaywrightService {
  constructor() {
    this.baseUrl = "http://localhost:8000";
    this.authService = new AuthService();
  }

  async getHeaders() {
    const token = this.authService.getToken();
    return {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  }

  async takeScreenshot(url, outputPath) {
    const headers = await this.getHeaders();

    const request = {
      type: "tool",
      name: "screenshot",
      params: {
        url,
        output_path: outputPath,
      },
    };

    const response = await fetch(`${this.baseUrl}/api/playwright`, {
      method: "POST",
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to take screenshot");
    }

    return response.json();
  }

  async extractText(url, selector = null) {
    const headers = await this.getHeaders();

    const request = {
      type: "tool",
      name: "extract_text",
      params: {
        url,
        ...(selector && { selector }),
      },
    };

    const response = await fetch(`${this.baseUrl}/api/playwright`, {
      method: "POST",
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to extract text");
    }

    return response.json();
  }

  async launchBrowser(headless = true) {
    const headers = await this.getHeaders();

    const request = {
      type: "tool",
      name: "launch_browser",
      params: {
        headless,
      },
    };

    const response = await fetch(`${this.baseUrl}/api/playwright`, {
      method: "POST",
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to launch browser");
    }

    return response.json();
  }

  async navigate(url) {
    const headers = await this.getHeaders();

    const request = {
      type: "tool",
      name: "navigate",
      params: {
        url,
      },
    };

    const response = await fetch(`${this.baseUrl}/api/playwright`, {
      method: "POST",
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to navigate");
    }

    return response.json();
  }

  async closeBrowser() {
    const headers = await this.getHeaders();

    const request = {
      type: "tool",
      name: "close_browser",
      params: {},
    };

    const response = await fetch(`${this.baseUrl}/api/playwright`, {
      method: "POST",
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to close browser");
    }

    return response.json();
  }
}
```

## Testing Requirements

The UI client should include comprehensive testing:

1. **Unit Tests**: Test individual components and services
2. **Integration Tests**: Test API integration with mock servers
3. **End-to-End Tests**: Test the full application flow

## Deployment Considerations

1. **Environment Configuration**:

   - Support for different environments (development, staging, production)
   - Configuration of API endpoints based on environment

2. **Build Process**:

   - Minification and bundling for production
   - Environment-specific builds

3. **Containerization** (optional):
   - Docker support for consistent deployment

## Conclusion

This document provides the requirements and guidelines for developing a UI client for the MCP Host service. By following these specifications, developers can create a robust and user-friendly interface that leverages the full capabilities of the MCP Host service and its model providers.
