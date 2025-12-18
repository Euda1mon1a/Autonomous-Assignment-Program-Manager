/**
 * Authentication Utilities for k6 Load Tests
 *
 * Provides JWT token management, login helpers, and authenticated request utilities.
 * Implements token caching to minimize auth overhead during load tests.
 *
 * @module utils/auth
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { getBaseURL } from '../k6.config.js';

/**
 * In-memory token cache
 * Key: username
 * Value: { token, expiresAt }
 *
 * Note: This is per-VU storage. Each virtual user maintains its own cache.
 */
const tokenCache = {};

/**
 * Default test credentials
 * These should match seeded test users in the database
 */
export const TEST_USERS = {
  admin: {
    username: 'admin',
    password: 'AdminPassword123!',
    role: 'admin',
  },
  coordinator: {
    username: 'coordinator',
    password: 'CoordinatorPass123!',
    role: 'coordinator',
  },
  faculty: {
    username: 'faculty',
    password: 'FacultyPassword123!',
    role: 'faculty',
  },
  resident: {
    username: 'resident',
    password: 'ResidentPassword123!',
    role: 'resident',
  },
  clinical_staff: {
    username: 'clinical_staff',
    password: 'ClinicalStaff123!',
    role: 'clinical_staff',
  },
};

/**
 * Get a random test user for load testing
 * Distributes load across different user roles
 *
 * @returns {Object} User credentials object
 */
export function getRandomTestUser() {
  const users = Object.values(TEST_USERS);
  return users[Math.floor(Math.random() * users.length)];
}

/**
 * Get test user by role
 *
 * @param {string} role - User role (admin, coordinator, faculty, resident, clinical_staff)
 * @returns {Object} User credentials object
 * @throws {Error} If role is not found
 */
export function getTestUserByRole(role) {
  const user = TEST_USERS[role];
  if (!user) {
    throw new Error(`No test user found for role: ${role}`);
  }
  return user;
}

/**
 * Login and get JWT token
 * Uses the /api/auth/login/json endpoint for JSON-based authentication
 *
 * @param {string} username - Username
 * @param {string} password - Password
 * @param {boolean} cache - Whether to cache the token (default: true)
 * @returns {string|null} JWT access token or null on failure
 */
export function login(username, password, cache = true) {
  const baseURL = getBaseURL();
  const url = `${baseURL}/api/auth/login/json`;

  const payload = JSON.stringify({
    username: username,
    password: password,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    tags: { name: 'auth_login' },
  };

  const response = http.post(url, payload, params);

  const success = check(response, {
    'login status is 200': (r) => r.status === 200,
    'login has access_token': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.access_token !== undefined;
      } catch {
        return false;
      }
    },
  });

  if (!success) {
    console.error(`Login failed for ${username}: ${response.status} - ${response.body}`);
    return null;
  }

  const body = JSON.parse(response.body);
  const token = body.access_token;

  // Cache token if requested (default 30 minutes expiry)
  if (cache && token) {
    const expiresAt = Date.now() + (30 * 60 * 1000); // 30 minutes from now
    tokenCache[username] = {
      token: token,
      expiresAt: expiresAt,
    };
  }

  return token;
}

/**
 * Get cached token or login if cache miss/expired
 * This reduces authentication load during tests
 *
 * @param {string} username - Username
 * @param {string} password - Password
 * @returns {string|null} JWT access token or null on failure
 */
export function getCachedToken(username, password) {
  // Check if token exists and is not expired
  const cached = tokenCache[username];
  if (cached && cached.expiresAt > Date.now()) {
    return cached.token;
  }

  // Cache miss or expired - login and cache
  return login(username, password, true);
}

/**
 * Clear token cache for a specific user or all users
 *
 * @param {string|null} username - Username to clear, or null to clear all
 */
export function clearTokenCache(username = null) {
  if (username) {
    delete tokenCache[username];
  } else {
    Object.keys(tokenCache).forEach(key => delete tokenCache[key]);
  }
}

/**
 * Generate authorization headers with JWT token
 *
 * @param {string} token - JWT access token
 * @returns {Object} Headers object with Authorization
 */
export function authHeaders(token) {
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
}

/**
 * Get authenticated HTTP request parameters
 *
 * @param {string} token - JWT access token
 * @param {Object} additionalHeaders - Additional headers to merge
 * @param {Object} tags - Custom tags for metrics
 * @returns {Object} Complete params object for k6 http requests
 */
export function getAuthParams(token, additionalHeaders = {}, tags = {}) {
  return {
    headers: {
      ...authHeaders(token),
      ...additionalHeaders,
    },
    tags: {
      name: 'authenticated-request',
      ...tags,
    },
    timeout: '30s',
  };
}

/**
 * Perform authenticated GET request
 *
 * @param {string} url - Request URL
 * @param {string} token - JWT access token
 * @param {Object} tags - Custom tags for metrics
 * @returns {Object} k6 Response object
 */
export function authenticatedGet(url, token, tags = {}) {
  const params = getAuthParams(token, {}, tags);
  return http.get(url, params);
}

/**
 * Perform authenticated POST request
 *
 * @param {string} url - Request URL
 * @param {Object} data - Request body data
 * @param {string} token - JWT access token
 * @param {Object} tags - Custom tags for metrics
 * @returns {Object} k6 Response object
 */
