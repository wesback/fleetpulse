/**
 * Example: Using Auto-Generated Routing in a Real MCP Server
 * This shows how to integrate the automated routing system into your actual MCP server
 */

import { OpenAPIAnalyzer, RoutingConfig } from './src/services/openapi-analyzer';
import { FleetPulseAPIClient } from './src/services/fleetpulse-client';
import { logger } from './src/logger';

export interface SmartQueryResult {
  success: boolean;
  data?: any;
  message: string;
  context_type: string;
  suggestions?: string[];
  routing_metadata: {
    matched_category: string;
    confidence: number;
    matched_keywords: string[];
    endpoint_used: string;
    processing_time_ms: number;
  };
}

export class SmartFleetPulseInterpreter {
  private apiClient: FleetPulseAPIClient;
  private routingConfig: RoutingConfig | null = null;
  private routingFunctions: Map<string, (query: string) => boolean> = new Map();

  constructor(backendUrl: string, openApiSpec?: any) {
    this.apiClient = new FleetPulseAPIClient(backendUrl);
    
    if (openApiSpec) {
      this.initializeSmartRouting(openApiSpec);
    }
  }

  /**
   * Initialize smart routing from OpenAPI specification
   */
  private initializeSmartRouting(openApiSpec: any): void {
    try {
      const analyzer = new OpenAPIAnalyzer(openApiSpec);
      this.routingConfig = analyzer.generateRoutingConfig();
      
      // Create optimized routing functions
      this.generateOptimizedRoutingFunctions();
      
      logger.info('Smart routing initialized successfully', {
        rules_count: this.routingConfig.rules.length,
        endpoints_count: this.routingConfig.metadata.totalEndpoints
      });
    } catch (error) {
      logger.error('Failed to initialize smart routing', { error });
    }
  }

  /**
   * Generate optimized routing functions with improved logic
   */
  private generateOptimizedRoutingFunctions(): void {
    if (!this.routingConfig) return;

    for (const rule of this.routingConfig.rules) {
      // Create smarter routing function that considers word boundaries
      const routingFunction = (query: string): boolean => {
        const normalizedQuery = query.toLowerCase().trim();
        
        // Check for exact keyword matches with word boundaries
        const hasExactKeyword = rule.keywords.some(keyword => {
          const wordBoundaryRegex = new RegExp(`\\\\b${keyword}\\\\b`, 'i');
          return wordBoundaryRegex.test(normalizedQuery);
        });
        
        // Check intent patterns
        const matchesIntent = rule.intentPatterns.some(pattern => {
          const regex = new RegExp(pattern.replace(/\\*/g, '\\\\w*'), 'i');
          return regex.test(normalizedQuery);
        });
        
        // Check negative keywords with word boundaries
        let hasNegativeKeyword = false;
        if (rule.negativeKeywords) {
          hasNegativeKeyword = rule.negativeKeywords.some(keyword => {
            const wordBoundaryRegex = new RegExp(`\\\\b${keyword}\\\\b`, 'i');
            return wordBoundaryRegex.test(normalizedQuery);
          });
        }
        
        return (hasExactKeyword || matchesIntent) && !hasNegativeKeyword;
      };
      
      this.routingFunctions.set(rule.category, routingFunction);
    }
  }

  /**
   * Smart query interpretation with enhanced routing
   */
  async interpretQuery(query: string): Promise<SmartQueryResult> {
    const startTime = Date.now();
    const normalizedQuery = query.toLowerCase().trim();
    
    try {
      // Route the query
      const routingResult = this.routeQuery(normalizedQuery);
      
      if (routingResult) {
        // Execute the appropriate handler
        const result = await this.executeHandler(query, routingResult);
        
        // Add routing metadata
        result.routing_metadata = {
          matched_category: routingResult.category,
          confidence: routingResult.confidence,
          matched_keywords: routingResult.matchedKeywords,
          endpoint_used: routingResult.endpointUsed,
          processing_time_ms: Date.now() - startTime
        };
        
        return result;
      }
      
      // Fallback for unmatched queries
      return this.handleUnknownQuery(query, Date.now() - startTime);
      
    } catch (error) {
      logger.error('Query interpretation failed', { query, error });
      
      return {
        success: false,
        message: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        context_type: 'error',
        routing_metadata: {
          matched_category: 'error',
          confidence: 0,
          matched_keywords: [],
          endpoint_used: 'none',
          processing_time_ms: Date.now() - startTime
        }
      };
    }
  }

