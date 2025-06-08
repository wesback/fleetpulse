from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel, Field, Session, create_engine, select
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import date, timedelta
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

class ChatQuery(SQLModel):
    """Model for natural language chat queries."""
    question: str = Field(max_length=500, description="Natural language question about package updates")

class ChatResponse(SQLModel):
    """Model for chat response."""
    answer: str = Field(description="Answer to the user's question")
    data: Optional[List[Dict[str, Any]]] = Field(default=None, description="Structured data supporting the answer")
    query_type: str = Field(description="Type of query that was processed")

def parse_natural_language_query(question: str, session: Session) -> ChatResponse:
    """Parse natural language questions and convert them to database queries."""
    question_lower = question.lower().strip()
    
    # Pattern: "which hosts had [package] updated [timeframe]?"
    if "which hosts" in question_lower and "updated" in question_lower:
        return handle_hosts_updated_query(question_lower, session)
    
    # Pattern: "what packages were updated on [hostname]?"
    elif "what packages" in question_lower and "updated" in question_lower:
        return handle_packages_on_host_query(question_lower, session)
    
    # Pattern: "show me [os] hosts" or "list [os] hosts"
    elif ("show me" in question_lower or "list" in question_lower) and "hosts" in question_lower:
        return handle_os_hosts_query(question_lower, session)
    
    # Pattern: "which hosts haven't been updated" or "hosts not updated"
    elif ("haven't been updated" in question_lower or "not updated" in question_lower) and "hosts" in question_lower:
        return handle_stale_hosts_query(question_lower, session)
    
    # Pattern: "how many hosts" or "count hosts"
    elif ("how many" in question_lower or "count" in question_lower) and "hosts" in question_lower:
        return handle_count_hosts_query(question_lower, session)
    
    else:
        return ChatResponse(
            answer="I can help you with questions about package updates. Try asking:\n"
                   "• 'Which hosts had Python packages updated last week?'\n"
                   "• 'What packages were updated on host-01?'\n"
                   "• 'Show me Ubuntu hosts'\n"
                   "• 'Which hosts haven't been updated in 30 days?'\n"
                   "• 'How many hosts do we have?'",
            query_type="help"
        )

def extract_timeframe(text: str) -> Optional[date]:
    """Extract timeframe from natural language text."""
    today = date.today()
    
    if "last week" in text or "past week" in text:
        return today - timedelta(days=7)
    elif "last month" in text or "past month" in text:
        return today - timedelta(days=30)
    elif "yesterday" in text:
        return today - timedelta(days=1)
    elif "last 3 days" in text or "past 3 days" in text:
        return today - timedelta(days=3)
    elif "last 7 days" in text or "past 7 days" in text:
        return today - timedelta(days=7)
    elif "last 30 days" in text or "past 30 days" in text:
        return today - timedelta(days=30)
    
    # Try to extract number of days
    import re
    day_match = re.search(r'(\d+)\s+days?', text)
    if day_match:
        days = int(day_match.group(1))
        return today - timedelta(days=days)
    
    return None

def extract_package_name(text: str) -> Optional[str]:
    """Extract package name from natural language text."""
    # Common package names to look for
    packages = ["python", "nginx", "apache", "mysql", "postgresql", "docker", "nodejs", "java", "php", "redis"]
    
    for package in packages:
        if package in text:
            return package
    
    # Try to extract words that might be package names (between common words)
    words = text.split()
    skip_words = {"which", "hosts", "had", "updated", "packages", "the", "a", "an", "in", "on", "at", "last", "past", "week", "month", "day", "days"}
    
    for word in words:
        clean_word = word.strip("?.,!").lower()
        if len(clean_word) > 2 and clean_word not in skip_words:
            return clean_word
    
    return None

def extract_hostname(text: str) -> Optional[str]:
    """Extract hostname from natural language text."""
    # Look for words that end with numbers (common hostname pattern)
    import re
    hostname_pattern = r'\b([a-zA-Z][-a-zA-Z0-9]*\d+|host[-\w]*\d*)\b'
    match = re.search(hostname_pattern, text)
    if match:
        return match.group(1)
    
    # Look for words after "on" 
    words = text.split()
    for i, word in enumerate(words):
        if word.lower() == "on" and i + 1 < len(words):
            hostname = words[i + 1].strip("?.,!")
            if len(hostname) > 0:
                return hostname
    
    return None

