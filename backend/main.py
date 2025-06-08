from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel, Field, Session, create_engine, select
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import date
import os
import logging
from contextlib import asynccontextmanager
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_HOSTNAME_LENGTH = 255
MAX_PACKAGE_NAME_LENGTH = 255
MAX_VERSION_LENGTH = 100
MAX_OS_LENGTH = 50

# Determine data directory based on environment variable
DATA_DIR = os.environ.get("FLEETPULSE_DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "updates.db")

# Global engine variable
engine = None

def validate_hostname(hostname: str) -> bool:
    """Validate hostname format and length."""
    if not hostname or len(hostname) > MAX_HOSTNAME_LENGTH:
        return False
    # Basic hostname validation (alphanumeric, dots, hyphens)
    pattern = r'^[a-zA-Z0-9.-]+$'
    return bool(re.match(pattern, hostname))

def validate_package_name(name: str) -> bool:
    """Validate package name format and length."""
    if not name or len(name) > MAX_PACKAGE_NAME_LENGTH:
        return False
    # Allow alphanumeric, dots, hyphens, underscores, plus signs
    pattern = r'^[a-zA-Z0-9._+-]+$'
    return bool(re.match(pattern, name))

def validate_version(version: str) -> bool:
    """Validate version string format and length."""
    if not version or len(version) > MAX_VERSION_LENGTH:
        return False
    # Allow common version patterns
    pattern = r'^[a-zA-Z0-9._+-:~]+$'
    return bool(re.match(pattern, version))

def validate_os(os_name: str) -> bool:
    """Validate OS name format and length."""
    if not os_name or len(os_name) > MAX_OS_LENGTH:
        return False
    # Allow alphanumeric, spaces, dots, hyphens
    pattern = r'^[a-zA-Z0-9. -]+$'
    return bool(re.match(pattern, os_name))

def get_engine():
    """Get database engine with proper error handling."""
    global engine
    if engine is None:
        try:
            logger.info(f"Creating database engine for: {DB_PATH}")
            
            # Ensure the directory exists
            db_dir = os.path.dirname(DB_PATH)
            if not os.path.exists(db_dir):
                logger.info(f"Creating database directory: {db_dir}")
                os.makedirs(db_dir, exist_ok=True)
            
            # Check if we can write to the database directory
            if not os.access(db_dir, os.W_OK):
                raise PermissionError(f"Cannot write to database directory: {db_dir}")
            
            engine = create_engine(
                f"sqlite:///{DB_PATH}",
                connect_args={"check_same_thread": False},
                echo=False  # Set to True for SQL debugging
            )
            
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Database engine created successfully: {DB_PATH}")
            
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            logger.error(f"Database path: {DB_PATH}")
            logger.error(f"Database directory: {os.path.dirname(DB_PATH)}")
            logger.error(f"Directory exists: {os.path.exists(os.path.dirname(DB_PATH))}")
            if os.path.exists(os.path.dirname(DB_PATH)):
                logger.error(f"Directory writable: {os.access(os.path.dirname(DB_PATH), os.W_OK)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
    return engine

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    try:
        logger.info(f"Starting FleetPulse application")
        logger.info(f"Data directory: {DATA_DIR}")
        logger.info(f"Database path: {DB_PATH}")
        
        # Check if data directory exists and permissions
        if os.path.exists(DATA_DIR):
            logger.info(f"Data directory exists: {DATA_DIR}")
            # Check if we can write to it
            test_file = os.path.join(DATA_DIR, "test_write.tmp")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                logger.info("Data directory is writable")
            except Exception as e:
                logger.error(f"Cannot write to data directory: {e}")
                raise
        else:
            logger.info(f"Creating data directory: {DATA_DIR}")
        
        os.makedirs(DATA_DIR, exist_ok=True)
        logger.info(f"Data directory ensured: {DATA_DIR}")
        
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
            db_exists = os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0
            
            if db_exists:
                # Check if our main table exists
                from sqlalchemy import inspect
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

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="FleetPulse API",
    description="API for tracking package updates across fleet hosts",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware with more restrictive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only allow necessary methods
    allow_headers=["*"],
)

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

@app.post("/report", status_code=status.HTTP_201_CREATED)
def report_update(update: UpdateIn, session: Session = Depends(get_session)):
    """Report package updates for a host."""
    try:
        # Validate input data
        if not validate_hostname(update.hostname):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid hostname format"
            )
        
        if not validate_os(update.os):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OS format"
            )
        
        if not update.updated_packages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No packages provided"
            )
        
        if len(update.updated_packages) > 1000:  # Reasonable limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many packages in single request"
            )
        
        # Validate each package
        for pkg in update.updated_packages:
            if not validate_package_name(pkg.name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid package name: {pkg.name}"
                )
            
            if not validate_version(pkg.old_version):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid old version: {pkg.old_version}"
                )
            
            if not validate_version(pkg.new_version):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid new version: {pkg.new_version}"
                )
        
        # Insert package updates using SQLModel (prevents SQL injection)
        updates_added = 0
        for pkg in update.updated_packages:
            package_update = PackageUpdate(
                hostname=update.hostname,
                os=update.os,
                update_date=update.update_date,
                name=pkg.name,
                old_version=pkg.old_version,
                new_version=pkg.new_version
            )
            session.add(package_update)
            updates_added += 1
        
        session.commit()
        logger.info(f"Added {updates_added} package updates for host {update.hostname}")
        
        return {
            "status": "success",
            "message": f"Recorded {updates_added} package updates",
            "hostname": update.hostname
        }
        
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error reporting update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record package updates"
        )

@app.get("/hosts", response_model=Dict[str, List[str]])
def list_hosts(session: Session = Depends(get_session)):
    """Get list of all hosts that have reported updates."""
    try:
        result = session.exec(select(PackageUpdate.hostname).distinct()).all()
        return {"hosts": result}
    except Exception as e:
        logger.error(f"Error listing hosts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve hosts"
        )

@app.get("/history/{hostname}", response_model=List[PackageUpdate])
def host_history(hostname: str, session: Session = Depends(get_session)):
    """Get update history for a specific host."""
    try:
        if not validate_hostname(hostname):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid hostname format"
            )
        
        result = session.exec(
            select(PackageUpdate)
            .where(PackageUpdate.hostname == hostname)
            .order_by(PackageUpdate.update_date.desc(), PackageUpdate.id.desc())
        ).all()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No update history found for host: {hostname}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting host history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve host history"
        )

@app.get("/last-updates", response_model=List[HostInfo])
def last_updates(session: Session = Depends(get_session)):
    """Get the last update date for each host."""
    try:
        hosts = session.exec(select(PackageUpdate.hostname).distinct()).all()
        data = []
        
        for host in hosts:
            update = session.exec(
                select(PackageUpdate)
                .where(PackageUpdate.hostname == host)
                .order_by(PackageUpdate.update_date.desc(), PackageUpdate.id.desc())
            ).first()
            
            if update:
                data.append(HostInfo(
                    hostname=host,
                    os=update.os,
                    last_update=update.update_date
                ))
        
        return data
        
    except Exception as e:
        logger.error(f"Error getting last updates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve last updates"
        )

@app.get("/health")
def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        with Session(get_engine()) as session:
            session.exec(select(1)).first()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)