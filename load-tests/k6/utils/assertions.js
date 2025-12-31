/**
 * Custom Assertions for k6
 *
 * Extended check functions for common validation patterns.
 */

import { check } from 'k6';

/**
 * Assert response is successful (2xx status)
 */
export function assertSuccess(response, customMessage = null) {
  return check(response, {
    [customMessage || 'status is 2xx']: (r) => r.status >= 200 && r.status < 300
  });
}

/**
 * Assert specific status code
 */
export function assertStatus(response, expectedStatus, customMessage = null) {
  return check(response, {
    [customMessage || `status is ${expectedStatus}`]: (r) => r.status === expectedStatus
  });
}

/**
 * Assert response time
 */
export function assertResponseTime(response, maxMs, customMessage = null) {
  return check(response, {
    [customMessage || `response time < ${maxMs}ms`]: (r) => r.timings.duration < maxMs
  });
}

/**
 * Assert JSON response structure
 */
export function assertJsonStructure(response, expectedKeys, customMessage = null) {
  return check(response, {
    [customMessage || 'response is valid JSON']: (r) => {
      try {
        const body = JSON.parse(r.body);
        return expectedKeys.every(key => key in body);
      } catch (e) {
        return false;
      }
    }
  });
}

/**
 * Assert JSON array response
 */
export function assertJsonArray(response, minLength = 0, customMessage = null) {
  return check(response, {
    [customMessage || 'response is JSON array']: (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body) && body.length >= minLength;
      } catch (e) {
        return false;
      }
    }
  });
}

/**
 * Assert pagination response
 */
export function assertPaginatedResponse(response) {
  return check(response, {
    'has items array': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body.items);
      } catch (e) {
        return false;
      }
    },
    'has total count': (r) => {
      try {
        const body = JSON.parse(r.body);
        return typeof body.total === 'number';
      } catch (e) {
        return false;
      }
    },
    'has skip and limit': (r) => {
      try {
        const body = JSON.parse(r.body);
        return typeof body.skip === 'number' && typeof body.limit === 'number';
      } catch (e) {
        return false;
      }
    }
  });
}

/**
 * Assert error response
 */
export function assertError(response, expectedStatus, expectedMessage = null) {
  const checks = {
    [`status is ${expectedStatus}`]: (r) => r.status === expectedStatus,
    'has error detail': (r) => {
      try {
        const body = JSON.parse(r.body);
        return 'detail' in body;
      } catch (e) {
        return false;
      }
    }
  };

  if (expectedMessage) {
    checks['error message matches'] = (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.detail.includes(expectedMessage);
      } catch (e) {
        return false;
      }
    };
  }

  return check(response, checks);
}

/**
 * Assert CRUD created response
 */
export function assertCreated(response, idField = 'id') {
  return check(response, {
    'status is 201': (r) => r.status === 201,
    'has ID': (r) => {
      try {
        const body = JSON.parse(r.body);
        return idField in body && body[idField] !== null;
      } catch (e) {
        return false;
      }
    },
    'has created_at': (r) => {
      try {
        const body = JSON.parse(r.body);
        return 'created_at' in body;
      } catch (e) {
        return false;
      }
    }
  });
}

/**
 * Assert CRUD updated response
 */
export function assertUpdated(response) {
  return check(response, {
    'status is 200': (r) => r.status === 200,
    'has updated_at': (r) => {
      try {
        const body = JSON.parse(r.body);
        return 'updated_at' in body;
      } catch (e) {
        return false;
      }
    }
  });
}

/**
 * Assert CRUD deleted response
 */
export function assertDeleted(response) {
  return check(response, {
    'status is 204 or 200': (r) => r.status === 204 || r.status === 200
  });
}

/**
 * Assert authentication response
 */
export function assertAuthenticated(response) {
  return check(response, {
    'status is 200': (r) => r.status === 200,
    'has access_token': (r) => {
      try {
        const body = JSON.parse(r.body);
        return 'access_token' in body && body.access_token.length > 0;
      } catch (e) {
        return false;
      }
    },
    'has token_type': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.token_type === 'bearer';
      } catch (e) {
        return false;
      }
    }
  });
}

/**
 * Assert unauthorized response
 */
export function assertUnauthorized(response) {
  return check(response, {
    'status is 401': (r) => r.status === 401,
    'has WWW-Authenticate header': (r) => 'www-authenticate' in r.headers || 'Www-Authenticate' in r.headers
  });
}

/**
 * Assert forbidden response
 */
export function assertForbidden(response) {
  return check(response, {
    'status is 403': (r) => r.status === 403
  });
}

