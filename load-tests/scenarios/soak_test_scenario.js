/**
 * Soak Test Scenario
 *
 * Long-duration test (2+ hours) to identify:
 * - Memory leaks
 * - Resource exhaustion
 * - Gradual performance degradation
 * - Database connection leaks
 * - File descriptor leaks
 *
 * Usage:
 *   k6 run soak_test_scenario.js
 *   k6 run --duration 4h soak_test_scenario.js  # Extended soak
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
const soakRequests = new Counter('soak_requests');
const soakErrors = new Counter('soak_errors');
const responseTimeBuckets = new Trend('response_time_buckets');
const memoryIndicator = new Trend('memory_indicator');  // Proxy via response times

// Test configuration - Soak test (2 hours)
export const options = {
  stages: [
    { duration: '5m', target: 30 },      // Warm up
    { duration: '2h', target: 30 },      // Soak (2 hours at steady load)
    { duration: '5m', target: 0 },       // Cool down
  ],
  thresholds: {
    // Strict thresholds - performance should not degrade
    'http_req_duration': ['p(95)<2000', 'p(99)<5000'],
    'http_req_failed': ['rate<0.01'],
    'response_time_buckets': ['p(95)<2000'],
  },
  tags: {
    test_type: 'soak',
    scenario: 'endurance',
  },
};

export function setup() {
  console.log('=' * 80);
  console.log('SOAK TEST - 2 HOUR ENDURANCE TEST');
  console.log('=' * 80);
  console.log('This test will run for 2 hours to identify memory leaks');
  console.log('and gradual performance degradation.');
  console.log();
  console.log('Monitoring checklist:');
  console.log('- Watch memory usage (should stay flat)');
  console.log('- Monitor database connections (should not grow)');
  console.log('- Check file descriptors (should be stable)');
  console.log('- Verify response times (should not increase)');
  console.log();

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
    startTime: Date.now(),
  };
}

export default function(data) {
  const { adminToken, facultyToken, residentToken, startTime } = data;

  // Simulate realistic user distribution
  const rand = Math.random();
  let token, userType;

  if (rand < 0.10) {
    token = adminToken;
    userType = 'admin';
  } else if (rand < 0.60) {
    token = facultyToken;
    userType = 'faculty';
  } else {
    token = residentToken;
    userType = 'resident';
  }

  const headers = createAuthHeaders(token);
  const elapsedMinutes = (Date.now() - startTime) / 1000 / 60;

  // Realistic user workflow
  group('Soak Test Workflow', () => {
    // View schedule
    const scheduleStart = Date.now();
    const scheduleResponse = http.get(
      `${BASE_URL}/api/schedule/my-schedule`,
      {
        headers,
        tags: { endpoint: 'schedule', user_type: userType },
      }
    );

    const scheduleTime = Date.now() - scheduleStart;
    responseTimeBuckets.add(scheduleTime);
    memoryIndicator.add(scheduleTime);  // Proxy for memory issues

    soakRequests.add(1);

    const scheduleOk = check(scheduleResponse, {
      'schedule view ok': (r) => r.status === 200,
      'response time stable': () => scheduleTime < 3000,
    });

    if (!scheduleOk) {
      soakErrors.add(1);
      console.log(`ERROR at ${elapsedMinutes.toFixed(1)} min: Schedule view failed`);
    }

    sleep(3 + Math.random() * 4);  // 3-7 seconds reading schedule

    // Faculty may view swap opportunities
    if (userType === 'faculty' && Math.random() < 0.3) {
      const swapsResponse = http.get(
        `${BASE_URL}/api/swaps/available`,
        {
          headers,
          tags: { endpoint: 'swaps', user_type: 'faculty' },
        }
      );

      soakRequests.add(1);

      check(swapsResponse, {
        'swaps view ok': (r) => r.status === 200,
      }) || soakErrors.add(1);

      sleep(2 + Math.random() * 2);
    }

    // Admins may check resilience dashboard
    if (userType === 'admin' && Math.random() < 0.2) {
      const resilienceResponse = http.get(
        `${BASE_URL}/api/resilience/dashboard`,
        {
          headers,
          tags: { endpoint: 'resilience', user_type: 'admin' },
        }
      );

      soakRequests.add(1);

      check(resilienceResponse, {
        'resilience dashboard ok': (r) => r.status === 200,
      }) || soakErrors.add(1);

      sleep(5);
    }
  });

  // Log progress every 15 minutes
  if (__ITER % 100 === 0) {
    console.log(`Soak test progress: ${elapsedMinutes.toFixed(1)} minutes elapsed`);
  }

  // Think time - realistic user behavior
  sleep(8 + Math.random() * 12);  // 8-20 seconds between workflows
}

export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000 / 60;

  console.log('\n' + '=' * 80);
  console.log('SOAK TEST COMPLETE');
  console.log('=' * 80);
  console.log(`Duration: ${duration.toFixed(1)} minutes`);
  console.log(`Total Requests: ${soakRequests.value || 0}`);
  console.log(`Total Errors: ${soakErrors.value || 0}`);
  console.log(`Error Rate: ${((soakErrors.value / soakRequests.value) * 100).toFixed(2)}%`);
  console.log();
  console.log('Post-test analysis:');
  console.log('1. Check memory usage trend (should be flat)');
  console.log('2. Verify database connection count (should not grow)');
  console.log('3. Review response time trend (should be stable)');
  console.log('4. Check for file descriptor leaks');
  console.log('5. Inspect logs for gradual degradation warnings');
  console.log('=' * 80);
}

/**
 * Expected behavior:
 * - Response times should remain constant throughout 2-hour test
 * - Memory usage should be stable (monitor via system metrics)
 * - No gradual increase in error rate
 * - Database connections should not leak
 * - File descriptors should remain stable
 *
 * Success criteria:
 * - Response times do not degrade over time
 * - Error rate < 1% throughout test
 * - Memory usage stays within 10% of starting value
 * - No resource exhaustion warnings
 * - System remains responsive after test completion
 *
 * Failure indicators:
 * - Gradual increase in response times (memory leak)
 * - Growing error rate (resource exhaustion)
 * - Database connection pool exhaustion
 * - Out of memory errors
 * - File descriptor limits reached
 *
 * Monitoring during test:
 * - Use Grafana to track memory, CPU, database connections
 * - Monitor PostgreSQL connection count
 * - Check Redis memory usage
 * - Watch Celery worker health
 * - Review application logs for warnings
 */
