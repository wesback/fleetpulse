/**
 * OpenTelemetry configuration for FleetPulse frontend.
 * 
 * This module sets up comprehensive browser observability including:
 * - Automatic instrumentation for fetch/XHR requests and user interactions
 * - Custom spans for business logic and user flows
 * - Real User Monitoring (RUM) metrics
 * - Correlation with backend traces
 * - Performance tracking (Core Web Vitals)
 */

import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { Resource } from '@opentelemetry/resources';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { getWebAutoInstrumentations } from '@opentelemetry/auto-instrumentations-web';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { B3Propagator } from '@opentelemetry/propagator-b3';
import { JaegerPropagator } from '@opentelemetry/propagator-jaeger';
import { propagation, trace, context } from '@opentelemetry/api';

// Semantic conventions
const SEMRESATTRS_SERVICE_NAME = 'service.name';
const SEMRESATTRS_SERVICE_VERSION = 'service.version';
const SEMRESATTRS_DEPLOYMENT_ENVIRONMENT = 'deployment.environment';

let tracer = null;
let isInitialized = false;

/**
 * Get telemetry configuration from environment variables or defaults
 */
function getTelemetryConfig() {
  return {
    serviceName: process.env.REACT_APP_OTEL_SERVICE_NAME || 'fleetpulse-frontend',
    serviceVersion: process.env.REACT_APP_OTEL_SERVICE_VERSION || '1.0.0',
    environment: process.env.REACT_APP_OTEL_ENVIRONMENT || 'development',
    jaegerEndpoint: process.env.REACT_APP_OTEL_EXPORTER_JAEGER_ENDPOINT || 'http://localhost:14268/api/traces',
    otlpEndpoint: process.env.REACT_APP_OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318/v1/traces',
    enableTelemetry: (process.env.REACT_APP_OTEL_ENABLE_TELEMETRY || 'true').toLowerCase() === 'true',
    traceSampleRate: parseFloat(process.env.REACT_APP_OTEL_TRACE_SAMPLE_RATE || '1.0'),
    exporterType: process.env.REACT_APP_OTEL_EXPORTER_TYPE || 'jaeger', // jaeger, otlp, or console
    enableConsoleExporter: (process.env.REACT_APP_OTEL_ENABLE_CONSOLE_EXPORTER || 'false').toLowerCase() === 'true',
  };
}

/**
 * Create and configure the OpenTelemetry resource
 */
function setupResource() {
  const config = getTelemetryConfig();
  
  return new Resource({
    [SEMRESATTRS_SERVICE_NAME]: config.serviceName,
    [SEMRESATTRS_SERVICE_VERSION]: config.serviceVersion,
    [SEMRESATTRS_DEPLOYMENT_ENVIRONMENT]: config.environment,
    'service.instance.id': `${window.location.hostname}-${Date.now()}`,
    'service.namespace': 'fleetpulse',
    'telemetry.sdk.name': 'opentelemetry',
    'telemetry.sdk.language': 'javascript',
    'telemetry.sdk.version': '1.28.0',
  });
}

/**
 * Set up OpenTelemetry tracing with appropriate exporters
 */
function setupTracing() {
  const config = getTelemetryConfig();
  
  if (!config.enableTelemetry) {
    console.log('OpenTelemetry: Telemetry disabled via configuration');
    return;
  }

  // Create resource
  const resource = setupResource();
  
  // Set up tracer provider
  const provider = new WebTracerProvider({
    resource: resource,
    sampler: {
      shouldSample: () => ({ decision: Math.random() < config.traceSampleRate ? 1 : 0 })
    }
  });

  // Configure exporter based on type
  let exporter;
  if (config.exporterType === 'jaeger') {
    // For web browsers, use OTLP to send to OpenTelemetry Collector which forwards to Jaeger
    exporter = new OTLPTraceExporter({
      url: config.otlpEndpoint, // Collector endpoint that forwards to Jaeger
    });
  } else if (config.exporterType === 'otlp') {
    exporter = new OTLPTraceExporter({
      url: config.otlpEndpoint,
    });
  } else {
    // Console exporter for development
    exporter = {
      export: (spans, resultCallback) => {
        console.log('OpenTelemetry Spans:', spans);
        resultCallback({ code: 0 });
      },
      shutdown: () => Promise.resolve(),
    };
  }

  // Add span processor
  provider.addSpanProcessor(new BatchSpanProcessor(exporter));

  // Register the provider
  provider.register();

  // Set up propagators for correlation with backend
  propagation.setGlobalPropagator(new B3Propagator());

  // Get tracer
  tracer = trace.getTracer(config.serviceName, config.serviceVersion);

  console.log(`OpenTelemetry: Tracing configured with ${config.exporterType} exporter`);
}

