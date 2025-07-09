# FleetPulse MCP Server - Deployment Guide

## Overview

The FleetPulse MCP (Model Context Protocol) server is now complete and ready for deployment. This TypeScript-based Express.js server provides intelligent integration with the FleetPulse backend, enabling natural language queries about fleet management data.

## Features Implemented

### ✅ Core MCP Protocol
- **OpenAPI 3.1 Specification**: Complete API documentation at `/mcp/v1/openapi`
- **Context Processing**: MCP context validation and processing at `/mcp/v1/context`
- **Proxy Functionality**: Request forwarding to model endpoints at `/mcp/v1/proxy`
- **Type Safety**: Full TypeScript implementation with Zod validation

### ✅ FleetPulse Integration
- **Natural Language Queries**: Intelligent interpretation of fleet management questions
- **Backend API Client**: Complete integration with FleetPulse FastAPI backend
- **Query Endpoint**: Direct query interface at `/mcp/v1/query`
- **Automatic Detection**: Context endpoint automatically detects FleetPulse questions

### ✅ Production Features
- **Security**: CORS, Helmet headers, input validation, request timeouts
- **Logging**: Structured Winston logging with request/response tracking
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Configuration**: Environment-based configuration with sensible defaults
- **Testing**: Complete test suite with Jest and Supertest

## Quick Start

### 1. Install Dependencies
```bash
cd /workspaces/fleetpulse/mcp
npm install
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Build and Test
```bash
npm run build
npm test
```

### 4. Start Server
```bash
# Development
npm run dev

# Production
npm start
```

### 5. Verify Installation
```bash
./test-mcp.sh
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_PORT` | `8001` | Server port |
| `MCP_HOST` | `0.0.0.0` | Server host |
| `FLEETPULSE_API_URL` | `http://localhost:8000` | FleetPulse backend URL |
| `MODEL_ENDPOINT_URL` | `http://localhost:8000/api/v1/completions` | Model proxy endpoint |
| `LOG_LEVEL` | `info` | Logging level |

## API Endpoints

### Health & Info
- `GET /health` - Server health status
- `GET /` - API information

### MCP Protocol
- `GET /mcp/v1/openapi` - OpenAPI specification
- `POST /mcp/v1/context` - Process MCP context (supports FleetPulse queries)
- `POST /mcp/v1/proxy` - Proxy to model endpoint

### FleetPulse Queries
- `POST /mcp/v1/query` - Direct FleetPulse queries with natural language

## Supported FleetPulse Queries

The server can understand and process various types of questions:

### Host Information
- "How many hosts do we have?"
- "Show me details for host server01"
- "Which hosts are running Ubuntu?"

### Package Management
- "What packages are installed on server01?"
- "Which hosts have nginx installed?"
- "Show me outdated packages"

### Statistics
- "What's the CPU usage across all hosts?"
- "Show me memory statistics"
- "Which hosts are using the most disk space?"

### Historical Data
- "Show me the history for host server01"
- "What changed on server01 yesterday?"

## Docker Deployment

### Single Container

The server includes Docker support with `Dockerfile.mcp`:

```bash
# Build image
docker build -f Dockerfile.mcp -t fleetpulse-mcp .

# Run container
docker run -p 8001:8001 --env-file mcp/.env fleetpulse-mcp
```

### Docker Compose (Recommended)

For complete FleetPulse deployment including the MCP server, use the provided Docker Compose configuration:

```bash
# Copy the sample configuration
cp docker-compose.sample.yml docker-compose.yml
cp .env.sample .env

# Edit environment variables
nano .env

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs mcp
```

The Docker Compose setup includes:
- **Backend**: FleetPulse FastAPI server
- **Frontend**: React-based web interface
- **MCP Server**: TypeScript-based Model Context Protocol server
- **Networking**: Internal network for service communication
- **Health Checks**: Automated health monitoring
- **Persistent Storage**: Data volume for backend storage

#### Environment Variables for Docker Compose

The MCP server in Docker Compose supports these environment variables:

```env
# FleetPulse Integration
FLEETPULSE_API_URL=http://backend:8000

# Server Configuration
MCP_PORT=8001
MCP_HOST=0.0.0.0
LOG_LEVEL=info
LOG_FORMAT=json

# Security & CORS
CORS_ORIGIN=*
CORS_CREDENTIALS=false
HELMET_ENABLED=true

# Request Handling
REQUEST_TIMEOUT=30000
MAX_REQUEST_SIZE=10mb

# Model Proxy (optional)
MODEL_ENDPOINT_URL=http://localhost:8000/api/v1/completions
```

