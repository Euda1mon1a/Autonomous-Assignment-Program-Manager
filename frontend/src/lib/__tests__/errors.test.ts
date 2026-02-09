import {
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
  isApiError,
  isError,
  getErrorMessage,
} from '../errors';

describe('isApiError', () => {
  it('returns true for valid ApiError shape', () => {
    expect(isApiError({ message: 'Not found', status: 404 })).toBe(true);
  });

  it('returns true with optional fields', () => {
    expect(
      isApiError({ message: 'Bad', status: 400, detail: 'field invalid', errors: {} })
    ).toBe(true);
  });

  it('returns false for null', () => {
    expect(isApiError(null)).toBe(false);
  });

  it('returns false for undefined', () => {
    expect(isApiError(undefined)).toBe(false);
  });

  it('returns false for plain string', () => {
    expect(isApiError('error')).toBe(false);
  });

  it('returns false for object missing status', () => {
    expect(isApiError({ message: 'oops' })).toBe(false);
  });

  it('returns false for object missing message', () => {
    expect(isApiError({ status: 500 })).toBe(false);
  });

  it('returns false for non-string message', () => {
    expect(isApiError({ message: 123, status: 500 })).toBe(false);
  });

  it('returns false for non-number status', () => {
    expect(isApiError({ message: 'err', status: '500' })).toBe(false);
  });
});

describe('isError', () => {
  it('returns true for Error instance', () => {
    expect(isError(new Error('test'))).toBe(true);
  });

  it('returns true for TypeError', () => {
    expect(isError(new TypeError('type error'))).toBe(true);
  });

  it('returns false for plain object', () => {
    expect(isError({ message: 'not an error' })).toBe(false);
  });

  it('returns false for string', () => {
    expect(isError('error string')).toBe(false);
  });

  it('returns false for null', () => {
    expect(isError(null)).toBe(false);
  });
});

