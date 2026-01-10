/**
 * Tests for FMIT Timeline types and utility functions.
 *
 * Tests cover:
 * - getFmitWeekDates: Friday-Thursday week boundary calculation
 * - getWeeksInRange: FMIT week period generation
 */

import { getFmitWeekDates, getWeeksInRange } from '../types';

// ============================================================================
// getFmitWeekDates Tests
// ============================================================================

describe('getFmitWeekDates', () => {
  it('should return Friday for a Friday date', () => {
    // 2026-01-02 is a Friday
    const date = new Date('2026-01-02');
    const { friday, thursday } = getFmitWeekDates(date);

    expect(friday.toISOString().split('T')[0]).toBe('2026-01-02');
    expect(thursday.toISOString().split('T')[0]).toBe('2026-01-08');
  });

  it('should return previous Friday for a Saturday date', () => {
    // 2026-01-03 is a Saturday
    const date = new Date('2026-01-03');
    const { friday, thursday } = getFmitWeekDates(date);

    expect(friday.toISOString().split('T')[0]).toBe('2026-01-02');
    expect(thursday.toISOString().split('T')[0]).toBe('2026-01-08');
  });

  it('should return previous Friday for a Sunday date', () => {
    // 2026-01-04 is a Sunday
    const date = new Date('2026-01-04');
    const { friday, thursday } = getFmitWeekDates(date);

    expect(friday.toISOString().split('T')[0]).toBe('2026-01-02');
    expect(thursday.toISOString().split('T')[0]).toBe('2026-01-08');
  });

  it('should return previous Friday for a Monday date', () => {
    // 2026-01-05 is a Monday
    const date = new Date('2026-01-05');
    const { friday, thursday } = getFmitWeekDates(date);

    expect(friday.toISOString().split('T')[0]).toBe('2026-01-02');
    expect(thursday.toISOString().split('T')[0]).toBe('2026-01-08');
  });

  it('should return previous Friday for a Tuesday date', () => {
    // 2026-01-06 is a Tuesday
    const date = new Date('2026-01-06');
    const { friday, thursday } = getFmitWeekDates(date);

    expect(friday.toISOString().split('T')[0]).toBe('2026-01-02');
    expect(thursday.toISOString().split('T')[0]).toBe('2026-01-08');
  });

  it('should return previous Friday for a Wednesday date', () => {
    // 2026-01-07 is a Wednesday
    const date = new Date('2026-01-07');
    const { friday, thursday } = getFmitWeekDates(date);

    expect(friday.toISOString().split('T')[0]).toBe('2026-01-02');
    expect(thursday.toISOString().split('T')[0]).toBe('2026-01-08');
  });

  it('should return previous Friday for a Thursday date', () => {
    // 2026-01-08 is a Thursday
    const date = new Date('2026-01-08');
    const { friday, thursday } = getFmitWeekDates(date);

    expect(friday.toISOString().split('T')[0]).toBe('2026-01-02');
    expect(thursday.toISOString().split('T')[0]).toBe('2026-01-08');
  });

  it('should handle week boundary correctly at Friday', () => {
    // 2026-01-09 is a Friday (new week starts)
    const date = new Date('2026-01-09');
    const { friday, thursday } = getFmitWeekDates(date);

    expect(friday.toISOString().split('T')[0]).toBe('2026-01-09');
    expect(thursday.toISOString().split('T')[0]).toBe('2026-01-15');
  });

  it('should always return a 7-day span from Friday to Thursday', () => {
    const testDates = [
      '2026-01-02', // Friday
      '2026-01-03', // Saturday
      '2026-01-04', // Sunday
      '2026-01-05', // Monday
      '2026-01-06', // Tuesday
      '2026-01-07', // Wednesday
      '2026-01-08', // Thursday
    ];

    for (const dateStr of testDates) {
      const date = new Date(dateStr);
      const { friday, thursday } = getFmitWeekDates(date);

      // Verify Friday is day 5 (Friday) - use UTC to match implementation
      expect(friday.getUTCDay()).toBe(5);

      // Verify Thursday is day 4 (Thursday) - use UTC to match implementation
      expect(thursday.getUTCDay()).toBe(4);

      // Verify span is exactly 6 days
      const daysDiff = (thursday.getTime() - friday.getTime()) / (1000 * 60 * 60 * 24);
      expect(daysDiff).toBe(6);
    }
  });
});

