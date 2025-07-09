"""Routes for package update reports."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from backend.models.schemas import UpdateIn
from backend.models.database import PackageUpdate
from backend.db.session import get_session
from backend.utils.validation import (
    validate_hostname,
    validate_os,
    validate_package_name,
    validate_version
)
from backend.utils.telemetry import (
    create_business_span,
    record_package_update_metrics,
    record_host_metrics,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/report", status_code=status.HTTP_201_CREATED)
def report_update(update: UpdateIn, session: Session = Depends(get_session)):
    """Report package updates for a host."""
    
    # Create custom span for business logic
    with create_business_span("report_package_updates", 
                             hostname=update.hostname,
                             os=update.os,
                             package_count=len(update.updated_packages),
                             update_date=str(update.update_date)) as span:
        try:
            # Validate input data
            if not validate_hostname(update.hostname):
                span.set_attribute("validation.error", "invalid_hostname")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid hostname format"
                )
            
            if not validate_os(update.os):
                span.set_attribute("validation.error", "invalid_os")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid OS format"
                )
            
            if not update.updated_packages:
                span.set_attribute("validation.error", "no_packages")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No packages provided"
                )
            
            if len(update.updated_packages) > 1000:  # Reasonable limit
                span.set_attribute("validation.error", "too_many_packages")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Too many packages in single request"
                )
            
            # Validate each package
            for pkg in update.updated_packages:
                if not validate_package_name(pkg.name):
                    span.set_attribute("validation.error", f"invalid_package_name_{pkg.name}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid package name: {pkg.name}"
                    )
                
                if not validate_version(pkg.old_version):
                    span.set_attribute("validation.error", f"invalid_old_version_{pkg.old_version}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid old version: {pkg.old_version}"
                    )
            
                if not validate_version(pkg.new_version):
                    span.set_attribute("validation.error", f"invalid_new_version_{pkg.new_version}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid new version: {pkg.new_version}"
                    )
            
            span.set_attribute("validation.passed", True)
            
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
            
            # Record business metrics
            record_package_update_metrics(update.hostname, updates_added)
            record_host_metrics(update.hostname, "add")
            
            span.set_attribute("updates.added", updates_added)
            span.set_attribute("operation.success", True)
            
            logger.info(f"Added {updates_added} package updates for host {update.hostname}")
            
            return {
                "status": "success",
                "message": f"Recorded {updates_added} package updates",
                "hostname": update.hostname
            }
            
        except HTTPException:
            session.rollback()
            span.set_attribute("operation.success", False)
            raise
        except Exception as e:
            session.rollback()
            span.set_attribute("operation.success", False)
            span.set_attribute("error.message", str(e))
            logger.error(f"Error reporting update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record package updates"
            )