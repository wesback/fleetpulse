"""
MCP tools implementation for FleetPulse operations.

Each tool provides read-only access to FleetPulse backend functionality.
"""

import asyncio
import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict

from .client import get_backend_client, BackendHTTPError, BackendConnectionError
from .models import (
    Host, UpdateReport, PackageInfo, HealthStatus, 
    FleetStatistics, SearchResult, SearchResponse,
    PackageUpdate, MCPErrorResponse
)
from .telemetry import create_custom_span, add_baggage


logger = logging.getLogger(__name__)


class MCPToolError(Exception):
    """Base exception for MCP tool errors."""
    pass


class MCPTools:
    """Collection of MCP tools for FleetPulse operations."""
    
    def __init__(self):
        self.client = get_backend_client()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Health Check Tool
        
        Query backend health status and return structured health information 
        including database connectivity and telemetry status.
        """
        with create_custom_span("mcp_tool_health_check") as span:
            try:
                add_baggage("mcp.tool", "health_check")
                
                health = await self.client.health_check()
                
                # Add timestamp and additional MCP server info
                result = health.dict()
                result["mcp_server"] = {
                    "status": "healthy",
                    "backend_connected": True
                }
                
                span.set_attribute("health.status", health.status)
                span.set_attribute("database.status", health.database)
                span.set_attribute("mcp.tool.success", True)
                
                return result
                
            except BackendConnectionError as e:
                span.set_attribute("mcp.tool.success", False)
                span.set_attribute("error.type", "backend_connection")
                return {
                    "status": "unhealthy",
                    "mcp_server": {
                        "status": "degraded",
                        "backend_connected": False,
                        "error": str(e)
                    },
                    "database": "unknown",
                    "telemetry": {"enabled": False}
                }
            
            except Exception as e:
                span.set_attribute("mcp.tool.success", False)
                span.set_attribute("error.message", str(e))
                logger.error(f"Health check tool failed: {e}")
                raise MCPToolError(f"Health check failed: {e}")
    
    async def list_hosts(self) -> List[Host]:
        """
        List Hosts Tool
        
        List all hosts in the fleet with metadata including hostname, OS, 
        last update date, and package count.
        """
        with create_custom_span("mcp_tool_list_hosts") as span:
            try:
                add_baggage("mcp.tool", "list_hosts")
                
                # Get host information with last updates
                host_infos = await self.client.get_host_info()
                
                hosts = []
                for info in host_infos:
                    # Get package count for this host by fetching recent history
                    try:
                        history = await self.client.get_host_history(
                            hostname=info.hostname,
                            limit=1000  # Get a large sample to count packages
                        )
                        
                        # Count unique packages
                        package_names = set()
                        for item in history.items:
                            package_names.add(item.get('name', ''))
                        
                        packages_count = len(package_names)
                        
                    except Exception:
                        packages_count = None  # Unable to determine
                    
                    hosts.append(Host(
                        hostname=info.hostname,
                        os=info.os,
                        last_update=info.last_update,
                        packages_count=packages_count
                    ))
                
                span.set_attribute("hosts.count", len(hosts))
                span.set_attribute("mcp.tool.success", True)
                
                return hosts
                
            except Exception as e:
                span.set_attribute("mcp.tool.success", False)
                span.set_attribute("error.message", str(e))
                logger.error(f"List hosts tool failed: {e}")
                raise MCPToolError(f"Failed to list hosts: {e}")
    
    async def get_host_details(self, hostname: str) -> Host:
        """
        Get Host Details Tool
        
        Get detailed information for a specific host.
        """
        with create_custom_span("mcp_tool_get_host_details", {"hostname": hostname}) as span:
            try:
                add_baggage("mcp.tool", "get_host_details")
                add_baggage("hostname", hostname)
                
                # Get host info from last updates
                host_infos = await self.client.get_host_info()
                host_info = None
                
                for info in host_infos:
                    if info.hostname == hostname:
                        host_info = info
                        break
                
                if not host_info:
                    raise MCPToolError(f"Host not found: {hostname}")
                
                # Get package count
                try:
                    history = await self.client.get_host_history(
                        hostname=hostname,
                        limit=1000
                    )
                    
                    package_names = set()
                    for item in history.items:
                        package_names.add(item.get('name', ''))
                    
                    packages_count = len(package_names)
                    
                except Exception:
                    packages_count = None
                
                host = Host(
                    hostname=host_info.hostname,
                    os=host_info.os,
                    last_update=host_info.last_update,
                    packages_count=packages_count
                )
                
                span.set_attribute("host.packages_count", packages_count or 0)
                span.set_attribute("mcp.tool.success", True)
                
                return host
                
            except Exception as e:
                span.set_attribute("mcp.tool.success", False)
                span.set_attribute("error.message", str(e))
                logger.error(f"Get host details tool failed: {e}")
                raise MCPToolError(f"Failed to get host details: {e}")
    
    async def get_update_reports(
        self, 
        hostname: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[UpdateReport]:
        """
        Get Update Reports Tool
        
        Retrieve package update reports with optional hostname filtering.
        Supports pagination with limit parameter.
        """
        with create_custom_span("mcp_tool_get_update_reports") as span:
            try:
                add_baggage("mcp.tool", "get_update_reports")
                if hostname:
                    add_baggage("hostname", hostname)
                
                # Get update data
                updates = await self.client.get_all_updates(
                    hostname=hostname,
                    limit=limit,
                    offset=offset
                )
                
                # Group by hostname and date to create reports
                reports_map = defaultdict(lambda: defaultdict(list))
                
                for update in updates:
                    host = update.get('hostname', '')
                    update_date = update.get('update_date', '')
                    
                    package_update = PackageUpdate(
                        name=update.get('name', ''),
                        old_version=update.get('old_version', ''),
                        new_version=update.get('new_version', '')
                    )
                    
                    reports_map[host][update_date].append(package_update)
                
                # Convert to UpdateReport objects
                reports = []
                report_id = 1
                
                for host, date_updates in reports_map.items():
                    for update_date, packages in date_updates.items():
                        # Get OS from first package update
                        os_name = "unknown"
                        for update in updates:
                            if (update.get('hostname') == host and 
                                update.get('update_date') == update_date):
                                os_name = update.get('os', 'unknown')
                                break
                        
                        reports.append(UpdateReport(
                            id=report_id,
                            hostname=host,
                            os=os_name,
                            update_date=date.fromisoformat(update_date) if update_date else date.today(),
                            updated_packages=packages
                        ))
                        report_id += 1
                
                # Sort by date (newest first)
                reports.sort(key=lambda r: r.update_date, reverse=True)
                
                span.set_attribute("reports.count", len(reports))
                span.set_attribute("mcp.tool.success", True)
                
                return reports
                
            except Exception as e:
                span.set_attribute("mcp.tool.success", False)
                span.set_attribute("error.message", str(e))
                logger.error(f"Get update reports tool failed: {e}")
                raise MCPToolError(f"Failed to get update reports: {e}")
    
    async def get_host_reports(self, hostname: str, limit: int = 50, offset: int = 0) -> List[UpdateReport]:
        """
        Get Host Reports Tool
        
        Get update reports for a specific host.
        """
        return await self.get_update_reports(hostname=hostname, limit=limit, offset=offset)
    
    async def list_packages(self) -> List[PackageInfo]:
        """
        List Packages Tool
        
        List all packages across the fleet with information about which hosts have them.
        """
        with create_custom_span("mcp_tool_list_packages") as span:
            try:
                add_baggage("mcp.tool", "list_packages")
                
                # Get all updates to analyze packages
                updates = await self.client.get_all_updates(limit=10000)  # Large limit to get all
                
                # Group by package name
                packages_map = defaultdict(lambda: {
                    'hosts': set(),
                    'versions': set(),
                    'last_updated': None
                })
                
                for update in updates:
                    package_name = update.get('name', '')
                    hostname = update.get('hostname', '')
                    new_version = update.get('new_version', '')
                    update_date = update.get('update_date', '')
                    
                    if package_name:
                        packages_map[package_name]['hosts'].add(hostname)
                        if new_version:
                            packages_map[package_name]['versions'].add(new_version)
                        
                        # Track latest update date
                        if update_date:
                            try:
                                update_date_obj = date.fromisoformat(update_date)
                                if (packages_map[package_name]['last_updated'] is None or
                                    update_date_obj > packages_map[package_name]['last_updated']):
                                    packages_map[package_name]['last_updated'] = update_date_obj
                            except ValueError:
                                pass
                
                # Convert to PackageInfo objects
                packages = []
                for package_name, info in packages_map.items():
                    # Use most common version as current version
                    current_version = None
                    if info['versions']:
                        version_counts = Counter(info['versions'])
                        current_version = version_counts.most_common(1)[0][0]
                    
                    packages.append(PackageInfo(
                        name=package_name,
                        current_version=current_version,
                        hosts=list(info['hosts']),
                        last_updated=info['last_updated']
                    ))
                
                # Sort by name
                packages.sort(key=lambda p: p.name)
                
                span.set_attribute("packages.count", len(packages))
                span.set_attribute("mcp.tool.success", True)
                
                return packages
                
            except Exception as e:
                span.set_attribute("mcp.tool.success", False)
                span.set_attribute("error.message", str(e))
                logger.error(f"List packages tool failed: {e}")
                raise MCPToolError(f"Failed to list packages: {e}")
    
    async def get_package_details(self, package_name: str) -> PackageInfo:
        """
        Get Package Details Tool
        
        Get detailed information about a specific package including which hosts have it installed.
        """
        with create_custom_span("mcp_tool_get_package_details", {"package_name": package_name}) as span:
            try:
                add_baggage("mcp.tool", "get_package_details")
                add_baggage("package_name", package_name)
                
                # Get all updates for this package
                updates = await self.client.get_all_updates(
                    package=package_name,
                    limit=10000
                )
                
                if not updates:
                    raise MCPToolError(f"Package not found: {package_name}")
                
                hosts = set()
                versions = []
                last_updated = None
                
                for update in updates:
                    if update.get('name', '') == package_name:
                        hosts.add(update.get('hostname', ''))
                        new_version = update.get('new_version', '')
                        if new_version:
                            versions.append(new_version)
                        
                        update_date = update.get('update_date', '')
                        if update_date:
                            try:
                                update_date_obj = date.fromisoformat(update_date)
                                if last_updated is None or update_date_obj > last_updated:
                                    last_updated = update_date_obj
                            except ValueError:
                                pass
                
                # Use most common version as current version
                current_version = None
                if versions:
                    version_counts = Counter(versions)
                    current_version = version_counts.most_common(1)[0][0]
                
                package_info = PackageInfo(
                    name=package_name,
                    current_version=current_version,
                    hosts=list(hosts),
                    last_updated=last_updated
                )
                
                span.set_attribute("package.hosts_count", len(hosts))
                span.set_attribute("package.current_version", current_version or "unknown")
                span.set_attribute("mcp.tool.success", True)
                
                return package_info
                
            except Exception as e:
                span.set_attribute("mcp.tool.success", False)
                span.set_attribute("error.message", str(e))
                logger.error(f"Get package details tool failed: {e}")
                raise MCPToolError(f"Failed to get package details: {e}")
    
    async def get_fleet_statistics(self) -> FleetStatistics:
        """
        Fleet Statistics Tool
        
        Get aggregate statistics about the fleet including total hosts, reports, 
        and activity metrics.
        """
        with create_custom_span("mcp_tool_get_fleet_statistics") as span:
            try:
                add_baggage("mcp.tool", "get_fleet_statistics")
                
                # Get all hosts and updates
                hosts = await self.client.list_hosts()
                all_updates = await self.client.get_all_updates(limit=10000)
                
                # Calculate statistics
                total_hosts = len(hosts)
                total_reports = len(all_updates)
                
                # Count unique packages
                unique_packages = set()
                for update in all_updates:
                    package_name = update.get('name', '')
                    if package_name:
                        unique_packages.add(package_name)
                
                total_packages = len(unique_packages)
                
                # Calculate activity metrics
                today = date.today()
                seven_days_ago = today - timedelta(days=7)
                thirty_days_ago = today - timedelta(days=30)
                
                active_hosts_7d = set()
                active_hosts_30d = set()
                package_counts = Counter()
                recent_activity = []
                
                for update in all_updates:
                    update_date_str = update.get('update_date', '')
                    hostname = update.get('hostname', '')
                    package_name = update.get('name', '')
                    
                    if update_date_str:
                        try:
                            update_date = date.fromisoformat(update_date_str)
                            
                            # Track active hosts
                            if update_date >= seven_days_ago:
                                active_hosts_7d.add(hostname)
                            if update_date >= thirty_days_ago:
                                active_hosts_30d.add(hostname)
                            
                            # Count package updates
                            if package_name:
                                package_counts[package_name] += 1
                            
                            # Track recent activity (last 7 days)
                            if update_date >= seven_days_ago:
                                recent_activity.append({
                                    "date": update_date_str,
                                    "hostname": hostname,
                                    "package": package_name,
                                    "old_version": update.get('old_version', ''),
                                    "new_version": update.get('new_version', '')
                                })
                                
                        except ValueError:
                            pass
                
                # Get most updated packages (top 10)
                most_updated_packages = [
                    {"package": package, "update_count": count}
                    for package, count in package_counts.most_common(10)
                ]
                
                # Sort recent activity by date (newest first)
                recent_activity.sort(key=lambda x: x['date'], reverse=True)
                recent_activity = recent_activity[:20]  # Limit to 20 most recent
                
                stats = FleetStatistics(
                    total_hosts=total_hosts,
                    total_reports=total_reports,
                    total_packages=total_packages,
                    active_hosts_last_7_days=len(active_hosts_7d),
                    active_hosts_last_30_days=len(active_hosts_30d),
                    most_updated_packages=most_updated_packages,
                    recent_activity=recent_activity
                )
                
                span.set_attribute("stats.total_hosts", total_hosts)
                span.set_attribute("stats.total_reports", total_reports)
                span.set_attribute("stats.total_packages", total_packages)
                span.set_attribute("mcp.tool.success", True)
                
                return stats
                
            except Exception as e:
                span.set_attribute("mcp.tool.success", False)
                span.set_attribute("error.message", str(e))
                logger.error(f"Get fleet statistics tool failed: {e}")
                raise MCPToolError(f"Failed to get fleet statistics: {e}")
    
    async def search(self, query: str, result_type: Optional[str] = None) -> SearchResponse:
        """
        Search Tool
        
        Search across hosts, packages, and reports for the given query.
        """
        with create_custom_span("mcp_tool_search", {"query": query}) as span:
            try:
                add_baggage("mcp.tool", "search")
                add_baggage("search.query", query)
                
                results = []
                query_lower = query.lower()
                
                # Search hosts if not filtered
                if not result_type or result_type == "host":
                    try:
                        hosts = await self.list_hosts()
                        for host in hosts:
                            if query_lower in host.hostname.lower() or query_lower in host.os.lower():
                                results.append(SearchResult(
                                    result_type="host",
                                    data=host.dict(),
                                    relevance_score=1.0 if query_lower == host.hostname.lower() else 0.8
                                ))
                    except Exception as e:
                        logger.warning(f"Failed to search hosts: {e}")
                
                # Search packages if not filtered
                if not result_type or result_type == "package":
                    try:
                        packages = await self.list_packages()
                        for package in packages:
                            if query_lower in package.name.lower():
                                results.append(SearchResult(
                                    result_type="package",
                                    data=package.dict(),
                                    relevance_score=1.0 if query_lower == package.name.lower() else 0.8
                                ))
                    except Exception as e:
                        logger.warning(f"Failed to search packages: {e}")
                
                # Search reports if not filtered
                if not result_type or result_type == "report":
                    try:
                        reports = await self.get_update_reports(limit=100)
                        for report in reports:
                            # Search in hostname, OS, or package names
                            match_score = 0.0
                            if query_lower in report.hostname.lower():
                                match_score = max(match_score, 0.9)
                            if query_lower in report.os.lower():
                                match_score = max(match_score, 0.7)
                            
                            for package in report.updated_packages:
                                if query_lower in package.name.lower():
                                    match_score = max(match_score, 0.8)
                            
                            if match_score > 0:
                                results.append(SearchResult(
                                    result_type="report",
                                    data=report.dict(),
                                    relevance_score=match_score
                                ))
                    except Exception as e:
                        logger.warning(f"Failed to search reports: {e}")
                
                # Sort by relevance score (highest first)
                results.sort(key=lambda x: x.relevance_score or 0, reverse=True)
                
                # Limit results
                results = results[:50]
                
                search_response = SearchResponse(
                    query=query,
                    results=results,
                    total_results=len(results)
                )
                
                span.set_attribute("search.results_count", len(results))
                span.set_attribute("mcp.tool.success", True)
                
                return search_response
                
            except Exception as e:
                span.set_attribute("mcp.tool.success", False)
                span.set_attribute("error.message", str(e))
                logger.error(f"Search tool failed: {e}")
                raise MCPToolError(f"Search failed: {e}")


# Global tools instance
_tools: Optional[MCPTools] = None


def get_mcp_tools() -> MCPTools:
    """Get or create the global MCP tools instance."""
    global _tools
    if _tools is None:
        _tools = MCPTools()
    return _tools