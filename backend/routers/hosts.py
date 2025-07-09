"""Routes for host-related operations."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from typing import List, Dict, Optional
from datetime import date
from backend.models.schemas import HostInfo, PaginatedResponse
from backend.models.database import PackageUpdate
from backend.db.session import get_session
from backend.utils.validation import validate_hostname, validate_os, validate_package_name
from backend.utils.telemetry import create_business_span, record_host_query_metrics

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/hosts", response_model=Dict[str, List[str]])
def list_hosts(session: Session = Depends(get_session)):
    """Get list of all hosts that have reported updates."""
    with create_business_span("list_hosts") as span:
        try:
            result = session.exec(select(PackageUpdate.hostname).distinct()).all()
            
            # Record telemetry
            record_host_query_metrics("list_hosts", result_count=len(result))
            span.set_attribute("hosts.count", len(result))
            span.set_attribute("operation.success", True)
            
            logger.info(f"Listed {len(result)} hosts")
            return {"hosts": result}
            
        except Exception as e:
            span.set_attribute("operation.success", False)
            span.set_attribute("error.message", str(e))
            logger.error(f"Error listing hosts: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve hosts"
            )


@router.get("/history/{hostname}", response_model=PaginatedResponse)
def host_history(
    hostname: str, 
    session: Session = Depends(get_session),
    date_from: Optional[date] = Query(None, description="Filter updates from this date (inclusive)"),
    date_to: Optional[date] = Query(None, description="Filter updates to this date (inclusive)"),
    os: Optional[str] = Query(None, description="Filter by operating system"),
    package: Optional[str] = Query(None, description="Filter by package name (partial match)"),
    limit: int = Query(50, ge=1, le=1000, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
):
    """Get update history for a specific host with optional filters."""
    with create_business_span("host_history", 
                             hostname=hostname, 
                             os=os or "any",
                             package_filter=package or "none",
                             limit=limit,
                             offset=offset) as span:
        try:
            if not validate_hostname(hostname):
                span.set_attribute("validation.error", "invalid_hostname")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid hostname format"
                )
            
            # Validate filter parameters
            if os and not validate_os(os):
                span.set_attribute("validation.error", "invalid_os")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid OS format"
                )
            
            if package and not validate_package_name(package):
                span.set_attribute("validation.error", "invalid_package_name")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid package name format"
                )
            
            if date_from and date_to and date_from > date_to:
                span.set_attribute("validation.error", "invalid_date_range")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="date_from cannot be after date_to"
                )
            
            span.set_attribute("validation.passed", True)
            
            # Build base query with filters
            base_query = select(PackageUpdate).where(PackageUpdate.hostname == hostname)
            
            if date_from:
                base_query = base_query.where(PackageUpdate.update_date >= date_from)
                span.set_attribute("filter.date_from", str(date_from))
            
            if date_to:
                base_query = base_query.where(PackageUpdate.update_date <= date_to)
                span.set_attribute("filter.date_to", str(date_to))
            
            if os:
                base_query = base_query.where(PackageUpdate.os == os)
                span.set_attribute("filter.os", os)
            
            if package:
                # Use SQL LIKE for partial matching (case-insensitive)
                base_query = base_query.where(PackageUpdate.name.ilike(f"%{package}%"))
                span.set_attribute("filter.package", package)
            
            # Get total count of items matching filters
            count_query = select(func.count()).select_from(
                base_query.subquery()
            )
            total = session.exec(count_query).one()
            
            # Apply ordering and pagination to the main query
            paginated_query = (
                base_query
                .order_by(PackageUpdate.update_date.desc(), PackageUpdate.id.desc())
                .offset(offset)
                .limit(limit)
            )
            
            result = session.exec(paginated_query).all()
            
            if total == 0:
                span.set_attribute("result.not_found", True)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No update history found for host: {hostname}"
                )
            
            # Record telemetry
            record_host_query_metrics("host_history", hostname=hostname, result_count=len(result))
            span.set_attribute("result.total", total)
            span.set_attribute("result.returned", len(result))
            span.set_attribute("operation.success", True)
            
            logger.info(f"Retrieved {len(result)}/{total} history entries for host {hostname}")
            
            return PaginatedResponse(
                items=result,
                total=total,
                limit=limit,
                offset=offset
            )
            
        except HTTPException:
            span.set_attribute("operation.success", False)
            raise
        except Exception as e:
            span.set_attribute("operation.success", False)
            span.set_attribute("error.message", str(e))
            logger.error(f"Error getting host history: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve host history"
            )


@router.get("/last-updates", response_model=List[HostInfo])
def last_updates(session: Session = Depends(get_session)):
    """Get the last update date for each host."""
    with create_business_span("last_updates") as span:
        try:
            hosts = session.exec(select(PackageUpdate.hostname).distinct()).all()
            data = []
            
            span.set_attribute("hosts.count", len(hosts))
            
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
            
            # Record telemetry
            record_host_query_metrics("last_updates", result_count=len(data))
            span.set_attribute("result.count", len(data))
            span.set_attribute("operation.success", True)
            
            logger.info(f"Retrieved last updates for {len(data)} hosts")
            return data
            
        except Exception as e:
            span.set_attribute("operation.success", False)
            span.set_attribute("error.message", str(e))
            logger.error(f"Error getting last updates: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve last updates"
            )