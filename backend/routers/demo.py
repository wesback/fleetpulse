"""Demo routes for generating sample data."""
import logging
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from backend.models.schemas import UpdateIn, PackageInfo
from backend.db.session import get_session
from backend.routers.reports import report_update

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/demo/sample-data")
def generate_sample_data(session: Session = Depends(get_session)):
    """Generate sample package update data for demonstration purposes."""
    try:
        # Sample data for different dates
        today = date.today()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        sample_reports = [
            UpdateIn(
                hostname="web-server-01",
                os="ubuntu",
                update_date=today,
                updated_packages=[
                    PackageInfo(name="nginx", old_version="1.18.0", new_version="1.20.2"),
                    PackageInfo(name="curl", old_version="7.68.0", new_version="7.81.0"),
                ]
            ),
            UpdateIn(
                hostname="web-server-02", 
                os="ubuntu",
                update_date=today,
                updated_packages=[
                    PackageInfo(name="apache2", old_version="2.4.41", new_version="2.4.52"),
                    PackageInfo(name="openssl", old_version="1.1.1f", new_version="1.1.1k"),
                ]
            ),
            UpdateIn(
                hostname="db-server-01",
                os="centos",
                update_date=yesterday,
                updated_packages=[
                    PackageInfo(name="postgresql", old_version="13.4", new_version="13.8"),
                    PackageInfo(name="systemd", old_version="245", new_version="246"),
                ]
            ),
            UpdateIn(
                hostname="api-server-01",
                os="debian",
                update_date=week_ago,
                updated_packages=[
                    PackageInfo(name="python3", old_version="3.9.2", new_version="3.9.7"),
                    PackageInfo(name="git", old_version="2.30.2", new_version="2.32.0"),
                    PackageInfo(name="nginx", old_version="1.18.0", new_version="1.20.2"),
                ]
            ),
            UpdateIn(
                hostname="monitoring-server",
                os="ubuntu",
                update_date=week_ago,
                updated_packages=[
                    PackageInfo(name="prometheus", old_version="2.28.1", new_version="2.30.3"),
                    PackageInfo(name="grafana", old_version="8.0.6", new_version="8.2.0"),
                ]
            ),
        ]
        
        total_packages = 0
        for report in sample_reports:
            # Use the existing report_update function to maintain consistency
            response = report_update(report, session)
            total_packages += len(report.updated_packages)
            
        logger.info(f"Generated sample data: {len(sample_reports)} reports, {total_packages} package updates")
        
        return {
            "status": "success",
            "message": f"Generated sample data with {len(sample_reports)} hosts and {total_packages} package updates",
            "hosts_created": len(sample_reports),
            "total_packages": total_packages
        }
        
    except Exception as e:
        logger.error(f"Error generating sample data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate sample data"
        )