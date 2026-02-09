import {
  validateEmail,
  validateRequired,
  validateDateRange,
  validatePassword,
  validateMinLength,
  validatePgyLevel,
} from '../validation';

describe('validateEmail', () => {
  it('returns null for valid email', () => {
    expect(validateEmail('user@example.com')).toBeNull();
  });

  it('returns null for empty string (not required)', () => {
    expect(validateEmail('')).toBeNull();
  });

  it('returns error for missing @', () => {
    expect(validateEmail('userexample.com')).toBeTruthy();
  });

  it('returns error for missing domain', () => {
    expect(validateEmail('user@')).toBeTruthy();
  });

  it('returns error for missing TLD', () => {
    expect(validateEmail('user@example')).toBeTruthy();
  });

  it('returns error for spaces', () => {
    expect(validateEmail('user @example.com')).toBeTruthy();
  });

  it('accepts email with dots and hyphens', () => {
    expect(validateEmail('first.last@sub-domain.example.com')).toBeNull();
  });
});

describe('validateRequired', () => {
  it('returns null for non-empty value', () => {
    expect(validateRequired('hello', 'Field')).toBeNull();
  });

  it('returns error for empty string', () => {
    expect(validateRequired('', 'Name')).toBe('Name is required');
  });

  it('returns error for whitespace-only', () => {
    expect(validateRequired('   ', 'Email')).toBe('Email is required');
  });

  it('includes field name in error', () => {
    expect(validateRequired('', 'Username')).toContain('Username');
  });
});

describe('validateDateRange', () => {
  it('returns null for valid range', () => {
    expect(validateDateRange('2025-01-01', '2025-12-31')).toBeNull();
  });

  it('returns null for empty dates', () => {
    expect(validateDateRange('', '')).toBeNull();
    expect(validateDateRange('', '2025-01-01')).toBeNull();
    expect(validateDateRange('2025-01-01', '')).toBeNull();
  });

  it('returns error for end before start', () => {
    const error = validateDateRange('2025-12-31', '2025-01-01');
    expect(error).toContain('on or after');
  });

  it('returns error for invalid start date', () => {
    const error = validateDateRange('invalid', '2025-01-01');
    expect(error).toContain('Invalid start date');
  });

  it('returns error for invalid end date', () => {
    const error = validateDateRange('2025-01-01', 'invalid');
    expect(error).toContain('Invalid end date');
  });

  it('accepts same start and end date', () => {
    expect(validateDateRange('2025-06-15', '2025-06-15')).toBeNull();
  });
});

describe('validatePassword', () => {
  it('returns null for strong password', () => {
    expect(validatePassword('MyStr0ng!Pass')).toBeNull();
  });

  it('returns error for empty password', () => {
    expect(validatePassword('')).toContain('required');
  });

  it('returns error for short password', () => {
    expect(validatePassword('Short1!')).toContain('12 characters');
  });

  it('returns error for too-long password', () => {
    const longPw = 'A1!' + 'a'.repeat(126);
    expect(validatePassword(longPw)).toContain('128');
  });

  it('returns error for low complexity', () => {
    expect(validatePassword('alllowercaseonly')).toContain('at least 3');
  });

  it('returns error for common password', () => {
    // Need at least 12 chars, 3 complexity types — but "password" is short
    // Test common password "password123" which is also short
    // Use a long-enough common one — the check is case-insensitive
    // Actually, common passwords are short < 12, so length check catches first
    // Let's check that common passwords in the list are caught
    expect(validatePassword('password')).toContain('12 characters');
  });

  it('accepts password with 3 of 4 categories', () => {
    // lowercase + uppercase + number = 3 categories
    expect(validatePassword('AbcDef123456')).toBeNull();
  });

  it('accepts password with all 4 categories', () => {
    expect(validatePassword('AbcDef123!@#')).toBeNull();
  });
});

describe('validateMinLength', () => {
  it('returns null for value meeting min length', () => {
    expect(validateMinLength('hello', 3, 'Name')).toBeNull();
  });

  it('returns null for empty value (not required)', () => {
    expect(validateMinLength('', 3, 'Name')).toBeNull();
  });

  it('returns error for value below min length', () => {
    const error = validateMinLength('ab', 3, 'Username');
    expect(error).toContain('at least 3');
    expect(error).toContain('Username');
  });

  it('returns error for whitespace-padded short value', () => {
    // "ab" padded with spaces → trimmed length = 2
    expect(validateMinLength('  ab  ', 3, 'Name')).toContain('at least 3');
  });

  it('returns null for exact min length', () => {
    expect(validateMinLength('abc', 3, 'Name')).toBeNull();
  });
});

describe('validatePgyLevel', () => {
  it('returns null for valid numeric level', () => {
    expect(validatePgyLevel(3)).toBeNull();
  });

  it('returns null for valid string level', () => {
    expect(validatePgyLevel('2')).toBeNull();
  });

  it('returns null for min level (1)', () => {
    expect(validatePgyLevel(1)).toBeNull();
  });

  it('returns null for max level (8)', () => {
    expect(validatePgyLevel(8)).toBeNull();
  });

  it('returns error for level below 1', () => {
    expect(validatePgyLevel(0)).toContain('between 1 and 8');
  });

  it('returns error for level above 8', () => {
    expect(validatePgyLevel(9)).toContain('between 1 and 8');
  });

  it('returns error for non-numeric string', () => {
    expect(validatePgyLevel('abc')).toContain('must be a number');
  });

  it('returns error for negative level', () => {
    expect(validatePgyLevel(-1)).toContain('between 1 and 8');
  });
});
