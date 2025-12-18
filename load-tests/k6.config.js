/**
 * k6 Load Testing Configuration
 *
 * Base configuration and shared settings for all k6 load tests.
 * Export this file to access common options and thresholds.
 *
 * @module k6.config
 */

/**
 * Get base URL from environment or use default
 * @returns {string} Base API URL
 */
export function getBaseURL() {
  return __ENV.API_BASE_URL || 'http://localhost:8000';
}

/**
 * Default performance thresholds for all tests
 * These can be overridden in individual test scenarios
 *
 * Thresholds enforce performance SLOs:
 * - 95th percentile response time < 500ms
 * - 99th percentile response time < 1000ms
 * - Error rate < 1%
 * - HTTP failure rate < 1%
 */
export const defaultThresholds = {
  'http_req_duration': [
    'p(95)<500',   // 95% of requests must complete below 500ms
    'p(99)<1000',  // 99% of requests must complete below 1000ms
  ],
  'http_req_failed': ['rate<0.01'],  // Error rate must be below 1%
  'http_reqs': ['count>0'],          // Must have made at least one request
};

/**
 * Strict thresholds for critical endpoints (auth, compliance checks)
 */
export const strictThresholds = {
  'http_req_duration': [
    'p(95)<300',   // Stricter: 95% under 300ms
    'p(99)<600',   // Stricter: 99% under 600ms
  ],
  'http_req_failed': ['rate<0.005'],  // Stricter: 0.5% error rate
};

/**
 * Relaxed thresholds for complex operations (schedule generation, analytics)
 */
export const relaxedThresholds = {
  'http_req_duration': [
    'p(95)<2000',  // Allow up to 2 seconds for 95th percentile
    'p(99)<5000',  // Allow up to 5 seconds for 99th percentile
  ],
  'http_req_failed': ['rate<0.02'],  // Allow 2% error rate for complex ops
};

/**
 * Default load test stages
 * Simulates realistic traffic pattern with warm-up, sustained load, peak, and cooldown
 *
 * Total duration: 5 minutes
 * Peak VUs: 50
 */
export const defaultStages = [
  { duration: '30s', target: 10 },   // Warm-up: ramp to 10 users
  { duration: '1m', target: 10 },    // Sustained: hold at 10 users
  { duration: '30s', target: 30 },   // Ramp up: increase to 30 users
  { duration: '1m', target: 30 },    // Peak: hold at 30 users
  { duration: '30s', target: 50 },   // Stress: spike to 50 users
  { duration: '1m', target: 50 },    // Stress sustained
  { duration: '30s', target: 0 },    // Cooldown: ramp down
];

/**
 * Smoke test stages - minimal load to verify functionality
 * Duration: 1 minute
 * Peak VUs: 5
 */
export const smokeTestStages = [
  { duration: '30s', target: 2 },
  { duration: '30s', target: 5 },
];

/**
 * Stress test stages - push system to limits
 * Duration: 10 minutes
 * Peak VUs: 200
 */
export const stressTestStages = [
  { duration: '1m', target: 20 },
  { duration: '2m', target: 50 },
  { duration: '2m', target: 100 },
  { duration: '2m', target: 150 },
  { duration: '1m', target: 200 },
  { duration: '1m', target: 100 },
  { duration: '1m', target: 0 },
];

/**
 * Spike test stages - sudden traffic burst
 * Duration: 5 minutes
 * Peak VUs: 100 (sudden)
 */
export const spikeTestStages = [
  { duration: '30s', target: 10 },
  { duration: '10s', target: 100 },   // Sudden spike
  { duration: '2m', target: 100 },    // Sustain spike
  { duration: '10s', target: 10 },    // Sudden drop
  { duration: '2m', target: 10 },
  { duration: '30s', target: 0 },
];

/**
 * Soak test stages - prolonged sustained load
 * Duration: 1 hour
 * VUs: 20 (constant)
 */
export const soakTestStages = [
  { duration: '2m', target: 20 },
  { duration: '56m', target: 20 },    // Long sustained load
  { duration: '2m', target: 0 },
];

/**
 * Base options for all tests
 * Individual tests can override these
 */
export const baseOptions = {
  thresholds: defaultThresholds,

  // Timeouts
  httpDebug: 'full', // Can be overridden with __ENV.HTTP_DEBUG
  timeout: '60s',

  // Batching and connection pooling
  batch: 10,
  batchPerHost: 5,

  // Don't save full responses to improve performance
  discardResponseBodies: false, // Set to true for high-load tests

  // Tags for all requests
  tags: {
    test_type: 'load_test',
  },

  // Summary configuration
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
  summaryTimeUnit: 'ms',
};

/**
 * Create test options with custom stages and thresholds
 *
 * @param {Object} config - Configuration object
 * @param {Array} config.stages - Load test stages
 * @param {Object} config.thresholds - Performance thresholds
 * @param {Object} config.tags - Custom tags for metrics
 * @returns {Object} Complete k6 options object
 */
export function createTestOptions({ stages, thresholds, tags = {} }) {
  return {
    ...baseOptions,
    stages: stages || defaultStages,
    thresholds: thresholds || defaultThresholds,
    tags: {
      ...baseOptions.tags,
      ...tags,
    },
  };
}

/**
 * Common HTTP request parameters
 */
export const httpParams = {
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  tags: {
    name: 'default-request',
  },
  timeout: '30s',
};

/**
 * Rate limiting settings (align with backend config)
 * These match the backend rate limits defined in app/core/config.py
 */
export const rateLimits = {
  login: {
    maxRequests: 5,
    windowSeconds: 300,  // 5 attempts per 5 minutes
  },
  register: {
    maxRequests: 3,
    windowSeconds: 3600,  // 3 attempts per hour
  },
  general: {
    maxRequests: 100,
    windowSeconds: 60,  // 100 requests per minute
  },
};

/**
 * Test data limits
 * Keep these reasonable to avoid overwhelming the test database
 */
export const testLimits = {
  maxPeople: 100,
  maxAssignments: 1000,
  maxConcurrentUsers: 200,
  dataCacheSize: 50,  // Number of pre-generated test entities to cache
};

/**
 * Environment-specific configuration
 * @returns {Object} Environment config
 */
export function getEnvironmentConfig() {
  const env = __ENV.TEST_ENV || 'local';

  const configs = {
    local: {
      baseURL: 'http://localhost:8000',
      maxVUs: 50,
      duration: '5m',
    },
    docker: {
      baseURL: 'http://backend:8000',
      maxVUs: 100,
      duration: '10m',
    },
    staging: {
      baseURL: __ENV.STAGING_URL || 'http://staging.example.com',
      maxVUs: 200,
      duration: '15m',
    },
  };

  return configs[env] || configs.local;
}

/**
 * Export all configuration
 */
export default {
  getBaseURL,
  defaultThresholds,
  strictThresholds,
  relaxedThresholds,
  defaultStages,
  smokeTestStages,
  stressTestStages,
  spikeTestStages,
  soakTestStages,
  baseOptions,
  createTestOptions,
  httpParams,
  rateLimits,
  testLimits,
  getEnvironmentConfig,
};
