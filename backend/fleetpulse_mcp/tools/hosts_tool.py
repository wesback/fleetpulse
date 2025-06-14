"""
Hosts Tool for FleetPulse MCP Server.

This tool exposes the /hosts endpoint from the FleetPulse API,
allowing users to retrieve the list of all hosts that have reported updates.
"""

import httpx
import logging
from typing import List, Dict, Any
from fleetpulse_mcp.config.settings import config

logger = logging.getLogger(__name__)


async def list_hosts() -> str:
    """
    Get list of all hosts that have reported updates.
    
    Returns:
        JSON string containing the list of hosts
        
    Raises:
        Exception: If the API request fails or returns an error
    """
    try:
        url = f"{config.base_url}/hosts"
        
        async with httpx.AsyncClient(timeout=config.request_timeout) as client:
            logger.info(f"Requesting hosts list from: {url}")
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            hosts = data.get("hosts", [])
            
            logger.info(f"Retrieved {len(hosts)} hosts")
            
            # Return formatted response
            if not hosts:
                return "No hosts have reported updates yet."
            
            # Format the response nicely
            result = {
                "hosts": hosts,
                "total_count": len(hosts),
                "message": f"Found {len(hosts)} host(s) that have reported updates"
            }
            
            import json
            return json.dumps(result, indent=2)
            
    except httpx.TimeoutException:
        error_msg = f"Request to FleetPulse API timed out after {config.request_timeout} seconds"
        logger.error(error_msg)
        raise Exception(error_msg)
    except httpx.HTTPStatusError as e:
        error_msg = f"FleetPulse API returned error {e.response.status_code}: {e.response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Failed to retrieve hosts: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)