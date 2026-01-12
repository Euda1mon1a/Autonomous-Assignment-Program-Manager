/**
 * @jest-environment node
 */
import {
  calculateTierFromRole,
  canViewOtherSchedules,
  canExportOtherSchedules,
  canMakeScheduleChanges,
  canPerformDestructiveOperations,
  getRiskBarTooltip,
  getRiskBarLabel,
} from '../tierUtils';

describe('tierUtils', () => {
  describe('calculateTierFromRole', () => {
    it('returns tier 2 for admin role', () => {
      expect(calculateTierFromRole('admin')).toBe(2);
      expect(calculateTierFromRole('ADMIN')).toBe(2);
      expect(calculateTierFromRole('Admin')).toBe(2);
    });

    it('returns tier 1 for coordinator role', () => {
      expect(calculateTierFromRole('coordinator')).toBe(1);
      expect(calculateTierFromRole('COORDINATOR')).toBe(1);
      expect(calculateTierFromRole('Coordinator')).toBe(1);
    });

    it('returns tier 0 for faculty role', () => {
      expect(calculateTierFromRole('faculty')).toBe(0);
      expect(calculateTierFromRole('FACULTY')).toBe(0);
    });

    it('returns tier 0 for resident role', () => {
      expect(calculateTierFromRole('resident')).toBe(0);
      expect(calculateTierFromRole('RESIDENT')).toBe(0);
    });

    it('returns tier 0 for undefined role', () => {
      expect(calculateTierFromRole(undefined)).toBe(0);
    });

    it('returns tier 0 for unknown role', () => {
      expect(calculateTierFromRole('unknown')).toBe(0);
      expect(calculateTierFromRole('superuser')).toBe(0);
    });
  });

  describe('canViewOtherSchedules', () => {
    it('returns false for tier 0', () => {
      expect(canViewOtherSchedules(0)).toBe(false);
    });

    it('returns true for tier 1', () => {
      expect(canViewOtherSchedules(1)).toBe(true);
    });

    it('returns true for tier 2', () => {
      expect(canViewOtherSchedules(2)).toBe(true);
    });
  });

  describe('canExportOtherSchedules', () => {
    it('returns false for tier 0', () => {
      expect(canExportOtherSchedules(0)).toBe(false);
    });

    it('returns true for tier 1', () => {
      expect(canExportOtherSchedules(1)).toBe(true);
    });

    it('returns true for tier 2', () => {
      expect(canExportOtherSchedules(2)).toBe(true);
    });
  });

  describe('canMakeScheduleChanges', () => {
    it('returns false for tier 0', () => {
      expect(canMakeScheduleChanges(0)).toBe(false);
    });

    it('returns true for tier 1', () => {
      expect(canMakeScheduleChanges(1)).toBe(true);
    });

    it('returns true for tier 2', () => {
      expect(canMakeScheduleChanges(2)).toBe(true);
    });
  });

  describe('canPerformDestructiveOperations', () => {
    it('returns false for tier 0', () => {
      expect(canPerformDestructiveOperations(0)).toBe(false);
    });

    it('returns false for tier 1', () => {
      expect(canPerformDestructiveOperations(1)).toBe(false);
    });

    it('returns true for tier 2', () => {
      expect(canPerformDestructiveOperations(2)).toBe(true);
    });
  });

  describe('getRiskBarTooltip', () => {
    it('returns appropriate tooltip for tier 0', () => {
      const tooltip = getRiskBarTooltip(0);
      expect(tooltip).toContain('view your own schedule');
      expect(tooltip).toContain('cannot make changes');
    });

    it('returns appropriate tooltip for tier 1 viewing self', () => {
      const tooltip = getRiskBarTooltip(1, false);
      expect(tooltip).toContain('reversible changes');
      expect(tooltip).toContain('within your assigned scope');
    });

    it('returns appropriate tooltip for tier 1 viewing other', () => {
      const tooltip = getRiskBarTooltip(1, true);
      expect(tooltip).toContain('another person');
      expect(tooltip).toContain('reversible');
    });

    it('returns appropriate tooltip for tier 2 viewing self', () => {
      const tooltip = getRiskBarTooltip(2, false);
      expect(tooltip).toContain('destructive');
      expect(tooltip).toContain('system-wide');
    });

    it('returns appropriate tooltip for tier 2 viewing other', () => {
      const tooltip = getRiskBarTooltip(2, true);
      expect(tooltip).toContain('another person');
      expect(tooltip).toContain('full administrative access');
    });
  });

  describe('getRiskBarLabel', () => {
    it('returns "Read-only" for tier 0', () => {
      expect(getRiskBarLabel(0)).toBe('Read-only');
      expect(getRiskBarLabel(0, true)).toBe('Read-only');
    });

    it('returns "Scoped Changes" for tier 1 viewing self', () => {
      expect(getRiskBarLabel(1, false)).toBe('Scoped Changes');
    });

    it('returns "Viewing Other" for tier 1 viewing other', () => {
      expect(getRiskBarLabel(1, true)).toBe('Viewing Other');
    });

    it('returns "High Impact" for tier 2', () => {
      expect(getRiskBarLabel(2, false)).toBe('High Impact');
      expect(getRiskBarLabel(2, true)).toBe('High Impact');
    });
  });
});
