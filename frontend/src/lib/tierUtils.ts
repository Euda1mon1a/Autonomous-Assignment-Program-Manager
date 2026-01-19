/**
 * Tier Utilities - Role-based access control helpers
 *
 * Tier Model (matches RiskBar component):
 * - Tier 0: Residents, Faculty (can view own schedule only)
 * - Tier 1: Coordinators (can view and export others' schedules)
 * - Tier 2: Admins (full access, high-impact operations)
 */

import type { RiskTier } from '@/components/ui/RiskBar'

/**
 * Map user role to access tier
 */
export function calculateTierFromRole(role: string | undefined): RiskTier {
  if (!role) return 0

  const roleLower = role.toLowerCase()

  // Tier 2: Admin roles
  if (roleLower === 'admin' || roleLower === 'superadmin') {
    return 2
  }

  // Tier 1: Coordinator roles
  if (roleLower === 'coordinator' || roleLower === 'scheduler') {
    return 1
  }

  // Tier 0: All others (resident, faculty, clinical_staff, etc.)
  return 0
}

/**
 * Get tooltip text for risk bar based on tier
 *
 * @param tier - The user's access tier
 * @param isViewingOther - Whether user is viewing another person's schedule
 */
export function getRiskBarTooltip(
  tier: RiskTier,
  isViewingOther = false
): string {
  if (isViewingOther) {
    return tier === 2
      ? 'Admin access - Viewing and editing other personnel schedules'
      : 'Coordinator access - Viewing another person\'s schedule'
  }

  switch (tier) {
    case 2:
      return 'Admin access - Full permissions including high-impact operations'
    case 1:
      return 'Coordinator access - Can view and manage schedules for all personnel'
    case 0:
    default:
      return 'Personal access - View your own schedule'
  }
}

/**
 * Get label for risk bar based on tier
 *
 * @param tier - The user's access tier
 * @param isViewingOther - Whether user is viewing another person's schedule
 */
export function getRiskBarLabel(tier: RiskTier, isViewingOther = false): string {
  if (isViewingOther) {
    return tier === 2 ? 'Admin View' : 'Viewing Other'
  }

  switch (tier) {
    case 2:
      return 'Admin'
    case 1:
      return 'Coordinator'
    case 0:
    default:
      return 'Personal'
  }
}

/**
 * Check if user can view other people's schedules
 */
export function canViewOthers(tier: RiskTier): boolean {
  return tier >= 1
}

/** Alias for canViewOthers - used in tests */
export const canViewOtherSchedules = canViewOthers

/** Check if user can export other schedules (tier 1+) */
export function canExportOtherSchedules(tier: RiskTier): boolean {
  return tier >= 1
}

/** Check if user can make schedule changes (tier 1+) */
export function canMakeScheduleChanges(tier: RiskTier): boolean {
  return tier >= 1
}

/** Check if user can perform destructive operations (admin only) */
export function canPerformDestructiveOperations(tier: RiskTier): boolean {
  return tier >= 2
}

/**
 * Check if user can perform admin operations
 */
export function isAdmin(tier: RiskTier): boolean {
  return tier >= 2
}
