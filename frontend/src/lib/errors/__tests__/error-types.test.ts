import {
  ErrorCode,
  ErrorSeverity,
  getErrorSeverity,
  isRFC7807Error,
  isValidationError,
  isACGMEComplianceError,
  isScheduleConflictError,
  isRateLimitError,
  hasErrorSuggestions,
} from '../error-types';

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

describe('isRFC7807Error', () => {
  it('returns true for valid RFC 7807 object', () => {
    expect(isRFC7807Error(makeRFC7807())).toBe(true);
  });

  it('returns false for null', () => {
    expect(isRFC7807Error(null)).toBe(false);
  });

  it('returns false for undefined', () => {
    expect(isRFC7807Error(undefined)).toBe(false);
  });

  it('returns false for string', () => {
    expect(isRFC7807Error('error')).toBe(false);
  });

  it('returns false when missing type', () => {
    const { type, ...rest } = makeRFC7807();
    expect(isRFC7807Error(rest)).toBe(false);
  });

  it('returns false when missing title', () => {
    const { title, ...rest } = makeRFC7807();
    expect(isRFC7807Error(rest)).toBe(false);
  });

  it('returns false when missing status', () => {
    const { status, ...rest } = makeRFC7807();
    expect(isRFC7807Error(rest)).toBe(false);
  });

  it('returns false when missing detail', () => {
    const { detail, ...rest } = makeRFC7807();
    expect(isRFC7807Error(rest)).toBe(false);
  });

  it('returns false when missing errorCode', () => {
    const { errorCode, ...rest } = makeRFC7807();
    expect(isRFC7807Error(rest)).toBe(false);
  });
});

describe('isValidationError', () => {
  it('returns true for RFC 7807 with errors array', () => {
    const error = makeRFC7807({
      errors: [{ field: 'name', message: 'Required' }],
    });
    expect(isValidationError(error)).toBe(true);
  });

  it('returns false without errors array', () => {
    expect(isValidationError(makeRFC7807())).toBe(false);
  });

  it('returns false with non-array errors', () => {
    const error = makeRFC7807({ errors: 'not an array' });
    expect(isValidationError(error)).toBe(false);
  });

  it('returns false for non-RFC7807 object', () => {
    expect(isValidationError({ errors: [] })).toBe(false);
  });
});

describe('isACGMEComplianceError', () => {
  it('returns true for RFC 7807 with violation object', () => {
    const error = makeRFC7807({
      violation: { ruleViolated: '80-hour', actualHours: 82 },
    });
    expect(isACGMEComplianceError(error)).toBe(true);
  });

  it('returns false without violation', () => {
    expect(isACGMEComplianceError(makeRFC7807())).toBe(false);
  });

  it('returns false with non-object violation', () => {
    const error = makeRFC7807({ violation: 'not an object' });
    expect(isACGMEComplianceError(error)).toBe(false);
  });
});

describe('isScheduleConflictError', () => {
  it('returns true for RFC 7807 with conflict object', () => {
    const error = makeRFC7807({
      conflict: { conflictType: 'time', requestedDate: '2024-01-15' },
    });
    expect(isScheduleConflictError(error)).toBe(true);
  });

  it('returns false without conflict', () => {
    expect(isScheduleConflictError(makeRFC7807())).toBe(false);
  });

  it('returns false with non-object conflict', () => {
    const error = makeRFC7807({ conflict: 'string' });
    expect(isScheduleConflictError(error)).toBe(false);
  });
});

describe('isRateLimitError', () => {
  it('returns true for RFC 7807 with limit and retryAfter', () => {
    const error = makeRFC7807({
      limit: 100,
      windowSeconds: 60,
      retryAfter: 30,
    });
    expect(isRateLimitError(error)).toBe(true);
  });

  it('returns false without limit', () => {
    const error = makeRFC7807({ retryAfter: 30 });
    expect(isRateLimitError(error)).toBe(false);
  });

  it('returns false without retryAfter', () => {
    const error = makeRFC7807({ limit: 100 });
    expect(isRateLimitError(error)).toBe(false);
  });

  it('returns false with non-number limit', () => {
    const error = makeRFC7807({ limit: '100', retryAfter: 30 });
    expect(isRateLimitError(error)).toBe(false);
  });
});

describe('hasErrorSuggestions', () => {
  it('returns true for RFC 7807 with suggestions array', () => {
    const error = makeRFC7807({ suggestions: ['Try again later'] });
    expect(hasErrorSuggestions(error)).toBe(true);
  });

  it('returns false without suggestions', () => {
    expect(hasErrorSuggestions(makeRFC7807())).toBe(false);
  });

  it('returns false with non-array suggestions', () => {
    const error = makeRFC7807({ suggestions: 'not an array' });
    expect(hasErrorSuggestions(error)).toBe(false);
  });
});

describe('getErrorSeverity', () => {
  it('returns INFO for 404', () => {
    expect(getErrorSeverity(404)).toBe(ErrorSeverity.INFO);
  });

  it('returns INFO for 422', () => {
    expect(getErrorSeverity(422)).toBe(ErrorSeverity.INFO);
  });

  it('returns WARNING for 401', () => {
    expect(getErrorSeverity(401)).toBe(ErrorSeverity.WARNING);
  });

  it('returns WARNING for 403', () => {
    expect(getErrorSeverity(403)).toBe(ErrorSeverity.WARNING);
  });

  it('returns CRITICAL for 500', () => {
    expect(getErrorSeverity(500)).toBe(ErrorSeverity.CRITICAL);
  });

  it('returns CRITICAL for 503', () => {
    expect(getErrorSeverity(503)).toBe(ErrorSeverity.CRITICAL);
  });

  it('returns ERROR for other codes', () => {
    expect(getErrorSeverity(400)).toBe(ErrorSeverity.ERROR);
    expect(getErrorSeverity(409)).toBe(ErrorSeverity.ERROR);
    expect(getErrorSeverity(429)).toBe(ErrorSeverity.ERROR);
  });
});

describe('ErrorCode enum', () => {
  it('has all expected categories', () => {
    expect(ErrorCode.NOT_FOUND).toBe('NOT_FOUND');
    expect(ErrorCode.VALIDATION_ERROR).toBe('VALIDATION_ERROR');
    expect(ErrorCode.UNAUTHORIZED).toBe('UNAUTHORIZED');
    expect(ErrorCode.SCHEDULING_ERROR).toBe('SCHEDULING_ERROR');
    expect(ErrorCode.ACGME_COMPLIANCE_ERROR).toBe('ACGME_COMPLIANCE_ERROR');
    expect(ErrorCode.DATABASE_ERROR).toBe('DATABASE_ERROR');
    expect(ErrorCode.RATE_LIMIT_EXCEEDED).toBe('RATE_LIMIT_EXCEEDED');
    expect(ErrorCode.INTERNAL_ERROR).toBe('INTERNAL_ERROR');
  });
});
