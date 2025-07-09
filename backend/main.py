"""FastAPI backend application with modular structure."""
import os
import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import HTTPException, status
from sqlmodel import SQLModel
from sqlalchemy import inspect

# Import telemetry functions with graceful fallback
try:
    from telemetry import (
        initialize_telemetry, 
        shutdown_telemetry,
        instrument_fastapi_app,
        create_custom_span,
        record_request_metrics,
        record_package_update_metrics,
        record_host_metrics,
        add_baggage,
        get_tracer,
    )
    TELEMETRY_ENABLED = True
except ImportError:
    # Telemetry dependencies not available - create stubs
    TELEMETRY_ENABLED = False
    def initialize_telemetry(): pass
    def shutdown_telemetry(): pass
    def instrument_fastapi_app(app): pass
    def create_custom_span(name, attributes=None):
        class DummySpan:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def set_attribute(self, key, value): pass
        return DummySpan()
    def record_request_metrics(*args, **kwargs): pass
    def record_package_update_metrics(*args, **kwargs): pass
    def record_host_metrics(*args, **kwargs): pass
    def add_baggage(*args, **kwargs): pass
    def get_tracer(*args, **kwargs): return None

# Import our modular components
from db.engine import get_engine
from utils import constants
from routers import reports, hosts, statistics, health
# Import models to ensure they're registered with SQLModel metadata
from models import database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    try:
        logger.info(f"Starting FleetPulse application")
        
        # Initialize OpenTelemetry first
        initialize_telemetry()
        
        # Use current values from constants module to allow test patching
        data_dir = constants.DATA_DIR
        db_path = constants.DB_PATH
        
        logger.info(f"Data directory: {data_dir}")
        logger.info(f"Database path: {db_path}")
        
        # Check if data directory exists and permissions
        if os.path.exists(data_dir):
            logger.info(f"Data directory exists: {data_dir}")
            # Check if we can write to it
            test_file = os.path.join(data_dir, "test_write.tmp")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                logger.info("Data directory is writable")
            except Exception as e:
                logger.error(f"Cannot write to data directory: {e}")
                raise
        else:
            logger.info(f"Creating data directory: {data_dir}")
        
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"Data directory ensured: {data_dir}")
        
        # Initialize database tables
        force_recreate = os.environ.get("FORCE_DB_RECREATE", "false").lower() == "true"
        engine = get_engine()
        
        if force_recreate:
            logger.info("Force recreation enabled - dropping and recreating all tables...")
            SQLModel.metadata.drop_all(engine)
            SQLModel.metadata.create_all(engine)
            logger.info("Database tables recreated successfully")
        else:
            # Check if database exists and has tables
            db_exists = os.path.exists(db_path) and os.path.getsize(db_path) > 0
            
            if db_exists:
                # Check if our main table exists
                inspector = inspect(engine)
                existing_tables = inspector.get_table_names()
                
                if "package_updates" in existing_tables:
                    logger.info("Database tables already exist - skipping creation")
                else:
                    logger.info("Database exists but tables missing - creating tables...")
                    SQLModel.metadata.create_all(engine)
                    logger.info("Database tables created successfully")
            else:
                logger.info("New database - creating tables...")
                SQLModel.metadata.create_all(engine)
                logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")
    shutdown_telemetry()


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="FleetPulse API",
    description="API for tracking package updates across fleet hosts",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument FastAPI app for OpenTelemetry tracing
instrument_fastapi_app(app)

# CORS middleware with more restrictive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only allow necessary methods
    allow_headers=["*"],
)

# Telemetry middleware to capture request metrics
@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    """Middleware to capture request telemetry."""
    start_time = time.time()
    
    # Add baggage for request tracking
    add_baggage("request.method", request.method)
    add_baggage("request.url", str(request.url))
    
    response = await call_next(request)
    
    # Calculate duration and record metrics
    duration_ms = (time.time() - start_time) * 1000
    
    # Extract endpoint path template
    endpoint = request.url.path
    if hasattr(request, "path_info"):
        endpoint = request.path_info
    
    record_request_metrics(
        method=request.method,
        endpoint=endpoint,
        status_code=response.status_code,
        duration_ms=duration_ms
    )
    
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"}
    )


# Include routers
app.include_router(reports.router, tags=["reports"])
app.include_router(hosts.router, tags=["hosts"])
app.include_router(statistics.router, tags=["statistics"])
app.include_router(health.router, tags=["health"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)