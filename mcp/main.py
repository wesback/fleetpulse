"""
FleetPulse MCP Server

A Model Context Protocol (MCP) server that provides read-only access to FleetPulse
backend data for AI assistants like Claude.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware

from .config import get_config, validate_config
from .telemetry import (
    initialize_telemetry, 
    shutdown_telemetry,
    instrument_fastapi_app,
    create_custom_span,
    record_mcp_request_metrics
)
from .client import get_backend_client, close_backend_client
from .tools import get_mcp_tools, MCPToolError
from .models import MCPErrorResponse


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    try:
        logger.info("Starting FleetPulse MCP Server")
        
        # Validate configuration
        validate_config()
        config = get_config()
        logger.info(f"Configuration validated - Backend: {config.fleetpulse_backend_url}")
        
        # Initialize OpenTelemetry
        initialize_telemetry()
        
        # Validate backend connection
        client = get_backend_client()
        is_connected = await client.validate_connection()
        if not is_connected:
            logger.warning("Backend connection validation failed - continuing with degraded functionality")
        else:
            logger.info("Backend connection validated successfully")
        
        logger.info(f"FleetPulse MCP Server started on port {config.mcp_port}")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FleetPulse MCP Server")
    await close_backend_client()
    shutdown_telemetry()


# Create FastAPI app
app = FastAPI(
    title="FleetPulse MCP Server",
    description="Model Context Protocol server for FleetPulse fleet management",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument FastAPI app for OpenTelemetry
instrument_fastapi_app(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MCP servers typically need broad access
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Telemetry middleware
@app.middleware("http")
async def telemetry_middleware(request, call_next):
    """Middleware to capture request telemetry."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Record MCP request metrics
    record_mcp_request_metrics(
        endpoint=request.url.path,
        status_code=response.status_code,
        duration_seconds=duration
    )
    
    return response


# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unexpected errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    error_response = MCPErrorResponse(
        error="Internal server error",
        detail=str(exc),
        error_code="INTERNAL_ERROR"
    )
    
    return HTTPException(
        status_code=500,
        detail=error_response.dict()
    )


# Get tools instance
tools = get_mcp_tools()


# REST API Endpoints (MCP tool implementations as REST endpoints for now)
@app.get("/")
async def root():
    """Root endpoint with basic information."""
    config = get_config()
    return {
        "service": "FleetPulse MCP Server",
        "version": "1.0.0",
        "description": "Model Context Protocol server for FleetPulse fleet management",
        "backend_url": config.fleetpulse_backend_url,
        "endpoints": {
            "health": "/health",
            "tools": "/tools",
            "hosts": "/hosts",
            "reports": "/reports",
            "packages": "/packages",
            "statistics": "/statistics",
            "search": "/search"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health Check Tool
    
    Check the health status of FleetPulse backend and MCP server.
    Returns comprehensive health information including database connectivity,
    telemetry status, and backend connection status.
    """
    return await tools.health_check()


@app.get("/hosts")
async def list_hosts():
    """
    List Hosts Tool
    
    List all hosts in the FleetPulse fleet.
    Returns detailed information about each host including hostname, operating system,
    last update date, and number of packages that have been updated.
    """
    hosts = await tools.list_hosts()
    return [host.dict() for host in hosts]


@app.get("/hosts/{hostname}")
async def get_host_details(hostname: str):
    """
    Get Host Details Tool
    
    Get detailed information for a specific host.
    Returns detailed host information including OS, last update date, and package count.
    """
    host = await tools.get_host_details(hostname)
    return host.dict()


@app.get("/reports")
async def get_update_reports(
    hostname: Optional[str] = Query(None, description="Optional hostname filter"),
    limit: int = Query(50, description="Maximum number of reports to return"),
    offset: int = Query(0, description="Number of reports to skip for pagination")
):
    """
    Get Update Reports Tool
    
    Get package update reports from the fleet.
    Returns list of update reports with package details grouped by host and date.
    """
    reports = await tools.get_update_reports(hostname=hostname, limit=limit, offset=offset)
    return [report.dict() for report in reports]


@app.get("/reports/{hostname}")
async def get_host_reports(
    hostname: str,
    limit: int = Query(50, description="Maximum number of reports to return"),
    offset: int = Query(0, description="Number of reports to skip for pagination")
):
    """
    Get Host Reports Tool
    
    Get update reports for a specific host.
    Returns list of update reports for the specified host.
    """
    reports = await tools.get_host_reports(hostname, limit=limit, offset=offset)
    return [report.dict() for report in reports]


@app.get("/packages")
async def list_packages():
    """
    List Packages Tool
    
    List all packages across the FleetPulse fleet.
    Returns information about each package including current version,
    list of hosts that have the package, and last update date.
    """
    packages = await tools.list_packages()
    return [package.dict() for package in packages]


@app.get("/packages/{package_name}")
async def get_package_details(package_name: str):
    """
    Get Package Details Tool
    
    Get detailed information about a specific package.
    Returns detailed package information including current version, hosts that have it,
    and last update date.
    """
    package = await tools.get_package_details(package_name)
    return package.dict()


@app.get("/stats")
async def get_fleet_statistics():
    """
    Fleet Statistics Tool
    
    Get aggregate statistics about the FleetPulse fleet.
    Returns comprehensive statistics including total hosts, reports, packages,
    activity metrics, most updated packages, and recent activity.
    """
    stats = await tools.get_fleet_statistics()
    return stats.dict()


@app.get("/search")
async def search(
    q: str = Query(..., description="Search query string"),
    result_type: Optional[str] = Query(None, description="Optional filter for result type (host, package, report)")
):
    """
    Search Tool
    
    Search across FleetPulse data including hosts, packages, and reports.
    Returns search results with relevance scores, grouped by type.
    """
    results = await tools.search(q, result_type=result_type)
    return results.dict()


@app.get("/tools")
async def list_tools():
    """List available MCP tools."""
    return {
        "tools": [
            {
                "name": "health_check",
                "description": "Check the health status of FleetPulse backend and MCP server",
                "endpoint": "/health"
            },
            {
                "name": "list_hosts",
                "description": "List all hosts in the FleetPulse fleet",
                "endpoint": "/hosts"
            },
            {
                "name": "get_host_details",
                "description": "Get detailed information for a specific host",
                "endpoint": "/hosts/{hostname}",
                "parameters": ["hostname"]
            },
            {
                "name": "get_update_reports",
                "description": "Get package update reports from the fleet",
                "endpoint": "/reports",
                "parameters": ["hostname (optional)", "limit", "offset"]
            },
            {
                "name": "get_host_reports",
                "description": "Get update reports for a specific host",
                "endpoint": "/reports/{hostname}",
                "parameters": ["hostname", "limit", "offset"]
            },
            {
                "name": "list_packages",
                "description": "List all packages across the FleetPulse fleet",
                "endpoint": "/packages"
            },
            {
                "name": "get_package_details",
                "description": "Get detailed information about a specific package",
                "endpoint": "/packages/{package_name}",
                "parameters": ["package_name"]
            },
            {
                "name": "get_fleet_statistics",
                "description": "Get aggregate statistics about the FleetPulse fleet",
                "endpoint": "/stats"
            },
            {
                "name": "search",
                "description": "Search across FleetPulse data",
                "endpoint": "/search",
                "parameters": ["q", "result_type (optional)"]
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    config = get_config()
    uvicorn.run(
        "mcp.main:app",
        host="0.0.0.0",
        port=config.mcp_port,
        reload=False,  # Don't use reload in production
        access_log=True
    )