"""MCP Client implementation for connecting to MCP Servers."""

import asyncio
import json
import logging
import subprocess
from typing import Any, Dict, List, Optional

import httpx

from app.config.config import MCPServerConfig, TransportType

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for connecting to MCP Servers."""

    def __init__(self, server_config: MCPServerConfig):
        """Initialize MCP client.
        
        Args:
            server_config: Configuration for the MCP server
        """
        self.config = server_config
        self.name = server_config.name
        self.transport_type = server_config.transport.type
        self.process = None
        self.client = None
        
        logger.info(f"Initialized MCP client for {self.name}")
    
    async def initialize(self) -> None:
        """Initialize the client connection."""
        if self.transport_type == TransportType.STDIO:
            await self._initialize_stdio()
        elif self.transport_type == TransportType.SSE:
            await self._initialize_sse()
        else:
            raise ValueError(f"Unsupported transport type: {self.transport_type}")
    
    async def _initialize_stdio(self) -> None:
        """Initialize stdio transport."""
        command = self.config.transport.command
        args = self.config.transport.args or []
        
        if not command:
            raise ValueError(f"Command not specified for STDIO transport of {self.name}")
        
        logger.info(f"Starting subprocess for {self.name}: {command} {' '.join(args)}")
        
        # Start the subprocess
        self.process = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        # Initialize with configuration if available
        if self.config.config:
            logger.info(f"Initializing {self.name} with configuration: {self.config.config}")
    
    async def _initialize_sse(self) -> None:
        """Initialize SSE transport."""
        url = self.config.transport.url
        
        if not url:
            raise ValueError(f"URL not specified for SSE transport of {self.name}")
        
        logger.info(f"Initializing SSE client for {self.name} at {url}")
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self) -> None:
        """Close the client connection."""
        if self.transport_type == TransportType.STDIO and self.process:
            logger.info(f"Terminating subprocess for {self.name}")
            try:
                self.process.terminate()
                await self.process.wait()
            except ProcessLookupError:
                logger.info(f"Process for {self.name} already terminated")
            except Exception as e:
                logger.error(f"Error terminating process for {self.name}: {e}")
        
        elif self.transport_type == TransportType.SSE and self.client:
            logger.info(f"Closing HTTP client for {self.name}")
            await self.client.aclose()
    
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
        request = {
            "type": "resource",
            "name": resource_name,
            "params": params or {},
        }
        
        return await self._send_request(request)
    
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
        request = {
            "type": "tool",
            "name": tool_name,
            "params": params or {},
        }
        
        return await self._send_request(request)
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server.
        
        Args:
            request: Request data
            
        Returns:
            Response data
        """
        if self.transport_type == TransportType.STDIO:
            return await self._send_stdio_request(request)
        elif self.transport_type == TransportType.SSE:
            return await self._send_sse_request(request)
        else:
            raise ValueError(f"Unsupported transport type: {self.transport_type}")
    
    async def _send_stdio_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request via stdio transport.
        
        Args:
            request: Request data
            
        Returns:
            Response data
        """
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError(f"STDIO process not initialized for {self.name}")
        
        # Send request
        request_json = json.dumps(request) + "\n"
        logger.debug(f"Sending request to {self.name}: {request_json}")
        
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        response_json = response_line.decode().strip()
        logger.debug(f"Received response from {self.name}: {response_json}")
        
        return json.loads(response_json)
    
    async def _send_sse_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request via SSE transport.
        
        Args:
            request: Request data
            
        Returns:
            Response data
        """
        if not self.client:
            raise RuntimeError(f"SSE client not initialized for {self.name}")
        
        url = self.config.transport.url
        if not url:
            raise ValueError(f"URL not specified for SSE transport of {self.name}")
        
        logger.debug(f"Sending request to {self.name} at {url}: {request}")
        
        response = await self.client.post(
            url,
            json=request,
            headers={"Content-Type": "application/json"},
        )
        
        response.raise_for_status()
        data = response.json()
        
        logger.debug(f"Received response from {self.name}: {data}")
        
        return data
