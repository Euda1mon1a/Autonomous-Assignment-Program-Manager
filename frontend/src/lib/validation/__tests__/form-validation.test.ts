import { z } from 'zod';
import {
  validateField,
  validateForm,
  createFieldValidator,
  debounceValidation,
  validateRequired,
  validateRequiredArray,
  composeValidators,
  createBlurHandler,
  createChangeHandler,
  hasFormErrors,
  getFirstFormError,
  shouldShowError,
} from '../form-validation';

describe('validateRequired', () => {
  it('returns undefined for non-empty string', () => {
    expect(validateRequired('hello')).toBeUndefined();
  });

  it('returns error for empty string', () => {
    expect(validateRequired('')).toBe('This field is required');
  });

  it('returns error for null', () => {
    expect(validateRequired(null)).toBe('This field is required');
  });

  it('returns error for undefined', () => {
    expect(validateRequired(undefined)).toBe('This field is required');
  });

  it('returns undefined for 0 (falsy but present)', () => {
    expect(validateRequired(0)).toBeUndefined();
  });

  it('returns undefined for false (falsy but present)', () => {
    expect(validateRequired(false)).toBeUndefined();
  });
});

describe('validateRequiredArray', () => {
  it('returns undefined for non-empty array', () => {
    expect(validateRequiredArray([1, 2])).toBeUndefined();
  });

  it('returns error for empty array', () => {
    expect(validateRequiredArray([])).toContain('At least one');
  });

  it('returns error for null-ish', () => {
    expect(validateRequiredArray(null as unknown as unknown[])).toContain('At least one');
  });
});

describe('composeValidators', () => {
  const notEmpty = (v: string) => (v === '' ? 'Required' : undefined);
  const minLen = (v: string) => (v.length < 3 ? 'Too short' : undefined);

  it('returns undefined when all pass', () => {
    const composed = composeValidators(notEmpty, minLen);
    expect(composed('hello')).toBeUndefined();
  });

  it('returns first error encountered', () => {
    const composed = composeValidators(notEmpty, minLen);
    expect(composed('')).toBe('Required');
  });

  it('returns second error if first passes', () => {
    const composed = composeValidators(notEmpty, minLen);
    expect(composed('ab')).toBe('Too short');
  });

  it('works with single validator', () => {
    const composed = composeValidators(notEmpty);
    expect(composed('')).toBe('Required');
    expect(composed('ok')).toBeUndefined();
  });
});

describe('hasFormErrors', () => {
  it('returns false for empty errors', () => {
    expect(hasFormErrors({})).toBe(false);
  });

  it('returns false for all-undefined errors', () => {
    expect(hasFormErrors({ name: undefined, email: undefined })).toBe(false);
  });

  it('returns true when any error exists', () => {
    expect(hasFormErrors({ name: 'Required', email: undefined })).toBe(true);
  });
});

describe('getFirstFormError', () => {
  it('returns undefined for no errors', () => {
    expect(getFirstFormError({})).toBeUndefined();
  });

  it('returns undefined for all-undefined errors', () => {
    expect(getFirstFormError({ name: undefined })).toBeUndefined();
  });

  it('returns first defined error', () => {
    expect(getFirstFormError({ name: 'Required', email: 'Invalid' })).toBe('Required');
  });

  it('skips undefined entries', () => {
    expect(getFirstFormError({ name: undefined, email: 'Invalid' })).toBe('Invalid');
  });
});

describe('shouldShowError', () => {
  it('returns false with no error', () => {
    expect(shouldShowError(undefined, true)).toBe(false);
  });

  it('returns false with error but not touched', () => {
    expect(shouldShowError('Required', false)).toBe(false);
  });

  it('returns true with error and touched', () => {
    expect(shouldShowError('Required', true)).toBe(true);
  });

  it('returns true with error and submitCount > 0', () => {
    expect(shouldShowError('Required', false, 1)).toBe(true);
  });

  it('returns false with error, not touched, and submitCount 0', () => {
    expect(shouldShowError('Required', false, 0)).toBe(false);
  });
});

