/**
 * Tests for DOW convention in faculty-activity.ts.
 *
 * Faculty activities use Python weekday convention (0=Monday, 6=Sunday),
 * NOT PG EXTRACT(DOW) convention (0=Sunday, 6=Saturday).
 *
 * See docs/architecture/DOW_CONVENTION_BUG.md for full reference.
 */

import {
  DAY_LABELS,
  DAY_LABELS_SHORT,
  isWeekend,
  type DayOfWeek,
} from '@/types/faculty-activity';

describe('Faculty Activity DOW Convention (Python weekday)', () => {
  describe('DAY_LABELS', () => {
    it('maps 0 to Monday (not Sunday)', () => {
      expect(DAY_LABELS[0 as DayOfWeek]).toBe('Monday');
    });

    it('maps 4 to Friday', () => {
      expect(DAY_LABELS[4 as DayOfWeek]).toBe('Friday');
    });

    it('maps 5 to Saturday', () => {
      expect(DAY_LABELS[5 as DayOfWeek]).toBe('Saturday');
    });

    it('maps 6 to Sunday (not Saturday)', () => {
      expect(DAY_LABELS[6 as DayOfWeek]).toBe('Sunday');
    });
  });

  describe('DAY_LABELS_SHORT', () => {
    it('maps 0 to Mon', () => {
      expect(DAY_LABELS_SHORT[0 as DayOfWeek]).toBe('Mon');
    });

    it('maps 4 to Fri', () => {
      expect(DAY_LABELS_SHORT[4 as DayOfWeek]).toBe('Fri');
    });

    it('maps 6 to Sun', () => {
      expect(DAY_LABELS_SHORT[6 as DayOfWeek]).toBe('Sun');
    });
  });

  describe('isWeekend', () => {
    it('Monday (0) is NOT weekend', () => {
      expect(isWeekend(0 as DayOfWeek)).toBe(false);
    });

    it('Tuesday (1) is NOT weekend', () => {
      expect(isWeekend(1 as DayOfWeek)).toBe(false);
    });

    it('Wednesday (2) is NOT weekend', () => {
      expect(isWeekend(2 as DayOfWeek)).toBe(false);
    });

    it('Thursday (3) is NOT weekend', () => {
      expect(isWeekend(3 as DayOfWeek)).toBe(false);
    });

    it('Friday (4) is NOT weekend', () => {
      expect(isWeekend(4 as DayOfWeek)).toBe(false);
    });

    it('Saturday (5) IS weekend', () => {
      expect(isWeekend(5 as DayOfWeek)).toBe(true);
    });

    it('Sunday (6) IS weekend', () => {
      expect(isWeekend(6 as DayOfWeek)).toBe(true);
    });
  });
});
