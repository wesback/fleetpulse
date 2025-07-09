/**
 * OpenAPI Analyzer for automatic query routing generation
 * Analyzes OpenAPI 3.0 specifications to extract routing patterns and generate query classification logic
 */

export interface OpenAPIEndpoint {
  path: string;
  method: string;
  operationId?: string;
  summary?: string;
  description?: string;
  tags?: string[];
  parameters?: Array<{
    name: string;
    in: string;
    required?: boolean;
    schema?: any;
    description?: string;
  }>;
  responses?: Record<string, any>;
}

export interface RoutingRule {
  category: string;
  priority: number;
  keywords: string[];
  intentPatterns: string[];
  negativeKeywords?: string[];
  endpoints: OpenAPIEndpoint[];
  confidence: number;
}

export interface RoutingConfig {
  rules: RoutingRule[];
  fallbackSuggestions: string[];
  metadata: {
    generatedAt: string;
    apiVersion?: string;
    totalEndpoints: number;
  };
}

export class OpenAPIAnalyzer {
  private spec: any;

  constructor(openApiSpec: any) {
    this.spec = openApiSpec;
  }

  /**
   * Generate routing configuration from OpenAPI spec
   */
  generateRoutingConfig(): RoutingConfig {
    const endpoints = this.extractEndpoints();
    const rules = this.generateRoutingRules(endpoints);
    
    return {
      rules: rules.sort((a, b) => b.priority - a.priority),
      fallbackSuggestions: this.generateFallbackSuggestions(rules),
      metadata: {
        generatedAt: new Date().toISOString(),
        apiVersion: this.spec.info?.version,
        totalEndpoints: endpoints.length
      }
    };
  }

  /**
   * Extract all endpoints from OpenAPI spec
   */
  private extractEndpoints(): OpenAPIEndpoint[] {
    const endpoints: OpenAPIEndpoint[] = [];
    
    if (!this.spec.paths) return endpoints;

    for (const [path, pathItem] of Object.entries(this.spec.paths as Record<string, any>)) {
      for (const [method, operation] of Object.entries(pathItem as Record<string, any>)) {
        if (['get', 'post', 'put', 'delete', 'patch'].includes(method.toLowerCase())) {
          endpoints.push({
            path,
            method: method.toUpperCase(),
            operationId: operation.operationId,
            summary: operation.summary,
            description: operation.description,
            tags: operation.tags,
            parameters: operation.parameters,
            responses: operation.responses
          });
        }
      }
    }

    return endpoints;
  }

  /**
   * Generate routing rules based on endpoint analysis
   */
  private generateRoutingRules(endpoints: OpenAPIEndpoint[]): RoutingRule[] {
    const rules: RoutingRule[] = [];
    
    // Group endpoints by common patterns
    const endpointGroups = this.groupEndpointsByPattern(endpoints);
    
    for (const [pattern, groupEndpoints] of Object.entries(endpointGroups)) {
      const rule = this.createRoutingRule(pattern, groupEndpoints);
      if (rule) {
        rules.push(rule);
      }
    }

    return rules;
  }

  /**
   * Group endpoints by semantic patterns
   */
  private groupEndpointsByPattern(endpoints: OpenAPIEndpoint[]): Record<string, OpenAPIEndpoint[]> {
    const groups: Record<string, OpenAPIEndpoint[]> = {};

    for (const endpoint of endpoints) {
      const patterns = this.identifyEndpointPatterns(endpoint);
      
      for (const pattern of patterns) {
        if (!groups[pattern]) {
          groups[pattern] = [];
        }
        groups[pattern].push(endpoint);
      }
    }

    return groups;
  }