/**
 * Set up automatic instrumentation for web APIs
 */
function setupAutoInstrumentation() {
  const config = getTelemetryConfig();
  
  if (!config.enableTelemetry) {
    return;
  }

  // Register auto-instrumentations
  registerInstrumentations({
    instrumentations: [
      getWebAutoInstrumentations({
        '@opentelemetry/instrumentation-fetch': {
          // Add custom attributes to fetch spans
          applyCustomAttributesOnSpan: (span, request, result) => {
            span.setAttributes({
              'http.request.body.size': request.body ? request.body.length : 0,
              'http.response.body.size': result.headers.get('content-length') || 0,
              'user_agent': navigator.userAgent,
            });
          },
          // Ignore telemetry requests to prevent infinite loops
          ignoreUrls: [
            /jaeger/,
            /otel/,
            /telemetry/,
          ],
        },
        '@opentelemetry/instrumentation-xml-http-request': {
          applyCustomAttributesOnSpan: (span, xhr) => {
            span.setAttributes({
              'user_agent': navigator.userAgent,
            });
          },
          ignoreUrls: [
            /jaeger/,
            /otel/,
            /telemetry/,
          ],
        },
        '@opentelemetry/instrumentation-user-interaction': {
          eventNames: ['click', 'submit', 'keydown'],
        },
      }),
    ],
  });

  console.log('OpenTelemetry: Auto-instrumentation configured');
}

/**
 * Track Core Web Vitals and performance metrics
 */
function setupPerformanceTracking() {
  const config = getTelemetryConfig();
  
  if (!config.enableTelemetry || !tracer) {
    return;
  }

  // Track page load performance
  window.addEventListener('load', () => {
    const span = tracer.startSpan('page_load');
    
    // Navigation timing
    const navigation = performance.getEntriesByType('navigation')[0];
    if (navigation) {
      span.setAttributes({
        'page.url': window.location.href,
        'page.title': document.title,
        'navigation.type': navigation.type,
        'timing.dom_content_loaded': navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        'timing.load_complete': navigation.loadEventEnd - navigation.loadEventStart,
        'timing.first_byte': navigation.responseStart - navigation.requestStart,
        'timing.dom_interactive': navigation.domInteractive - navigation.navigationStart,
      });
    }

    span.end();
  });

  // Track Core Web Vitals using Performance Observer if available
  if ('PerformanceObserver' in window) {
    // Largest Contentful Paint (LCP)
    try {
      const lcpObserver = new PerformanceObserver((entryList) => {
        const lcpEntry = entryList.getEntries().pop();
        if (lcpEntry) {
          const span = tracer.startSpan('core_web_vital.lcp');
          span.setAttributes({
            'metric.name': 'largest_contentful_paint',
            'metric.value': lcpEntry.startTime,
            'metric.unit': 'ms',
            'page.url': window.location.href,
          });
          span.end();
        }
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
    } catch (e) {
      console.warn('OpenTelemetry: LCP observation not supported');
    }

    // First Input Delay (FID)
    try {
      const fidObserver = new PerformanceObserver((entryList) => {
        entryList.getEntries().forEach((entry) => {
          const span = tracer.startSpan('core_web_vital.fid');
          span.setAttributes({
            'metric.name': 'first_input_delay',
            'metric.value': entry.processingStart - entry.startTime,
            'metric.unit': 'ms',
            'page.url': window.location.href,
          });
          span.end();
        });
      });
      fidObserver.observe({ entryTypes: ['first-input'] });
    } catch (e) {
      console.warn('OpenTelemetry: FID observation not supported');
    }

    // Cumulative Layout Shift (CLS)
    try {
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((entryList) => {
        entryList.getEntries().forEach((entry) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
          }
        });
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });

      // Report CLS on page unload
      window.addEventListener('beforeunload', () => {
        const span = tracer.startSpan('core_web_vital.cls');
        span.setAttributes({
          'metric.name': 'cumulative_layout_shift',
          'metric.value': clsValue,
          'metric.unit': 'score',
          'page.url': window.location.href,
        });
        span.end();
      });
    } catch (e) {
      console.warn('OpenTelemetry: CLS observation not supported');
    }
  }

  console.log('OpenTelemetry: Performance tracking configured');
}

