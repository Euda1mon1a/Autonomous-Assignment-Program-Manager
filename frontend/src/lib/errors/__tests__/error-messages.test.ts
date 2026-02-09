import { ErrorCode } from '../error-types';
import {
  ERROR_MESSAGES,
  getErrorMessage,
  getDetailedErrorMessage,
  getErrorTitle,
} from '../error-messages';

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

describe('ERROR_MESSAGES', () => {
  it('has a message for every ErrorCode', () => {
    for (const code of Object.values(ErrorCode)) {
      expect(ERROR_MESSAGES[code]).toBeDefined();
      expect(typeof ERROR_MESSAGES[code]).toBe('string');
      expect(ERROR_MESSAGES[code].length).toBeGreaterThan(0);
    }
  });
});

describe('getErrorMessage', () => {
  describe('with RFC 7807 errors', () => {
    it('returns mapped message for known error code', () => {
      const error = makeRFC7807({ errorCode: ErrorCode.NOT_FOUND });
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES[ErrorCode.NOT_FOUND]);
    });

    it('returns validation details for validation errors with field errors', () => {
      const error = makeRFC7807({
        errors: [
          { field: 'name', message: 'Name is required' },
          { field: 'email', message: 'Invalid email' },
        ],
      });
      const result = getErrorMessage(error);
      expect(result).toContain('Validation failed');
      expect(result).toContain('Name is required');
      expect(result).toContain('Invalid email');
    });

    it('returns detail when no mapped message exists', () => {
      const error = makeRFC7807({
        errorCode: 'UNKNOWN_CODE' as ErrorCode,
        detail: 'Custom detail',
      });
      expect(getErrorMessage(error)).toBe('Custom detail');
    });
  });

  describe('with standard errors', () => {
    it('returns Error message', () => {
      expect(getErrorMessage(new Error('Something broke'))).toBe('Something broke');
    });

    it('returns TypeError message', () => {
      expect(getErrorMessage(new TypeError('type issue'))).toBe('type issue');
    });
  });

  describe('with strings', () => {
    it('returns the string', () => {
      expect(getErrorMessage('An error occurred')).toBe('An error occurred');
    });
  });

  describe('with objects having message property', () => {
    it('returns message string', () => {
      expect(getErrorMessage({ message: 'Object error' })).toBe('Object error');
    });

    it('returns fallback for non-string message', () => {
      expect(getErrorMessage({ message: 42 })).toContain('unexpected error');
    });
  });

  describe('with null/undefined', () => {
    it('returns fallback for null', () => {
      expect(getErrorMessage(null)).toContain('unexpected error');
    });

    it('returns fallback for undefined', () => {
      expect(getErrorMessage(undefined)).toContain('unexpected error');
    });

    it('returns custom fallback', () => {
      expect(getErrorMessage(null, 'Custom')).toBe('Custom');
    });
  });
});

describe('getDetailedErrorMessage', () => {
  it('returns message only for non-RFC7807 errors', () => {
    const result = getDetailedErrorMessage(new Error('simple'));
    expect(result.message).toBe('simple');
    expect(result.details).toBeUndefined();
    expect(result.suggestions).toBeUndefined();
  });

  it('includes validation details for validation errors', () => {
    const error = makeRFC7807({
      errors: [
        { field: 'name', message: 'Required' },
        { field: 'email', message: 'Invalid' },
      ],
    });
    const result = getDetailedErrorMessage(error);
    expect(result.details).toHaveLength(2);
    expect(result.details![0]).toContain('name');
    expect(result.details![1]).toContain('email');
  });

  it('includes suggestions when present', () => {
    const error = makeRFC7807({
      suggestions: ['Try a different value', 'Contact support'],
    });
    const result = getDetailedErrorMessage(error);
    expect(result.suggestions).toHaveLength(2);
    expect(result.suggestions![0]).toBe('Try a different value');
  });

  it('returns message without details for plain RFC 7807', () => {
    const result = getDetailedErrorMessage(makeRFC7807());
    expect(result.message).toBeDefined();
    expect(result.details).toBeUndefined();
    expect(result.suggestions).toBeUndefined();
  });
});

describe('getErrorTitle', () => {
  it('returns title for RFC 7807 error', () => {
    expect(getErrorTitle(makeRFC7807({ title: 'Validation Error' }))).toBe(
      'Validation Error'
    );
  });

  it('returns Error name for standard Error', () => {
    expect(getErrorTitle(new Error('test'))).toBe('Error');
  });

  it('returns TypeError name for TypeError', () => {
    expect(getErrorTitle(new TypeError('test'))).toBe('TypeError');
  });

  it('returns generic "Error" for unknown types', () => {
    expect(getErrorTitle('string error')).toBe('Error');
    expect(getErrorTitle(null)).toBe('Error');
    expect(getErrorTitle(42)).toBe('Error');
  });
});
