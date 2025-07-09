"""Database models using SQLModel."""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date
from utils.constants import (
    MAX_HOSTNAME_LENGTH,
    MAX_PACKAGE_NAME_LENGTH,
    MAX_VERSION_LENGTH,
    MAX_OS_LENGTH
)


class PackageUpdate(SQLModel, table=True):
    """Database model for package updates."""
    __tablename__ = "package_updates"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    hostname: str = Field(max_length=MAX_HOSTNAME_LENGTH, index=True)
    os: str = Field(max_length=MAX_OS_LENGTH)
    update_date: date = Field(index=True)
    name: str = Field(max_length=MAX_PACKAGE_NAME_LENGTH, index=True)
    old_version: str = Field(max_length=MAX_VERSION_LENGTH)
    new_version: str = Field(max_length=MAX_VERSION_LENGTH)