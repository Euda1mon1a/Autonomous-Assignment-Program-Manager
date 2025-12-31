/**
 * Load Test
 *
 * Standard load test with production-like traffic patterns.
 * Purpose: Validate system performance under expected load.
 *
 * Run: k6 run load-test.js
 * Run with custom VUs: k6 run --vus 50 --duration 10m load-test.js
 */

import { sleep, group } from 'k6';
import { htmlReport } from 'https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';
import { getBaseUrl, getDefaultVUs, getDuration } from '../config/environments.js';
import { LOAD_THRESHOLDS } from '../config/thresholds.js';
import { createAuthSession } from '../utils/auth.js';
import { httpGet, buildUrl } from '../utils/http-helpers.js';
import { assertSuccess, assertPaginatedResponse } from '../utils/assertions.js';
import { MetricTracker } from '../utils/metrics.js';
import { generateFilterParams, generateSortParams, generatePaginationParams } from '../utils/data-generators.js';

export const options = {
  // Ramping VU configuration
  stages: [
    { duration: '2m', target: getDefaultVUs() },      // Ramp up
    { duration: '5m', target: getDefaultVUs() },      // Steady state
    { duration: '2m', target: getDefaultVUs() * 2 },  // Peak load
    { duration: '3m', target: getDefaultVUs() * 2 },  // Peak steady state
    { duration: '2m', target: 0 }                     // Ramp down
  ],

  // Thresholds
  thresholds: LOAD_THRESHOLDS,

  // Tags
  tags: {
    test_type: 'load',
    environment: __ENV.ENVIRONMENT || 'local'
  }
};

/**
 * Setup
 */
export function setup() {
  console.log('======================================');
  console.log('LOAD TEST CONFIGURATION');
  console.log('======================================');
  console.log(`Base URL: ${getBaseUrl()}`);
  console.log(`VUs: ${getDefaultVUs()}`);
  console.log(`Duration: ${getDuration()}`);
  console.log('======================================');

  return {
    baseUrl: getBaseUrl(),
    startTime: Date.now()
  };
}

/**
 * Main test function - simulates realistic user behavior
 */
export default function (data) {
  const metrics = new MetricTracker();
  const session = createAuthSession('faculty');

  // Simulate think time between actions
  const thinkTime = () => sleep(__ENV.THINK_TIME || 1);

  // User Flow 1: View Schedule (most common operation)
  if (Math.random() < 0.6) {  // 60% of users
    group('View Schedule', () => {
      const startTime = Date.now();

      // List assignments with filters
      const params = {
        ...generatePaginationParams(),
        ...generateFilterParams()
      };

      const response = session.get(buildUrl('/api/v1/assignments', params));
      assertSuccess(response);
      assertPaginatedResponse(response);

      metrics.trackUserFlow('schedule_view', Date.now() - startTime, response.status === 200);
    });

    thinkTime();
  }

  // User Flow 2: Check Compliance (moderately common)
  if (Math.random() < 0.3) {  // 30% of users
    group('Check Compliance', () => {
      const startTime = Date.now();

      const response = session.get(buildUrl('/api/v1/compliance/work-hours'));
      assertSuccess(response);

      const duration = Date.now() - startTime;
      metrics.trackComplianceCheck(duration);
    });

    thinkTime();
  }

  // User Flow 3: Browse Rotations
  if (Math.random() < 0.4) {  // 40% of users
    group('Browse Rotations', () => {
      const params = generatePaginationParams();
      const response = session.get(buildUrl('/api/v1/rotations', params));
      assertSuccess(response);
    });

    thinkTime();
  }

  // User Flow 4: View Personnel
  if (Math.random() < 0.35) {  // 35% of users
    group('View Personnel', () => {
      const params = {
        ...generatePaginationParams(),
        ...generateFilterParams()
      };

      const response = session.get(buildUrl('/api/v1/persons', params));
      assertSuccess(response);
      assertPaginatedResponse(response);
    });

    thinkTime();
  }

  // User Flow 5: View Swap Requests (less common)
  if (Math.random() < 0.2) {  // 20% of users
    group('View Swaps', () => {
      const response = session.get(buildUrl('/api/v1/swaps?limit=20'));
      assertSuccess(response);
    });

    thinkTime();
  }

  // User Flow 6: Check Resilience Metrics (admin/coordinator only)
  if (Math.random() < 0.1) {  // 10% of users
    group('Resilience Metrics', () => {
      const response = session.get(buildUrl('/api/v1/resilience/metrics'));
      assertSuccess(response);
    });

    thinkTime();
  }

  // User Flow 7: Search Operations (occasional)
  if (Math.random() < 0.15) {  // 15% of users
    group('Search', () => {
      const searchQuery = 'clinic';
      const response = session.get(buildUrl('/api/v1/rotations', { search: searchQuery }));
      assertSuccess(response);
    });

    thinkTime();
  }

  // User Flow 8: View Blocks (calendar view)
  if (Math.random() < 0.25) {  // 25% of users
    group('View Blocks', () => {
      const today = new Date().toISOString().split('T')[0];
      const params = {
        start_date: today,
        limit: 30
      };

      const response = session.get(buildUrl('/api/v1/blocks', params));
      assertSuccess(response);
    });

    thinkTime();
  }

  // Random sleep to simulate realistic pacing
  sleep(Math.random() * 2 + 1);
}

