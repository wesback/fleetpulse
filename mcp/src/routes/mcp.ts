import express from 'express';
import { Request, Response } from 'express';
import { createProxyMiddleware, RequestHandler } from 'http-proxy-middleware';
import { v4 as uuidv4 } from 'uuid';
import { MCPContextSchema, MCPContextOpenAPISchema, MCPContext } from '../schemas';
import { logger, logRequest, logResponse, logError, logProxyRequest } from '../logger';
import { config } from '../config';
import { createEnhancedInterpreter, loadOpenApiSpec } from '../services/enhanced-query-interpreter';
import { FleetPulseQueryInterpreter } from '../services/query-interpreter';

/**
 * MCP Routes Handler
 */
export class MCPRoutes {
  private router: express.Router;
  private queryInterpreter: FleetPulseQueryInterpreter;

  constructor() {
    this.router = express.Router();
    // Initialize with basic interpreter first
    this.queryInterpreter = new FleetPulseQueryInterpreter(config.fleetpulse.apiUrl);
    this.setupRoutes();
    // Try to upgrade to enhanced interpreter asynchronously
    this.upgradeToEnhancedInterpreter();
  }

  /**
   * Upgrade to enhanced interpreter with OpenAPI spec
   */
  private async upgradeToEnhancedInterpreter(): Promise<void> {
    try {
      // Try to load FleetPulse OpenAPI spec for enhanced routing
      const fleetPulseApiUrl = `${config.fleetpulse.apiUrl}/openapi.json`;
      const openApiSpec = await loadOpenApiSpec(fleetPulseApiUrl);
      
      this.queryInterpreter = createEnhancedInterpreter(config.fleetpulse.apiUrl, openApiSpec);
      logger.info('Enhanced query interpreter initialized', { apiUrl: config.fleetpulse.apiUrl });
    } catch (error) {
      // Continue with basic interpreter if OpenAPI spec loading fails
      logger.warn('Failed to load OpenAPI spec, using basic interpreter', { error });
    }
  }

  /**
   * Get the Express router
   */
  public getRouter(): express.Router {
    return this.router;
  }

  /**
   * Setup all MCP routes
   */
  private setupRoutes(): void {
    // OpenAPI specification endpoint
    this.router.get('/openapi', this.getOpenAPISpec.bind(this));
    
    // Context submission endpoint
    this.router.post('/context', this.handleContext.bind(this));
    
    // FleetPulse query endpoint
    this.router.post('/query', this.handleFleetPulseQuery.bind(this));
    
    // Proxy endpoint
    this.router.post('/proxy', this.handleProxy.bind(this));
  }

  /**
   * GET /mcp/v1/openapi
   * Returns the OpenAPI 3.1 specification
   */
  private async getOpenAPISpec(_req: Request, res: Response): Promise<void> {
    const startTime = Date.now();
    
    try {
      logRequest('GET', '/mcp/v1/openapi');
      
      res.status(200).json(MCPContextOpenAPISchema);
      
      const responseTime = Date.now() - startTime;
      logResponse('GET', '/mcp/v1/openapi', 200, responseTime);
    } catch (error) {
      logError(error as Error, { endpoint: '/mcp/v1/openapi' });
      res.status(500).json({
        success: false,
        error: 'Internal server error'
      });
    }
  }

