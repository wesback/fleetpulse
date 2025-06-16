"""
FleetPulse MCP Server

A Model Context Protocol (MCP) server that provides read-only access to FleetPulse
backend data for AI assistants like Claude.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional, Union

from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
import json
from pydantic import BaseModel

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
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )


# Get tools instance
tools = get_mcp_tools()


# MCP Protocol Models
class MCPRequest(BaseModel):
    """MCP JSON-RPC 2.0 request model."""
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None


class MCPResponse(BaseModel):
    """MCP JSON-RPC 2.0 response model."""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None


class MCPToolDefinition(BaseModel):
    """MCP tool definition model."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class MCPListToolsResponse(BaseModel):
    """MCP list tools response model."""
    tools: List[MCPToolDefinition]


# MCP Protocol Implementation
@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest):
    """
    MCP Protocol Endpoint
    
    Implements the Model Context Protocol JSON-RPC 2.0 specification.
    This endpoint allows FastMCP and other MCP clients to connect and use tools.
    """
    try:
        # Handle different MCP methods
        if request.method == "tools/list":
            # List available tools
            tool_definitions = [
                MCPToolDefinition(
                    name="health_check",
                    description="Check the health status of FleetPulse backend and MCP server",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                MCPToolDefinition(
                    name="list_hosts",
                    description="List all hosts in the FleetPulse fleet",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                MCPToolDefinition(
                    name="get_host_details",
                    description="Get detailed information for a specific host",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "hostname": {
                                "type": "string",
                                "description": "The hostname to get details for"
                            }
                        },
                        "required": ["hostname"]
                    }
                ),
                MCPToolDefinition(
                    name="get_update_reports",
                    description="Get system update reports with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "hostname": {
                                "type": "string",
                                "description": "Filter by hostname"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of reports to return"
                            }
                        },
                        "required": []
                    }
                ),
                MCPToolDefinition(
                    name="list_packages",
                    description="List all packages in the fleet",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                MCPToolDefinition(
                    name="get_package_details",
                    description="Get detailed information about a specific package",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "package_name": {
                                "type": "string",
                                "description": "Name of the package to get details for"
                            }
                        },
                        "required": ["package_name"]
                    }
                ),
                MCPToolDefinition(
                    name="get_fleet_statistics",
                    description="Get FleetPulse fleet statistics and metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                MCPToolDefinition(
                    name="search",
                    description="Search across FleetPulse data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query string"
                            },
                            "result_type": {
                                "type": "string",
                                "description": "Type of results to return (hosts, packages, reports)"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                MCPToolDefinition(
                    name="get_host_reports",
                    description="Get update reports for a specific host",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "hostname": {
                                "type": "string",
                                "description": "Hostname to get reports for"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of reports to return"
                            },
                            "offset": {
                                "type": "integer",
                                "description": "Number of reports to skip"
                            }
                        },
                        "required": ["hostname"]
                    }
                )
            ]
            
            response = MCPResponse(
                id=request.id,
                result=MCPListToolsResponse(tools=tool_definitions).model_dump()
            )
            return response.model_dump()
            
        elif request.method == "tools/call":
            # Call a specific tool
            if not request.params:
                raise HTTPException(status_code=400, detail="Missing tool call parameters")
            
            tool_name = request.params.get("name")
            tool_arguments = request.params.get("arguments", {})
            
            if not tool_name:
                raise HTTPException(status_code=400, detail="Missing tool name")
            
            # Map MCP tool names to internal tool methods
            tool_mapping = {
                "health_check": tools.health_check,
                "list_hosts": tools.list_hosts,
                "get_host_details": tools.get_host_details,
                "get_update_reports": tools.get_update_reports,
                "list_packages": tools.list_packages,
                "get_package_details": tools.get_package_details,
                "get_fleet_statistics": tools.get_fleet_statistics,
                "search": tools.search,
                "get_host_reports": tools.get_host_reports
            }
            
            if tool_name not in tool_mapping:
                raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
            
            tool_func = tool_mapping[tool_name]
            
            # Call the tool function with arguments
            try:
                if tool_arguments:
                    result = await tool_func(**tool_arguments)
                else:
                    result = await tool_func()
                
                # Convert result to JSON-serializable format
                if hasattr(result, 'model_dump'):
                    result = result.model_dump()
                elif isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'model_dump'):
                    result = [item.model_dump() for item in result]
                
                response = MCPResponse(
                    id=request.id,
                    result={
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2, default=str)
                            }
                        ]
                    }
                )
                return response.model_dump()
                
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                response = MCPResponse(
                    id=request.id,
                    error={
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    }
                )
                return response.model_dump()
        
        elif request.method == "initialize":
            # MCP initialization
            response = MCPResponse(
                id=request.id,
                result={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "FleetPulse MCP Server",
                        "version": "1.0.0"
                    }
                }
            )
            return response.model_dump()
            
        elif request.method == "ping":
            # MCP ping for connection testing
            response = MCPResponse(
                id=request.id,
                result={}
            )
            return response.model_dump()
            
        else:
            # Unknown method
            response = MCPResponse(
                id=request.id,
                error={
                    "code": -32601,
                    "message": "Method not found",
                    "data": f"Unknown method: {request.method}"
                }
            )
            return response.model_dump()
            
    except Exception as e:
        logger.error(f"MCP endpoint error: {e}")
        response = MCPResponse(
            id=request.id,
            error={
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            }
        )
        return response.model_dump()


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
    return [host.model_dump() for host in hosts]


