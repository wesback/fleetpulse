#!/usr/bin/env python3
"""
FleetPulse MCP HTTP Server

This module provides an HTTP wrapper around the MCP server to enable
external clients (like chatbots) to connect via HTTP REST API instead
of just stdio transport.

The server exposes the same MCP tools as HTTP endpoints and returns
JSON responses suitable for AI assistant consumption.
"""

import logging
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import MCP tools directly
from fleetpulse_mcp.tools.hosts_tool import list_hosts
from fleetpulse_mcp.tools.history_tool import get_host_history
from fleetpulse_mcp.tools.last_updates_tool import get_last_updates
from fleetpulse_mcp.tools.health_tool import check_health
from fleetpulse_mcp.config.settings import config

# Configure logging
if config.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Pydantic models for request validation
class HostHistoryRequest(BaseModel):
    hostname: str = Field(..., description="The hostname to get history for")
    date_from: Optional[str] = Field(None, description="Filter updates from this date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Filter updates to this date (YYYY-MM-DD)")
    os: Optional[str] = Field(None, description="Filter by operating system")
    package: Optional[str] = Field(None, description="Filter by package name")
    limit: int = Field(50, description="Number of items per page", ge=1, le=1000)
    offset: int = Field(0, description="Number of items to skip", ge=0)

# Create FastAPI app
app = FastAPI(
    title="FleetPulse MCP HTTP Server",
    description="HTTP wrapper for FleetPulse MCP tools to enable chatbot integration",
    version=config.mcp_server_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": config.mcp_server_name,
        "version": config.mcp_server_version,
        "description": "HTTP wrapper for FleetPulse MCP tools",
        "backend_url": config.base_url,
        "available_endpoints": [
            "/tools/list-hosts",
            "/tools/host-history",
            "/tools/last-updates", 
            "/tools/health"
        ],
        "documentation": "/docs"
    }

@app.get("/health")
async def http_health():
    """Health check for the HTTP server itself."""
    return {"status": "healthy", "server": "mcp-http"}

@app.get("/tools/list-hosts")
async def api_list_hosts():
    """Get list of all hosts that have reported package updates."""
    try:
        result = await list_hosts()
        # Parse the JSON string returned by the tool
        return json.loads(result)
    except Exception as e:
        logger.error(f"Error in list_hosts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/host-history")
async def api_get_host_history(request: HostHistoryRequest):
    """Get package update history for a specific host with filtering."""
    try:
        result = await get_host_history(
            hostname=request.hostname,
            date_from=request.date_from,
            date_to=request.date_to,
            os=request.os,
            package=request.package,
            limit=request.limit,
            offset=request.offset
        )
        # Parse the JSON string returned by the tool
        return json.loads(result)
    except Exception as e:
        logger.error(f"Error in get_host_history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/host-history/{hostname}")
async def api_get_host_history_get(
    hostname: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    os: Optional[str] = None,
    package: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """GET version of host history endpoint for simple queries."""
    try:
        result = await get_host_history(
            hostname=hostname,
            date_from=date_from,
            date_to=date_to,
            os=os,
            package=package,
            limit=limit,
            offset=offset
        )
        return json.loads(result)
    except Exception as e:
        logger.error(f"Error in get_host_history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/last-updates")
async def api_get_last_updates():
    """Get the last update date and OS information for each host."""
    try:
        result = await get_last_updates()
        return json.loads(result)
    except Exception as e:
        logger.error(f"Error in get_last_updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/health")
async def api_check_health():
    """Check the health status of the FleetPulse backend API."""
    try:
        result = await check_health()
        return json.loads(result)
    except Exception as e:
        logger.error(f"Error in check_health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled error in {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )

async def start_http_server(host: str = "0.0.0.0", port: int = 8001):
    """Start the HTTP server."""
    logger.info(f"Starting FleetPulse MCP HTTP Server on {host}:{port}")
    logger.info(f"Backend URL: {config.base_url}")
    logger.info("Available endpoints:")
    logger.info("  GET  /tools/list-hosts - Get list of all hosts")
    logger.info("  POST /tools/host-history - Get host history with filtering")
    logger.info("  GET  /tools/host-history/{hostname} - Get host history (simple)")
    logger.info("  GET  /tools/last-updates - Get last update dates")
    logger.info("  GET  /tools/health - Check backend health")
    logger.info("  GET  /docs - API documentation")
    
    # Validate configuration
    if not config.validate():
        logger.error("Invalid configuration - exiting")
        return 1
    
    # Run the server
    uvicorn_config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info" if not config.debug else "debug"
    )
    server = uvicorn.Server(uvicorn_config)
    await server.serve()

if __name__ == "__main__":
    import asyncio
    import os
    
    # Get host and port from environment
    host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_HTTP_PORT", "8001"))
    
    try:
        asyncio.run(start_http_server(host, port))
    except KeyboardInterrupt:
        logger.info("HTTP server stopped by user")
    except Exception as e:
        logger.error(f"HTTP server error: {e}")
        exit(1)