  /**
   * Route query to appropriate category
   */
  private routeQuery(query: string): {
    category: string;
    confidence: number;
    matchedKeywords: string[];
    endpointUsed: string;
  } | null {
    if (!this.routingConfig) return null;

    // Sort rules by priority and test each one
    const sortedRules = [...this.routingConfig.rules].sort((a, b) => b.priority - a.priority);
    
    for (const rule of sortedRules) {
      const routingFunction = this.routingFunctions.get(rule.category);
      
      if (routingFunction && routingFunction(query)) {
        const matchedKeywords = rule.keywords.filter(keyword => {
          const wordBoundaryRegex = new RegExp(`\\\\b${keyword}\\\\b`, 'i');
          return wordBoundaryRegex.test(query);
        });
        
        const primaryEndpoint = rule.endpoints[0];
        const endpointUsed = primaryEndpoint ? `${primaryEndpoint.method} ${primaryEndpoint.path}` : 'unknown';
        
        return {
          category: rule.category,
          confidence: rule.confidence,
          matchedKeywords,
          endpointUsed
        };
      }
    }

    return null;
  }

  /**
   * Execute the appropriate handler based on routing result
   */
  private async executeHandler(
    query: string, 
    routing: { category: string; confidence: number; matchedKeywords: string[]; endpointUsed: string }
  ): Promise<SmartQueryResult> {
    
    switch (routing.category) {
      case 'health_status':
        return await this.handleHealthQuery();
        
      case 'statistics_overview':
        return await this.handleStatisticsQuery(query);
        
      case 'host_management':
        return await this.handleHostQuery(query);
        
      case 'update_tracking':
        return await this.handleUpdateQuery(query);
        
      case 'historical_data':
        return await this.handleHistoryQuery(query);
        
      case 'reporting':
        return await this.handleReportQuery(query);
        
      case 'package_management':
        return await this.handlePackageQuery(query);
        
      default:
        return await this.handleGenericCategoryQuery(routing.category, query);
    }
  }

  /**
   * Health status query handler
   */
  private async handleHealthQuery(): Promise<SmartQueryResult> {
    const health = await this.apiClient.checkHealth();
    
    return {
      success: health.status === 'healthy',
      data: health,
      message: health.status === 'healthy' 
        ? 'FleetPulse backend is healthy and operational!' 
        : `FleetPulse backend status: ${health.status}`,
      context_type: 'health_check',
      suggestions: [
        'Get fleet statistics',
        'List all hosts',
        'Check recent updates'
      ],
      routing_metadata: {
        matched_category: 'health_status',
        confidence: 1.0,
        matched_keywords: ['health', 'status'],
        endpoint_used: 'GET /health',
        processing_time_ms: 0
      }
    };
  }

  /**
   * Statistics overview query handler
   */
  private async handleStatisticsQuery(query: string): Promise<SmartQueryResult> {
    const stats = await this.apiClient.getStatistics();
    
    // Customize response based on query specifics
    if (query.includes('recent') || query.includes('latest')) {
      return {
        success: true,
        data: { recent_updates: stats.recent_updates, total_updates: stats.total_updates },
        message: `FleetPulse shows ${stats.recent_updates} recent updates out of ${stats.total_updates} total.`,
        context_type: 'recent_statistics',
        suggestions: [
          'Get detailed host list',
          'Check top packages',
          'View update timeline'
        ],
        routing_metadata: {
          matched_category: 'statistics_overview',
          confidence: 0.9,
          matched_keywords: ['recent', 'statistics'],
          endpoint_used: 'GET /statistics',
          processing_time_ms: 0
        }
      };
    }

    return {
      success: true,
      data: stats,
      message: `FleetPulse Overview: ${stats.total_hosts} hosts, ${stats.total_updates} total updates, ${stats.recent_updates} recent updates.`,
      context_type: 'full_statistics',
      suggestions: [
        'View host details',
        'Check package trends',
        'Generate reports'
      ],
      routing_metadata: {
        matched_category: 'statistics_overview',
        confidence: 1.0,
        matched_keywords: ['statistics', 'overview'],
        endpoint_used: 'GET /statistics',
        processing_time_ms: 0
      }
    };
  }

