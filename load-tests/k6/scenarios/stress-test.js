/**
 * Stress Test
 *
 * Push system beyond normal capacity to find breaking point.
 * Purpose: Identify system limits and failure modes.
 *
 * Run: k6 run stress-test.js
 */

import { sleep, group } from 'k6';
import { htmlReport } from 'https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js';
import { getBaseUrl } from '../config/environments.js';
import { STRESS_THRESHOLDS } from '../config/thresholds.js';
import { createAuthSession } from '../utils/auth.js';
import { httpGet, httpPost, buildUrl } from '../utils/http-helpers.js';
import { assertSuccess } from '../utils/assertions.js';
import { MetricTracker } from '../utils/metrics.js';
import {
  generatePerson,
  generateAssignment,
  generateFilterParams,
  generatePaginationParams
} from '../utils/data-generators.js';

export const options = {
  // Aggressive ramping pattern
  stages: [
    { duration: '2m', target: 20 },    // Warm up
    { duration: '5m', target: 50 },    // Ramp to normal load
    { duration: '3m', target: 100 },   // Ramp to high load
    { duration: '3m', target: 150 },   // Push harder
    { duration: '3m', target: 200 },   // Maximum stress
    { duration: '2m', target: 200 },   // Hold at max
    { duration: '5m', target: 0 }      // Gradual recovery
  ],

  // Relaxed thresholds for stress conditions
  thresholds: STRESS_THRESHOLDS,

  // Tags
  tags: {
    test_type: 'stress',
    environment: __ENV.ENVIRONMENT || 'local'
  }
};

export function setup() {
  console.log('======================================');
  console.log('STRESS TEST');
  console.log('======================================');
  console.log(`Base URL: ${getBaseUrl()}`);
  console.log('WARNING: This test will push the system hard!');
  console.log('======================================');

  return {
    baseUrl: getBaseUrl(),
    startTime: Date.now()
  };
}

export default function (data) {
  const metrics = new MetricTracker();
  const session = createAuthSession('admin');

  // Minimal think time during stress test
  const thinkTime = () => sleep(0.3);

  // Aggressive read operations
  group('Stress: Read Operations', () => {
    const operations = [
      () => session.get(buildUrl('/api/v1/assignments', generatePaginationParams())),
      () => session.get(buildUrl('/api/v1/persons', generateFilterParams())),
      () => session.get(buildUrl('/api/v1/rotations', { limit: 100 })),
      () => session.get(buildUrl('/api/v1/blocks', { limit: 100 })),
      () => session.get(buildUrl('/api/v1/swaps')),
      () => session.get(buildUrl('/api/v1/compliance/work-hours')),
      () => session.get(buildUrl('/api/v1/resilience/metrics'))
    ];

    // Execute multiple operations rapidly
    const numOps = Math.floor(Math.random() * 3) + 2;
    for (let i = 0; i < numOps; i++) {
      const op = operations[Math.floor(Math.random() * operations.length)];
      const response = op();
      metrics.trackApiResponse(response);
    }
  });

  thinkTime();

  // Write operations (less frequent but more expensive)
  if (Math.random() < 0.2) {
    group('Stress: Write Operations', () => {
      // Create person
      const personData = generatePerson('RESIDENT');
      const response = session.post(buildUrl('/api/v1/persons'), personData);

      if (response.status === 201) {
        metrics.businessMetrics.assignmentsCreated.add(1);
      }

      metrics.trackApiResponse(response);
    });

    thinkTime();
  }

  // Complex operations (compliance checks, schedule validation)
  if (Math.random() < 0.15) {
    group('Stress: Complex Operations', () => {
      const response = session.get(buildUrl('/api/v1/compliance/validate'));
      metrics.trackApiResponse(response);
    });

    thinkTime();
  }

  // Search operations
  if (Math.random() < 0.3) {
    group('Stress: Search Operations', () => {
      const queries = ['resident', 'clinic', 'call', 'emergency', 'faculty'];
      const query = queries[Math.floor(Math.random() * queries.length)];
      const response = session.get(buildUrl('/api/v1/rotations', { search: query }));
      metrics.trackApiResponse(response);
    });
  }

  // Minimal sleep - keep the pressure on
  sleep(0.1 + Math.random() * 0.2);
}

export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log('======================================');
  console.log(`Stress test completed in ${duration.toFixed(2)}s`);
  console.log('System recovery should be monitored');
  console.log('======================================');
}

export function handleSummary(data) {
  console.log('======================================');
  console.log('STRESS TEST RESULTS');
  console.log('======================================');

  const httpReqs = data.metrics.http_reqs;
  const httpReqDuration = data.metrics.http_req_duration;
  const httpReqFailed = data.metrics.http_req_failed;
  const vus = data.metrics.vus;
  const vusMax = data.metrics.vus_max;

  if (httpReqs) {
    console.log(`Total Requests: ${httpReqs.values.count}`);
    console.log(`Peak Request Rate: ${httpReqs.values.rate.toFixed(2)} req/s`);
  }

  if (httpReqFailed) {
    const failRate = httpReqFailed.values.rate * 100;
    console.log(`Failed Requests: ${failRate.toFixed(2)}%`);

    if (failRate > 10) {
      console.log('⚠️  HIGH FAILURE RATE - System stressed beyond capacity');
    } else if (failRate > 5) {
      console.log('⚠️  MODERATE FAILURE RATE - System near limits');
    }
  }

  if (httpReqDuration) {
    console.log(`\nResponse Times Under Stress:`);
    console.log(`  Avg: ${httpReqDuration.values.avg.toFixed(2)}ms`);
    console.log(`  P90: ${httpReqDuration.values['p(90)'].toFixed(2)}ms`);
    console.log(`  P95: ${httpReqDuration.values['p(95)'].toFixed(2)}ms`);
    console.log(`  P99: ${httpReqDuration.values['p(99)'].toFixed(2)}ms`);
    console.log(`  Max: ${httpReqDuration.values.max.toFixed(2)}ms`);

    if (httpReqDuration.values['p(95)'] > 2000) {
      console.log('⚠️  P95 response time exceeds 2s under stress');
    }
  }

  if (vusMax) {
    console.log(`\nPeak Virtual Users: ${vusMax.values.max}`);
  }

  console.log('======================================');

  // Analyze degradation
  console.log('\nDegradation Analysis:');

  const p95ResponseTime = httpReqDuration ? httpReqDuration.values['p(95)'] : 0;
  const failureRate = httpReqFailed ? httpReqFailed.values.rate * 100 : 0;

  if (p95ResponseTime < 1000 && failureRate < 5) {
    console.log('✅ System handled stress well - no significant degradation');
  } else if (p95ResponseTime < 2000 && failureRate < 10) {
    console.log('⚠️  Graceful degradation observed - acceptable under stress');
  } else {
    console.log('❌ Significant degradation - system near or exceeded limits');
  }

  console.log('======================================');

  return {
    'stress-test-summary.html': htmlReport(data),
    'stress-test-summary.json': JSON.stringify(data, null, 2)
  };
}
