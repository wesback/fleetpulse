"""Routes for health checking and monitoring."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from backend.db.session import get_session
from backend.utils.telemetry import create_business_span, is_telemetry_enabled

# Try to import telemetry configuration function directly for health check
try:
    from backend.telemetry import get_telemetry_config
    TELEMETRY_CONFIG_AVAILABLE = True
except ImportError:
    TELEMETRY_CONFIG_AVAILABLE = False
    def get_telemetry_config(): 
        return {}

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health_check(session: Session = Depends(get_session)):
    """Health check endpoint with telemetry information."""
    with create_business_span("health_check") as span:
        try:
            # Test database connection
            session.exec(select(1)).first()
            
            # Get telemetry configuration
            telemetry_enabled = is_telemetry_enabled()
            if telemetry_enabled and TELEMETRY_CONFIG_AVAILABLE:
                telemetry_config = get_telemetry_config()
                health_data = {
                    "status": "healthy", 
                    "database": "connected",
                    "telemetry": {
                        "enabled": telemetry_config.get("enable_telemetry", False),
                        "service_name": telemetry_config.get("service_name", "unknown"),
                        "service_version": telemetry_config.get("service_version", "unknown"),
                        "environment": telemetry_config.get("environment", "unknown"),
                        "exporter_type": telemetry_config.get("exporter_type", "unknown"),
                    }
                }
                span.set_attribute("telemetry.enabled", telemetry_config.get("enable_telemetry", False))
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
            span.set_attribute("operation.success", True)
            
            return health_data
            
        except Exception as e:
            span.set_attribute("health.status", "unhealthy")
            span.set_attribute("operation.success", False)
            span.set_attribute("error.message", str(e))
            logger.error(f"Health check failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unhealthy"
            )