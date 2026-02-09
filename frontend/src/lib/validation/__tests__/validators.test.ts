import {
  validateFutureDate,
  validateDateRange,
  validateEmailDomain,
  validateFileExtension,
  validateFileSize,
  validatePgyLevel,
  validateFacultyRole,
  validateAssignmentRole,
  validateUniqueValues,
  validatePasswordStrength,
} from '../validators';

describe('validateFutureDate', () => {
  it('accepts a future date', () => {
    const future = new Date();
    future.setDate(future.getDate() + 10);
    const result = validateFutureDate(future.toISOString());
    expect(result.isValid).toBe(true);
  });

  it('rejects a past date', () => {
    const result = validateFutureDate('2020-01-01');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('future');
  });

  it('accepts date meeting minDaysAhead', () => {
    const future = new Date();
    future.setDate(future.getDate() + 7);
    const result = validateFutureDate(future.toISOString(), 5);
    expect(result.isValid).toBe(true);
  });

  it('rejects date not meeting minDaysAhead', () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const result = validateFutureDate(tomorrow.toISOString(), 5);
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('5 days');
  });
});

describe('validateDateRange', () => {
  it('accepts valid range', () => {
    const result = validateDateRange('2025-01-01', '2025-12-31');
    expect(result.isValid).toBe(true);
  });

  it('accepts same start and end', () => {
    const result = validateDateRange('2025-06-15', '2025-06-15');
    expect(result.isValid).toBe(true);
  });

  it('rejects end before start', () => {
    const result = validateDateRange('2025-12-31', '2025-01-01');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('after');
  });
});

describe('validateEmailDomain', () => {
  it('accepts valid email without domain restriction', () => {
    const result = validateEmailDomain('user@example.com');
    expect(result.isValid).toBe(true);
  });

  it('rejects email without @', () => {
    const result = validateEmailDomain('invalid-email');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('Invalid email');
  });

  it('rejects empty email', () => {
    const result = validateEmailDomain('');
    expect(result.isValid).toBe(false);
  });

  it('accepts email with allowed domain', () => {
    const result = validateEmailDomain('user@hospital.org', ['hospital.org', 'mil.gov']);
    expect(result.isValid).toBe(true);
  });

  it('rejects email with disallowed domain', () => {
    const result = validateEmailDomain('user@gmail.com', ['hospital.org']);
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('hospital.org');
  });

  it('is case-insensitive for domain matching', () => {
    const result = validateEmailDomain('user@Hospital.Org', ['hospital.org']);
    expect(result.isValid).toBe(true);
  });
});

describe('validateFileExtension', () => {
  it('accepts valid extension', () => {
    const result = validateFileExtension('report.csv', ['csv', 'xlsx']);
    expect(result.isValid).toBe(true);
  });

  it('rejects disallowed extension', () => {
    const result = validateFileExtension('virus.exe', ['csv', 'xlsx']);
    expect(result.isValid).toBe(false);
  });

  it('rejects file without extension', () => {
    const result = validateFileExtension('noext', ['csv']);
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('extension');
  });

  it('rejects empty filename', () => {
    const result = validateFileExtension('', ['csv']);
    expect(result.isValid).toBe(false);
  });

  it('is case-insensitive', () => {
    const result = validateFileExtension('data.CSV', ['csv']);
    expect(result.isValid).toBe(true);
  });
});

describe('validateFileSize', () => {
  it('accepts file within limit', () => {
    const result = validateFileSize(1024 * 1024, 5); // 1MB < 5MB
    expect(result.isValid).toBe(true);
  });

  it('rejects file exceeding limit', () => {
    const result = validateFileSize(10 * 1024 * 1024, 5); // 10MB > 5MB
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('10.0MB');
    expect(result.error).toContain('5MB');
  });

  it('accepts file exactly at limit', () => {
    const result = validateFileSize(5 * 1024 * 1024, 5); // 5MB = 5MB
    expect(result.isValid).toBe(true);
  });
});

