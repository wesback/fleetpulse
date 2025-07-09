"""Pydantic models for request/response schemas."""
from sqlmodel import SQLModel, Field
from typing import List, Optional, Dict, Any
from datetime import date
from utils.constants import (
    MAX_HOSTNAME_LENGTH,
    MAX_PACKAGE_NAME_LENGTH,
    MAX_VERSION_LENGTH,
    MAX_OS_LENGTH
)
from models.database import PackageUpdate


class PackageInfo(SQLModel):
    """Model for individual package update information."""
    name: str = Field(max_length=MAX_PACKAGE_NAME_LENGTH)
    old_version: str = Field(max_length=MAX_VERSION_LENGTH)
    new_version: str = Field(max_length=MAX_VERSION_LENGTH)


class UpdateIn(SQLModel):
    """Input model for package update reports."""
    hostname: str = Field(max_length=MAX_HOSTNAME_LENGTH)
    os: str = Field(max_length=MAX_OS_LENGTH)
    update_date: date
    updated_packages: List[PackageInfo]


class HostInfo(SQLModel):
    """Model for host information."""
    hostname: str
    os: str
    last_update: date


class ErrorResponse(SQLModel):
    """Standard error response model."""
    error: str
    detail: Optional[str] = None


class PaginatedResponse(SQLModel):
    """Response model for paginated data."""
    items: List[PackageUpdate]
    total: int
    limit: int
    offset: int


class StatisticsResponse(SQLModel):
    """Response model for statistics data."""
    total_hosts: int
    total_updates: int
    recent_updates: int  # updates in last 30 days
    top_packages: List[Dict[str, Any]]
    updates_by_os: List[Dict[str, Any]]
    updates_timeline: List[Dict[str, Any]]
    host_activity: List[Dict[str, Any]]