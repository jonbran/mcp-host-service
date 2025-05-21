# MCP Host Development Guide

This document provides guidance for developers working on the MCP Host/Client/Service project.

## Environment Setup

### Setting Up Development Environment

1. **Clone the repository**

```bash
git clone <repository-url>
cd mcp_service
```

2. **Create and activate a virtual environment using UV**

```bash
# Install UV if not already installed
curl -sSf https://astral.sh/uv/install.sh | bash

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
```

3. **Install dependencies**

```bash
uv pip install -e ".[dev]"
```

### Environment Variables

Create a `.env` file in the project root for local development:

```
# Model configuration
MODEL_ID=deepseek-ai/DeepSeek-R1
USE_GPU=0

# API configuration
API_HOST=0.0.0.0
API_PORT=8000

# Data directory
DATA_DIR=./data
```

## Project Structure

The project is organized as follows:

```
mcp_service/
├── app/                  # Main application package
│   ├── api/              # REST API implementation
│   ├── config/           # Configuration management
│   ├── host/             # MCP Host implementation
│   ├── model/            # Model integration
│   ├── persistence/      # Conversation storage
│   └── utils/            # Utility functions
├── config/               # Configuration files
├── scripts/              # Utility scripts
│   ├── search_server.py  # Sample SearchEngine MCP server
│   ├── test_mcp_service.py  # Test script for the service
│   └── webscraper_server.py  # Sample WebScraper MCP server
├── tests/                # Test suite
├── Dockerfile            # Docker configuration
├── pyproject.toml        # Project metadata and dependencies
└── README.md             # Project documentation
```

## Development Workflow

### Running the Application

1. **Start the MCP service**

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the start script
python scripts/start_services.py
```

2. **Testing with Sample MCP Servers**

```bash
# Start with sample MCP servers
python scripts/start_services.py --all

# Test the service
python scripts/test_mcp_service.py
```

### Testing

1. **Running Tests**

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_config.py
```

2. **Code Quality**

```bash
# Formatting
black .

# Import sorting
isort .

# Linting
ruff check .

# Type checking
mypy .
```

## MCP Protocol Implementation

### Adding a New MCP Server

To add a new MCP server:

1. Create a new server implementation in the `scripts/` directory
2. Update the configuration in `config/config.json` to include the new server
3. Implement the appropriate transport mechanism (stdio or SSE)

Example config entry:

```json
{
  "name": "NewServer",
  "transport": {
    "type": "stdio",
    "command": "python",
    "args": ["scripts/new_server.py"]
  }
}
```

### Extending the MCP Host

To extend the MCP Host with new capabilities:

1. Update the `extract_mcp_requests_from_text` function in `app/utils/model_mcp.py` if needed
2. Modify the `_fulfill_mcp_requests` method in `app/host/host.py` to handle new request types
3. Update system prompts in `create_mcp_system_prompt` to include new capabilities

## Model Integration

### Provider Architecture

The MCP Host uses a provider-based architecture to support different model providers:

1. `ModelProvider` - Abstract base class defining the common interface
2. `HuggingFaceProvider` - For local HuggingFace models
3. `OpenAIProvider` - For OpenAI API models (including Azure OpenAI)
4. `AnthropicProvider` - For Anthropic API models

The provider system allows easy switching between model providers without changing the core application logic.

### Adding Support for a New Model Provider

To add support for a new model provider:

1. Create a new provider class in `app/model/provider.py` that inherits from `ModelProvider`
2. Implement the required methods: `initialize()` and `generate_response()`
3. Update the `ModelProviderType` enum in `app/config/config.py`
4. Add the new provider to the `get_provider()` factory function
5. Update the example configurations

Example:

```python
class NewProvider(ModelProvider):
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        # Initialize provider-specific attributes

    async def initialize(self) -> None:
        # Implementation for provider initialization
        pass

    async def generate_response(self, messages: List[Dict[str, Any]]) -> str:
        # Implementation for response generation
        pass
```

### Adding Support for a New Model Type

To add support for a new model format within an existing provider:

1. Add a new formatting method in the provider class
2. Update the provider's internal methods to handle the new model type
3. Test with sample conversations

## Docker Deployment

### Building the Docker Image

```bash
docker build -t mcp-service .
```

### Running with Docker

```bash
docker run -p 8000:8000 mcp-service
```

## API Reference

### Endpoints

- `GET /health` - Health check endpoint
- `POST /assistant/conversations` - Create a new conversation
- `GET /assistant/conversations/{conversation_id}` - Get a conversation
- `POST /assistant/conversations/{conversation_id}/messages` - Add a message to a conversation
- `DELETE /assistant/conversations/{conversation_id}` - Delete a conversation

## Troubleshooting

### Common Issues

1. **Model loading fails**

   - Check if the model ID is correct
   - Ensure sufficient memory for model loading
   - Set `USE_GPU=0` if GPU is not available

2. **MCP Server communication fails**

   - Check if the MCP server is running
   - Verify the transport configuration
   - Check logs for detailed error messages

3. **API errors**
   - Check if the service is running
   - Verify the request format
   - Check API responses for error details

## Contributing

1. Follow the project's code style (black, isort, ruff, mypy)
2. Write tests for new functionality
3. Update documentation as needed
4. Submit a pull request with a clear description of changes
