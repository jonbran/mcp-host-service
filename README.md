# MCP Host/Client/Service

## Overview

This project implements an MCP (Model Context Protocol) Host/Client/Service that hosts a Hugging Face model. It provides an intermediary between users and various MCP servers, allowing the model to interact with external data sources and tools through the standardized MCP protocol.

## Features

- Host models from multiple providers as an MCP Host:
  - Hugging Face models (local inference)
  - OpenAI API models (including Azure OpenAI)
  - Anthropic API models
- Connect to configured MCP Servers to extend the model's capabilities:
  - WebScraper: Extract text and data from websites
  - SearchEngine: Perform web searches for information retrieval
  - Scheduler: Schedule conversations for future delivery
- Uses the official MCP Python SDK for standardized integration
- Support for multiple transport types (STDIO, SSE, HTTP)
- Authentication support for secure MCP server connections
- Provide a REST API for users to interact with the model
- Support conversation persistence for continued interactions
- Docker support for containerization

## Architecture

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
                      ┌───────────────────────┐
                      │     MCP Servers:      │
                      │ • WebScraper          │
                      │ • SearchEngine        │
                      │ • Scheduler           │
                      └───────────────────────┘
```

## Components

### MCP Host

The MCP Host manages the model and determines when to use MCP Servers for additional capabilities. It orchestrates the flow of information between the user, model, and MCP Servers. The host now uses the official MCP Python SDK for standardized integration.

### MCP Client

The MCP Client establishes and maintains connections to configured MCP Servers. It supports both stdio and SSE transport protocols for flexible integration with different server types.

### MCP Servers

The system integrates with several MCP servers that provide specialized functionalities:

1. **WebScraper**: Scrapes and extracts content from web pages.
2. **SearchEngine**: Performs web searches to provide up-to-date information.
3. **Scheduler**: Manages scheduling of conversations for future delivery.

### Model Integration

The service integrates with multiple model providers:

1. **HuggingFace Models**: Local inference with models like DeepSeek that demonstrate strong reasoning capabilities.
2. **OpenAI API Models**: Access to OpenAI's powerful models like GPT-4 through their API service.
3. **Anthropic API Models**: Integration with Anthropic's Claude models through their API.

The implementation uses a provider-based architecture that handles model initialization, formatting, and response generation appropriately for each provider type.

### Conversation Persistence

The service maintains conversation history for context continuation. Conversations are stored in a file-based system with support for basic CRUD operations.

### REST API

The API provides endpoints for creating conversations, adding messages, retrieving conversation history, and managing conversations. All interactions with the model and MCP servers are accessible through these endpoints.

## Installation

### Prerequisites

- Python 3.10+
- UV from Astral (used instead of pip)
- Docker (for containerization)

### Setup with UV

```bash
# Install UV
curl -sSf https://astral.sh/uv/install.sh | bash

# Clone the repository
git clone <repository-url>
cd mcp_service

# Create and activate a virtual environment
uv venv

# Install dependencies
uv pip install -e .
```

### Setup with Docker

```bash
# Build the Docker image
docker build -t mcp-service .

# Run the container
docker run -p 8000:8000 mcp-service
```

## Usage

### Configuration

Configure the MCP Servers and model settings in the `config` directory. Example configuration files are provided.

### Running the Service

```bash
# Start the service
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API Endpoints

- `POST /api/conversations` - Create a new conversation
- `PUT /api/conversations/{conversation_id}` - Add to an existing conversation
- `GET /api/conversations/{conversation_id}` - Retrieve a conversation by ID
- `DELETE /api/conversations/{conversation_id}` - Delete a conversation
- `GET /api/models` - List available model providers and MCP servers

## Development

### Project Structure

```
mcp_service/
├── app/
│   ├── api/                # REST API implementation
│   ├── config/             # Configuration management
│   ├── host/               # MCP Host implementation
│   ├── model/              # Model integration
│   ├── persistence/        # Conversation storage
│   ├── scheduler/          # Scheduler service integration
│   └── utils/              # Utility functions
├── docker/                 # Docker configuration
├── tests/                  # Test suite
├── docs/                   # Documentation
│   ├── mcp_sdk_integration.md      # MCP SDK integration guide
│   ├── mcp_sdk_integration_summary.md # Integration summary
│   └── scheduler_guide.md          # Scheduler service guide
├── .dockerignore           # Docker ignore file
├── .gitignore              # Git ignore file
├── Dockerfile              # Docker build file
├── pyproject.toml          # Project dependencies
└── README.md               # Project documentation
```

### Running Tests

```bash
pytest
```

## MCP SDK Integration

This project uses the official Model Context Protocol (MCP) Python SDK for standardized integration with MCP servers. The SDK provides support for multiple transport types and authentication methods. For more details, see:

- [MCP SDK Integration Guide](docs/mcp_sdk_integration.md)
- [MCP SDK Integration Summary](docs/mcp_sdk_integration_summary.md)

## Scheduler Service

The Scheduler service allows scheduling conversations for future delivery using the MCP protocol. It's implemented as a separate .NET Core service that has been integrated with this project. For more details, see:

- [Scheduler Service Guide](docs/scheduler_guide.md)

### Starting the Scheduler Service

```bash
# Start both the API server and Scheduler service
python scripts/start_services.py --scheduler

# Or start just the Scheduler service
python scripts/start_scheduler.py
```

### Using the Scheduler Service

```bash
# Schedule a conversation
python scripts/scheduler_example.py --schedule

# Check a conversation status
python scripts/scheduler_example.py --check <conversation-id>

# Cancel a scheduled conversation
python scripts/scheduler_example.py --cancel <conversation-id>
```

## License

MIT
