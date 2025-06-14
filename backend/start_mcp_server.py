#!/usr/bin/env python3
"""
FleetPulse MCP Server Startup Script

This script provides an easy way to start the FleetPulse MCP server
with proper configuration and error handling.
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Import and run the MCP server
if __name__ == "__main__":
    from fleetpulse_mcp.server import main
    import asyncio
    asyncio.run(main())