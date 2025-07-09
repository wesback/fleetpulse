"""Database models using SQLModel."""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date
from backend.utils import constants


class PackageUpdate(SQLModel, table=True):
    """Database model for package updates."""
    __tablename__ = "package_updates"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    hostname: str = Field(max_length=constants.MAX_HOSTNAME_LENGTH, index=True)
    os: str = Field(max_length=constants.MAX_OS_LENGTH)
    update_date: date = Field(index=True)
    name: str = Field(max_length=constants.MAX_PACKAGE_NAME_LENGTH, index=True)
    old_version: str = Field(max_length=constants.MAX_VERSION_LENGTH)
    new_version: str = Field(max_length=constants.MAX_VERSION_LENGTH)