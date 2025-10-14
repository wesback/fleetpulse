#!/bin/bash
# Integration test script for database configurations

set -e

echo "=== FleetPulse Database Configuration Integration Tests ==="
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function test_health() {
    local url=$1
    local expected_db_type=$2
    
    echo "Testing health endpoint: $url"
    response=$(curl -s $url)
    
    if echo "$response" | grep -q '"status":"healthy"'; then
        echo -e "${GREEN}✓ Health check passed${NC}"
    else
        echo -e "${RED}✗ Health check failed${NC}"
        echo "Response: $response"
        return 1
    fi
    
    if echo "$response" | grep -q "\"type\":\"$expected_db_type\""; then
        echo -e "${GREEN}✓ Database type is $expected_db_type${NC}"
    else
        echo -e "${RED}✗ Expected database type $expected_db_type${NC}"
        echo "Response: $response"
        return 1
    fi
    
    echo
}

echo "1. Testing SQLite configuration (default)"
echo "   Starting application with SQLite..."

# Clean up any existing containers
docker compose down -v 2>/dev/null || true

# Start with SQLite (default)
docker compose up -d backend

# Wait for backend to be ready
echo "   Waiting for backend to start..."
sleep 10

# Check if container is running
if docker compose ps backend | grep -q "Up"; then
    echo -e "${GREEN}✓ Backend container is running${NC}"
else
    echo -e "${RED}✗ Backend container failed to start${NC}"
    docker compose logs backend
    exit 1
fi

# Test health endpoint
if test_health "http://localhost:8000/health" "sqlite"; then
    echo -e "${GREEN}✓ SQLite configuration test passed${NC}"
else
    echo -e "${RED}✗ SQLite configuration test failed${NC}"
    docker compose logs backend
    exit 1
fi

# Clean up
docker compose down -v

echo
echo "2. Testing PostgreSQL configuration"
echo "   Starting application with PostgreSQL..."

# Start with PostgreSQL
docker compose -f docker-compose.postgres.yml up -d postgres backend

# Wait for services to be ready
echo "   Waiting for PostgreSQL to start..."
sleep 15

# Check if containers are running
if docker compose -f docker-compose.postgres.yml ps postgres | grep -q "Up"; then
    echo -e "${GREEN}✓ PostgreSQL container is running${NC}"
else
    echo -e "${RED}✗ PostgreSQL container failed to start${NC}"
    docker compose -f docker-compose.postgres.yml logs postgres
    exit 1
fi

if docker compose -f docker-compose.postgres.yml ps backend | grep -q "Up"; then
    echo -e "${GREEN}✓ Backend container is running${NC}"
else
    echo -e "${RED}✗ Backend container failed to start${NC}"
    docker compose -f docker-compose.postgres.yml logs backend
    exit 1
fi

# Test health endpoint
if test_health "http://localhost:8000/health" "postgresql"; then
    echo -e "${GREEN}✓ PostgreSQL configuration test passed${NC}"
else
    echo -e "${RED}✗ PostgreSQL configuration test failed${NC}"
    docker compose -f docker-compose.postgres.yml logs backend
    exit 1
fi

# Clean up
docker compose -f docker-compose.postgres.yml down -v

echo
echo -e "${GREEN}=== All integration tests passed! ===${NC}"
echo
echo "Summary:"
echo "  ✓ SQLite (default) configuration works"
echo "  ✓ PostgreSQL configuration works"
echo "  ✓ Health endpoints report correct database types"
