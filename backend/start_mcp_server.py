#!/usr/bin/env python3
"""
FleetPulse MCP Server Startup Script

This script provides an easy way to start the FleetPulse MCP server
in either stdio mode (for direct MCP clients) or HTTP mode (for chatbots
and other external clients).

Usage:
    # Start in stdio mode (default - for MCP clients)
    python start_mcp_server.py
    
    # Start in HTTP mode (for chatbots)
    MCP_MODE=http python start_mcp_server.py
    
    # Or set port for HTTP mode
    MCP_MODE=http MCP_HTTP_PORT=8001 python start_mcp_server.py
"""

import sys
import os
import asyncio
import logging

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Import configuration
from fleetpulse_mcp.config.settings import config

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point for the MCP server."""
    # Determine mode from environment
    mode = os.getenv("MCP_MODE", "stdio").lower()
    
    if mode == "http":
        # Start HTTP server for chatbot connectivity
        logger.info("Starting FleetPulse MCP server in HTTP mode")
        from fleetpulse_mcp.http_server import start_http_server
        
        host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_HTTP_PORT", "8001"))
        
        await start_http_server(host, port)
        
    elif mode == "stdio":
        # Start stdio server for direct MCP client connectivity
        logger.info("Starting FleetPulse MCP server in stdio mode")
        from fleetpulse_mcp.server import main as stdio_main
        
        await stdio_main()
        
    else:
        logger.error(f"Invalid MCP_MODE: {mode}. Valid options are 'stdio' or 'http'")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)