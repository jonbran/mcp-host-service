#!/usr/bin/env python
"""
Sample MCP Server for WebScraper functionality.

This is a simple implementation of an MCP server that provides web scraping capabilities.
It communicates using the STDIO transport method (reading from stdin, writing to stdout).

Usage:
    python webscraper_server.py
"""

import json
import logging
import sys
from typing import Any, Dict, Optional

import httpx

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="webscraper_server.log",
)
logger = logging.getLogger("webscraper_server")


class WebScraperServer:
    """MCP server for web scraping capabilities."""

    def __init__(self):
        """Initialize the server."""
        self.client = httpx.Client(timeout=30.0)
        logger.info("WebScraper server initialized")

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP request.
        
        Args:
            request: The MCP request to handle
            
        Returns:
            Response data
        """
        request_type = request.get("type")
        name = request.get("name")
        params = request.get("params", {})
        
        logger.info(f"Received {request_type} request for {name}")
        
        if request_type == "resource":
            return self._handle_resource(name, params)
        elif request_type == "tool":
            return self._handle_tool(name, params)
        else:
            logger.warning(f"Unsupported request type: {request_type}")
            return {"error": f"Unsupported request type: {request_type}"}
    
    def _handle_resource(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a resource request.
        
        Args:
            name: Resource name
            params: Resource parameters
            
        Returns:
            Resource data
        """
        if name == "webpage":
            return self._get_webpage(params.get("url"))
        elif name == "available_resources":
            return {"resources": ["webpage"]}
        else:
            logger.warning(f"Unknown resource: {name}")
            return {"error": f"Unknown resource: {name}"}
    
    def _handle_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a tool request.
        
        Args:
            name: Tool name
            params: Tool parameters
            
        Returns:
            Tool result
        """
        if name == "extract_text":
            return self._extract_text(params.get("html"), params.get("selector"))
        elif name == "search_text":
            return self._search_text(
                params.get("html"), params.get("query")
            )
        elif name == "available_tools":
            return {"tools": ["extract_text", "search_text"]}
        else:
            logger.warning(f"Unknown tool: {name}")
            return {"error": f"Unknown tool: {name}"}
    
    def _get_webpage(self, url: Optional[str]) -> Dict[str, Any]:
        """Get a webpage.
        
        Args:
            url: URL to fetch
            
        Returns:
            Webpage content
        """
        if not url:
            return {"error": "URL is required"}
        
        try:
            logger.info(f"Fetching webpage: {url}")
            response = self.client.get(
                url,
                headers={"User-Agent": "MCP-WebScraper/1.0"},
            )
            response.raise_for_status()
            
            return {
                "url": url,
                "status_code": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "html": response.text,
            }
        except Exception as e:
            logger.exception(f"Error fetching webpage {url}: {e}")
            return {"error": str(e)}
    
    def _extract_text(
        self, html: Optional[str], selector: Optional[str]
    ) -> Dict[str, Any]:
        """Extract text from HTML using a CSS selector.
        
        Args:
            html: HTML content
            selector: CSS selector
            
        Returns:
            Extracted text
        """
        if not html:
            return {"error": "HTML content is required"}
        
        if not selector:
            return {"error": "CSS selector is required"}
        
        try:
            # Simple implementation - in a real server, use a proper HTML parser
            import re
            
            # Very basic extraction - this is just for demonstration
            if selector == "title":
                match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
                if match:
                    return {"text": match.group(1).strip()}
            
            return {"text": "Text extraction not fully implemented in this demo"}
        except Exception as e:
            logger.exception(f"Error extracting text: {e}")
            return {"error": str(e)}
    
    def _search_text(
        self, html: Optional[str], query: Optional[str]
    ) -> Dict[str, Any]:
        """Search for text in HTML content.
        
        Args:
            html: HTML content
            query: Search query
            
        Returns:
            Search results
        """
        if not html:
            return {"error": "HTML content is required"}
        
        if not query:
            return {"error": "Search query is required"}
        
        try:
            # Simple implementation - in a real server, use a proper HTML parser
            import re
            
            # Case-insensitive search
            matches = re.findall(
                rf"{re.escape(query)}", html, re.IGNORECASE
            )
            
            return {
                "query": query,
                "match_count": len(matches),
                "matches": matches[:10],  # Limit to first 10 matches
            }
        except Exception as e:
            logger.exception(f"Error searching text: {e}")
            return {"error": str(e)}


def main():
    """Main entry point for the server."""
    server = WebScraperServer()
    
    logger.info("WebScraper server started")
    
    while True:
        try:
            # Read a line from stdin
            line = sys.stdin.readline()
            if not line:
                logger.info("Received EOF, exiting")
                break
            
            # Parse the JSON request
            request = json.loads(line)
            
            # Handle the request
            response = server.handle_request(request)
            
            # Write the response as JSON
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            response = {"error": f"Invalid JSON: {str(e)}"}
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            response = {"error": f"Server error: {str(e)}"}
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
