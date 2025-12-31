/**
 * Environment-Specific Configuration
 *
 * Defines configuration for different deployment environments.
 */

export const ENVIRONMENTS = {
  /**
   * Local Development
   */
  local: {
    name: 'local',
    baseUrl: 'http://localhost:8000',
    wsUrl: 'ws://localhost:8000',

    // Relaxed thresholds for local dev
    thresholds: {
      http_req_duration: ['p(95)<2000'],
      http_req_failed: ['rate<0.10']
    },

    // Test data
    testUsers: {
      admin: { email: 'admin@test.com', password: 'TestPassword123!' },
      faculty: { email: 'faculty@test.com', password: 'TestPassword123!' },
      resident: { email: 'resident@test.com', password: 'TestPassword123!' }
    },

    // Features
    features: {
      authentication: true,
      rateLimit: true,
      cache: true,
      realtime: false
    },

    // Load settings
    defaultVUs: 5,
    maxVUs: 20,
    duration: '1m'
  },

  /**
   * Docker Compose Environment
   */
  docker: {
    name: 'docker',
    baseUrl: 'http://backend:8000',
    wsUrl: 'ws://backend:8000',

    // Standard thresholds
    thresholds: {
      http_req_duration: ['p(95)<1000'],
      http_req_failed: ['rate<0.05']
    },

    testUsers: {
      admin: { email: 'admin@test.com', password: 'TestPassword123!' },
      faculty: { email: 'faculty@test.com', password: 'TestPassword123!' },
      resident: { email: 'resident@test.com', password: 'TestPassword123!' }
    },

    features: {
      authentication: true,
      rateLimit: true,
      cache: true,
      realtime: true
    },

    defaultVUs: 10,
    maxVUs: 50,
    duration: '5m'
  },

  /**
   * CI/CD Environment
   */
  ci: {
    name: 'ci',
    baseUrl: process.env.CI_BASE_URL || 'http://localhost:8000',
    wsUrl: process.env.CI_WS_URL || 'ws://localhost:8000',

    // Strict thresholds for CI
    thresholds: {
      http_req_duration: ['p(95)<800'],
      http_req_failed: ['rate<0.02']
    },

    testUsers: {
      admin: {
        email: process.env.CI_ADMIN_EMAIL || 'admin@test.com',
        password: process.env.CI_ADMIN_PASSWORD || 'TestPassword123!'
      }
    },

    features: {
      authentication: true,
      rateLimit: true,
      cache: true,
      realtime: false
    },

    // Conservative CI settings
    defaultVUs: 5,
    maxVUs: 20,
    duration: '2m'
  },

  /**
   * Staging Environment
   */
  staging: {
    name: 'staging',
    baseUrl: 'https://staging-api.scheduler.example.com',
    wsUrl: 'wss://staging-api.scheduler.example.com',

    // Production-like thresholds
    thresholds: {
      http_req_duration: ['p(95)<500'],
      http_req_failed: ['rate<0.01']
    },

    testUsers: {
      admin: {
        email: process.env.STAGING_ADMIN_EMAIL,
        password: process.env.STAGING_ADMIN_PASSWORD
      },
      faculty: {
        email: process.env.STAGING_FACULTY_EMAIL,
        password: process.env.STAGING_FACULTY_PASSWORD
      }
    },

    features: {
      authentication: true,
      rateLimit: true,
      cache: true,
      realtime: true,
      monitoring: true
    },

    defaultVUs: 20,
    maxVUs: 100,
    duration: '10m',

    // Security
    tls: {
      verify: true,
      minVersion: 'TLS1.2'
    }
  },

  /**
   * Production Environment (Read-Only Tests)
   */
  production: {
    name: 'production',
    baseUrl: 'https://api.scheduler.example.com',
    wsUrl: 'wss://api.scheduler.example.com',

    // Strict production thresholds
    thresholds: {
      http_req_duration: ['p(95)<300'],
      http_req_failed: ['rate<0.001']
    },

    // Read-only test user
    testUsers: {
      readonly: {
        email: process.env.PROD_READONLY_EMAIL,
        password: process.env.PROD_READONLY_PASSWORD
      }
    },

    features: {
      authentication: true,
      rateLimit: true,
      cache: true,
      realtime: true,
      monitoring: true,
      readonly: true  // Only read operations allowed
    },

    // Conservative production load
    defaultVUs: 10,
    maxVUs: 50,
    duration: '5m',

    // Security
    tls: {
      verify: true,
      minVersion: 'TLS1.3'
    },

    // Rate limits
    rateLimit: {
      maxRequestsPerSecond: 10,
      burstSize: 20
    }
  }
};