  /**
   * Identify semantic patterns from an endpoint
   */
  private identifyEndpointPatterns(endpoint: OpenAPIEndpoint): string[] {
    const patterns: string[] = [];
    
    // Pattern based on tags
    if (endpoint.tags && endpoint.tags.length > 0) {
      patterns.push(...endpoint.tags.map(tag => tag.toLowerCase()));
    }

    // Pattern based on path segments
    const pathSegments = endpoint.path.split('/').filter(s => s && !s.startsWith('{'));
    patterns.push(...pathSegments.map(s => s.toLowerCase()));

    // Pattern based on operation type
    if (endpoint.method === 'GET') {
      if (endpoint.path.includes('/health')) patterns.push('health');
      if (endpoint.path.includes('/stats') || endpoint.path.includes('/statistics')) patterns.push('statistics');
      if (endpoint.path.includes('/history')) patterns.push('history');
      if (endpoint.path.includes('/reports')) patterns.push('reports');
    }

    // Pattern based on summary/description keywords
    const textContent = [endpoint.summary, endpoint.description].filter(Boolean).join(' ').toLowerCase();
    const commonPatterns = [
      'health', 'status', 'statistics', 'stats', 'hosts', 'packages', 
      'updates', 'history', 'reports', 'monitoring', 'metrics'
    ];
    
    for (const pattern of commonPatterns) {
      if (textContent.includes(pattern)) {
        patterns.push(pattern);
      }
    }

    return [...new Set(patterns)];
  }

  /**
   * Create a routing rule for a specific pattern
   */
  private createRoutingRule(pattern: string, endpoints: OpenAPIEndpoint[]): RoutingRule | null {
    if (endpoints.length === 0) return null;

    const config = this.getPatternConfig(pattern, endpoints);
    
    return {
      category: config.category,
      priority: config.priority,
      keywords: config.keywords,
      intentPatterns: config.intentPatterns,
      ...(config.negativeKeywords && { negativeKeywords: config.negativeKeywords }),
      endpoints,
      confidence: this.calculateConfidence(pattern, endpoints)
    };
  }

  /**
   * Get configuration for a specific pattern
   */
  private getPatternConfig(_pattern: string, _endpoints: OpenAPIEndpoint[]): {
    category: string;
    priority: number;
    keywords: string[];
    intentPatterns: string[];
    negativeKeywords?: string[];
  } {
    const configs: Record<string, any> = {
      health: {
        category: 'health_status',
        priority: 100,
        keywords: ['health', 'status', 'up', 'running', 'operational', 'working', 'alive'],
        intentPatterns: [
          'is * working',
          'check * status',
          '* health',
          'is * up',
          'system status'
        ]
      },
      statistics: {
        category: 'statistics_overview',
        priority: 80,
        keywords: ['statistics', 'stats', 'overview', 'summary', 'dashboard', 'metrics', 'total', 'count'],
        intentPatterns: [
          'get * statistics',
          'show * overview',
          'how many *',
          'total *',
          '* summary'
        ],
        negativeKeywords: ['specific', 'individual', 'particular']
      },
      hosts: {
        category: 'host_management',
        priority: 70,
        keywords: ['host', 'hosts', 'server', 'servers', 'machine', 'machines', 'computer', 'node', 'nodes'],
        intentPatterns: [
          'list * hosts',
          'show * servers',
          'get host *',
          'which hosts *',
          'host information'
        ]
      },
      packages: {
        category: 'package_management',
        priority: 60,
        keywords: ['package', 'packages', 'software', 'application', 'app', 'program', 'library'],
        intentPatterns: [
          'package *',
          'software *',
          'application *',
          'what packages *'
        ]
      },
      updates: {
        category: 'update_tracking',
        priority: 90,
        keywords: ['update', 'updates', 'upgrade', 'upgraded', 'install', 'installed', 'recent', 'latest'],
        intentPatterns: [
          'recent updates',
          'latest *',
          'what was updated',
          'package updates',
          'updates in *',
          'last * updates'
        ]
      },
      history: {
        category: 'historical_data',
        priority: 50,
        keywords: ['history', 'timeline', 'when', 'what happened', 'past', 'previous', 'before'],
        intentPatterns: [
          '* history',
          'what happened *',
          'when was *',
          'timeline of *'
        ]
      },
      reports: {
        category: 'reporting',
        priority: 40,
        keywords: ['report', 'reports', 'analysis', 'analytics', 'insights'],
        intentPatterns: [
          'generate report',
          'show report',
          'analysis of *',
          'insights about *'
        ]
      }
    };

    return configs[_pattern] || {
      category: _pattern,
      priority: 30,
      keywords: [_pattern],
      intentPatterns: [`* ${_pattern}`, `${_pattern} *`]
    };
  }

