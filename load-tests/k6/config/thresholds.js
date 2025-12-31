/**
 * Performance Thresholds Configuration
 *
 * Defines acceptable performance criteria for different test types.
 * Tests fail if thresholds are not met.
 *
 * Threshold format:
 * - 'http_req_duration': ['p(95)<500'] means 95th percentile must be < 500ms
 * - 'http_req_failed': ['rate<0.01'] means error rate must be < 1%
 */

/**
 * Smoke Test Thresholds
 * Quick validation with minimal load
 */
export const SMOKE_THRESHOLDS = {
  // HTTP metrics
  http_req_duration: [
    'p(95)<1000',  // 95% of requests complete in < 1s
    'p(99)<2000'   // 99% of requests complete in < 2s
  ],
  http_req_failed: ['rate<0.05'],  // Error rate < 5%
  http_req_waiting: ['p(95)<800'],  // Server processing time < 800ms

  // Checks
  checks: ['rate>0.95'],  // 95% of checks must pass

  // Iterations
  iterations: ['count>10']  // At least 10 iterations
};

/**
 * Load Test Thresholds
 * Standard production-like load
 */
export const LOAD_THRESHOLDS = {
  // HTTP metrics - stricter than smoke test
  http_req_duration: [
    'p(90)<500',   // 90% < 500ms
    'p(95)<800',   // 95% < 800ms
    'p(99)<1500'   // 99% < 1.5s
  ],
  http_req_failed: ['rate<0.01'],  // Error rate < 1%
  http_req_waiting: ['p(95)<600'],
  http_req_connecting: ['p(95)<100'],  // Connection time < 100ms

  // Checks
  checks: ['rate>0.98'],  // 98% of checks must pass

  // Data transfer
  data_received: ['rate>1000000'],  // At least 1MB/s received
  data_sent: ['rate>100000']  // At least 100KB/s sent
};

/**
 * Stress Test Thresholds
 * Higher load - degraded performance acceptable
 */
export const STRESS_THRESHOLDS = {
  // HTTP metrics - relaxed for stress conditions
  http_req_duration: [
    'p(90)<1000',   // 90% < 1s
    'p(95)<2000',   // 95% < 2s
    'p(99)<5000'    // 99% < 5s
  ],
  http_req_failed: ['rate<0.05'],  // Error rate < 5%
  http_req_waiting: ['p(95)<1500'],

  // Checks
  checks: ['rate>0.90'],  // 90% of checks must pass

  // Availability
  'group_duration{group:::api_availability}': ['p(95)<3000']
};

/**
 * Spike Test Thresholds
 * Sudden load increase - focus on recovery
 */
export const SPIKE_THRESHOLDS = {
  // HTTP metrics
  http_req_duration: [
    'p(90)<2000',   // Allow higher latency during spike
    'p(95)<3000',
    'p(99)<8000'
  ],
  http_req_failed: ['rate<0.10'],  // Allow 10% errors during spike

  // Checks
  checks: ['rate>0.85'],  // 85% of checks must pass

  // Focus on recovery time
  'http_req_duration{scenario:recovery}': ['p(95)<500']  // Quick recovery
};

/**
 * Soak Test Thresholds
 * Long-running stability test
 */
export const SOAK_THRESHOLDS = {
  // HTTP metrics - consistent over time
  http_req_duration: [
    'p(95)<1000',   // Performance shouldn't degrade
    'p(99)<2000'
  ],
  http_req_failed: ['rate<0.02'],  // Error rate < 2%

  // Checks
  checks: ['rate>0.95'],

  // Memory stability (custom metrics)
  memory_usage: ['max<80'],  // Max 80% memory
  connection_pool: ['value<100']  // Max 100 connections
};

/**
 * API-Specific Thresholds
 */
