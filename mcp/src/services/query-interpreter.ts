import { FleetPulseAPIClient } from './fleetpulse-client';
import { logger } from '../logger';

/**
 * FleetPulse Query Interpreter
 * Interprets natural language questions about FleetPulse and routes them to appropriate API calls
 */

export interface QueryResult {
  success: boolean;
  data?: any;
  message: string;
  context_type: string;
  suggestions?: string[];
}

export class FleetPulseQueryInterpreter {
  private apiClient: FleetPulseAPIClient;

  constructor(backendUrl?: string) {
    this.apiClient = new FleetPulseAPIClient(backendUrl);
  }

  /**
   * Interpret and execute a query about FleetPulse
   */
  async interpretQuery(query: string): Promise<QueryResult> {
    const normalizedQuery = query.toLowerCase().trim();
    
    try {
      // Debug logging
      logger.info('Query interpretation debug', {
        originalQuery: query,
        normalizedQuery,
        isHealth: this.isHealthQuery(normalizedQuery),
        isPackageUpdate: this.isPackageUpdateQuery(normalizedQuery),
        isStatistics: this.isStatisticsQuery(normalizedQuery),
        isHost: this.isHostQuery(normalizedQuery)
      });

      // Health and status queries
      if (this.isHealthQuery(normalizedQuery)) {
        return await this.handleHealthQuery();
      }

      // Package update queries (high priority to catch specific timeframe questions)
      if (this.isPackageUpdateQuery(normalizedQuery)) {
        return await this.handlePackageUpdateQuery(normalizedQuery);
      }

      // Statistics and overview queries
      if (this.isStatisticsQuery(normalizedQuery)) {
        return await this.handleStatisticsQuery(normalizedQuery);
      }

      // Host-related queries
      if (this.isHostQuery(normalizedQuery)) {
        return await this.handleHostQuery(normalizedQuery);
      }

      // Package-related queries
      if (this.isPackageQuery(normalizedQuery)) {
        return await this.handlePackageQuery(normalizedQuery);
      }

      // Update history queries
      if (this.isHistoryQuery(normalizedQuery)) {
        return await this.handleHistoryQuery(normalizedQuery);
      }

      // General help or unknown queries
      return this.handleGeneralQuery();

    } catch (error) {
      logger.error('Query interpretation failed', { 
        query, 
        error: error instanceof Error ? error.message : error 
      });
      
      return {
        success: false,
        message: `Sorry, I encountered an error while processing your query: ${error instanceof Error ? error.message : 'Unknown error'}`,
        context_type: 'error',
        suggestions: [
          'Try asking about FleetPulse statistics',
          'Ask about specific hosts',
          'Check the health status'
        ]
      };
    }
  }

  private isHealthQuery(query: string): boolean {
    const healthKeywords = ['health', 'status', 'running', 'operational', 'working'];
    
    // Check for "up" as a standalone word only (not part of upgrade, update, etc.)
    const standaloneUp = /\bis\s+(?:the\s+)?(?:system|server|service|backend|api)\s+up\b/i.test(query) ||
                         /\bup\s+(?:and\s+)?(?:running|operational)\b/i.test(query) ||
                         /\bsystem\s+up\b/i.test(query);
    
    return healthKeywords.some(keyword => query.includes(keyword)) || standaloneUp;
  }

  private isStatisticsQuery(query: string): boolean {
    // Don't classify as statistics if it's specifically about packages/updates with timeframes
    if (this.isPackageUpdateQuery(query)) {
      return false;
    }
    
    const statsKeywords = ['statistics', 'stats', 'overview', 'summary', 'dashboard'];
    const generalCountKeywords = ['total', 'count', 'how many'];
    
    // Only match general count queries if they don't have specific context
    const hasGeneralCount = generalCountKeywords.some(keyword => query.includes(keyword));
    const hasSpecificContext = query.includes('package') || query.includes('update') || query.includes('upgrade') || 
                              query.includes('host') || query.includes('day') || query.includes('week') || query.includes('month');
    
    return statsKeywords.some(keyword => query.includes(keyword)) || 
           (hasGeneralCount && !hasSpecificContext);
  }

  private isHostQuery(query: string): boolean {
    const hostKeywords = ['host', 'hosts', 'server', 'servers', 'machine', 'machines', 'computer'];
    return hostKeywords.some(keyword => query.includes(keyword)) && !this.isPackageUpdateQuery(query);
  }

