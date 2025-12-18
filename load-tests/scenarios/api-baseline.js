/**
 * API Baseline Performance Test
 *
 * Establishes baseline performance metrics for all major API endpoints.
 * Single user, 100 iterations per endpoint to measure p50, p95, p99 latencies.
 *
 * Usage:
 *   k6 run api-baseline.js
 *   k6 run --env BASE_URL=http://api.example.com api-baseline.js
 *   k6 run --out json=baseline-results.json api-baseline.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Counter } from 'k6/metrics';
import {
  loginFormData,
  extractAccessToken,
  createAuthHeaders,
  validateLoginSuccess,
  BASE_URL
} from '../utils/auth.js';
import {
  generateAssignmentFilters,
  generatePersonFilters,
  generateBlockFilters,
  generatePagination,
  toQueryString,
} from '../utils/data-generators.js';

// Custom metrics per endpoint
const metricsMap = {
  'auth_login': new Trend('auth_login_duration', true),
  'health_check': new Trend('health_check_duration', true),
  'list_assignments': new Trend('list_assignments_duration', true),
  'get_assignment': new Trend('get_assignment_duration', true),
  'list_persons': new Trend('list_persons_duration', true),
  'get_person': new Trend('get_person_duration', true),
  'list_blocks': new Trend('list_blocks_duration', true),
  'get_block': new Trend('get_block_duration', true),
  'my_assignments': new Trend('my_assignments_duration', true),
  'list_rotations': new Trend('list_rotations_duration', true),
};

const totalRequests = new Counter('total_requests');
const successfulRequests = new Counter('successful_requests');
const failedRequests = new Counter('failed_requests');

// Test configuration - single user, 100 iterations
export const options = {
  vus: 1,
  iterations: 100,
  thresholds: {
    // Baseline thresholds - should be easy to meet
    'http_req_duration': ['p(50)<500', 'p(95)<2000', 'p(99)<5000'],
    'http_req_failed': ['rate<0.01'],
    'checks': ['rate>0.98'],
  },
  tags: {
    test_type: 'baseline',
    scenario: 'api_baseline',
  },
};

// Setup: Authenticate users
export function setup() {
  console.log('Setting up API baseline performance test...');
  console.log(`Target URL: ${BASE_URL}`);

  // Authenticate different user types
  const adminResponse = loginFormData('admin@example.com', 'admin_password_123');
  const adminToken = extractAccessToken(adminResponse);

  const facultyResponse = loginFormData('faculty@example.com', 'faculty_pass_123');
  const facultyToken = extractAccessToken(facultyResponse);

  if (!adminToken || !facultyToken || !validateLoginSuccess(adminResponse) || !validateLoginSuccess(facultyResponse)) {
    throw new Error('Failed to authenticate users for baseline test.');
  }

  console.log('User authentication successful');
  console.log('Establishing baseline metrics for all endpoints...\n');

  return {
    adminToken,
    facultyToken,
  };
}

// Measure endpoint performance
function measureEndpoint(name, url, params = {}) {
  totalRequests.add(1);

  const startTime = Date.now();
  const response = http.get(url, {
    ...params,
    tags: { endpoint: name, ...params.tags },
  });
  const duration = Date.now() - startTime;

  // Record metric
  if (metricsMap[name]) {
    metricsMap[name].add(duration);
  }

  // Validate response
  const success = check(response, {
    [`${name}: status is 200`]: (r) => r.status === 200,
    [`${name}: response time < 5s`]: (r) => r.timings.duration < 5000,
    [`${name}: has response body`]: (r) => r.body && r.body.length > 0,
  });

  if (success) {
    successfulRequests.add(1);
  } else {
    failedRequests.add(1);
    console.error(`${name} failed: ${response.status} - ${response.body.substring(0, 100)}`);
  }

  return response;
}

// Test endpoints in rotation
const endpointTests = [
  // Public endpoint
  {
    name: 'health_check',
    execute: () => {
      measureEndpoint('health_check', `${BASE_URL}/health`, {});
    },
  },

  // Assignments endpoints
  {
    name: 'list_assignments',
    execute: (data) => {
      const filters = generateAssignmentFilters();
      const pagination = generatePagination();
      const query = toQueryString({ ...filters, ...pagination });

      measureEndpoint(
        'list_assignments',
        `${BASE_URL}/api/assignments${query}`,
        { headers: createAuthHeaders(data.adminToken) }
      );
    },
  },

  {
    name: 'my_assignments',
    execute: (data) => {
      measureEndpoint(
        'my_assignments',
        `${BASE_URL}/api/assignments/me`,
        { headers: createAuthHeaders(data.facultyToken) }
      );
    },
  },

  // Persons endpoints
  {
    name: 'list_persons',
    execute: (data) => {
      const filters = generatePersonFilters();
      const pagination = generatePagination();
      const query = toQueryString({ ...filters, ...pagination });

      measureEndpoint(
        'list_persons',
        `${BASE_URL}/api/persons${query}`,
        { headers: createAuthHeaders(data.adminToken) }
      );
    },
  },

  // Blocks endpoints
  {
    name: 'list_blocks',
    execute: (data) => {
      const filters = generateBlockFilters();
      const pagination = generatePagination();
      const query = toQueryString({ ...filters, ...pagination });

      measureEndpoint(
        'list_blocks',
        `${BASE_URL}/api/blocks${query}`,
        { headers: createAuthHeaders(data.adminToken) }
      );
    },
  },

  // Rotations endpoints
  {
    name: 'list_rotations',
    execute: (data) => {
      const query = toQueryString(generatePagination());

      measureEndpoint(
        'list_rotations',
        `${BASE_URL}/api/rotations${query}`,
        { headers: createAuthHeaders(data.adminToken) }
      );
    },
  },
];

// Main test function
export default function(data) {
  const iteration = __ITER;

  // Cycle through all endpoint tests
  const testIndex = iteration % endpointTests.length;
  const test = endpointTests[testIndex];

  try {
    test.execute(data);
  } catch (error) {
    console.error(`Error testing ${test.name}: ${error.message}`);
    failedRequests.add(1);
  }

  // Small delay between requests
  sleep(0.1);
}

// Teardown: Generate structured baseline report
export function teardown(data) {
  console.log('\n' + '='.repeat(70));
  console.log('API BASELINE PERFORMANCE REPORT');
  console.log('='.repeat(70));
  console.log(`Target: ${BASE_URL}`);
  console.log(`Total Requests: ${totalRequests.value || 0}`);
  console.log(`Successful: ${successfulRequests.value || 0}`);
  console.log(`Failed: ${failedRequests.value || 0}`);
  console.log(`Success Rate: ${((successfulRequests.value / totalRequests.value) * 100).toFixed(2)}%`);
  console.log('='.repeat(70));
  console.log('\nBASELINE METRICS BY ENDPOINT:');
  console.log('-'.repeat(70));
  console.log(sprintf('%-25s %10s %10s %10s', 'Endpoint', 'p50', 'p95', 'p99'));
  console.log('-'.repeat(70));

  // Note: Actual percentile values are available in k6 Cloud or Grafana
  // This is a placeholder for the report structure
  console.log('\nDetailed percentile metrics available in:');
  console.log('  - k6 Cloud dashboard');
  console.log('  - Grafana (if configured)');
  console.log('  - JSON output (use: k6 run --out json=baseline.json api-baseline.js)');

  console.log('\n' + '='.repeat(70));
  console.log('BASELINE TEST COMPLETE');
  console.log('='.repeat(70));
  console.log('\nNext steps:');
  console.log('  1. Review metrics in Grafana dashboard');
  console.log('  2. Document baseline values for regression testing');
  console.log('  3. Run load tests to compare against baseline');
  console.log('  4. Investigate any endpoints with p95 > 2s');
  console.log('');
}

// Helper for formatted output
function sprintf(format, ...args) {
  let result = format;
  args.forEach((arg) => {
    result = result.replace(/%[-]?\d*[sd]/, arg);
  });
  return result;
}

/**
 * Baseline Performance Targets:
 *
 * Excellent:
 * - p50 < 100ms
 * - p95 < 500ms
 * - p99 < 1000ms
 *
 * Good:
 * - p50 < 200ms
 * - p95 < 1000ms
 * - p99 < 2000ms
 *
 * Acceptable:
 * - p50 < 500ms
 * - p95 < 2000ms
 * - p99 < 5000ms
 *
 * Needs Optimization:
 * - p50 > 500ms
 * - p95 > 2000ms
 * - p99 > 5000ms
 *
 * How to use baseline data:
 *
 * 1. Run baseline test on production-like environment
 * 2. Document metrics in spreadsheet or monitoring system
 * 3. Set up alerting for regression (>20% degradation)
 * 4. Re-run baseline after major changes
 * 5. Use baseline to validate optimization efforts
 *
 * Export results:
 *   k6 run --out json=baseline-$(date +%Y%m%d).json api-baseline.js
 *   k6 run --out influxdb=http://localhost:8086/k6 api-baseline.js
 *   k6 run --out cloud api-baseline.js
 */
