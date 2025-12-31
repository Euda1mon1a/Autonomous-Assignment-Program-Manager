/**
 * Authentication Utilities for k6
 *
 * Handles login, token management, and authenticated requests.
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { getBaseUrl } from '../config/environments.js';
import { BASE_CONFIG } from '../config/base.js';

/**
 * Login and get authentication token
 */
export function login(email, password) {
  const baseUrl = getBaseUrl();
  const loginUrl = `${baseUrl}${BASE_CONFIG.endpoints.auth.login}`;

  const payload = JSON.stringify({
    username: email,  // Backend uses 'username' field
    password: password
  });

  const params = {
    headers: {
      'Content-Type': 'application/json'
    },
    tags: { name: 'login' }
  };

  const response = http.post(loginUrl, payload, params);

  const success = check(response, {
    'login successful': (r) => r.status === 200,
    'token received': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.access_token !== undefined;
      } catch (e) {
        return false;
      }
    }
  });

  if (success) {
    const body = JSON.parse(response.body);
    return {
      accessToken: body.access_token,
      refreshToken: body.refresh_token,
      tokenType: body.token_type || 'bearer',
      expiresIn: body.expires_in || 3600
    };
  }

  console.error(`Login failed: ${response.status} ${response.body}`);
  return null;
}

/**
 * Logout (invalidate token)
 */
export function logout(token) {
  const baseUrl = getBaseUrl();
  const logoutUrl = `${baseUrl}${BASE_CONFIG.endpoints.auth.logout}`;

  const params = {
    headers: getAuthHeaders(token),
    tags: { name: 'logout' }
  };

  const response = http.post(logoutUrl, null, params);

  check(response, {
    'logout successful': (r) => r.status === 200 || r.status === 204
  });

  return response.status === 200 || response.status === 204;
}

/**
 * Refresh access token
 */
export function refreshToken(refreshToken) {
  const baseUrl = getBaseUrl();
  const refreshUrl = `${baseUrl}${BASE_CONFIG.endpoints.auth.refresh}`;

  const payload = JSON.stringify({
    refresh_token: refreshToken
  });

  const params = {
    headers: {
      'Content-Type': 'application/json'
    },
    tags: { name: 'refresh_token' }
  };

  const response = http.post(refreshUrl, payload, params);

  const success = check(response, {
    'refresh successful': (r) => r.status === 200,
    'new token received': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.access_token !== undefined;
      } catch (e) {
        return false;
      }
    }
  });

  if (success) {
    const body = JSON.parse(response.body);
    return {
      accessToken: body.access_token,
      refreshToken: body.refresh_token,
      tokenType: body.token_type || 'bearer',
      expiresIn: body.expires_in || 3600
    };
  }

  return null;
}

/**
 * Get current user info
 */
export function getCurrentUser(token) {
  const baseUrl = getBaseUrl();
  const meUrl = `${baseUrl}${BASE_CONFIG.endpoints.auth.me}`;

  const params = {
    headers: getAuthHeaders(token),
    tags: { name: 'get_current_user' }
  };

  const response = http.get(meUrl, params);

  check(response, {
    'get user successful': (r) => r.status === 200
  });

  if (response.status === 200) {
    return JSON.parse(response.body);
  }

  return null;
}

/**
 * Get authorization headers
 */
export function getAuthHeaders(token, additionalHeaders = {}) {
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
    ...additionalHeaders
  };

  return headers;
}

/**
 * Make authenticated GET request
 */
export function authenticatedGet(url, token, params = {}) {
  const requestParams = {
    ...params,
    headers: {
      ...getAuthHeaders(token),
      ...(params.headers || {})
    }
  };

  return http.get(url, requestParams);
}

/**
 * Make authenticated POST request
 */
export function authenticatedPost(url, payload, token, params = {}) {
  const requestParams = {
    ...params,
    headers: {
      ...getAuthHeaders(token),
      ...(params.headers || {})
    }
  };

  const body = typeof payload === 'string' ? payload : JSON.stringify(payload);
  return http.post(url, body, requestParams);
}

/**
 * Make authenticated PUT request
 */
export function authenticatedPut(url, payload, token, params = {}) {
  const requestParams = {
    ...params,
    headers: {
      ...getAuthHeaders(token),
      ...(params.headers || {})
    }
  };

  const body = typeof payload === 'string' ? payload : JSON.stringify(payload);
  return http.put(url, body, requestParams);
}