  private isPackageQuery(query: string): boolean {
    const packageKeywords = ['package', 'packages', 'software', 'application', 'app', 'program'];
    return packageKeywords.some(keyword => query.includes(keyword));
  }

  private isHistoryQuery(query: string): boolean {
    const historyKeywords = ['history', 'updates', 'recent', 'latest', 'timeline', 'when', 'what happened'];
    return historyKeywords.some(keyword => query.includes(keyword));
  }

  private isPackageUpdateQuery(query: string): boolean {
    const packageKeywords = ['package', 'packages'];
    const updateKeywords = ['update', 'updates', 'upgrade', 'upgraded', 'install', 'installed'];
    const timeKeywords = ['day', 'days', 'week', 'weeks', 'month', 'months', 'last', 'recent', 'today', 'yesterday'];
    
    const hasPackage = packageKeywords.some(keyword => query.includes(keyword));
    const hasUpdate = updateKeywords.some(keyword => query.includes(keyword));
    const hasTime = timeKeywords.some(keyword => query.includes(keyword));
    
    return (hasPackage && hasUpdate) || (hasUpdate && hasTime);
  }

  private async handleHealthQuery(): Promise<QueryResult> {
    const health = await this.apiClient.checkHealth();
    
    return {
      success: health.status === 'healthy',
      data: health,
      message: health.status === 'healthy' 
        ? 'FleetPulse backend is healthy and operational!' 
        : `FleetPulse backend status: ${health.status}`,
      context_type: 'health_check',
      suggestions: [
        'Get overall statistics',
        'List all hosts',
        'Check recent updates'
      ]
    };
  }

  private async handleStatisticsQuery(query: string): Promise<QueryResult> {
    const stats = await this.apiClient.getStatistics();
    
    // Customize response based on specific aspect requested
    if (query.includes('recent')) {
      return {
        success: true,
        data: { recent_updates: stats.recent_updates, total_updates: stats.total_updates },
        message: `FleetPulse has recorded ${stats.recent_updates} updates in the last 30 days out of ${stats.total_updates} total updates.`,
        context_type: 'recent_updates',
        suggestions: [
          'Get list of all hosts',
          'Check top updated packages',
          'View updates by operating system'
        ]
      };
    }

    if (query.includes('host')) {
      return {
        success: true,
        data: { total_hosts: stats.total_hosts, host_activity: stats.host_activity },
        message: `FleetPulse is currently tracking ${stats.total_hosts} hosts across your fleet.`,
        context_type: 'host_statistics',
        suggestions: [
          'Get detailed host list',
          'Check specific host history',
          'View host activity details'
        ]
      };
    }

    // General statistics response
    const topPackage = stats.top_packages[0];
    return {
      success: true,
      data: stats,
      message: `FleetPulse Overview: ${stats.total_hosts} hosts, ${stats.total_updates} total updates, ${stats.recent_updates} recent updates. Most updated package: ${topPackage?.name || 'N/A'} (${topPackage?.count || 0} updates).`,
      context_type: 'full_statistics',
      suggestions: [
        'Get list of hosts',
        'View top packages by updates',
        'Check updates by OS',
        'View recent activity timeline'
      ]
    };
  }

  private async handleHostQuery(query: string): Promise<QueryResult> {
    const hosts = await this.apiClient.getHosts();
    
    // Check if asking for a specific host
    const hostMatch = this.extractHostname(query, hosts);
    if (hostMatch) {
      const history = await this.apiClient.getHostHistory(hostMatch, { limit: 10 });
      return {
        success: true,
        data: { hostname: hostMatch, recent_updates: history.items, total: history.total },
        message: `Host "${hostMatch}" has ${history.total} total updates. Most recent: ${history.items[0]?.name || 'none'} on ${history.items[0]?.update_date || 'N/A'}.`,
        context_type: 'specific_host_info',
        suggestions: [
          `Get full history for ${hostMatch}`,
          'Check other hosts',
          'View host statistics'
        ]
      };
    }

    // General host list
    return {
      success: true,
      data: { hosts, count: hosts.length },
      message: `FleetPulse is tracking ${hosts.length} hosts: ${hosts.slice(0, 5).join(', ')}${hosts.length > 5 ? '...' : ''}`,
      context_type: 'host_list',
      suggestions: hosts.slice(0, 3).map(host => `Get updates for ${host}`)
    };
  }

