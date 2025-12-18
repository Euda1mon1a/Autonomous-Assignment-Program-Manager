/**
 * Schedule Generation Load Test
 *
 * Tests concurrent schedule generation under load.
 * Simulates multiple admins triggering schedule generation simultaneously.
 *
 * Usage:
 *   k6 run schedule-generation.js
 *   k6 run --env BASE_URL=http://api.example.com schedule-generation.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend, Rate } from 'k6/metrics';
import {
  loginFormData,
  extractAccessToken,
  createAuthHeaders,
  validateLoginSuccess,
  BASE_URL
} from '../utils/auth.js';
import { generateScheduleRequest } from '../utils/data-generators.js';

// Custom metrics
const scheduleGenerationDuration = new Trend('schedule_generation_duration', true);
const schedulesCreated = new Counter('schedules_created');
const scheduleGenerationErrors = new Rate('schedule_generation_errors');
const acgmeViolations = new Counter('acgme_violations');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 1 },   // Warm-up: 1 user
    { duration: '3m', target: 5 },   // Ramp to 5 concurrent admins
    { duration: '5m', target: 10 },  // Peak: 10 concurrent admins
    { duration: '3m', target: 5 },   // Ramp down
    { duration: '2m', target: 0 },   // Cooldown
  ],
  thresholds: {
    // Schedule generation is slow, so p95 < 30s is acceptable
    'schedule_generation_duration': ['p(95)<30000', 'p(99)<60000'],

    // Error rate should be very low
    'schedule_generation_errors': ['rate<0.05'],

    // HTTP failures should be minimal
    'http_req_failed': ['rate<0.05'],

    // Most requests should complete within reasonable time
    'http_req_duration': ['p(95)<35000'],
  },
  tags: {
    test_type: 'load',
    scenario: 'schedule_generation',
  },
};

// Setup: Authenticate admin user
export function setup() {
  console.log('Setting up schedule generation load test...');
  console.log(`Target URL: ${BASE_URL}`);

  // Authenticate as admin (required for schedule generation)
  const response = loginFormData('admin@example.com', 'admin_password_123');
  const adminToken = extractAccessToken(response);

  if (!adminToken || !validateLoginSuccess(response)) {
    throw new Error('Failed to authenticate admin user. Cannot proceed with test.');
  }

  console.log('Admin authentication successful');
  return { adminToken };
}

// Main test function - executed by each virtual user
export default function(data) {
  const { adminToken } = data;
  const headers = createAuthHeaders(adminToken);

  // Generate schedule request payload
  const payload = generateScheduleRequest();

  const params = {
    headers: headers,
    timeout: '120s',  // Schedule generation can take time
    tags: {
      name: 'generate_schedule',
      endpoint: '/api/schedule/generate',
    },
  };

  console.log(`VU ${__VU}: Requesting schedule generation...`);
  const startTime = Date.now();

  // POST to schedule generation endpoint
  const response = http.post(
    `${BASE_URL}/api/schedule/generate`,
    JSON.stringify(payload),
    params
  );

  const duration = Date.now() - startTime;
  scheduleGenerationDuration.add(duration);

  // Validate response
  const success = check(response, {
    'status is 200 or 201': (r) => r.status === 200 || r.status === 201,
    'response has schedule_id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.schedule_id !== undefined || body.id !== undefined;
      } catch (e) {
        return false;
      }
    },
    'response time < 60s': (r) => r.timings.duration < 60000,
  });

  if (success) {
    schedulesCreated.add(1);
    console.log(`VU ${__VU}: Schedule generated successfully in ${duration}ms`);

    try {
      const body = JSON.parse(response.body);

      // Check for ACGME compliance info
      if (body.acgme_compliant === false) {
        acgmeViolations.add(1);
        console.warn(`VU ${__VU}: Generated schedule has ACGME violations`);
      }

      // Log schedule metadata
      if (body.total_assignments) {
        console.log(`VU ${__VU}: Created ${body.total_assignments} assignments`);
      }
    } catch (e) {
      console.error(`VU ${__VU}: Failed to parse response body: ${e.message}`);
    }
  } else {
    scheduleGenerationErrors.add(1);
    console.error(`VU ${__VU}: Schedule generation failed - Status: ${response.status}`);
    console.error(`VU ${__VU}: Response: ${response.body.substring(0, 200)}`);
  }

  // Additional checks for specific error conditions
  check(response, {
    'no server errors (5xx)': (r) => r.status < 500,
    'no timeout errors': (r) => r.status !== 504,
    'no rate limit errors': (r) => r.status !== 429,
  });

  // Think time: Wait before next generation attempt
  // In reality, admins wouldn't trigger generation continuously
  sleep(10 + Math.random() * 20);  // 10-30 seconds between attempts
}

// Teardown: Log final statistics
export function teardown(data) {
  console.log('\n=== Schedule Generation Load Test Complete ===');
  console.log(`Total schedules created: ${schedulesCreated.value || 0}`);
  console.log(`ACGME violations detected: ${acgmeViolations.value || 0}`);
  console.log('Check Grafana dashboard for detailed metrics.');
}

/**
 * Expected behavior:
 * - Each VU simulates an admin triggering schedule generation
 * - Schedule generation is CPU-intensive and may take 5-30+ seconds
 * - The system should handle 5-10 concurrent generation requests
 * - Error rate should be < 5% under normal load
 * - ACGME violations should be investigated if detected
 *
 * Success criteria:
 * - p95 response time < 30 seconds
 * - Error rate < 5%
 * - No server crashes or timeouts
 * - Generated schedules are valid and compliant
 *
 * Failure modes to watch:
 * - Database connection pool exhaustion
 * - Memory issues from large schedule computations
 * - Lock contention if multiple generations conflict
 * - Timeout errors (504) indicating overload
 */
