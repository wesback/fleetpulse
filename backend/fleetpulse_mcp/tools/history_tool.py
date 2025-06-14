"""
History Tool for FleetPulse MCP Server.

This tool exposes the /history/{hostname} endpoint from the FleetPulse API,
allowing users to retrieve update history for specific hosts with optional filtering.
"""

import httpx
import logging
from typing import Optional
from datetime import date
from fleetpulse_mcp.config.settings import config

logger = logging.getLogger(__name__)


async def get_host_history(
    hostname: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    os: Optional[str] = None,
    package: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> str:
    """
    Get update history for a specific host with optional filters.
    
    Args:
        hostname: The hostname to get history for
        date_from: Filter updates from this date (YYYY-MM-DD format, inclusive)
        date_to: Filter updates to this date (YYYY-MM-DD format, inclusive)
        os: Filter by operating system
        package: Filter by package name (partial match)
        limit: Number of items per page (1-1000, default: 50)
        offset: Number of items to skip (default: 0)
        
    Returns:
        JSON string containing the paginated update history
        
    Raises:
        Exception: If the API request fails or returns an error
    """
    try:
        # Validate hostname
        if not hostname or not hostname.strip():
            raise ValueError("Hostname is required and cannot be empty")
        
        # Validate limit
        if not (1 <= limit <= 1000):
            raise ValueError("Limit must be between 1 and 1000")
        
        # Validate offset
        if offset < 0:
            raise ValueError("Offset must be 0 or greater")
        
        # Validate dates if provided
        if date_from:
            try:
                date.fromisoformat(date_from)
            except ValueError:
                raise ValueError("date_from must be in YYYY-MM-DD format")
        
        if date_to:
            try:
                date.fromisoformat(date_to)
            except ValueError:
                raise ValueError("date_to must be in YYYY-MM-DD format")
        
        # Build query parameters
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if os:
            params["os"] = os
        if package:
            params["package"] = package
        
        url = f"{config.base_url}/history/{hostname}"
        
        async with httpx.AsyncClient(timeout=config.request_timeout) as client:
            logger.info(f"Requesting history for host '{hostname}' from: {url}")
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract pagination info
            items = data.get("items", [])
            total = data.get("total", 0)
            returned_limit = data.get("limit", limit)
            returned_offset = data.get("offset", offset)
            
            logger.info(f"Retrieved {len(items)} items (total: {total}) for host '{hostname}'")
            
            # Format the response nicely
            result = {
                "hostname": hostname,
                "update_history": items,
                "pagination": {
                    "total_items": total,
                    "returned_items": len(items),
                    "limit": returned_limit,
                    "offset": returned_offset,
                    "has_more": (returned_offset + len(items)) < total
                },
                "filters_applied": {
                    "date_from": date_from,
                    "date_to": date_to,
                    "os": os,
                    "package": package
                }
            }
            
            if not items:
                result["message"] = f"No update history found for host '{hostname}' with the specified filters"
            else:
                result["message"] = f"Found {total} total update(s) for host '{hostname}', showing {len(items)} item(s)"
            
            import json
            return json.dumps(result, indent=2, default=str)
            
    except ValueError as e:
        error_msg = f"Invalid parameter: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except httpx.TimeoutException:
        error_msg = f"Request to FleetPulse API timed out after {config.request_timeout} seconds"
        logger.error(error_msg)
        raise Exception(error_msg)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            error_msg = f"No update history found for host '{hostname}'"
        else:
            error_msg = f"FleetPulse API returned error {e.response.status_code}: {e.response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Failed to retrieve history for host '{hostname}': {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)