/**
 * Teardown
 */
export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log('======================================');
  console.log(`Load test completed in ${duration.toFixed(2)}s`);
  console.log('======================================');
}

/**
 * Custom summary report
 */
export function handleSummary(data) {
  const summary = {
    'load-test-summary.html': htmlReport(data),
    'load-test-summary.json': JSON.stringify(data, null, 2),
    'stdout': textSummary(data, { indent: ' ', enableColors: true })
  };

  // Custom console summary
  console.log('======================================');
  console.log('LOAD TEST RESULTS');
  console.log('======================================');

  const httpReqs = data.metrics.http_reqs;
  const httpReqDuration = data.metrics.http_req_duration;
  const httpReqFailed = data.metrics.http_req_failed;
  const checks = data.metrics.checks;
  const iterations = data.metrics.iterations;

  if (httpReqs) {
    console.log(`Total Requests: ${httpReqs.values.count}`);
    console.log(`Request Rate: ${httpReqs.values.rate.toFixed(2)} req/s`);
  }

  if (httpReqFailed) {
    console.log(`Failed Requests: ${(httpReqFailed.values.rate * 100).toFixed(2)}%`);
  }

  if (httpReqDuration) {
    console.log(`\nResponse Times:`);
    console.log(`  Avg: ${httpReqDuration.values.avg.toFixed(2)}ms`);
    console.log(`  Min: ${httpReqDuration.values.min.toFixed(2)}ms`);
    console.log(`  Med: ${httpReqDuration.values.med.toFixed(2)}ms`);
    console.log(`  Max: ${httpReqDuration.values.max.toFixed(2)}ms`);
    console.log(`  P90: ${httpReqDuration.values['p(90)'].toFixed(2)}ms`);
    console.log(`  P95: ${httpReqDuration.values['p(95)'].toFixed(2)}ms`);
    console.log(`  P99: ${httpReqDuration.values['p(99)'].toFixed(2)}ms`);
  }

  if (checks) {
    console.log(`\nChecks Passed: ${(checks.values.rate * 100).toFixed(2)}%`);
  }

  if (iterations) {
    console.log(`Total Iterations: ${iterations.values.count}`);
    console.log(`Iteration Rate: ${iterations.values.rate.toFixed(2)} iter/s`);
  }

  console.log('======================================');

  // Check if thresholds passed
  const thresholdsPassed = Object.keys(data.metrics).every(metricName => {
    const metric = data.metrics[metricName];
    return !metric.thresholds || Object.values(metric.thresholds).every(t => t.ok);
  });

  if (thresholdsPassed) {
    console.log('✅ All thresholds PASSED');
  } else {
    console.log('❌ Some thresholds FAILED');

    // Show failed thresholds
    console.log('\nFailed Thresholds:');
    Object.keys(data.metrics).forEach(metricName => {
      const metric = data.metrics[metricName];
      if (metric.thresholds) {
        Object.entries(metric.thresholds).forEach(([threshold, result]) => {
          if (!result.ok) {
            console.log(`  ${metricName}: ${threshold}`);
          }
        });
      }
    });
  }

  console.log('======================================');

  return summary;
}
