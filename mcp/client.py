"""
HTTP client for communicating with FleetPulse backend API.

Handles all HTTP requests to the backend with retry logic and instrumentation.
"""

import asyncio
import logging
import time
from typing import List, Optional, Dict, Any, Union
from contextlib import asynccontextmanager

import httpx
from httpx import AsyncClient, Response, HTTPError, TimeoutException

from .config import get_config
from .models import (
    BackendHostsResponse, 
    BackendHostInfo, 
    BackendPaginatedResponse,
    HealthStatus
)
from .telemetry import create_custom_span, record_backend_api_metrics, add_baggage


logger = logging.getLogger(__name__)


class BackendConnectionError(Exception):
    """Raised when unable to connect to the backend."""
    pass


class BackendHTTPError(Exception):
    """Raised when backend returns an HTTP error."""
    
    def __init__(self, message: str, status_code: int, response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class FleetPulseBackendClient:
    """HTTP client for FleetPulse backend API."""
    
    def __init__(self):
        self.config = get_config()
        self.base_url = self.config.fleetpulse_backend_url.rstrip('/')
        self._client: Optional[AsyncClient] = None
    
    @asynccontextmanager
    async def get_client(self):
        """Get or create HTTP client with proper lifecycle management."""
        if self._client is None:
            self._client = AsyncClient(
                timeout=self.config.request_timeout,
                follow_redirects=True,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20
                )
            )
        
        try:
            yield self._client
        finally:
            # Keep client alive for reuse
            pass
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Response:
        """Make HTTP request with retry logic and instrumentation."""
        
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        with create_custom_span(
            f"backend_api_{method.lower()}",
            attributes={
                "http.method": method,
                "http.url": url,
                "backend.endpoint": endpoint,
                "retry.count": retry_count
            }
        ) as span:
            
            add_baggage("backend.endpoint", endpoint)
            add_baggage("http.method", method)
            
            try:
                async with self.get_client() as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        params=params,
                        json=json_data
                    )
                    
                    duration = time.time() - start_time
                    
                    # Record metrics
                    record_backend_api_metrics(
                        endpoint=endpoint,
                        status_code=response.status_code,
                        duration_seconds=duration
                    )
                    
                    # Update span attributes
                    span.set_attribute("http.status_code", response.status_code)
                    span.set_attribute("http.response_size", len(response.content))
                    span.set_attribute("duration.seconds", duration)
                    
                    # Handle HTTP errors
                    if response.status_code >= 400:
                        error_body = response.text
                        span.set_attribute("error", True)
                        span.set_attribute("error.message", f"HTTP {response.status_code}")
                        
                        # Retry on 5xx errors
                        if (response.status_code >= 500 and 
                            retry_count < self.config.max_retries):
                            
                            wait_time = 2 ** retry_count  # Exponential backoff
                            logger.warning(
                                f"Backend request failed with {response.status_code}, "
                                f"retrying in {wait_time}s (attempt {retry_count + 1})"
                            )
                            await asyncio.sleep(wait_time)
                            return await self._make_request(
                                method, endpoint, params, json_data, retry_count + 1
                            )
                        
                        raise BackendHTTPError(
                            f"Backend API returned {response.status_code}",
                            status_code=response.status_code,
                            response_body=error_body
                        )
                    
                    span.set_attribute("success", True)
                    return response
                    
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                duration = time.time() - start_time
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("duration.seconds", duration)
                
                # Record failed request metrics
                record_backend_api_metrics(
                    endpoint=endpoint,
                    status_code=0,  # Connection error
                    duration_seconds=duration
                )
                
                # Retry on connection errors
                if retry_count < self.config.max_retries:
                    wait_time = 2 ** retry_count
                    logger.warning(
                        f"Backend connection failed, retrying in {wait_time}s "
                        f"(attempt {retry_count + 1}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                    return await self._make_request(
                        method, endpoint, params, json_data, retry_count + 1
                    )
                
                raise BackendConnectionError(
                    f"Failed to connect to backend after {retry_count + 1} attempts: {e}"
                )
            
            except Exception as e:
                duration = time.time() - start_time
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                span.set_attribute("duration.seconds", duration)
                
                logger.error(f"Unexpected error in backend request: {e}")
                raise
    
    async def health_check(self) -> HealthStatus:
        """Check backend health status."""
        response = await self._make_request("GET", "/health")
        data = response.json()
        return HealthStatus(**data)
    
    async def list_hosts(self) -> List[str]:
        """Get list of all hosts."""
        response = await self._make_request("GET", "/hosts")
        data = BackendHostsResponse(**response.json())
        return data.hosts
    
    async def get_host_info(self) -> List[BackendHostInfo]:
        """Get host information with last update dates."""
        response = await self._make_request("GET", "/last-updates")
        data = response.json()
        return [BackendHostInfo(**item) for item in data]
    
    async def get_host_history(
        self,
        hostname: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        os: Optional[str] = None,
        package: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> BackendPaginatedResponse:
        """Get update history for a specific host."""
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        # Add optional filters
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if os:
            params["os"] = os
        if package:
            params["package"] = package
        
        response = await self._make_request(
            "GET", 
            f"/history/{hostname}",
            params=params
        )
        
        return BackendPaginatedResponse(**response.json())
    
    async def get_all_updates(
        self,
        limit: int = 100,
        offset: int = 0,
        hostname: Optional[str] = None,
        package: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all updates across the fleet by aggregating host histories."""
        
        all_updates = []
        
        # If specific hostname requested, just get that host's history
        if hostname:
            try:
                history = await self.get_host_history(
                    hostname=hostname,
                    date_from=date_from,
                    date_to=date_to,
                    package=package,
                    limit=limit,
                    offset=offset
                )
                return history.items
            except BackendHTTPError as e:
                if e.status_code == 404:
                    return []  # Host not found
                raise
        
        # Otherwise, get all hosts and aggregate their histories
        hosts = await self.list_hosts()
        
        for host in hosts:
            try:
                history = await self.get_host_history(
                    hostname=host,
                    date_from=date_from,
                    date_to=date_to,
                    package=package,
                    limit=limit,
                    offset=0  # Get from beginning for each host
                )
                all_updates.extend(history.items)
            except BackendHTTPError as e:
                if e.status_code == 404:
                    continue  # Skip hosts with no history
                # Log other errors but continue
                logger.warning(f"Failed to get history for host {host}: {e}")
                continue
        
        # Sort by update date (newest first) and apply pagination
        all_updates.sort(key=lambda x: x.get('update_date', ''), reverse=True)
        
        # Apply offset and limit
        end_index = offset + limit
        return all_updates[offset:end_index]
    
    async def validate_connection(self) -> bool:
        """Validate connection to the backend."""
        try:
            await self.health_check()
            return True
        except Exception as e:
            logger.error(f"Backend connection validation failed: {e}")
            return False


# Global client instance
_client: Optional[FleetPulseBackendClient] = None


def get_backend_client() -> FleetPulseBackendClient:
    """Get or create the global backend client."""
    global _client
    if _client is None:
        _client = FleetPulseBackendClient()
    return _client


async def close_backend_client():
    """Close the global backend client."""
    global _client
    if _client:
        await _client.close()
        _client = None