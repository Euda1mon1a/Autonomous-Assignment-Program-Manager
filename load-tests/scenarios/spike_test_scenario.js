/**
 * Spike Test Scenario
 *
 * Tests system behavior under sudden traffic spikes.
 * Simulates scenarios like:
 * - Everyone logging in after a system outage
 * - Mass schedule view after email notification
 * - Sudden surge after new schedule release
 *
 * Usage:
 *   k6 run spike_test_scenario.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate } from 'k6/metrics';
import {
  loginFormData,
  extractAccessToken,
  createAuthHeaders,
  BASE_URL
} from '../utils/auth.js';

// Custom metrics
const spikeRequests = new Counter('spike_requests');
const spikeErrors = new Rate('spike_errors');
const recoverySuccess = new Rate('recovery_success');

// Test configuration - Spike test
export const options = {
  stages: [
    { duration: '30s', target: 10 },    // Normal load
    { duration: '10s', target: 200 },   // SPIKE! (20x increase in 10 seconds)
    { duration: '1m', target: 200 },    // Sustain spike for 1 minute
    { duration: '10s', target: 10 },    // Drop back to normal
    { duration: '1m', target: 10 },     // Verify recovery
  ],
  thresholds: {
    'http_req_duration': ['p(95)<10000'],  // Relaxed during spike
    'http_req_failed': ['rate<0.20'],      // Accept 20% failures during spike
    'recovery_success': ['rate>0.95'],     // Must recover well
    'spike_errors': ['rate<0.30'],         // Overall spike error rate
  },
  tags: {
    test_type: 'spike',
    scenario: 'sudden_load',
  },
};

export function setup() {
  console.log('Setting up spike test...');
  console.log('Spike: 10 → 200 VUs in 10 seconds');

  const facultyResponse = loginFormData('faculty@example.com', 'faculty_password_123');
  const facultyToken = extractAccessToken(facultyResponse);

  return { facultyToken };
}

export default function(data) {
  const { facultyToken } = data;
  const headers = createAuthHeaders(facultyToken);

  const currentStage = Math.floor(__ITER / 100);  // Approximate stage
  const isRecovery = currentStage >= 4;  // Last stage is recovery

  const response = http.get(
    `${BASE_URL}/api/schedule/my-schedule`,
    {
      headers,
      tags: { phase: isRecovery ? 'recovery' : 'spike' },
    }
  );

  spikeRequests.add(1);

  const success = check(response, {
    'request successful': (r) => r.status === 200,
    'not rate limited': (r) => r.status !== 429,
    'not server error': (r) => r.status < 500,
  });

  if (!success) {
    spikeErrors.add(1);
  }

  if (isRecovery && success) {
    recoverySuccess.add(1);
  }

  sleep(1 + Math.random());  // Short think time during spike
}

export function teardown(data) {
  console.log('\n=== Spike Test Complete ===');
  console.log(`Total Requests: ${spikeRequests.value || 0}`);
  console.log(`Spike Error Rate: ${((spikeErrors.value / spikeRequests.value) * 100).toFixed(1)}%`);
  console.log('Check recovery metrics and system stability.');
}

/**
 * Expected behavior:
 * - Initial 10 VUs should have excellent performance
 * - Spike to 200 VUs will cause degradation
 * - System should NOT crash (graceful degradation)
 * - After spike ends, system should recover quickly
 * - Recovery phase should show normal performance
 *
 * Success criteria:
 * - No system crashes during spike
 * - Error rate < 30% during spike
 * - Recovery success rate > 95%
 * - Response times return to normal within 30 seconds of spike end
 *
 * Failure modes to watch:
 * - System crash (500 errors)
 * - Slow recovery (performance doesn't return to normal)
 * - Connection pool exhaustion
 * - Circuit breakers tripping
 */
