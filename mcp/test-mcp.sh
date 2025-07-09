#!/bin/bash

# FleetPulse MCP Server Test Script
# This script demonstrates how to interact with the MCP server

MCP_URL="http://localhost:8001"

echo "🚀 Testing FleetPulse MCP Server..."
echo "=================================="

# Test health endpoint
echo "📊 Testing health endpoint..."
curl -s "$MCP_URL/health" | jq . || echo "Health check failed"
echo ""

# Test OpenAPI spec
echo "📋 Testing OpenAPI specification..."
curl -s "$MCP_URL/mcp/v1/openapi" | jq '.info' || echo "OpenAPI endpoint failed"
echo ""

# Test context submission
echo "📝 Testing context submission..."
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "type": "completion_request",
      "data": {
        "prompt": "Complete this sentence: The weather today is",
        "temperature": 0.7
      },
      "metadata": {
        "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
        "source": "test-script"
      }
    },
    "metadata": {
      "traceId": "trace-123",
      "spanId": "span-456"
    }
  }' \
  "$MCP_URL/mcp/v1/context" | jq . || echo "Context submission failed"
echo ""

# Test invalid context
echo "❌ Testing invalid context (should fail)..."
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"invalid": "structure"}' \
  "$MCP_URL/mcp/v1/context" | jq . || echo "Invalid context test failed"
echo ""

# Test FleetPulse query endpoint
echo "🔍 Testing FleetPulse query endpoint..."
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many hosts do we have?",
    "metadata": {
      "source": "test-script",
      "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
    }
  }' \
  "$MCP_URL/mcp/v1/query" | jq . || echo "FleetPulse query failed"
echo ""

# Test FleetPulse context with question
echo "💬 Testing context with FleetPulse question..."
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "type": "question",
      "data": {
        "question": "What packages are installed on server01?",
        "user": "test-user"
      },
      "metadata": {
        "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
        "source": "test-script"
      }
    }
  }' \
  "$MCP_URL/mcp/v1/context" | jq . || echo "FleetPulse context question failed"
echo ""

# Test another FleetPulse query
echo "📊 Testing statistics query..."
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me CPU usage statistics",
    "metadata": {
      "source": "test-script",
      "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
    }
  }' \
  "$MCP_URL/mcp/v1/query" | jq . || echo "Statistics query failed"
echo ""

echo "✅ All tests completed!"
echo ""
echo "💡 Note: Some FleetPulse tests may fail if the backend is not running."
echo "   Start the FleetPulse backend with: cd backend && uvicorn main:app --reload"