  /**
   * Host management query handler
   */
  private async handleHostQuery(query: string): Promise<SmartQueryResult> {
    const hosts = await this.apiClient.getHosts();
    
    return {
      success: true,
      data: { hosts, count: hosts.length },
      message: `FleetPulse is monitoring ${hosts.length} hosts: ${hosts.slice(0, 3).join(', ')}${hosts.length > 3 ? '...' : ''}`,
      context_type: 'host_list',
      suggestions: hosts.slice(0, 3).map(host => `Get history for ${host}`),
      routing_metadata: {
        matched_category: 'host_management',
        confidence: 1.0,
        matched_keywords: ['hosts', 'host'],
        endpoint_used: 'GET /hosts',
        processing_time_ms: 0
      }
    };
  }

  /**
   * Update tracking query handler
   */
  private async handleUpdateQuery(query: string): Promise<SmartQueryResult> {
    const stats = await this.apiClient.getStatistics();
    
    return {
      success: true,
      data: { 
        recent_updates: stats.recent_updates,
        top_packages: stats.top_packages.slice(0, 5)
      },
      message: `Found ${stats.recent_updates} recent updates. Top packages: ${stats.top_packages.slice(0, 3).map(p => p.name).join(', ')}`,
      context_type: 'update_tracking',
      suggestions: [
        'Get updates for specific host',
        'View package details',
        'Check update timeline'
      ],
      routing_metadata: {
        matched_category: 'update_tracking',
        confidence: 0.95,
        matched_keywords: ['update', 'updates'],
        endpoint_used: 'GET /statistics',
        processing_time_ms: 0
      }
    };
  }

  /**
   * Historical data query handler
   */
  private async handleHistoryQuery(query: string): Promise<SmartQueryResult> {
    // Try to extract hostname from query
    const hosts = await this.apiClient.getHosts();
    const hostMatch = this.extractHostname(query, hosts);
    
    if (hostMatch) {
      const history = await this.apiClient.getHostHistory(hostMatch, { limit: 10 });
      return {
        success: true,
        data: { hostname: hostMatch, updates: history.items, total: history.total },
        message: `History for ${hostMatch}: ${history.total} total updates. Recent: ${history.items.slice(0, 3).map(u => u.name).join(', ')}`,
        context_type: 'host_history',
        suggestions: [
          `Get more history for ${hostMatch}`,
          'Check other hosts',
          'View timeline'
        ],
        routing_metadata: {
          matched_category: 'historical_data',
          confidence: 1.0,
          matched_keywords: ['history'],
          endpoint_used: `GET /hosts/${hostMatch}/history`,
          processing_time_ms: 0
        }
      };
    }

    return {
      success: false,
      message: 'To view history, please specify a hostname. Which host would you like to check?',
      context_type: 'history_needs_host',
      suggestions: hosts.slice(0, 5).map(host => `Get history for ${host}`),
      routing_metadata: {
        matched_category: 'historical_data',
        confidence: 0.7,
        matched_keywords: ['history'],
        endpoint_used: 'none',
        processing_time_ms: 0
      }
    };
  }

  /**
   * Report generation query handler
   */
  private async handleReportQuery(query: string): Promise<SmartQueryResult> {
    // In a real implementation, you'd call actual report endpoints
    return {
      success: true,
      message: 'Report generation is available. You can request host activity reports or package update reports.',
      context_type: 'reporting',
      suggestions: [
        'Generate host activity report',
        'Create package update report',
        'View analytics dashboard'
      ],
      routing_metadata: {
        matched_category: 'reporting',
        confidence: 0.8,
        matched_keywords: ['report', 'reports'],
        endpoint_used: 'GET /reports/*',
        processing_time_ms: 0
      }
    };
  }