def extract_os_name(text: str) -> Optional[str]:
    """Extract OS name from natural language text."""
    os_names = ["ubuntu", "debian", "centos", "rhel", "fedora", "arch", "archlinux", "alpine", "opensuse", "windows", "macos"]
    
    for os_name in os_names:
        if os_name in text.lower():
            return os_name
    
    return None

def handle_hosts_updated_query(question: str, session: Session) -> ChatResponse:
    """Handle queries about which hosts had packages updated."""
    package_name = extract_package_name(question)
    timeframe = extract_timeframe(question)
    
    query = select(PackageUpdate.hostname).distinct()
    
    if package_name:
        query = query.where(PackageUpdate.name.ilike(f"%{package_name}%"))
    
    if timeframe:
        query = query.where(PackageUpdate.update_date >= timeframe)
    
    try:
        result = session.exec(query).all()
        
        if not result:
            answer = f"No hosts found"
            if package_name:
                answer += f" with {package_name} packages"
            if timeframe:
                answer += f" updated since {timeframe}"
            answer += "."
        else:
            answer = f"Found {len(result)} host(s)"
            if package_name:
                answer += f" with {package_name} packages"
            if timeframe:
                answer += f" updated since {timeframe}"
            answer += f": {', '.join(result)}"
        
        return ChatResponse(
            answer=answer,
            data=[{"hostname": host} for host in result],
            query_type="hosts_updated"
        )
    except Exception as e:
        logger.error(f"Error in hosts updated query: {e}")
        return ChatResponse(
            answer="Sorry, I encountered an error while searching for hosts.",
            query_type="error"
        )

def handle_packages_on_host_query(question: str, session: Session) -> ChatResponse:
    """Handle queries about packages updated on a specific host."""
    hostname = extract_hostname(question)
    timeframe = extract_timeframe(question)
    
    if not hostname:
        return ChatResponse(
            answer="Please specify which host you'd like to know about. For example: 'What packages were updated on host-01?'",
            query_type="clarification"
        )
    
    query = select(PackageUpdate).where(PackageUpdate.hostname == hostname)
    
    if timeframe:
        query = query.where(PackageUpdate.update_date >= timeframe)
    
    query = query.order_by(PackageUpdate.update_date.desc())
    
    try:
        result = session.exec(query).all()
        
        if not result:
            answer = f"No package updates found for host '{hostname}'"
            if timeframe:
                answer += f" since {timeframe}"
            answer += "."
        else:
            packages = [f"{r.name} ({r.old_version} → {r.new_version})" for r in result[:10]]
            answer = f"Found {len(result)} package update(s) for host '{hostname}'"
            if timeframe:
                answer += f" since {timeframe}"
            if len(result) > 10:
                answer += f". Here are the most recent 10: {', '.join(packages)}"
            else:
                answer += f": {', '.join(packages)}"
        
        return ChatResponse(
            answer=answer,
            data=[{
                "package": r.name,
                "old_version": r.old_version,
                "new_version": r.new_version,
                "update_date": str(r.update_date),
                "os": r.os
            } for r in result],
            query_type="packages_on_host"
        )
    except Exception as e:
        logger.error(f"Error in packages on host query: {e}")
        return ChatResponse(
            answer="Sorry, I encountered an error while searching for package updates.",
            query_type="error"
        )

def handle_os_hosts_query(question: str, session: Session) -> ChatResponse:
    """Handle queries about hosts with specific OS."""
    os_name = extract_os_name(question)
    
    query = select(PackageUpdate.hostname, PackageUpdate.os).distinct()
    
    if os_name:
        query = query.where(PackageUpdate.os.ilike(f"%{os_name}%"))
    
    try:
        result = session.exec(query).all()
        
        if not result:
            answer = f"No hosts found"
            if os_name:
                answer += f" running {os_name}"
            answer += "."
        else:
            if os_name:
                answer = f"Found {len(result)} host(s) running {os_name}: "
            else:
                answer = f"Found {len(result)} host(s) with these operating systems: "
            
            host_list = [f"{r[0]} ({r[1]})" for r in result]
            answer += ", ".join(host_list)
        
        return ChatResponse(
            answer=answer,
            data=[{"hostname": r[0], "os": r[1]} for r in result],
            query_type="os_hosts"
        )
    except Exception as e:
        logger.error(f"Error in OS hosts query: {e}")
        return ChatResponse(
            answer="Sorry, I encountered an error while searching for hosts.",
            query_type="error"
        )

