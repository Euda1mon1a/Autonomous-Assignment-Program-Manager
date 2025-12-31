/**
 * Base k6 Configuration
 *
 * Shared configuration for all load tests.
 * Defines default options, common settings, and base URLs.
 */

export const BASE_CONFIG = {
  // Base URLs for different environments
  baseUrls: {
    local: 'http://localhost:8000',
    docker: 'http://backend:8000',
    staging: 'https://staging.scheduler.example.com',
    production: 'https://scheduler.example.com'
  },

  // Default test options
  defaultOptions: {
    // HTTP settings
    http: {
      timeout: '30s',
      responseType: 'text'
    },

    // Batch requests
    batch: 10,
    batchPerHost: 5,

    // Discard response bodies by default to save memory
    discardResponseBodies: false,

    // DNS settings
    dns: {
      ttl: '5m',
      select: 'roundRobin',
      policy: 'preferIPv4'
    },

    // User agent
    userAgent: 'k6-load-test/1.0.0',

    // Hosts mapping (for docker environments)
    hosts: {
      'backend': '127.0.0.1'
    },

    // No connection reuse by default
    noConnectionReuse: false,

    // VU settings
    vus: 1,
    duration: '30s',

    // Tags for all requests
    tags: {
      test_type: 'load',
      environment: __ENV.ENVIRONMENT || 'local',
      version: __ENV.VERSION || 'unknown'
    },

    // System tags
    systemTags: [
      'status',
      'method',
      'url',
      'name',
      'group',
      'check',
      'error',
      'error_code',
      'tls_version',
      'scenario',
      'service'
    ],

    // Summary settings
    summaryTrendStats: [
      'avg',
      'min',
      'med',
      'max',
      'p(90)',
      'p(95)',
      'p(99)',
      'p(99.9)',
      'count'
    ],

    // Time format
    summaryTimeUnit: 'ms'
  },

  // API endpoints
  endpoints: {
    health: '/health',
    auth: {
      login: '/api/v1/auth/login',
      logout: '/api/v1/auth/logout',
      refresh: '/api/v1/auth/refresh',
      me: '/api/v1/auth/me'
    },
    schedules: {
      list: '/api/v1/schedules',
      create: '/api/v1/schedules',
      detail: '/api/v1/schedules/{id}',
      generate: '/api/v1/schedules/generate',
      validate: '/api/v1/schedules/{id}/validate'
    },
    assignments: {
      list: '/api/v1/assignments',
      create: '/api/v1/assignments',
      detail: '/api/v1/assignments/{id}',
      bulk: '/api/v1/assignments/bulk'
    },
    swaps: {
      list: '/api/v1/swaps',
      create: '/api/v1/swaps',
      detail: '/api/v1/swaps/{id}',
      execute: '/api/v1/swaps/{id}/execute',
      match: '/api/v1/swaps/match',
      rollback: '/api/v1/swaps/{id}/rollback'
    },
    compliance: {
      validate: '/api/v1/compliance/validate',
      workHours: '/api/v1/compliance/work-hours',
      violations: '/api/v1/compliance/violations'
    },
    resilience: {
      health: '/api/v1/resilience/health',
      metrics: '/api/v1/resilience/metrics',
      nMinusOne: '/api/v1/resilience/n-minus-one',
      utilization: '/api/v1/resilience/utilization'
    },
    persons: {
      list: '/api/v1/persons',
      create: '/api/v1/persons',
      detail: '/api/v1/persons/{id}'
    },
    rotations: {
      list: '/api/v1/rotations',
      create: '/api/v1/rotations',
      detail: '/api/v1/rotations/{id}'
    },
    blocks: {
      list: '/api/v1/blocks',
      create: '/api/v1/blocks',
      detail: '/api/v1/blocks/{id}'
    }
  },

  // Test users (credentials)
  testUsers: {
    admin: {
      email: 'admin@test.com',
      password: 'TestPassword123!',
      role: 'ADMIN'
    },
    coordinator: {
      email: 'coordinator@test.com',
      password: 'TestPassword123!',
      role: 'COORDINATOR'
    },
    faculty: {
      email: 'faculty@test.com',
      password: 'TestPassword123!',
      role: 'FACULTY'
    },
    resident: {
      email: 'resident@test.com',
      password: 'TestPassword123!',
      role: 'RESIDENT'
    }
  },

  // Rate limits (from backend configuration)
  rateLimits: {
    default: {
      requests: 100,
      window: '1m'
    },
    auth: {
      requests: 5,
      window: '15m'
    },
    scheduleGeneration: {
      requests: 10,
      window: '1h'
    }
  }
};

/**
 * Get base URL for current environment
 */
export function getBaseUrl() {
  const env = __ENV.ENVIRONMENT || 'local';
  return __ENV.BASE_URL || BASE_CONFIG.baseUrls[env] || BASE_CONFIG.baseUrls.local;
}

/**
 * Get full URL for an endpoint
 */
export function getEndpointUrl(endpointPath) {
  const baseUrl = getBaseUrl();
  return `${baseUrl}${endpointPath}`;
}

/**
 * Replace path parameters in endpoint
 */
export function replacePathParams(endpoint, params) {
  let url = endpoint;
  for (const [key, value] of Object.entries(params)) {
    url = url.replace(`{${key}}`, value);
  }
  return url;
}

/**
 * Get test user credentials
 */
export function getTestUser(role = 'admin') {
  return BASE_CONFIG.testUsers[role.toLowerCase()] || BASE_CONFIG.testUsers.admin;
}

export default BASE_CONFIG;
