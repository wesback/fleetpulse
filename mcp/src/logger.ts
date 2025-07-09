import winston from 'winston';
import { config } from './config';

/**
 * Create and configure the application logger
 */
export const logger = winston.createLogger({
  level: config.logging.level,
  format: config.logging.format === 'json' 
    ? winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      )
    : winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.simple()
      ),
  defaultMeta: { service: 'mcp-server' },
  transports: [
    new winston.transports.Console({
      format: config.logging.format === 'json'
        ? winston.format.json()
        : winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
    })
  ]
});

/**
 * Log request details for debugging
 */
export function logRequest(method: string, path: string, metadata?: any): void {
  logger.info('Incoming request', {
    method,
    path,
    metadata: metadata ? JSON.stringify(metadata) : undefined
  });
}

/**
 * Log response details
 */
export function logResponse(method: string, path: string, statusCode: number, responseTime?: number): void {
  logger.info('Response sent', {
    method,
    path,
    statusCode,
    responseTime: responseTime ? `${responseTime}ms` : undefined
  });
}

/**
 * Log proxy request details
 */
export function logProxyRequest(targetUrl: string, method: string, headers?: Record<string, string>): void {
  logger.info('Proxying request', {
    targetUrl,
    method,
    headers: headers ? Object.keys(headers) : undefined
  });
}

/**
 * Log errors with context
 */
export function logError(error: Error, context?: Record<string, any>): void {
  logger.error('Error occurred', {
    message: error.message,
    stack: error.stack,
    ...context
  });
}
