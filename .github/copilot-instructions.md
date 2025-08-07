# FleetPulse - GitHub Copilot Instructions

**Always follow these repository-specific instructions first. Only use general search or bash commands when the information here is incomplete or found to be incorrect.**

FleetPulse is a lightweight dashboard for monitoring Linux package updates across your fleet. It consists of three main services: FastAPI backend (Python), React frontend, and TypeScript MCP server.

## Working Effectively

### Bootstrap and Build - NEVER CANCEL Build Commands
Always run these commands with sufficient timeouts. Build processes may take several minutes.

**Backend Setup (Python 3.12+)**:
```bash
# Create virtual environment (5 seconds)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (90 seconds - NEVER CANCEL, set timeout 180s+)
pip install -r backend/requirements.txt
```

**Frontend Setup (Node 18+)**:
```bash
cd frontend
# Install dependencies (160 seconds - NEVER CANCEL, set timeout 300s+)
npm install

# Build production assets (20 seconds - NEVER CANCEL, set timeout 60s+)
npm run build
```

**MCP Server Setup (Node 18+)**:
```bash
cd mcp
# Install dependencies (20 seconds - NEVER CANCEL, set timeout 60s+)
npm install

# Build TypeScript (3 seconds)
npm run build
```

**Run All Tests (10 seconds)**:
```bash
./run_tests.sh
```

### Running the Application

**Backend Development**:
```bash
# From project root with .venv activated
source .venv/bin/activate
python -m backend.main
# Runs on http://localhost:8000
```

**Frontend Development**:
```bash
cd frontend
# Note: npm start may fail due to webpack config issues
# Always use npm run build for production builds
npm run build
# Serve build/ directory with static server
```

**MCP Server Development**:
```bash
cd mcp
# Set backend URL for local development
FLEETPULSE_API_URL=http://localhost:8000 npm run dev
# Runs on http://localhost:8001
```

**Docker Compose (Full Stack)**:
```bash
# Build and start all services (may fail on some systems due to Docker issues)
docker compose up --build -d
# Frontend: http://localhost:8080
# Backend: http://localhost:8000
# MCP: http://localhost:8001
```

## Validation Scenarios

Always test these scenarios after making changes:

**Backend API Validation**:
```bash
# Health check
curl http://localhost:8000/health

# Submit a test report
curl -X POST http://localhost:8000/report \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "test-host",
    "os": "ubuntu", 
    "update_date": "2025-08-07",
    "updated_packages": [{"name": "nginx", "old_version": "1.18.0", "new_version": "1.20.2"}]
  }'

# Verify data was stored
curl http://localhost:8000/hosts
curl http://localhost:8000/statistics
```

**MCP Server Validation**:
```bash
# Health check
curl http://localhost:8001/health

# Test context endpoint
curl -X POST http://localhost:8001/mcp/v1/context \
  -H "Content-Type: application/json" \
  -d '{"context": {"type": "question", "data": {"question": "Show fleet status"}}}'
```

## Key Project Structure

- `backend/` - FastAPI application with SQLite database
  - `main.py` - Application entry point (run as `python -m backend.main`)
  - `routers/` - API endpoint handlers
  - `models/` - Pydantic models and database schemas
  - `db/` - Database engine and session management
  - `telemetry.py` - OpenTelemetry instrumentation
- `frontend/` - React application with Material UI
  - `src/` - React components and pages
  - `package.json` - Build scripts and dependencies
- `mcp/` - TypeScript MCP server
  - `src/server.ts` - Express.js MCP server
  - `src/services/` - FleetPulse API client and query processing
  - `tests/` - Jest test suites
- `docker-compose.yml` - Full stack deployment
- `run_tests.sh` - Comprehensive test runner
- `.env.example` - Environment configuration template

## Build Timing Expectations

- **Backend pip install**: 90 seconds (timeout: 180s+)
- **Frontend npm install**: 160 seconds (timeout: 300s+) 
- **Frontend npm run build**: 20 seconds (timeout: 60s+)
- **MCP npm install**: 20 seconds (timeout: 60s+)
- **MCP npm run build**: 3 seconds
- **Full test suite**: 10 seconds
- **Docker compose build**: May fail due to system constraints

## Common Issues and Solutions

**Backend Import Errors**: Always run backend as module from project root: `python -m backend.main`

**Frontend Development Server Issues**: `npm start` may fail due to webpack configuration. Always use `npm run build` for production builds.

**Telemetry Errors**: Backend shows Jaeger connection errors when telemetry services aren't running. This is normal in development - the application functions correctly.

**Missing Tests**: The repository has tests for MCP server but minimal backend/frontend tests. This is expected - focus on integration testing via API validation.

**Docker Build Failures**: Docker compose may fail on resource-constrained systems. Use local development mode instead.

## Validation Requirements

Before committing changes:
1. Run `./run_tests.sh` - must complete successfully
2. Start backend and test API endpoints as shown above
3. Build frontend successfully with `npm run build`
4. Build and test MCP server with `npm run build && npm test`
5. Verify no new errors in application logs during basic operations

## Critical Reminders

- **NEVER CANCEL** long-running build commands - they are expected to take 2-3 minutes
- Always use virtual environment for Python development
- Backend must be run as module: `python -m backend.main`
- Always validate API functionality with curl commands after changes
- OpenTelemetry errors about Jaeger connectivity are expected in development
- Docker builds may fail - use local development setup as primary method

---

## General Coding Standards

- **Python**: Use FastAPI dependency injection, Pydantic models, proper error handling
- **TypeScript**: Use Zod validation, proper async/await, comprehensive error handling
- **React**: Use Material UI components, proper state management, error boundaries
- **Testing**: pytest for backend, Jest for MCP, minimal frontend tests (as designed)
- **Security**: All inputs validated via Pydantic/Zod, no SQL injection risks (SQLModel ORM)
- **Performance**: Database queries optimized, proper indexing, telemetry for monitoring