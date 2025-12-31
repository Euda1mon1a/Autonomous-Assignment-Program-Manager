/**
 * HTTP Helper Functions
 *
 * Wrapper functions for common HTTP operations with built-in error handling,
 * retries, and metrics tracking.
 */

import http from 'k6/http';
import { sleep } from 'k6';
import { getBaseUrl } from '../config/environments.js';
import { trackResponse } from './metrics.js';

/**
 * Make HTTP GET request with retries
 */
export function httpGet(url, params = {}, retries = 3) {
  let lastError = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = http.get(url, params);

      // Success or client error (don't retry)
      if (response.status < 500) {
        return trackResponse(response, { attempt });
      }

      lastError = response;

      // Wait before retry (exponential backoff)
      if (attempt < retries) {
        sleep(Math.pow(2, attempt));
      }
    } catch (error) {
      lastError = error;
      if (attempt < retries) {
        sleep(Math.pow(2, attempt));
      }
    }
  }

  return lastError;
}

/**
 * Make HTTP POST request with retries
 */
export function httpPost(url, payload = null, params = {}, retries = 3) {
  let lastError = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const body = payload && typeof payload !== 'string'
        ? JSON.stringify(payload)
        : payload;

      const response = http.post(url, body, params);

      // Success or client error (don't retry)
      if (response.status < 500) {
        return trackResponse(response, { attempt });
      }

      lastError = response;

      if (attempt < retries) {
        sleep(Math.pow(2, attempt));
      }
    } catch (error) {
      lastError = error;
      if (attempt < retries) {
        sleep(Math.pow(2, attempt));
      }
    }
  }

  return lastError;
}

/**
 * Make HTTP PUT request
 */
export function httpPut(url, payload = null, params = {}, retries = 3) {
  let lastError = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const body = payload && typeof payload !== 'string'
        ? JSON.stringify(payload)
        : payload;

      const response = http.put(url, body, params);

      if (response.status < 500) {
        return trackResponse(response, { attempt });
      }

      lastError = response;

      if (attempt < retries) {
        sleep(Math.pow(2, attempt));
      }
    } catch (error) {
      lastError = error;
      if (attempt < retries) {
        sleep(Math.pow(2, attempt));
      }
    }
  }

  return lastError;
}

/**
 * Make HTTP PATCH request
 */
export function httpPatch(url, payload = null, params = {}, retries = 3) {
  let lastError = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const body = payload && typeof payload !== 'string'
        ? JSON.stringify(payload)
        : payload;

      const response = http.patch(url, body, params);

      if (response.status < 500) {
        return trackResponse(response, { attempt });
      }

      lastError = response;

      if (attempt < retries) {
        sleep(Math.pow(2, attempt));
      }
    } catch (error) {
      lastError = error;
      if (attempt < retries) {
        sleep(Math.pow(2, attempt));
      }
    }
  }

  return lastError;
}

/**
 * Make HTTP DELETE request
 */
export function httpDelete(url, params = {}, retries = 3) {
  let lastError = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = http.del(url, null, params);

      if (response.status < 500) {
        return trackResponse(response, { attempt });
      }

      lastError = response;

      if (attempt < retries) {
        sleep(Math.pow(2, attempt));
      }
    } catch (error) {
      lastError = error;
      if (attempt < retries) {
        sleep(Math.pow(2, attempt));
      }
    }
  }

  return lastError;
}

/**
 * Make batch HTTP requests
 */
export function httpBatch(requests) {
  return http.batch(requests);
}

/**
 * Build query string from parameters
 */
export function buildQueryString(params) {
  const parts = [];

  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined) {
      if (Array.isArray(value)) {
        value.forEach(v => parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(v)}`));
      } else {
        parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
      }
    }
  }

  return parts.length > 0 ? `?${parts.join('&')}` : '';
}

/**
 * Build full URL with query parameters
 */
export function buildUrl(endpoint, params = {}) {
  const baseUrl = getBaseUrl();
  const url = `${baseUrl}${endpoint}`;
  const queryString = buildQueryString(params);
  return `${url}${queryString}`;
}

/**
 * Parse JSON response safely
 */
export function parseJson(response) {
  try {
    return JSON.parse(response.body);
  } catch (error) {
    console.error(`Failed to parse JSON: ${error.message}`);
    console.error(`Response body: ${response.body}`);
    return null;
  }
}

/**
 * Extract response header (case-insensitive)
 */
export function getHeader(response, headerName) {
  const headerLower = headerName.toLowerCase();
  const header = Object.keys(response.headers).find(
    h => h.toLowerCase() === headerLower
  );
  return header ? response.headers[header] : null;
}

/**
 * Check if response is JSON
 */
export function isJsonResponse(response) {
  const contentType = getHeader(response, 'content-type') || '';
  return contentType.includes('application/json');
}

/**
 * Handle paginated requests
 */
export function* paginatedGet(endpoint, params = {}, pageSize = 100) {
  let skip = 0;
  let hasMore = true;

  while (hasMore) {
    const queryParams = {
      ...params,
      skip: skip,
      limit: pageSize
    };

    const url = buildUrl(endpoint, queryParams);
    const response = httpGet(url);

    if (response.status !== 200) {
      break;
    }

    const data = parseJson(response);
    if (!data || !data.items || data.items.length === 0) {
      break;
    }

    yield data.items;

    // Check if there are more pages
    hasMore = data.items.length === pageSize && skip + pageSize < data.total;
    skip += pageSize;
  }
}

/**
 * Wait for condition with timeout
 */
export function waitFor(conditionFn, timeoutMs = 30000, pollIntervalMs = 1000) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeoutMs) {
    if (conditionFn()) {
      return true;
    }
    sleep(pollIntervalMs / 1000);
  }

  return false;
}

/**
 * Poll endpoint until condition met
 */
export function pollUntil(url, conditionFn, params = {}, timeoutMs = 30000, pollIntervalMs = 1000) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeoutMs) {
    const response = httpGet(url, params);

    if (response.status === 200) {
      const data = parseJson(response);
      if (conditionFn(data)) {
        return { success: true, data, response };
      }
    }

    sleep(pollIntervalMs / 1000);
  }

  return { success: false, data: null, response: null };
}

/**
 * Upload file
 */
export function uploadFile(url, fileData, fieldName = 'file', params = {}) {
  const formData = {
    [fieldName]: http.file(fileData, 'upload.dat')
  };

  return http.post(url, formData, params);
}

/**
 * Default request parameters
 */
export function getDefaultParams(additionalParams = {}) {
  return {
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...((additionalParams.headers) || {})
    },
    timeout: '30s',
    ...additionalParams
  };
}

/**
 * Rate limit aware request
 */
export function rateLimitedRequest(requestFn, maxRetries = 5) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const response = requestFn();

    // If not rate limited, return
    if (response.status !== 429) {
      return response;
    }

    // Extract retry-after header
    const retryAfter = getHeader(response, 'retry-after');
    const waitTime = retryAfter ? parseInt(retryAfter) : Math.pow(2, attempt);

    console.log(`Rate limited. Waiting ${waitTime}s before retry...`);
    sleep(waitTime);
  }

  // Return last response after max retries
  return requestFn();
}

export default {
  httpGet,
  httpPost,
  httpPut,
  httpPatch,
  httpDelete,
  httpBatch,
  buildQueryString,
  buildUrl,
  parseJson,
  getHeader,
  isJsonResponse,
  paginatedGet,
  waitFor,
  pollUntil,
  uploadFile,
  getDefaultParams,
  rateLimitedRequest
};
