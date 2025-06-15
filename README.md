# FleetPulse

**FleetPulse** is a lightweight dashboard to monitor and audit Linux package updates across your fleet.  
It collects update reports (host, OS, date, packages upgraded, old/new versions) via a simple API and displays them in a modern, browser-friendly web UI.

Vibcoding for the win!

---

## Features

- 🚀 **FastAPI backend** with SQLite database
- ⚡ **React frontend** with Material UI for a modern look
- 🤖 **MCP Server**: Model Context Protocol server for AI assistant integration
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

## FleetPulse MCP Server

FleetPulse includes a **Model Context Protocol (MCP) server** that provides read-only access to fleet data for AI assistants like Claude. The MCP server acts as a bridge between AI tools and the FleetPulse backend API.

### Features

- 🤖 **AI Assistant Integration**: Standardized MCP tools for fleet management queries
- 🔍 **Comprehensive Search**: Search across hosts, packages, and update reports
- 📊 **Fleet Analytics**: Aggregate statistics and activity metrics
- 🛡️ **Robust Error Handling**: Graceful degradation when backend is unavailable
- 📈 **OpenTelemetry Observability**: Full tracing and metrics for MCP operations
- ⚡ **Async Performance**: Non-blocking HTTP client with connection pooling

### Quick Start

1. **Install MCP server dependencies**:
   ```bash
   cd mcp/
   pip install -r requirements.txt
   ```

2. **Configure the MCP server**:
   ```bash
   export FLEETPULSE_BACKEND_URL="http://localhost:8000"
   export MCP_PORT="8001"
   export OTEL_ENABLE_TELEMETRY="true"
   ```

3. **Start the MCP server**:
   ```bash
   cd mcp/
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn mcp.main:app --host 0.0.0.0 --port 8001
   ```

### Available MCP Tools

The MCP server exposes these tools for AI assistants:

- **`health_check`** - Check backend and MCP server health status
- **`list_hosts`** - List all hosts with metadata (OS, last update, package count)
- **`get_host_details`** - Get detailed information for a specific host
- **`get_update_reports`** - Retrieve package update reports with filtering
- **`get_host_reports`** - Get update reports for a specific host
- **`list_packages`** - List all packages across the fleet
- **`get_package_details`** - Get detailed package information
- **`get_fleet_statistics`** - Get aggregate statistics and activity metrics
- **`search`** - Search across hosts, packages, and reports

### Example AI Queries

With the MCP server running, AI assistants can answer questions like:

- *"Show me all hosts in the fleet and their last update times"*
- *"What packages were updated on server-01 in the last week?"*
- *"Which hosts have the nginx package installed?"*
- *"What's the overall health of my FleetPulse system?"*
- *"Search for any activity related to openssl"*

### REST API Access

The MCP server also provides REST endpoints for direct access:

```bash
# List available tools
curl http://localhost:8001/tools

# Health check
curl http://localhost:8001/health

# List hosts
curl http://localhost:8001/hosts

# Get host details
curl http://localhost:8001/hosts/server-01

# Search for packages
curl "http://localhost:8001/search?q=nginx"

# Get fleet statistics
curl http://localhost:8001/stats
```

### Configuration

The MCP server supports extensive configuration via environment variables:

```bash
# Backend connection
FLEETPULSE_BACKEND_URL=http://localhost:8000

# MCP server settings
MCP_PORT=8001
REQUEST_TIMEOUT=30.0
MAX_RETRIES=3

# OpenTelemetry (inherits from backend configuration)
OTEL_SERVICE_NAME=fleetpulse-mcp
OTEL_ENABLE_TELEMETRY=true
OTEL_EXPORTER_TYPE=console  # console, jaeger, or otlp
```

### Architecture

```
┌─────────────────┐    MCP Protocol     ┌──────────────────┐    HTTP API     ┌─────────────────┐
│   AI Assistant  │ ─────────────────▶  │  FleetPulse MCP  │ ─────────────▶ │ FleetPulse      │
│   (Claude, etc) │                     │  Server          │                 │ Backend         │
└─────────────────┘                     └──────────────────┘                 └─────────────────┘
```

The MCP server:
- **Does NOT** connect directly to the database
- **Makes HTTP requests** to the existing FleetPulse backend API
- **Provides read-only access** - no modification operations
- **Includes comprehensive instrumentation** with OpenTelemetry
- **Handles errors gracefully** with retry logic and fallbacks

### Documentation

For detailed MCP server documentation, configuration options, and development guide, see: **[mcp/README.md](mcp/README.md)**

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