export const API_THRESHOLDS = {
  // Schedule generation (expensive operation)
  schedule: {
    'http_req_duration{name:generate_schedule}': [
      'p(95)<10000',  // Schedule generation < 10s
      'p(99)<20000'   // 99th percentile < 20s
    ],
    'http_req_duration{name:validate_schedule}': [
      'p(95)<2000'    // Validation < 2s
    ]
  },

  // Swap operations
  swap: {
    'http_req_duration{name:match_swap}': [
      'p(95)<1000'    // Swap matching < 1s
    ],
    'http_req_duration{name:execute_swap}': [
      'p(95)<500'     // Swap execution < 500ms
    ]
  },

  // Compliance validation
  compliance: {
    'http_req_duration{name:validate_compliance}': [
      'p(95)<1500'    // ACGME validation < 1.5s
    ],
    'http_req_duration{name:work_hours}': [
      'p(95)<500'     // Work hours calculation < 500ms
    ]
  },

  // Resilience metrics
  resilience: {
    'http_req_duration{name:n_minus_one}': [
      'p(95)<3000'    // N-1 analysis < 3s
    ],
    'http_req_duration{name:utilization}': [
      'p(95)<1000'    // Utilization calculation < 1s
    ]
  },

  // CRUD operations
  crud: {
    'http_req_duration{name:list}': [
      'p(95)<300'     // List operations < 300ms
    ],
    'http_req_duration{name:create}': [
      'p(95)<500'     // Create operations < 500ms
    ],
    'http_req_duration{name:update}': [
      'p(95)<500'     // Update operations < 500ms
    ],
    'http_req_duration{name:delete}': [
      'p(95)<300'     // Delete operations < 300ms
    ]
  },

  // Authentication
  auth: {
    'http_req_duration{name:login}': [
      'p(95)<1000'    // Login < 1s
    ],
    'http_req_duration{name:refresh}': [
      'p(95)<300'     // Token refresh < 300ms
    ]
  }
};

/**
 * Database Performance Thresholds
 */
export const DATABASE_THRESHOLDS = {
  // Query performance
  'db_query_duration': [
    'p(95)<100',    // Most queries < 100ms
    'p(99)<500'     // Complex queries < 500ms
  ],

  // Connection pool
  'db_connections_active': ['max<80'],  // Max 80 active connections
  'db_connections_idle': ['min>5'],     // Keep 5 idle connections

  // Transaction success
  'db_transactions_failed': ['rate<0.01']  // < 1% transaction failures
};

/**
 * Cache Performance Thresholds
 */
export const CACHE_THRESHOLDS = {
  'cache_hit_rate': ['rate>0.80'],  // 80% cache hit rate
  'cache_response_time': ['p(95)<10'],  // Cache response < 10ms
  'cache_miss_recovery': ['p(95)<200']  // Cache miss recovery < 200ms
};

/**
 * Rate Limit Thresholds
 */
export const RATE_LIMIT_THRESHOLDS = {
  'http_req_duration{status:429}': ['count>0'],  // Expect rate limiting
  'rate_limit_triggered': ['rate>0.80'],  // 80% should hit rate limit
  'rate_limit_recovery': ['p(95)<1000']   // Recovery after rate limit < 1s
};

/**
 * Get thresholds for test type
 */
export function getThresholdsForTestType(testType) {
  const thresholds = {
    smoke: SMOKE_THRESHOLDS,
    load: LOAD_THRESHOLDS,
    stress: STRESS_THRESHOLDS,
    spike: SPIKE_THRESHOLDS,
    soak: SOAK_THRESHOLDS
  };

  return thresholds[testType] || LOAD_THRESHOLDS;
}

/**
 * Merge thresholds (combine multiple threshold sets)
 */
export function mergeThresholds(...thresholdSets) {
  return Object.assign({}, ...thresholdSets);
}

/**
 * Get API-specific thresholds
 */
export function getApiThresholds(apiName) {
  return API_THRESHOLDS[apiName] || {};
}

/**
 * Create custom threshold
 */
export function customThreshold(metric, conditions) {
  return {
    [metric]: Array.isArray(conditions) ? conditions : [conditions]
  };
}

/**
 * SLA-based thresholds (Service Level Agreement)
 */
export const SLA_THRESHOLDS = {
  // 99.9% availability (three nines)
  threeNines: {
    http_req_failed: ['rate<0.001'],  // 0.1% error rate
    checks: ['rate>0.999']
  },

  // 99% availability (two nines)
  twoNines: {
    http_req_failed: ['rate<0.01'],  // 1% error rate
    checks: ['rate>0.99']
  },

  // 95% availability
  basic: {
    http_req_failed: ['rate<0.05'],  // 5% error rate
    checks: ['rate>0.95']
  }
};

export default {
  SMOKE_THRESHOLDS,
  LOAD_THRESHOLDS,
  STRESS_THRESHOLDS,
  SPIKE_THRESHOLDS,
  SOAK_THRESHOLDS,
  API_THRESHOLDS,
  DATABASE_THRESHOLDS,
  CACHE_THRESHOLDS,
  RATE_LIMIT_THRESHOLDS,
  SLA_THRESHOLDS,
  getThresholdsForTestType,
  mergeThresholds,
  getApiThresholds,
  customThreshold
};
