# MCP Host Service Requirements Specification

## Overview

The MCP Host Service is a flexible, provider-based system for hosting language models with Model Context Protocol (MCP) capabilities. It serves as an intermediary between users and various MCP servers, allowing models to interact with external data sources and tools through standardized protocols.

## System Architecture

### High-Level Architecture

```
┌─────────────┐       ┌───────────────┐      ┌────────────────┐
│             │       │               │      │   Model        │
│  REST API   │ <──── │   MCP Host    │ <────│   Providers:   │
│  Service    │       │               │      │ • HuggingFace  │
│             │       │               │      │ • OpenAI       │
└─────────────┘       └───────────────┘      │ • Anthropic    │
       ^                      ^              └────────────────┘
       │                      │
       v                      v
┌─────────────┐       ┌───────────────┐
│             │       │               │
│ Conversation│       │   MCP Client  │
│    Store    │       │               │
│             │       └───────────────┘
└─────────────┘               │
                              v
                      ┌───────────────┐
                      │  MCP Servers  │
                      │ (External)    │
                      │               │
                      └───────────────┘
```

### Core Components

1. **REST API Service**: Exposes endpoints for client interaction with the system
2. **MCP Host**: Manages the language model and coordinates with MCP servers
3. **Model Providers**: Abstracts different model implementations (HuggingFace, OpenAI, Anthropic)
4. **MCP Client**: Communicates with external MCP servers
5. **Conversation Store**: Persists conversation history
6. **Configuration Manager**: Handles system configuration

## Detailed Requirements

### 1. Model Provider Architecture

#### 1.1 Base Provider Interface

The system must implement a base abstract class for all model providers with these methods:
- `initialize()`: Set up the provider's resources
- `generate_response(messages)`: Generate text responses from conversation history

#### 1.2 Provider Implementations

The system must include these provider implementations:

##### 1.2.1 HuggingFace Provider
- **Purpose**: Local inference with HuggingFace models
- **Requirements**:
  - Support for different model formats (DeepSeek, LLaMA, generic)
  - Local model loading with GPU acceleration when available
  - Model optimization for improved performance
  - Customizable inference parameters (temperature, top_p)

##### 1.2.2 OpenAI Provider
- **Purpose**: Remote inference via OpenAI's API
- **Requirements**:
  - Support for OpenAI models (GPT family)
  - Support for Azure OpenAI deployments
  - Authentication via API keys
  - Error handling for API failures
  - Message format conversion for OpenAI expectations

##### 1.2.3 Anthropic Provider
- **Purpose**: Remote inference via Anthropic's API
- **Requirements**:
  - Support for Claude model family
  - Authentication via API keys
  - Error handling for API failures
  - Message format conversion for Anthropic expectations

#### 1.3 Provider Factory

The system must include a factory function that instantiates the appropriate provider based on configuration.

### 2. Model Service

The model service must serve as a facade for all provider implementations:

- **Initialization**: Set up the appropriate provider based on configuration
- **Response Generation**: Delegate to the provider for generating responses
- **Environment Integration**: Support environment variable configuration for API keys

### 3. REST API

The API must expose these endpoints:

#### 3.1 Conversation Management
- `POST /conversations`: Create a new conversation
- `GET /conversations/{id}`: Retrieve a conversation by ID
- `DELETE /conversations/{id}`: Delete a conversation
- `POST /conversations/{id}/messages`: Add a message to a conversation

#### 3.2 Health Checks
- `GET /health`: Basic health check endpoint

#### 3.3 API Models
The API must define data models for all requests and responses, including:
- Conversation models
- Message models
- Error responses

### 4. MCP Integration

#### 4.1 MCP Host
- Orchestrate interactions between users, models, and MCP servers
- Extract MCP requests from model outputs
- Route MCP requests to appropriate servers
- Integrate MCP server responses into the conversation

#### 4.2 MCP Client
- Support multiple transport protocols:
  - Standard I/O (stdio) for local servers
  - Server-Sent Events (SSE) for remote servers
