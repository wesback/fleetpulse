/**
 * Test script for the automated query routing system
 * Demonstrates how to use the OpenAPI analyzer and enhanced interpreter
 */

import { OpenAPIAnalyzer } from './src/services/openapi-analyzer';
import { EnhancedFleetPulseQueryInterpreter } from './src/services/enhanced-query-interpreter';

// Mock FleetPulse OpenAPI spec based on your current API structure
const mockFleetPulseSpec = {
  openapi: '3.0.0',
  info: {
    title: 'FleetPulse API',
    version: '1.0.0',
    description: 'Fleet management and package update tracking system'
  },
  paths: {
    '/health': {
      get: {
        summary: 'Health check endpoint',
        description: 'Check the health status of the FleetPulse backend',
        tags: ['health', 'monitoring'],
        operationId: 'healthCheck',
        responses: {
          '200': {
            description: 'Service is healthy'
          }
        }
      }
    },
    '/statistics': {
      get: {
        summary: 'Get fleet statistics',
        description: 'Retrieve comprehensive statistics about the fleet including host counts, update metrics, and package information',
        tags: ['statistics', 'overview'],
        operationId: 'getStatistics',
        responses: {
          '200': {
            description: 'Statistics retrieved successfully'
          }
        }
      }
    },
    '/hosts': {
      get: {
        summary: 'List all hosts',
        description: 'Get a list of all hosts being monitored by FleetPulse',
        tags: ['hosts', 'fleet'],
        operationId: 'getHosts',
        responses: {
          '200': {
            description: 'Hosts retrieved successfully'
          }
        }
      }
    },
    '/hosts/{hostname}/history': {
      get: {
        summary: 'Get host update history',
        description: 'Retrieve the update history for a specific host',
        tags: ['hosts', 'history', 'updates'],
        operationId: 'getHostHistory',
        parameters: [
          {
            name: 'hostname',
            in: 'path',
            required: true,
            schema: { type: 'string' },
            description: 'The hostname to get history for'
          },
          {
            name: 'limit',
            in: 'query',
            schema: { type: 'integer', default: 10 },
            description: 'Maximum number of updates to return'
          }
        ],
        responses: {
          '200': {
            description: 'Host history retrieved successfully'
          }
        }
      }
    },
    '/reports/host-activity': {
      get: {
        summary: 'Generate host activity report',
        description: 'Create a comprehensive report of host activity and update patterns',
        tags: ['reports', 'analytics'],
        operationId: 'generateHostActivityReport',
        responses: {
          '200': {
            description: 'Report generated successfully'
          }
        }
      }
    },
    '/reports/package-updates': {
      get: {
        summary: 'Generate package update report',
        description: 'Create a report showing package update trends and statistics',
        tags: ['reports', 'packages', 'updates'],
        operationId: 'generatePackageUpdateReport',
        parameters: [
          {
            name: 'timeframe',
            in: 'query',
            schema: { type: 'string', enum: ['day', 'week', 'month'] },
            description: 'Timeframe for the report'
          }
        ],
        responses: {
          '200': {
            description: 'Package update report generated'
          }
        }
      }
    }
  }
};

async function testRoutingGeneration(): Promise<void> {
  console.log('🧪 Testing Automated Query Routing Generation\\n');

  // 1. Generate routing configuration from OpenAPI spec
  console.log('📊 Analyzing OpenAPI specification...');
  const analyzer = new OpenAPIAnalyzer(mockFleetPulseSpec);
  const routingConfig = analyzer.generateRoutingConfig();

  console.log(`✅ Generated ${routingConfig.rules.length} routing rules from ${routingConfig.metadata.totalEndpoints} endpoints\\n`);

  // 2. Display generated rules
  console.log('📋 Generated Routing Rules:');
  routingConfig.rules.forEach((rule, index) => {
    console.log(`\\n${index + 1}. Category: ${rule.category}`);
    console.log(`   Priority: ${rule.priority}`);
    console.log(`   Confidence: ${rule.confidence.toFixed(2)}`);
    console.log(`   Keywords: ${rule.keywords.join(', ')}`);
    console.log(`   Intent Patterns: ${rule.intentPatterns.join(', ')}`);
    if (rule.negativeKeywords) {
      console.log(`   Negative Keywords: ${rule.negativeKeywords.join(', ')}`);
    }
    console.log(`   Endpoints: ${rule.endpoints.map(e => `${e.method} ${e.path}`).join(', ')}`);
  });

  // 3. Generate TypeScript routing functions
  console.log('\\n🔧 Generating TypeScript routing functions...');
  const typeScriptCode = analyzer.generateTypeScriptRoutingFunctions(routingConfig);
  console.log('✅ TypeScript functions generated');
  console.log(`📝 Generated ${typeScriptCode.split('\\n').length} lines of TypeScript code`);

  // 4. Test enhanced interpreter
  console.log('\\n🤖 Testing Enhanced Query Interpreter...');
  const interpreter = new EnhancedFleetPulseQueryInterpreter('http://localhost:8000', mockFleetPulseSpec);

  // Test queries
  const testQueries = [
    'What is the health status?',
    'Show me fleet statistics',
    'List all hosts in the system',
    'Get recent package updates',
    'Show update history for web-server-01',
    'Generate a report about host activity',
    'How many total updates have there been?',
    'What packages were updated today?',
    'Is the system working properly?',
    'Give me an overview of the fleet'
  ];

  console.log('\\n🔍 Testing Query Routing:');
  for (const query of testQueries) {
    const routingResults = interpreter.testQueryRouting(query);
    const topMatch = routingResults.find(r => r.matches);
    
    console.log(`\\n"${query}"`);
    if (topMatch) {
      console.log(`   ✅ Routed to: ${topMatch.category} (confidence: ${topMatch.confidence.toFixed(2)})`);
      console.log(`   📝 Keywords: ${topMatch.matchedKeywords.join(', ') || 'none'}`);
    } else {
      console.log(`   ❌ No route found - would use fallback`);
    }
  }

  // 5. Show LLM prompt for further customization
  console.log('\\n📝 Generated LLM Prompt for further customization:');
  const llmPrompt = analyzer.generateRoutingPrompt(mockFleetPulseSpec);
  console.log('\\n' + '='.repeat(80));
  console.log(llmPrompt);
  console.log('='.repeat(80));

  console.log('\\n✨ Test completed successfully!');
}

async function showRoutingStrategies(): Promise<void> {
  console.log('\\n🎯 Query Routing Strategies for MCP Servers:\\n');

  console.log('1. **Keyword-Based Routing**');
  console.log('   - Simple string matching against predefined keywords');
  console.log('   - Fast but can miss context and intent');
  console.log('   - Example: "health" → health_status category\\n');

  console.log('2. **Intent Pattern Matching**');
  console.log('   - Uses regex patterns to match user intentions');
  console.log('   - More flexible than pure keyword matching');
  console.log('   - Example: "check * status" matches "check system status"\\n');

  console.log('3. **Contextual Exclusion**');
  console.log('   - Uses negative keywords to prevent false positives');
  console.log('   - Helps distinguish between similar categories');
  console.log('   - Example: "statistics" but not "host statistics"\\n');

  console.log('4. **Priority-Based Routing**');
  console.log('   - Routes to higher priority categories first');
  console.log('   - Specific patterns take precedence over general ones');
  console.log('   - Example: Package updates (90) > General statistics (80)\\n');

  console.log('5. **Confidence Scoring**');
  console.log('   - Each rule has a confidence score based on API quality');
  console.log('   - Well-documented endpoints get higher confidence');
  console.log('   - Helps with routing decisions and user feedback\\n');

  console.log('🔧 **Automation Benefits:**');
  console.log('   ✅ Consistent routing logic across endpoints');
  console.log('   ✅ Automatic updates when API changes');
  console.log('   ✅ Reduced manual coding for new endpoints');
  console.log('   ✅ Better coverage of edge cases');
  console.log('   ✅ Standardized intent recognition patterns\\n');
}

// Run the test if called directly
if (require.main === module) {
  Promise.all([
    testRoutingGeneration(),
    showRoutingStrategies()
  ]).catch(error => {
    console.error('❌ Test failed:', error);
    process.exit(1);
  });
}

export { testRoutingGeneration, showRoutingStrategies, mockFleetPulseSpec };
