/**
 * Sustained Load Scenario
 *
 * Tests system stability under sustained normal load over extended period.
 * Identifies memory leaks, connection leaks, and gradual performance degradation.
 *
 * Usage:
 *   k6 run sustained_load_scenario.js
 *   k6 run --duration 30m sustained_load_scenario.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Trend } from 'k6/metrics';
import {
  loginFormData,
  extractAccessToken,
  createAuthHeaders,
  BASE_URL
} from '../utils/auth.js';

// Custom metrics
const sustainedRequests = new Counter('sustained_requests');
const sustainedErrors = new Counter('sustained_errors');
const responseTimeTrend = new Trend('sustained_response_time');

// Test configuration - Sustained load
export const options = {
  stages: [
    { duration: '2m', target: 50 },    // Ramp up
    { duration: '30m', target: 50 },   // Sustained load (30 minutes)
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<2000'],  // Should stay fast throughout
    'http_req_failed': ['rate<0.02'],     // Very low error rate
    'sustained_response_time': ['p(95)<2000', 'p(99)<5000'],
  },
  tags: {
    test_type: 'sustained_load',
    scenario: 'endurance',
  },
};

export function setup() {
  console.log('Setting up sustained load test...');
  console.log('Duration: 30 minutes at 50 VUs');

  const adminResponse = loginFormData('admin@example.com', 'admin_password_123');
  const adminToken = extractAccessToken(adminResponse);

  const facultyResponse = loginFormData('faculty@example.com', 'faculty_password_123');
  const facultyToken = extractAccessToken(facultyResponse);

  return { adminToken, facultyToken };
}

export default function(data) {
  const { adminToken, facultyToken } = data;
  const token = Math.random() < 0.7 ? facultyToken : adminToken;
  const headers = createAuthHeaders(token);

  group('Sustained Operations', () => {
    const startTime = Date.now();

    // Typical user workflow
    const scheduleResponse = http.get(
      `${BASE_URL}/api/schedule/my-schedule`,
      { headers }
    );

    const responseTime = Date.now() - startTime;
    responseTimeTrend.add(responseTime);
    sustainedRequests.add(1);

    const success = check(scheduleResponse, {
      'sustained request successful': (r) => r.status === 200,
      'response time stable': (r) => responseTime < 3000,
    });

    if (!success) {
      sustainedErrors.add(1);
    }

    sleep(5 + Math.random() * 5);  // 5-10 seconds between requests
  });
}

export function teardown(data) {
  console.log('\n=== Sustained Load Test Complete ===');
  console.log(`Total Requests: ${sustainedRequests.value || 0}`);
  console.log(`Total Errors: ${sustainedErrors.value || 0}`);
  console.log('Check for memory leaks and performance degradation over time.');
}

/**
 * Success criteria:
 * - Response times remain stable throughout 30-minute test
 * - No gradual increase in response time (indicates memory leak)
 * - Error rate < 2%
 * - No database connection leaks
 * - Memory usage remains stable (monitor via metrics)
 */
