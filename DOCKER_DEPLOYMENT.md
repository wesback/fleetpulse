# FleetPulse Docker Deployment Quick Reference

## Updated MCP Server Implementation

The FleetPulse MCP server has been completely rewritten in TypeScript with enhanced capabilities:

### What Changed
- **Language**: Python → TypeScript/Node.js
- **Framework**: FastAPI → Express.js  
- **Features**: Added natural language query processing for FleetPulse data
- **Type Safety**: Full TypeScript implementation with Zod validation
- **API**: Enhanced with dedicated query endpoint and FleetPulse integration

### Quick Start with Docker Compose

```bash
# 1. Copy configuration files
cp docker-compose.sample.yml docker-compose.yml
cp .env.sample .env

# 2. Start all services
docker-compose up -d

# 3. Verify services are running
docker-compose ps

# 4. Test MCP server
curl http://localhost:8001/health
```

### Service Endpoints

After running `docker-compose up -d`:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:8080 | Web interface |
| Backend API | http://localhost:8000 | FastAPI backend |
| MCP Server | http://localhost:8001 | Model Context Protocol server |
| MCP Health | http://localhost:8001/health | Health check |
| MCP OpenAPI | http://localhost:8001/mcp/v1/openapi | API documentation |

### MCP Server Capabilities

The new TypeScript MCP server can:

1. **Process Natural Language Queries**:
   ```bash
   curl -X POST http://localhost:8001/mcp/v1/query \
     -H "Content-Type: application/json" \
     -d '{"query": "How many hosts do we have?"}'
   ```

2. **Handle MCP Context Objects**:
   ```bash
   curl -X POST http://localhost:8001/mcp/v1/context \
     -H "Content-Type: application/json" \
     -d '{"context": {"type": "question", "data": {"question": "Show me CPU statistics"}}}'
   ```

3. **Proxy Requests to Model Endpoints**:
   ```bash
   curl -X POST http://localhost:8001/mcp/v1/proxy \
     -H "Content-Type: application/json" \
     -d '{"context": {...}, "request": {...}}'
   ```

### Environment Configuration

Key environment variables for the MCP service:

```env
# Core Configuration
FLEETPULSE_API_URL=http://backend:8000  # Internal backend URL
MCP_PORT=8001                           # Server port
LOG_LEVEL=info                          # Logging level

# Security
CORS_ORIGIN=*                           # CORS configuration
HELMET_ENABLED=true                     # Security headers

# Performance
REQUEST_TIMEOUT=30000                   # Request timeout (ms)
MAX_REQUEST_SIZE=10mb                   # Max request body size
```

### Troubleshooting

#### Service Not Starting
```bash
# Check logs
docker-compose logs mcp

# Check if port is available
netstat -tulpn | grep :8001

# Restart specific service
docker-compose restart mcp
```

#### MCP Server Connection Issues
```bash
# Test backend connectivity from MCP container
docker-compose exec mcp curl http://backend:8000/health

# Check network configuration
docker-compose exec mcp nslookup backend
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check service health
docker-compose exec mcp curl http://localhost:8001/health
```

### Migration from Python MCP Server

If upgrading from the previous Python implementation:

1. **Environment Variables**: Update variable names (see .env.sample)
2. **API Endpoints**: New endpoint structure with `/mcp/v1/` prefix
3. **Query Format**: Enhanced query processing with natural language support
4. **Docker Image**: Uses Node.js base image instead of Python

### Production Considerations

For production deployment:

1. **Environment Variables**: Use proper secrets management
2. **CORS**: Restrict to specific domains
3. **HTTPS**: Use reverse proxy for SSL termination
4. **Monitoring**: Implement health checks and metrics collection
5. **Logging**: Configure centralized logging
6. **Scaling**: Use Docker Swarm or Kubernetes for scaling

### Development

For local development with the new MCP server:

```bash
# Navigate to MCP directory
cd mcp/

# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

The development server will hot-reload on code changes and provide detailed logging for debugging.
