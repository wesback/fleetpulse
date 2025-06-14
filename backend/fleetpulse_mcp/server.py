#!/usr/bin/env python3
"""
FleetPulse MCP Server

This module implements a Model Context Protocol (MCP) server for FleetPulse,
exposing read-only API endpoints as MCP tools for AI assistant integration.

The server provides tools for:
- Listing hosts that have reported updates
- Getting update history for specific hosts (with filtering)
- Getting last update dates for all hosts
- Checking the health status of the FleetPulse backend

Usage:
    python -m fleetpulse_mcp.server
    
For development/testing:
    python fleetpulse_mcp/server.py
"""

import logging
import asyncio
import json
from typing import Any, Sequence

# Import MCP server components
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, TextContent, CallToolRequest, CallToolResult,
    Resource, ReadResourceRequest, ReadResourceResult,
    ListResourcesResult, ListToolsResult
)

# Import configuration
from fleetpulse_mcp.config.settings import config

# Import tool functions
from fleetpulse_mcp.tools.hosts_tool import list_hosts
from fleetpulse_mcp.tools.history_tool import get_host_history
from fleetpulse_mcp.tools.last_updates_tool import get_last_updates
from fleetpulse_mcp.tools.health_tool import check_health

# Configure logging
if config.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Create MCP server
server = Server(config.mcp_server_name)


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="fleetpulse_list_hosts",
            description="Get list of all hosts that have reported package updates to FleetPulse",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="fleetpulse_get_host_history",
            description="Get package update history for a specific host with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "hostname": {
                        "type": "string",
                        "description": "The hostname to get history for (required)"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Filter updates from this date (YYYY-MM-DD format, optional)"
                    },
                    "date_to": {
                        "type": "string", 
                        "description": "Filter updates to this date (YYYY-MM-DD format, optional)"
                    },
                    "os": {
                        "type": "string",
                        "description": "Filter by operating system (e.g., 'ubuntu', 'centos', optional)"
                    },
                    "package": {
                        "type": "string",
                        "description": "Filter by package name - supports partial matching (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of items per page, 1-1000 (default: 50)",
                        "minimum": 1,
                        "maximum": 1000,
                        "default": 50
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of items to skip for pagination (default: 0)",
                        "minimum": 0,
                        "default": 0
                    }
                },
                "required": ["hostname"]
            }
        ),
        Tool(
            name="fleetpulse_get_last_updates",
            description="Get the last update date and OS information for each host in FleetPulse",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="fleetpulse_check_health",
            description="Check the health status of the FleetPulse backend API",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "fleetpulse_list_hosts":
            result = await list_hosts()
            return [TextContent(type="text", text=result)]
            
        elif name == "fleetpulse_get_host_history":
            hostname = arguments.get("hostname")
            if not hostname:
                raise ValueError("hostname is required")
                
            result = await get_host_history(
                hostname=hostname,
                date_from=arguments.get("date_from"),
                date_to=arguments.get("date_to"),
                os=arguments.get("os"),
                package=arguments.get("package"),
                limit=arguments.get("limit", 50),
                offset=arguments.get("offset", 0)
            )
            return [TextContent(type="text", text=result)]
            
        elif name == "fleetpulse_get_last_updates":
            result = await get_last_updates()
            return [TextContent(type="text", text=result)]
            
        elif name == "fleetpulse_check_health":
            result = await check_health()
            return [TextContent(type="text", text=result)]
            
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        error_result = {
            "error": str(e),
            "tool": name,
            "arguments": arguments
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="fleetpulse://server-info",
            name="FleetPulse MCP Server Information",
            description="Information about the FleetPulse MCP server configuration and capabilities",
            mimeType="application/json"
        )
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Handle resource reading."""
    if uri == "fleetpulse://server-info":
        info = {
            "server_name": config.mcp_server_name,
            "server_version": config.mcp_server_version,
            "backend_url": config.base_url,
            "available_tools": [
                "fleetpulse_list_hosts",
                "fleetpulse_get_host_history", 
                "fleetpulse_get_last_updates",
                "fleetpulse_check_health"
            ],
            "description": "MCP server providing read-only access to FleetPulse package update tracking API",
            "documentation_url": "https://github.com/wesback/fleetpulse#mcp-server"
        }
        return json.dumps(info, indent=2)
    else:
        raise ValueError(f"Unknown resource: {uri}")


async def main():
    """Main entry point for the MCP server."""
    logger.info(f"Starting {config.mcp_server_name} v{config.mcp_server_version}")
    logger.info(f"Backend URL: {config.base_url}")
    
    # Validate configuration
    if not config.validate():
        logger.error("Invalid configuration - exiting")
        return 1
    
    logger.info("Configuration validated successfully")
    logger.info("MCP server tools available:")
    logger.info("  - fleetpulse_list_hosts: Get list of all hosts")
    logger.info("  - fleetpulse_get_host_history: Get update history with filtering")
    logger.info("  - fleetpulse_get_last_updates: Get last update dates for all hosts")
    logger.info("  - fleetpulse_check_health: Check backend health status")
    
    # Run the server with stdio transport
    async with stdio_server(server) as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        exit(1)