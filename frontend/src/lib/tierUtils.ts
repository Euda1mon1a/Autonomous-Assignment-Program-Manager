/**
 * Tier Calculation Utilities
 *
 * Provides consistent tier calculation for risk bar and access control.
 * Based on the Frontend Consolidation Map tier model:
 *
 * - Tier 0: Read-only and self-service actions (no changes to shared data)
 * - Tier 1: Manual operational changes (reversible, scoped changes)
 * - Tier 2: Destructive or system-wide changes (bulk delete, overrides, rollback)
 *
 * Role mappings:
 * - Resident/Faculty: Tier 0
 * - Program Coordinator: Tier 1
 * - Admin/Skeleton Key: Tier 2
 */

import type { RiskTier } from '@/components/ui/RiskBar';

/** User roles from the auth system */
export type UserRole = 'admin' | 'coordinator' | 'faculty' | 'resident';

/**
 * Calculate the risk tier for a user based on their role.
 *
 * @param role - The user's role from authentication
 * @returns The calculated risk tier (0, 1, or 2)
 */
export function calculateTierFromRole(role: UserRole | string | undefined): RiskTier {
  if (!role) return 0;

  const normalizedRole = role.toLowerCase();

  // Tier 2: Admin (full destructive access)
  if (normalizedRole === 'admin') {
    return 2;
  }

  // Tier 1: Coordinator (scoped operational changes)
  if (normalizedRole === 'coordinator') {
    return 1;
  }

  // Tier 0: Faculty, Resident, or unknown (read-only)
  return 0;
}

/**
 * Check if a tier level allows viewing other users' schedules.
 *
 * @param tier - The user's tier level
 * @returns True if the user can view other users' schedules
 */
export function canViewOtherSchedules(tier: RiskTier): boolean {
  return tier >= 1;
}

/**
 * Check if a tier level allows exporting other users' schedules.
 *
 * @param tier - The user's tier level
 * @returns True if the user can export other users' schedules
 */
export function canExportOtherSchedules(tier: RiskTier): boolean {
  return tier >= 1;
}

/**
 * Check if a tier level allows making manual schedule changes.
 *
 * @param tier - The user's tier level
 * @returns True if the user can make manual schedule changes
 */
export function canMakeScheduleChanges(tier: RiskTier): boolean {
  return tier >= 1;
}

/**
 * Check if a tier level allows destructive operations.
 *
 * @param tier - The user's tier level
 * @returns True if the user can perform destructive operations
 */
export function canPerformDestructiveOperations(tier: RiskTier): boolean {
  return tier >= 2;
}

/**
 * Get the appropriate risk bar tooltip based on tier and context.
 *
 * @param tier - The user's tier level
 * @param isViewingOther - Whether the user is viewing another person's data
 * @returns The tooltip text for the risk bar
 */
export function getRiskBarTooltip(tier: RiskTier, isViewingOther = false): string {
  switch (tier) {
    case 0:
      return 'You can view your own schedule but cannot make changes to shared data.';
    case 1:
      return isViewingOther
        ? 'You are viewing another person\'s schedule. You can make reversible, scoped changes.'
        : 'You can make reversible changes within your assigned scope.';
    case 2:
      return isViewingOther
        ? 'You are viewing another person\'s schedule with full administrative access.'
        : 'You have access to destructive or system-wide operations. Proceed with caution.';
    default:
      return '';
  }
}

/**
 * Get the appropriate risk bar label based on tier and context.
 *
 * @param tier - The user's tier level
 * @param isViewingOther - Whether the user is viewing another person's data
 * @returns The label text for the risk bar
 */
export function getRiskBarLabel(tier: RiskTier, isViewingOther = false): string {
  switch (tier) {
    case 0:
      return 'Read-only';
    case 1:
      return isViewingOther ? 'Viewing Other' : 'Scoped Changes';
    case 2:
      return 'High Impact';
    default:
      return 'Unknown';
  }
}