  private async handlePackageQuery(query: string): Promise<QueryResult> {
    const stats = await this.apiClient.getStatistics();
    
    if (query.includes('top') || query.includes('most')) {
      return {
        success: true,
        data: { top_packages: stats.top_packages },
        message: `Top updated packages: ${stats.top_packages.slice(0, 5).map(p => `${p.name} (${p.count} updates)`).join(', ')}`,
        context_type: 'top_packages',
        suggestions: [
          'Get updates for specific host',
          'Check recent package updates',
          'View package updates by OS'
        ]
      };
    }

    // Check if asking about a specific package
    const packageName = this.extractPackageName(query);
    if (packageName) {
      // This would require a new API endpoint to search by package name
      return {
        success: false,
        message: `I'd love to help you find information about package "${packageName}", but I need a specific host to search on. Which host would you like me to check?`,
        context_type: 'package_search_needs_host',
        suggestions: [
          'List all hosts first',
          'Check top packages overall',
          'Get recent updates for a specific host'
        ]
      };
    }

    return {
      success: true,
      data: { top_packages: stats.top_packages, updates_by_os: stats.updates_by_os },
      message: `FleetPulse tracks package updates across your fleet. Top packages: ${stats.top_packages.slice(0, 3).map(p => p.name).join(', ')}`,
      context_type: 'package_overview',
      suggestions: [
        'View top updated packages',
        'Check packages by operating system',
        'Get updates for specific host'
      ]
    };
  }

  private async handleHistoryQuery(query: string): Promise<QueryResult> {
    // If a specific host is mentioned, get its history
    const hosts = await this.apiClient.getHosts();
    const hostMatch = this.extractHostname(query, hosts);
    
    if (hostMatch) {
      const history = await this.apiClient.getHostHistory(hostMatch, { limit: 20 });
      const recentUpdates = history.items.slice(0, 5);
      
      return {
        success: true,
        data: { hostname: hostMatch, updates: recentUpdates, total: history.total },
        message: `Recent updates for ${hostMatch}: ${recentUpdates.map(u => `${u.name} (${u.old_version} → ${u.new_version})`).join(', ')}`,
        context_type: 'host_update_history',
        suggestions: [
          `Get older updates for ${hostMatch}`,
          'Check other hosts',
          'View overall statistics'
        ]
      };
    }

    // General recent activity
    const stats = await this.apiClient.getStatistics();
    return {
      success: true,
      data: { recent_updates: stats.recent_updates, timeline: stats.updates_timeline, host_activity: stats.host_activity },
      message: `Recent FleetPulse activity: ${stats.recent_updates} updates in the last 30 days across ${stats.host_activity.length} active hosts.`,
      context_type: 'recent_activity_overview',
      suggestions: [
        'Get updates for specific host',
        'View most active hosts',
        'Check top updated packages'
      ]
    };
  }

  private async handlePackageUpdateQuery(query: string): Promise<QueryResult> {
    // Extract timeframe from query
    const timeframe = this.extractTimeframe(query);
    
    try {
      if (timeframe.days <= 1) {
        // For "last day" or "today" queries, we need to get recent updates
        // Get updates from all hosts and filter by date
        const hosts = await this.apiClient.getHosts();
        let totalUpdates = 0;
        const updatesByHost: Record<string, number> = {};
        
        for (const host of hosts.slice(0, 10)) { // Limit to first 10 hosts for performance
          try {
            const history = await this.apiClient.getHostHistory(host, { limit: 50 });
            const recentUpdates = history.items.filter(update => {
              const updateDate = new Date(update.update_date);
              const cutoffDate = new Date();
              cutoffDate.setDate(cutoffDate.getDate() - timeframe.days);
              return updateDate >= cutoffDate;
            });
            updatesByHost[host] = recentUpdates.length;
            totalUpdates += recentUpdates.length;
          } catch (error) {
            logger.warn(`Failed to get history for host ${host}`, { error });
          }
        }
        
        const topHosts = Object.entries(updatesByHost)
          .filter(([, count]) => count > 0)
          .sort(([, a], [, b]) => b - a)
          .slice(0, 5);
        
        return {
          success: true,
          data: { 
            total_updates: totalUpdates, 
            timeframe: timeframe.description,
            updates_by_host: updatesByHost,
            top_hosts: topHosts
          },
          message: totalUpdates > 0 
            ? `Found ${totalUpdates} package updates in ${timeframe.description}. Top active hosts: ${topHosts.map(([host, count]) => `${host} (${count})`).join(', ')}`
            : `No package updates found in ${timeframe.description}.`,
          context_type: 'package_updates_timeframe',
          suggestions: [
            'Check updates for specific hosts',
            'View top updated packages',
            'Get updates for longer timeframe'
          ]
        };
      } else {
        // For longer timeframes, use the statistics data
        const stats = await this.apiClient.getStatistics();
        
        return {
          success: true,
          data: { 
            recent_updates: stats.recent_updates, 
            timeframe: timeframe.description,
            total_updates: stats.total_updates,
            top_packages: stats.top_packages.slice(0, 5)
          },
          message: `FleetPulse has recorded ${stats.recent_updates} package updates in ${timeframe.description}. Most updated packages: ${stats.top_packages.slice(0, 3).map(p => `${p.name} (${p.count})`).join(', ')}`,
          context_type: 'package_updates_period',
          suggestions: [
            'Get updates by host',
            'View specific package details',
            'Check updates by operating system'
          ]
        };
      }
    } catch (error) {
      logger.error('Failed to get package update data', { query, error });
      return {
        success: false,
        message: `Sorry, I couldn't retrieve package update information: ${error instanceof Error ? error.message : 'Unknown error'}`,
        context_type: 'error',
        suggestions: [
          'Try asking about general statistics',
          'Check specific host updates',
          'View system health status'
        ]
      };
    }
  }