/**
 * Make authenticated PATCH request
 */
export function authenticatedPatch(url, payload, token, params = {}) {
  const requestParams = {
    ...params,
    headers: {
      ...getAuthHeaders(token),
      ...(params.headers || {})
    }
  };

  const body = typeof payload === 'string' ? payload : JSON.stringify(payload);
  return http.patch(url, body, requestParams);
}

/**
 * Make authenticated DELETE request
 */
export function authenticatedDelete(url, token, params = {}) {
  const requestParams = {
    ...params,
    headers: {
      ...getAuthHeaders(token),
      ...(params.headers || {})
    }
  };

  return http.del(url, null, requestParams);
}

/**
 * Token manager for VU (maintains token across iterations)
 */
export class TokenManager {
  constructor(email, password) {
    this.email = email;
    this.password = password;
    this.token = null;
    this.refreshToken = null;
    this.expiresAt = null;
  }

  /**
   * Get valid token (login or refresh if needed)
   */
  getToken() {
    // If no token, login
    if (!this.token) {
      this.performLogin();
      return this.token;
    }

    // If token expired, refresh
    if (this.isTokenExpired()) {
      this.performRefresh();
    }

    return this.token;
  }

  /**
   * Perform login
   */
  performLogin() {
    const auth = login(this.email, this.password);
    if (auth) {
      this.token = auth.accessToken;
      this.refreshToken = auth.refreshToken;
      this.expiresAt = Date.now() + (auth.expiresIn * 1000);
    }
  }

  /**
   * Perform token refresh
   */
  performRefresh() {
    if (!this.refreshToken) {
      this.performLogin();
      return;
    }

    const auth = refreshToken(this.refreshToken);
    if (auth) {
      this.token = auth.accessToken;
      this.refreshToken = auth.refreshToken;
      this.expiresAt = Date.now() + (auth.expiresIn * 1000);
    } else {
      // Refresh failed, re-login
      this.performLogin();
    }
  }

  /**
   * Check if token is expired
   */
  isTokenExpired() {
    if (!this.expiresAt) return true;
    // Refresh 5 minutes before expiry
    return Date.now() >= (this.expiresAt - 300000);
  }

  /**
   * Logout and clear token
   */
  logout() {
    if (this.token) {
      logout(this.token);
    }
    this.token = null;
    this.refreshToken = null;
    this.expiresAt = null;
  }

  /**
   * Make authenticated request
   */
  get(url, params = {}) {
    return authenticatedGet(url, this.getToken(), params);
  }

  post(url, payload, params = {}) {
    return authenticatedPost(url, payload, this.getToken(), params);
  }

  put(url, payload, params = {}) {
    return authenticatedPut(url, payload, this.getToken(), params);
  }

  patch(url, payload, params = {}) {
    return authenticatedPatch(url, payload, this.getToken(), params);
  }

  delete(url, params = {}) {
    return authenticatedDelete(url, this.getToken(), params);
  }
}

/**
 * Create authenticated session for VU
 */
export function createAuthSession(role = 'admin') {
  const user = BASE_CONFIG.testUsers[role.toLowerCase()];
  if (!user) {
    throw new Error(`Unknown user role: ${role}`);
  }

  return new TokenManager(user.email, user.password);
}

/**
 * Test authentication flow
 */
export function testAuthFlow(email, password) {
  console.log('Testing authentication flow...');

  // Login
  const auth = login(email, password);
  if (!auth) {
    console.error('Login failed');
    return false;
  }
  console.log('✓ Login successful');

  sleep(1);

  // Get current user
  const user = getCurrentUser(auth.accessToken);
  if (!user) {
    console.error('Get current user failed');
    return false;
  }
  console.log('✓ Get current user successful');

  sleep(1);

  // Refresh token
  const refreshed = refreshToken(auth.refreshToken);
  if (!refreshed) {
    console.error('Token refresh failed');
    return false;
  }
  console.log('✓ Token refresh successful');

  sleep(1);

  // Logout
  const loggedOut = logout(refreshed.accessToken);
  if (!loggedOut) {
    console.error('Logout failed');
    return false;
  }
  console.log('✓ Logout successful');

  return true;
}

export default {
  login,
  logout,
  refreshToken,
  getCurrentUser,
  getAuthHeaders,
  authenticatedGet,
  authenticatedPost,
  authenticatedPut,
  authenticatedPatch,
  authenticatedDelete,
  TokenManager,
  createAuthSession,
  testAuthFlow
};