- Manage connections to multiple MCP servers
- Handle connection/disconnection gracefully

### 5. Conversation Persistence

- Store conversations in a file-based system
- Support CRUD operations for conversations
- Maintain conversation history for context

### 6. Configuration

#### 6.1 Structure
The configuration system must support:

```json
{
  "mcp": {
    "mcp_servers": [
      {
        "name": "ServerName",
        "transport": {
          "type": "stdio|sse",
          "command": "command_for_stdio",
          "args": ["arg1", "arg2"],
          "url": "url_for_sse"
        }
      }
    ]
  },
  "model": {
    "provider": "huggingface|openai|anthropic",
    "model_id": "model_identifier",
    "max_sequence_length": 1024,
    "temperature": 0.7,
    "top_p": 0.9,
    "batch_size": 1,
    "device": "cpu|cuda",
    "optimize": true,
    "api_key": "api_key_or_null",
    "api_base": "api_base_url_or_null"
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8000,
    "timeout": 60,
    "max_request_size": 1048576,
    "default_format": "json",
    "rate_limit_enabled": false,
    "rate_limit": 100
  },
  "data_dir": "./data"
}
```

#### 6.2 Configuration Enums
The system must define enums for:
- Transport types (stdio, sse)
- Provider types (huggingface, openai, anthropic)

### 7. Authentication & Security

- Basic authentication support for API endpoints
- User management with simple file-based storage
- Environment variable integration for sensitive values

## Implementation Requirements

### 1. Project Structure

```
mcp_service/
├── app/
│   ├── api/                # REST API implementation
│   │   ├── __init__.py
│   │   ├── models.py       # API data models
│   │   └── router.py       # FastAPI router
│   ├── auth/               # Authentication
│   │   ├── __init__.py
│   │   ├── models.py       # User models
│   │   ├── router.py       # Auth routes
│   │   ├── store.py        # User storage
│   │   └── utils.py        # Auth utilities
│   ├── config/             # Configuration management
│   │   ├── __init__.py
│   │   └── config.py       # Config models and utils
│   ├── host/               # MCP Host implementation
│   │   ├── __init__.py
│   │   ├── client.py       # MCP client
│   │   └── host.py         # MCP host
│   ├── model/              # Model integration
│   │   ├── __init__.py
│   │   ├── model.py        # Model service
│   │   └── provider.py     # Model providers
│   ├── persistence/        # Conversation storage
│   │   ├── __init__.py
│   │   └── conversation.py # Conversation store
│   ├── utils/              # Utility functions
│   │   ├── __init__.py
│   │   ├── cache.py        # Caching utilities
│   │   ├── env.py          # Environment utilities
│   │   ├── mcp.py          # MCP utilities
│   │   └── model_mcp.py    # Model-MCP integration
│   ├── __init__.py
│   └── main.py             # FastAPI application
├── config/                 # Configuration files
│   ├── config.json         # Main configuration
│   └── example_configs.json # Configuration examples
├── data/                   # Data storage
│   ├── conversations/      # Conversation storage
│   └── users.json          # User storage
├── scripts/                # Utility scripts
│   ├── configure_mcp_servers.py
│   ├── search_server.py
│   ├── test_api.py
│   ├── test_providers.py   # Provider testing
│   └── webscraper_server.py
├── tests/                  # Test suite
│   ├── __init__.py
│   └── test_config.py
├── DEVELOPMENT.md          # Development guide
├── Dockerfile              # Docker configuration
├── pyproject.toml          # Dependencies
├── README.md               # Documentation
└── requirements.md         # This requirements document
```

### 2. Technology Stack

- **Python**: 3.10+
- **Web Framework**: FastAPI
- **Dependency Management**: UV (as an alternative to pip)
- **Model Integration**:
  - HuggingFace Transformers
  - OpenAI API (via httpx)
  - Anthropic API (via httpx)
- **Container Support**: Docker

### 3. Provider Implementation Details

#### 3.1 HuggingFace Provider

