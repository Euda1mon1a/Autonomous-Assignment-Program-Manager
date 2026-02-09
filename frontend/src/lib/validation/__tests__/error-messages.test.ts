import {
  validationErrors,
  getFieldError,
  formatZodError,
  getApiErrorMessage,
} from '../error-messages';

describe('validationErrors', () => {
  describe('function messages', () => {
    it('required returns field name', () => {
      expect(validationErrors.required('Name')).toBe('Name is required');
    });

    it('minLength includes field and count', () => {
      expect(validationErrors.minLength('Username', 3)).toContain('Username');
      expect(validationErrors.minLength('Username', 3)).toContain('3');
    });

    it('maxLength includes field and count', () => {
      expect(validationErrors.maxLength('Bio', 500)).toContain('500');
    });

    it('emailDomain lists allowed domains', () => {
      const msg = validationErrors.emailDomain(['hospital.org', 'mil.gov']);
      expect(msg).toContain('hospital.org');
      expect(msg).toContain('mil.gov');
    });

    it('dateTooSoon includes days', () => {
      expect(validationErrors.dateTooSoon(7)).toContain('7 days');
    });

    it('fileTooLarge includes sizes', () => {
      expect(validationErrors.fileTooLarge('10.5', 5)).toContain('10.5MB');
      expect(validationErrors.fileTooLarge('10.5', 5)).toContain('5MB');
    });

    it('passwordTooShort includes min', () => {
      expect(validationErrors.passwordTooShort(12)).toContain('12');
    });

    it('duplicateValues includes field name', () => {
      expect(validationErrors.duplicateValues('Tags')).toContain('Tags');
    });
  });

  describe('static messages', () => {
    it('has required field error', () => {
      expect(validationErrors.requiredField).toBeTruthy();
    });

    it('has invalid email error', () => {
      expect(validationErrors.invalidEmail).toBeTruthy();
    });

    it('has swap-specific errors', () => {
      expect(validationErrors.cannotSwapWithSelf).toContain('yourself');
    });

    it('has generic errors', () => {
      expect(validationErrors.somethingWentWrong).toBeTruthy();
      expect(validationErrors.networkError).toBeTruthy();
    });
  });
});

describe('getFieldError', () => {
  it('calls function-type errors with field name', () => {
    const result = getFieldError('Email', 'required');
    expect(result).toBe('Email is required');
  });

  it('returns static string for non-function errors', () => {
    const result = getFieldError('', 'requiredField');
    expect(result).toBe('This field is required');
  });

  it('passes additional args to function errors', () => {
    const result = getFieldError('Name', 'minLength', 5);
    expect(result).toContain('Name');
    expect(result).toContain('5');
  });
});

describe('formatZodError', () => {
  it('extracts field errors from Zod-like error', () => {
    const zodError = {
      errors: [
        { path: ['name'], message: 'Name is required' },
        { path: ['email'], message: 'Invalid email' },
      ],
    };
    const result = formatZodError(zodError);
    expect(result.name).toBe('Name is required');
    expect(result.email).toBe('Invalid email');
  });

  it('joins nested paths with dots', () => {
    const zodError = {
      errors: [{ path: ['address', 'zipCode'], message: 'Invalid zip' }],
    };
    const result = formatZodError(zodError);
    expect(result['address.zipCode']).toBe('Invalid zip');
  });

  it('handles numeric paths', () => {
    const zodError = {
      errors: [{ path: ['items', 0, 'name'], message: 'Required' }],
    };
    const result = formatZodError(zodError);
    expect(result['items.0.name']).toBe('Required');
  });

  it('returns empty object for non-Zod errors', () => {
    expect(formatZodError('string error')).toEqual({});
    expect(formatZodError(null)).toEqual({});
    expect(formatZodError(undefined)).toEqual({});
  });

  it('returns empty object for errors without errors array', () => {
    expect(formatZodError({ message: 'oops' })).toEqual({});
  });
});

describe('getApiErrorMessage', () => {
  it('extracts error from response.data.error', () => {
    const error = { response: { data: { error: 'Not found' } } };
    expect(getApiErrorMessage(error)).toBe('Not found');
  });

  it('extracts message from response.data.message', () => {
    const error = { response: { data: { message: 'Server error' } } };
    expect(getApiErrorMessage(error)).toBe('Server error');
  });

  it('falls back to error.message', () => {
    const error = { message: 'Network error' };
    expect(getApiErrorMessage(error)).toBe('Network error');
  });

  it('returns generic error for non-object', () => {
    expect(getApiErrorMessage('string')).toBe(validationErrors.somethingWentWrong);
  });

  it('returns generic error for null', () => {
    expect(getApiErrorMessage(null)).toBe(validationErrors.somethingWentWrong);
  });

  it('prefers response.data.error over message', () => {
    const error = {
      response: { data: { error: 'Specific error' } },
      message: 'Generic',
    };
    expect(getApiErrorMessage(error)).toBe('Specific error');
  });
});
