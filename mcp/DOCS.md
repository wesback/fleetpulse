# FleetPulse MCP Server - Documentation Summary

## 📚 Documentation Structure

All documentation has been consolidated into a single comprehensive guide: **[README.md](README.md)**

## 🚀 Quick Reference

### What is this?
The FleetPulse MCP server features an **automated query routing system** that:
- Analyzes OpenAPI 3.0 specifications
- Auto-generates intelligent routing logic
- Classifies natural language queries using intent patterns
- Provides confidence scores and routing metadata

### Key Commands

```bash
# Generate routing from your API
npx ts-node generate-routing.ts http://localhost:8000/openapi.json

# Test the routing system
npx ts-node test-routing.ts

# Run the server
npm run dev

# Test a query
curl -X POST http://localhost:3001/mcp/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the health status?"}'
```

### Example Usage

```typescript
import { EnhancedFleetPulseQueryInterpreter } from './services/enhanced-query-interpreter';

const interpreter = new EnhancedFleetPulseQueryInterpreter(backendUrl, openApiSpec);
const result = await interpreter.interpretQuery("Show me fleet statistics");

console.log(result.routing_metadata);
// {
//   matched_category: "statistics_overview",
//   confidence: 0.95,
//   matched_keywords: ["statistics"],
//   processing_time_ms: 42
// }
```

## 📖 Full Documentation

For complete documentation including:
- Detailed setup instructions
- API reference
- Deployment guide
- Troubleshooting
- Development guide
- Testing instructions

**→ See [README.md](README.md)**

## 🎯 Key Benefits

- ✅ **Automated**: No more manual `if (query.includes('health'))` routing
- ✅ **Intelligent**: Intent-based classification, not just keywords
- ✅ **Maintainable**: Updates automatically when API changes
- ✅ **Observable**: Full routing metadata and confidence scores
- ✅ **Extensible**: Easy to add new categories and patterns

## 🔧 Files Generated

| File | Purpose |
|------|---------|
| `src/services/openapi-analyzer.ts` | Analyzes OpenAPI specs |
| `src/services/enhanced-query-interpreter.ts` | Auto-generated routing |
| `generate-routing.ts` | CLI tool for generation |
| `test-routing.ts` | Test and demo script |
| `smart-interpreter-example.ts` | Production-ready example |

This system transforms manual query routing into an intelligent, automated solution that scales with your API!
