import dotenv from 'dotenv';
import path from 'path';

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../.env') });

export interface Config {
  server: {
    port: number;
    host: string;
    requestTimeout: number;
    maxRequestSize: string;
  };
  model: {
    endpointUrl: string;
  };
  logging: {
    level: string;
    format: 'json' | 'simple';
  };
  cors: {
    origin: string | string[] | boolean;
    credentials: boolean;
  };
  security: {
    helmetEnabled: boolean;
  };
}

/**
 * Parse CORS origin configuration
 */
function parseCorsOrigin(origin: string): string | string[] | boolean {
  if (origin === '*') return true;
  if (origin === 'false') return false;
  if (origin.includes(',')) {
    return origin.split(',').map(o => o.trim());
  }
  return origin;
}

/**
 * Application configuration
 */
export const config: Config = {
  server: {
    port: parseInt(process.env.MCP_PORT || '8001', 10),
    host: process.env.MCP_HOST || '0.0.0.0',
    requestTimeout: parseInt(process.env.REQUEST_TIMEOUT || '30000', 10),
    maxRequestSize: process.env.MAX_REQUEST_SIZE || '10mb',
  },
  model: {
    endpointUrl: process.env.MODEL_ENDPOINT_URL || 'http://localhost:8000/api/v1/completions',
  },
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    format: (process.env.LOG_FORMAT as 'json' | 'simple') || 'json',
  },
  cors: {
    origin: parseCorsOrigin(process.env.CORS_ORIGIN || '*'),
    credentials: process.env.CORS_CREDENTIALS === 'true',
  },
  security: {
    helmetEnabled: process.env.HELMET_ENABLED !== 'false',
  },
};

/**
 * Validate configuration
 */
export function validateConfig(): void {
  const errors: string[] = [];

  if (!config.server.port || config.server.port < 1 || config.server.port > 65535) {
    errors.push('Invalid server port');
  }

  if (!config.model.endpointUrl) {
    errors.push('MODEL_ENDPOINT_URL is required');
  }

  try {
    new URL(config.model.endpointUrl);
  } catch {
    errors.push('MODEL_ENDPOINT_URL must be a valid URL');
  }

  if (!['debug', 'info', 'warn', 'error'].includes(config.logging.level)) {
    errors.push('Invalid log level');
  }

  if (errors.length > 0) {
    throw new Error(`Configuration validation failed: ${errors.join(', ')}`);
  }
}