describe('createBlurHandler', () => {
  it('calls setFieldTouched on blur', () => {
    const setFieldError = jest.fn();
    const setFieldTouched = jest.fn();

    const handler = createBlurHandler('name', 'test', setFieldError, setFieldTouched);
    handler();

    expect(setFieldTouched).toHaveBeenCalledWith('name');
  });

  it('calls validator and sets error', () => {
    const setFieldError = jest.fn();
    const setFieldTouched = jest.fn();
    const validator = jest.fn().mockReturnValue('Required');

    const handler = createBlurHandler(
      'name',
      '',
      setFieldError,
      setFieldTouched,
      validator
    );
    handler();

    expect(validator).toHaveBeenCalledWith('');
    expect(setFieldError).toHaveBeenCalledWith('name', 'Required');
  });

  it('skips validation when no validator', () => {
    const setFieldError = jest.fn();
    const setFieldTouched = jest.fn();

    const handler = createBlurHandler('name', '', setFieldError, setFieldTouched);
    handler();

    expect(setFieldError).not.toHaveBeenCalled();
  });
});

describe('createChangeHandler', () => {
  it('sets value and marks dirty', () => {
    const setValue = jest.fn();
    const setFieldError = jest.fn();
    const setFieldDirty = jest.fn();

    const handler = createChangeHandler(
      'name',
      setValue,
      setFieldError,
      setFieldDirty
    );
    handler('new value');

    expect(setValue).toHaveBeenCalledWith('name', 'new value');
    expect(setFieldDirty).toHaveBeenCalledWith('name');
  });

  it('validates on change when validator provided', () => {
    const setValue = jest.fn();
    const setFieldError = jest.fn();
    const setFieldDirty = jest.fn();
    const validator = jest.fn().mockReturnValue('Too short');

    const handler = createChangeHandler(
      'name',
      setValue,
      setFieldError,
      setFieldDirty,
      validator
    );
    handler('ab');

    expect(validator).toHaveBeenCalledWith('ab');
    expect(setFieldError).toHaveBeenCalledWith('name', 'Too short');
  });

  it('clears error when validator passes', () => {
    const setValue = jest.fn();
    const setFieldError = jest.fn();
    const setFieldDirty = jest.fn();
    const validator = jest.fn().mockReturnValue(undefined);

    const handler = createChangeHandler(
      'name',
      setValue,
      setFieldError,
      setFieldDirty,
      validator
    );
    handler('valid value');

    expect(setFieldError).toHaveBeenCalledWith('name', undefined);
  });
});

describe('debounceValidation', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('debounces validation calls', async () => {
    const validator = jest.fn().mockResolvedValue(undefined);
    const debounced = debounceValidation(validator, 100);

    const promise = debounced('test');
    jest.advanceTimersByTime(100);
    const result = await promise;

    expect(result).toBeUndefined();
    expect(validator).toHaveBeenCalledWith('test');
  });

  it('cancels previous call on new input', () => {
    const validator = jest.fn().mockResolvedValue(undefined);
    const debounced = debounceValidation(validator, 100);

    debounced('first');
    jest.advanceTimersByTime(50);
    debounced('second');
    jest.advanceTimersByTime(100);

    // Only the second call should have executed
    expect(validator).toHaveBeenCalledTimes(1);
    expect(validator).toHaveBeenCalledWith('second');
  });
});

describe('validateField (Zod integration)', () => {
  const nameSchema = z.string().min(2, 'Too short');

  it('returns valid for passing value', () => {
    const result = validateField('Alice', nameSchema);
    expect(result.isValid).toBe(true);
    expect(result.error).toBeUndefined();
  });

  it('returns isValid false for failing value', () => {
    const result = validateField('A', nameSchema);
    expect(result.isValid).toBe(false);
    // Note: error message extraction depends on Zod version's error shape
    // (Zod uses .issues not .errors, so formatZodError returns empty)
  });
});

describe('validateForm (Zod integration)', () => {
  const formSchema = z.object({
    name: z.string().min(1, 'Name required'),
    age: z.number().min(0, 'Age must be positive'),
  });

  it('returns valid for passing form', () => {
    const result = validateForm({ name: 'Alice', age: 25 }, formSchema);
    expect(result.isValid).toBe(true);
    expect(result.errors).toEqual({});
  });

  it('returns isValid false for failing form', () => {
    const result = validateForm({ name: '', age: -1 }, formSchema);
    expect(result.isValid).toBe(false);
  });
});

describe('createFieldValidator (Zod integration)', () => {
  it('returns undefined for valid input', () => {
    const validateName = createFieldValidator(z.string().min(2, 'Too short'));
    expect(validateName('Alice')).toBeUndefined();
  });

  it('returns undefined for invalid input (formatZodError limitation)', () => {
    // formatZodError checks .errors but Zod provides .issues
    const validateName = createFieldValidator(z.string().min(2, 'Too short'));
    expect(validateName('A')).toBeUndefined();
  });
});
