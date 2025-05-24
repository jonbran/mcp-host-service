# Playwright MCP Server Integration

This document provides instructions for integrating and using the Playwright MCP server with the MCP Host.

## Table of Contents

- [Overview](#overview)
- [Configuration](#configuration)
- [Running the Playwright MCP Server](#running-the-playwright-mcp-server)
- [Available Tools](#available-tools)
- [Usage Examples](#usage-examples)
- [Testing](#testing)

## Overview

The Playwright MCP server provides web automation capabilities through the Model Context Protocol (MCP). It allows models to interact with web browsers to perform various tasks such as:

- Taking screenshots
- Extracting content
- Interacting with web elements
- Testing web applications

## Configuration

The Playwright MCP server is configured in `config/config.json` under the `mcp_servers` section:

```json
{
  "name": "Playwright",
  "transport": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@executeautomation/playwright-mcp-server"]
  },
  "config": {
    "mode": "snapshot"
  }
}
```

### Setting the Mode

The Playwright MCP server can operate in two modes:

- `snapshot` (default): For stateless, one-off interactions with web pages
- `vision`: For interactive, stateful browser automation sequences

To change the mode, update the `mode` parameter in the `config` section of the Playwright MCP server configuration, or use the provided script:

```bash
# Switch to Snapshot mode (default)
python scripts/set_playwright_mode.py snapshot

# Switch to Vision mode
python scripts/set_playwright_mode.py vision
```

## Running the Playwright MCP Server

The Playwright MCP server is automatically started when the MCP host service is launched.

To manually start the server, you can use:

```bash
npx -y @executeautomation/playwright-mcp-server
```

Or use the helper function in `scripts/start_services.py`:

```bash
python -c "from scripts.start_services import start_playwright_server; start_playwright_server()"
```

## Available Tools

The Playwright MCP server operates in two modes:

### 1. Snapshot Mode (Default)

In Snapshot mode, the Playwright MCP server provides tools for static interaction with web pages:

| Tool            | Description                        | Parameters                   |
| --------------- | ---------------------------------- | ---------------------------- |
| `screenshot`    | Captures a screenshot of a URL     | `url`, `output_path`         |
| `extract_text`  | Extracts text content from a URL   | `url`, `selector` (optional) |
| `extract_html`  | Extracts HTML content from a URL   | `url`, `selector` (optional) |
| `extract_links` | Extracts links from a URL          | `url`, `selector` (optional) |
| `find_elements` | Finds elements matching a selector | `url`, `selector`            |
| `get_title`     | Gets the page title                | `url`                        |

### 2. Vision Mode

In Vision mode, the Playwright MCP server provides tools for more interactive automation:

| Tool                | Description                        | Parameters                                       |
| ------------------- | ---------------------------------- | ------------------------------------------------ |
| `launch_browser`    | Launches a browser session         | `browser_type` (optional), `headless` (optional) |
| `navigate`          | Navigates to a URL                 | `url`                                            |
| `click`             | Clicks an element                  | `selector`                                       |
| `type`              | Types text into an element         | `selector`, `text`                               |
| `get_text`          | Gets text from an element          | `selector`                                       |
| `wait_for_selector` | Waits for an element to be visible | `selector`, `timeout_ms` (optional)              |
| `take_screenshot`   | Takes a screenshot                 | `output_path`, `full_page` (optional)            |
| `close_browser`     | Closes the browser                 | None                                             |

## Usage Examples

### API Usage

You can interact with the Playwright MCP server through the `/api/playwright` endpoint:

```python
import httpx

async def take_screenshot(url: str, output_path: str):
    """Take a screenshot of a URL using Playwright MCP server."""
    request = {
        "type": "tool",
        "name": "screenshot",
        "params": {
            "url": url,
            "output_path": output_path
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:8001/api/playwright", json=request)
        return response.json()

# Example usage
result = await take_screenshot("https://example.com", "example_screenshot.png")
print(result)
```

### Interactive Session Example

For more complex interactions, you can use multiple tool calls in sequence:

```python
import httpx
import asyncio

async def automate_form_submission():
    """Automate form submission using Playwright MCP server."""
    base_url = "http://localhost:8001/api/playwright"
    async with httpx.AsyncClient() as client:
        # Step 1: Launch browser
        response = await client.post(base_url, json={
            "type": "tool",
            "name": "launch_browser",
            "params": {"headless": False}
        })
        print("Browser launched:", response.json())

        # Step 2: Navigate to website
        response = await client.post(base_url, json={
            "type": "tool",
            "name": "navigate",
            "params": {"url": "https://example.com/form"}
        })
        print("Navigated to form:", response.json())

        # Step 3: Fill form fields
        response = await client.post(base_url, json={
            "type": "tool",
            "name": "type",
            "params": {"selector": "#name", "text": "John Doe"}
        })
        print("Filled name field:", response.json())

        # Step 4: Submit form
        response = await client.post(base_url, json={
            "type": "tool",
            "name": "click",
            "params": {"selector": "#submit-button"}
        })
        print("Submitted form:", response.json())

        # Step 5: Take screenshot of result
        response = await client.post(base_url, json={
            "type": "tool",
            "name": "take_screenshot",
            "params": {"output_path": "form_submission_result.png"}
        })
        print("Took screenshot:", response.json())

        # Step 6: Close browser
        response = await client.post(base_url, json={
            "type": "tool",
            "name": "close_browser",
            "params": {}
        })
        print("Browser closed:", response.json())

# Run the automation
asyncio.run(automate_form_submission())
```

## Testing

To test the Playwright MCP server integration, run:

```bash
pytest tests/test_playwright_mcp_server.py -v
```

This test verifies:

1. The Playwright MCP server is properly registered as a provider in the `/api/models` endpoint
2. A basic screenshot tool call works correctly
