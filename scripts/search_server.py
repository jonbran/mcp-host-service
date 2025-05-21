#!/usr/bin/env python
"""
Sample MCP Server for SearchEngine functionality.

This is a simple implementation of an MCP server that provides search capabilities.
It's designed to run as a web server that can be accessed via Server-Sent Events (SSE).

Usage:
    python search_server.py
"""

import json
import logging
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("search_server")

# Create FastAPI app
app = FastAPI(
    title="Search MCP Server",
    description="MCP Server for search functionality",
)


class SearchEngine:
    """Simple search engine for demonstration."""
    
    def __init__(self):
        """Initialize with some sample data."""
        self.documents = [
            {
                "id": "doc1",
                "title": "Introduction to MCP",
                "content": "The Model Context Protocol (MCP) is a standardized way for models to interact with external data sources and tools.",
            },
            {
                "id": "doc2",
                "title": "Python Programming",
                "content": "Python is a high-level, interpreted programming language known for its readability and versatility.",
            },
            {
                "id": "doc3",
                "title": "Machine Learning Basics",
                "content": "Machine learning is a subset of artificial intelligence focusing on creating systems that learn from data.",
            },
            {
                "id": "doc4",
                "title": "Natural Language Processing",
                "content": "NLP combines linguistics, computer science, and AI to enable computers to process human language.",
            },
            {
                "id": "doc5",
                "title": "RESTful API Design",
                "content": "REST (Representational State Transfer) is an architectural style for designing networked applications.",
            },
        ]
    
    def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search for documents containing the query.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of matching documents
        """
        if not query:
            return []
        
        # Very simple search implementation
        query = query.lower()
        results = []
        
        for doc in self.documents:
            score = 0
            if query in doc["title"].lower():
                score += 2
            if query in doc["content"].lower():
                score += 1
            
            if score > 0:
                results.append({
                    "id": doc["id"],
                    "title": doc["title"],
                    "snippet": doc["content"][:100] + "...",
                    "score": score,
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]


# Initialize search engine
search_engine = SearchEngine()


@app.post("/search-mcp")
async def search_mcp(request: Request):
    """Handle MCP requests.
    
    This endpoint accepts MCP requests and returns responses.
    """
    try:
        # Parse the request
        data = await request.json()
        
        request_type = data.get("type")
        name = data.get("name")
        params = data.get("params", {})
        
        logger.info(f"Received {request_type} request for {name}")
        
        # Handle the request
        if request_type == "resource":
            response = handle_resource(name, params)
        elif request_type == "tool":
            response = handle_tool(name, params)
        else:
            logger.warning(f"Unsupported request type: {request_type}")
            response = {"error": f"Unsupported request type: {request_type}"}
        
        # Return the response
        return response
    
    except Exception as e:
        logger.exception(f"Error handling request: {e}")
        return {"error": f"Server error: {str(e)}"}


def handle_resource(name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle a resource request.
    
    Args:
        name: Resource name
        params: Resource parameters
        
    Returns:
        Resource data
    """
    if name == "search_results":
        query = params.get("query", "")
        max_results = params.get("max_results", 3)
        
        results = search_engine.search(query, max_results)
        return {"results": results}
    
    elif name == "available_resources":
        return {"resources": ["search_results"]}
    
    else:
        logger.warning(f"Unknown resource: {name}")
        return {"error": f"Unknown resource: {name}"}


def handle_tool(name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle a tool request.
    
    Args:
        name: Tool name
        params: Tool parameters
        
    Returns:
        Tool result
    """
    if name == "search":
        query = params.get("query", "")
        max_results = params.get("max_results", 3)
        
        results = search_engine.search(query, max_results)
        return {
            "query": query,
            "results": results,
        }
    
    elif name == "available_tools":
        return {"tools": ["search"]}
    
    else:
        logger.warning(f"Unknown tool: {name}")
        return {"error": f"Unknown tool: {name}"}


if __name__ == "__main__":
    uvicorn.run(
        "search_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
