# FleetPulse

**FleetPulse** is a lightweight dashboard to monitor and audit Linux package updates across your fleet.  
It collects update reports (host, OS, date, packages upgraded, old/new versions) via a simple API and displays them in a modern, browser-friendly web UI.

Vibcoding for the win!

---

## Features

- 🚀 **FastAPI backend** with SQLite database
- ⚡ **React frontend** with Material UI for a modern look
- 📦 **Works with any OS**: Includes drop-in Ansible snippets for ArchLinux and Debian/Ubuntu
- 🐳 **Docker Compose**: One command to launch everything
- 👀 **Zero-config UI**: Open your browser and see updates at a glance
- 📊 **OpenTelemetry Observability**: Backend tracing, metrics, and logging

---

## Quickstart

1. **Clone the repo**

    ```bash
    git clone https://github.com/wesback/fleetpulse.git
    cd fleetpulse
    ```

2. **Configure data storage (optional)**

    By default, data is stored in `./data` directory. To customize the storage location:
    
    ```bash
    # Option 1: Set environment variable
    export FLEETPULSE_DATA_PATH=/your/preferred/path
    
    # Option 2: Copy and edit the environment file
    cp .env.example .env
    # Edit .env to set FLEETPULSE_DATA_PATH
    
    # Option 3: Create the directory and let Docker Compose use the default
    mkdir -p ./data
    ```

3. **Launch the stack**

    ```bash
    docker compose up --build -d
    ```

    - The **backend** runs on port **8000** (API)
    - The **frontend** runs on port **8080** (UI served by nginx)

