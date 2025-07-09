import { MCPContextSchema } from '../src/schemas';

describe('MCP Schema Validation', () => {
  describe('Valid contexts', () => {
    it('should validate minimal context', () => {
      const context = {
        context: {
          type: 'test',
          data: { test: 'data' }
        }
      };

      const result = MCPContextSchema.safeParse(context);
      expect(result.success).toBe(true);
    });

    it('should validate context with metadata', () => {
      const context = {
        context: {
          type: 'completion',
          data: { prompt: 'Hello world' },
          metadata: {
            timestamp: '2024-01-01T00:00:00Z',
            source: 'test-client',
            traceId: 'trace-123'
          }
        },
        metadata: {
          timestamp: '2024-01-01T00:00:00Z',
          version: '1.0.0'
        }
      };

      const result = MCPContextSchema.safeParse(context);
      expect(result.success).toBe(true);
    });

    it('should validate context with request info', () => {
      const context = {
        context: {
          type: 'proxy_request',
          data: { model: 'gpt-4' }
        },
        request: {
          method: 'POST' as const,
          path: '/v1/completions',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token'
          },
          body: { prompt: 'Test prompt' },
          query: { temperature: '0.7' }
        }
      };

      const result = MCPContextSchema.safeParse(context);
      expect(result.success).toBe(true);
    });
  });

  describe('Invalid contexts', () => {
    it('should reject context without required fields', () => {
      const context = {
        invalid: 'structure'
      };

      const result = MCPContextSchema.safeParse(context);
      expect(result.success).toBe(false);
      expect(result.error?.errors).toContainEqual(
        expect.objectContaining({
          path: ['context'],
          code: 'invalid_type'
        })
      );
    });

    it('should reject context with invalid HTTP method', () => {
      const context = {
        context: {
          type: 'test',
          data: {}
        },
        request: {
          method: 'INVALID_METHOD',
          path: '/test'
        }
      };

      const result = MCPContextSchema.safeParse(context);
      expect(result.success).toBe(false);
    });

    it('should reject context with extra properties', () => {
      const context = {
        context: {
          type: 'test',
          data: {},
          extraProperty: 'not allowed'
        }
      };

      const result = MCPContextSchema.safeParse(context);
      expect(result.success).toBe(false);
    });
  });
});
