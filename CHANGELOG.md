# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-05-27

### Added

- Integrated official MCP Python SDK (`mcp>=1.9.0`)
- Added support for HTTP transport type with JWT authentication
- Added Scheduler service integration for scheduling future conversations
- Created `MCPSdkClient` and `MCPSdkHost` classes using the official SDK
- Created `SchedulerService` wrapper for easy interaction with the Scheduler
- Added utility scripts:
  - `update_scheduler_config.py` - Updates Scheduler configuration
  - `start_scheduler.py` - Starts the Scheduler service
  - `test_scheduler_mcp.py` - Tests connectivity to the Scheduler
  - `test_scheduler_auth.py` - Tests authentication with the Scheduler
  - `test_mcp_sdk_integration.py` - Tests MCP SDK integration
  - `test_scheduler_integration.py` - Tests the full integration cycle
  - `scheduler_example.py` - Example usage of the SchedulerService
- Updated `start_services.py` to include Scheduler service
- Added comprehensive documentation:
  - `mcp_sdk_integration.md` - MCP SDK integration details
  - `mcp_sdk_integration_summary.md` - Integration summary
  - `scheduler_guide.md` - Scheduler service usage guide

### Changed

- Updated transport configuration to include authentication
- Updated API router to use the new MCP SDK Host
- Modified `TransportType` enum to include HTTP transport

### Fixed

- Improved error handling for server connections
- Fixed URL validation for different transport types

### Deprecated

- Original MCP implementation (still available for backward compatibility)

## [1.0.0] - 2025-04-15

### Added

- Initial release of MCP Host/Client/Service
- Support for multiple model providers (HuggingFace, OpenAI, Anthropic)
- Integration with WebScraper and SearchEngine MCP servers
- Conversation persistence
- REST API for user interaction
- Docker support for containerization
