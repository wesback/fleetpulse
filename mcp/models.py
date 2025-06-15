"""
Pydantic data models for FleetPulse MCP Server.

These models match the API responses from the FleetPulse backend.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PackageUpdate(BaseModel):
    """Model for individual package update information."""
    name: str = Field(description="Package name")
    old_version: str = Field(description="Previous version")
    new_version: str = Field(description="New version")


class Host(BaseModel):
    """Model for host information."""
    hostname: str = Field(description="Hostname")
    os: str = Field(description="Operating system")
    last_update: date = Field(description="Last update date")
    packages_count: Optional[int] = Field(default=None, description="Number of packages updated")


class UpdateReport(BaseModel):
    """Model for package update report."""
    id: int = Field(description="Report ID")
    hostname: str = Field(description="Hostname")
    os: str = Field(description="Operating system")
    update_date: date = Field(description="Update date")
    updated_packages: List[PackageUpdate] = Field(description="List of updated packages")


class PackageInfo(BaseModel):
    """Model for package information across the fleet."""
    name: str = Field(description="Package name")
    current_version: Optional[str] = Field(default=None, description="Current version")
    hosts: List[str] = Field(description="List of hosts with this package")
    last_updated: Optional[date] = Field(default=None, description="Last update date")


class HealthStatus(BaseModel):
    """Model for health status information."""
    status: str = Field(description="Overall health status")
    database: str = Field(description="Database connection status")
    telemetry: Dict[str, Any] = Field(description="Telemetry configuration")
    timestamp: Optional[datetime] = Field(default=None, description="Health check timestamp")


class FleetStatistics(BaseModel):
    """Model for fleet-wide statistics."""
    total_hosts: int = Field(description="Total number of hosts")
    total_reports: int = Field(description="Total number of update reports")
    total_packages: int = Field(description="Total number of unique packages")
    active_hosts_last_7_days: int = Field(description="Hosts active in last 7 days")
    active_hosts_last_30_days: int = Field(description="Hosts active in last 30 days")
    most_updated_packages: List[Dict[str, Any]] = Field(description="Most frequently updated packages")
    recent_activity: List[Dict[str, Any]] = Field(description="Recent update activity")


class SearchResult(BaseModel):
    """Model for search results."""
    result_type: str = Field(description="Type of result (host, package, report)")
    data: Dict[str, Any] = Field(description="Result data")
    relevance_score: Optional[float] = Field(default=None, description="Relevance score")


class SearchResponse(BaseModel):
    """Model for search response."""
    query: str = Field(description="Search query")
    results: List[SearchResult] = Field(description="Search results")
    total_results: int = Field(description="Total number of results")


class PaginatedResponse(BaseModel):
    """Generic paginated response model."""
    items: List[Any] = Field(description="Items in current page")
    total: int = Field(description="Total number of items")
    limit: int = Field(description="Items per page")
    offset: int = Field(description="Number of items skipped")


class MCPErrorResponse(BaseModel):
    """Model for MCP error responses."""
    error: str = Field(description="Error message")
    detail: Optional[str] = Field(default=None, description="Error details")
    error_code: Optional[str] = Field(default=None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


# Backend API response models (for internal use)
class BackendHostsResponse(BaseModel):
    """Backend /hosts response."""
    hosts: List[str]


class BackendHostInfo(BaseModel):
    """Backend host info from /last-updates."""
    hostname: str
    os: str
    last_update: date


class BackendPaginatedResponse(BaseModel):
    """Backend paginated response."""
    items: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


class BackendPackageUpdate(BaseModel):
    """Backend package update model."""
    id: int
    hostname: str
    os: str
    update_date: date
    name: str
    old_version: str
    new_version: str