export function authenticatedPost(url, data, token, tags = {}) {
  const params = getAuthParams(token, {}, tags);
  const payload = JSON.stringify(data);
  return http.post(url, payload, params);
}

/**
 * Perform authenticated PUT request
 *
 * @param {string} url - Request URL
 * @param {Object} data - Request body data
 * @param {string} token - JWT access token
 * @param {Object} tags - Custom tags for metrics
 * @returns {Object} k6 Response object
 */
export function authenticatedPut(url, data, token, tags = {}) {
  const params = getAuthParams(token, {}, tags);
  const payload = JSON.stringify(data);
  return http.put(url, payload, params);
}

/**
 * Perform authenticated DELETE request
 *
 * @param {string} url - Request URL
 * @param {string} token - JWT access token
 * @param {Object} tags - Custom tags for metrics
 * @returns {Object} k6 Response object
 */
export function authenticatedDelete(url, token, tags = {}) {
  const params = getAuthParams(token, {}, tags);
  return http.del(url, params);
}

/**
 * Logout (invalidate token)
 *
 * @param {string} token - JWT access token
 * @returns {boolean} True if logout successful
 */
export function logout(token) {
  const baseURL = getBaseURL();
  const url = `${baseURL}/api/auth/logout`;

  const params = getAuthParams(token, {}, { name: 'auth_logout' });
  const response = http.post(url, null, params);

  const success = check(response, {
    'logout status is 200': (r) => r.status === 200,
  });

  return success;
}

/**
 * Verify token is valid by calling /api/auth/me
 *
 * @param {string} token - JWT access token
 * @returns {Object|null} User info object or null if invalid
 */
export function verifyToken(token) {
  const baseURL = getBaseURL();
  const url = `${baseURL}/api/auth/me`;

  const response = authenticatedGet(url, token, { name: 'auth_verify' });

  if (response.status !== 200) {
    return null;
  }

  try {
    return JSON.parse(response.body);
  } catch {
    return null;
  }
}

/**
 * Setup function - login and return token
 * Use this in k6 setup() function to authenticate once
 *
 * @param {string} username - Username (default: admin)
 * @param {string} password - Password
 * @returns {string|null} JWT access token
 */
export function setupAuth(username = 'admin', password = 'AdminPassword123!') {
  console.log(`Setting up authentication for user: ${username}`);
  const token = login(username, password);

  if (!token) {
    throw new Error(`Failed to authenticate user: ${username}`);
  }

  // Verify token works
  const userInfo = verifyToken(token);
  if (!userInfo) {
    throw new Error(`Token verification failed for user: ${username}`);
  }

  console.log(`Authentication successful. User: ${userInfo.username}, Role: ${userInfo.role}`);
  return token;
}

/**
 * Create authenticated user session
 * Returns an object with token and convenience methods
 *
 * @param {string} username - Username
 * @param {string} password - Password
 * @returns {Object} Session object with token and methods
 */
export function createSession(username, password) {
  const token = getCachedToken(username, password);

  if (!token) {
    throw new Error(`Failed to create session for user: ${username}`);
  }

  return {
    token: token,
    username: username,

    /**
     * Make authenticated GET request
     */
    get: (url, tags) => authenticatedGet(url, token, tags),

    /**
     * Make authenticated POST request
     */
    post: (url, data, tags) => authenticatedPost(url, data, token, tags),

    /**
     * Make authenticated PUT request
     */
    put: (url, data, tags) => authenticatedPut(url, data, token, tags),

    /**
     * Make authenticated DELETE request
     */
    delete: (url, tags) => authenticatedDelete(url, token, tags),

    /**
     * Verify session is still valid
     */
    verify: () => verifyToken(token),

    /**
     * Logout and invalidate token
     */
    logout: () => logout(token),
  };
}

/**
 * Rate limit aware login
 * Implements exponential backoff if rate limited
 *
 * @param {string} username - Username
 * @param {string} password - Password
 * @param {number} maxRetries - Maximum retry attempts (default: 3)
 * @returns {string|null} JWT access token or null on failure
 */
export function loginWithRetry(username, password, maxRetries = 3) {
  let attempt = 0;
  let backoffSeconds = 1;

  while (attempt < maxRetries) {
    const token = login(username, password, false);

    if (token) {
      return token;
    }

    attempt++;
    if (attempt < maxRetries) {
      console.warn(`Login attempt ${attempt} failed. Retrying in ${backoffSeconds}s...`);
      sleep(backoffSeconds);
      backoffSeconds *= 2; // Exponential backoff
    }
  }

  console.error(`Login failed after ${maxRetries} attempts for user: ${username}`);
  return null;
}

/**
 * Export all utilities
 */
export default {
  TEST_USERS,
  getRandomTestUser,
  getTestUserByRole,
  login,
  getCachedToken,
  clearTokenCache,
  authHeaders,
  getAuthParams,
  authenticatedGet,
  authenticatedPost,
  authenticatedPut,
  authenticatedDelete,
  logout,
  verifyToken,
  setupAuth,
  createSession,
  loginWithRetry,
};
