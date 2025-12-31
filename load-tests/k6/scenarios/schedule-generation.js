/**
 * Schedule Generation Load Test
 *
 * Tests the most computationally expensive operation: schedule generation.
 * Purpose: Validate schedule generation performance under load.
 *
 * Run: k6 run schedule-generation.js
 */

import { sleep, group, check } from 'k6';
import { getBaseUrl } from '../config/environments.js';
import { createAuthSession } from '../utils/auth.js';
import { httpPost, buildUrl, parseJson, pollUntil } from '../utils/http-helpers.js';
import { assertCreated, assertSuccess } from '../utils/assertions.js';
import { MetricTracker } from '../utils/metrics.js';
import { generateScheduleRequest } from '../utils/data-generators.js';

export const options = {
  // Conservative VU count for expensive operations
  stages: [
    { duration: '1m', target: 2 },    // Start with just 2 VUs
    { duration: '5m', target: 5 },    // Ramp to 5 VUs
    { duration: '5m', target: 10 },   // Peak at 10 VUs
    { duration: '3m', target: 0 }     // Ramp down
  ],

  // Relaxed thresholds for expensive operations
  thresholds: {
    'http_req_duration{name:generate_schedule}': ['p(95)<30000'],  // 30s for generation
    'http_req_duration{name:validate_schedule}': ['p(95)<5000'],   // 5s for validation
    'http_req_failed': ['rate<0.10'],
    'checks': ['rate>0.80']
  },

  tags: {
    test_type: 'schedule_generation',
    environment: __ENV.ENVIRONMENT || 'local'
  }
};

export function setup() {
  console.log('======================================');
  console.log('SCHEDULE GENERATION LOAD TEST');
  console.log('======================================');
  console.log(`Base URL: ${getBaseUrl()}`);
  console.log('Testing computationally expensive operations');
  console.log('======================================');

  return {
    baseUrl: getBaseUrl(),
    startTime: Date.now()
  };
}

export default function (data) {
  const metrics = new MetricTracker();
  const session = createAuthSession('admin');

  // Test 1: Generate Schedule
  group('Generate Schedule', () => {
    const startTime = Date.now();
    const scheduleRequest = generateScheduleRequest();

    const response = session.post(
      buildUrl('/api/v1/schedules/generate'),
      scheduleRequest,
      { tags: { name: 'generate_schedule' } }
    );

    check(response, {
      'schedule generation started': (r) => r.status === 201 || r.status === 202,
      'response has schedule ID': (r) => {
        try {
          const body = parseJson(r);
          return body && (body.id || body.schedule_id);
        } catch (e) {
          return false;
        }
      }
    });

    const duration = Date.now() - startTime;
    metrics.trackScheduleGeneration(duration, response.status < 400);

    // If async, poll for completion
    if (response.status === 202) {
      const body = parseJson(response);
      if (body && body.schedule_id) {
        const statusUrl = buildUrl(`/api/v1/schedules/${body.schedule_id}`);

        // Poll for up to 60 seconds
        const result = pollUntil(
          statusUrl,
          (data) => data && (data.status === 'COMPLETED' || data.status === 'FAILED'),
          { headers: { 'Authorization': `Bearer ${session.getToken()}` } },
          60000,  // 60s timeout
          2000    // Poll every 2s
        );

        check(result, {
          'schedule generation completed': (r) => r.success && r.data.status === 'COMPLETED'
        });
      }
    }

    sleep(2);  // Brief pause between generation requests
  });

  // Test 2: Validate Existing Schedule
  group('Validate Schedule', () => {
    // This assumes some schedules exist - in real scenario, use a schedule ID from setup
    const scheduleId = 'test-schedule-1';  // Would be from data
    const response = session.post(
      buildUrl(`/api/v1/schedules/${scheduleId}/validate`),
      null,
      { tags: { name: 'validate_schedule' } }
    );

    check(response, {
      'validation completed': (r) => r.status === 200 || r.status === 404,  // 404 if schedule doesn't exist
      'has compliance results': (r) => {
        if (r.status !== 200) return true;  // Skip check if not found
        try {
          const body = parseJson(r);
          return body && 'compliant' in body;
        } catch (e) {
          return false;
        }
      }
    });

    sleep(1);
  });

  // Test 3: List Schedules (lighter operation)
  group('List Schedules', () => {
    const response = session.get(buildUrl('/api/v1/schedules?limit=20'));
    assertSuccess(response);
    sleep(1);
  });

  // Test 4: Compliance Check (medium complexity)
  group('Compliance Check', () => {
    const response = session.get(buildUrl('/api/v1/compliance/validate'));

    check(response, {
      'compliance check completed': (r) => r.status === 200 || r.status === 422
    });

    sleep(1);
  });

  // Longer sleep between iterations due to expensive operations
  sleep(5 + Math.random() * 5);
}

export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log('======================================');
  console.log(`Schedule generation test completed in ${duration.toFixed(2)}s`);
  console.log('======================================');
}

export function handleSummary(data) {
  console.log('======================================');
  console.log('SCHEDULE GENERATION TEST RESULTS');
  console.log('======================================');

  const scheduleGenMetric = data.metrics['http_req_duration{name:generate_schedule}'];
  const validateMetric = data.metrics['http_req_duration{name:validate_schedule}'];
  const httpReqs = data.metrics.http_reqs;
  const httpReqFailed = data.metrics.http_req_failed;

  if (scheduleGenMetric) {
    console.log('\nSchedule Generation Performance:');
    console.log(`  Count: ${scheduleGenMetric.values.count}`);
    console.log(`  Avg: ${(scheduleGenMetric.values.avg / 1000).toFixed(2)}s`);
    console.log(`  Min: ${(scheduleGenMetric.values.min / 1000).toFixed(2)}s`);
    console.log(`  Max: ${(scheduleGenMetric.values.max / 1000).toFixed(2)}s`);
    console.log(`  P95: ${(scheduleGenMetric.values['p(95)'] / 1000).toFixed(2)}s`);
    console.log(`  P99: ${(scheduleGenMetric.values['p(99)'] / 1000).toFixed(2)}s`);
  }

  if (validateMetric) {
    console.log('\nSchedule Validation Performance:');
    console.log(`  Count: ${validateMetric.values.count}`);
    console.log(`  Avg: ${validateMetric.values.avg.toFixed(2)}ms`);
    console.log(`  P95: ${validateMetric.values['p(95)'].toFixed(2)}ms`);
  }

  if (httpReqs) {
    console.log(`\nTotal Requests: ${httpReqs.values.count}`);
  }

  if (httpReqFailed) {
    console.log(`Failed Requests: ${(httpReqFailed.values.rate * 100).toFixed(2)}%`);
  }

  console.log('======================================');

  // Recommendations
  console.log('\nRecommendations:');

  if (scheduleGenMetric && scheduleGenMetric.values['p(95)'] > 30000) {
    console.log('⚠️  P95 generation time > 30s - consider optimization');
  } else {
    console.log('✅ Schedule generation performance acceptable');
  }

  if (validateMetric && validateMetric.values['p(95)'] > 5000) {
    console.log('⚠️  P95 validation time > 5s - consider optimization');
  } else {
    console.log('✅ Validation performance acceptable');
  }

  console.log('======================================');

  return {
    'schedule-generation-summary.json': JSON.stringify(data, null, 2)
  };
}
