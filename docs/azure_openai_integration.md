# MCP Integration with Azure OpenAI Services

This document provides guidance on integrating the Model Context Protocol (MCP) SDK with Azure OpenAI services, leveraging Azure's secure and compliant AI capabilities.

## Overview

Azure OpenAI Service provides the same powerful language models as OpenAI but with the added security, compliance, and regional availability features of the Azure platform. This guide explains how to integrate Azure OpenAI with our MCP SDK implementation.

## Prerequisites

- Azure subscription with access to Azure OpenAI services
- Azure OpenAI deployment (a deployed model in your Azure OpenAI resource)
- MCP SDK integration as described in [MCP SDK Integration Guide](mcp_sdk_integration.md)

## Configuration Steps

### 1. Create Azure OpenAI Resource

First, create an Azure OpenAI resource in the Azure portal:

1. Navigate to the Azure portal
2. Create a new Azure OpenAI resource
3. Deploy a model in your Azure OpenAI resource
4. Note your endpoint and API key

### 2. Update Configuration

Update your `config.json` to include Azure OpenAI model configuration:

```json
{
  "model": {
    "provider": "openai",
    "model_id": "your-deployed-model-name",
    "max_sequence_length": 4096,
    "temperature": 0.7,
    "top_p": 0.9,
    "api_key": "your_azure_openai_api_key",
    "api_base": "https://your-resource-name.openai.azure.com/openai/deployments/your-deployed-model-name",
    "api_version": "2023-05-15",
    "azure_deployment": true
  },
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

### 3. Update Provider Implementation

Ensure your `provider.py` implementation supports Azure OpenAI specifics:

```python
class OpenAIProvider(ModelProvider):
    """OpenAI model provider implementation."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI provider.

        Args:
            config: Configuration for the provider
        """
        super().__init__(config)
        self.api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        # Azure OpenAI specific configuration
        self.is_azure = config.get("azure_deployment", False)
        self.api_base = config.get("api_base")
        self.api_version = config.get("api_version", "2023-05-15")

        # Initialize client
        if self.is_azure:
            # Azure OpenAI client setup
            if not self.api_base:
                raise ValueError("Azure OpenAI API base URL not provided")

            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
                api_version=self.api_version,
                azure_ad_token=config.get("azure_ad_token"),
                azure_deployment=self.config['model_id']
            )
        else:
            # Standard OpenAI client setup
            self.client = AsyncOpenAI(api_key=self.api_key)

        logger.info(f"Initialized OpenAI provider with model {self.config['model_id']}")

    async def generate_response(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a response from the model based on conversation history.

        Args:
            messages: Conversation history

        Returns:
            Generated response text
        """
        try:
            completion = await self.client.chat.completions.create(
                model=self.config["model_id"] if not self.is_azure else None,
                messages=[{
                    "role": msg["role"],
                    "content": msg["content"]
                } for msg in messages],
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
                top_p=self.config["top_p"],
                n=1
            )

            return completion.choices[0].message.content

        except Exception as e:
            logger.exception(f"Error generating response from OpenAI: {e}")
            raise
```

### 4. Secure Azure OpenAI API Key with Key Vault

For enhanced security, store your Azure OpenAI API key in Azure Key Vault:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def get_provider_api_key(config: Dict[str, Any]) -> str:
    """Retrieve API key, potentially from Azure Key Vault."""
    # Check if Azure integration is enabled and Key Vault is configured
    if config.get("use_key_vault") and os.environ.get("KEYVAULT_URI"):
        try:
            # Use managed identity to access Key Vault
            credential = DefaultAzureCredential()
            client = SecretClient(
                vault_url=os.environ["KEYVAULT_URI"],
                credential=credential
            )

            # Get API key from Key Vault
            secret_name = config.get("key_vault_secret_name", "AZURE-OPENAI-API-KEY")
            secret = client.get_secret(secret_name)
            return secret.value

        except Exception as e:
            logger.warning(f"Could not retrieve API key from Key Vault: {e}")
            # Fall back to config or environment variable

    # Return from config or environment
    return config.get("api_key") or os.environ.get("OPENAI_API_KEY")
```

### 5. Create Helper Script for Azure OpenAI Testing

Create a test script to validate Azure OpenAI integration:

```python
"""Test Azure OpenAI integration with MCP SDK."""
import asyncio
import os
import json
import logging
from app.model.model import ModelService
from app.config.config import AppConfig
from app.host.mcp_host import MCPSdkHost
from app.utils.model_mcp import create_mcp_system_prompt

async def test_azure_openai_mcp():
    """Test Azure OpenAI with MCP."""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Load config
    config = AppConfig.from_file("config/config.json")

    # Initialize model service
    model_service = ModelService(config)

    # Initialize MCP host
    mcp_host = MCPSdkHost(config, model_service)
    await mcp_host.initialize()

    # Test conversation with MCP request
    conversation_history = [
        {
            "role": "system",
            "content": create_mcp_system_prompt()
        },
        {
            "role": "user",
            "content": "What time is it? Can you use a tool to find out?"
        }
    ]

    # Process with Azure OpenAI
    response, updated_history = await mcp_host._process_with_model(
        conversation_history=conversation_history,
        provider_name="openai"  # Use the OpenAI provider with Azure deployment
    )

    logger.info(f"Azure OpenAI Response: {response}")

    # Close connections
    await mcp_host.close()

if __name__ == "__main__":
    asyncio.run(test_azure_openai_mcp())
```

## Azure OpenAI Integration Best Practices

### 1. Content Filtering

Azure OpenAI provides content filtering capabilities. Configure these to meet your compliance requirements:

```python
# Add content filtering parameters when using Azure OpenAI
completion = await self.client.chat.completions.create(
    # ... other parameters ...
    content_filter={
        "hate": "medium",
        "sexual": "high",
        "violence": "high",
        "self_harm": "high"
    } if self.is_azure else None
)
```

### 2. Azure Active Directory (AAD) Authentication

For environments requiring AAD authentication:

```python
from azure.identity import DefaultAzureCredential

# Get token from AAD
credential = DefaultAzureCredential()
token = credential.get_token("https://cognitiveservices.azure.com/.default")

# Use token for Azure OpenAI
self.client = AsyncOpenAI(
    api_key="not-used-with-azure-ad",  # Placeholder, not actually used
    base_url=self.api_base,
    api_version=self.api_version,
    azure_ad_token=token.token,
    azure_deployment=self.config['model_id']
)
```

### 3. Regional Compliance

Azure OpenAI is available in various regions. Choose a region that complies with your data residency requirements:

```json
{
  "model": {
    "provider": "openai",
    "model_id": "your-deployed-model-name",
    "api_base": "https://your-resource-name.{region}.api.cognitive.microsoft.com/openai/deployments/your-deployed-model-name",
    "region": "westeurope", // Choose an appropriate region
    "azure_deployment": true
  }
}
```

### 4. Monitoring and Usage Tracking

Azure OpenAI provides monitoring through Azure Monitor. Integrate this with your application:

```python
# Add custom dimensions to Application Insights for tracking
from opencensus.ext.azure import metrics_exporter

# Set up metrics exporter
exporter = metrics_exporter.new_metrics_exporter(
    connection_string='InstrumentationKey=00000000-0000-0000-0000-000000000000'
)

# Track token usage
def track_token_usage(completion):
    """Track token usage in Azure Monitor."""
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    total_tokens = completion.usage.total_tokens

    # Record metrics
    exporter.add_metrics({
        'name': 'azure_openai_prompt_tokens',
        'value': prompt_tokens,
        'tags': {'model': self.config['model_id']}
    })
    exporter.add_metrics({
        'name': 'azure_openai_completion_tokens',
        'value': completion_tokens,
        'tags': {'model': self.config['model_id']}
    })
    exporter.add_metrics({
        'name': 'azure_openai_total_tokens',
        'value': total_tokens,
        'tags': {'model': self.config['model_id']}
    })
```

## Conclusion

Integrating Azure OpenAI with the MCP SDK provides enterprise-grade AI capabilities with enhanced security, compliance, and regional availability. The implementation follows the same pattern as the standard OpenAI integration but adds Azure-specific configuration and authentication options.

For more information, refer to:

- [Azure OpenAI Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)
- [Azure OpenAI Python SDK](https://github.com/openai/openai-python)