- **Class**: `HuggingFaceProvider`
- **Methods**:
  - `initialize()`: Load model and tokenizer
  - `generate_response()`: Generate text using local model
  - `_format_conversation()`: Format messages for model
  - Format-specific methods for different model families:
    - `_format_deepseek_conversation()`
    - `_format_llama_conversation()`
    - `_format_generic_conversation()`

#### 3.2 OpenAI Provider

- **Class**: `OpenAIProvider`
- **Methods**:
  - `initialize()`: Set up API client
  - `generate_response()`: Call OpenAI's API for generation
- **Configuration**:
  - `api_key`: OpenAI API key
  - `api_base`: API endpoint (default or Azure)

#### 3.3 Anthropic Provider

- **Class**: `AnthropicProvider`
- **Methods**:
  - `initialize()`: Set up API client
  - `generate_response()`: Call Anthropic's API for generation
- **Configuration**:
  - `api_key`: Anthropic API key
  - `anthropic_version`: API version header

### 4. MCP Host Implementation

- **Initialization**: Set up services and MCP servers
- **Message Processing**: Extract MCP requests from messages
- **MCP Request Fulfillment**: Route requests to appropriate servers
- **Response Generation**: Combine model and MCP responses

### 5. Environment Variables

The system must support these environment variables:
- `OPENAI_API_KEY`: For OpenAI authentication
- `ANTHROPIC_API_KEY`: For Anthropic authentication
- `OPENAI_API_BASE`: For custom OpenAI endpoints
- `USE_GPU`: Flag to enable GPU acceleration

## Testing Requirements

### 1. Provider Testing

The system must include a test script (`test_providers.py`) that:
- Tests each provider independently
- Verifies initialization and response generation
- Handles cases with/without API keys

### 2. API Testing

Test scripts must verify:
- Conversation creation, retrieval, and deletion
- Message addition and response generation
- Error handling

### 3. MCP Testing

Tests must verify:
- MCP server connections
- Request extraction and routing
- Response integration

## Deployment Requirements

### 1. Docker Support

- Dockerfile for containerization
- Support for CPU and GPU configurations
- Environment variable injection

### 2. Scalability Considerations

- Stateless API design for horizontal scaling
- Configurable timeouts for long-running operations
- Performance optimization options

## Documentation Requirements

### 1. README.md

Basic documentation covering:
- System overview
- Installation instructions
- Usage examples
- Configuration guidance

### 2. DEVELOPMENT.md

Developer documentation covering:
- Project structure
- Adding new providers
- Extending MCP capabilities
- Docker deployment

### 3. API Documentation

Generated from FastAPI's automatic documentation system, covering:
- Endpoint descriptions
- Request/response models
- Authentication requirements

## Appendix: Example Configurations

### HuggingFace Configuration

```json
{
  "provider": "huggingface",
  "model_id": "deepseek-ai/DeepSeek-R1",
  "max_sequence_length": 4096,
  "temperature": 0.7,
  "top_p": 0.9,
  "batch_size": 1,
  "device": "cuda",
  "optimize": true
}
```

### OpenAI Configuration

```json
{
  "provider": "openai",
  "model_id": "gpt-4-turbo",
  "max_sequence_length": 4096,
  "temperature": 0.7,
  "top_p": 0.9,
  "api_key": "your_openai_api_key_here",
  "api_base": "https://api.openai.com/v1"
}
```

### Azure OpenAI Configuration

```json
{
  "provider": "openai",
  "model_id": "your-deployed-model-name",
  "max_sequence_length": 4096,
  "temperature": 0.7,
  "top_p": 0.9,
  "api_key": "your_azure_openai_api_key_here",
  "api_base": "https://your-resource-name.openai.azure.com/openai/deployments/your-deployed-model-name"
}
```

### Anthropic Configuration

```json
{
  "provider": "anthropic",
  "model_id": "claude-3-opus-20240229",
  "max_sequence_length": 4096,
  "temperature": 0.7,
  "top_p": 0.9,
  "api_key": "your_anthropic_api_key_here"
}
```
