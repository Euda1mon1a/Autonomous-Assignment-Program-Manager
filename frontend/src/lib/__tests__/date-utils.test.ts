import {
  formatLocalDate,
  getTodayLocal,
  getFirstOfMonthLocal,
  getLastOfMonthLocal,
  addDaysLocal,
  getMondayOfWeek,
} from '../date-utils';

describe('formatLocalDate', () => {
  it('formats a date as YYYY-MM-DD', () => {
    const date = new Date(2025, 0, 15); // Jan 15, 2025
    expect(formatLocalDate(date)).toBe('2025-01-15');
  });

  it('zero-pads single-digit months', () => {
    const date = new Date(2025, 2, 5); // Mar 5
    expect(formatLocalDate(date)).toBe('2025-03-05');
  });

  it('zero-pads single-digit days', () => {
    const date = new Date(2025, 11, 1); // Dec 1
    expect(formatLocalDate(date)).toBe('2025-12-01');
  });

  it('handles end of year', () => {
    const date = new Date(2025, 11, 31); // Dec 31
    expect(formatLocalDate(date)).toBe('2025-12-31');
  });

  it('handles beginning of year', () => {
    const date = new Date(2025, 0, 1); // Jan 1
    expect(formatLocalDate(date)).toBe('2025-01-01');
  });
});

describe('getTodayLocal', () => {
  it('returns a string in YYYY-MM-DD format', () => {
    const result = getTodayLocal();
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it('matches the current local date', () => {
    const now = new Date();
    const expected = formatLocalDate(now);
    expect(getTodayLocal()).toBe(expected);
  });
});

describe('getFirstOfMonthLocal', () => {
  it('returns a string ending in -01', () => {
    const result = getFirstOfMonthLocal();
    expect(result).toMatch(/^\d{4}-\d{2}-01$/);
  });
});

describe('getLastOfMonthLocal', () => {
  it('returns a valid date string', () => {
    const result = getLastOfMonthLocal();
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it('returns a day between 28 and 31', () => {
    const result = getLastOfMonthLocal();
    const day = parseInt(result.split('-')[2], 10);
    expect(day).toBeGreaterThanOrEqual(28);
    expect(day).toBeLessThanOrEqual(31);
  });
});

describe('addDaysLocal', () => {
  it('adds positive days', () => {
    expect(addDaysLocal('2025-01-01', 5)).toBe('2025-01-06');
  });

  it('subtracts with negative days', () => {
    expect(addDaysLocal('2025-01-10', -5)).toBe('2025-01-05');
  });

  it('crosses month boundary', () => {
    expect(addDaysLocal('2025-01-30', 3)).toBe('2025-02-02');
  });

  it('crosses year boundary', () => {
    expect(addDaysLocal('2025-12-30', 5)).toBe('2026-01-04');
  });

  it('adds zero days', () => {
    expect(addDaysLocal('2025-06-15', 0)).toBe('2025-06-15');
  });

  it('handles leap year', () => {
    expect(addDaysLocal('2024-02-28', 1)).toBe('2024-02-29');
    expect(addDaysLocal('2024-02-29', 1)).toBe('2024-03-01');
  });
});

describe('getMondayOfWeek', () => {
  it('returns Monday for a Wednesday', () => {
    // Jan 15, 2025 is a Wednesday
    const wed = new Date(2025, 0, 15);
    expect(getMondayOfWeek(wed)).toBe('2025-01-13');
  });

  it('returns same day for a Monday', () => {
    // Jan 13, 2025 is a Monday
    const mon = new Date(2025, 0, 13);
    expect(getMondayOfWeek(mon)).toBe('2025-01-13');
  });

  it('returns previous Monday for a Sunday', () => {
    // Jan 19, 2025 is a Sunday
    const sun = new Date(2025, 0, 19);
    expect(getMondayOfWeek(sun)).toBe('2025-01-13');
  });

  it('returns previous Monday for a Saturday', () => {
    // Jan 18, 2025 is a Saturday
    const sat = new Date(2025, 0, 18);
    expect(getMondayOfWeek(sat)).toBe('2025-01-13');
  });

  it('handles month boundary', () => {
    // Feb 1, 2025 is a Saturday → Monday is Jan 27
    const feb1 = new Date(2025, 1, 1);
    expect(getMondayOfWeek(feb1)).toBe('2025-01-27');
  });
});
