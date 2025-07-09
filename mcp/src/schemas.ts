import { z } from 'zod';

/**
 * MCP Context Schema - defines the structure of context objects
 * that can be sent to the MCP server
 */

// Base metadata schema
const MetadataSchema = z.object({
  timestamp: z.string().datetime().optional(),
  source: z.string().optional(),
  version: z.string().optional(),
  traceId: z.string().optional(),
  spanId: z.string().optional(),
}).strict();

// Headers schema for proxy requests
const HeadersSchema = z.record(z.string(), z.string());

// Request body schema - can be either JSON object or string
const RequestBodySchema = z.union([
  z.record(z.unknown()),
  z.string(),
  z.null()
]);

// HTTP method schema
const HttpMethodSchema = z.enum(['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']);

// MCP Context schema
export const MCPContextSchema = z.object({
  // Core context data
  context: z.object({
    type: z.string(),
    data: z.unknown(),
    metadata: MetadataSchema.optional(),
  }).strict(),
  
  // Request information for proxy functionality
  request: z.object({
    method: HttpMethodSchema.default('POST'),
    path: z.string().default('/'),
    headers: HeadersSchema.optional(),
    body: RequestBodySchema.optional(),
    query: z.record(z.string(), z.string()).optional(),
  }).strict().optional(),
  
  // Additional metadata
  metadata: MetadataSchema.optional(),
}).strict();

// Type exports
export type MCPContext = z.infer<typeof MCPContextSchema>;
export type Metadata = z.infer<typeof MetadataSchema>;
export type RequestBody = z.infer<typeof RequestBodySchema>;
export type HttpMethod = z.infer<typeof HttpMethodSchema>;

/**
 * OpenAPI 3.1 Schema for MCP Context
 * This will be returned by the /mcp/v1/openapi endpoint
 */
