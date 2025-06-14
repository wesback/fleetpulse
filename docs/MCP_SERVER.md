# FleetPulse MCP Server Documentation

This document provides detailed information about the FleetPulse Model Context Protocol (MCP) server implementation.

## Overview

The FleetPulse MCP server exposes read-only access to package update tracking data through the standardized MCP protocol. This enables AI assistants and other MCP clients to query fleet information in a structured, consistent way.

## Architecture

### Components

1. **MCP Server** (`fleetpulse_mcp/server.py`)
   - Main server implementation using the `mcp` Python package
   - Handles tool registration and request routing
   - Provides stdio transport for MCP communication

2. **Tools** (`fleetpulse_mcp/tools/`)
   - Individual tool implementations for each API endpoint
   - Input validation and error handling
   - JSON response formatting for AI consumption

3. **Configuration** (`fleetpulse_mcp/config/settings.py`)
   - Environment-based configuration management
   - Connection settings for FastAPI backend
   - Server behavior customization

### Data Flow

```
AI Assistant/MCP Client
         ↓ (MCP Protocol over stdio)
FleetPulse MCP Server
         ↓ (HTTP requests)
FastAPI Backend
         ↓ (SQL queries)
SQLite Database
```

## Tool Reference

### fleetpulse_list_hosts

**Purpose:** Get a list of all hosts that have reported package updates.

**Parameters:** None

**Returns:**
```json
{
  "hosts": ["host1", "host2", "host3"],
  "total_count": 3,
  "message": "Found 3 host(s) that have reported updates"
}
```

**Example Usage:**
- "Show me all hosts in the fleet"
- "List all systems reporting to FleetPulse"

### fleetpulse_get_host_history

**Purpose:** Get package update history for a specific host with optional filtering.

**Parameters:**
- `hostname` (required): The hostname to query
- `date_from` (optional): Start date in YYYY-MM-DD format
- `date_to` (optional): End date in YYYY-MM-DD format
- `os` (optional): Filter by operating system
- `package` (optional): Filter by package name (partial matching)
- `limit` (optional): Number of items per page (1-1000, default: 50)
- `offset` (optional): Number of items to skip (default: 0)

**Returns:**
```json
{
  "hostname": "web-server-01",
  "update_history": [
    {
      "id": 1,
      "hostname": "web-server-01",
      "os": "ubuntu",
      "update_date": "2025-06-14",
      "name": "nginx",
      "old_version": "1.18.0",
      "new_version": "1.20.1"
    }
  ],
  "pagination": {
    "total_items": 1,
    "returned_items": 1,
    "limit": 50,
    "offset": 0,
    "has_more": false
  },
  "filters_applied": {
    "date_from": null,
    "date_to": null,
    "os": null,
    "package": null
  },
  "message": "Found 1 total update(s) for host 'web-server-01', showing 1 item(s)"
}
```

**Example Usage:**
- "Get nginx updates for web-server-01 this week"
- "Show all package updates for database-01 since June 1st"
- "Find curl updates across all Ubuntu hosts"

### fleetpulse_get_last_updates

**Purpose:** Get the last update date and OS information for each host.

**Parameters:** None

**Returns:**
```json
{
  "hosts": [
    {
      "hostname": "web-server-01",
      "os": "ubuntu",
      "last_update": "2025-06-14"
    },
    {
      "hostname": "db-server-01",
      "os": "centos",
      "last_update": "2025-06-13"
    }
  ],
  "total_count": 2,
  "summary": {
    "most_recent_update": "2025-06-14",
    "oldest_update": "2025-06-13"
  },
  "message": "Found last update information for 2 host(s)"
}
```

**Example Usage:**
- "Which hosts haven't updated recently?"
- "Show me the last update date for each system"
- "Find systems that might need attention"

### fleetpulse_check_health

**Purpose:** Check the health status of the FleetPulse backend API.

**Parameters:** None

**Returns:**
```json
{
  "http_status": 200,
  "http_status_text": "OK",
  "backend_health": {
    "status": "healthy",
    "database": "connected",
    "telemetry": {
      "enabled": true,
      "service_name": "fleetpulse-backend",
      "service_version": "1.0.0",
      "environment": "development",
      "exporter_type": "jaeger"
    }
  },
  "api_endpoint": "http://localhost:8000/health",
  "timestamp": "2025-06-14T15:39:43.141685Z",
  "overall_status": "healthy",
  "message": "FleetPulse backend is healthy and operational"
}
```

