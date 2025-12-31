/**
 * Smoke Test
 *
 * Quick validation test with minimal load.
 * Purpose: Verify system is functional before running larger tests.
 *
 * Run: k6 run smoke-test.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { getBaseUrl } from '../config/environments.js';
import { SMOKE_THRESHOLDS } from '../config/thresholds.js';
import { login, getCurrentUser } from '../utils/auth.js';
import { getTestUser } from '../config/base.js';
import { httpGet, buildUrl } from '../utils/http-helpers.js';
import { assertSuccess, assertJsonContent } from '../utils/assertions.js';

export const options = {
  // Single VU for quick validation
  vus: 1,
  duration: '1m',

  // Thresholds
  thresholds: SMOKE_THRESHOLDS,

  // Tags
  tags: {
    test_type: 'smoke',
    environment: __ENV.ENVIRONMENT || 'local'
  }
};

/**
 * Setup - runs once before test
 */
export function setup() {
  console.log('Starting smoke test...');
  console.log(`Base URL: ${getBaseUrl()}`);

  // Verify service is accessible
  const healthUrl = buildUrl('/health');
  const healthResponse = http.get(healthUrl);

  if (healthResponse.status !== 200) {
    throw new Error(`Service not available: ${healthResponse.status}`);
  }

  console.log('✓ Service is accessible');

  return {
    baseUrl: getBaseUrl(),
    startTime: Date.now()
  };
}

/**
 * Main test function
 */
export default function (data) {
  const baseUrl = data.baseUrl;

  // Test 1: Health Check
  group('Health Check', () => {
    const response = httpGet(buildUrl('/health'));

    check(response, {
      'health check successful': (r) => r.status === 200,
      'response time < 100ms': (r) => r.timings.duration < 100
    });

    sleep(0.5);
  });

  // Test 2: Authentication
  group('Authentication', () => {
    const user = getTestUser('admin');
    const auth = login(user.email, user.password);

    check(auth, {
      'login successful': (a) => a !== null,
      'access token received': (a) => a && a.accessToken !== null
    });

    if (auth) {
      const currentUser = getCurrentUser(auth.accessToken);
      check(currentUser, {
        'user data received': (u) => u !== null,
        'email matches': (u) => u && u.email === user.email
      });
    }

    sleep(0.5);
  });

  // Test 3: List Endpoints
  group('List Operations', () => {
    const user = getTestUser('admin');
    const auth = login(user.email, user.password);

    if (auth) {
      const endpoints = [
        '/api/v1/persons?limit=10',
        '/api/v1/rotations?limit=10',
        '/api/v1/blocks?limit=10',
        '/api/v1/assignments?limit=10'
      ];

      endpoints.forEach(endpoint => {
        const response = httpGet(buildUrl(endpoint), {
          headers: {
            'Authorization': `Bearer ${auth.accessToken}`,
            'Content-Type': 'application/json'
          }
        });

        assertSuccess(response);
        assertJsonContent(response);
      });
    }

    sleep(0.5);
  });

  // Test 4: Compliance Endpoints
  group('Compliance', () => {
    const user = getTestUser('admin');
    const auth = login(user.email, user.password);

    if (auth) {
      const response = httpGet(buildUrl('/api/v1/compliance/validate'), {
        headers: {
          'Authorization': `Bearer ${auth.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      check(response, {
        'compliance endpoint accessible': (r) => r.status === 200 || r.status === 422
      });
    }

    sleep(0.5);
  });

  // Test 5: Resilience Endpoints
  group('Resilience', () => {
    const user = getTestUser('admin');
    const auth = login(user.email, user.password);

    if (auth) {
      const response = httpGet(buildUrl('/api/v1/resilience/health'), {
        headers: {
          'Authorization': `Bearer ${auth.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      assertSuccess(response);
    }

    sleep(0.5);
  });

  sleep(1);
}

/**
 * Teardown - runs once after test
 */
export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`Smoke test completed in ${duration.toFixed(2)}s`);
}

/**
 * Handle summary for custom output
 */
export function handleSummary(data) {
  console.log('======================================');
  console.log('SMOKE TEST SUMMARY');
  console.log('======================================');

  const httpReqs = data.metrics.http_reqs;
  const httpReqDuration = data.metrics.http_req_duration;
  const httpReqFailed = data.metrics.http_req_failed;
  const checks = data.metrics.checks;

  console.log(`Total Requests: ${httpReqs ? httpReqs.values.count : 0}`);
  console.log(`Failed Requests: ${httpReqFailed ? (httpReqFailed.values.rate * 100).toFixed(2) : 0}%`);
  console.log(`Avg Response Time: ${httpReqDuration ? httpReqDuration.values.avg.toFixed(2) : 0}ms`);
  console.log(`P95 Response Time: ${httpReqDuration ? httpReqDuration.values['p(95)'].toFixed(2) : 0}ms`);
  console.log(`Checks Passed: ${checks ? (checks.values.rate * 100).toFixed(2) : 0}%`);
  console.log('======================================');

  return {
    'stdout': JSON.stringify(data, null, 2),
    'summary.json': JSON.stringify(data, null, 2)
  };
}
