# Azure Integration Guide for MCP SDK and Scheduler

This guide provides practical steps for integrating the MCP SDK and Scheduler service with Azure services, focusing on two main deployment scenarios: Azure App Service and Azure Container Apps.

## Prerequisites

- An active Azure subscription
- Basic knowledge of Azure services and the Azure portal
- The MCP SDK integrated project as described in [MCP SDK Integration Guide](mcp_sdk_integration.md)

## Integration Steps

### 1. Set Up Azure Resources

#### Key Vault Setup

1. Create an Azure Key Vault to store sensitive configuration like authentication keys:

```bash
# Create a resource group if needed
az group create --name mcp-scheduler-rg --location eastus

# Create Key Vault
az keyvault create --name mcp-scheduler-kv --resource-group mcp-scheduler-rg --location eastus

# Add secrets for Scheduler service
az keyvault secret set --vault-name mcp-scheduler-kv --name "SCHEDULER-CLIENT-ID" --value "your_client_id"
az keyvault secret set --vault-name mcp-scheduler-kv --name "SCHEDULER-API-KEY" --value "your_api_key"
```

#### Application Insights Setup

1. Create an Application Insights instance for telemetry:

```bash
# Create Application Insights
az monitor app-insights component create --app mcp-scheduler-insights \
  --resource-group mcp-scheduler-rg \
  --location eastus \
  --kind web \
  --application-type web
```

### 2. Deploy the Scheduler Service

#### Option A: Azure Container Apps

1. Create an Azure Container Registry:

```bash
# Create ACR
az acr create --name mcpschedulerregistry \
  --resource-group mcp-scheduler-rg \
  --sku Basic \
  --admin-enabled true
```

2. Build and push the Scheduler container:

```bash
# Build container locally
docker build -t mcpscheduler:latest .

# Log in to ACR
az acr login --name mcpschedulerregistry

# Tag and push container
docker tag mcpscheduler:latest mcpschedulerregistry.azurecr.io/mcpscheduler:latest
docker push mcpschedulerregistry.azurecr.io/mcpscheduler:latest
```

3. Deploy to Azure Container Apps:

```bash
# Create Container Apps environment
az containerapp env create \
  --name mcp-scheduler-env \
  --resource-group mcp-scheduler-rg \
  --location eastus

# Deploy Scheduler container
az containerapp create \
  --name mcp-scheduler-app \
  --resource-group mcp-scheduler-rg \
  --environment mcp-scheduler-env \
  --image mcpschedulerregistry.azurecr.io/mcpscheduler:latest \
  --target-port 5146 \
  --ingress external \
  --registry-server mcpschedulerregistry.azurecr.io \
  --query properties.configuration.ingress.fqdn
```

#### Option B: Azure App Service

1. Create an App Service Plan:

```bash
# Create App Service Plan
az appservice plan create \
  --name mcp-scheduler-plan \
  --resource-group mcp-scheduler-rg \
  --sku B1 \
  --is-linux
```

2. Create a Web App:

```bash
# Create Web App
az webapp create \
  --name mcp-scheduler-webapp \
  --resource-group mcp-scheduler-rg \
  --plan mcp-scheduler-plan \
  --runtime "PYTHON|3.10" \
  --deployment-source-url https://github.com/your-repo/mcpscheduler
```

3. Configure environment variables:

```bash
# Set environment variables with Key Vault references
az webapp config appsettings set \
  --name mcp-scheduler-webapp \
  --resource-group mcp-scheduler-rg \
  --settings \
  SCHEDULER_CLIENT_ID="@Microsoft.KeyVault(SecretUri=https://mcp-scheduler-kv.vault.azure.net/secrets/SCHEDULER-CLIENT-ID/)" \
  SCHEDULER_API_KEY="@Microsoft.KeyVault(SecretUri=https://mcp-scheduler-kv.vault.azure.net/secrets/SCHEDULER-API-KEY/)" \
  PORT="5146"
```

### 3. Update MCP Client Configuration

1. Modify your configuration to point to the Azure-deployed Scheduler:

```json
{
  "mcp": {
    "mcp_servers": [
      {
        "name": "Scheduler",
        "transport": {
          "type": "http",
          "url": "https://mcp-scheduler-app.azurecontainerapps.io/mcp",
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

2. For managed identity authentication (if using Azure App Service or Azure Functions):

```json
{
  "mcp": {
    "mcp_servers": [
      {
        "name": "Scheduler",
        "transport": {
          "type": "http",
          "url": "https://mcp-scheduler-app.azurecontainerapps.io/mcp",
          "auth": {
            "use_managed_identity": true
          }
        }
      }
    ]
  },
  "azure": {
    "use_managed_identity": true,
    "key_vault_name": "mcp-scheduler-kv",
    "application_insights_connection_string": "InstrumentationKey=..."
  }
}
```

### 4. Deploy the MCP Host Service

#### Azure App Service Deployment

1. Create an App Service Plan (if not already created):

```bash
# Create App Service Plan
az appservice plan create \
  --name mcp-host-plan \
  --resource-group mcp-scheduler-rg \
  --sku B1 \
  --is-linux
```

2. Create a Web App for the Host Service:

```bash
# Create Web App
az webapp create \
  --name mcp-host-webapp \
  --resource-group mcp-scheduler-rg \
  --plan mcp-host-plan \
  --runtime "PYTHON|3.10"
```

3. Configure environment variables and deployment:

```bash
# Set environment variables
az webapp config appsettings set \
  --name mcp-host-webapp \
  --resource-group mcp-scheduler-rg \
  --settings \
  USE_AZURE_SERVICES="true" \
  KEYVAULT_URI="https://mcp-scheduler-kv.vault.azure.net/"

# Configure GitHub Actions deployment (if using GitHub)
az webapp deployment github-actions add \
  --repo your-username/your-repo \
  --branch main \
  --name mcp-host-webapp \
  --resource-group mcp-scheduler-rg
```

### 5. Configure Azure Networking and Security

#### Private Link Setup (Optional)

For enhanced security, use Azure Private Link:

```bash
# Create Virtual Network
az network vnet create \
  --name mcp-vnet \
  --resource-group mcp-scheduler-rg \
  --address-prefix 10.0.0.0/16 \
  --subnet-name default \
  --subnet-prefix 10.0.0.0/24

# Create Private Endpoint
az network private-endpoint create \
  --name mcp-scheduler-pe \
  --resource-group mcp-scheduler-rg \
  --vnet-name mcp-vnet \
  --subnet default \
  --private-connection-resource-id $(az webapp show --name mcp-scheduler-webapp --resource-group mcp-scheduler-rg --query id -o tsv) \
  --group-id sites \
  --connection-name mcp-scheduler-connection
```

### 6. Implement Azure-Enhanced MCPSdkClient

Create a new `azure_mcp_client.py` file with Azure-specific enhancements:

```python
from app.host.mcp_client import MCPSdkClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
import os
import logging
import asyncio
from contextlib import nullcontext
from typing import Any, Dict, Optional

class AzureMCPSdkClient(MCPSdkClient):
    """Azure-enhanced MCP SDK Client implementation."""

    async def initialize(self) -> None:
        """Initialize with Azure enhancements if configured."""
        # Check if Azure integration is enabled
        if os.environ.get("USE_AZURE_SERVICES") == "true" and self.config.transport.auth.get("use_managed_identity"):
            await self._initialize_with_managed_identity()
        else:
            await super().initialize()

        # Set up Application Insights if connection string is provided
        insights_key = os.environ.get("APPINSIGHTS_INSTRUMENTATIONKEY")
        if insights_key:
            self._setup_telemetry(insights_key)

    async def _initialize_with_managed_identity(self) -> None:
        """Initialize using managed identity."""
        # Initialize transport based on type
        if self.config.transport.type == "http":
            await self._initialize_http_with_managed_identity()
        else:
            await super().initialize()

    async def _initialize_http_with_managed_identity(self) -> None:
        """Initialize HTTP transport using managed identity."""
        url = self.config.transport.url
        if not url:
            raise ValueError(f"URL not specified for HTTP transport of {self.name}")

        logging.info(f"Initializing HTTP client with managed identity for {self.name} at {url}")

        try:
            # Get token from managed identity
            credential = DefaultAzureCredential()
            token = await asyncio.to_thread(
                credential.get_token,
                "https://management.azure.com/.default"
            )

            # Create client with token
            from mcp import Client
            self.client = Client(url, headers={"Authorization": f"Bearer {token.token}"})

            # Set up refresh mechanism
            self._setup_token_refresh_task(credential)
        except Exception as e:
            logging.error(f"Failed to initialize with managed identity: {e}")
            # Fall back to regular initialization
            await super().initialize()

    def _setup_telemetry(self, instrumentation_key: str) -> None:
        """Set up Application Insights telemetry."""
        exporter = AzureExporter(connection_string=f'InstrumentationKey={instrumentation_key}')
        self.tracer = Tracer(exporter=exporter, sampler=ProbabilitySampler(1.0))

    async def _setup_token_refresh_task(self, credential) -> None:
        """Set up a background task to refresh token periodically."""
        async def refresh_token_periodically():
            while True:
                await asyncio.sleep(3300)  # Refresh every 55 minutes (tokens usually valid for 60)
                try:
                    token = await asyncio.to_thread(
                        credential.get_token,
                        "https://management.azure.com/.default"
                    )
                    self.client = Client(
                        self.config.transport.url,
                        headers={"Authorization": f"Bearer {token.token}"}
                    )
                    logging.info(f"Token refreshed for {self.name}")
                except Exception as e:
                    logging.error(f"Failed to refresh token: {e}")

        # Start background task
        asyncio.create_task(refresh_token_periodically())

    async def call_tool(self, name: str, params: Dict[str, Any]) -> Any:
        """Call a tool with telemetry tracking."""
        span_context = self.tracer.span(name=f"mcp_call_tool_{name}") if hasattr(self, 'tracer') else nullcontext()
        with span_context:
            return await super().call_tool(name, params)