  /**
   * Package management query handler
   */
  private async handlePackageQuery(query: string): Promise<SmartQueryResult> {
    const stats = await this.apiClient.getStatistics();
    
    return {
      success: true,
      data: { top_packages: stats.top_packages },
      message: `Top packages by update frequency: ${stats.top_packages.slice(0, 5).map(p => `${p.name} (${p.count} updates)`).join(', ')}`,
      context_type: 'package_overview',
      suggestions: [
        'Get package updates for specific host',
        'View package trends',
        'Check security updates'
      ],
      routing_metadata: {
        matched_category: 'package_management',
        confidence: 0.9,
        matched_keywords: ['package', 'packages'],
        endpoint_used: 'GET /statistics',
        processing_time_ms: 0
      }
    };
  }

  /**
   * Generic category handler for auto-detected categories
   */
  private async handleGenericCategoryQuery(category: string, query: string): Promise<SmartQueryResult> {
    return {
      success: false,
      message: `I detected that you're asking about ${category.replace('_', ' ')}, but I don't have a specific handler for this yet.`,
      context_type: 'unhandled_category',
      suggestions: [
        'Try asking about health status',
        'Get fleet statistics',
        'List hosts'
      ],
      routing_metadata: {
        matched_category: category,
        confidence: 0.5,
        matched_keywords: [],
        endpoint_used: 'none',
        processing_time_ms: 0
      }
    };
  }

  /**
   * Handle queries that don't match any routing rules
   */
  private handleUnknownQuery(query: string, processingTime: number): SmartQueryResult {
    return {
      success: false,
      message: `I'm not sure how to help with "${query}". Here are some things I can do:`,
      context_type: 'unknown_query',
      suggestions: this.routingConfig?.fallbackSuggestions || [
        'Check system health',
        'Get fleet statistics',
        'List hosts',
        'View recent updates'
      ],
      routing_metadata: {
        matched_category: 'unknown',
        confidence: 0,
        matched_keywords: [],
        endpoint_used: 'none',
        processing_time_ms: processingTime
      }
    };
  }

  /**
   * Extract hostname from query text
   */
  private extractHostname(query: string, availableHosts: string[]): string | null {
    const normalizedQuery = query.toLowerCase();
    
    // Look for exact matches first
    for (const host of availableHosts) {
      if (normalizedQuery.includes(host.toLowerCase())) {
        return host;
      }
    }
    
    // Look for partial matches
    for (const host of availableHosts) {
      const hostParts = host.toLowerCase().split(/[-._]/);
      for (const part of hostParts) {
        if (part.length > 2 && normalizedQuery.includes(part)) {
          return host;
        }
      }
    }
    
    return null;
  }

  /**
   * Get routing statistics for monitoring
   */
  getRoutingStats(): {
    total_rules: number;
    categories: string[];
    confidence_distribution: Record<string, number>;
  } {
    if (!this.routingConfig) {
      return { total_rules: 0, categories: [], confidence_distribution: {} };
    }

    const confidenceDistribution: Record<string, number> = {};
    for (const rule of this.routingConfig.rules) {
      const bucket = Math.floor(rule.confidence * 10) / 10;
      confidenceDistribution[bucket.toString()] = (confidenceDistribution[bucket.toString()] || 0) + 1;
    }

    return {
      total_rules: this.routingConfig.rules.length,
      categories: this.routingConfig.rules.map(r => r.category),
      confidence_distribution: confidenceDistribution
    };
  }
}

// Example usage
export async function exampleUsage(): Promise<void> {
  const openApiSpec = {
    // Your OpenAPI spec here
  };
  
  const interpreter = new SmartFleetPulseInterpreter('http://localhost:8000', openApiSpec);
  
  const testQueries = [
    'What is the health status?',
    'Show me statistics',
    'List hosts',
    'Get recent updates',
    'Show history for web-server-01'
  ];
  
  for (const query of testQueries) {
    const result = await interpreter.interpretQuery(query);
    console.log(`Query: "${query}"`);
    console.log(`Routed to: ${result.routing_metadata.matched_category}`);
    console.log(`Confidence: ${result.routing_metadata.confidence}`);
    console.log(`Processing time: ${result.routing_metadata.processing_time_ms}ms`);
    console.log('---');
  }
}

export default SmartFleetPulseInterpreter;
