"""Utility functions for MCP service."""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def format_mcp_request(
    request_type: str,
    server_name: str,
    name: str,
    params: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Format an MCP request.
    
    Args:
        request_type: Type of request (resource/tool)
        server_name: Name of the MCP server
        name: Name of the resource or tool
        params: Parameters for the request
        request_id: Optional request ID
        
    Returns:
        Formatted MCP request dictionary
    """
    request = {
        "type": request_type,
        "server": server_name,
        "name": name,
        "params": params or {},
    }
    
    if request_id:
        request["id"] = request_id
    
    return request


def parse_mcp_marker(text: str) -> Dict[str, Any]:
    """Parse MCP marker from text.
    
    This function extracts MCP markers from text. The format is expected to be:
    
    ```mcp
    {
        "type": "resource",
        "server": "server_name",
        "name": "resource_name",
        "params": {...}
    }
    ```
    
    Args:
        text: Text containing MCP marker
        
    Returns:
        Parsed MCP request dictionary, or empty dict if no marker found
    """
    # Look for MCP markers
    start_marker = "```mcp"
    end_marker = "```"
    
    start_idx = text.find(start_marker)
    if start_idx == -1:
        return {}
    
    start_idx += len(start_marker)
    end_idx = text.find(end_marker, start_idx)
    
    if end_idx == -1:
        return {}
    
    # Extract the JSON
    json_str = text[start_idx:end_idx].strip()
    
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.warning(f"Error parsing MCP marker: {e}")
        return {}
