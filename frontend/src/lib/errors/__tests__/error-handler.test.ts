import { ErrorCode } from '../error-types';
import { errorHandler } from '../error-handler';

// Helper to build a valid RFC 7807 error object
function makeRFC7807(overrides: Record<string, unknown> = {}) {
  return {
    type: 'https://example.com/error',
    title: 'Test Error',
    status: 400,
    detail: 'Something went wrong',
    instance: '/api/test',
    errorCode: ErrorCode.VALIDATION_ERROR,
    errorId: 'err-123',
    timestamp: new Date().toISOString(),
    ...overrides,
  };
}

beforeEach(() => {
  // Reset handler config between tests
  errorHandler.configure({ enableLogging: false, enableReporting: false });
});

describe('errorHandler.handle', () => {
  it('returns RFC 7807 error as-is', () => {
    const error = makeRFC7807();
    const result = errorHandler.handle(error);
    expect(result).toBe(error);
  });

  it('returns standard Error as-is', () => {
    const error = new Error('test');
    const result = errorHandler.handle(error);
    expect(result).toBe(error);
  });

  it('wraps unknown types in Error', () => {
    const result = errorHandler.handle('string error');
    expect(result).toBeInstanceOf(Error);
    expect((result as Error).message).toBe('string error');
  });

  it('calls onError callback when configured', () => {
    const onError = jest.fn();
    errorHandler.configure({ enableLogging: false, onError });

    const error = new Error('test');
    errorHandler.handle(error);

    expect(onError).toHaveBeenCalledWith(error);
  });
});

describe('errorHandler.shouldReauthenticate', () => {
  it('returns true for TOKEN_EXPIRED', () => {
    const error = makeRFC7807({ errorCode: ErrorCode.TOKEN_EXPIRED });
    expect(errorHandler.shouldReauthenticate(error)).toBe(true);
  });

  it('returns true for INVALID_TOKEN', () => {
    const error = makeRFC7807({ errorCode: ErrorCode.INVALID_TOKEN });
    expect(errorHandler.shouldReauthenticate(error)).toBe(true);
  });

  it('returns true for TOKEN_REVOKED', () => {
    const error = makeRFC7807({ errorCode: ErrorCode.TOKEN_REVOKED });
    expect(errorHandler.shouldReauthenticate(error)).toBe(true);
  });

  it('returns true for UNAUTHORIZED', () => {
    const error = makeRFC7807({ errorCode: ErrorCode.UNAUTHORIZED });
    expect(errorHandler.shouldReauthenticate(error)).toBe(true);
  });

  it('returns false for other error codes', () => {
    const error = makeRFC7807({ errorCode: ErrorCode.FORBIDDEN });
    expect(errorHandler.shouldReauthenticate(error)).toBe(false);
  });

  it('returns false for non-RFC7807 errors', () => {
    expect(errorHandler.shouldReauthenticate(new Error('test'))).toBe(false);
  });
});

describe('errorHandler.isRetryable', () => {
  it('returns true for DATABASE_TIMEOUT', () => {
    const error = makeRFC7807({ errorCode: ErrorCode.DATABASE_TIMEOUT });
    expect(errorHandler.isRetryable(error)).toBe(true);
  });

  it('returns true for SERVICE_TIMEOUT', () => {
    const error = makeRFC7807({ errorCode: ErrorCode.SERVICE_TIMEOUT });
    expect(errorHandler.isRetryable(error)).toBe(true);
  });

  it('returns true for SERVICE_UNAVAILABLE', () => {
    const error = makeRFC7807({ errorCode: ErrorCode.SERVICE_UNAVAILABLE });
    expect(errorHandler.isRetryable(error)).toBe(true);
  });

  it('returns true for DATABASE_CONNECTION_ERROR', () => {
    const error = makeRFC7807({ errorCode: ErrorCode.DATABASE_CONNECTION_ERROR });
    expect(errorHandler.isRetryable(error)).toBe(true);
  });

  it('returns false for VALIDATION_ERROR', () => {
    const error = makeRFC7807({ errorCode: ErrorCode.VALIDATION_ERROR });
    expect(errorHandler.isRetryable(error)).toBe(false);
  });

  it('returns false for non-RFC7807 errors', () => {
    expect(errorHandler.isRetryable(new Error('timeout'))).toBe(false);
  });
});