@app.get("/hosts/{hostname}")
async def get_host_details(hostname: str):
    """
    Get Host Details Tool
    
    Get detailed information for a specific host.
    Returns detailed host information including OS, last update date, and package count.
    """
    host = await tools.get_host_details(hostname)
    return host.model_dump()


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
    return [report.model_dump() for report in reports]


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
    return [report.model_dump() for report in reports]


@app.get("/packages")
async def list_packages():
    """
    List Packages Tool
    
    List all packages across the FleetPulse fleet.
    Returns information about each package including current version,
    list of hosts that have the package, and last update date.
    """
    packages = await tools.list_packages()
    return [package.model_dump() for package in packages]


@app.get("/packages/{package_name}")
async def get_package_details(package_name: str):
    """
    Get Package Details Tool
    
    Get detailed information about a specific package.
    Returns detailed package information including current version, hosts that have it,
    and last update date.
    """
    package = await tools.get_package_details(package_name)
    return package.model_dump()


@app.get("/stats")
async def get_fleet_statistics():
    """
    Fleet Statistics Tool
    
    Get aggregate statistics about the FleetPulse fleet.
    Returns comprehensive statistics including total hosts, reports, packages,
    activity metrics, most updated packages, and recent activity.
    """
    stats = await tools.get_fleet_statistics()
    return stats.model_dump()


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
    return results.model_dump()


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


@app.post("/sse")
async def sse_endpoint(request: Request):
    """
    SSE Endpoint for Claude Desktop integration.
    Accepts POST requests with JSON specifying the tool and parameters, invokes the tool, and streams the result as SSE.
    Example request body:
    {
        "tool": "list_hosts",
        "params": {}
    }
    """
    try:
        data = await request.json()
        tool_name = data.get("tool")
        params = data.get("params", {})
        if not tool_name or not hasattr(tools, tool_name):
            return JSONResponse(status_code=400, content={"error": "Invalid or missing tool name"})
        tool_func = getattr(tools, tool_name)
        # Call the tool function with params
        result = await tool_func(**params) if params else await tool_func()
        # Stream the result as SSE (single event for now)
        async def event_generator():
            yield {
                "event": "result",
                "data": json.dumps(result, default=str)
            }
        return EventSourceResponse(event_generator())
    except Exception as e:
        logger.error(f"SSE endpoint error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# MCP Protocol (JSON-RPC 2.0) Endpoint
@app.post("/mcp")
async def mcp_protocol(request: Request):
    """
    MCP Protocol Endpoint
    
    Implements the Model Context Protocol (MCP) using JSON-RPC 2.0.
    Accepts JSON-RPC requests, invokes the corresponding MCP tool,
    and returns the result as JSON-RPC response.
    
    Example request:
    {
        "jsonrpc": "2.0",
        "method": "list_hosts",
        "params": {},
        "id": 1
    }
    
    Example response:
    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": [...]
    }
    """
    try:
        # Parse JSON-RPC request
        json_rpc = await request.json()
        method = json_rpc.get("method")
        params = json_rpc.get("params", {})
        request_id = json_rpc.get("id")
        
        if not method or not hasattr(tools, method):
            return JSONResponse(status_code=400, content={"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}}, media_type="application/json")
        
        tool_func = getattr(tools, method)
        # Call the tool function with params
        result = await tool_func(**params) if params else await tool_func()
        
        # Build JSON-RPC response
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result.model_dump() if hasattr(result, "model_dump") else result
        }
        
        return JSONResponse(content=response, media_type="application/json")
    
    except Exception as e:
        logger.error(f"MCP Protocol error: {e}")
        return JSONResponse(status_code=500, content={"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}}, media_type="application/json")


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