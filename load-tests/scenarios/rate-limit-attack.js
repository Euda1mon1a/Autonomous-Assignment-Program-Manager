/**
 * Rate Limiting Attack Simulation for k6
 *
 * Tests rate limiting effectiveness under various attack scenarios:
 * 1. Brute force login attempts (should trigger after 5 attempts)
 * 2. API flooding (should trigger at 30 req/s)
 * 3. Schedule generation spam (should trigger at 1 req/10s)
 * 4. Distributed attack simulation (multiple IPs)
 *
 * Rate Limits (from nginx.conf):
 * - Login: 5 requests per minute per IP
 * - API: 30 requests per second per IP
 * - Schedule Generation: 1 request per 10 seconds per IP
 *
 * Usage:
 *   k6 run load-tests/scenarios/rate-limit-attack.js
 *   K6_BASE_URL=https://api.example.com k6 run load-tests/scenarios/rate-limit-attack.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import {
    BASE_URL,
    loginJSON,
    validateRateLimitResponse,
    extractAccessToken,
    authenticatedRequest,
    DEFAULT_TEST_USER,
} from '../utils/auth.js';

// ============================================================================
// Custom Metrics
// ============================================================================
const rateLimitTriggers = new Counter('rate_limit_triggers');
const blockedRequests = new Counter('blocked_requests');
const legitimateAfterCooldown = new Counter('legitimate_after_cooldown');
const rateLimitResponseTime = new Trend('rate_limit_response_time');
const serverErrors = new Counter('server_errors');
const requestsUntilLimit = new Trend('requests_until_limit');

// ============================================================================
// Test Configuration
// ============================================================================
export const options = {
    scenarios: {
        // Scenario 1: Brute Force Login Attack
        bruteForceLogin: {
            executor: 'per-vu-iterations',
            vus: 1,
            iterations: 15, // Exceed the 5/min limit
            maxDuration: '30s',
            startTime: '0s',
            tags: { scenario: 'brute_force_login' },
        },

        // Scenario 2: API Flooding Attack
        apiFlood: {
            executor: 'constant-arrival-rate',
            rate: 50, // 50 requests per second (exceeds 30 req/s limit)
            timeUnit: '1s',
            duration: '10s',
            preAllocatedVUs: 10,
            maxVUs: 20,
            startTime: '35s', // Start after brute force test
            tags: { scenario: 'api_flood' },
        },

        // Scenario 3: Schedule Generation Spam
        scheduleGenSpam: {
            executor: 'per-vu-iterations',
            vus: 1,
            iterations: 5, // Rapid fire attempts
            maxDuration: '15s',
            startTime: '50s', // Start after API flood
            tags: { scenario: 'schedule_gen_spam' },
        },

        // Scenario 4: Distributed Attack Simulation
        distributedAttack: {
            executor: 'ramping-arrival-rate',
            startRate: 10,
            timeUnit: '1s',
            preAllocatedVUs: 20,
            maxVUs: 50,
            stages: [
                { duration: '10s', target: 60 }, // Ramp up to 60 req/s
                { duration: '10s', target: 60 }, // Sustain
                { duration: '10s', target: 0 },  // Ramp down
            ],
            startTime: '70s',
            tags: { scenario: 'distributed_attack' },
        },
    },

    thresholds: {
        // Rate limiting should trigger within acceptable bounds
        'rate_limit_triggers': ['count>0'], // Should trigger at least once
        'requests_until_limit': ['p95<15'], // Should trigger within 15 requests over limit
        'rate_limit_response_time': ['p95<50'], // 429 responses should be < 50ms
        'server_errors': ['count==0'], // No 5xx errors during rate limiting
        'http_req_failed{scenario:brute_force_login}': ['rate<0.9'], // Some requests should succeed initially
        'http_req_failed{scenario:api_flood}': ['rate>0.3'], // Significant blocking expected
        'legitimate_after_cooldown': ['count>0'], // Legitimate requests should succeed after cooldown
    },
};

// ============================================================================
// Rate Limit Configuration (environment variable overrides)
// ============================================================================
const RATE_LIMITS = {
    login: {
        max: parseInt(__ENV.LOGIN_RATE_LIMIT || '5'),
        window: parseInt(__ENV.LOGIN_WINDOW_SECONDS || '60'),
    },
    api: {
        max: parseInt(__ENV.API_RATE_LIMIT || '30'),
        window: parseInt(__ENV.API_WINDOW_SECONDS || '1'),
    },
    scheduleGen: {
        max: parseInt(__ENV.SCHEDULE_GEN_RATE_LIMIT || '1'),
        window: parseInt(__ENV.SCHEDULE_GEN_WINDOW_SECONDS || '10'),
    },
};

// ============================================================================
// Scenario 1: Brute Force Login Attack
// ============================================================================
export function bruteForceLogin() {
    const startTime = Date.now();
    let requestCount = 0;
    let limitTriggered = false;

    console.log('[BRUTE_FORCE] Starting brute force login attack simulation');

    // Attempt rapid login requests with invalid credentials
    for (let i = 0; i < 15; i++) {
        requestCount++;
        const response = loginJSON(
            'attacker@malicious.com',
            'WrongPassword123',
            { tags: { attack_type: 'brute_force' } }
        );

        // Track response
        if (response.status === 429) {
            rateLimitTriggers.add(1);
            blockedRequests.add(1);
            rateLimitResponseTime.add(response.timings.duration);

            if (!limitTriggered) {
                limitTriggered = true;
                requestsUntilLimit.add(requestCount);
                console.log(`[BRUTE_FORCE] Rate limit triggered after ${requestCount} requests`);
            }

            // Validate rate limit response
            validateRateLimitResponse(response);
        } else if (response.status >= 500) {
            serverErrors.add(1);
            console.error(`[BRUTE_FORCE] Server error: ${response.status}`);
        }

        // Check for proper rate limit headers
        check(response, {
            'no server errors during brute force': (r) => r.status < 500,
            'rate limit or auth error': (r) => r.status === 429 || r.status === 401,
        });

        // Small delay between attempts (realistic brute force)
        sleep(0.1);
    }

    // Wait for rate limit window to expire
    const cooldownTime = RATE_LIMITS.login.window + 5; // Add 5s buffer
    console.log(`[BRUTE_FORCE] Waiting ${cooldownTime}s for rate limit cooldown`);
    sleep(cooldownTime);

    // Test legitimate request after cooldown
    console.log('[BRUTE_FORCE] Testing legitimate request after cooldown');
    const legitResponse = loginJSON(
        DEFAULT_TEST_USER.username,
        DEFAULT_TEST_USER.password,
        { tags: { attack_type: 'legitimate_after_cooldown' } }
    );

    if (legitResponse.status === 200) {
        legitimateAfterCooldown.add(1);
        console.log('[BRUTE_FORCE] ✓ Legitimate request succeeded after cooldown');
    } else {
        console.error(`[BRUTE_FORCE] ✗ Legitimate request failed: ${legitResponse.status}`);
    }

    check(legitResponse, {
        'legitimate request succeeds after cooldown': (r) => r.status === 200,
    });
}

// ============================================================================
// Scenario 2: API Flooding Attack
// ============================================================================
export function apiFlood() {
    // First, get a valid token
    const loginResponse = loginJSON(
        DEFAULT_TEST_USER.username,
        DEFAULT_TEST_USER.password
    );

    const token = extractAccessToken(loginResponse);
    if (!token) {
        console.error('[API_FLOOD] Failed to obtain authentication token');
        return;
    }

    // Flood API with requests (GET /api/persons is a common endpoint)
    const response = authenticatedRequest(
        'GET',
        '/api/persons',
        token,
        null,
        { tags: { attack_type: 'api_flood' } }
    );

    // Track rate limiting
    if (response.status === 429) {
        rateLimitTriggers.add(1);
        blockedRequests.add(1);
        rateLimitResponseTime.add(response.timings.duration);
        validateRateLimitResponse(response);
    } else if (response.status >= 500) {
        serverErrors.add(1);
    }

    check(response, {
        'api flood: no server errors': (r) => r.status < 500,
        'api flood: rate limited or successful': (r) => r.status === 200 || r.status === 429,
    });
}

// ============================================================================
// Scenario 3: Schedule Generation Spam
// ============================================================================
export function scheduleGenSpam() {
    // First, get a valid admin token
    const loginResponse = loginJSON(
        DEFAULT_TEST_USER.username,
        DEFAULT_TEST_USER.password
    );

    const token = extractAccessToken(loginResponse);
    if (!token) {
        console.error('[SCHEDULE_SPAM] Failed to obtain authentication token');
        return;
    }

    console.log('[SCHEDULE_SPAM] Attempting rapid schedule generation requests');

    // Attempt rapid schedule generation (should be blocked after 1 request per 10s)
    for (let i = 0; i < 5; i++) {
        const response = authenticatedRequest(
            'POST',
            '/api/schedule/generate',
            token,
            {
                start_date: '2024-07-01',
                end_date: '2024-12-31',
            },
            { tags: { attack_type: 'schedule_spam' } }
        );

        // Track response
        if (response.status === 429) {
            rateLimitTriggers.add(1);
            blockedRequests.add(1);
            rateLimitResponseTime.add(response.timings.duration);
            console.log(`[SCHEDULE_SPAM] Request ${i + 1} rate limited (expected)`);
            validateRateLimitResponse(response);
        } else if (response.status >= 500) {
            serverErrors.add(1);
        } else if (response.status === 200 || response.status === 202) {
            console.log(`[SCHEDULE_SPAM] Request ${i + 1} accepted`);
        }

        check(response, {
            'schedule spam: no server errors': (r) => r.status < 500,
            'schedule spam: rate limited or accepted': (r) =>
                r.status === 200 || r.status === 202 || r.status === 429 || r.status === 400,
        });

        // No delay - testing rapid fire
    }
}

// ============================================================================
// Scenario 4: Distributed Attack Simulation
// ============================================================================
export function distributedAttack() {
    // Simulate distributed attack by making varied API requests
    // In a real distributed attack, requests would come from different IPs
    // Here we simulate with different endpoints

    const endpoints = [
        '/api/persons',
        '/api/blocks',
        '/api/assignments',
        '/api/rotations',
        '/health',
    ];

    const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];

    // Some requests with auth, some without (mixed attack)
    const useAuth = Math.random() > 0.5;
    let response;

    if (useAuth) {
        // First get token (this itself might be rate limited)
        const loginResponse = loginJSON(
            DEFAULT_TEST_USER.username,
            DEFAULT_TEST_USER.password
        );

        const token = extractAccessToken(loginResponse);
        if (token) {
            response = authenticatedRequest(
                'GET',
                endpoint,
                token,
                null,
                { tags: { attack_type: 'distributed_auth' } }
            );
        } else {
            response = loginResponse;
        }
    } else {
        // Unauthenticated request
        response = http.get(
            `${BASE_URL}${endpoint}`,
            { tags: { attack_type: 'distributed_unauth' } }
        );
    }

    // Track metrics
    if (response.status === 429) {
        rateLimitTriggers.add(1);
        blockedRequests.add(1);
        rateLimitResponseTime.add(response.timings.duration);
    } else if (response.status >= 500) {
        serverErrors.add(1);
    }

    check(response, {
        'distributed attack: no server errors': (r) => r.status < 500,
    });
}

// ============================================================================
// Main Execution Function (selects appropriate scenario)
// ============================================================================
export default function () {
    const scenario = __ENV.SCENARIO || __ITER;

    // Route to appropriate scenario based on k6 scenario executor
    if (__VU <= 1 && scenario === 0) {
        // This is a fallback for single-scenario execution
        bruteForceLogin();
    }
    // Otherwise, k6's scenario executors will call the appropriate functions
}

// ============================================================================
// Setup Function (runs once before test)
// ============================================================================
export function setup() {
    console.log('='.repeat(80));
    console.log('RATE LIMITING ATTACK SIMULATION');
    console.log('='.repeat(80));
    console.log(`Base URL: ${BASE_URL}`);
    console.log('\nConfigured Rate Limits:');
    console.log(`  Login:              ${RATE_LIMITS.login.max} requests per ${RATE_LIMITS.login.window}s`);
    console.log(`  API:                ${RATE_LIMITS.api.max} requests per ${RATE_LIMITS.api.window}s`);
    console.log(`  Schedule Generation: ${RATE_LIMITS.scheduleGen.max} requests per ${RATE_LIMITS.scheduleGen.window}s`);
    console.log('='.repeat(80));
    console.log('\nTest Scenarios:');
    console.log('  1. Brute Force Login (0-35s)');
    console.log('  2. API Flooding (35-50s)');
    console.log('  3. Schedule Gen Spam (50-70s)');
    console.log('  4. Distributed Attack (70-100s)');
    console.log('='.repeat(80));
    console.log('');

    return {
        startTime: Date.now(),
    };
}

// ============================================================================
// Teardown Function (runs once after test)
// ============================================================================
export function teardown(data) {
    const duration = (Date.now() - data.startTime) / 1000;

    console.log('');
    console.log('='.repeat(80));
    console.log('RATE LIMITING TEST COMPLETE');
    console.log('='.repeat(80));
    console.log(`Total Duration: ${duration.toFixed(2)}s`);
    console.log('');
    console.log('Check the metrics output for:');
    console.log('  - rate_limit_triggers: Number of times rate limiting was triggered');
    console.log('  - blocked_requests: Number of requests blocked by rate limiting');
    console.log('  - requests_until_limit: How many requests until rate limit kicked in');
    console.log('  - rate_limit_response_time: Response time for 429 responses');
    console.log('  - server_errors: Should be 0 (no 5xx errors)');
    console.log('  - legitimate_after_cooldown: Legitimate requests after cooldown');
    console.log('='.repeat(80));
}
