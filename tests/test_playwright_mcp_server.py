import pytest
import asyncio
import httpx

@pytest.mark.asyncio
async def test_playwright_mcp_server():
    """Test the Playwright MCP server integration."""
    # Define the base URL for the API
    base_url = "http://localhost:8001/api"

    # Step 1: Verify Playwright is listed in the /models endpoint
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/models")
        assert response.status_code == 200, "Failed to fetch models"

        models_data = response.json()
        assert "providers" in models_data, "No providers found in response"

        providers = [provider["name"] for provider in models_data["providers"]]
        assert "Playwright" in providers, "Playwright MCP server is not listed as a provider"

    # Step 2: Send a sample request to the Playwright MCP server
    sample_request = {
        "type": "tool",
        "name": "screenshot",
        "params": {
            "url": "https://example.com",
            "output_path": "example_screenshot.png"
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{base_url}/playwright", json=sample_request)
        assert response.status_code == 200, "Failed to interact with Playwright MCP server"

        response_data = response.json()
        assert "result" in response_data, "No result found in Playwright response"
        assert response_data["result"] == "success", "Playwright MCP server did not return success"

        # Verify additional data if needed
        assert "output_path" in response_data, "Output path not found in response"
        assert response_data["output_path"] == "example_screenshot.png", "Output path mismatch"