/**
 * Assert rate limited response
 */
export function assertRateLimited(response) {
  return check(response, {
    'status is 429': (r) => r.status === 429,
    'has Retry-After header': (r) => 'retry-after' in r.headers || 'Retry-After' in r.headers
  });
}

/**
 * Assert validation error
 */
export function assertValidationError(response, fieldName = null) {
  const checks = {
    'status is 422': (r) => r.status === 422,
    'has validation errors': (r) => {
      try {
        const body = JSON.parse(r.body);
        return 'detail' in body && Array.isArray(body.detail);
      } catch (e) {
        return false;
      }
    }
  };

  if (fieldName) {
    checks[`validation error for ${fieldName}`] = (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.detail.some(err => err.loc && err.loc.includes(fieldName));
      } catch (e) {
        return false;
      }
    };
  }

  return check(response, checks);
}

/**
 * Assert header present
 */
export function assertHeader(response, headerName, expectedValue = null) {
  const headerLower = headerName.toLowerCase();
  const checks = {
    [`has ${headerName} header`]: (r) => {
      return Object.keys(r.headers).some(h => h.toLowerCase() === headerLower);
    }
  };

  if (expectedValue !== null) {
    checks[`${headerName} equals ${expectedValue}`] = (r) => {
      const header = Object.keys(r.headers).find(h => h.toLowerCase() === headerLower);
      return header && r.headers[header] === expectedValue;
    };
  }

  return check(response, checks);
}

/**
 * Assert CORS headers
 */
export function assertCorsHeaders(response, origin = null) {
  const checks = {
    'has Access-Control-Allow-Origin': (r) => {
      return Object.keys(r.headers).some(h =>
        h.toLowerCase() === 'access-control-allow-origin'
      );
    }
  };

  if (origin) {
    checks['CORS origin matches'] = (r) => {
      const header = Object.keys(r.headers).find(h =>
        h.toLowerCase() === 'access-control-allow-origin'
      );
      return header && (r.headers[header] === origin || r.headers[header] === '*');
    };
  }

  return check(response, checks);
}

/**
 * Assert content type
 */
export function assertContentType(response, expectedType) {
  return check(response, {
    [`content-type is ${expectedType}`]: (r) => {
      const ct = r.headers['Content-Type'] || r.headers['content-type'] || '';
      return ct.includes(expectedType);
    }
  });
}

/**
 * Assert JSON content type
 */
export function assertJsonContent(response) {
  return assertContentType(response, 'application/json');
}

/**
 * Assert response body size
 */
export function assertBodySize(response, minBytes, maxBytes = null) {
  const checks = {
    [`body size >= ${minBytes} bytes`]: (r) => r.body.length >= minBytes
  };

  if (maxBytes !== null) {
    checks[`body size <= ${maxBytes} bytes`] = (r) => r.body.length <= maxBytes;
  }

  return check(response, checks);
}

/**
 * Assert ACGME compliance response
 */
export function assertComplianceResponse(response) {
  return check(response, {
    'status is 200': (r) => r.status === 200,
    'has compliant field': (r) => {
      try {
        const body = JSON.parse(r.body);
        return typeof body.compliant === 'boolean';
      } catch (e) {
        return false;
      }
    },
    'has violations array': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body.violations);
      } catch (e) {
        return false;
      }
    }
  });
}

/**
 * Assert schedule response
 */
export function assertScheduleResponse(response) {
  return check(response, {
    'status is 200': (r) => r.status === 200,
    'has schedule data': (r) => {
      try {
        const body = JSON.parse(r.body);
        return 'start_date' in body && 'end_date' in body;
      } catch (e) {
        return false;
      }
    },
    'has assignments': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body.assignments);
      } catch (e) {
        return false;
      }
    }
  });
}

/**
 * Composite assertion helper
 */
export function assertAll(response, assertions) {
  let allPassed = true;

  for (const assertion of assertions) {
    const passed = assertion(response);
    allPassed = allPassed && passed;
  }

  return allPassed;
}

export default {
  assertSuccess,
  assertStatus,
  assertResponseTime,
  assertJsonStructure,
  assertJsonArray,
  assertPaginatedResponse,
  assertError,
  assertCreated,
  assertUpdated,
  assertDeleted,
  assertAuthenticated,
  assertUnauthorized,
  assertForbidden,
  assertRateLimited,
  assertValidationError,
  assertHeader,
  assertCorsHeaders,
  assertContentType,
  assertJsonContent,
  assertBodySize,
  assertComplianceResponse,
  assertScheduleResponse,
  assertAll
};
