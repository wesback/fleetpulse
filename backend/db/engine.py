"""Database engine management for FleetPulse."""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool, QueuePool
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
            db_type = constants.DATABASE_TYPE
            db_url = constants.DATABASE_URL
            
            logger.info(f"Creating database engine for type: {db_type}")
            logger.info(f"Database URL: {db_url.split('@')[-1] if '@' in db_url else db_url}")
            
            # Database-specific configuration
            engine_kwargs = {"echo": False}  # Set to True for SQL debugging
            
            if db_type == "sqlite":
                # SQLite-specific configuration
                db_path = constants.DB_PATH
                
                # Ensure the directory exists for SQLite
                db_dir = os.path.dirname(db_path)
                if not os.path.exists(db_dir):
                    logger.info(f"Creating database directory: {db_dir}")
                    os.makedirs(db_dir, exist_ok=True)
                
                # Check if we can write to the database directory
                if not os.access(db_dir, os.W_OK):
                    raise PermissionError(f"Cannot write to database directory: {db_dir}")
                
                engine_kwargs["connect_args"] = {"check_same_thread": False}
                engine_kwargs["poolclass"] = NullPool  # SQLite doesn't need connection pooling
                
            elif db_type == "postgresql":
                # PostgreSQL-specific configuration with connection pooling
                engine_kwargs["pool_size"] = int(os.environ.get("DB_POOL_SIZE", "5"))
                engine_kwargs["max_overflow"] = int(os.environ.get("DB_MAX_OVERFLOW", "10"))
                engine_kwargs["pool_pre_ping"] = True  # Verify connections before using
                engine_kwargs["pool_recycle"] = 3600  # Recycle connections after 1 hour
                engine_kwargs["poolclass"] = QueuePool
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            # Create the engine
            engine = create_engine(db_url, **engine_kwargs)
            
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Database engine created successfully for {db_type}")
            
            # Instrument the engine for OpenTelemetry tracing
            try:
                from backend.telemetry import instrument_database_engine
                instrument_database_engine(engine)
            except ImportError:
                logger.debug("Telemetry not available - skipping database instrumentation")
            
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            logger.error(f"Database type: {constants.DATABASE_TYPE}")
            logger.error(f"Database URL pattern: {constants.DATABASE_URL.split('@')[-1] if '@' in constants.DATABASE_URL else constants.DATABASE_URL}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database connection failed: {str(e)}"
            )
    return engine