  /**
   * POST /mcp/v1/context
   * Receives and logs MCP context objects
   */
  private async handleContext(req: Request, res: Response): Promise<void> {
    const startTime = Date.now();
    const contextId = uuidv4();
    
    try {
      logRequest('POST', '/mcp/v1/context', { contextId });

      // Validate the request body against the schema
      const validationResult = MCPContextSchema.safeParse(req.body);
      
      if (!validationResult.success) {
        const errorDetails = validationResult.error.errors.map(err => ({
          path: err.path.join('.'),
          message: err.message,
          code: err.code
        }));

        logger.warn('Invalid MCP context received', { 
          contextId,
          errors: errorDetails 
        });

        res.status(400).json({
          success: false,
          error: 'Invalid request body',
          details: {
            contextId,
            validationErrors: errorDetails
          }
        });
        return;
      }

      const mcpContext: MCPContext = validationResult.data;

      // Check if this is a FleetPulse query and handle it intelligently
      if (mcpContext.context.type === 'fleetpulse_query' || 
          mcpContext.context.type === 'question' ||
          mcpContext.context.type === 'completion_request') {
        
        const queryText = this.extractQueryFromContext(mcpContext);
        if (queryText && this.isFleetPulseRelated(queryText)) {
          // Handle as FleetPulse query
          const result = await this.queryInterpreter.interpretQuery(queryText);
          
          res.status(200).json({
            success: true,
            message: 'FleetPulse query processed',
            contextId,
            query_result: result
          });

          const responseTime = Date.now() - startTime;
          logResponse('POST', '/mcp/v1/context', 200, responseTime);
          return;
        }
      }

      // Log the context for processing (original behavior)
      logger.info('MCP context received and validated', {
        contextId,
        contextType: mcpContext.context.type,
        hasMetadata: !!mcpContext.metadata,
        hasRequest: !!mcpContext.request,
        timestamp: new Date().toISOString()
      });

      // Log context data (be careful with sensitive information)
      logger.debug('MCP context data', {
        contextId,
        context: {
          type: mcpContext.context.type,
          dataKeys: typeof mcpContext.context.data === 'object' && mcpContext.context.data !== null
            ? Object.keys(mcpContext.context.data)
            : 'non-object-data'
        }
      });

      // Send success response
      res.status(200).json({
        success: true,
        message: 'Context received and processed',
        contextId
      });

      const responseTime = Date.now() - startTime;
      logResponse('POST', '/mcp/v1/context', 200, responseTime);

    } catch (error) {
      logError(error as Error, { 
        endpoint: '/mcp/v1/context',
        contextId 
      });
      
      res.status(500).json({
        success: false,
        error: 'Internal server error',
        details: { contextId }
      });
    }
  }

  /**
   * POST /mcp/v1/proxy
   * Proxies MCP context to the configured model endpoint
   */
  private async handleProxy(req: Request, res: Response): Promise<void> {
    const proxyId = uuidv4();
    
    try {
      logRequest('POST', '/mcp/v1/proxy', { proxyId });

      // Validate the request body
      const validationResult = MCPContextSchema.safeParse(req.body);
      
      if (!validationResult.success) {
        const errorDetails = validationResult.error.errors.map(err => ({
          path: err.path.join('.'),
          message: err.message,
          code: err.code
        }));

        res.status(400).json({
          success: false,
          error: 'Invalid request body',
          details: {
            proxyId,
            validationErrors: errorDetails
          }
        });
        return;
      }

      const mcpContext: MCPContext = validationResult.data;

      // Create proxy middleware for this request
      const proxyMiddleware = this.createProxyMiddleware(mcpContext, proxyId);
      
      // Use the proxy middleware
      proxyMiddleware(req, res, (err) => {
        if (err) {
          logError(err as Error, { 
            endpoint: '/mcp/v1/proxy',
            proxyId,
            targetUrl: config.model.endpointUrl
          });
          
          if (!res.headersSent) {
            res.status(502).json({
              success: false,
              error: 'Proxy error',
              details: { proxyId }
            });
          }
        }
      });

    } catch (error) {
      logError(error as Error, { 
        endpoint: '/mcp/v1/proxy',
        proxyId 
      });
      
      if (!res.headersSent) {
        res.status(500).json({
          success: false,
          error: 'Internal server error',
          details: { proxyId }
        });
      }
    }
  }

  /**
   * POST /mcp/v1/query
   * Dedicated endpoint for FleetPulse queries
   */
  private async handleFleetPulseQuery(req: Request, res: Response): Promise<void> {
    const startTime = Date.now();
    const queryId = uuidv4();
    
    try {
      logRequest('POST', '/mcp/v1/query', { queryId });

      const { query } = req.body;
      
      if (!query || typeof query !== 'string') {
        res.status(400).json({
          success: false,
          error: 'Missing or invalid query parameter',
          details: { queryId }
        });
        return;
      }

      // Process the FleetPulse query
      const result = await this.queryInterpreter.interpretQuery(query);
      
      res.status(200).json({
        success: true,
        message: 'FleetPulse query processed successfully',
        queryId,
        query: query,
        result
      });

      const responseTime = Date.now() - startTime;
      logResponse('POST', '/mcp/v1/query', 200, responseTime);

    } catch (error) {
      logError(error as Error, { 
        endpoint: '/mcp/v1/query',
        queryId 
      });
      
      res.status(500).json({
        success: false,
        error: 'Failed to process FleetPulse query',
        details: { queryId }
      });
    }
  }

