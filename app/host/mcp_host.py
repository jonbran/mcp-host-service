"""MCP Host implementation using the official MCP SDK."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from app.config.config import AppConfig, MCPServerConfig
from app.host.mcp_client import MCPSdkClient
from app.model.model import ModelService
from app.utils.model_mcp import (
    create_mcp_system_prompt,
    extract_mcp_requests_from_text,
    format_mcp_results_for_model,
)

logger = logging.getLogger(__name__)


class MCPSdkHost:
    """Host for MCP protocol implementation using the official MCP SDK."""

    def __init__(self, config: AppConfig, model_service: ModelService):
        """Initialize MCP host.
        
        Args:
            config: Application configuration
            model_service: Model service for inference
        """
        self.config = config
        self.model_service = model_service
        self.clients: Dict[str, MCPSdkClient] = {}
        self.available_resources: Dict[str, Set[str]] = {}
        self.available_tools: Dict[str, Set[str]] = {}
        
        logger.info("Initialized MCP SDK host")
    
    async def initialize(self) -> None:
        """Initialize MCP host and clients."""
        # Initialize clients for all configured MCP servers
        for server_config in self.config.mcp.mcp_servers:
            await self._initialize_client(server_config)
        
        logger.info(f"Initialized {len(self.clients)} MCP clients")
    
    async def _initialize_client(self, server_config: MCPServerConfig) -> None:
        """Initialize a client for an MCP server.
        
        Args:
            server_config: Configuration for the MCP server
        """
        client = MCPSdkClient(server_config)
        await client.initialize()
        
        self.clients[server_config.name] = client
        
        # Fetch available resources and tools from the server
        try:
            resources = await client.list_resources()
            self.available_resources[server_config.name] = {r["name"] for r in resources}
            
            tools = await client.list_tools()
            self.available_tools[server_config.name] = {t["name"] for t in tools}
            
            logger.info(f"Discovered {len(resources)} resources and {len(tools)} tools for {server_config.name}")
        except Exception as e:
            logger.warning(f"Could not fetch capabilities from {server_config.name}: {e}")
    
    async def close(self) -> None:
        """Close all client connections."""
        for name, client in self.clients.items():
            logger.info(f"Closing client connection for {name}")
            await client.close()
    
    async def process_message(
        self, message: str, conversation_history: List[Dict[str, Any]] = None, provider_name: Optional[str] = "anthropic"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Process a user message and generate a response.
        
        This method handles:
        1. Sending the message to the model
        2. Interpreting model requests for MCP resources/tools
        3. Fetching data from MCP servers as needed
        4. Generating the final response
        
        Args:
            message: User message
            conversation_history: Previous conversation history
            provider_name: Optional provider name to use (defaults to anthropic)
            
        Returns:
            Tuple of (response text, updated conversation history)
        """
        if conversation_history is None:
            conversation_history = []
        
        # If this is the first message, add a system prompt to guide MCP usage
        if not conversation_history:
            conversation_history.append({
                "role": "system",
                "content": create_mcp_system_prompt(),
            })
        
        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": message,
        })
        
        # Process the message with the model, handling any MCP requests
        response, updated_history = await self._process_with_model(conversation_history, provider_name)
        
        return response, updated_history
    
    async def _process_with_model(
        self, conversation_history: List[Dict[str, Any]], provider_name: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Process conversation with the model, handling MCP requests.
        
        Args:
            conversation_history: Conversation history
            provider_name: Optional provider name to use
            
        Returns:
            Tuple of (response text, updated conversation history)
        """
        # Initial model call with the conversation history
        response = await self.model_service.generate_response(conversation_history, provider_name)
        
        # Check if the response contains MCP requests
        cleaned_response, mcp_requests = extract_mcp_requests_from_text(response)
        
        # If there are MCP requests, fulfill them and call the model again
        if mcp_requests:
            logger.info(f"Found {len(mcp_requests)} MCP requests in model output")
            
            # Fulfill MCP requests
            mcp_results = await self._fulfill_mcp_requests(mcp_requests)
            
            # Format results for the model
            results_text = format_mcp_results_for_model(mcp_results)
            
            # Add MCP results to history
            conversation_history.append({
                "role": "system",
                "content": results_text,
            })
            
            # Call model again with updated history
            response = await self.model_service.generate_response(conversation_history, provider_name)
            
            # Clean up any remaining MCP requests
            cleaned_response, _ = extract_mcp_requests_from_text(response)
            response = cleaned_response
        else:
            response = cleaned_response
        
        # Add assistant response to history
        conversation_history.append({
            "role": "assistant",
            "content": response,
        })
        
        return response, conversation_history
    
    async def _fulfill_mcp_requests(
        self, requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fulfill MCP requests by calling appropriate MCP servers.
        
        Args:
            requests: List of MCP requests
            
        Returns:
            Dictionary of request results
        """
        results = {}
        
        for request in requests:
            request_type = request.get("type")
            server_name = request.get("server")
            name = request.get("name")
            params = request.get("params", {})
            
            if not all([request_type, server_name, name]):
                logger.warning(f"Invalid MCP request: {request}")
                continue
            
            client = self.clients.get(server_name)
            if not client:
                logger.warning(f"MCP server not found: {server_name}")
                continue
            
            try:
                if request_type == "resource":
                    result = await client.call_resource(name, params)
                elif request_type == "tool":
                    result = await client.call_tool(name, params)
                else:
                    logger.warning(f"Unsupported MCP request type: {request_type}")
                    continue
                
                request_id = request.get("id", f"{server_name}_{name}")
                results[request_id] = result
                
            except Exception as e:
                logger.exception(f"Error fulfilling MCP request: {e}")
                results[f"{server_name}_{name}_error"] = str(e)
        
        return results
    
    def get_server_capabilities(self) -> Dict[str, Dict[str, List[str]]]:
        """Get capabilities of all connected MCP servers.
        
        Returns:
            Dictionary mapping server names to their capabilities
        """
        capabilities = {}
        
        for server_name in self.clients:
            capabilities[server_name] = {
                "resources": list(self.available_resources.get(server_name, set())),
                "tools": list(self.available_tools.get(server_name, set()))
            }
        
        return capabilities