/**
 * Initialize all OpenTelemetry components
 */
export function initializeTelemetry() {
  if (isInitialized) {
    console.warn('OpenTelemetry: Already initialized');
    return;
  }

  try {
    setupTracing();
    setupAutoInstrumentation();
    setupPerformanceTracking();
    isInitialized = true;
    console.log('OpenTelemetry: Initialization completed successfully');
  } catch (error) {
    console.error('OpenTelemetry: Failed to initialize:', error);
    // Don't fail application startup if telemetry fails
  }
}

/**
 * Get the configured tracer instance
 */
export function getTracer() {
  if (!tracer) {
    const config = getTelemetryConfig();
    tracer = trace.getTracer(config.serviceName, config.serviceVersion);
  }
  return tracer;
}

/**
 * Create a custom span with optional attributes
 */
export function createCustomSpan(name, attributes = {}) {
  const currentTracer = getTracer();
  if (!currentTracer) {
    return {
      setAttributes: () => {},
      addEvent: () => {},
      setStatus: () => {},
      end: () => {},
    };
  }

  const span = currentTracer.startSpan(name);
  
  // Add default attributes
  span.setAttributes({
    'page.url': window.location.href,
    'page.title': document.title,
    'user_agent': navigator.userAgent,
    ...attributes,
  });

  return span;
}

/**
 * Track user interactions and flows
 */
export function trackUserFlow(flowName, stepName, attributes = {}) {
  const span = createCustomSpan(`user_flow.${flowName}.${stepName}`, {
    'flow.name': flowName,
    'flow.step': stepName,
    ...attributes,
  });

  // Auto-end span after a reasonable timeout
  setTimeout(() => {
    span.end();
  }, 30000);

  return span;
}

/**
 * Track API calls with correlation
 */
export function trackApiCall(method, url, attributes = {}) {
  const span = createCustomSpan('api_call', {
    'http.method': method,
    'http.url': url,
    'component': 'frontend',
    ...attributes,
  });

  return span;
}

/**
 * Track component renders
 */
export function trackComponentRender(componentName, props = {}) {
  const span = createCustomSpan('component_render', {
    'component.name': componentName,
    'component.props': JSON.stringify(props),
  });

  // Components typically render quickly
  setTimeout(() => {
    span.end();
  }, 1000);

  return span;
}

/**
 * Track errors with context
 */
export function trackError(error, context = {}) {
  const span = createCustomSpan('error', {
    'error.type': error.name || 'Unknown',
    'error.message': error.message || 'Unknown error',
    'error.stack': error.stack || '',
    ...context,
  });

  span.setStatus({ code: 2, message: error.message }); // ERROR status
  span.end();
}

/**
 * Add baggage for context propagation
 */
export function addBaggage(key, value) {
  const currentContext = context.active();
  const updatedContext = context.setValue(currentContext, key, value);
  context.with(updatedContext, () => {
    // Context is now active with the baggage
  });
}

/**
 * Check if telemetry is enabled and initialized
 */
export function isTelemetryEnabled() {
  const config = getTelemetryConfig();
  return config.enableTelemetry && isInitialized;
}

/**
 * Get current telemetry configuration
 */
export function getTelemetryStatus() {
  const config = getTelemetryConfig();
  return {
    enabled: config.enableTelemetry,
    initialized: isInitialized,
    serviceName: config.serviceName,
    serviceVersion: config.serviceVersion,
    environment: config.environment,
    exporterType: config.exporterType,
  };
}