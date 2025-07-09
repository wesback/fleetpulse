/**
 * Enhanced Query Interpreter with auto-generated routing logic
 * This class extends the base interpreter with OpenAPI-generated routing functions
 */

import { FleetPulseQueryInterpreter, QueryResult } from './query-interpreter';
import { OpenAPIAnalyzer, RoutingConfig, RoutingRule } from './openapi-analyzer';
import { logger } from '../logger';

export interface EnhancedQueryResult extends QueryResult {
  routing_metadata?: {
    matched_category: string;
    confidence: number;
    matched_keywords: string[];
    suggested_endpoints: string[];
  };
}

export class EnhancedFleetPulseQueryInterpreter extends FleetPulseQueryInterpreter {
  private routingConfig: RoutingConfig | null = null;
  private generatedFunctions: Map<string, (query: string) => boolean> = new Map();

  constructor(backendUrl?: string, openApiSpec?: any) {
    super(backendUrl);
    
    if (openApiSpec) {
      this.initializeRouting(openApiSpec);
    }
  }

  /**
   * Initialize routing from OpenAPI specification
   */
  private initializeRouting(openApiSpec: any): void {
    try {
      const analyzer = new OpenAPIAnalyzer(openApiSpec);
      this.routingConfig = analyzer.generateRoutingConfig();
      this.generateRuntimeFunctions();
      
      logger.info('Enhanced routing initialized', {
        rules_count: this.routingConfig.rules.length,
        total_endpoints: this.routingConfig.metadata.totalEndpoints
      });
    } catch (error) {
      logger.error('Failed to initialize enhanced routing', { error });
    }
  }

  /**
   * Generate runtime routing functions from configuration
   */
  private generateRuntimeFunctions(): void {
    if (!this.routingConfig) return;

    for (const rule of this.routingConfig.rules) {
      const functionName = this.getRuleFunctionName(rule);
      const routingFunction = this.createRuntimeRoutingFunction(rule);
      this.generatedFunctions.set(functionName, routingFunction);
    }
  }

  /**
   * Create a runtime routing function for a rule
   */
  private createRuntimeRoutingFunction(rule: RoutingRule): (query: string) => boolean {
    return (query: string): boolean => {
      const normalizedQuery = query.toLowerCase().trim();
      
      // Check keywords
      const hasKeyword = rule.keywords.some(keyword => normalizedQuery.includes(keyword));
      
      // Check intent patterns
      const intentRegexes = rule.intentPatterns.map(pattern => 
        new RegExp(pattern.replace(/\*/g, '\\w*'), 'i')
      );
      const matchesIntent = intentRegexes.some(regex => regex.test(normalizedQuery));
      
      // Check negative keywords
      let hasNegativeKeyword = false;
      if (rule.negativeKeywords) {
        hasNegativeKeyword = rule.negativeKeywords.some(keyword => 
          normalizedQuery.includes(keyword)
        );
      }
      
      return (hasKeyword || matchesIntent) && !hasNegativeKeyword;
    };
  }

  /**
   * Enhanced query interpretation with auto-generated routing
   */
  async interpretQuery(query: string): Promise<EnhancedQueryResult> {
    const normalizedQuery = query.toLowerCase().trim();
    
    // Try enhanced routing first
    if (this.routingConfig) {
      const routingResult = this.routeQueryWithMetadata(normalizedQuery);
      
      if (routingResult) {
        try {
          const result = await this.handleCategorizedQuery(
            normalizedQuery, 
            routingResult.category, 
            routingResult.rule
          );
          
          // Add routing metadata to result
          result.routing_metadata = {
            matched_category: routingResult.category,
            confidence: routingResult.rule.confidence,
            matched_keywords: routingResult.matchedKeywords,
            suggested_endpoints: routingResult.rule.endpoints.map(e => `${e.method} ${e.path}`)
          };
          
          return result;
        } catch (error) {
          logger.error('Enhanced routing handler failed, falling back', { 
            category: routingResult.category, 
            error 
          });
        }
      }
    }
    
    // Fallback to original interpretation
    return await super.interpretQuery(query);
  }

  /**
   * Route query with detailed metadata
   */
  private routeQueryWithMetadata(query: string): {
    category: string;
    rule: RoutingRule;
    matchedKeywords: string[];
  } | null {
    if (!this.routingConfig) return null;

    for (const rule of this.routingConfig.rules) {
      const functionName = this.getRuleFunctionName(rule);
      const routingFunction = this.generatedFunctions.get(functionName);
      
      if (routingFunction && routingFunction(query)) {
        const matchedKeywords = rule.keywords.filter(keyword => 
          query.includes(keyword)
        );
        
        return {
          category: rule.category,
          rule,
          matchedKeywords
        };
      }
    }

    return null;
  }