export const MCPContextOpenAPISchema = {
  openapi: '3.1.0',
  info: {
    title: 'Model Context Protocol (MCP) API',
    version: '1.0.0',
    description: 'API for handling Model Context Protocol interactions',
    contact: {
      name: 'FleetPulse Team',
      email: 'support@fleetpulse.com'
    }
  },
  servers: [
    {
      url: '/mcp/v1',
      description: 'MCP API v1'
    }
  ],
  paths: {
    '/context': {
      post: {
        summary: 'Submit MCP context',
        description: 'Receive and process an MCP context object. Can intelligently handle FleetPulse-related queries.',
        operationId: 'submitContext',
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                $ref: '#/components/schemas/MCPContext'
              }
            }
          }
        },
        responses: {
          '200': {
            description: 'Context processed successfully',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: {
                      type: 'boolean',
                      example: true
                    },
                    message: {
                      type: 'string',
                      example: 'Context received and processed'
                    },
                    contextId: {
                      type: 'string',
                      format: 'uuid',
                      example: '123e4567-e89b-12d3-a456-426614174000'
                    }
                  },
                  required: ['success', 'message']
                }
              }
            }
          },
          '400': {
            description: 'Invalid request body',
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/Error'
                }
              }
            }
          },
          '500': {
            description: 'Internal server error',
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/Error'
                }
              }
            }
          }
        }
      }
    },
    '/query': {
      post: {
        summary: 'Query FleetPulse information',
        description: 'Ask questions about your FleetPulse fleet and get intelligent responses',
        operationId: 'queryFleetPulse',
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                required: ['query'],
                properties: {
                  query: {
                    type: 'string',
                    description: 'Natural language question about FleetPulse',
                    example: 'How many hosts are in my fleet?'
                  },
                  context: {
                    type: 'object',
                    description: 'Additional context for the query',
                    additionalProperties: true
                  }
                }
              }
            }
          }
        },
        responses: {
          '200': {
            description: 'Query processed successfully',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: {
                      type: 'boolean',
                      example: true
                    },
                    message: {
                      type: 'string',
                      example: 'FleetPulse query processed successfully'
                    },
                    queryId: {
                      type: 'string',
                      format: 'uuid'
                    },
                    query: {
                      type: 'string',
                      description: 'The original query'
                    },
                    result: {
                      type: 'object',
                      properties: {
                        success: {
                          type: 'boolean'
                        },
                        data: {
                          type: 'object',
                          description: 'Query result data'
                        },
                        message: {
                          type: 'string',
                          description: 'Human-readable response'
                        },
                        context_type: {
                          type: 'string',
                          description: 'Type of information returned'
                        },
                        suggestions: {
                          type: 'array',
                          items: {
                            type: 'string'
                          },
                          description: 'Suggested follow-up queries'
                        }
                      }
                    }
                  },
                  required: ['success', 'message', 'queryId', 'query', 'result']
                }
              }
            }
          },
          '400': {
            description: 'Invalid query',
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/Error'
                }
              }
            }
          },
          '500': {
            description: 'Internal server error',
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/Error'
                }
              }
            }
          }
        }
      }
    },
    '/proxy': {
      post: {
        summary: 'Proxy MCP context to model endpoint',
        description: 'Forward MCP context to configured model endpoint with streaming support',
        operationId: 'proxyContext',
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                $ref: '#/components/schemas/MCPContext'
              }
            }
          }
        },
        responses: {
          '200': {
            description: 'Successful proxy response',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  description: 'Response from the model endpoint'
                }
              },
              'text/plain': {
                schema: {
                  type: 'string',
                  description: 'Text response from the model endpoint'
                }
              }
            }
          },
          '400': {
            description: 'Invalid request body',
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/Error'
                }
              }
            }
          },
          '502': {
            description: 'Bad gateway - error from model endpoint',
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/Error'
                }
              }
            }
          },
          '504': {
            description: 'Gateway timeout - model endpoint did not respond',
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/Error'
                }
              }
            }
          }
        }
      }
    },
    '/openapi': {
      get: {
        summary: 'Get OpenAPI specification',
        description: 'Returns the OpenAPI 3.1 specification for the MCP API',
        operationId: 'getOpenAPISpec',
        responses: {
          '200': {
            description: 'OpenAPI specification',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  description: 'OpenAPI 3.1 specification'
                }
              }
            }
          }
        }
      }
    }
  },
  components: {
    schemas: {
      MCPContext: {
        type: 'object',
        required: ['context'],
        properties: {
          context: {
            type: 'object',
            required: ['type', 'data'],
            properties: {
              type: {
                type: 'string',
                description: 'Type of the context data',
                example: 'completion_request'
              },
              data: {
                type: 'object',
                description: 'The actual context data',
                additionalProperties: true
              },
              metadata: {
                $ref: '#/components/schemas/Metadata'
              }
            }
          },
          request: {
            type: 'object',
            properties: {
              method: {
                type: 'string',
                enum: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'],
                default: 'POST',
                description: 'HTTP method for proxy request'
              },
              path: {
                type: 'string',
                default: '/',
                description: 'Path for proxy request'
              },
              headers: {
                type: 'object',
                additionalProperties: {
                  type: 'string'
                },
                description: 'Headers to forward in proxy request'
              },
              body: {
                oneOf: [
                  { type: 'object' },
                  { type: 'string' },
                  { type: 'null' }
                ],
                description: 'Request body for proxy request'
              },
              query: {
                type: 'object',
                additionalProperties: {
                  type: 'string'
                },
                description: 'Query parameters for proxy request'
              }
            }
          },
          metadata: {
            $ref: '#/components/schemas/Metadata'
          }
        }
      },
      Metadata: {
        type: 'object',
        properties: {
          timestamp: {
            type: 'string',
            format: 'date-time',
            description: 'ISO 8601 timestamp'
          },
          source: {
            type: 'string',
            description: 'Source of the context data'
          },
          version: {
            type: 'string',
            description: 'Version of the context format'
          },
          traceId: {
            type: 'string',
            description: 'Distributed tracing trace ID'
          },
          spanId: {
            type: 'string',
            description: 'Distributed tracing span ID'
          }
        }
      },
      Error: {
        type: 'object',
        required: ['success', 'error'],
        properties: {
          success: {
            type: 'boolean',
            example: false
          },
          error: {
            type: 'string',
            description: 'Error message'
          },
          details: {
            type: 'object',
            description: 'Additional error details',
            additionalProperties: true
          }
        }
      }
    }
  }
} as const;
