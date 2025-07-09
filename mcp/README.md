# FleetPulse MCP Server

A Model Context Protocol (MCP) server that provides read-only access to FleetPulse backend data for AI assistants like Claude.

## Overview

The FleetPulse MCP Server acts as a bridge between AI assistants and the FleetPulse backend API, exposing fleet management data through standardized MCP tools. It provides comprehensive observability with OpenTelemetry instrumentation and robust error handling.

## Features

### Core MCP Tools

1. **Health Check** - Monitor backend and MCP server health status
2. **Host Management** - List hosts and get detailed host information  
3. **Update Reports** - Retrieve package update reports with filtering and pagination
4. **Package Information** - List packages and get package details across the fleet
5. **Fleet Statistics** - Get aggregate statistics and activity metrics
6. **Search** - Search across hosts, packages, and reports

### Technical Features

- **Async HTTP Client** - Non-blocking backend API communication with retry logic
- **OpenTelemetry Instrumentation** - Comprehensive tracing and metrics
- **Configuration Management** - Environment variable-based configuration
- **Error Handling** - Graceful degradation when backend is unavailable
- **Connection Pooling** - Efficient HTTP connection management
- **Request Validation** - Input validation and sanitization

## Architecture

```
┌─────────────────┐    HTTP/MCP     ┌──────────────────┐    HTTP     ┌─────────────────┐
│   AI Assistant  │ ───────────────▶│  FleetPulse MCP  │ ─────────▶ │ FleetPulse      │
│   (Claude, etc) │                 │  Server          │             │ Backend API     │
└─────────────────┘                 └──────────────────┘             └─────────────────┘
                                            │                                │
                                            ▼                                ▼
                                    ┌──────────────────┐              ┌─────────────────┐
                                    │  OpenTelemetry   │              │ SQLite Database │
                                    │  Observability   │              │                 │
                                    └──────────────────┘              └─────────────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- FleetPulse backend running and accessible
- Required Python dependencies (see requirements.txt)

### Dependencies

Install the MCP server dependencies:

```bash
cd mcp/
pip install -r requirements.txt
```

### Configuration

Configure the MCP server using environment variables:

```bash
# Backend connection
export FLEETPULSE_BACKEND_URL="http://localhost:8000"

# MCP server settings  
export MCP_PORT="8001"

# HTTP client settings
export REQUEST_TIMEOUT="30.0"
export MAX_RETRIES="3"

# OpenTelemetry configuration
export OTEL_SERVICE_NAME="fleetpulse-mcp"
export OTEL_SERVICE_VERSION="1.0.0"
export OTEL_ENVIRONMENT="development"
export OTEL_ENABLE_TELEMETRY="true"
export OTEL_EXPORTER_TYPE="console"  # console, jaeger, or otlp
export OTEL_TRACE_SAMPLE_RATE="1.0"

# For Jaeger tracing
export OTEL_EXPORTER_JAEGER_ENDPOINT="http://jaeger:14268/api/traces"

# For OTLP tracing  
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317"
```

### Running the Server

#### Development Mode

```bash
cd mcp/
python main.py
```

#### Production Mode

```bash
cd mcp/
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

#### Docker Mode

```bash
# Build the Docker image
docker build -t fleetpulse-mcp .

# Run the container
docker run -d \
  --name fleetpulse-mcp \
  -p 8001:8001 \
  -e FLEETPULSE_BACKEND_URL=http://backend:8000 \
  fleetpulse-mcp
```

#### Docker Compose Mode

For easy deployment alongside the FleetPulse backend, use Docker Compose:

```bash
# Using the full stack (includes MCP server)
docker-compose up -d

# Using only MCP server with existing backend
docker-compose -f docker-compose.mcp.yml up -d
```

