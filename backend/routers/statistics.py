"""Routes for statistics and analytics."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from datetime import datetime, timedelta
from backend.models.schemas import StatisticsResponse
from backend.models.database import PackageUpdate
from backend.db.session import get_session

# Import telemetry after standard imports  
try:
    from backend.telemetry import create_custom_span
    TELEMETRY_ENABLED = True
except ImportError:
    # Telemetry dependencies not available - create stub
    TELEMETRY_ENABLED = False
    def create_custom_span(name, attributes=None):
        class DummySpan:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def set_attribute(self, key, value): pass
        return DummySpan()

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/statistics", response_model=StatisticsResponse)
def get_statistics(session: Session = Depends(get_session)):
    """Get comprehensive statistics for the dashboard."""
    try:
        with create_custom_span("get_statistics") as span:
            # Total hosts
            total_hosts = session.exec(
                select(func.count(func.distinct(PackageUpdate.hostname)))
            ).one()
            
            # Total updates
            total_updates = session.exec(
                select(func.count(PackageUpdate.id))
            ).one()
            
            # Recent updates (last 30 days)
            thirty_days_ago = datetime.now().date() - timedelta(days=30)
            recent_updates = session.exec(
                select(func.count(PackageUpdate.id))
                .where(PackageUpdate.update_date >= thirty_days_ago)
            ).one()
            
            # Top packages by update frequency
            top_packages_query = session.exec(
                select(
                    PackageUpdate.name,
                    func.count(PackageUpdate.id).label("count")
                )
                .group_by(PackageUpdate.name)
                .order_by(func.count(PackageUpdate.id).desc())
                .limit(10)
            )
            top_packages = [
                {"name": row.name, "count": row.count} 
                for row in top_packages_query
            ]
            
            # Updates by OS
            updates_by_os_query = session.exec(
                select(
                    PackageUpdate.os,
                    func.count(PackageUpdate.id).label("count")
                )
                .group_by(PackageUpdate.os)
                .order_by(func.count(PackageUpdate.id).desc())
            )
            updates_by_os = [
                {"os": row.os, "count": row.count} 
                for row in updates_by_os_query
            ]
            
            # Updates timeline (last 30 days)
            timeline_query = session.exec(
                select(
                    PackageUpdate.update_date,
                    func.count(PackageUpdate.id).label("count")
                )
                .where(PackageUpdate.update_date >= thirty_days_ago)
                .group_by(PackageUpdate.update_date)
                .order_by(PackageUpdate.update_date.asc())
            )
            updates_timeline = [
                {"date": row.update_date.isoformat(), "count": row.count} 
                for row in timeline_query
            ]
            
            # Host activity (updates per host)
            host_activity_query = session.exec(
                select(
                    PackageUpdate.hostname,
                    func.count(PackageUpdate.id).label("count"),
                    func.max(PackageUpdate.update_date).label("last_update")
                )
                .group_by(PackageUpdate.hostname)
                .order_by(func.count(PackageUpdate.id).desc())
                .limit(10)
            )
            host_activity = [
                {
                    "hostname": row.hostname, 
                    "count": row.count,
                    "last_update": row.last_update.isoformat()
                } 
                for row in host_activity_query
            ]
            
            span.set_attribute("statistics.total_hosts", total_hosts)
            span.set_attribute("statistics.total_updates", total_updates)
            span.set_attribute("statistics.recent_updates", recent_updates)
            
            return StatisticsResponse(
                total_hosts=total_hosts,
                total_updates=total_updates,
                recent_updates=recent_updates,
                top_packages=top_packages,
                updates_by_os=updates_by_os,
                updates_timeline=updates_timeline,
                host_activity=host_activity
            )
            
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )