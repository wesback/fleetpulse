/**
 * CLI Tool for generating query routing logic from OpenAPI specifications
 * Run with: npx ts-node generate-routing.ts <openapi-spec-url-or-file>
 */

import * as fs from 'fs';
import * as path from 'path';
import { OpenAPIAnalyzer } from './src/services/openapi-analyzer';

interface GenerationOptions {
  input: string;
  output?: string;
  format: 'typescript' | 'json' | 'both';
  includePrompt?: boolean;
}

async function loadOpenApiSpec(input: string): Promise<any> {
  try {
    // Check if it's a URL
    if (input.startsWith('http://') || input.startsWith('https://')) {
      const response = await fetch(input);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    }
    
    // It's a file path
    const content = fs.readFileSync(input, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    console.error(`Failed to load OpenAPI spec from ${input}:`, error);
    process.exit(1);
  }
}

function writeGeneratedCode(
  config: any, 
  typeScriptCode: string, 
  options: GenerationOptions
): void {
  const outputDir = options.output || './generated';
  
  // Ensure output directory exists
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Write JSON config
  if (options.format === 'json' || options.format === 'both') {
    const configPath = path.join(outputDir, 'routing-config.json');
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    console.log(`✅ Generated routing config: ${configPath}`);
  }

  // Write TypeScript code
  if (options.format === 'typescript' || options.format === 'both') {
    const tsPath = path.join(outputDir, 'generated-routing.ts');
    const fullCode = `/**
 * Auto-generated query routing functions
 * Generated at: ${new Date().toISOString()}
 * Source: ${options.input}
 */

import { logger } from '../logger';

export interface RoutingMetadata {
  category: string;
  confidence: number;
  matchedKeywords: string[];
  endpoints: string[];
}

export class AutoGeneratedQueryRouter {
  /**
   * Route a query to the appropriate category
   */
  routeQuery(query: string): RoutingMetadata | null {
    const normalizedQuery = query.toLowerCase().trim();
    
    ${config.rules.map((rule: any) => {
      const functionName = `is${rule.category.split('_').map((s: string) => s.charAt(0).toUpperCase() + s.slice(1)).join('')}Query`;
      return `
    if (this.${functionName}(normalizedQuery)) {
      return {
        category: '${rule.category}',
        confidence: ${rule.confidence},
        matchedKeywords: [${rule.keywords.map((k: string) => `'${k}'`).join(', ')}].filter(k => normalizedQuery.includes(k)),
        endpoints: [${rule.endpoints.map((e: any) => `'${e.method} ${e.path}'`).join(', ')}]
      };
    }`;
    }).join('')}
    
    return null;
  }

${typeScriptCode}

  /**
   * Get all available categories
   */
  getAvailableCategories(): string[] {
    return [${config.rules.map((rule: any) => `'${rule.category}'`).join(', ')}];
  }

  /**
   * Test query against all routing rules
   */
  testAllRoutes(query: string): Array<{category: string; matches: boolean; confidence: number}> {
    const normalizedQuery = query.toLowerCase().trim();
    return [
      ${config.rules.map((rule: any) => {
        const functionName = `is${rule.category.split('_').map((s: string) => s.charAt(0).toUpperCase() + s.slice(1)).join('')}Query`;
        return `{ category: '${rule.category}', matches: this.${functionName}(normalizedQuery), confidence: ${rule.confidence} }`;
      }).join(',\\n      ')}
    ];
  }
}`;

    fs.writeFileSync(tsPath, fullCode);
    console.log(`✅ Generated TypeScript routing: ${tsPath}`);
  }

  // Write LLM prompt for further customization
  if (options.includePrompt) {
    const promptPath = path.join(outputDir, 'routing-generation-prompt.md');
    const analyzer = new OpenAPIAnalyzer(config.metadata.originalSpec);
    const prompt = analyzer.generateRoutingPrompt(config.metadata.originalSpec);
    fs.writeFileSync(promptPath, prompt);
    console.log(`✅ Generated LLM prompt: ${promptPath}`);
  }
}

function generateUsageExamples(config: any): string {
  return `
## Usage Examples

\`\`\`typescript
import { AutoGeneratedQueryRouter } from './generated/generated-routing';

const router = new AutoGeneratedQueryRouter();

// Route a query
const result = router.routeQuery("What's the health status?");
if (result) {
  console.log(\`Category: \${result.category}, Confidence: \${result.confidence}\`);
}

// Test all routes
const testResults = router.testAllRoutes("show me statistics");
console.log(testResults);
\`\`\`

## Generated Categories

${config.rules.map((rule: any) => `
### ${rule.category}
- **Keywords**: ${rule.keywords.join(', ')}
- **Confidence**: ${rule.confidence.toFixed(2)}
- **Endpoints**: ${rule.endpoints.map((e: any) => `${e.method} ${e.path}`).join(', ')}
- **Intent Patterns**: ${rule.intentPatterns.join(', ')}
${rule.negativeKeywords ? `- **Negative Keywords**: ${rule.negativeKeywords.join(', ')}` : ''}
`).join('')}

## Routing Configuration Metadata

- **Generated**: ${config.metadata.generatedAt}
- **API Version**: ${config.metadata.apiVersion || 'Unknown'}
- **Total Endpoints**: ${config.metadata.totalEndpoints}
- **Total Rules**: ${config.rules.length}
`;
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log(`
Usage: npx ts-node generate-routing.ts <openapi-spec> [options]

Arguments:
  <openapi-spec>     URL or file path to OpenAPI 3.0 specification

Options:
  --output, -o       Output directory (default: ./generated)
  --format, -f       Output format: typescript, json, both (default: both)
  --prompt, -p       Include LLM prompt for further customization
  --help, -h         Show this help

Examples:
  npx ts-node generate-routing.ts ./backend/openapi.json
  npx ts-node generate-routing.ts http://localhost:8000/openapi.json -o ./src/generated
  npx ts-node generate-routing.ts ./api-spec.json --format typescript --prompt
`);
    process.exit(0);
  }

  const options: GenerationOptions = {
    input: args[0],
    output: './generated',
    format: 'both',
    includePrompt: false
  };

  // Parse options
  for (let i = 1; i < args.length; i++) {
    switch (args[i]) {
      case '--output':
      case '-o':
        options.output = args[++i];
        break;
      case '--format':
      case '-f':
        options.format = args[++i] as 'typescript' | 'json' | 'both';
        break;
      case '--prompt':
      case '-p':
        options.includePrompt = true;
        break;
      case '--help':
      case '-h':
        console.log('Help text shown above');
        process.exit(0);
    }
  }

  console.log(`🔍 Loading OpenAPI spec from: ${options.input}`);
  const spec = await loadOpenApiSpec(options.input);
  
  console.log(`📊 Analyzing API specification...`);
  const analyzer = new OpenAPIAnalyzer(spec);
  const config = analyzer.generateRoutingConfig();
  
  // Add original spec to metadata for prompt generation
  (config.metadata as any).originalSpec = spec;
  
  console.log(`🎯 Generated ${config.rules.length} routing rules from ${config.metadata.totalEndpoints} endpoints`);
  
  const typeScriptCode = analyzer.generateTypeScriptRoutingFunctions(config);
  
  writeGeneratedCode(config, typeScriptCode, options);
  
  // Write usage examples
  const examplesPath = path.join(options.output || './generated', 'README.md');
  fs.writeFileSync(examplesPath, generateUsageExamples(config));
  console.log(`📖 Generated usage examples: ${examplesPath}`);
  
  console.log(`\\n✨ Generation complete! Files created in: ${options.output || './generated'}`);
  
  // Show summary
  console.log(`\\n📋 Summary:`);
  config.rules.forEach((rule: any) => {
    console.log(`  📁 ${rule.category}: ${rule.keywords.length} keywords, confidence ${rule.confidence.toFixed(2)}`);
  });
}

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Generation failed:', error);
    process.exit(1);
  });
}

export { main as generateRouting };