See the [Docker Compose Configuration](#docker-compose-configuration) section for detailed setup instructions.

> **Quick Start**: For step-by-step Docker Compose setup instructions, see [DOCKER_COMPOSE_MCP.md](../DOCKER_COMPOSE_MCP.md)

## Usage

### AI Assistant Integration

The MCP server exposes standardized tools that AI assistants can use to query FleetPulse data:

#### Example Queries

- **"Show me all hosts in the fleet and their last update times"**
  - Uses: `list_hosts` tool
  
- **"What packages were updated on server-01 in the last week?"**
  - Uses: `get_host_reports` tool with hostname filter
  
- **"Which hosts have the nginx package installed?"**
  - Uses: `get_package_details` tool with package_name="nginx"
  
- **"What's the overall health of my FleetPulse system?"**
  - Uses: `health_check` tool
  
- **"Search for any activity related to openssl"**
  - Uses: `search` tool with query="openssl"

### REST API Endpoints

The MCP server also exposes REST endpoints for debugging and direct access:

```bash
# Health check
curl http://localhost:8001/health

# List all hosts
curl http://localhost:8001/hosts

# Get host details
curl http://localhost:8001/hosts/server-01

# Get update reports
curl http://localhost:8001/reports?limit=10

# Get reports for specific host  
curl http://localhost:8001/reports/server-01

# List all packages
curl http://localhost:8001/packages

# Get package details
curl http://localhost:8001/packages/nginx

# Get fleet statistics
curl http://localhost:8001/stats

# Search
curl "http://localhost:8001/search?q=nginx&result_type=package"

# List available tools
curl http://localhost:8001/tools
```

## Claude Desktop Integration

To integrate the FleetPulse MCP server with Claude Desktop, you need to configure Claude Desktop to connect to your MCP server.

### Prerequisites

1. **Claude Desktop App**: Download and install Claude Desktop from [Anthropic's website](https://claude.ai/download)
2. **FleetPulse MCP Server**: Ensure your MCP server is running and accessible
3. **Network Access**: Claude Desktop must be able to reach your MCP server

### Configuration Steps

#### 1. Locate Claude Desktop Configuration

Find your Claude Desktop configuration file:

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

#### 2. Configure MCP Server Connection

Edit the `claude_desktop_config.json` file to add the FleetPulse MCP server:

```json
{
  "mcpServers": {
    "fleetpulse": {
      "command": "python",
      "args": ["-m", "mcp.main"],
      "cwd": "/path/to/your/fleetpulse/mcp",
      "env": {
        "FLEETPULSE_BACKEND_URL": "http://localhost:8000",
        "MCP_PORT": "8001",
        "REQUEST_TIMEOUT": "30.0",
        "MAX_RETRIES": "3",
        "OTEL_ENABLE_TELEMETRY": "false"
      }
    }
  }
}
```

#### 3. Alternative: Remote MCP Server Configuration

If your MCP server is running on a remote host or via Docker, configure it as a remote server:

```json
{
  "mcpServers": {
    "fleetpulse": {
      "command": "stdio",
      "transport": {
        "type": "sse",
        "url": "http://your-mcp-server:8001/sse"
      },
      "env": {}
    }
  }
}
```

#### 4. Docker-based Configuration

For Docker deployments, you can configure Claude Desktop to run the MCP server in a container:

```json
{
  "mcpServers": {
    "fleetpulse": {
      "command": "docker",
      "args": [
        "run", 
        "--rm", 
        "-i",
        "--network", "fleetpulse_default",
        "-e", "FLEETPULSE_BACKEND_URL=http://backend:8000",
        "fleetpulse-mcp:latest",
        "python", "-m", "mcp.main"
      ],
      "env": {}
    }
  }
}
```

### Environment Variables

Configure these environment variables for optimal Claude Desktop integration:

```bash
# Required: Backend connection
FLEETPULSE_BACKEND_URL=http://localhost:8000

# Optional: Performance tuning
REQUEST_TIMEOUT=15.0
MAX_RETRIES=2

# Optional: Disable telemetry for Claude Desktop usage
OTEL_ENABLE_TELEMETRY=false

# Optional: Logging configuration
LOG_LEVEL=INFO
```

### Verification Steps

1. **Start the MCP Server**:
   ```bash
   cd mcp/
   python main.py
   ```

2. **Restart Claude Desktop**: Close and reopen Claude Desktop to load the new configuration

3. **Verify Connection**: In Claude Desktop, try asking questions about your fleet:
   - "Show me all hosts in my fleet"
   - "What packages need updates?"
   - "Check the health of my FleetPulse system"

4. **Check MCP Tools**: Claude should now have access to FleetPulse tools:
   - `health_check`
   - `list_hosts`
   - `get_host_details`
   - `list_packages`
   - `get_package_details`
   - `get_reports`
   - `get_host_reports`
   - `get_fleet_stats`
   - `search`

### Troubleshooting Claude Desktop Integration

**MCP Server Not Found:**
```bash
# Verify Python path and dependencies
which python
pip list | grep mcp

# Check configuration file syntax
python -m json.tool ~/.config/Claude/claude_desktop_config.json
```

**Connection Issues:**
```bash
# Test MCP server accessibility
curl http://localhost:8001/health

# Check Claude Desktop logs (varies by OS)
# Windows: %APPDATA%\Claude\logs\
# macOS: ~/Library/Logs/Claude/
# Linux: ~/.local/share/Claude/logs/
```

**Permission Issues:**
```bash
# Ensure Claude Desktop can execute Python
# Check file permissions on MCP directory
chmod +x /path/to/fleetpulse/mcp/main.py
```

**Docker Network Issues:**
```bash
# Verify Docker network connectivity
docker network ls
docker network inspect fleetpulse_default

# Test container connectivity
docker run --rm --network fleetpulse_default curlimages/curl curl http://backend:8000/health
```

### Security Considerations for Claude Desktop

- **Local Execution**: When running locally, ensure your MCP server only accepts local connections
- **Authentication**: Consider implementing authentication if exposing the MCP server to external networks
- **Firewall Rules**: Configure appropriate firewall rules to restrict access to the MCP server
- **Environment Variables**: Avoid storing sensitive credentials in the Claude Desktop configuration file

### Performance Optimization for Claude Desktop

For optimal performance with Claude Desktop:

```json
{
  "mcpServers": {
    "fleetpulse": {
      "command": "python",
      "args": ["-m", "mcp.main"],
      "cwd": "/path/to/your/fleetpulse/mcp",
      "env": {
        "FLEETPULSE_BACKEND_URL": "http://localhost:8000",
        "REQUEST_TIMEOUT": "10.0",
        "MAX_RETRIES": "2",
        "OTEL_ENABLE_TELEMETRY": "false",
        "LOG_LEVEL": "WARNING"
      }
    }
  }
}
```

## Observability

### OpenTelemetry Metrics

The MCP server exposes comprehensive metrics:

- `mcp_requests_total` - Total MCP requests by endpoint and status
- `mcp_request_duration_seconds` - MCP request duration histogram  
- `backend_api_requests_total` - Backend API requests by endpoint and status
- `backend_api_duration_seconds` - Backend API request duration histogram
- `mcp_active_connections` - Current active HTTP connections

### OpenTelemetry Tracing

All requests are traced with spans including:

- MCP tool execution spans
- Backend API request spans  
- Error tracking and status information
- Request correlation with baggage propagation

### Monitoring Dashboards

Configure your observability stack to monitor:

- Request latency and error rates
- Backend API connectivity and health
- Resource utilization and performance
- Active connections and throughput

## Error Handling

The MCP server implements comprehensive error handling:

### Backend Connectivity Issues

- **Connection Errors**: Automatic retry with exponential backoff
- **Timeout Errors**: Configurable request timeouts
- **HTTP Errors**: Proper status code mapping and error propagation
- **Graceful Degradation**: Continues operating with degraded functionality

### Request Validation

- Input parameter validation
- Query parameter sanitization  
- Hostname and package name format validation
- Pagination parameter bounds checking

### Logging

Structured logging with appropriate log levels:

- `INFO`: Normal operation events
- `WARNING`: Recoverable errors and degraded functionality  
- `ERROR`: Serious errors requiring attention
- `DEBUG`: Detailed debugging information

## Testing

Run the test suite:

```bash
# Run all MCP server tests
pytest tests/mcp/ -v

# Run specific test
pytest tests/mcp/test_mcp_server.py::test_health_endpoint -v

# Run with coverage
pytest tests/mcp/ --cov=mcp --cov-report=html
```

## Development

### Project Structure

```
mcp/
├── __init__.py           # Package initialization
├── main.py              # FastAPI application and MCP tools
├── config.py            # Configuration management
├── models.py            # Pydantic data models  
├── client.py            # Backend HTTP client
├── tools.py             # MCP tool implementations
├── telemetry.py         # OpenTelemetry instrumentation
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

### Adding New Tools

1. Add the tool implementation to `tools.py`
2. Add corresponding data models to `models.py`  
3. Add REST endpoint to `main.py`
4. Add tests to `tests/mcp/test_mcp_server.py`
5. Update documentation

### Contributing

1. Follow existing code patterns and conventions
2. Add comprehensive tests for new functionality
3. Update documentation and docstrings
4. Ensure OpenTelemetry instrumentation for new operations
5. Validate error handling and edge cases

## Troubleshooting

### Common Issues

**Backend Connection Failed**
```bash
# Check backend connectivity
curl http://localhost:8000/health

# Verify configuration
env | grep FLEETPULSE_BACKEND_URL
```

**MCP Server Won't Start**
```bash
# Check port availability  
netstat -tlnp | grep 8001

# Check configuration
python -c "from mcp.config import validate_config; validate_config()"
```

**High Latency**
```bash
# Check backend response times
curl -w "@curl-format.txt" http://localhost:8000/health

# Monitor OpenTelemetry metrics
curl http://localhost:8001/metrics
```

### Logs Analysis

Check application logs for issues:

```bash
# Follow logs in real-time
tail -f /var/log/fleetpulse-mcp.log

# Search for errors
grep -i error /var/log/fleetpulse-mcp.log

# Check OpenTelemetry output
grep -i "telemetry\|trace\|span" /var/log/fleetpulse-mcp.log
```

## Security Considerations

- **Input Validation**: All user inputs are validated and sanitized
- **Connection Security**: Uses HTTPS when configured with secure backend URLs
- **Resource Limits**: Implements connection pooling and request timeouts
- **Error Information**: Avoids exposing sensitive internal details in error responses
- **Access Control**: Designed to be deployed behind authentication proxies when needed

## Performance

### Optimization Settings

For production deployments:

```bash
# Use multiple workers
uvicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Tune connection pooling
export HTTPX_MAX_CONNECTIONS=100
export HTTPX_MAX_KEEPALIVE_CONNECTIONS=20

# Adjust timeouts
export REQUEST_TIMEOUT=10.0
export MAX_RETRIES=2

# Reduce tracing overhead
export OTEL_TRACE_SAMPLE_RATE=0.1
```

### Capacity Planning

- **Memory**: ~50-100 MB per worker process
- **CPU**: Minimal CPU usage, I/O bound workload  
- **Network**: Depends on backend API latency and request volume
- **Connections**: Configure based on expected concurrent users

## License

This project is part of FleetPulse and follows the same licensing terms.

## Docker Compose Configuration

The MCP server can be easily deployed using Docker Compose in several configurations:

### Option 1: Full FleetPulse Stack with MCP

To run the complete FleetPulse stack including the MCP server, backend, frontend, and observability tools:

```bash
# From the root directory
docker-compose up -d
```

This includes:
- FleetPulse Backend API (port 8000)
- FleetPulse Frontend (port 8080)
- FleetPulse MCP Server (port 8001)
- Jaeger Tracing UI (port 16686)
- OpenTelemetry Collector

### Option 2: MCP Server Only

To run just the MCP server against an existing FleetPulse backend:

```bash
# Using the MCP-specific compose file
docker-compose -f docker-compose.mcp.yml up -d
```

### Option 3: Pre-built Images

To use pre-built images from Docker Hub:

```bash
# Using the sample compose file
docker-compose -f docker-compose.sample.yml up -d
```

### Environment Configuration

Create a `.env` file in your project root to customize the deployment:

```bash
# Backend connection
FLEETPULSE_BACKEND_URL=http://backend:8000

# MCP server settings
MCP_PORT=8001
REQUEST_TIMEOUT=30.0
MAX_RETRIES=3

# OpenTelemetry configuration
OTEL_SERVICE_NAME=fleetpulse-mcp
OTEL_SERVICE_VERSION=1.0.0
OTEL_ENVIRONMENT=production
OTEL_ENABLE_TELEMETRY=true
OTEL_EXPORTER_TYPE=jaeger
OTEL_TRACE_SAMPLE_RATE=0.1

# For Jaeger tracing
OTEL_EXPORTER_JAEGER_ENDPOINT=http://jaeger:14268/api/traces

# For OTLP tracing
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

### Accessing the Services

After starting with Docker Compose, the services will be available at:

- **MCP Server**: http://localhost:8001
- **Backend API**: http://localhost:8000 (if included)
- **Frontend UI**: http://localhost:8080 (if included)
- **Jaeger UI**: http://localhost:16686 (if included)

### Health Checks

Verify all services are running:

```bash
# Check MCP server health
curl http://localhost:8001/health

# Check backend health (if running)
curl http://localhost:8000/health

# Check service status
docker-compose ps
```

### Scaling and Production Considerations

For production deployments, consider:

```yaml
# In your docker-compose.override.yml
services:
  mcp:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    restart: always
    environment:
      - OTEL_TRACE_SAMPLE_RATE=0.1  # Reduce tracing overhead
      - REQUEST_TIMEOUT=10.0        # Faster timeouts
```

### Troubleshooting Docker Compose

**Services won't start:**
```bash
# Check logs
docker-compose logs mcp

# Rebuild images
docker-compose build --no-cache

# Reset everything
docker-compose down -v
docker-compose up -d
```

**Network connectivity issues:**
```bash
# Test container connectivity
docker-compose exec mcp curl http://backend:8000/health

# Check network configuration
docker network ls
docker network inspect fleetpulse_default
```

**Resource issues:**
```bash
# Monitor resource usage
docker stats

# Check container health
docker-compose ps
```

## SSE Endpoint for Claude Desktop

The MCP server now provides an SSE endpoint for integration with Claude Desktop or other AI assistants that require Server-Sent Events.

### Endpoint

- **POST /sse**
- Accepts: JSON body specifying the tool and parameters
- Streams: Result as SSE (Server-Sent Events)

#### Example Request

```
POST /sse
Content-Type: application/json

{
  "tool": "list_hosts",
  "params": {}
}
```

#### Example SSE Response

```
event: result
data: [{"hostname": "server-01", "os": "Ubuntu", ...}, ...]

```

### Claude Desktop Integration

To use the MCP server with Claude Desktop in remote (SSE) mode, configure your Claude Desktop MCP config as follows:

```
{
  "mcpServers": {
    "fleetpulse": {
      "command": "stdio",
      "transport": {
        "type": "sse",
        "url": "http://your-mcp-server:8001/sse"
      },
      "env": {}
    }
  }
}
```

- The MCP server must be accessible from the Claude Desktop host.
- The /sse endpoint now supports POST requests with tool invocation.