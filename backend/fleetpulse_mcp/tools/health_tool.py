"""
Health Tool for FleetPulse MCP Server.

This tool exposes the /health endpoint from the FleetPulse API,
allowing users to check the health status of the FleetPulse backend.
"""

import httpx
import logging
from fleetpulse_mcp.config.settings import config

logger = logging.getLogger(__name__)


async def check_health() -> str:
    """
    Check the health status of the FleetPulse backend.
    
    Returns:
        JSON string containing the health status information
        
    Raises:
        Exception: If the API request fails or returns an error
    """
    try:
        url = f"{config.base_url}/health"
        
        async with httpx.AsyncClient(timeout=config.request_timeout) as client:
            logger.info(f"Requesting health status from: {url}")
            response = await client.get(url)
            
            # For health checks, we want to include the status code in our response
            health_data = {}
            
            try:
                health_data = response.json()
            except Exception:
                # If we can't parse JSON, create a basic response
                health_data = {
                    "status": "unknown",
                    "message": "Could not parse health response"
                }
            
            # Add HTTP status information
            result = {
                "http_status": response.status_code,
                "http_status_text": response.reason_phrase,
                "backend_health": health_data,
                "api_endpoint": url,
                "timestamp": None
            }
            
            # Add timestamp
            import datetime
            result["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
            
            # Determine overall status
            if response.status_code == 200:
                backend_status = health_data.get("status", "unknown")
                if backend_status == "healthy":
                    result["overall_status"] = "healthy"
                    result["message"] = "FleetPulse backend is healthy and operational"
                else:
                    result["overall_status"] = "degraded"
                    result["message"] = f"FleetPulse backend reports status: {backend_status}"
            else:
                result["overall_status"] = "unhealthy"
                result["message"] = f"FleetPulse backend returned HTTP {response.status_code}"
            
            logger.info(f"Health check completed: {result['overall_status']}")
            
            import json
            return json.dumps(result, indent=2, default=str)
            
    except httpx.TimeoutException:
        error_msg = f"Health check timed out after {config.request_timeout} seconds"
        logger.error(error_msg)
        
        # For health checks, return a structured error rather than raising
        result = {
            "overall_status": "timeout",
            "message": error_msg,
            "api_endpoint": f"{config.base_url}/health",
            "timestamp": None
        }
        
        import datetime, json
        result["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Health check failed: {str(e)}"
        logger.error(error_msg)
        
        # For health checks, return a structured error rather than raising
        result = {
            "overall_status": "error",
            "message": error_msg,
            "api_endpoint": f"{config.base_url}/health",
            "timestamp": None
        }
        
        import datetime, json
        result["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
        return json.dumps(result, indent=2)