describe('errorHandler.getRetryDelay', () => {
  it('returns delay in ms for rate limit errors', () => {
    const error = makeRFC7807({
      errorCode: ErrorCode.RATE_LIMIT_EXCEEDED,
      limit: 100,
      windowSeconds: 60,
      retryAfter: 30,
    });
    expect(errorHandler.getRetryDelay(error)).toBe(30000);
  });

  it('returns null for non-rate-limit errors', () => {
    expect(errorHandler.getRetryDelay(makeRFC7807())).toBeNull();
  });

  it('returns null for non-RFC7807 errors', () => {
    expect(errorHandler.getRetryDelay(new Error('rate limited'))).toBeNull();
  });
});

describe('errorHandler.getValidationErrors', () => {
  it('returns field errors for validation errors', () => {
    const error = makeRFC7807({
      errors: [
        { field: 'name', message: 'Required', type: 'missing' },
        { field: 'email', message: 'Invalid format' },
      ],
    });
    const result = errorHandler.getValidationErrors(error);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({ field: 'name', message: 'Required' });
    expect(result[1]).toEqual({ field: 'email', message: 'Invalid format' });
  });

  it('returns empty array for non-validation errors', () => {
    expect(errorHandler.getValidationErrors(makeRFC7807())).toEqual([]);
  });

  it('returns empty array for non-RFC7807 errors', () => {
    expect(errorHandler.getValidationErrors(new Error('test'))).toEqual([]);
  });
});

describe('errorHandler.getACGMEViolationDetails', () => {
  it('returns violation for ACGME errors', () => {
    const violation = { ruleViolated: '80-hour', actualHours: 82, limitHours: 80 };
    const error = makeRFC7807({ violation });
    const result = errorHandler.getACGMEViolationDetails(error);
    expect(result).toEqual(violation);
  });

  it('returns null for non-ACGME errors', () => {
    expect(errorHandler.getACGMEViolationDetails(makeRFC7807())).toBeNull();
  });
});

describe('errorHandler.getScheduleConflictDetails', () => {
  it('returns conflict for schedule conflict errors', () => {
    const conflict = { conflictType: 'time', requestedDate: '2024-01-15' };
    const error = makeRFC7807({ conflict });
    const result = errorHandler.getScheduleConflictDetails(error);
    expect(result).toEqual(conflict);
  });

  it('returns null for non-conflict errors', () => {
    expect(errorHandler.getScheduleConflictDetails(makeRFC7807())).toBeNull();
  });
});

describe('errorHandler.getUserMessage', () => {
  it('delegates to getErrorMessage', () => {
    const error = makeRFC7807({ errorCode: ErrorCode.NOT_FOUND });
    const result = errorHandler.getUserMessage(error);
    expect(result).toContain('not found');
  });

  it('returns fallback for unknown errors', () => {
    const result = errorHandler.getUserMessage(null);
    expect(result).toContain('unexpected error');
  });
});

describe('errorHandler.configure', () => {
  it('enables logging', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    errorHandler.configure({ enableLogging: true });
    errorHandler.handle(makeRFC7807({ status: 400 }));

    // Status 400 -> ERROR severity -> console.error
    expect(consoleSpy).toHaveBeenCalled();

    consoleSpy.mockRestore();
  });

  it('disables logging', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    errorHandler.configure({ enableLogging: false });
    errorHandler.handle(makeRFC7807({ status: 500 }));

    expect(consoleSpy).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });
});
