/**
 * Concurrent Users Load Test
 *
 * Simulates realistic multi-user patterns with mixed operations.
 * Models coordinators viewing schedules, faculty checking assignments,
 * residents viewing their schedules, etc.
 *
 * Usage:
 *   k6 run concurrent-users.js
 *   k6 run --env BASE_URL=http://api.example.com concurrent-users.js
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
import {
  generateAssignmentFilters,
  generatePersonFilters,
  generateBlockFilters,
  generatePagination,
  toQueryString,
  thinkTime,
  randomElement,
} from '../utils/data-generators.js';

// Custom metrics
const readOperations = new Counter('read_operations');
const writeOperations = new Counter('write_operations');
const cacheHits = new Rate('cache_hits');
const authErrors = new Counter('auth_errors');
const apiLatency = new Trend('api_latency', true);

// Test configuration
export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Warm-up: 10 users
    { duration: '3m', target: 50 },   // Ramp to 50 concurrent users
    { duration: '5m', target: 100 },  // Peak: 100 concurrent users
    { duration: '3m', target: 50 },   // Ramp down to 50
    { duration: '2m', target: 10 },   // Ramp down to 10
    { duration: '1m', target: 0 },    // Cooldown
  ],
  thresholds: {
    // API should be responsive under load
    'http_req_duration': ['p(95)<2000', 'p(99)<5000'],

    // Most requests should succeed
    'http_req_failed': ['rate<0.01'],

    // Check success rate
    'checks': ['rate>0.95'],

    // API latency for different endpoints
    'api_latency': ['p(95)<2000', 'p(99)<5000'],
  },
  tags: {
    test_type: 'load',
    scenario: 'concurrent_users',
  },
};

// Setup: Authenticate all user types
export function setup() {
  console.log('Setting up concurrent users test...');
  console.log(`Target URL: ${BASE_URL}`);

  // Authenticate different user roles
  const userCredentials = [
    { role: 'admin', email: 'admin@example.com', password: 'admin_password_123' },
    { role: 'coordinator', email: 'coordinator@example.com', password: 'coordinator_pass_123' },
    { role: 'faculty', email: 'faculty@example.com', password: 'faculty_pass_123' },
    { role: 'resident', email: 'resident@example.com', password: 'resident_pass_123' },
  ];

  const sessions = {};
  for (const user of userCredentials) {
    const response = loginFormData(user.email, user.password);
    const token = extractAccessToken(response);

    if (token && validateLoginSuccess(response)) {
      sessions[user.role] = token;
      console.log(`✓ Authenticated ${user.role}`);
    } else {
      console.warn(`✗ Failed to authenticate ${user.role}`);
    }
  }

  if (Object.keys(sessions).length === 0) {
    throw new Error('Failed to create any user sessions. Cannot proceed with test.');
  }

  console.log(`Created ${Object.keys(sessions).length} user sessions:`, Object.keys(sessions));
  return { sessions };
}

// User behavior scenarios
const scenarios = {
  // Coordinator: Views schedules, manages assignments
  coordinator: (headers) => {
    // View assignments with filters
    const assignmentFilters = generateAssignmentFilters();
    const assignmentQuery = toQueryString({ ...assignmentFilters, ...generatePagination() });

    let response = http.get(
      `${BASE_URL}/api/assignments${assignmentQuery}`,
      {
        headers,
        tags: { name: 'list_assignments', role: 'coordinator' },
      }
    );

    check(response, {
      'assignments loaded': (r) => r.status === 200,
      'has assignments array': (r) => {
        try {
          return Array.isArray(JSON.parse(r.body).assignments || JSON.parse(r.body));
        } catch {
          return false;
        }
      },
    }) && readOperations.add(1);

    sleep(thinkTime(1, 3));

    // View persons list
    const personFilters = generatePersonFilters();
    const personQuery = toQueryString({ ...personFilters, ...generatePagination() });

    response = http.get(
      `${BASE_URL}/api/persons${personQuery}`,
      {
        headers,
        tags: { name: 'list_persons', role: 'coordinator' },
      }
    );

    check(response, {
      'persons loaded': (r) => r.status === 200,
    }) && readOperations.add(1);

    sleep(thinkTime(2, 4));
  },

  // Faculty: Checks own assignments, views schedule
  faculty: (headers) => {
    // View own assignments
    let response = http.get(
      `${BASE_URL}/api/assignments/me`,
      {
        headers,
        tags: { name: 'my_assignments', role: 'faculty' },
      }
    );

    check(response, {
      'my assignments loaded': (r) => r.status === 200,
    }) && readOperations.add(1);

    sleep(thinkTime(1, 2));

    // View upcoming blocks
    const blockFilters = generateBlockFilters();
    const blockQuery = toQueryString({ ...blockFilters, limit: 20 });

    response = http.get(
      `${BASE_URL}/api/blocks${blockQuery}`,
      {
        headers,
        tags: { name: 'list_blocks', role: 'faculty' },
      }
    );

    check(response, {
      'blocks loaded': (r) => r.status === 200,
    }) && readOperations.add(1);

    sleep(thinkTime(2, 5));
  },

  // Resident: Views schedule, checks assignments
  resident: (headers) => {
    // View own schedule
    let response = http.get(
      `${BASE_URL}/api/assignments/me`,
      {
        headers,
        tags: { name: 'my_assignments', role: 'resident' },
      }
    );

    check(response, {
      'my schedule loaded': (r) => r.status === 200,
    }) && readOperations.add(1);

    sleep(thinkTime(1, 3));

    // Check specific block details (if we got assignments)
    if (response.status === 200) {
      try {
        const assignments = JSON.parse(response.body);
        if (assignments.length > 0) {
          const randomAssignment = randomElement(assignments);
          if (randomAssignment.block_id) {
            response = http.get(
              `${BASE_URL}/api/blocks/${randomAssignment.block_id}`,
              {
                headers,
                tags: { name: 'get_block', role: 'resident' },
              }
            );

            check(response, {
              'block details loaded': (r) => r.status === 200,
            }) && readOperations.add(1);
          }
        }
      } catch (e) {
        // Ignore parsing errors
      }
    }

    sleep(thinkTime(3, 6));
  },

  // Admin: Overview of system, checks multiple resources
  admin: (headers) => {
    // Dashboard-style data fetching
    const requests = [
      {
        method: 'GET',
        url: `${BASE_URL}/api/assignments${toQueryString(generatePagination())}`,
        params: { headers, tags: { name: 'list_assignments', role: 'admin' } },
      },
      {
        method: 'GET',
        url: `${BASE_URL}/api/persons${toQueryString({ limit: 50 })}`,
        params: { headers, tags: { name: 'list_persons', role: 'admin' } },
      },
      {
        method: 'GET',
        url: `${BASE_URL}/api/blocks${toQueryString({ limit: 50 })}`,
        params: { headers, tags: { name: 'list_blocks', role: 'admin' } },
      },
    ];

    // Parallel requests (dashboard loads multiple resources)
    const responses = http.batch(requests);

    responses.forEach((response, index) => {
      check(response, {
        'resource loaded': (r) => r.status === 200,
      }) && readOperations.add(1);
    });

    sleep(thinkTime(2, 4));

    // Check system health
    const healthResponse = http.get(
      `${BASE_URL}/health`,
      {
        tags: { name: 'health_check', role: 'admin' },
      }
    );

    check(healthResponse, {
      'system healthy': (r) => r.status === 200,
    });

    sleep(thinkTime(3, 5));
  },
};

// Main test function
export default function(data) {
  const { sessions } = data;

  // Randomly select a user role to simulate
  const roles = Object.keys(sessions);
  const role = randomElement(roles);
  const token = sessions[role];
  const headers = createAuthHeaders(token);

  // Track API latency
  const startTime = Date.now();

  try {
    // Execute behavior pattern for this role
    if (scenarios[role]) {
      scenarios[role](headers);
    } else {
      // Fallback: basic read operations
      const response = http.get(
        `${BASE_URL}/api/assignments/me`,
        {
          headers,
          tags: { name: 'my_assignments', role },
        }
      );

      check(response, {
        'request successful': (r) => r.status === 200,
      });
    }

    const duration = Date.now() - startTime;
    apiLatency.add(duration);

  } catch (error) {
    console.error(`Error in ${role} scenario: ${error.message}`);
    authErrors.add(1);
  }

  // Think time between user sessions
  sleep(thinkTime(1, 3));
}

// Teardown: Log statistics
export function teardown(data) {
  console.log('\n=== Concurrent Users Load Test Complete ===');
  console.log(`Total read operations: ${readOperations.value || 0}`);
  console.log(`Total write operations: ${writeOperations.value || 0}`);
  console.log(`Auth errors: ${authErrors.value || 0}`);
  console.log('Check Grafana dashboard for detailed metrics and trends.');
}

/**
 * Test scenarios and expected behavior:
 *
 * Coordinator:
 * - Views filtered assignment lists (high volume)
 * - Manages person records
 * - Moderate read frequency
 *
 * Faculty:
 * - Checks own assignments frequently
 * - Views upcoming blocks
 * - High read frequency, low write
 *
 * Resident:
 * - Views own schedule (highest frequency)
 * - Checks block details
 * - Very high read frequency
 *
 * Admin:
 * - Dashboard with multiple resources
 * - System health monitoring
 * - Batch requests for efficiency
 *
 * Success criteria:
 * - p95 latency < 2s under 100 concurrent users
 * - Error rate < 1%
 * - System remains responsive
 * - No authentication issues
 *
 * Performance optimizations to validate:
 * - Database query optimization
 * - Redis caching effectiveness
 * - Connection pool sizing
 * - Rate limiting tolerance
 */
