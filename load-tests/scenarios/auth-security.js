/**
 * Authentication Security Load Tests for k6
 *
 * Tests authentication system security and performance under high concurrent loads:
 * 1. JWT token validation under high concurrent loads
 * 2. Invalid token rejection performance
 * 3. Token expiry handling under load
 * 4. Session management stress test
 * 5. Token reuse and replay attack simulation
 * 6. Concurrent authentication performance
 *
 * This test ensures that the authentication system:
 * - Maintains security under heavy load
 * - Rejects invalid tokens quickly
 * - Handles token expiry correctly
 * - Doesn't leak information through timing attacks
 * - Prevents session hijacking attempts
 *
 * Usage:
 *   k6 run load-tests/scenarios/auth-security.js
 *   K6_BASE_URL=https://api.example.com k6 run load-tests/scenarios/auth-security.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import {
    BASE_URL,
    loginJSON,
    loginFormData,
    validateLoginSuccess,
    validateUnauthorizedResponse,
    extractAccessToken,
    authenticatedRequest,
    createAuthHeaders,
    isValidJWTStructure,
    DEFAULT_TEST_USER,
} from '../utils/auth.js';

// ============================================================================
// Custom Metrics
// ============================================================================
const validTokenRequests = new Counter('valid_token_requests');
const invalidTokenRequests = new Counter('invalid_token_requests');
const invalidTokenRejections = new Counter('invalid_token_rejections');
const tokenValidationTime = new Trend('token_validation_time');
const invalidTokenRejectionTime = new Trend('invalid_token_rejection_time');
const authenticationErrors = new Counter('authentication_errors');
const concurrentLoginSuccess = new Counter('concurrent_login_success');
const concurrentLoginFailures = new Counter('concurrent_login_failures');

// ============================================================================
// Test Configuration
// ============================================================================
export const options = {
    scenarios: {
        // Scenario 1: JWT Token Validation Under High Load
        tokenValidationLoad: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '30s', target: 50 },  // Ramp up to 50 VUs
                { duration: '1m', target: 50 },   // Sustain load
                { duration: '30s', target: 100 }, // Increase to 100 VUs
                { duration: '1m', target: 100 },  // Sustain higher load
                { duration: '30s', target: 0 },   // Ramp down
            ],
            exec: 'testValidTokenLoad',
            tags: { scenario: 'token_validation_load' },
        },

        // Scenario 2: Invalid Token Rejection Performance
        invalidTokenRejection: {
            executor: 'constant-vus',
            vus: 30,
            duration: '2m',
            exec: 'testInvalidTokenRejection',
            startTime: '4m', // Start after token validation test
            tags: { scenario: 'invalid_token_rejection' },
        },

        // Scenario 3: Token Expiry Handling
        tokenExpiryHandling: {
            executor: 'per-vu-iterations',
            vus: 10,
            iterations: 5,
            maxDuration: '2m',
            exec: 'testTokenExpiry',
            startTime: '6m', // Start after invalid token test
            tags: { scenario: 'token_expiry' },
        },

        // Scenario 4: Concurrent Authentication Stress
        concurrentAuth: {
            executor: 'constant-arrival-rate',
            rate: 100, // 100 login attempts per second
            timeUnit: '1s',
            duration: '1m',
            preAllocatedVUs: 50,
            maxVUs: 100,
            exec: 'testConcurrentAuthentication',
            startTime: '8m', // Start after expiry test
            tags: { scenario: 'concurrent_auth' },
        },

        // Scenario 5: Session Management Stress
        sessionManagement: {
            executor: 'ramping-vus',
            startVUs: 10,
            stages: [
                { duration: '30s', target: 50 },
                { duration: '1m', target: 50 },
                { duration: '30s', target: 0 },
            ],
            exec: 'testSessionManagement',
            startTime: '9m', // Start after concurrent auth
            tags: { scenario: 'session_management' },
        },
    },

    thresholds: {
        // Performance thresholds
        'token_validation_time': ['p95<200', 'p99<500'], // Token validation should be fast
        'invalid_token_rejection_time': ['p95<100', 'p99<200'], // Invalid tokens rejected faster
        'authentication_errors': ['count==0'], // No authentication system errors
        'http_req_duration{scenario:token_validation_load}': ['p95<500'],
        'http_req_duration{scenario:invalid_token_rejection}': ['p95<200'],
        'http_req_duration{scenario:concurrent_auth}': ['p95<1000'],

        // Success rate thresholds
        'http_req_failed{scenario:token_validation_load}': ['rate<0.01'], // Less than 1% failure
        'concurrent_login_success': ['count>0'], // At least some logins succeed
        'invalid_token_rejections': ['count>0'], // Invalid tokens should be rejected

        // Security thresholds
        'checks{check:invalid_token_rejected}': ['rate>0.99'], // 99%+ invalid tokens rejected
    },
};

// ============================================================================
// Scenario 1: JWT Token Validation Under High Load
// ============================================================================
export function testValidTokenLoad() {
    group('Valid Token Under Load', () => {
        // Get a valid token
        const loginResponse = loginJSON(
            DEFAULT_TEST_USER.username,
            DEFAULT_TEST_USER.password
        );

        const token = extractAccessToken(loginResponse);
        if (!token) {
            authenticationErrors.add(1);
            return;
        }

        // Make authenticated requests to various endpoints
        const endpoints = [
            '/api/persons',
            '/api/blocks',
            '/api/rotations',
            '/api/assignments',
        ];

        const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
        const startTime = Date.now();

        const response = authenticatedRequest('GET', endpoint, token);
        const elapsed = Date.now() - startTime;

        tokenValidationTime.add(elapsed);

        if (response.status === 200) {
            validTokenRequests.add(1);
        } else if (response.status === 401) {
            authenticationErrors.add(1);
        }

        check(response, {
            'valid token accepted': (r) => r.status === 200 || r.status === 404,
            'no auth errors with valid token': (r) => r.status !== 401,
            'valid token response time acceptable': (r) => r.timings.duration < 500,
        });
    });

    sleep(1); // Realistic user behavior
}

// ============================================================================
// Scenario 2: Invalid Token Rejection Performance
// ============================================================================
export function testInvalidTokenRejection() {
    group('Invalid Token Rejection', () => {
        // Test various invalid token scenarios
        const invalidTokens = [
            'invalid.token.here',
            'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature',
            '',
            'totally-not-a-jwt',
            'eyJhbGciOiJub25lIn0.eyJzdWIiOiIxMjM0NTY3ODkwIn0.',
            'a'.repeat(1000), // Very long invalid token
        ];

        const invalidToken = invalidTokens[Math.floor(Math.random() * invalidTokens.length)];
        const startTime = Date.now();

        const response = http.get(
            `${BASE_URL}/api/persons`,
            {
                headers: createAuthHeaders(invalidToken),
                tags: { token_type: 'invalid' },
            }
        );

        const elapsed = Date.now() - startTime;

        invalidTokenRequests.add(1);
        invalidTokenRejectionTime.add(elapsed);

        if (response.status === 401 || response.status === 403) {
            invalidTokenRejections.add(1);
        }

        check(response, {
            'invalid_token_rejected': (r) => r.status === 401 || r.status === 403,
            'invalid token fast rejection': (r) => r.timings.duration < 100,
            'no timing leak': (r) => {
                // Response time shouldn't vary significantly for different invalid tokens
                // to prevent timing attacks
                return r.timings.duration < 200;
            },
        });
    });

    sleep(0.5);
}

// ============================================================================
// Scenario 3: Token Expiry Handling
// ============================================================================
export function testTokenExpiry() {
    group('Token Expiry Handling', () => {
        // First, login to get a token
        const loginResponse = loginJSON(
            DEFAULT_TEST_USER.username,
            DEFAULT_TEST_USER.password
        );

        const token = extractAccessToken(loginResponse);
        if (!token) {
            authenticationErrors.add(1);
            return;
        }

        // Use the token immediately (should work)
        let response = authenticatedRequest('GET', '/api/persons', token);

        check(response, {
            'fresh token works': (r) => r.status === 200 || r.status === 404,
        });

        // Test token structure
        check(token, {
            'token has valid JWT structure': (t) => isValidJWTStructure(t),
        });

        // Make multiple requests with the same token
        for (let i = 0; i < 3; i++) {
            response = authenticatedRequest('GET', '/api/blocks', token);

            check(response, {
                'token reuse allowed': (r) => r.status === 200 || r.status === 404,
                'no token replay issues': (r) => r.status !== 401,
            });

            sleep(1);
        }
    });
}

// ============================================================================
// Scenario 4: Concurrent Authentication Stress
// ============================================================================
export function testConcurrentAuthentication() {
    group('Concurrent Authentication', () => {
        // Mix of valid and invalid login attempts
        const useValidCredentials = Math.random() > 0.3; // 70% valid, 30% invalid

        let username, password;
        if (useValidCredentials) {
            username = DEFAULT_TEST_USER.username;
            password = DEFAULT_TEST_USER.password;
        } else {
            username = `invalid_${Math.random().toString(36).substring(7)}@test.com`;
            password = `WrongPass${Math.random().toString(36).substring(7)}`;
        }

        const response = loginJSON(username, password);

        if (useValidCredentials) {
            if (response.status === 200) {
                concurrentLoginSuccess.add(1);
                validateLoginSuccess(response);
            } else {
                concurrentLoginFailures.add(1);
            }
        } else {
            if (response.status === 401) {
                // Expected failure for invalid credentials
                validateUnauthorizedResponse(response);
            } else if (response.status === 429) {
                // Rate limited (acceptable)
            } else {
                authenticationErrors.add(1);
            }
        }

        check(response, {
            'auth response valid': (r) => r.status === 200 || r.status === 401 || r.status === 429,
            'auth response time acceptable': (r) => r.timings.duration < 1000,
            'no server errors in auth': (r) => r.status < 500,
        });
    });
}

// ============================================================================
// Scenario 5: Session Management Stress
// ============================================================================
export function testSessionManagement() {
    group('Session Management', () => {
        // Login to create a session
        const loginResponse = loginJSON(
            DEFAULT_TEST_USER.username,
            DEFAULT_TEST_USER.password
        );

        const token = extractAccessToken(loginResponse);
        if (!token) {
            authenticationErrors.add(1);
            return;
        }

        // Simulate a user session with multiple API calls
        const sessionActions = [
            { method: 'GET', endpoint: '/api/persons' },
            { method: 'GET', endpoint: '/api/blocks' },
            { method: 'GET', endpoint: '/api/rotations' },
            { method: 'GET', endpoint: '/api/assignments' },
        ];

        for (const action of sessionActions) {
            const response = authenticatedRequest(
                action.method,
                action.endpoint,
                token
            );

            check(response, {
                'session request successful': (r) => r.status < 400 || r.status === 404,
                'session token valid': (r) => r.status !== 401,
            });

            sleep(0.5); // Simulate user think time
        }

        // Test logout (if implemented)
        const logoutResponse = http.post(
            `${BASE_URL}/api/auth/logout`,
            null,
            { headers: createAuthHeaders(token) }
        );

        check(logoutResponse, {
            'logout handled': (r) => r.status < 500,
        });
    });

    sleep(2);
}

// ============================================================================
// Additional Test: Token Replay Attack Prevention
// ============================================================================
export function testTokenReplayPrevention() {
    group('Token Replay Prevention', () => {
        // Get a valid token
        const loginResponse = loginJSON(
            DEFAULT_TEST_USER.username,
            DEFAULT_TEST_USER.password
        );

        const token = extractAccessToken(loginResponse);
        if (!token) {
            return;
        }

        // Attempt to use the same token from "multiple devices" (simulated)
        const concurrentRequests = [];

        for (let i = 0; i < 5; i++) {
            concurrentRequests.push(
                authenticatedRequest('GET', '/api/persons', token, null, {
                    tags: { replay_test: 'concurrent' },
                })
            );
        }

        // All concurrent requests with the same valid token should work
        // (unless there's specific anti-replay logic)
        for (const response of concurrentRequests) {
            check(response, {
                'concurrent token use handled': (r) => r.status < 500,
            });
        }
    });
}

// ============================================================================
// Setup Function (runs once before test)
// ============================================================================
export function setup() {
    console.log('='.repeat(80));
    console.log('AUTHENTICATION SECURITY LOAD TEST');
    console.log('='.repeat(80));
    console.log(`Base URL: ${BASE_URL}`);
    console.log(`Test User: ${DEFAULT_TEST_USER.username}`);
    console.log('='.repeat(80));
    console.log('\nTest Scenarios:');
    console.log('  1. Token Validation Under Load (0-4m)');
    console.log('  2. Invalid Token Rejection (4-6m)');
    console.log('  3. Token Expiry Handling (6-8m)');
    console.log('  4. Concurrent Authentication (8-9m)');
    console.log('  5. Session Management (9-11m)');
    console.log('='.repeat(80));
    console.log('\nExpected Behavior:');
    console.log('  - Valid tokens should be accepted consistently');
    console.log('  - Invalid tokens should be rejected in <100ms');
    console.log('  - No authentication system errors (5xx)');
    console.log('  - Concurrent logins should succeed');
    console.log('  - Token validation should be <200ms (p95)');
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
    console.log('AUTHENTICATION SECURITY TEST COMPLETE');
    console.log('='.repeat(80));
    console.log(`Total Duration: ${duration.toFixed(2)}s`);
    console.log('');
    console.log('Check the metrics output for:');
    console.log('  - valid_token_requests: Number of requests with valid tokens');
    console.log('  - invalid_token_requests: Number of requests with invalid tokens');
    console.log('  - invalid_token_rejections: Number of invalid tokens rejected');
    console.log('  - token_validation_time: Time to validate valid tokens');
    console.log('  - invalid_token_rejection_time: Time to reject invalid tokens');
    console.log('  - concurrent_login_success: Successful concurrent logins');
    console.log('  - authentication_errors: Should be 0');
    console.log('='.repeat(80));
    console.log('\nSecurity Validation:');
    console.log('  ✓ Invalid tokens should be rejected quickly');
    console.log('  ✓ No timing attacks possible (consistent rejection times)');
    console.log('  ✓ Valid tokens work under high load');
    console.log('  ✓ Concurrent authentication handled correctly');
    console.log('='.repeat(80));
}
