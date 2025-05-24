"""Router for Playwright MCP server endpoints."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.auth.models import User
from app.auth.utils import get_current_active_user
from app.host.host import MCPHost

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["playwright"])


def get_mcp_host() -> MCPHost:
    """Get the MCP host instance."""
    # This depends on the mcp_host being initialized in the main router
    from app.api.router import mcp_host
    return mcp_host


@router.post(
    "/playwright",
    summary="Interact with Playwright MCP server",
    description="Send requests to the Playwright MCP server"
)
async def call_playwright(
    request: Dict[str, Any],
    mcp_host: MCPHost = Depends(get_mcp_host),
    current_user: User = Depends(get_current_active_user),
):
    """Call Playwright MCP tool.
    
    Args:
        request: Request to send to the Playwright MCP server
        mcp_host: MCP host instance
        current_user: Current authenticated user
        
    Returns:
        Response from the Playwright MCP server
    """
    if not mcp_host.clients.get("Playwright"):
        raise HTTPException(status_code=500, detail="Playwright MCP server not available")
    
    try:
        if request.get("type") == "tool":
            # For tool calls
            tool_name = request.get("name")
            params = request.get("params", {})
            
            if not tool_name:
                raise HTTPException(status_code=400, detail="Tool name not specified")
            
            response = await mcp_host.clients["Playwright"].call_tool(tool_name, params)
            return response
        else:
            # Invalid request type
            raise HTTPException(status_code=400, detail="Invalid request type")
    except Exception as e:
        logger.error(f"Error calling Playwright MCP server: {e}")
        raise HTTPException(status_code=500, detail=f"Error calling Playwright MCP server: {str(e)}")