def handle_stale_hosts_query(question: str, session: Session) -> ChatResponse:
    """Handle queries about hosts that haven't been updated recently."""
    timeframe = extract_timeframe(question)
    
    if not timeframe:
        timeframe = date.today() - timedelta(days=30)  # Default to 30 days
    
    try:
        # Get all hosts and their last update dates
        recent_hosts = session.exec(
            select(PackageUpdate.hostname).distinct()
            .where(PackageUpdate.update_date >= timeframe)
        ).all()
        
        all_hosts = session.exec(select(PackageUpdate.hostname).distinct()).all()
        
        stale_hosts = [host for host in all_hosts if host not in recent_hosts]
        
        if not stale_hosts:
            answer = f"All hosts have been updated since {timeframe}."
        else:
            answer = f"Found {len(stale_hosts)} host(s) that haven't been updated since {timeframe}: {', '.join(stale_hosts)}"
        
        return ChatResponse(
            answer=answer,
            data=[{"hostname": host, "status": "stale"} for host in stale_hosts],
            query_type="stale_hosts"
        )
    except Exception as e:
        logger.error(f"Error in stale hosts query: {e}")
        return ChatResponse(
            answer="Sorry, I encountered an error while searching for stale hosts.",
            query_type="error"
        )

def handle_count_hosts_query(question: str, session: Session) -> ChatResponse:
    """Handle queries about counting hosts."""
    os_name = extract_os_name(question)
    
    try:
        if os_name:
            count = session.exec(
                select(PackageUpdate.hostname).distinct()
                .where(PackageUpdate.os.ilike(f"%{os_name}%"))
            ).all()
            answer = f"We have {len(count)} host(s) running {os_name}."
        else:
            count = session.exec(select(PackageUpdate.hostname).distinct()).all()
            answer = f"We have {len(count)} host(s) total in the fleet."
        
        return ChatResponse(
            answer=answer,
            data={"count": len(count)},
            query_type="count_hosts"
        )
    except Exception as e:
        logger.error(f"Error in count hosts query: {e}")
        return ChatResponse(
            answer="Sorry, I encountered an error while counting hosts.",
            query_type="error"
        )
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
def host_history(
    hostname: str, 
    session: Session = Depends(get_session),
    date_from: Optional[date] = Query(None, description="Filter updates from this date (inclusive)"),
    date_to: Optional[date] = Query(None, description="Filter updates to this date (inclusive)"),
    os: Optional[str] = Query(None, description="Filter by operating system"),
    package: Optional[str] = Query(None, description="Filter by package name (partial match)")
):
    """Get update history for a specific host with optional filters."""
    try:
        if not validate_hostname(hostname):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid hostname format"
            )
        
        # Validate filter parameters
        if os and not validate_os(os):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OS format"
            )
        
        if package and not validate_package_name(package):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid package name format"
            )
        
        if date_from and date_to and date_from > date_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="date_from cannot be after date_to"
            )
        
        # Build query with filters
        query = select(PackageUpdate).where(PackageUpdate.hostname == hostname)
        
        if date_from:
            query = query.where(PackageUpdate.update_date >= date_from)
        
        if date_to:
            query = query.where(PackageUpdate.update_date <= date_to)
        
        if os:
            query = query.where(PackageUpdate.os == os)
        
        if package:
            # Use SQL LIKE for partial matching (case-insensitive)
            query = query.where(PackageUpdate.name.ilike(f"%{package}%"))
        
        query = query.order_by(PackageUpdate.update_date.desc(), PackageUpdate.id.desc())
        
        result = session.exec(query).all()
        
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

@app.post("/chat", response_model=ChatResponse)
def chat_query(chat: ChatQuery, session: Session = Depends(get_session)):
    """Process natural language queries about package updates."""
    try:
        if not chat.question or len(chat.question.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
        
        # Basic sanitization
        if len(chat.question) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question too long (max 500 characters)"
            )
        
        response = parse_natural_language_query(chat.question, session)
        logger.info(f"Processed chat query: '{chat.question}' -> {response.query_type}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)