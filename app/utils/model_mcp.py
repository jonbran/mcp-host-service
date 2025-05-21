"""Utilities for working with MCP in the model's output."""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def extract_mcp_requests_from_text(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Extract MCP requests from model output text.
    
    This function looks for MCP requests in the format:
    
    ```mcp
    {
        "type": "resource",
        "server": "server_name",
        "name": "resource_name",
        "params": {...}
    }
    ```
    
    Args:
        text: Model output text
        
    Returns:
        Tuple of (cleaned text without MCP markers, list of MCP requests)
    """
    requests = []
    cleaned_text = text
    
    # Pattern to match MCP code blocks
    pattern = r"```mcp\s+([\s\S]*?)```"
    
    # Find all matches
    matches = re.finditer(pattern, text)
    
    for match in matches:
        try:
            # Extract the JSON content
            json_str = match.group(1).strip()
            request = json.loads(json_str)
            
            # Validate the request
            if _validate_mcp_request(request):
                requests.append(request)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in MCP request: {e}")
        except Exception as e:
            logger.warning(f"Error processing MCP request: {e}")
    
    # Remove MCP markers from the text
    if requests:
        cleaned_text = re.sub(pattern, "", text)
        # Clean up any resulting double newlines
        cleaned_text = re.sub(r"\n\s*\n\s*\n", "\n\n", cleaned_text)
    
    return cleaned_text, requests


def _validate_mcp_request(request: Dict[str, Any]) -> bool:
    """Validate an MCP request.
    
    Args:
        request: MCP request to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["type", "server", "name"]
    
    for field in required_fields:
        if field not in request:
            logger.warning(f"Missing required field '{field}' in MCP request")
            return False
    
    valid_types = ["resource", "tool"]
    if request["type"] not in valid_types:
        logger.warning(f"Invalid request type '{request['type']}' in MCP request")
        return False
    
    return True


def create_mcp_system_prompt() -> str:
    """Create a system prompt to guide the model in using MCP.
    
    Returns:
        System prompt text
    """
    return """You are an assistant with access to external tools and data sources via the Model Context Protocol (MCP).

When you need to access external information or use a tool, you can use the MCP format:

```mcp
{
    "type": "resource",
    "server": "WebScraper",
    "name": "webpage",
    "params": {
        "url": "https://example.com"
    }
}
```

Or for tools:

```mcp
{
    "type": "tool",
    "server": "SearchEngine",
    "name": "search",
    "params": {
        "query": "sample search query"
    }
}
```

Available MCP servers:
- WebScraper: Access web content
  - Resources: webpage
  - Tools: extract_text, search_text

- SearchEngine: Search for information
  - Resources: search_results
  - Tools: search

First try to answer from your knowledge. If you need external information, use the appropriate MCP request.
"""


def format_mcp_results_for_model(results: Dict[str, Any]) -> str:
    """Format MCP results to provide as context to the model.
    
    Args:
        results: MCP request results
        
    Returns:
        Formatted results string
    """
    formatted = "Here are the results from the MCP requests:\n\n"
    
    for request_id, result in results.items():
        formatted += f"# {request_id}\n"
        formatted += f"```json\n{json.dumps(result, indent=2)}\n```\n\n"
    
    formatted += "Use this information to formulate your response."
    
    return formatted
