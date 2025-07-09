// Jest setup file
import 'jest';

// Set test environment variables
process.env.NODE_ENV = 'test';
process.env.MCP_PORT = '8002';
process.env.LOG_LEVEL = 'error';
process.env.MODEL_ENDPOINT_URL = 'http://localhost:8888/test-endpoint';

// Global test timeout
jest.setTimeout(10000);
