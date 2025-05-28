# MCP SDK Azure Integration Best Practices

This document provides specific guidance for integrating the Model Context Protocol (MCP) SDK with Azure services, with a focus on security, performance, and reliability.

## Authentication Best Practices

### 1. Secure Secret Management

When deploying to Azure, replace local authentication approaches with Azure-native services:

```python
# Instead of this:
client_id = os.environ.get("SCHEDULER_CLIENT_ID")
api_key = os.environ.get("SCHEDULER_API_KEY")

# Use this for Azure deployments:
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Initialize the managed identity credential
credential = DefaultAzureCredential()

# Access secrets from Key Vault
secret_client = SecretClient(vault_url="https://your-keyvault.vault.azure.net", credential=credential)
client_id = secret_client.get_secret("SCHEDULER-CLIENT-ID").value
api_key = secret_client.get_secret("SCHEDULER-API-KEY").value
```

### 2. Managed Identities for Service-to-Service Authentication

For services deployed to Azure, use managed identities instead of client credentials:

```python
# MCPSdkClient enhancement for Azure deployments
async def initialize_with_managed_identity(self) -> None:
    """Initialize the MCP client using a managed identity."""
    if self.config.transport.type == TransportType.HTTP:
        from azure.identity.aio import DefaultAzureCredential

        # Get token from managed identity
        credential = DefaultAzureCredential()
        token = await credential.get_token("https://management.azure.com/.default")

        # Create client with token
        url = self.config.transport.url
        self.client = Client(url, headers={"Authorization": f"Bearer {token.token}"})

        # Set up token refresh
        self._setup_token_refresh(credential)
```

## Transport Security

### 1. Private Endpoints and Service Endpoints

For HTTP transport within Azure, use private endpoints for secure communication:

```json
{
  "transport": {
    "type": "http",
    "url": "https://scheduler-service.privatelink.azurewebsites.net/mcp",
    "auth": {
      "use_managed_identity": true
    }
  }
}
```

### 2. TLS Configuration for HTTP Transport

Always use HTTPS with proper TLS configuration:

```python
# Enhanced HTTP client initialization
import ssl
import certifi

ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1  # Disable older TLS protocols

client = httpx.AsyncClient(
    base_url=url,
    verify=ssl_context,
    http2=True  # Enable HTTP/2 for better performance
)
```

## Monitoring and Logging

### 1. Application Insights Integration

Add telemetry to track MCP SDK operations:

```python
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace import config_integration

# Configure Azure Monitor integration
config_integration.trace_integrations(['httpx'])
tracer = Tracer(
    exporter=AzureExporter(connection_string='InstrumentationKey=your-instrumentation-key'),
    sampler=ProbabilitySampler(1.0),
)

# Enhanced MCP client with telemetry
class TelemetryEnabledMCPClient(MCPSdkClient):
    async def call_tool(self, name: str, params: Dict[str, Any]) -> Any:
        with tracer.span(name=f"mcp_call_tool_{name}"):
            return await super().call_tool(name, params)
```

### 2. Structured Logging for Azure Log Analytics

Configure logging to integrate with Azure Log Analytics:

```python
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler

# Configure logger
logger = logging.getLogger("mcp_sdk")
logger.setLevel(logging.INFO)

# Add Azure Log Analytics handler
logger.addHandler(AzureLogHandler(
    connection_string='InstrumentationKey=your-instrumentation-key'
))
```

## Resilience and Error Handling

### 1. Circuit Breaker Pattern

Implement circuit breakers to prevent cascading failures:

```python
import asyncio
import time
from typing import Callable, TypeVar, Any

T = TypeVar('T')

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_time: float = 30.0,
    ):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.last_failure_time = 0
        self.open = False

    async def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        if self.open:
            if time.time() - self.last_failure_time > self.recovery_time:
                # Try to close circuit for one request
                self.open = False
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            # Success, reset failure count
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.open = True
                self.last_failure_time = time.time()
            raise e

# Usage with MCP client
scheduler_cb = CircuitBreaker()

async def schedule_with_cb(scheduler, *args, **kwargs):
    return await scheduler_cb.execute(scheduler.schedule_conversation, *args, **kwargs)
```

### 2. Retry with Exponential Backoff

Implement Azure-friendly retry policies:

```python
import asyncio
import random

async def retry_with_backoff(
    func,
    max_retries=3,
    base_delay=1,
    max_delay=60,
    retryable_exceptions=(ConnectionError, TimeoutError)
):
    retries = 0
    while True:
        try:
            return await func()
        except retryable_exceptions as e:
            retries += 1
            if retries > max_retries:
                raise

            # Calculate delay with jitter to prevent thundering herd
            delay = min(base_delay * (2 ** (retries - 1)) + (random.random() * 0.1 * base_delay), max_delay)

            # Log retry attempt
            logger.warning(f"Retrying {func.__name__} after {delay}s due to {e.__class__.__name__}: {e}")

            await asyncio.sleep(delay)
```

## Performance Optimization

### 1. Connection Pooling

Optimize HTTP connections for Azure deployments:

```python
# Enhanced HTTP client with connection pooling
from httpx import AsyncClient, Limits

class PooledMCPHttpClient:
    def __init__(
        self,
        base_url: str,
        headers: Dict[str, str] = None,
        max_connections: int = 100,
        max_keepalive: int = 20,
        keepalive_expiry: int = 60, # seconds
        timeout: float = 30.0
    ):
        self.client = AsyncClient(
            base_url=base_url,
            headers=headers,
            limits=Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive,
                keepalive_expiry=keepalive_expiry
            ),
            timeout=timeout
        )

    async def close(self):
        await self.client.aclose()
```

