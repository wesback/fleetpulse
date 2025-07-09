"""Database engine management for FleetPulse."""

import os
import logging
from sqlalchemy import create_engine, text
from fastapi import HTTPException, status
from backend.utils import constants

# Configure logging
logger = logging.getLogger(__name__)

# Global engine variable
engine = None


def get_engine():
    """Get database engine with proper error handling."""
    global engine
    if engine is None:
        try:
            # Use current value from constants module to allow test patching
            db_path = constants.DB_PATH
            logger.info(f"Creating database engine for: {db_path}")
            
            # Ensure the directory exists
            db_dir = os.path.dirname(db_path)
            if not os.path.exists(db_dir):
                logger.info(f"Creating database directory: {db_dir}")
                os.makedirs(db_dir, exist_ok=True)
            
            # Check if we can write to the database directory
            if not os.access(db_dir, os.W_OK):
                raise PermissionError(f"Cannot write to database directory: {db_dir}")
            
            engine = create_engine(
                f"sqlite:///{db_path}",
                connect_args={"check_same_thread": False},
                echo=False  # Set to True for SQL debugging
            )
            
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Database engine created successfully: {db_path}")
            
            # Instrument the engine for OpenTelemetry tracing
            try:
                from backend.telemetry import instrument_database_engine
                instrument_database_engine(engine)
            except ImportError:
                logger.debug("Telemetry not available - skipping database instrumentation")
            
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            logger.error(f"Database path: {constants.DB_PATH}")
            logger.error(f"Database directory: {os.path.dirname(constants.DB_PATH)}")
            logger.error(f"Directory exists: {os.path.exists(os.path.dirname(constants.DB_PATH))}")
            if os.path.exists(os.path.dirname(constants.DB_PATH)):
                logger.error(f"Directory writable: {os.access(os.path.dirname(constants.DB_PATH), os.W_OK)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
    return engine