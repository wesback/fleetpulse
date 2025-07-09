"""Routes for health checking and monitoring."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from backend.db.session import get_session

# Import telemetry after standard imports  
try:
    from backend.telemetry import create_custom_span, get_telemetry_config
    TELEMETRY_ENABLED = True
except ImportError:
    # Telemetry dependencies not available - create stubs
    TELEMETRY_ENABLED = False
    def create_custom_span(name, attributes=None):
        class DummySpan:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def set_attribute(self, key, value): pass
        return DummySpan()
    def get_telemetry_config(): return {}

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health_check(session: Session = Depends(get_session)):
    """Health check endpoint with telemetry information."""
    with create_custom_span("health_check") as span:
        try:
            # Test database connection
            session.exec(select(1)).first()
            
            # Get telemetry configuration
            if TELEMETRY_ENABLED:
                telemetry_config = get_telemetry_config()
                health_data = {
                    "status": "healthy", 
                    "database": "connected",
                    "telemetry": {
                        "enabled": telemetry_config["enable_telemetry"],
                        "service_name": telemetry_config["service_name"],
                        "service_version": telemetry_config["service_version"],
                        "environment": telemetry_config["environment"],
                        "exporter_type": telemetry_config["exporter_type"],
                    }
                }
                span.set_attribute("telemetry.enabled", telemetry_config["enable_telemetry"])
            else:
                health_data = {
                    "status": "healthy", 
                    "database": "connected",
                    "telemetry": {
                        "enabled": False,
                        "note": "OpenTelemetry dependencies not installed"
                    }
                }
                span.set_attribute("telemetry.enabled", False)
            
            span.set_attribute("health.status", "healthy")
            span.set_attribute("database.status", "connected")
            
            return health_data
            
        except Exception as e:
            span.set_attribute("health.status", "unhealthy")
            span.set_attribute("error.message", str(e))
            logger.error(f"Health check failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unhealthy"
            )