  private extractTimeframe(query: string): { days: number; description: string } {
    // Handle specific timeframe keywords
    if (query.includes('today')) {
      return { days: 0, description: 'today' };
    }
    if (query.includes('yesterday')) {
      return { days: 1, description: 'yesterday' };
    }
    if (query.includes('last day') || query.includes('past day')) {
      return { days: 1, description: 'the last day' };
    }
    if (query.includes('last week') || query.includes('past week')) {
      return { days: 7, description: 'the last week' };
    }
    if (query.includes('last month') || query.includes('past month')) {
      return { days: 30, description: 'the last month' };
    }
    
    // Look for number patterns
    const dayMatch = query.match(/(\d+)\s*days?/);
    if (dayMatch) {
      const days = parseInt(dayMatch[1]);
      return { days, description: `the last ${days} day${days > 1 ? 's' : ''}` };
    }
    
    const weekMatch = query.match(/(\d+)\s*weeks?/);
    if (weekMatch) {
      const weeks = parseInt(weekMatch[1]);
      const days = weeks * 7;
      return { days, description: `the last ${weeks} week${weeks > 1 ? 's' : ''}` };
    }
    
    // Default to last 30 days for general "recent" queries
    return { days: 30, description: 'the last 30 days' };
  }

  private handleGeneralQuery(): QueryResult {
    const capabilities = [
      'Check FleetPulse system health and status',
      'Get overall statistics and metrics',
      'List all hosts in your fleet',
      'View update history for specific hosts',
      'Find top updated packages',
      'Analyze updates by operating system',
      'Track recent update activity'
    ];

    return {
      success: true,
      data: { capabilities },
      message: `I can help you with FleetPulse fleet management! I can: ${capabilities.slice(0, 3).join(', ')}, and more.`,
      context_type: 'general_help',
      suggestions: [
        'Get FleetPulse statistics',
        'List all hosts',
        'Check system health',
        'View recent updates'
      ]
    };
  }

  private extractHostname(query: string, availableHosts: string[]): string | null {
    // Look for exact host matches
    for (const host of availableHosts) {
      if (query.includes(host.toLowerCase())) {
        return host;
      }
    }
    
    // Look for partial matches
    for (const host of availableHosts) {
      const hostParts = host.toLowerCase().split(/[-._]/);
      if (hostParts.some(part => query.includes(part) && part.length > 2)) {
        return host;
      }
    }
    
    return null;
  }

  private extractPackageName(query: string): string | null {
    // Simple extraction - look for quoted strings or common package names
    const quotedMatch = query.match(/["']([^"']+)["']/);
    if (quotedMatch) {
      return quotedMatch[1];
    }
    
    // Common package patterns
    const packagePatterns = [
      /package\s+([a-zA-Z0-9\-_]+)/,
      /([a-zA-Z0-9\-_]+)\s+package/,
      /about\s+([a-zA-Z0-9\-_]+)/
    ];
    
    for (const pattern of packagePatterns) {
      const match = query.match(pattern);
      if (match && match[1].length > 2) {
        return match[1];
      }
    }
    
    return null;
  }
}