### 2. Asynchronous Batch Processing

For multiple scheduled conversations, use efficient batching:

```python
async def batch_schedule_conversations(
    scheduler_service,
    conversations: List[Dict[str, Any]]
):
    """Schedule multiple conversations efficiently."""
    tasks = [
        scheduler_service.schedule_conversation(
            conversation_text=conv["text"],
            scheduled_time=conv["time"],
            endpoint=conv["endpoint"]
        )
        for conv in conversations
    ]

    # Process in batches to avoid overwhelming the service
    batch_size = 10
    results = []

    for i in range(0, len(tasks), batch_size):
        batch_tasks = tasks[i:i+batch_size]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        results.extend(batch_results)

        # Small delay between batches to reduce load
        if i + batch_size < len(tasks):
            await asyncio.sleep(0.5)

    return results
```

## Azure Service Integration

### 1. Azure Functions Integration

For serverless processing of scheduled callbacks:

```python
# Example Azure Function for handling scheduler callbacks
import azure.functions as func
import json
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Function to handle callbacks from the Scheduler service."""
    logging.info('Received callback from Scheduler')

    try:
        req_body = req.get_json()
        conversation_id = req_body.get('conversationId')
        status = req_body.get('status')
        content = req_body.get('content')

        # Process the scheduled conversation
        # ...

        return func.HttpResponse(
            json.dumps({"success": True}),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error processing scheduler callback: {str(e)}")
        return func.HttpResponse(
            json.dumps({"success": False, "error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
```

### 2. Azure Storage for Conversation Persistence

Use Azure Storage for durable persistence:

```python
from azure.storage.blob.aio import BlobServiceClient
import json

class AzureStorageConversationStore:
    """Store conversations in Azure Blob Storage."""

    def __init__(self, connection_string: str, container_name: str = "conversations"):
        self.service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_name = container_name
        self.container_client = None

    async def initialize(self):
        """Ensure container exists."""
        self.container_client = self.service_client.get_container_client(self.container_name)
        try:
            await self.container_client.create_container()
        except Exception:
            # Container may already exist
            pass

    async def store_conversation(self, conversation_id: str, data: Dict[str, Any]):
        """Store a conversation."""
        blob_client = self.container_client.get_blob_client(f"{conversation_id}.json")
        await blob_client.upload_blob(json.dumps(data), overwrite=True)

    async def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Retrieve a conversation."""
        blob_client = self.container_client.get_blob_client(f"{conversation_id}.json")
        download = await blob_client.download_blob()
        content = await download.content_as_text()
        return json.loads(content)
```

## Deployment Best Practices

### 1. Azure App Service Configuration

Optimize App Service settings for MCP SDK:

```json
{
  "name": "mcp-host-app",
  "type": "Microsoft.Web/sites",
  "properties": {
    "siteConfig": {
      "appSettings": [
        {
          "name": "WEBSITE_RUN_FROM_PACKAGE",
          "value": "1"
        },
        {
          "name": "SCM_DO_BUILD_DURING_DEPLOYMENT",
          "value": "true"
        },
        {
          "name": "USE_AZURE_SERVICES",
          "value": "true"
        },
        {
          "name": "APPINSIGHTS_INSTRUMENTATIONKEY",
          "value": "your-instrumentation-key"
        },
        {
          "name": "KEYVAULT_URI",
          "value": "https://your-keyvault.vault.azure.net/"
        }
      ],
      "alwaysOn": true,
      "http20Enabled": true,
      "minTlsVersion": "1.2"
    }
  }
}
```

### 2. Azure Container Apps for MCP Servers

For containerized MCP servers, use Azure Container Apps:

```yaml
# Sample Azure Container Apps configuration
name: scheduler-mcp-service
type: Microsoft.App/containerApps
properties:
  managedEnvironmentId: /subscriptions/{sub-id}/resourceGroups/{rg-name}/providers/Microsoft.App/managedEnvironments/{env-name}
  configuration:
    ingress:
      external: true
      targetPort: 5146
      transport: auto
    secrets:
      - name: scheduler-auth-key
        value: your-scheduler-auth-key
  template:
    containers:
      - name: scheduler
        image: myregistry.azurecr.io/mcp-scheduler:latest
        resources:
          cpu: 0.5
          memory: 1Gi
        env:
          - name: PORT
            value: "5146"
          - name: AUTH_KEY
            secretRef: scheduler-auth-key
    scale:
      minReplicas: 1
      maxReplicas: 10
      rules:
        - name: http-scale
          http:
            metadata:
              concurrentRequests: "10"
```

## Conclusion

By following these Azure-specific best practices, you can ensure that your MCP SDK integration is secure, reliable, and optimized for Azure environments. These practices align with the Azure Well-Architected Framework and will help you build robust applications that leverage both the MCP SDK and Azure services effectively.

For more information, refer to:

- [Azure Application Architecture Guide](https://docs.microsoft.com/en-us/azure/architecture/guide/)
- [Azure Security Best Practices](https://docs.microsoft.com/en-us/azure/security/fundamentals/best-practices-and-patterns)
- [Azure Well-Architected Framework](https://docs.microsoft.com/en-us/azure/architecture/framework/)
