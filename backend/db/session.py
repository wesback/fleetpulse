"""Database session management for FleetPulse."""

import logging
from sqlmodel import Session
from fastapi import HTTPException, status
from db.engine import get_engine

# Configure logging
logger = logging.getLogger(__name__)


def get_session():
    """Get database session with proper cleanup."""
    try:
        with Session(get_engine()) as session:
            yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session failed"
        )