// ============================================================================
// getWeeksInRange Tests
// ============================================================================

describe('getWeeksInRange', () => {
  it('should return weeks starting on Friday', () => {
    // Start on a Wednesday, should align to previous Friday
    const periods = getWeeksInRange('2026-01-07', '2026-01-31');

    // First period should start on Friday 2026-01-02
    expect(periods[0].startDate).toBe('2026-01-02');

    // All weeks should start on Friday (use UTC to match implementation)
    for (const period of periods) {
      const startDate = new Date(period.startDate);
      expect(startDate.getUTCDay()).toBe(5); // Friday
    }
  });

  it('should return weeks ending on Thursday', () => {
    const periods = getWeeksInRange('2026-01-02', '2026-01-31');

    // All weeks except possibly the last should end on Thursday (use UTC)
    for (let i = 0; i < periods.length - 1; i++) {
      const endDate = new Date(periods[i].endDate);
      expect(endDate.getUTCDay()).toBe(4); // Thursday
    }
  });

  it('should handle start date that is already Friday', () => {
    // 2026-01-02 is a Friday
    const periods = getWeeksInRange('2026-01-02', '2026-01-15');

    expect(periods[0].startDate).toBe('2026-01-02');
    expect(periods[0].endDate).toBe('2026-01-08');
    expect(periods[1].startDate).toBe('2026-01-09');
    expect(periods[1].endDate).toBe('2026-01-15');
  });

  it('should truncate last week end date if it exceeds range', () => {
    // End on a Monday (2026-01-12), which is mid-week
    const periods = getWeeksInRange('2026-01-02', '2026-01-12');

    const lastPeriod = periods[periods.length - 1];
    expect(lastPeriod.endDate).toBe('2026-01-12');
  });

  it('should have sequential week numbers', () => {
    const periods = getWeeksInRange('2026-01-02', '2026-02-28');

    for (let i = 0; i < periods.length; i++) {
      expect(periods[i].label).toBe(`Week ${i + 1}`);
    }
  });

  it('should generate correct number of weeks', () => {
    // 4 complete FMIT weeks from 2026-01-02 (Fri) to 2026-01-29 (Thu)
    const periods = getWeeksInRange('2026-01-02', '2026-01-29');

    expect(periods.length).toBe(4);
    expect(periods[0].startDate).toBe('2026-01-02');
    expect(periods[0].endDate).toBe('2026-01-08');
    expect(periods[3].startDate).toBe('2026-01-23');
    expect(periods[3].endDate).toBe('2026-01-29');
  });

  it('should handle single week range', () => {
    const periods = getWeeksInRange('2026-01-05', '2026-01-07');

    // Should include the FMIT week containing these dates
    expect(periods.length).toBe(1);
    expect(periods[0].startDate).toBe('2026-01-02');
  });

  it('should align to previous Friday even when start date is Thursday', () => {
    // 2026-01-08 is a Thursday (end of FMIT week starting 2026-01-02)
    const periods = getWeeksInRange('2026-01-08', '2026-01-22');

    // Should start from the Friday of that week (2026-01-02)
    expect(periods[0].startDate).toBe('2026-01-02');
  });

  it('should handle start date on Saturday correctly', () => {
    // 2026-01-03 is a Saturday
    const periods = getWeeksInRange('2026-01-03', '2026-01-15');

    // Should align to previous Friday (2026-01-02)
    expect(periods[0].startDate).toBe('2026-01-02');
    expect(periods[0].endDate).toBe('2026-01-08');
  });

  it('should handle start date on Sunday correctly', () => {
    // 2026-01-04 is a Sunday
    const periods = getWeeksInRange('2026-01-04', '2026-01-15');

    // Should align to previous Friday (2026-01-02)
    expect(periods[0].startDate).toBe('2026-01-02');
    expect(periods[0].endDate).toBe('2026-01-08');
  });
});
