# Azure Deployment Best Practices for MCP SDK Integration

This document outlines best practices for deploying the MCP SDK integration and Scheduler service to Azure environments.

## Overview

When deploying the MCP SDK integration to Azure, several considerations should be made to ensure security, reliability, and performance. The recommendations below address these concerns specifically for the MCP SDK integration and Scheduler service.

## Authentication and Security

### Key and Secret Management

1. **Azure Key Vault Integration**

   - Store client IDs, API keys, and other secrets in Azure Key Vault
   - Use Key Vault references in your configuration instead of hardcoded values
   - Example:

   ```python
   from azure.keyvault.secrets import SecretClient
   from azure.identity import DefaultAzureCredential

   keyVaultName = "your-kv-name"
   KVUri = f"https://{keyVaultName}.vault.azure.net"

   credential = DefaultAzureCredential()
   client = SecretClient(vault_url=KVUri, credential=credential)

   # Get secrets
   client_id = client.get_secret("SCHEDULER-CLIENT-ID").value
   api_key = client.get_secret("SCHEDULER-API-KEY").value
   ```

2. **Managed Identities**

   - Use Azure Managed Identities to authenticate to Azure services
   - Eliminate the need to store credentials in code or configuration files
   - Configure appropriate RBAC permissions for the managed identity

3. **JWT Token Security**
   - Store JWT tokens securely in memory, not in logs or persistent storage
   - Implement token refresh mechanisms before expiration
   - Add jitter to token refresh timing to prevent thundering herd problems

## Networking and Connectivity

