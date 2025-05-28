"""MCP Client implementation using the official MCP Python SDK."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from mcp import Client, StdioServerParameters, types
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from app.config.config import MCPServerConfig, TransportType

logger = logging.getLogger(__name__)


class MCPSdkClient:
    """Client for connecting to MCP Servers using the official MCP SDK."""

    def __init__(self, server_config: MCPServerConfig):
        """Initialize MCP client.
        
        Args:
            server_config: Configuration for the MCP server
        """
        self.config = server_config
        self.name = server_config.name
        self.transport_type = server_config.transport.type
        self.client: Optional[Client] = None
        self.session: Optional[ClientSession] = None
        
        logger.info(f"Initialized MCP SDK client for {self.name}")
    
    async def initialize(self) -> None:
        """Initialize the client connection."""
        if self.transport_type == TransportType.STDIO:
            await self._initialize_stdio()
        elif self.transport_type == TransportType.SSE:
            await self._initialize_sse()
        elif self.transport_type == TransportType.HTTP:
            await self._initialize_http()
        else:
            raise ValueError(f"Unsupported transport type: {self.transport_type}")
    
    async def _initialize_stdio(self) -> None:
        """Initialize stdio transport."""
        command = self.config.transport.command
        args = self.config.transport.args or []
        
        if not command:
            raise ValueError(f"Command not specified for STDIO transport of {self.name}")
        
        logger.info(f"Starting subprocess for {self.name}: {command} {' '.join(args)}")
        
        # Create stdio parameters for the official SDK
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=None,  # We could add environment variables from config if needed
        )
        
        # Create and initialize the client
        self.client = Client(server_params)
        await self.client.__aenter__()
    
    async def _initialize_sse(self) -> None:
        """Initialize SSE transport."""
        url = self.config.transport.url
        
        if not url:
            raise ValueError(f"URL not specified for SSE transport of {self.name}")
        
        logger.info(f"Initializing SSE client for {self.name} at {url}")
        
        # Create and initialize the client
        self.client = Client(url)
        await self.client.__aenter__()
    
    async def _initialize_http(self) -> None:
        """Initialize HTTP transport using Streamable HTTP."""
        url = self.config.transport.url
        
        if not url:
            raise ValueError(f"URL not specified for HTTP transport of {self.name}")
        
        logger.info(f"Initializing HTTP client for {self.name} at {url}")
        
        # Check if authentication is required
        auth_info = self.config.transport.auth
        if auth_info and 'client_id' in auth_info and 'api_key' in auth_info:
            # Authenticate and get JWT token
            logger.info(f"Authenticating with {self.name} using provided credentials")
            
            try:
                # Extract base URL from MCP endpoint
                base_url = url.rsplit('/mcp', 1)[0] if '/mcp' in url else url
                auth_url = f"{base_url}/api/auth/token"
                
                # Prepare authentication payload
                payload = {
                    "clientId": auth_info["client_id"],
                    "apiKey": auth_info["api_key"]
                }
                
                # Make authentication request
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.post(auth_url, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        token = data["token"]
                        logger.info(f"Authentication successful for {self.name}")
                        
                        # Create SDK client with authentication header
                        self.client = Client(
                            url, 
                            headers={"Authorization": f"Bearer {token}"}
                        )
                    else:
                        logger.error(f"Authentication failed for {self.name}: {response.status_code} - {response.text}")
                        raise ValueError(f"Authentication failed for {self.name}")
                    
            except Exception as e:
                logger.error(f"Error during authentication for {self.name}: {e}")
                raise
        else:
            # Create client without authentication
            self.client = Client(url)
        
        # Initialize the client
        await self.client.__aenter__()
    
    async def close(self) -> None:
        """Close the client connection."""
        if self.client:
            logger.info(f"Closing client connection for {self.name}")
            await self.client.__aexit__(None, None, None)
            self.client = None
    
    async def call_resource(
        self, resource_name: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call a resource on the MCP server.
        
        Args:
            resource_name: Name of the resource to call
            params: Parameters to pass to the resource
            
        Returns:
            Resource response data
        """
        if not self.client:
            raise RuntimeError(f"Client not initialized for {self.name}")
        
        logger.debug(f"Reading resource {resource_name} with params: {params}")
        
        # Format the resource URI with parameters if needed
        resource_uri = resource_name
        if params:
            # If the resource_name has placeholders like "users://{user_id}", 
            # we need to format it with the params
            # This is a simplistic approach and might need to be enhanced
            for key, value in params.items():
                placeholder = f"{{{key}}}"
                if placeholder in resource_uri:
                    resource_uri = resource_uri.replace(placeholder, str(value))
        
        try:
            # Call the resource using the SDK client
            content, mime_type = await self.client.read_resource(resource_uri)
            
            # Return in a format compatible with the existing implementation
            return {
                "content": content,
                "mime_type": mime_type
            }
        except Exception as e:
            logger.error(f"Error calling resource {resource_name}: {e}")
            return {"error": str(e)}
    
    async def call_tool(
        self, tool_name: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            params: Parameters to pass to the tool
            
        Returns:
            Tool response data
        """
        if not self.client:
            raise RuntimeError(f"Client not initialized for {self.name}")
        
        logger.debug(f"Calling tool {tool_name} with params: {params}")
        
        try:
            # Call the tool using the SDK client
            result = await self.client.call_tool(tool_name, params or {})
            
            # Transform the result to be compatible with the existing implementation
            # The SDK returns a CallToolResult object which we need to convert
            return {
                "text": result.text if hasattr(result, "text") else str(result),
                "mime_type": getattr(result, "mime_type", "text/plain")
            }
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": str(e)}

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools on the MCP server.
        
        Returns:
            List of available tools
        """
        if not self.client:
            raise RuntimeError(f"Client not initialized for {self.name}")
        
        try:
            tools = await self.client.list_tools()
            
            # Convert to the format expected by the existing implementation
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": [
                        {
                            "name": param.name,
                            "description": param.description,
                            "required": param.required
                        }
                        for param in (tool.parameters or [])
                    ]
                }
                for tool in tools
            ]
        except Exception as e:
            logger.error(f"Error listing tools for {self.name}: {e}")
            return []

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources on the MCP server.
        
        Returns:
            List of available resources
        """
        if not self.client:
            raise RuntimeError(f"Client not initialized for {self.name}")
        
        try:
            resources = await self.client.list_resources()
            
            # Convert to the format expected by the existing implementation
            return [
                {
                    "name": resource.name,
                    "description": resource.description,
                    "uri_template": resource.uri_template
                }
                for resource in resources
            ]
        except Exception as e:
            logger.error(f"Error listing resources for {self.name}: {e}")
            return []
