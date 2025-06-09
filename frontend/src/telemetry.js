/**
 * Telemetry stub module for FleetPulse frontend.
 * 
 * This module provides no-op stub functions for telemetry operations.
 * All telemetry functionality has been disabled for the frontend.
 */

// Stub span object that provides the expected interface
const createStubSpan = () => ({
  setAttributes: () => {},
  addEvent: () => {},
  setStatus: () => {},
  setAttribute: () => {},
  end: () => {},
  __enter__: () => {},
  __exit__: () => {},
});

/**
 * Initialize telemetry (no-op stub)
 */
export function initializeTelemetry() {
  console.log('Telemetry: Frontend telemetry disabled');
}

/**
 * Create custom span (stub)
 */
export function createCustomSpan(name, attributes = {}) {
  return createStubSpan();
}

/**
 * Track user interactions and flows (stub)
 */
export function trackUserFlow(flowName, stepName, attributes = {}) {
  return createStubSpan();
}

/**
 * Track API calls with correlation (stub)
 */
export function trackApiCall(method, url, attributes = {}) {
  return createStubSpan();
}

/**
 * Track component renders (stub)
 */
export function trackComponentRender(componentName, props = {}) {
  return createStubSpan();
}

/**
 * Track errors with context (stub)
 */
export function trackError(error, context = {}) {
  // No-op
}

/**
 * Add baggage for context propagation (stub)
 */
export function addBaggage(key, value) {
  // No-op
}

/**
 * Check if telemetry is enabled and initialized
 */
export function isTelemetryEnabled() {
  return false;
}

/**
 * Get current telemetry configuration
 */
export function getTelemetryStatus() {
  return {
    enabled: false,
    initialized: false,
    serviceName: 'fleetpulse-frontend',
    serviceVersion: '1.0.0',
    environment: 'development',
    exporterType: 'disabled',
  };
}