1. **Private Endpoints**

   - If the Scheduler service is deployed to Azure, use Private Endpoints to secure communication
   - Configure Azure Private Link for secure connectivity between your application and the service
   - Example:

   ```json
   {
     "mcp": {
       "mcp_servers": [
         {
           "name": "Scheduler",
           "transport": {
             "type": "http",
             "url": "http://scheduler.privatelink.servicebus.windows.net/mcp",
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

2. **Service Endpoints**

   - Configure Azure Service Endpoints for your virtual network
   - Restrict access to the Scheduler service to specific virtual networks

3. **Network Security Groups (NSGs)**
   - Configure NSGs to restrict traffic between your application and the Scheduler service
   - Only allow necessary ports and protocols

## Scalability and Performance

1. **Azure App Service / AKS Deployment**

   - Deploy the application to Azure App Service for managed hosting
   - For more control, use Azure Kubernetes Service (AKS) with proper scaling configuration
   - Example App Service configuration:

   ```json
   {
     "name": "mcp-scheduler-app",
     "type": "Microsoft.Web/sites",
     "properties": {
       "siteConfig": {
         "appSettings": [
           {
             "name": "SCHEDULER_CLIENT_ID",
             "value": "@Microsoft.KeyVault(SecretUri=https://your-kv-name.vault.azure.net/secrets/SCHEDULER-CLIENT-ID/)"
           },
           {
             "name": "SCHEDULER_API_KEY",
             "value": "@Microsoft.KeyVault(SecretUri=https://your-kv-name.vault.azure.net/secrets/SCHEDULER-API-KEY/)"
           }
         ]
       }
     }
   }
   ```

2. **Connection Pooling**

   - Implement connection pooling for HTTP transport connections
   - Reuse authenticated connections where possible
   - Example:

   ```python
   import httpx

   class PooledHttpClient:
       def __init__(self, base_url, timeout=10, pool_limits=None):
           self.client = httpx.AsyncClient(
               base_url=base_url,
               timeout=timeout,
               limits=pool_limits or httpx.Limits(max_connections=100, max_keepalive_connections=20),
           )

       async def request(self, method, url, **kwargs):
           return await self.client.request(method, url, **kwargs)

       async def close(self):
           await self.client.aclose()
   ```

3. **Retry Logic**

   - Implement exponential backoff with jitter for API calls
   - Handle transient failures gracefully
   - Example:

   ```python
   import asyncio
   import random

   async def retry_with_backoff(func, max_retries=3, base_delay=1, max_delay=10):
       retries = 0
       while True:
           try:
               return await func()
           except Exception as e:
               retries += 1
               if retries > max_retries:
                   raise
               # Calculate delay with jitter
               delay = min(base_delay * (2 ** (retries - 1)) + random.uniform(0, 1), max_delay)
               print(f"Retrying after {delay}s due to error: {e}")
               await asyncio.sleep(delay)
   ```

## Monitoring and Diagnostics

1. **Application Insights Integration**

   - Use Application Insights for monitoring and telemetry
   - Track authentication attempts, token refreshes, and API calls
   - Example:

   ```python
   from opencensus.ext.azure.trace_exporter import AzureExporter
   from opencensus.trace.samplers import ProbabilitySampler
   from opencensus.trace.tracer import Tracer

   # Configure exporter
   exporter = AzureExporter(
       connection_string='InstrumentationKey=00000000-0000-0000-0000-000000000000'
   )

   # Create tracer
   tracer = Tracer(exporter=exporter, sampler=ProbabilitySampler(1.0))

   # Use in code
   with tracer.span(name="scheduler_api_call"):
       await client.call_tool("scheduleConversation", params)
   ```

2. **Log Analytics**

   - Send logs to Azure Log Analytics for centralized logging
   - Set up alerts for authentication failures and API errors
   - Use KQL queries to analyze service performance and usage patterns

3. **Health Checks**
   - Implement health probes for the Scheduler service
   - Regular connectivity checks to detect issues proactively
   - Example:
   ```python
   async def health_check(client):
       try:
           # Simple check - list tools
           tools = await client.list_tools()
           return len(tools) > 0
       except Exception as e:
           logger.error(f"Health check failed: {e}")
           return False
   ```

## Disaster Recovery and High Availability

1. **Multi-Region Deployment**

   - Deploy the Scheduler service to multiple regions
   - Implement automatic failover between regions
   - Example failover configuration:

   ```python
   scheduler_endpoints = [
       "https://scheduler-eastus.azurewebsites.net/mcp",
       "https://scheduler-westus.azurewebsites.net/mcp"
   ]

   async def get_available_endpoint():
       for endpoint in scheduler_endpoints:
           try:
               response = await asyncio.wait_for(
                   httpx.AsyncClient().get(f"{endpoint}/ping"),
                   timeout=2
               )
               if response.status_code == 200:
                   return endpoint
           except:
               continue
       raise Exception("No scheduler endpoints available")
   ```

2. **Backup and Recovery Strategy**
   - Implement regular backups of scheduler configuration
   - Document recovery procedures for service failures
   - Test recovery procedures periodically

## Cost Optimization

1. **Azure Functions for Utilities**

   - Consider moving utility scripts to Azure Functions to reduce compute costs
   - Implement consumption-based billing for infrequently used operations
   - Example:

   ```python
   # Example Azure Function for scheduler status checking
   import azure.functions as func
   import json

   async def main(req: func.HttpRequest) -> func.HttpResponse:
       conversation_id = req.params.get('conversation_id')
       if not conversation_id:
           return func.HttpResponse("Please pass a conversation_id on the query string", status_code=400)

       status = await check_conversation_status(conversation_id)
       return func.HttpResponse(json.dumps({"status": status}), mimetype="application/json")
   ```

2. **Resource Autoscaling**
   - Configure autoscaling based on load patterns
   - Scale down during low-usage periods to minimize costs

## Implementation Guidelines

1. **Update Configuration for Azure**

   - Modify `config.py` to support Azure-specific features
   - Add support for Key Vault references
   - Example addition:

   ```python
   class AzureConfig(BaseModel):
       """Azure-specific configuration."""

       use_managed_identity: bool = False
       key_vault_name: Optional[str] = None
       application_insights_connection_string: Optional[str] = None
   ```

2. **Enhance the MCPSdkClient**

   - Add Azure-specific features to the client implementation
   - Support for Azure monitor integration
   - Example enhancement:

   ```python
   async def _initialize_http_azure(self) -> None:
       """Initialize HTTP transport using Streamable HTTP with Azure enhancements."""
       url = self.config.transport.url

       if not url:
           raise ValueError(f"URL not specified for HTTP transport of {self.name}")

       logger.info(f"Initializing Azure-enhanced HTTP client for {self.name} at {url}")

       # Use DefaultAzureCredential for managed identity if configured
       if self.config.azure and self.config.azure.use_managed_identity:
           from azure.identity import DefaultAzureCredential
           credential = DefaultAzureCredential()
           token = await asyncio.to_thread(credential.get_token, "https://management.azure.com/.default")
           self.client = Client(url, headers={"Authorization": f"Bearer {token.token}"})
       else:
           # Fall back to regular auth
           await self._initialize_http()
   ```

3. **Update Scheduler Service Wrapper**
   - Add Azure-specific enhancements to the scheduler service
   - Support for resilient communication patterns
   - Example:
   ```python
   class AzureSchedulerService(SchedulerService):
       """Azure-enhanced wrapper for the Scheduler MCP service."""

       def __init__(self, config, application_insights_key=None):
           super().__init__(config)
           self.ai_key = application_insights_key
           self.tracer = None
           if self.ai_key:
               # Initialize Application Insights
               # ...

       async def schedule_conversation_with_reliability(self, *args, **kwargs):
           """Schedule conversation with enhanced reliability patterns."""
           with self.tracer.span(name="schedule_conversation") if self.tracer else nullcontext():
               return await retry_with_backoff(
                   lambda: self.schedule_conversation(*args, **kwargs)
               )
   ```

## Conclusion

Following these best practices will help ensure that your MCP SDK integration and Scheduler service deployment to Azure is secure, reliable, and performant. These recommendations align with the Azure Well-Architected Framework's principles of reliability, security, cost optimization, operational excellence, and performance efficiency.

For more information on Azure security practices, refer to the [Azure security documentation](https://docs.microsoft.com/en-us/azure/security/).