4. **Open the dashboard:**  
   Visit [http://YOUR-HOST-IP:8080](http://YOUR-HOST-IP:8080) from any browser on your LAN.

---

## Deployment Configuration

FleetPulse is designed as a microservices architecture with separate frontend and backend containers for better scalability and maintainability.

### Architecture Overview

- **Frontend**: React application served by nginx on port 8080
- **Backend**: FastAPI application on port 8000
- **Communication**: Frontend proxies API calls to backend via nginx

### Backend Deployment Modes

The backend supports flexible deployment modes to match your specific use case:

### Backend Deployment Modes

#### **Uvicorn Mode (Default - Recommended)**
Single-process deployment optimized for simplicity and resource efficiency:

```bash
# Default in .env or docker-compose.yml
DEPLOYMENT_MODE=uvicorn
```

**Best for:**
- Single-container deployments
- Development environments  
- Low to medium traffic (< 100 concurrent users)
- Simplified setup and debugging
- Lower memory footprint

#### **Gunicorn Mode**
Multi-process deployment with enhanced fault tolerance:

```bash
# For high-traffic production deployments
DEPLOYMENT_MODE=gunicorn
GUNICORN_WORKERS=4  # Scale based on your needs
```

**Best for:**
- High-traffic production deployments (> 100 concurrent users)
- When you need process-level fault tolerance
- Multi-core CPU utilization requirements

### Service Configuration Examples

**Development:**
```bash
# docker-compose.yml or .env
DEPLOYMENT_MODE=uvicorn
FORCE_DB_RECREATE=true
```

**Production (simple):**
```bash
# docker-compose.yml or .env
DEPLOYMENT_MODE=uvicorn
FORCE_DB_RECREATE=false
```

**Production (high-traffic):**
```bash
# docker-compose.yml or .env
DEPLOYMENT_MODE=gunicorn
GUNICORN_WORKERS=4
FORCE_DB_RECREATE=false
```

### Docker Images

FleetPulse publishes separate Docker images for frontend and backend:

- **Backend**: `wesback/fleetpulse-backend:latest`
- **Frontend**: `wesback/fleetpulse-frontend:latest`

Use the provided `docker-compose.sample.yml` for production deployments with pre-built images.

**High-traffic production:**
```bash
DEPLOYMENT_MODE=gunicorn
GUNICORN_WORKERS=6
FORCE_DB_RECREATE=false
```

**Development:**
```bash
DEPLOYMENT_MODE=uvicorn
FORCE_DB_RECREATE=true  # Reset database on each startup
```

### Why We Default to Uvicorn

For FleetPulse's typical use case (fleet package update monitoring), the traffic patterns are:
- Periodic update reports from hosts
- Occasional dashboard access by administrators
- I/O-bound operations (database queries, static file serving)

Uvicorn provides excellent performance for this workload while being simpler to configure and debug.

---


For more details, see the `docker-compose.yml` and Dockerfiles in the repository.

---

## Reporting from Ansible

Add the relevant Ansible snippet to your playbooks and your updates will appear automatically in the FleetPulse dashboard!

### **ArchLinux Playbook Snippet**

```yaml
- name: Get pacman log timestamp before upgrade
  shell: date "+[%Y-%m-%dT%H:%M:%S"
  register: pacman_log_start
  changed_when: false

- name: Perform system upgrade
  pacman:
    upgrade: yes
    update_cache: yes
  register: upgrade_result

- name: Parse pacman.log for upgrades since playbook started
  shell: |
    awk -v start="{{ pacman_log_start.stdout }}" '
      $1 >= start && $3 == "upgraded" {
        match($0, /upgraded ([^ ]+) $begin:math:text$([^ ]+) -> ([^)]*)$end:math:text$/, a)
        if (a[1] && a[2] && a[3])
          print "{\"name\":\"" a[1] "\",\"old_version\":\"" a[2] "\",\"new_version\":\"" a[3] "\"}"
      }' /var/log/pacman.log | \
    paste -sd, - | sed 's/^/[/' | sed 's/$/]/'
  register: updated_packages_json
  changed_when: false

- name: POST upgraded packages to FleetPulse backend
  uri:
    url: "http://YOUR-BACKEND-IP:8000/report"
    method: POST
    headers:
      Content-Type: "application/json"
    body_format: json
    body: |
      {
        "hostname": "{{ inventory_hostname }}",
        "os": "archlinux",
        "update_date": "{{ pacman_log_start.stdout[1:11] }}",
        "updated_packages": {{ updated_packages_json.stdout | default('[]') | from_json }}
      }
    status_code: [200, 201]
  when: updated_packages_json.stdout != "[]"
```

---

## Backend Observability with OpenTelemetry

FleetPulse includes comprehensive OpenTelemetry instrumentation for the backend, providing insights into API performance and server-side operations.

### Features

- 📊 **Distributed Tracing**: Backend API request tracing and database operations
- 📈 **Metrics Collection**: API response times, error rates, and business KPIs
- 📝 **Structured Logging**: Trace-correlated logs for debugging
- 🎯 **Custom Spans**: Business logic instrumentation for package updates and host management

### Quick Start with Observability

Launch FleetPulse with Jaeger for observability:

```bash
# Enable telemetry (enabled by default)
export OTEL_ENABLE_TELEMETRY=true

# Launch with Jaeger included
docker compose up --build -d

# Access services
# - FleetPulse UI: http://localhost:8080
# - Jaeger UI: http://localhost:16686
```

### Telemetry Configuration

Configure telemetry through environment variables in `.env` file:

```bash
# Basic Configuration
OTEL_ENABLE_TELEMETRY=true
OTEL_ENVIRONMENT=development
OTEL_EXPORTER_TYPE=jaeger

# Sampling (adjust for production)
OTEL_TRACE_SAMPLE_RATE=1.0  # 100% for development, consider 0.1 (10%) for production
```

#### Available Exporters

**Jaeger (Default - Recommended for Development)**
```bash
OTEL_EXPORTER_TYPE=jaeger
# Jaeger UI: http://localhost:16686
```

**OpenTelemetry Collector (Recommended for Production)**
```bash
OTEL_EXPORTER_TYPE=otlp
OTEL_EXPORTER_OTLP_ENDPOINT=http://your-otel-collector:4317
```

**Console (Debug)**
```bash
OTEL_EXPORTER_TYPE=console
# Traces logged to application console
```

### Production Configuration Example

```bash
# .env for production
OTEL_ENABLE_TELEMETRY=true
OTEL_ENVIRONMENT=production
OTEL_EXPORTER_TYPE=otlp
OTEL_TRACE_SAMPLE_RATE=0.1
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

### Viewing Traces and Metrics

#### Jaeger UI (Default Setup)

1. Open http://localhost:16686
2. Select service: `fleetpulse-backend`
3. Click "Find Traces" to see recent activity
4. Click on traces to see detailed spans and timing

#### Key Traces to Monitor

**Backend Traces:**
- `report_package_updates`: Package update submissions
- `fetch_hosts`: Host listing operations
- `fetch_history`: Package history queries
- `health_check`: Service health monitoring

#### Custom Business Metrics

- `package_updates_total`: Total package updates by host
- `active_hosts_total`: Number of active hosts
- `http_requests_total`: API request count by endpoint
- `http_request_duration_ms`: API response times

### Troubleshooting Telemetry

#### Check Telemetry Status

```bash
# Check health endpoint for telemetry status
curl http://localhost:8000/health

# Response includes telemetry configuration:
{
  "status": "healthy",
  "database": "connected",
  "telemetry": {
    "enabled": true,
    "service_name": "fleetpulse-backend",
    "service_version": "1.0.0",
    "environment": "development",
    "exporter_type": "jaeger"
  }
}
```

#### Common Issues

**No traces in Jaeger:**
- Verify `OTEL_ENABLE_TELEMETRY=true`
- Check Jaeger container is running: `docker ps | grep jaeger`
- Verify sampling rate: `OTEL_TRACE_SAMPLE_RATE=1.0`

**High overhead in production:**
- Reduce sampling: `OTEL_TRACE_SAMPLE_RATE=0.1`
- Switch to OTLP with collector: `OTEL_EXPORTER_TYPE=otlp`

**Network connectivity issues:**
- Check Jaeger endpoint accessibility
- Verify Docker network configuration
- Review container logs: `docker logs fleetpulse-jaeger`

#### Disabling Telemetry

```bash
# Disable completely
OTEL_ENABLE_TELEMETRY=false

# Or remove Jaeger from docker-compose
docker compose up backend frontend
```

### Telemetry Best Practices

- **Development**: Use 100% sampling rate with Jaeger for full visibility
- **Production**: Use 10% sampling rate with OTLP collector for efficiency
- **Monitoring**: Set up alerts on telemetry pipeline health
- **Security**: Ensure telemetry data doesn't include sensitive information
- **Performance**: Monitor telemetry overhead and adjust sampling accordingly

---

## Running Tests

### Backend Tests

The backend tests use `pytest` and are located in `tests/backend/`.

1. (Recommended) Create and activate a Python virtual environment from the project root:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies (pytest is included in requirements.txt):
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Run the tests from the project root:
   ```bash
   pytest tests/backend/
   ```
   Or use the provided script (recommended - handles both backend and frontend):
   ```bash
   ./run_tests.sh
   ```

### Frontend Tests

The frontend tests use Jest and React Testing Library, located in `src/App.test.js`.

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Run the tests:
   ```bash
   npm test
   ```

**Note:** The `run_tests.sh` script automatically runs both backend and frontend tests for convenience.

---

## MCP Server Integration

FleetPulse includes a **Model Context Protocol (MCP) server** that exposes read-only API endpoints as tools for AI assistant integration. This allows AI assistants to query package update information through a standardized protocol.

### What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open standard that enables AI models to securely connect with external data sources and tools. FleetPulse's MCP server provides read-only access to package update data, making it easy for AI assistants to help with fleet monitoring tasks.

### Available MCP Tools

The FleetPulse MCP server provides these tools:

- **`fleetpulse_list_hosts`** - Get list of all hosts that have reported updates
- **`fleetpulse_get_host_history`** - Get package update history for specific hosts with filtering options
- **`fleetpulse_get_last_updates`** - Get last update dates and OS information for all hosts
- **`fleetpulse_check_health`** - Check the health status of the FleetPulse backend

### Starting the MCP Server

1. **Start the FastAPI backend** (if not already running):
   ```bash
   cd backend
   python main.py
   ```

2. **Start the MCP server** in a separate terminal:
   ```bash
   cd backend
   python start_mcp_server.py
   ```

   Or run it directly:
   ```bash
   cd backend
   python -m fleetpulse_mcp.server
   ```

### Configuration

The MCP server can be configured using environment variables:

```bash
# FastAPI backend connection
export FLEETPULSE_API_HOST=localhost      # Default: localhost
export FLEETPULSE_API_PORT=8000           # Default: 8000

# MCP server settings
export MCP_SERVER_NAME="FleetPulse MCP Server"  # Default: FleetPulse MCP Server
export MCP_SERVER_VERSION="1.0.0"               # Default: 1.0.0
export MCP_REQUEST_TIMEOUT=30.0                  # Default: 30.0 seconds
export MCP_DEBUG=false                           # Default: false
```

### Testing MCP Tools

You can test the MCP tools directly:

```bash
cd backend

# Test health check
python -c "
import asyncio
from fleetpulse_mcp.tools.health_tool import check_health
print(asyncio.run(check_health()))
"

# Test host listing
python -c "
import asyncio
from fleetpulse_mcp.tools.hosts_tool import list_hosts
print(asyncio.run(list_hosts()))
"

# Test host history (replace 'hostname' with actual host)
python -c "
import asyncio
from fleetpulse_mcp.tools.history_tool import get_host_history
print(asyncio.run(get_host_history('your-hostname')))
"
```

### Integration with AI Assistants

The MCP server uses the standard MCP protocol over stdio, making it compatible with various AI assistants and MCP clients. Each tool returns structured JSON responses optimized for AI consumption.

**Example tool usage scenarios:**
- "Show me all hosts in the fleet" → `fleetpulse_list_hosts`
- "Get nginx updates for web-server-01 this week" → `fleetpulse_get_host_history` with filtering
- "Which hosts haven't updated recently?" → `fleetpulse_get_last_updates`
- "Is the FleetPulse backend healthy?" → `fleetpulse_check_health`

### MCP Server Architecture

The MCP implementation follows best practices:

```
backend/fleetpulse_mcp/
├── server.py              # Main MCP server
├── config/
│   └── settings.py        # Configuration management
├── tools/                 # Individual MCP tools
│   ├── hosts_tool.py     # Host listing functionality
│   ├── history_tool.py   # History querying with filters
│   ├── last_updates_tool.py  # Last update information
│   └── health_tool.py    # Health checking
└── resources/            # Future resource implementations
```

### Limitations and Future Enhancements

**Current limitations:**
- Read-only access only (no package update reporting via MCP)
- No authentication/authorization (planned for future releases)
- Single FastAPI backend connection (no load balancing)

**Planned enhancements:**
- Write operations for reporting updates
- Authentication and authorization
- Multi-backend support
- Streaming responses for large datasets
- Additional filtering and search capabilities

### Running Tests

Test the MCP functionality:

```bash
# Run MCP integration tests (requires running FastAPI backend)
pytest tests/backend/mcp/ -v

# Run specific MCP test
pytest tests/backend/mcp/test_mcp_integration.py::TestMCPIntegration::test_health_tool_integration -v
```

For more information about MCP, visit the [official documentation](https://modelcontextprotocol.io/).