describe('validatePgyLevel', () => {
  it('accepts null for faculty', () => {
    const result = validatePgyLevel(null, 'faculty');
    expect(result.isValid).toBe(true);
  });

  it('rejects PGY level for faculty', () => {
    const result = validatePgyLevel(2, 'faculty');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('Faculty cannot');
  });

  it('accepts valid PGY level for resident', () => {
    expect(validatePgyLevel(1, 'resident').isValid).toBe(true);
    expect(validatePgyLevel(2, 'resident').isValid).toBe(true);
    expect(validatePgyLevel(3, 'resident').isValid).toBe(true);
  });

  it('rejects null PGY for resident', () => {
    const result = validatePgyLevel(null, 'resident');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('must have');
  });

  it('rejects out of range PGY for resident', () => {
    expect(validatePgyLevel(0, 'resident').isValid).toBe(false);
    expect(validatePgyLevel(4, 'resident').isValid).toBe(false);
  });

  it('accepts any for unknown person types', () => {
    const result = validatePgyLevel(null, 'other');
    expect(result.isValid).toBe(true);
  });
});

describe('validateFacultyRole', () => {
  it('rejects faculty role for residents', () => {
    const result = validateFacultyRole('attending', 'resident');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('Residents cannot');
  });

  it('accepts null role for residents', () => {
    const result = validateFacultyRole(null, 'resident');
    expect(result.isValid).toBe(true);
  });

  it('accepts role for faculty', () => {
    const result = validateFacultyRole('attending', 'faculty');
    expect(result.isValid).toBe(true);
  });
});

describe('validateAssignmentRole', () => {
  it('rejects supervising role for non-faculty', () => {
    const result = validateAssignmentRole('supervising', 'resident');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('faculty');
  });

  it('accepts supervising role for faculty', () => {
    const result = validateAssignmentRole('supervising', 'faculty');
    expect(result.isValid).toBe(true);
  });

  it('accepts primary role for resident', () => {
    const result = validateAssignmentRole('primary', 'resident');
    expect(result.isValid).toBe(true);
  });
});

describe('validateUniqueValues', () => {
  it('accepts all unique values', () => {
    const result = validateUniqueValues([1, 2, 3]);
    expect(result.isValid).toBe(true);
  });

  it('detects duplicates', () => {
    const result = validateUniqueValues([1, 2, 2, 3]);
    expect(result.isValid).toBe(false);
    expect(result.duplicates).toEqual([2]);
  });

  it('includes field name in error', () => {
    const result = validateUniqueValues(['a', 'a'], 'Tags');
    expect(result.error).toContain('Tags');
  });

  it('uses generic message without field name', () => {
    const result = validateUniqueValues([1, 1]);
    expect(result.error).toContain('duplicate');
  });

  it('handles empty array', () => {
    const result = validateUniqueValues([]);
    expect(result.isValid).toBe(true);
  });

  it('detects multiple duplicates', () => {
    const result = validateUniqueValues(['a', 'b', 'a', 'b', 'c']);
    expect(result.duplicates).toEqual(['a', 'b']);
  });
});

describe('validatePasswordStrength', () => {
  it('accepts strong password', () => {
    const result = validatePasswordStrength('MyStr0ng!Pass');
    expect(result.isValid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('rejects short password', () => {
    const result = validatePasswordStrength('Short!1');
    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('Password must be at least 12 characters');
  });

  it('rejects no uppercase', () => {
    const result = validatePasswordStrength('lowercaseonly123!');
    expect(result.errors).toContain(
      'Password must contain at least one uppercase letter'
    );
  });

  it('rejects no lowercase', () => {
    const result = validatePasswordStrength('UPPERCASEONLY123!');
    expect(result.errors).toContain(
      'Password must contain at least one lowercase letter'
    );
  });

  it('rejects no digit', () => {
    const result = validatePasswordStrength('NoDigitsHere!!!');
    expect(result.errors).toContain('Password must contain at least one digit');
  });

  it('rejects no special character', () => {
    const result = validatePasswordStrength('NoSpecials1234');
    expect(result.errors).toContain(
      'Password must contain at least one special character'
    );
  });

  it('rates weak passwords', () => {
    const result = validatePasswordStrength('weak');
    expect(result.strength).toBe('weak');
  });

  it('rates medium passwords', () => {
    const result = validatePasswordStrength('MediumPass12');
    expect(result.strength).toBe('medium');
  });

  it('rates strong passwords with extra length and special chars', () => {
    const result = validatePasswordStrength('VeryStr0ng!!Password');
    expect(result.strength).toBe('strong');
  });
});