## Integration with FleetPulse Backend

The MCP server integrates seamlessly with the FleetPulse FastAPI backend:

1. **Automatic Discovery**: Detects FleetPulse-related questions in context
2. **API Client**: Uses the FleetPulse REST API for data retrieval
3. **Query Interpretation**: Converts natural language to specific API calls
4. **Error Handling**: Graceful fallbacks when backend is unavailable

## CI/CD Integration

The server is integrated into the existing GitHub Actions workflow:

- **Automated Testing**: Tests run on every push
- **Docker Build**: Automatic image building and publishing
- **Type Checking**: TypeScript compilation validation

## Monitoring and Observability

### Logging
- Structured JSON logging with Winston
- Request/response tracking with timing
- Error logging with context and stack traces
- Configurable log levels (debug, info, warn, error)

### Health Checks
- `/health` endpoint for monitoring systems
- Server status and version information
- Dependency health checks

### Metrics
The server is designed to integrate with monitoring systems:
- Request timing and throughput
- Error rates and types
- FleetPulse backend connectivity

## Development

### Project Structure
```
mcp/
├── src/
│   ├── config.ts                    # Configuration management
│   ├── logger.ts                    # Logging utilities
│   ├── schemas.ts                   # Zod schemas and OpenAPI spec
│   ├── server.ts                    # Main Express server
│   ├── routes/mcp.ts               # MCP route handlers
│   └── services/
│       ├── fleetpulse-client.ts    # FleetPulse API client
│       └── query-interpreter.ts    # Natural language processor
├── tests/                          # Jest test suites
├── Dockerfile.mcp                  # Docker configuration
└── test-mcp.sh                     # Manual endpoint testing
```

### Adding New Query Types

To add support for new FleetPulse queries:

1. **Update Query Classifier**: Add new patterns in `query-interpreter.ts`
2. **Implement Handler**: Create new handler method for the query type
3. **Add API Client Methods**: Extend `fleetpulse-client.ts` if needed
4. **Update Tests**: Add test cases for new functionality
5. **Update Documentation**: Update README and this guide

### Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Manual endpoint testing
./test-mcp.sh

# Linting
npm run lint
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**: Check for existing processes on port 8001
   ```bash
   lsof -i :8001
   kill <PID>
   ```

2. **FleetPulse Backend Not Available**: 
   - Ensure backend is running on configured URL
   - Check `FLEETPULSE_API_URL` environment variable
   - Verify network connectivity

3. **TypeScript Compilation Errors**:
   - Run `npm run build` to check for errors
   - Ensure all dependencies are installed
   - Check TypeScript version compatibility

4. **Test Failures**:
   - Ensure no other services are running on test ports
   - Check environment variables in test configuration
   - Verify all dependencies are properly installed

### Debug Mode

Enable debug logging for detailed troubleshooting:
```bash
LOG_LEVEL=debug npm run dev
```

## Security Considerations

### Production Deployment
- Use environment variables for sensitive configuration
- Enable Helmet security headers (default: enabled)
- Configure CORS appropriately for your domain
- Use HTTPS in production environments
- Implement rate limiting if needed
- Monitor for unusual query patterns

### Input Validation
- All inputs validated with Zod schemas
- Request body size limits enforced
- Timeout protection for long-running requests
- SQL injection protection (parameterized queries in backend)

## Next Steps

The MCP server is production-ready. Consider these enhancements:

1. **Advanced NLP**: Integrate with more sophisticated language models
2. **Caching**: Add Redis for query result caching
3. **Rate Limiting**: Implement per-user rate limiting
4. **Metrics**: Add Prometheus metrics collection
5. **Authentication**: Add API key or JWT authentication
6. **Batch Queries**: Support for multiple queries in one request

## Support

For issues or questions:
- Check the logs with `LOG_LEVEL=debug`
- Run the test suite to verify functionality
- Use the test script for manual verification
- Check the OpenAPI specification for API details

The FleetPulse MCP server is now ready for production deployment and integration with your Model Context Protocol workflows.