  /**
   * Extract query text from MCP context
   */
  private extractQueryFromContext(context: MCPContext): string | null {
    const data = context.context.data;
    
    if (typeof data === 'string') {
      return data;
    }
    
    if (typeof data === 'object' && data !== null) {
      // Check common query fields
      const possibleFields = ['query', 'question', 'prompt', 'message', 'text', 'input'];
      for (const field of possibleFields) {
        if (field in data && typeof (data as any)[field] === 'string') {
          return (data as any)[field];
        }
      }
      
      // If it's a messages array (like ChatML format)
      if ('messages' in data && Array.isArray((data as any).messages)) {
        const lastMessage = (data as any).messages[(data as any).messages.length - 1];
        if (lastMessage && typeof lastMessage.content === 'string') {
          return lastMessage.content;
        }
      }
    }
    
    return null;
  }

  /**
   * Check if query is related to FleetPulse
   */
  private isFleetPulseRelated(query: string): boolean {
    const fleetPulseKeywords = [
      'fleetpulse', 'fleet', 'host', 'hosts', 'server', 'servers',
      'package', 'packages', 'update', 'updates', 'statistics',
      'stats', 'health', 'status', 'machine', 'machines', 'computer'
    ];
    
    const lowerQuery = query.toLowerCase();
    return fleetPulseKeywords.some(keyword => lowerQuery.includes(keyword));
  }

  /**
   * Create dynamic proxy middleware for the MCP context
   */
  private createProxyMiddleware(mcpContext: MCPContext, proxyId: string): RequestHandler {
    const targetUrl = new URL(config.model.endpointUrl);
    
    // Use request path if provided, otherwise use the base path
    if (mcpContext.request?.path) {
      targetUrl.pathname = mcpContext.request.path;
    }

    // Add query parameters if provided
    if (mcpContext.request?.query) {
      Object.entries(mcpContext.request.query).forEach(([key, value]) => {
        targetUrl.searchParams.set(key, value);
      });
    }

    logProxyRequest(
      targetUrl.toString(), 
      mcpContext.request?.method || 'POST',
      mcpContext.request?.headers
    );

    return createProxyMiddleware({
      target: targetUrl.origin,
      changeOrigin: true,
      pathRewrite: {
        '^/mcp/v1/proxy': targetUrl.pathname
      },
      timeout: config.server.requestTimeout,
      
      // Transform the request
      onProxyReq: (proxyReq, _req, _res) => {
        // Set method from MCP context
        if (mcpContext.request?.method) {
          proxyReq.method = mcpContext.request.method;
        }

        // Forward headers from MCP context
        if (mcpContext.request?.headers) {
          Object.entries(mcpContext.request.headers).forEach(([key, value]) => {
            proxyReq.setHeader(key, value);
          });
        }

        // Add tracing headers if available
        if (mcpContext.metadata?.traceId) {
          proxyReq.setHeader('X-Trace-Id', mcpContext.metadata.traceId);
        }
        if (mcpContext.metadata?.spanId) {
          proxyReq.setHeader('X-Span-Id', mcpContext.metadata.spanId);
        }

        // Add proxy identification
        proxyReq.setHeader('X-Proxy-Id', proxyId);
        proxyReq.setHeader('X-Forwarded-By', 'fleetpulse-mcp-server');

        // Handle request body transformation
        if (mcpContext.request?.body !== undefined) {
          let bodyData: string;
          
          if (typeof mcpContext.request.body === 'string') {
            bodyData = mcpContext.request.body;
          } else if (mcpContext.request.body === null) {
            bodyData = '';
          } else {
            bodyData = JSON.stringify(mcpContext.request.body);
            proxyReq.setHeader('Content-Type', 'application/json');
          }

          if (bodyData) {
            proxyReq.setHeader('Content-Length', Buffer.byteLength(bodyData));
            proxyReq.write(bodyData);
          }
        }

        proxyReq.end();
      },

      // Log successful proxy responses
      onProxyRes: (proxyRes, _req, _res) => {
        logger.info('Proxy response received', {
          proxyId,
          statusCode: proxyRes.statusCode,
          headers: Object.keys(proxyRes.headers || {}),
          contentType: proxyRes.headers?.['content-type']
        });
      },

      // Handle proxy errors
      onError: (err, _req, _res) => {
        logError(err, { 
          proxyId,
          targetUrl: targetUrl.toString(),
          event: 'proxy_error' 
        });
      }
    });
  }
}
