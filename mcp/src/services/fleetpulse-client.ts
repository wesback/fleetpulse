import { logger } from '../logger';

/**
 * FleetPulse Backend API Client
 * Handles communication with the FastAPI backend
 */

export interface FleetPulseHost {
  hostname: string;
  os: string;
  last_update: string;
}

export interface PackageUpdate {
  id: number;
  hostname: string;
  os: string;
  update_date: string;
  name: string;
  old_version: string;
  new_version: string;
}

export interface FleetPulseStatistics {
  total_hosts: number;
  total_updates: number;
  recent_updates: number;
  top_packages: Array<{ name: string; count: number }>;
  updates_by_os: Array<{ os: string; count: number }>;
  updates_timeline: Array<{ date: string; count: number }>;
  host_activity: Array<{ hostname: string; last_activity: string; update_count: number }>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export class FleetPulseAPIClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    // Use provided URL or fall back to default localhost
    this.baseUrl = baseUrl || 'http://localhost:8000';
  }

  /**
   * Get list of all hosts
   */
  async getHosts(): Promise<string[]> {
    try {
      const response = await fetch(`${this.baseUrl}/hosts`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json() as { hosts?: string[] };
      return data.hosts || [];
    } catch (error) {
      logger.error('Failed to fetch hosts', { error: error instanceof Error ? error.message : error });
      throw new Error('Failed to fetch hosts from FleetPulse backend');
    }
  }

  /**
   * Get update history for a specific host
   */
  async getHostHistory(
    hostname: string,
    options: {
      dateFrom?: string;
      dateTo?: string;
      os?: string;
      package?: string;
      limit?: number;
      offset?: number;
    } = {}
  ): Promise<PaginatedResponse<PackageUpdate>> {
    try {
      const params = new URLSearchParams();
      if (options.dateFrom) params.set('date_from', options.dateFrom);
      if (options.dateTo) params.set('date_to', options.dateTo);
      if (options.os) params.set('os', options.os);
      if (options.package) params.set('package', options.package);
      if (options.limit) params.set('limit', options.limit.toString());
      if (options.offset) params.set('offset', options.offset.toString());

      const url = `${this.baseUrl}/history/${encodeURIComponent(hostname)}?${params.toString()}`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json() as PaginatedResponse<PackageUpdate>;
    } catch (error) {
      logger.error('Failed to fetch host history', { 
        hostname, 
        options, 
        error: error instanceof Error ? error.message : error 
      });
      throw new Error(`Failed to fetch history for host ${hostname}`);
    }
  }

  /**
   * Get comprehensive statistics
   */
  async getStatistics(): Promise<FleetPulseStatistics> {
    try {
      const response = await fetch(`${this.baseUrl}/statistics`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json() as FleetPulseStatistics;
    } catch (error) {
      logger.error('Failed to fetch statistics', { error: error instanceof Error ? error.message : error });
      throw new Error('Failed to fetch statistics from FleetPulse backend');
    }
  }

  /**
   * Check backend health
   */
  async checkHealth(): Promise<{ status: string; details?: any }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json() as { status: string; details?: any };
    } catch (error) {
      logger.error('Failed to check backend health', { error: error instanceof Error ? error.message : error });
      return { status: 'unhealthy', details: error instanceof Error ? error.message : error };
    }
  }

  /**
   * Submit a package update report
   */
  async reportUpdate(update: {
    hostname: string;
    os: string;
    update_date: string;
    updated_packages: Array<{
      name: string;
      old_version: string;
      new_version: string;
    }>;
  }): Promise<{ status: string; message: string; hostname: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(update),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({})) as { detail?: string };
        throw new Error(`HTTP ${response.status}: ${errorData.detail || response.statusText}`);
      }
      
      return await response.json() as { status: string; message: string; hostname: string };
    } catch (error) {
      logger.error('Failed to report update', { 
        hostname: update.hostname, 
        error: error instanceof Error ? error.message : error 
      });
      throw new Error(`Failed to report update for host ${update.hostname}`);
    }
  }
}