**Example Usage:**
- "Is FleetPulse working properly?"
- "Check system health before querying data"
- "Verify backend connectivity"

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLEETPULSE_API_HOST` | `localhost` | FastAPI backend hostname |
| `FLEETPULSE_API_PORT` | `8000` | FastAPI backend port |
| `MCP_SERVER_NAME` | `FleetPulse MCP Server` | MCP server identification name |
| `MCP_SERVER_VERSION` | `1.0.0` | MCP server version |
| `MCP_REQUEST_TIMEOUT` | `30.0` | HTTP request timeout in seconds |
| `MCP_DEBUG` | `false` | Enable debug logging |

### Configuration Examples

**Development:**
```bash
export MCP_DEBUG=true
export MCP_REQUEST_TIMEOUT=10.0
```

**Production:**
```bash
export FLEETPULSE_API_HOST=fleetpulse-api.company.com
export FLEETPULSE_API_PORT=443
export MCP_REQUEST_TIMEOUT=60.0
export MCP_DEBUG=false
```

## Error Handling

### Common Error Scenarios

1. **Backend Unavailable**
   - Timeout errors return structured responses with timeout status
   - Connection failures provide clear error messages

2. **Invalid Parameters**
   - Parameter validation occurs before API calls
   - Descriptive error messages indicate the specific issue

3. **No Data Found**
   - Empty results return appropriate "no data" messages
   - 404 errors from backend are handled gracefully

### Error Response Format

```json
{
  "error": "Description of the error",
  "tool": "tool_name",
  "arguments": { "provided": "arguments" }
}
```

## Testing

### Unit Tests

Located in `tests/backend/mcp/test_mcp_tools.py` - focused on individual tool logic with mocked HTTP responses.

### Integration Tests

Located in `tests/backend/mcp/test_mcp_integration.py` - tests against actual running FastAPI backend.

**Running Tests:**
```bash
# All MCP tests
pytest tests/backend/mcp/ -v

# Integration tests only (requires running backend)
pytest tests/backend/mcp/test_mcp_integration.py -v

# Specific test
pytest tests/backend/mcp/test_mcp_integration.py::TestMCPIntegration::test_health_tool_integration -v
```

### Manual Testing

Test tools directly:
```bash
cd backend

# Test health
python -c "
import asyncio
from fleetpulse_mcp.tools.health_tool import check_health
result = asyncio.run(check_health())
print(result)
"

# Test with actual host data
python -c "
import asyncio
from fleetpulse_mcp.tools.history_tool import get_host_history
result = asyncio.run(get_host_history('actual-hostname', limit=5))
print(result)
"
```

## Deployment Considerations

### Prerequisites

1. **FastAPI Backend Running**
   - MCP server requires active FastAPI backend
   - Configure connection settings via environment variables

2. **Python Dependencies**
   - MCP package (`mcp==1.0.0`)
   - HTTP client (`httpx`)
   - All FastAPI backend dependencies

### Production Deployment

1. **Process Management**
   ```bash
   # Using systemd service
   [Unit]
   Description=FleetPulse MCP Server
   After=fleetpulse-backend.service
   Requires=fleetpulse-backend.service

   [Service]
   Type=simple
   User=fleetpulse
   WorkingDirectory=/opt/fleetpulse/backend
   ExecStart=/opt/fleetpulse/venv/bin/python start_mcp_server.py
   Restart=always
   Environment=FLEETPULSE_API_HOST=localhost
   Environment=FLEETPULSE_API_PORT=8000

   [Install]
   WantedBy=multi-user.target
   ```

2. **Docker Deployment**
   ```dockerfile
   FROM python:3.12-slim
   
   WORKDIR /app
   COPY backend/requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY backend/ .
   
   ENV FLEETPULSE_API_HOST=fleetpulse-backend
   ENV FLEETPULSE_API_PORT=8000
   
   CMD ["python", "start_mcp_server.py"]
   ```

### Monitoring

Monitor MCP server health by:
- Checking process status
- Monitoring log output for errors
- Testing tool functionality periodically
- Verifying FastAPI backend connectivity

## Security Considerations

### Current Security Model

- **Read-only access**: No write operations exposed
- **No authentication**: Direct API access (FastAPI handles any auth)
- **Local communication**: Default configuration uses localhost

### Future Security Enhancements

- Authentication/authorization for MCP clients
- Rate limiting and request validation
- Audit logging for tool usage
- Encrypted communication channels

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure Python path includes backend directory
   - Check virtual environment activation

2. **Connection timeouts**
   - Verify FastAPI backend is running
   - Check network connectivity
   - Adjust `MCP_REQUEST_TIMEOUT` if needed

3. **Import errors**
   - Verify MCP package installation: `pip list | grep mcp`
   - Check Python version compatibility (3.8+)

4. **JSON parsing errors**
   - Usually indicates FastAPI backend errors
   - Check backend logs for root cause

### Debug Mode

Enable debug logging:
```bash
export MCP_DEBUG=true
python start_mcp_server.py
```

This provides detailed information about:
- HTTP requests to FastAPI backend
- Response processing
- Error details and stack traces

## Future Development

### Planned Features

1. **Write Operations**
   - Tool for submitting package updates via MCP
   - Bulk operations support

2. **Enhanced Filtering**
   - Advanced query capabilities
   - Saved filter templates

3. **Streaming Responses**
   - Large dataset handling
   - Real-time update notifications

4. **Multi-backend Support**
   - Load balancing across multiple FastAPI instances
   - Failover capabilities

### Contributing

To contribute to MCP server development:

1. Follow existing code patterns in `fleetpulse_mcp/`
2. Add tests for new functionality
3. Update documentation
4. Ensure compatibility with MCP specification

For detailed contribution guidelines, see the main project README.