```

### 7. Update Startup Scripts

Create an `azure_startup.py` script for Azure environments:

```python
"""Startup script for Azure deployment."""
import os
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import asyncio
from app.main import app
from app.config.config import AppConfig
from app.host.azure_mcp_client import AzureMCPSdkClient

async def initialize_azure_services():
    """Initialize Azure-specific services."""
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Get Key Vault URI
    key_vault_uri = os.environ.get("KEYVAULT_URI")
    if not key_vault_uri:
        logging.warning("KEYVAULT_URI not set, skipping Key Vault integration")
        return

    try:
        # Use managed identity to access Key Vault
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=key_vault_uri, credential=credential)

        # Get secrets and set as environment variables
        for secret_name in ["SCHEDULER-CLIENT-ID", "SCHEDULER-API-KEY"]:
            secret = client.get_secret(secret_name)
            os.environ[secret_name.replace("-", "_")] = secret.value
            logging.info(f"Loaded secret {secret_name} from Key Vault")

    except Exception as e:
        logging.error(f"Failed to initialize Azure services: {e}")

if __name__ == "__main__":
    # Run initialization on startup
    if os.environ.get("USE_AZURE_SERVICES") == "true":
        asyncio.run(initialize_azure_services())

    # Import uvicorn here to avoid circular imports
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
```

### 8. Testing Azure Integration

1. Create an `azure_integration_test.py` script:

```python
"""Test script for Azure integration."""
import asyncio
import os
import json
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from app.host.azure_mcp_client import AzureMCPSdkClient
from app.config.config import AppConfig, MCPServerConfig, TransportConfig, TransportType

async def test_azure_integration():
    """Test Azure integration features."""
    logging.basicConfig(level=logging.INFO)

    # Get Key Vault URI from env or use default for testing
    key_vault_uri = os.environ.get("KEYVAULT_URI", "https://mcp-scheduler-kv.vault.azure.net/")

    try:
        # Create server config for testing
        server_config = MCPServerConfig(
            name="Scheduler",
            transport=TransportConfig(
                type=TransportType.HTTP,
                url=os.environ.get(
                    "SCHEDULER_URL",
                    "https://mcp-scheduler-app.azurecontainerapps.io/mcp"
                ),
                auth={"use_managed_identity": True}
            )
        )

        # Initialize Azure MCP client
        client = AzureMCPSdkClient(server_config)
        await client.initialize()

        # List tools
        tools = await client.list_tools()
        logging.info(f"Available tools: {json.dumps(tools, indent=2)}")

        # Close client
        await client.close()

    except Exception as e:
        logging.error(f"Azure integration test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_azure_integration())
```

2. Run the test script:

```bash
# Set environment variables
export USE_AZURE_SERVICES=true
export KEYVAULT_URI=https://mcp-scheduler-kv.vault.azure.net/

# Run test
python azure_integration_test.py
```

## Next Steps

1. Set up a CI/CD pipeline using Azure DevOps or GitHub Actions
2. Configure Azure Monitor alerts for service health monitoring
3. Implement backup and disaster recovery procedures
4. Set up scaling rules based on traffic patterns

For more detailed guidance, refer to:

- [Azure Deployment Best Practices](azure_deployment_best_practices.md)
- [MCP SDK Azure Integration Best Practices](mcp_sdk_azure_integration.md)