  /**
   * Handle categorized query based on routing result
   */
  private async handleCategorizedQuery(
    query: string, 
    category: string, 
    _rule: RoutingRule
  ): Promise<EnhancedQueryResult> {
    
    try {
      let result: QueryResult;
      
      // Call parent class methods through interpretQuery to avoid access issues
      switch (category) {
        case 'health_status':
          // Create a health-specific query that will be routed by parent class
          result = await super.interpretQuery('health status check');
          break;
        case 'statistics_overview':
          result = await super.interpretQuery('show statistics overview');
          break;
        case 'host_management':
          result = await super.interpretQuery('list hosts');
          break;
        case 'package_management':
          result = await super.interpretQuery('show packages');
          break;
        case 'update_tracking':
          result = await super.interpretQuery('show recent updates');
          break;
        case 'historical_data':
          result = await super.interpretQuery('show history');
          break;
        case 'reporting':
          result = await this.handleReportQuery(query);
          break;
        default:
          result = await super.interpretQuery(query);
      }
      
      return result as EnhancedQueryResult;
    } catch (error) {
      logger.error('Category handler failed', { category, error });
      throw error;
    }
  }

  /**
   * Handle report-related queries
   */
  private async handleReportQuery(_query: string): Promise<QueryResult> {
    // This would be implemented based on your reporting endpoints
    return {
      success: true,
      message: 'Report functionality is available. You can request various types of reports about your fleet.',
      context_type: 'reporting',
      suggestions: [
        'Generate host activity report',
        'Create package update summary',
        'View security update report'
      ]
    };
  }

  /**
   * Get function name for a routing rule
   */
  private getRuleFunctionName(rule: RoutingRule): string {
    return rule.category.split('_')
      .map(part => part.charAt(0).toUpperCase() + part.slice(1))
      .join('');
  }

  /**
   * Get routing configuration for inspection
   */
  getRoutingConfig(): RoutingConfig | null {
    return this.routingConfig;
  }

  /**
   * Get available categories
   */
  getAvailableCategories(): string[] {
    return this.routingConfig?.rules.map(rule => rule.category) || [];
  }

  /**
   * Test query against all routing rules (for debugging)
   */
  testQueryRouting(query: string): Array<{
    category: string;
    matches: boolean;
    confidence: number;
    matchedKeywords: string[];
  }> {
    if (!this.routingConfig) return [];

    const results: Array<{
      category: string;
      matches: boolean;
      confidence: number;
      matchedKeywords: string[];
    }> = [];

    for (const rule of this.routingConfig.rules) {
      const functionName = this.getRuleFunctionName(rule);
      const routingFunction = this.generatedFunctions.get(functionName);
      
      const matches = routingFunction ? routingFunction(query) : false;
      const matchedKeywords = rule.keywords.filter(keyword => 
        query.toLowerCase().includes(keyword)
      );
      
      results.push({
        category: rule.category,
        matches,
        confidence: rule.confidence,
        matchedKeywords
      });
    }

    return results.sort((a, b) => {
      if (a.matches && !b.matches) return -1;
      if (!a.matches && b.matches) return 1;
      return b.confidence - a.confidence;
    });
  }

  /**
   * Generate LLM prompt for creating new routing rules
   */
  generateRoutingPrompt(openApiSpec: any): string {
    const analyzer = new OpenAPIAnalyzer(openApiSpec);
    const endpoints = analyzer['extractEndpoints'](); // Access private method for prompt generation
    
    const endpointDescriptions = endpoints.map(endpoint => {
      return `${endpoint.method} ${endpoint.path}: ${endpoint.summary || endpoint.description || 'No description'}${
        endpoint.tags ? ` [Tags: ${endpoint.tags.join(', ')}]` : ''
      }`;
    }).join('\\n');

    return `
# Query Routing Generation Prompt

You are an expert at analyzing REST API specifications and generating natural language query routing logic.

## API Endpoints
${endpointDescriptions}

## Task
Generate TypeScript routing functions that can classify natural language queries to the appropriate API endpoints.

For each logical group of endpoints, create:

1. **Category Name**: A clear category identifier (e.g., 'health_status', 'host_management')
2. **Keywords**: Array of words that indicate this category
3. **Intent Patterns**: Regex-friendly patterns that match user intentions
4. **Priority**: Number indicating routing priority (1-100, higher = more specific)
5. **Negative Keywords**: Words that should exclude this category

## Example Output Format:
\`\`\`typescript
{
  category: 'health_status',
  priority: 100,
  keywords: ['health', 'status', 'up', 'running'],
  intentPatterns: ['check * status', 'is * working', '* health'],
  negativeKeywords: ['host', 'specific'],
  confidence: 0.9
}
\`\`\`

## Guidelines:
- Prioritize specific over general patterns
- Include synonyms and common variations
- Consider user intent, not just keywords
- Handle edge cases with negative keywords
- Ensure patterns don't overlap inappropriately

Generate routing rules for the provided API endpoints.
`.trim();
  }
}

// Export factory function for easy integration
export function createEnhancedInterpreter(
  backendUrl?: string, 
  openApiSpec?: any
): EnhancedFleetPulseQueryInterpreter {
  return new EnhancedFleetPulseQueryInterpreter(backendUrl, openApiSpec);
}

// Export OpenAPI spec loader utility
export async function loadOpenApiSpec(specUrl: string): Promise<any> {
  try {
    const response = await fetch(specUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch OpenAPI spec: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    logger.error('Failed to load OpenAPI specification', { specUrl, error });
    throw error;
  }
}
