/**
 * Peak Load Scenario
 *
 * Simulates peak usage periods (e.g., end of month when schedules are finalized).
 * Tests system behavior under maximum expected concurrent users.
 *
 * Usage:
 *   k6 run peak_load_scenario.js
 *   k6 run --env PEAK_VUS=200 peak_load_scenario.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Trend, Rate } from 'k6/metrics';
import {
  loginFormData,
  extractAccessToken,
  createAuthHeaders,
  validateLoginSuccess,
  BASE_URL
} from '../utils/auth.js';

// Custom metrics
const scheduleViews = new Counter('schedule_views');
const swapRequests = new Counter('swap_requests');
const validationChecks = new Counter('validation_checks');
const peakErrors = new Rate('peak_load_errors');

// Test configuration - Peak load scenario
export const options = {
  stages: [
    { duration: '2m', target: 50 },    // Ramp up to 50% capacity
    { duration: '3m', target: 100 },   // Reach full expected load
    { duration: '5m', target: 150 },   // Peak load (150% capacity)
    { duration: '5m', target: 200 },   // Absolute peak (2x capacity)
    { duration: '3m', target: 150 },   // Start ramping down
    { duration: '2m', target: 100 },   // Continue ramp down
    { duration: '2m', target: 0 },     // Cooldown
  ],
  thresholds: {
    // Relaxed thresholds for peak load
    'http_req_duration': ['p(95)<5000', 'p(99)<10000'],  // Allow degradation under peak
    'http_req_failed': ['rate<0.10'],  // Accept up to 10% failures at peak
    'peak_load_errors': ['rate<0.15'],  // Monitor overall error rate
    'http_req_duration{endpoint:schedule_view}': ['p(95)<3000'],
    'http_req_duration{endpoint:swap_request}': ['p(95)<2000'],
  },
  tags: {
    test_type: 'peak_load',
    scenario: 'maximum_capacity',
  },
};

// Setup: Authenticate different user types
export function setup() {
  console.log('Setting up peak load test...');
  console.log(`Target URL: ${BASE_URL}`);
  console.log('Peak VUs: 200 (2x expected capacity)');

  // Authenticate different user types
  const adminResponse = loginFormData('admin@example.com', 'admin_password_123');
  const adminToken = extractAccessToken(adminResponse);

  const facultyResponse = loginFormData('faculty@example.com', 'faculty_password_123');
  const facultyToken = extractAccessToken(facultyResponse);

  const residentResponse = loginFormData('resident@example.com', 'resident_password_123');
  const residentToken = extractAccessToken(residentResponse);

  return {
    adminToken,
    facultyToken,
    residentToken,
  };
}

// Main test function - Simulates realistic user behavior under peak load
export default function(data) {
  const { adminToken, facultyToken, residentToken } = data;

  // Randomly select user type (faculty more likely during peak times)
  const rand = Math.random();
  let token, userType;

  if (rand < 0.15) {
    token = adminToken;
    userType = 'admin';
  } else if (rand < 0.65) {
    token = facultyToken;
    userType = 'faculty';
  } else {
    token = residentToken;
    userType = 'resident';
  }

  const headers = createAuthHeaders(token);

  // Simulate realistic user journey during peak load
  group('View Schedule (Peak Load)', () => {
    const response = http.get(
      `${BASE_URL}/api/schedule/my-schedule`,
      {
        headers,
        tags: { endpoint: 'schedule_view', user_type: userType },
      }
    );

    check(response, {
      'schedule view successful': (r) => r.status === 200,
      'schedule has data': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.assignments || body.schedule;
        } catch (e) {
          return false;
        }
      },
    }) && scheduleViews.add(1);

    if (response.status !== 200) {
      peakErrors.add(1);
    }

    sleep(1 + Math.random() * 2);  // 1-3 seconds viewing
  });

  // Faculty and residents may request swaps during peak times
  if (userType === 'faculty' || userType === 'resident') {
    if (Math.random() < 0.3) {  // 30% request a swap
      group('Request Swap (Peak Load)', () => {
        const swapPayload = {
          original_block_id: `block-${Math.floor(Math.random() * 100)}`,
          desired_block_id: `block-${Math.floor(Math.random() * 100)}`,
          swap_type: 'one_to_one',
          reason: 'Peak load test swap request',
        };

        const response = http.post(
          `${BASE_URL}/api/swaps/request`,
          JSON.stringify(swapPayload),
          {
            headers,
            tags: { endpoint: 'swap_request', user_type: userType },
          }
        );

        check(response, {
          'swap request accepted': (r) => r.status === 201 || r.status === 200,
        }) && swapRequests.add(1);

        if (response.status >= 400) {
          peakErrors.add(1);
        }

        sleep(0.5);
      });
    }
  }

  // Admins may validate schedules during peak
  if (userType === 'admin' && Math.random() < 0.4) {
    group('Validate Schedule (Peak Load)', () => {
      const response = http.post(
        `${BASE_URL}/api/schedule/validate`,
        JSON.stringify({
          start_date: '2024-01-01',
          end_date: '2024-01-31',
        }),
        {
          headers,
          tags: { endpoint: 'validation', user_type: 'admin' },
          timeout: '30s',
        }
      );

      check(response, {
        'validation completed': (r) => r.status === 200,
        'validation not timeout': (r) => r.status !== 504,
      }) && validationChecks.add(1);

      if (response.status >= 400) {
        peakErrors.add(1);
      }

      sleep(2);
    });
  }

  // Think time - shorter during peak load (users are more urgent)
  sleep(2 + Math.random() * 4);  // 2-6 seconds between actions
}

// Teardown: Log final statistics
export function teardown(data) {
  console.log('\n=== Peak Load Test Complete ===');
  console.log(`Schedule Views: ${scheduleViews.value || 0}`);
  console.log(`Swap Requests: ${swapRequests.value || 0}`);
  console.log(`Validation Checks: ${validationChecks.value || 0}`);
  console.log('Check detailed metrics in Grafana dashboard.');
}

/**
 * Expected behavior:
 * - System should handle 100 concurrent users without degradation
 * - At 150 VUs, response times may increase but should stay under 5s p95
 * - At 200 VUs (peak), expect some degradation but < 10% error rate
 * - Database connection pooling should prevent connection exhaustion
 * - Rate limiting may kick in for excessive requests from same user
 *
 * Success criteria:
 * - p95 response time < 5s even at peak (200 VUs)
 * - Error rate < 10% at absolute peak
 * - No crashes or 500 errors from system failures
 * - Graceful degradation under extreme load
 *
 * Failure modes to watch:
 * - Database connection pool exhaustion
 * - Memory issues from concurrent schedule operations
 * - Rate limiting blocking legitimate users
 * - Background tasks (Celery) overwhelming Redis
 */
