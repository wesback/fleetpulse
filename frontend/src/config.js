/**
 * Frontend configuration
 * Reads runtime configuration from window.FLEETPULSE_CONFIG
 * which is injected at container startup
 */

const getConfig = () => {
  // Default configuration
  const defaultConfig = {
    API_BASE_URL: '/api'
  };

  // Merge with runtime config if available
  if (window.FLEETPULSE_CONFIG) {
    return {
      ...defaultConfig,
      ...window.FLEETPULSE_CONFIG
    };
  }

  return defaultConfig;
};

export const config = getConfig();
export default config;
