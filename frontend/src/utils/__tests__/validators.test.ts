import { isValidEmail, isValidUUID, isValidDateRange, isNonEmpty, isInRange } from '../validators';

describe('isValidEmail', () => {
  it('accepts valid email', () => {
    expect(isValidEmail('user@example.com')).toBe(true);
  });

  it('accepts email with dots and hyphens', () => {
    expect(isValidEmail('first.last@sub-domain.example.com')).toBe(true);
  });

  it('rejects empty string', () => {
    expect(isValidEmail('')).toBe(false);
  });

  it('rejects missing @', () => {
    expect(isValidEmail('userexample.com')).toBe(false);
  });

  it('rejects missing domain', () => {
    expect(isValidEmail('user@')).toBe(false);
  });

  it('rejects missing TLD', () => {
    expect(isValidEmail('user@example')).toBe(false);
  });

  it('rejects spaces', () => {
    expect(isValidEmail('user @example.com')).toBe(false);
  });
});

describe('isValidUUID', () => {
  it('accepts valid v4 UUID', () => {
    expect(isValidUUID('550e8400-e29b-41d4-a716-446655440000')).toBe(true);
  });

  it('accepts uppercase UUID', () => {
    expect(isValidUUID('550E8400-E29B-41D4-A716-446655440000')).toBe(true);
  });

  it('rejects empty string', () => {
    expect(isValidUUID('')).toBe(false);
  });

  it('rejects non-v4 UUID (wrong version digit)', () => {
    expect(isValidUUID('550e8400-e29b-31d4-a716-446655440000')).toBe(false);
  });

  it('rejects malformed UUID', () => {
    expect(isValidUUID('not-a-uuid')).toBe(false);
  });

  it('rejects UUID without hyphens', () => {
    expect(isValidUUID('550e8400e29b41d4a716446655440000')).toBe(false);
  });
});

describe('isValidDateRange', () => {
  it('accepts valid range', () => {
    expect(isValidDateRange('2025-01-01', '2025-12-31')).toBe(true);
  });

  it('accepts same start and end', () => {
    expect(isValidDateRange('2025-06-15', '2025-06-15')).toBe(true);
  });

  it('rejects end before start', () => {
    expect(isValidDateRange('2025-12-31', '2025-01-01')).toBe(false);
  });

  it('accepts Date objects', () => {
    expect(isValidDateRange(new Date(2025, 0, 1), new Date(2025, 11, 31))).toBe(true);
  });

  it('rejects invalid start date', () => {
    expect(isValidDateRange('invalid', '2025-01-01')).toBe(false);
  });

  it('rejects invalid end date', () => {
    expect(isValidDateRange('2025-01-01', 'invalid')).toBe(false);
  });
});

describe('isNonEmpty', () => {
  it('returns true for non-empty string', () => {
    expect(isNonEmpty('hello')).toBe(true);
  });

  it('returns false for empty string', () => {
    expect(isNonEmpty('')).toBe(false);
  });

  it('returns false for whitespace-only string', () => {
    expect(isNonEmpty('   ')).toBe(false);
  });

  it('returns false for null', () => {
    expect(isNonEmpty(null)).toBe(false);
  });

  it('returns false for undefined', () => {
    expect(isNonEmpty(undefined)).toBe(false);
  });

  it('returns true for non-empty array', () => {
    expect(isNonEmpty([1, 2])).toBe(true);
  });

  it('returns false for empty array', () => {
    expect(isNonEmpty([])).toBe(false);
  });

  it('returns true for number', () => {
    expect(isNonEmpty(0)).toBe(true);
  });

  it('returns true for object', () => {
    expect(isNonEmpty({})).toBe(true);
  });
});

describe('isInRange', () => {
  it('returns true for value in range', () => {
    expect(isInRange(5, 1, 10)).toBe(true);
  });

  it('returns true for value at min', () => {
    expect(isInRange(1, 1, 10)).toBe(true);
  });

  it('returns true for value at max', () => {
    expect(isInRange(10, 1, 10)).toBe(true);
  });

  it('returns false for value below min', () => {
    expect(isInRange(0, 1, 10)).toBe(false);
  });

  it('returns false for value above max', () => {
    expect(isInRange(11, 1, 10)).toBe(false);
  });

  it('returns false for NaN', () => {
    expect(isInRange(NaN, 1, 10)).toBe(false);
  });
});
