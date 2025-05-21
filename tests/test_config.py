"""Tests for configuration module."""

import os
import tempfile
from pathlib import Path

import pytest

from app.config.config import (
    APIConfig,
    AppConfig,
    MCPConfig,
    MCPServerConfig,
    ModelConfig,
    TransportConfig,
    TransportType,
    load_config,
)


def test_transport_config():
    """Test transport configuration."""
    # Test SSE transport
    sse_config = TransportConfig(
        type=TransportType.SSE,
        url="https://example.com/mcp",
    )
    assert sse_config.type == TransportType.SSE
    assert sse_config.url == "https://example.com/mcp"
    
    # Test STDIO transport
    stdio_config = TransportConfig(
        type=TransportType.STDIO,
        command="python",
        args=["-m", "mcp_server"],
    )
    assert stdio_config.type == TransportType.STDIO
    assert stdio_config.command == "python"
    assert stdio_config.args == ["-m", "mcp_server"]


def test_mcp_server_config():
    """Test MCP server configuration."""
    server_config = MCPServerConfig(
        name="TestServer",
        transport=TransportConfig(
            type=TransportType.STDIO,
            command="python",
            args=["-m", "mcp_server"],
        ),
        params={"timeout": 30},
    )
    
    assert server_config.name == "TestServer"
    assert server_config.transport.type == TransportType.STDIO
    assert server_config.params == {"timeout": 30}


def test_model_config():
    """Test model configuration."""
    model_config = ModelConfig(
        model_id="test/model",
        max_sequence_length=2048,
        temperature=0.8,
    )
    
    assert model_config.model_id == "test/model"
    assert model_config.max_sequence_length == 2048
    assert model_config.temperature == 0.8
    
    # Test defaults
    default_config = ModelConfig()
    assert default_config.model_id == "deepseek-ai/DeepSeek-R1"
    
    # Override device with environment variable
    os.environ["USE_GPU"] = "1"
    gpu_config = ModelConfig()
    assert gpu_config.device == "cuda"
    
    os.environ["USE_GPU"] = "0"
    cpu_config = ModelConfig()
    assert cpu_config.device == "cpu"


def test_load_config():
    """Test loading configuration from file."""
    # Create a temporary config file
    config_data = {
        "mcp": {
            "mcp_servers": [
                {
                    "name": "TestServer",
                    "transport": {
                        "type": "stdio",
                        "command": "python",
                        "args": ["-m", "mcp_server"],
                    },
                }
            ]
        },
        "model": {
            "model_id": "test/model",
            "max_sequence_length": 2048,
        },
        "api": {
            "host": "localhost",
            "port": 9000,
        },
        "data_dir": "/tmp/data",
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        import json
        f.write(json.dumps(config_data))
        f.flush()
        
        config = load_config(f.name)
        
        assert isinstance(config, AppConfig)
        assert config.model.model_id == "test/model"
        assert config.api.host == "localhost"
        assert config.api.port == 9000
        assert len(config.mcp.mcp_servers) == 1
        assert config.mcp.mcp_servers[0].name == "TestServer"