describe('getErrorMessage', () => {
  describe('with null/undefined', () => {
    it('returns fallback for null', () => {
      expect(getErrorMessage(null)).toBe(ERROR_MESSAGES.UNKNOWN_ERROR);
    });

    it('returns fallback for undefined', () => {
      expect(getErrorMessage(undefined)).toBe(ERROR_MESSAGES.UNKNOWN_ERROR);
    });

    it('returns custom fallback', () => {
      expect(getErrorMessage(null, 'Custom fallback')).toBe('Custom fallback');
    });
  });

  describe('with ApiError', () => {
    it('returns message for friendly API error', () => {
      expect(getErrorMessage({ message: 'User not found', status: 404 })).toBe(
        'User not found'
      );
    });

    it('maps status 0 to network error', () => {
      expect(getErrorMessage({ message: 'Error: connection', status: 0 })).toBe(
        ERROR_MESSAGES.NETWORK_ERROR
      );
    });

    it('maps status 401 to unauthorized', () => {
      expect(getErrorMessage({ message: 'Error: auth', status: 401 })).toBe(
        ERROR_MESSAGES.UNAUTHORIZED
      );
    });

    it('maps status 403 to forbidden', () => {
      expect(getErrorMessage({ message: 'Error: forbidden', status: 403 })).toBe(
        ERROR_MESSAGES.FORBIDDEN
      );
    });

    it('maps status 404 to not found', () => {
      expect(getErrorMessage({ message: 'Error: missing', status: 404 })).toBe(
        ERROR_MESSAGES.NOT_FOUND
      );
    });

    it('maps status 500 to server error', () => {
      expect(getErrorMessage({ message: 'Error: internal', status: 500 })).toBe(
        ERROR_MESSAGES.SERVER_ERROR
      );
    });

    it('maps status 504 to timeout', () => {
      expect(getErrorMessage({ message: 'Error: gateway', status: 504 })).toBe(
        ERROR_MESSAGES.TIMEOUT_ERROR
      );
    });

    it('uses detail for 400 with technical message', () => {
      expect(
        getErrorMessage({
          message: 'Error: validation',
          status: 400,
          detail: 'Name is required',
        })
      ).toBe('Name is required');
    });

    it('uses detail for 409 with technical message', () => {
      expect(
        getErrorMessage({
          message: 'Error: conflict',
          status: 409,
          detail: 'Email already exists',
        })
      ).toBe('Email already exists');
    });
  });

  describe('with Error objects', () => {
    it('returns friendly message for short errors', () => {
      expect(getErrorMessage(new Error('Something went wrong'))).toBe(
        'Something went wrong'
      );
    });

    it('returns network error for network-related messages', () => {
      expect(getErrorMessage(new Error('network failure'))).toBe(
        ERROR_MESSAGES.NETWORK_ERROR
      );
    });

    it('returns network error for fetch-related messages', () => {
      expect(getErrorMessage(new Error('fetch failed'))).toBe(
        ERROR_MESSAGES.NETWORK_ERROR
      );
    });

    it('returns timeout error for timeout messages', () => {
      expect(getErrorMessage(new Error('request timeout'))).toBe(
        ERROR_MESSAGES.TIMEOUT_ERROR
      );
    });

    it('returns fallback for technical Error: messages', () => {
      expect(getErrorMessage(new Error('Error: stack trace here'))).toBe(
        ERROR_MESSAGES.UNKNOWN_ERROR
      );
    });

    it('returns fallback for very long messages', () => {
      const longMessage = 'x'.repeat(201);
      expect(getErrorMessage(new Error(longMessage))).toBe(
        ERROR_MESSAGES.UNKNOWN_ERROR
      );
    });
  });

  describe('with string errors', () => {
    it('returns the string for short messages', () => {
      expect(getErrorMessage('Something broke')).toBe('Something broke');
    });

    it('returns fallback for empty string', () => {
      expect(getErrorMessage('')).toBe(ERROR_MESSAGES.UNKNOWN_ERROR);
    });

    it('returns fallback for very long string', () => {
      expect(getErrorMessage('x'.repeat(201))).toBe(ERROR_MESSAGES.UNKNOWN_ERROR);
    });
  });

  describe('with objects having message property', () => {
    it('extracts message from plain object', () => {
      expect(getErrorMessage({ message: 'Object error' })).toBe('Object error');
    });

    it('returns fallback for empty message', () => {
      expect(getErrorMessage({ message: '' })).toBe(ERROR_MESSAGES.UNKNOWN_ERROR);
    });

    it('returns fallback for non-string message', () => {
      expect(getErrorMessage({ message: 42 })).toBe(ERROR_MESSAGES.UNKNOWN_ERROR);
    });
  });

  describe('with other types', () => {
    it('returns fallback for number', () => {
      expect(getErrorMessage(42)).toBe(ERROR_MESSAGES.UNKNOWN_ERROR);
    });

    it('returns fallback for boolean', () => {
      expect(getErrorMessage(false)).toBe(ERROR_MESSAGES.UNKNOWN_ERROR);
    });

    it('returns fallback for array', () => {
      expect(getErrorMessage([1, 2, 3])).toBe(ERROR_MESSAGES.UNKNOWN_ERROR);
    });
  });
});

describe('ERROR_MESSAGES', () => {
  it('has all expected keys', () => {
    expect(ERROR_MESSAGES.NETWORK_ERROR).toBeDefined();
    expect(ERROR_MESSAGES.UNAUTHORIZED).toBeDefined();
    expect(ERROR_MESSAGES.FORBIDDEN).toBeDefined();
    expect(ERROR_MESSAGES.NOT_FOUND).toBeDefined();
    expect(ERROR_MESSAGES.SERVER_ERROR).toBeDefined();
    expect(ERROR_MESSAGES.UNKNOWN_ERROR).toBeDefined();
  });

  it('all values are non-empty strings', () => {
    for (const [, value] of Object.entries(ERROR_MESSAGES)) {
      expect(typeof value).toBe('string');
      expect(value.length).toBeGreaterThan(0);
    }
  });
});

describe('SUCCESS_MESSAGES', () => {
  it('has all expected keys', () => {
    expect(SUCCESS_MESSAGES.SAVED).toBeDefined();
    expect(SUCCESS_MESSAGES.CREATED).toBeDefined();
    expect(SUCCESS_MESSAGES.DELETED).toBeDefined();
    expect(SUCCESS_MESSAGES.LOGIN_SUCCESS).toBeDefined();
  });

  it('all values are non-empty strings', () => {
    for (const [, value] of Object.entries(SUCCESS_MESSAGES)) {
      expect(typeof value).toBe('string');
      expect(value.length).toBeGreaterThan(0);
    }
  });
});
