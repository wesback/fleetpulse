"""
Last Updates Tool for FleetPulse MCP Server.

This tool exposes the /last-updates endpoint from the FleetPulse API,
allowing users to retrieve the last update date for each host.
"""

import httpx
import logging
from fleetpulse_mcp.config.settings import config

logger = logging.getLogger(__name__)


async def get_last_updates() -> str:
    """
    Get the last update date for each host.
    
    Returns:
        JSON string containing the last update information for all hosts
        
    Raises:
        Exception: If the API request fails or returns an error
    """
    try:
        url = f"{config.base_url}/last-updates"
        
        async with httpx.AsyncClient(timeout=config.request_timeout) as client:
            logger.info(f"Requesting last updates from: {url}")
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Retrieved last update info for {len(data)} hosts")
            
            # Format the response nicely
            if not data:
                result = {
                    "hosts": [],
                    "total_count": 0,
                    "message": "No hosts have reported updates yet."
                }
            else:
                # Sort by last update date (most recent first)
                sorted_data = sorted(data, key=lambda x: x.get('last_update', ''), reverse=True)
                
                result = {
                    "hosts": sorted_data,
                    "total_count": len(sorted_data),
                    "message": f"Found last update information for {len(sorted_data)} host(s)",
                    "summary": {
                        "most_recent_update": sorted_data[0]['last_update'] if sorted_data else None,
                        "oldest_update": sorted_data[-1]['last_update'] if sorted_data else None
                    }
                }
            
            import json
            return json.dumps(result, indent=2, default=str)
            
    except httpx.TimeoutException:
        error_msg = f"Request to FleetPulse API timed out after {config.request_timeout} seconds"
        logger.error(error_msg)
        raise Exception(error_msg)
    except httpx.HTTPStatusError as e:
        error_msg = f"FleetPulse API returned error {e.response.status_code}: {e.response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Failed to retrieve last updates: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)