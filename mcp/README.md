# FleetPulse MCP Server - Complete Documentation

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start) 
3. [Automated Query Routing System](#automated-query-routing-system)
4. [Architecture](#architecture)
5. [API Reference](#api-reference)
6. [Deployment Guide](#deployment-guide)
7. [Development Guide](#development-guide)
8. [Testing](#testing)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)
11. [Migration from Manual Routing](#migration-from-manual-routing)

---

## Overview

The FleetPulse MCP (Model Context Protocol) server is a TypeScript-based Express.js server that provides intelligent integration with the FleetPulse backend. It features an **automated query routing system** that uses OpenAPI specifications to generate intelligent natural language query classification.

### Key Features

- 🤖 **Automated Query Routing** - Auto-generates routing logic from OpenAPI specs
- 🔍 **Natural Language Processing** - Intelligent interpretation of fleet management questions  
- 🔌 **MCP Protocol Compliance** - Full Model Context Protocol implementation
- 🛡️ **Production Ready** - Security, logging, error handling, and testing
- 📊 **FleetPulse Integration** - Complete backend API integration
- 🎯 **Intent Recognition** - Pattern-based query classification with confidence scoring

---

## Quick Start

### 1. Installation

```bash
cd /workspaces/fleetpulse/mcp
npm install
```

### 2. Environment Setup

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Server Configuration
PORT=3001
NODE_ENV=development
LOG_LEVEL=info

# FleetPulse Backend
FLEETPULSE_BACKEND_URL=http://localhost:8000

# Security
CORS_ORIGIN=http://localhost:3000
REQUEST_TIMEOUT=30000
```

### 3. Generate Automated Routing

```bash
# Generate routing from your running FleetPulse API
npx ts-node generate-routing.ts http://localhost:8000/openapi.json --output ./src/generated

# Or from a saved spec file
npx ts-node generate-routing.ts ../backend/openapi.json --format both
```

### 4. Build and Start

```bash
# Development
npm run dev

# Production
npm run build
npm start
```

### 5. Test the Server

```bash
# Run tests
npm test

# Test routing generation
npx ts-node test-routing.ts

# Manual test
curl -X POST http://localhost:3001/mcp/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the health status?"}'
```

---

## Automated Query Routing System

The MCP server features an advanced automated query routing system that generates intelligent routing logic from OpenAPI 3.0 specifications.

### How It Works

1. **OpenAPI Analysis** - Extracts semantic patterns from API endpoints
2. **Rule Generation** - Creates routing rules with keywords and intent patterns  
3. **TypeScript Generation** - Generates runtime routing functions
4. **Intelligent Classification** - Routes queries based on intent, not just keywords

### Generated Routing Categories

Based on your FleetPulse API, the system automatically creates:

| Category | Priority | Keywords | Intent Patterns |
|----------|----------|----------|-----------------|
| **Health Status** | 100 | health, status, operational | "check * status", "is * working" |
| **Update Tracking** | 90 | update, updates, recent | "recent updates", "what was updated" |
| **Statistics** | 80 | statistics, stats, overview | "show * overview", "how many *" |
| **Host Management** | 70 | host, hosts, server | "list * hosts", "get host *" |
| **Package Management** | 60 | package, packages, software | "package *", "what packages *" |
| **Historical Data** | 50 | history, timeline, when | "* history", "what happened *" |
| **Reporting** | 40 | report, reports, analytics | "generate report", "analysis of *" |

### Usage Examples

```typescript
import { EnhancedFleetPulseQueryInterpreter } from './services/enhanced-query-interpreter';

// Initialize with auto-generated routing
const spec = await loadOpenApiSpec('http://localhost:8000/openapi.json');
const interpreter = new EnhancedFleetPulseQueryInterpreter(backendUrl, spec);

// Process queries with routing metadata
const result = await interpreter.interpretQuery("What's the health status?");
console.log(result.routing_metadata); // {
//   matched_category: "health_status",
//   confidence: 1.0,
//   matched_keywords: ["health", "status"],
//   suggested_endpoints: ["GET /health"]
// }
```

### Customization Options

#### 1. Manual Rule Adjustment

Edit generated `routing-config.json`:

```json
{
  "category": "custom_category",
  "priority": 85,
  "keywords": ["custom", "specific"],
  "intentPatterns": ["custom pattern *"],
  "negativeKeywords": ["exclude"],
  "confidence": 0.8
}
```

#### 2. LLM-Assisted Generation

```bash
# Generate LLM prompt for custom rules
npx ts-node generate-routing.ts ./api-spec.json --prompt
```

#### 3. Runtime Testing

```typescript
// Test query against all routing rules
const results = interpreter.testQueryRouting("show me statistics");
console.log(results); // See all potential matches
```

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Server                                │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│ │   MCP Protocol  │  │ Query Routing   │  │ FleetPulse API  │   │
│ │   Endpoints     │  │    System       │  │    Client       │   │
│ └─────────────────┘  └─────────────────┘  └─────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                     Express.js Server                           │
├─────────────────────────────────────────────────────────────────┤
│ Security │ Logging │ Validation │ Error Handling │ Testing      │
└─────────────────────────────────────────────────────────────────┘
```

### Core Files

| File | Purpose |
|------|---------|
| `src/server.ts` | Main Express server and MCP endpoints |
| `src/services/openapi-analyzer.ts` | OpenAPI specification analysis |
| `src/services/enhanced-query-interpreter.ts` | Auto-generated query routing |
| `src/services/fleetpulse-client.ts` | FleetPulse backend API client |
| `src/services/query-interpreter.ts` | Base query interpretation logic |
| `generate-routing.ts` | CLI tool for routing generation |
| `smart-interpreter-example.ts` | Production-ready routing example |

### Data Flow

1. **Query Received** → MCP endpoint receives natural language query
2. **Route Analysis** → Enhanced interpreter analyzes query intent
3. **Category Matching** → Auto-generated functions classify the query
4. **API Call** → FleetPulse client makes appropriate backend request
5. **Response Processing** → Results formatted with routing metadata
6. **MCP Response** → Structured response sent back with suggestions

---

## API Reference

### MCP Protocol Endpoints

#### GET /mcp/v1/openapi

Returns OpenAPI 3.1 specification for the MCP server.

#### POST /mcp/v1/context

```json
{
  "context": "User query or context to process"
}
```

**Response**: Context analysis with FleetPulse integration detection.

#### POST /mcp/v1/proxy

```json
{
  "method": "GET|POST|PUT|DELETE",
  "url": "/target/endpoint", 
  "headers": {},
  "body": {}
}
```

**Response**: Proxied response from target endpoint.

### FleetPulse Integration

#### POST /mcp/v1/query

```json
{
  "query": "Natural language question about fleet"
}
```

**Response**:

```json
{
  "success": true,
  "data": {},
  "message": "Human-readable response",
  "context_type": "health_check",
  "suggestions": ["Follow-up suggestions"],
  "routing_metadata": {
    "matched_category": "health_status",
    "confidence": 0.95,
    "matched_keywords": ["health", "status"],
    "suggested_endpoints": ["GET /health"],
    "processing_time_ms": 45
  }
}
```

### Backend Integration Endpoints

The server integrates with these FleetPulse backend endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | System health check |
| `/statistics` | GET | Fleet statistics and metrics |
| `/hosts` | GET | List all monitored hosts |
| `/hosts/{hostname}/history` | GET | Host update history |
| `/reports/host-activity` | GET | Host activity reports |
| `/reports/package-updates` | GET | Package update reports |

---

## Deployment Guide

### Production Deployment

#### 1. Docker Deployment

```bash
# Build the image
docker build -t fleetpulse-mcp .

# Run the container
docker run -p 3001:3001 \
  -e FLEETPULSE_BACKEND_URL=http://your-backend:8000 \
  -e NODE_ENV=production \
  fleetpulse-mcp
```

#### 2. Docker Compose

```yaml
version: '3.8'
services:
  mcp-server:
    build: ./mcp
    ports:
      - "3001:3001"
    environment:
      - FLEETPULSE_BACKEND_URL=http://backend:8000
      - NODE_ENV=production
    depends_on:
      - backend
```

#### 3. Process Manager (PM2)

```bash
npm install -g pm2
npm run build
pm2 start dist/server.js --name fleetpulse-mcp
```

### Environment Configuration

#### Production Environment Variables

```env
# Server
PORT=3001
NODE_ENV=production
LOG_LEVEL=warn

# Backend Integration  
FLEETPULSE_BACKEND_URL=https://your-backend.com
API_TIMEOUT=30000

# Security
CORS_ORIGIN=https://your-frontend.com
HELMET_CSP_DIRECTIVES=default-src 'self'
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100

# Monitoring
HEALTH_CHECK_INTERVAL=60000
METRICS_ENABLED=true
```

### Load Balancing

```nginx
upstream mcp_servers {
    server mcp-server-1:3001;
    server mcp-server-2:3001;
    server mcp-server-3:3001;
}

server {
    listen 80;
    server_name mcp.yourdomain.com;
    
    location / {
        proxy_pass http://mcp_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## Development Guide

### Project Structure

```
/workspaces/fleetpulse/mcp/
├── src/
│   ├── server.ts                    # Main Express server
│   ├── config.ts                    # Configuration management
│   ├── logger.ts                    # Winston logging setup
│   ├── schemas.ts                   # Zod validation schemas
│   ├── routes/
│   │   └── mcp.ts                   # MCP protocol routes
│   └── services/
│       ├── openapi-analyzer.ts      # OpenAPI analysis
│       ├── enhanced-query-interpreter.ts # Auto-generated routing
│       ├── query-interpreter.ts     # Base query interpretation logic
│       └── fleetpulse-client.ts     # Backend API client
├── tests/                           # Test files
├── generated/                       # Auto-generated routing files
├── generate-routing.ts              # CLI routing generator
├── test-routing.ts                  # Routing test script
└── smart-interpreter-example.ts     # Production example
```

### Development Workflow

#### 1. Setup Development Environment

```bash
npm install
npm run dev  # Starts with hot reload
```

#### 2. Generate and Test Routing

```bash
# Generate routing from API
npx ts-node generate-routing.ts http://localhost:8000/openapi.json

# Test routing logic
npx ts-node test-routing.ts

# Test specific queries
npm run test:routing
```

#### 3. Add New Query Categories

1. Update your OpenAPI specification with better descriptions
2. Regenerate routing: `npx ts-node generate-routing.ts`
3. Test new categories: `npx ts-node test-routing.ts`
4. Add specific handlers in `enhanced-query-interpreter.ts`

#### 4. Custom Routing Rules

```typescript
// Add to routing configuration
{
  category: 'security_updates',
  priority: 95,
  keywords: ['security', 'vulnerability', 'patch', 'critical'],
  intentPatterns: ['security updates', 'critical patches', 'vulnerability *'],
  negativeKeywords: ['general', 'all'],
  confidence: 0.9
}
```

### Adding New Features

#### 1. New MCP Endpoint

```typescript
// In src/routes/mcp.ts
router.post('/v1/new-endpoint', validateSchema(NewEndpointSchema), async (req, res) => {
  try {
    const result = await processNewEndpoint(req.body);
    res.json(result);
  } catch (error) {
    handleError(error, res);
  }
});
```

#### 2. New FleetPulse Integration

```typescript
// In src/services/fleetpulse-client.ts
async getNewData(params: NewDataParams): Promise<NewDataResponse> {
  return this.request<NewDataResponse>('GET', '/new-endpoint', { params });
}

// In enhanced-query-interpreter.ts  
private async handleNewDataQuery(query: string): Promise<QueryResult> {
  const data = await this.apiClient.getNewData({});
  return {
    success: true,
    data,
    message: 'New data retrieved successfully',
    context_type: 'new_data'
  };
}
```

---

## Testing

### Test Suite

```bash
# Run all tests
npm test

# Run specific test suites
npm run test:unit
npm run test:integration
npm run test:routing

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

### Test Categories

#### 1. Unit Tests
- Schema validation
- Query interpretation logic
- OpenAPI analysis
- Client API methods

#### 2. Integration Tests  
- MCP endpoint functionality
- FleetPulse backend integration
- Error handling scenarios
- Authentication flows

#### 3. Routing Tests
- Query classification accuracy
- Intent pattern matching
- Confidence scoring
- Category prioritization

### Example Tests

```typescript
describe('Enhanced Query Interpreter', () => {
  test('should route health queries correctly', async () => {
    const result = await interpreter.interpretQuery('What is the health status?');
    expect(result.routing_metadata.matched_category).toBe('health_status');
    expect(result.routing_metadata.confidence).toBeGreaterThan(0.9);
  });

  test('should handle ambiguous queries', async () => {
    const result = await interpreter.interpretQuery('show me updates');
    expect(result.routing_metadata.confidence).toBeDefined();
    expect(result.suggestions).toHaveLength(3);
  });
});
```

### Manual Testing

```bash
# Test routing generation
curl -X POST http://localhost:3001/mcp/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the health status?"}'

# Test context processing
curl -X POST http://localhost:3001/mcp/v1/context \
  -H "Content-Type: application/json" \
  -d '{"context": "I need to check fleet statistics"}'

# Test OpenAPI endpoint
curl http://localhost:3001/mcp/v1/openapi
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 3001 | Server port |
| `NODE_ENV` | development | Environment mode |
| `LOG_LEVEL` | info | Logging level |
| `FLEETPULSE_BACKEND_URL` | http://localhost:8000 | Backend API URL |
| `CORS_ORIGIN` | * | CORS allowed origins |
| `REQUEST_TIMEOUT` | 30000 | Request timeout (ms) |
| `RATE_LIMIT_WINDOW_MS` | 900000 | Rate limit window |
| `RATE_LIMIT_MAX_REQUESTS` | 100 | Max requests per window |

### Routing Configuration

Generated routing config structure:

```json
{
  "rules": [
    {
      "category": "health_status",
      "priority": 100,
      "keywords": ["health", "status"],
      "intentPatterns": ["check * status"],
      "negativeKeywords": ["host"],
      "endpoints": [{"method": "GET", "path": "/health"}],
      "confidence": 1.0
    }
  ],
  "fallbackSuggestions": ["Check health", "Get statistics"],
  "metadata": {
    "generatedAt": "2025-07-09T15:26:12.911Z",
    "totalEndpoints": 6
  }
}
```

### Logging Configuration

```typescript
// Custom log levels
const logConfig = {
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ 
      filename: 'logs/error.log', 
      level: 'error' 
    })
  ]
};
```

---

## Troubleshooting

### Common Issues

#### 1. Query Routing Problems

**Issue**: Queries routing to wrong category

```typescript
// Debug routing
const results = interpreter.testQueryRouting("your query");
console.log(results);

// Solution: Add negative keywords or adjust priorities
{
  "category": "specific_category", 
  "negativeKeywords": ["general", "all"],
  "priority": 95  // Higher priority
}
```

**Issue**: Low confidence scores

```typescript
// Solution: Improve OpenAPI documentation
// Add better summaries, descriptions, and tags to your API spec
{
  "summary": "Get comprehensive fleet health status",
  "description": "Returns detailed health information including system status, database connectivity, and service availability",
  "tags": ["health", "monitoring", "status"]
}
```

#### 2. Backend Integration Issues

**Issue**: Connection timeouts

```bash
# Check backend URL
curl $FLEETPULSE_BACKEND_URL/health

# Increase timeout
export REQUEST_TIMEOUT=60000
```

**Issue**: CORS errors

```typescript
// Update CORS configuration
const corsOptions = {
  origin: process.env.CORS_ORIGIN?.split(',') || '*',
  credentials: true,
  optionsSuccessStatus: 200
};
```

#### 3. Performance Issues

**Issue**: Slow routing

```typescript
// Use smart interpreter with word boundaries
import { SmartFleetPulseInterpreter } from './smart-interpreter-example';
const interpreter = new SmartFleetPulseInterpreter(backendUrl, apiSpec);
```

**Issue**: Memory usage

```bash
# Monitor memory
node --max-old-space-size=4096 dist/server.js

# Profile memory usage
npm run profile
```

### Debugging Tools

#### 1. Routing Analysis

```typescript
// Test all routing rules
const results = interpreter.testQueryRouting(query);
results.forEach(result => {
  console.log(`${result.category}: ${result.matches} (${result.confidence})`);
});
```

#### 2. API Client Testing

```typescript
// Test backend connectivity
const client = new FleetPulseAPIClient(backendUrl);
const health = await client.checkHealth();
console.log('Backend health:', health);
```

#### 3. Performance Monitoring

```typescript
// Add timing to requests
const start = Date.now();
const result = await interpreter.interpretQuery(query);
console.log(`Query processed in ${Date.now() - start}ms`);
```

### Logs Analysis

Common log patterns:

```bash
# Find routing errors
grep "routing.*error" logs/app.log

# Check backend connectivity
grep "FleetPulse.*connection" logs/app.log

# Monitor query performance
grep "processing_time_ms.*[0-9]{4,}" logs/app.log
```

---

## Migration from Manual Routing

### Phase 1: Parallel Implementation
1. Keep existing `query-interpreter.ts`
2. Add `enhanced-query-interpreter.ts` alongside
3. Route 10% of traffic to new system
4. Compare results and accuracy

### Phase 2: Gradual Migration
1. Increase traffic to 50%
2. Monitor routing metadata and confidence scores
3. Refine rules based on real usage patterns
4. Add category-specific handlers

### Phase 3: Full Migration
1. Replace manual routing completely
2. Use routing metadata for analytics
3. Implement confidence-based fallbacks
4. Add performance monitoring

### Migration Checklist

- [ ] Generate routing config from current API
- [ ] Test routing with existing queries  
- [ ] Add enhanced interpreter alongside current one
- [ ] Implement A/B testing between interpreters
- [ ] Monitor routing accuracy and performance
- [ ] Gradually increase traffic to new system
- [ ] Update client integrations
- [ ] Remove old manual routing logic
- [ ] Add routing analytics and monitoring

---

This consolidated documentation provides everything needed to understand, deploy, and maintain the FleetPulse MCP server with its automated query routing system. The system transforms manual query routing into an intelligent, maintainable, and scalable solution that grows with your API.
