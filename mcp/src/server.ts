import express, { Application, Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { config, validateConfig } from './config';
import { logger, logError, logRequest, logResponse } from './logger';
import { MCPRoutes } from './routes/mcp';

/**
 * MCP Server Application
 */
export class MCPServer {
  private app: Application;
  private mcpRoutes: MCPRoutes;

  constructor() {
    this.app = express();
    this.mcpRoutes = new MCPRoutes();
    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
  }

  /**
   * Setup middleware
   */
  private setupMiddleware(): void {
    // Security headers
    if (config.security.helmetEnabled) {
      this.app.use(helmet({
        contentSecurityPolicy: false, // Allow for development flexibility
        crossOriginEmbedderPolicy: false,
      }));
    }

    // CORS configuration
    this.app.use(cors({
      origin: config.cors.origin,
      credentials: config.cors.credentials,
      methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With', 'X-Trace-Id', 'X-Span-Id'],
    }));

    // Body parsing with size limits
    this.app.use(express.json({ 
      limit: config.server.maxRequestSize,
      strict: true
    }));
    this.app.use(express.urlencoded({ 
      extended: true,
      limit: config.server.maxRequestSize
    }));

    // Request timeout middleware
    this.app.use((req: Request, res: Response, next: NextFunction) => {
      res.setTimeout(config.server.requestTimeout, () => {
        logError(new Error('Request timeout'), {
          method: req.method,
          path: req.path,
          timeout: config.server.requestTimeout
        });
        
        if (!res.headersSent) {
          res.status(408).json({
            success: false,
            error: 'Request timeout'
          });
        }
      });
      next();
    });

    // Request logging middleware
    this.app.use((req: Request, res: Response, next: NextFunction) => {
      const startTime = Date.now();
      
      // Log the incoming request
      logRequest(req.method, req.path, {
        userAgent: req.get('User-Agent'),
        contentType: req.get('Content-Type'),
        contentLength: req.get('Content-Length')
      });

      // Override res.end to log response
      const originalEnd = res.end.bind(res);
      res.end = function(...args: any[]): any {
        const responseTime = Date.now() - startTime;
        logResponse(req.method, req.path, res.statusCode, responseTime);
        return originalEnd(...args);
      };

      next();
    });
  }

  /**
   * Setup application routes
   */
  private setupRoutes(): void {
    // Health check endpoint
    this.app.get('/health', (_req: Request, res: Response) => {
      res.status(200).json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        service: 'mcp-server'
      });
    });

    // API info endpoint
    this.app.get('/', (_req: Request, res: Response) => {
      res.status(200).json({
        name: 'FleetPulse MCP Server',
        version: '1.0.0',
        description: 'Model Context Protocol server for FleetPulse',
        endpoints: {
          health: '/health',
          openapi: '/mcp/v1/openapi',
          context: '/mcp/v1/context',
          proxy: '/mcp/v1/proxy'
        },
        timestamp: new Date().toISOString()
      });
    });

    // Mount MCP routes
    this.app.use('/mcp/v1', this.mcpRoutes.getRouter());

    // 404 handler
    this.app.use('*', (req: Request, res: Response) => {
      logger.warn('Route not found', {
        method: req.method,
        path: req.path,
        ip: req.ip
      });

      res.status(404).json({
        success: false,
        error: 'Route not found',
        message: `${req.method} ${req.path} is not a valid endpoint`
      });
    });
  }

  /**
   * Setup error handling middleware
   */
  private setupErrorHandling(): void {
    // Global error handler
    this.app.use((error: Error, req: Request, res: Response, _next: NextFunction) => {
      logError(error, {
        method: req.method,
        path: req.path,
        ip: req.ip,
        userAgent: req.get('User-Agent')
      });

      // Don't send error details in production
      const isDevelopment = process.env.NODE_ENV === 'development';
      
      if (!res.headersSent) {
        res.status(500).json({
          success: false,
          error: 'Internal server error',
          ...(isDevelopment && { 
            details: error.message,
            stack: error.stack 
          })
        });
      }
    });

    // Handle uncaught exceptions
    process.on('uncaughtException', (error: Error) => {
      logError(error, { event: 'uncaughtException' });
      process.exit(1);
    });

    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason: any, promise: Promise<any>) => {
      logError(new Error(`Unhandled Rejection: ${reason}`), { 
        event: 'unhandledRejection',
        promise: promise.toString()
      });
      process.exit(1);
    });

    // Graceful shutdown
    process.on('SIGTERM', () => {
      logger.info('SIGTERM received, shutting down gracefully');
      process.exit(0);
    });

    process.on('SIGINT', () => {
      logger.info('SIGINT received, shutting down gracefully');
      process.exit(0);
    });
  }

  /**
   * Start the server
   */
  public async start(): Promise<void> {
    try {
      // Validate configuration
      validateConfig();

      // Start the server
      this.app.listen(config.server.port, config.server.host, () => {
        logger.info('MCP Server started successfully', {
          port: config.server.port,
          host: config.server.host,
          modelEndpoint: config.model.endpointUrl,
          logLevel: config.logging.level,
          corsOrigin: config.cors.origin,
          helmetEnabled: config.security.helmetEnabled
        });

        logger.info('Available endpoints:', {
          health: `http://${config.server.host}:${config.server.port}/health`,
          openapi: `http://${config.server.host}:${config.server.port}/mcp/v1/openapi`,
          context: `http://${config.server.host}:${config.server.port}/mcp/v1/context`,
          proxy: `http://${config.server.host}:${config.server.port}/mcp/v1/proxy`
        });
      });

    } catch (error) {
      logError(error as Error, { event: 'server_start_failed' });
      process.exit(1);
    }
  }

  /**
   * Get the Express application instance
   */
  public getApp(): Application {
    return this.app;
  }
}

/**
 * Start the server if this file is run directly
 */
if (require.main === module) {
  const server = new MCPServer();
  server.start().catch((error) => {
    console.error('Failed to start server:', error);
    process.exit(1);
  });
}
