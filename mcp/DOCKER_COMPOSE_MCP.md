# FleetPulse MCP Server - Docker Compose Quick Start

This guide provides quick setup instructions for running the FleetPulse MCP Server using Docker Compose.

## Prerequisites

- Docker Engine 20.10+ and Docker Compose 2.0+
- At least 2GB of available RAM
- Ports 8000, 8001, and optionally 8080, 16686 available

## Quick Start Options

### Option 1: Full Stack (Recommended for Development)

Run the complete FleetPulse stack including backend, frontend, MCP server, and observability tools:

```bash
# Clone the repository
git clone https://github.com/your-org/fleetpulse.git
cd fleetpulse

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

**Services available:**
- Frontend UI: http://localhost:8080
- Backend API: http://localhost:8000
- MCP Server: http://localhost:8001
- Jaeger UI: http://localhost:16686

### Option 2: MCP Server Only

Run just the MCP server with a local backend (no frontend or observability):

```bash
# Start MCP server and backend only
docker-compose --profile backend -f docker-compose.mcp.yml up -d

# Check status
curl http://localhost:8001/health
```

### Option 3: Pre-built Images

Use pre-built images from Docker Hub:

```bash
# Copy sample configuration
cp docker-compose.sample.yml docker-compose.yml
cp .env.mcp.sample .env

# Edit .env file as needed
nano .env

# Start services
docker-compose up -d
```

### Option 4: External Backend

Connect MCP server to an existing FleetPulse backend:

```bash
# Set backend URL and start MCP server only
FLEETPULSE_BACKEND_URL=https://your-backend.example.com \
docker-compose -f docker-compose.mcp.yml up mcp
```

## Configuration

### Environment Variables

Copy and customize the sample environment file:

```bash
cp .env.mcp.sample .env
```

Key settings to customize:

```bash
# Backend connection
FLEETPULSE_BACKEND_URL=http://backend:8000

# MCP server port
MCP_PORT=8001

# Environment type
OTEL_ENVIRONMENT=development  # or production

# Tracing configuration
OTEL_EXPORTER_TYPE=jaeger     # or console, otlp
OTEL_TRACE_SAMPLE_RATE=1.0    # Use 0.1 for production
```

### Profiles

Use Docker Compose profiles to control which services run:

```bash
# Backend only (no observability)
docker-compose --profile backend up

# Full observability stack
docker-compose --profile backend --profile observability up

# MCP server only (requires external backend)
docker-compose up mcp
```

## Verification

### Health Checks

```bash
# Check all services
docker-compose ps

# Test MCP server
curl http://localhost:8001/health

# Test backend (if running locally)
curl http://localhost:8000/health

# List available MCP tools
curl http://localhost:8001/tools
```

### Logs

```bash
# View all logs
docker-compose logs

# Follow MCP server logs
docker-compose logs -f mcp

# Check for errors
docker-compose logs mcp | grep -i error
```

## Common Tasks

### Update Services

```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build
```

### Scale MCP Server

```bash
# Run multiple MCP server instances
docker-compose up -d --scale mcp=3
```

### View Metrics

```bash
# OpenTelemetry metrics (if otel-collector is running)
curl http://localhost:8888/metrics

# Container stats
docker stats
```

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check port conflicts
netstat -tulpn | grep -E ':(8000|8001|8080|16686)'

# Check logs for errors
docker-compose logs mcp
```

**Can't connect to backend:**
```bash
# Test network connectivity
docker-compose exec mcp curl http://backend:8000/health

# Check backend logs
docker-compose logs backend
```

**High memory usage:**
```bash
# Monitor resource usage
docker stats

# Reduce tracing overhead
echo "OTEL_TRACE_SAMPLE_RATE=0.1" >> .env
docker-compose restart mcp
```

### Reset Everything

```bash
# Stop all services and remove data
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Clean system
docker system prune -f
```

## Production Deployment

For production use:

1. **Update configuration:**
   ```bash
   OTEL_ENVIRONMENT=production
   OTEL_TRACE_SAMPLE_RATE=0.1
   REQUEST_TIMEOUT=10.0
   ```

2. **Use external backend:**
   ```bash
   FLEETPULSE_BACKEND_URL=https://your-production-backend.com
   ```

3. **Enable resource limits:**
   ```yaml
   services:
     mcp:
       deploy:
         resources:
           limits:
             memory: 512M
             cpus: '0.5'
   ```

4. **Set up monitoring:**
   - Configure external observability system
   - Set up log aggregation
   - Configure alerting

## Next Steps

- **AI Assistant Integration**: Connect Claude or other AI assistants to your MCP server
- **Custom Tools**: Extend the MCP server with custom tools for your use case  
- **Monitoring**: Set up comprehensive monitoring and alerting
- **Security**: Configure authentication and access controls

For detailed configuration options, see the main [MCP README](mcp/README.md).
