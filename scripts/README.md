# MCP Sample Servers

This directory contains sample MCP (Model Context Protocol) servers that can be used for testing and development of the MCP Host service.

## Available Servers

### WebScraper Server

A simple MCP server that provides web scraping capabilities. It supports:

**Resources:**

- `webpage` - Get the HTML content of a webpage

**Tools:**

- `extract_text` - Extract text from HTML using a CSS selector
- `search_text` - Search for text within HTML content

### SearchEngine Server

A simple MCP server that provides search capabilities. It supports:

**Resources:**

- `search_results` - Get search results for a query

**Tools:**

- `search` - Search for documents containing a query

## Usage

### Starting the Servers

You can start the servers using the provided `start_services.py` script:

```bash
# Start the WebScraper server
python scripts/start_services.py --webscraper

# Start the SearchEngine server
python scripts/start_services.py --searchengine

# Start all servers
python scripts/start_services.py --all
```

### Direct Server Usage

You can also start the servers directly:

```bash
# Start the WebScraper server
python scripts/webscraper_server.py

# Start the SearchEngine server
uvicorn scripts.search_server:app --host 0.0.0.0 --port 8002
```

## MCP Protocol

These servers implement the MCP (Model Context Protocol) to allow the model to interact with external data sources and tools.

### Request Format

Requests to MCP servers follow this general format:

```json
{
  "type": "resource|tool",
  "name": "resource_or_tool_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

### Response Format

Responses from MCP servers will include the requested data or tool result:

```json
{
  "result": "...",
  "additionalData": "..."
}
```

## Example Requests

### WebScraper: Get a Webpage

```json
{
  "type": "resource",
  "name": "webpage",
  "params": {
    "url": "https://example.com"
  }
}
```

### SearchEngine: Search

```json
{
  "type": "tool",
  "name": "search",
  "params": {
    "query": "machine learning",
    "max_results": 5
  }
}
```

## Extending

You can create additional MCP servers by following the same pattern as these examples. Each server should:

1. Accept MCP requests in the standardized format
2. Process the requests according to its capabilities
3. Return responses in a structured format
4. Support both resource and tool types as appropriate

For more information about the MCP protocol, refer to the [Model Context Protocol documentation](https://github.com/anthropics/anthropic-cookbook/tree/main/model_context_protocol).