  /**
   * Calculate confidence score for a rule based on endpoint quality
   */
  private calculateConfidence(pattern: string, endpoints: OpenAPIEndpoint[]): number {
    let confidence = 0.5; // Base confidence

    // Higher confidence for well-documented endpoints
    const hasDescriptions = endpoints.some(e => e.description || e.summary);
    if (hasDescriptions) confidence += 0.2;

    // Higher confidence for tagged endpoints
    const hasTags = endpoints.some(e => e.tags && e.tags.length > 0);
    if (hasTags) confidence += 0.1;

    // Higher confidence for specific patterns
    const specificPatterns = ['health', 'statistics', 'hosts', 'updates'];
    if (specificPatterns.includes(pattern)) confidence += 0.2;

    return Math.min(confidence, 1.0);
  }

  /**
   * Generate fallback suggestions based on available rules
   */
  private generateFallbackSuggestions(rules: RoutingRule[]): string[] {
    const suggestions: string[] = [];
    
    for (const rule of rules.slice(0, 5)) { // Top 5 rules
      const endpoint = rule.endpoints[0];
      if (endpoint?.summary) {
        suggestions.push(endpoint.summary);
      } else if (rule.keywords.length > 0) {
        suggestions.push(`Check ${rule.keywords[0]}`);
      }
    }

    return suggestions;
  }

  /**
   * Generate TypeScript routing functions
   */
  generateTypeScriptRoutingFunctions(config: RoutingConfig): string {
    const functions: string[] = [];
    
    // Generate individual routing functions
    for (const rule of config.rules) {
      const functionCode = this.generateSingleRoutingFunction(rule);
      functions.push(functionCode);
    }

    // Generate main routing dispatcher
    const dispatcherCode = this.generateDispatcherFunction(config.rules);
    functions.push(dispatcherCode);

    return functions.join('\n\n');
  }

  /**
   * Generate a single routing function for a rule
   */
  private generateSingleRoutingFunction(rule: RoutingRule): string {
    const functionName = `is${rule.category.split('_').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join('')}Query`;
    
    const negativeChecks = rule.negativeKeywords 
      ? rule.negativeKeywords.map(k => `!query.includes('${k}')`).join(' && ')
      : '';

    return `
/**
 * Check if query matches ${rule.category} pattern
 * Generated from OpenAPI endpoints: ${rule.endpoints.map(e => `${e.method} ${e.path}`).join(', ')}
 * Confidence: ${rule.confidence.toFixed(2)}
 */
private ${functionName}(query: string): boolean {
  const keywords = [${rule.keywords.map(k => `'${k}'`).join(', ')}];
  const hasKeyword = keywords.some(k => query.includes(k));
  
  const intentPatterns = [${rule.intentPatterns.map(p => `/${p.replace(/\*/g, '\\\\w*')}/i`).join(', ')}];
  const matchesIntent = intentPatterns.some(pattern => pattern.test(query));
  
  ${negativeChecks ? `const hasNegativeKeyword = ${rule.negativeKeywords!.map(k => `query.includes('${k}')`).join(' || ')};` : ''}
  
  return (hasKeyword || matchesIntent)${negativeChecks ? ' && !hasNegativeKeyword' : ''};
}`.trim();
  }

  /**
   * Generate main dispatcher function
   */
  private generateDispatcherFunction(rules: RoutingRule[]): string {
    const checks = rules.map(rule => {
      const functionName = `is${rule.category.split('_').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join('')}Query`;
      return `    if (this.${functionName}(query)) return '${rule.category}';`;
    }).join('\n');

    return `
/**
 * Main query routing dispatcher
 * Auto-generated from OpenAPI specification
 */
private routeQuery(query: string): string | null {
  const normalizedQuery = query.toLowerCase().trim();
  
${checks}
  
  return null; // No matching route found
}`.trim();
  }

  /**
   * Generate LLM prompt for creating new routing rules
   */
  generateRoutingPrompt(_openApiSpec: any): string {
    const endpoints = this.extractEndpoints();
    
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
