import request from 'supertest';
import { MCPServer } from '../src/server';

describe('MCP Server Integration Tests', () => {
  let server: MCPServer;
  let app: any;

  beforeAll(async () => {
    server = new MCPServer();
    app = server.getApp();
  });

  describe('Health Check', () => {
    it('should return healthy status', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toMatchObject({
        status: 'healthy',
        service: 'mcp-server'
      });
      expect(response.body.timestamp).toBeDefined();
    });
  });

  describe('Root Endpoint', () => {
    it('should return API information', async () => {
      const response = await request(app)
        .get('/')
        .expect(200);

      expect(response.body).toMatchObject({
        name: 'FleetPulse MCP Server',
        version: '1.0.0',
        description: 'Model Context Protocol server for FleetPulse'
      });
      expect(response.body.endpoints).toBeDefined();
    });
  });

  describe('OpenAPI Specification', () => {
    it('should return OpenAPI 3.1 spec', async () => {
      const response = await request(app)
        .get('/mcp/v1/openapi')
        .expect(200);

      expect(response.body.openapi).toBe('3.1.0');
      expect(response.body.info.title).toBe('Model Context Protocol (MCP) API');
      expect(response.body.paths).toBeDefined();
      expect(response.body.components.schemas.MCPContext).toBeDefined();
    });
  });

  describe('Context Endpoint', () => {
    it('should accept valid MCP context', async () => {
      const validContext = {
        context: {
          type: 'test_context',
          data: { message: 'Hello, MCP!' }
        }
      };

      const response = await request(app)
        .post('/mcp/v1/context')
        .send(validContext)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.message).toBe('Context received and processed');
      expect(response.body.contextId).toBeDefined();
    });

    it('should reject invalid MCP context', async () => {
      const invalidContext = {
        invalid: 'structure'
      };

      const response = await request(app)
        .post('/mcp/v1/context')
        .send(invalidContext)
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toBe('Invalid request body');
      expect(response.body.details.validationErrors).toBeDefined();
    });

    it('should handle context with metadata', async () => {
      const contextWithMetadata = {
        context: {
          type: 'completion_request',
          data: { prompt: 'Complete this sentence...' },
          metadata: {
            timestamp: new Date().toISOString(),
            source: 'test-client'
          }
        },
        metadata: {
          traceId: 'test-trace-123',
          spanId: 'test-span-456'
        }
      };

      const response = await request(app)
        .post('/mcp/v1/context')
        .send(contextWithMetadata)
        .expect(200);

      expect(response.body.success).toBe(true);
    });
  });

  describe('404 Handler', () => {
    it('should return 404 for unknown routes', async () => {
      const response = await request(app)
        .get('/unknown/route')
        .expect(404);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toBe('Route not found');
    });
  });

  describe('Error Handling', () => {
    it('should handle malformed JSON', async () => {
      const response = await request(app)
        .post('/mcp/v1/context')
        .set('Content-Type', 'application/json')
        .send('{ invalid json }');

      // Express/body-parser automatically handles malformed JSON
      // The status can be either 400 (bad request) or 500 (server error)
      expect([400, 500]).toContain(response.status);
    });
  });
});