/**
 * Get environment configuration
 */
export function getEnvironment(envName) {
  const env = envName || __ENV.ENVIRONMENT || 'local';
  const config = ENVIRONMENTS[env];

  if (!config) {
    console.warn(`Unknown environment: ${env}, using 'local'`);
    return ENVIRONMENTS.local;
  }

  return config;
}

/**
 * Get current environment name
 */
export function getCurrentEnvironment() {
  return __ENV.ENVIRONMENT || 'local';
}

/**
 * Check if feature is enabled
 */
export function isFeatureEnabled(feature) {
  const env = getEnvironment();
  return env.features && env.features[feature] === true;
}

/**
 * Get base URL for current environment
 */
export function getBaseUrl() {
  const env = getEnvironment();
  return __ENV.BASE_URL || env.baseUrl;
}

/**
 * Get WebSocket URL for current environment
 */
export function getWsUrl() {
  const env = getEnvironment();
  return __ENV.WS_URL || env.wsUrl;
}

/**
 * Get test user for current environment
 */
export function getTestUser(role = 'admin') {
  const env = getEnvironment();
  return env.testUsers[role];
}

/**
 * Get default VU count
 */
export function getDefaultVUs() {
  const env = getEnvironment();
  return parseInt(__ENV.VUS) || env.defaultVUs || 1;
}

/**
 * Get max VU count
 */
export function getMaxVUs() {
  const env = getEnvironment();
  return parseInt(__ENV.MAX_VUS) || env.maxVUs || 10;
}

/**
 * Get test duration
 */
export function getDuration() {
  const env = getEnvironment();
  return __ENV.DURATION || env.duration || '1m';
}

/**
 * Check if running in production
 */
export function isProduction() {
  return getCurrentEnvironment() === 'production';
}

/**
 * Check if running in CI
 */
export function isCI() {
  return getCurrentEnvironment() === 'ci' || __ENV.CI === 'true';
}

/**
 * Get TLS configuration
 */
export function getTlsConfig() {
  const env = getEnvironment();
  return env.tls || {};
}

/**
 * Get rate limit configuration
 */
export function getRateLimitConfig() {
  const env = getEnvironment();
  return env.rateLimit || {};
}

/**
 * Validate environment configuration
 */
export function validateEnvironment() {
  const env = getEnvironment();
  const errors = [];

  // Check required fields
  if (!env.baseUrl) {
    errors.push('baseUrl is required');
  }

  // Check test users for non-production
  if (!isProduction() && (!env.testUsers || Object.keys(env.testUsers).length === 0)) {
    errors.push('testUsers are required');
  }

  // Check for secrets in production
  if (isProduction()) {
    if (!env.testUsers.readonly || !env.testUsers.readonly.email) {
      errors.push('Production requires readonly test user with credentials');
    }
  }

  if (errors.length > 0) {
    throw new Error(`Environment validation failed: ${errors.join(', ')}`);
  }

  return true;
}

/**
 * Get environment summary for logging
 */
export function getEnvironmentSummary() {
  const env = getEnvironment();
  return {
    name: env.name,
    baseUrl: env.baseUrl,
    defaultVUs: env.defaultVUs,
    maxVUs: env.maxVUs,
    duration: env.duration,
    features: Object.keys(env.features || {}).filter(f => env.features[f])
  };
}

export default {
  ENVIRONMENTS,
  getEnvironment,
  getCurrentEnvironment,
  isFeatureEnabled,
  getBaseUrl,
  getWsUrl,
  getTestUser,
  getDefaultVUs,
  getMaxVUs,
  getDuration,
  isProduction,
  isCI,
  getTlsConfig,
  getRateLimitConfig,
  validateEnvironment,
  getEnvironmentSummary
};
