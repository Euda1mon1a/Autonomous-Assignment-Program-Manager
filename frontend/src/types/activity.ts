/**
 * Activity Types for Slot-Level Schedule Events
 *
 * Activities are distinct from Rotations:
 * - Rotation = Multi-week block assignment (e.g., "Neurology" for 4 weeks)
 * - Activity = Slot-level event (e.g., "FM Clinic AM", "LEC Wednesday PM")
 */

import type { UUID } from './api';

// ============================================================================
// Activity Category
// ============================================================================

/**
 * Categories for activities to enable filtering and business logic.
 */
export type ActivityCategory = 'clinical' | 'educational' | 'administrative' | 'time_off';

/**
 * All valid activity categories.
 */
export const ACTIVITY_CATEGORIES: ActivityCategory[] = [
  'clinical',
  'educational',
  'administrative',
  'time_off',
];

/**
 * Human-readable labels for activity categories.
 */
export const ACTIVITY_CATEGORY_LABELS: Record<ActivityCategory, string> = {
  clinical: 'Clinical',
  educational: 'Educational',
  administrative: 'Administrative',
  time_off: 'Time Off',
};

// ============================================================================
// Activity
// ============================================================================

/**
 * Represents a slot-level schedule activity.
 *
 * @example
 * ```typescript
 * const fmClinic: Activity = {
 *   id: 'uuid',
 *   name: 'FM Clinic',
 *   code: 'fm_clinic',
 *   displayAbbreviation: 'C',
 *   activityCategory: 'clinical',
 *   isProtected: false,
 *   displayOrder: 1,
 * };
 * ```
 */
export interface Activity {
  /** Unique identifier */
  id: UUID;
  /** Human-readable name (e.g., 'FM Clinic', 'Lecture') */
  name: string;
  /** Stable identifier for solver (e.g., 'fm_clinic') */
  code: string;
  /** Short code for UI grid (e.g., 'C', 'LEC') */
  displayAbbreviation: string | null;
  /** Category: clinical, educational, administrative, timeOff */
  activityCategory: ActivityCategory;
  /** Tailwind color class for text */
  fontColor: string | null;
  /** Tailwind color class for background */
  backgroundColor: string | null;
  /** ACGME supervision requirement */
  requiresSupervision: boolean;
  /** True for locked slots (e.g., LEC Wednesday PM) */
  isProtected: boolean;
  /** ACGME clinical hour limit tracking */
  countsTowardClinicalHours: boolean;
  /** Sort order for UI */
  displayOrder: number;
  /** Whether this activity is archived (soft deleted) */
  isArchived: boolean;
  /** When the activity was archived */
  archivedAt: string | null;
  /** When the activity was created */
  createdAt: string;
  /** When the activity was last updated */
  updatedAt: string;
}

/**
 * Request payload for creating an activity.
 */
export interface ActivityCreateRequest {
  name: string;
  code: string;
  displayAbbreviation?: string | null;
  activityCategory: ActivityCategory;
  fontColor?: string | null;
  backgroundColor?: string | null;
  requiresSupervision?: boolean;
  isProtected?: boolean;
  countsTowardClinicalHours?: boolean;
  displayOrder?: number;
}

/**
 * Request payload for updating an activity.
 */
export interface ActivityUpdateRequest {
  name?: string;
  code?: string;
  displayAbbreviation?: string | null;
  activityCategory?: ActivityCategory;
  fontColor?: string | null;
  backgroundColor?: string | null;
  requiresSupervision?: boolean;
  isProtected?: boolean;
  countsTowardClinicalHours?: boolean;
  displayOrder?: number;
}

/**
 * Response from activity list API.
 */
export interface ActivityListResponse {
  activities: Activity[];
  total: number;
}

// ============================================================================
// Activity Requirement (Soft Constraints)
// ============================================================================

/**
 * Week numbers within a 4-week block.
 * null means the requirement applies to all weeks.
 */
export type ApplicableWeeks = number[] | null;

/**
 * Represents a soft constraint for how many half-days of an activity
 * should be scheduled within a rotation.
 *
 * @example
 * ```typescript
 * const fmClinicReq: ActivityRequirement = {
 *   id: 'uuid',
 *   rotationTemplateId: 'rotation-uuid',
 *   activityId: 'fm-clinic-uuid',
 *   activity: fmClinicActivity,
 *   minHalfdays: 3,
 *   maxHalfdays: 5,
 *   targetHalfdays: 4,
 *   applicableWeeks: null, // all weeks
 *   preferFullDays: true,
 *   preferredDays: [1, 2, 3, 4, 5], // Mon-Fri
 *   avoidDays: [0, 6], // Sun, Sat
 *   priority: 75,
 * };
 * ```
 */
export interface ActivityRequirement {
  /** Unique identifier */
  id: UUID;
  /** The rotation template this requirement belongs to */
  rotationTemplateId: UUID;
  /** The activity this requirement is for */
  activityId: UUID;
  /** Nested activity data */
  activity: Activity;
  /** Minimum half-days required (hard floor) */
  minHalfdays: number;
  /** Maximum half-days allowed (hard ceiling) */
  maxHalfdays: number;
  /** Preferred count (soft optimization target) */
  targetHalfdays: number | null;
  /** Week numbers [1,2,3,4] or null for all weeks */
  applicableWeeks: ApplicableWeeks;
  /** Prefer AM+PM together for same activity */
  preferFullDays: boolean;
  /** Preferred day numbers [0-6, 0=Sun, 6=Sat] */
  preferredDays: number[] | null;
  /** Days to avoid [0-6, 0=Sun, 6=Sat] */
  avoidDays: number[] | null;
  /** Priority 0-100, higher = more important */
  priority: number;
  /** When the requirement was created */
  createdAt: string;
  /** When the requirement was last updated */
  updatedAt: string;
}

/**
 * Request payload for creating an activity requirement.
 */
export interface ActivityRequirementCreateRequest {
  activityId: UUID;
  minHalfdays?: number;
  maxHalfdays?: number;
  targetHalfdays?: number | null;
  applicableWeeks?: ApplicableWeeks;
  preferFullDays?: boolean;
  preferredDays?: number[] | null;
  avoidDays?: number[] | null;
  priority?: number;
}

/**
 * Request payload for updating an activity requirement.
 */
export interface ActivityRequirementUpdateRequest {
  minHalfdays?: number;
  maxHalfdays?: number;
  targetHalfdays?: number | null;
  applicableWeeks?: ApplicableWeeks;
  preferFullDays?: boolean;
  preferredDays?: number[] | null;
  avoidDays?: number[] | null;
  priority?: number;
}

/**
 * Request payload for bulk updating all requirements for a rotation.
 */
export interface ActivityRequirementBulkUpdateRequest {
  requirements: ActivityRequirementCreateRequest[];
}

/**
 * Response from activity requirements list API.
 */
export interface ActivityRequirementListResponse {
  requirements: ActivityRequirement[];
  totalHalfdays: number;
}

// ============================================================================
// Priority Levels
// ============================================================================

/**
 * Standard priority levels for activity requirements.
 * Higher = more important to the solver.
 */
export const PRIORITY_LEVELS = {
  /** Nice to have (0-30) */
  LOW: { min: 0, max: 30, label: 'Low' },
  /** Should satisfy (31-60) */
  MEDIUM: { min: 31, max: 60, label: 'Medium' },
  /** Strong preference (61-90) */
  HIGH: { min: 61, max: 90, label: 'High' },
  /** Near-hard constraint (91-100) */
  CRITICAL: { min: 91, max: 100, label: 'Critical' },
} as const;

/**
 * Get the priority level label for a numeric priority.
 */
export function getPriorityLabel(priority: number): string {
  if (priority <= 30) return PRIORITY_LEVELS.LOW.label;
  if (priority <= 60) return PRIORITY_LEVELS.MEDIUM.label;
  if (priority <= 90) return PRIORITY_LEVELS.HIGH.label;
  return PRIORITY_LEVELS.CRITICAL.label;
}

/**
 * Get the color class for a priority level (for UI badges).
 */
export function getPriorityColor(priority: number): string {
  if (priority <= 30) return 'bg-gray-100 text-gray-700';
  if (priority <= 60) return 'bg-yellow-100 text-yellow-700';
  if (priority <= 90) return 'bg-orange-100 text-orange-700';
  return 'bg-red-100 text-red-700';
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Formats applicable weeks for display.
 *
 * @example
 * formatApplicableWeeks(null) // "All weeks"
 * formatApplicableWeeks([1, 2, 3]) // "Weeks 1-3"
 * formatApplicableWeeks([1, 3, 4]) // "Weeks 1, 3, 4"
 */
export function formatApplicableWeeks(weeks: ApplicableWeeks): string {
  if (!weeks || weeks.length === 0) return 'All weeks';
  if (weeks.length === 4) return 'All weeks';

  const sorted = [...weeks].sort((a, b) => a - b);

  // Check for consecutive sequence
  const isConsecutive = sorted.every((w, i) => i === 0 || w === sorted[i - 1] + 1);

  if (isConsecutive && sorted.length > 1) {
    return `Weeks ${sorted[0]}-${sorted[sorted.length - 1]}`;
  }

  return `Weeks ${sorted.join(', ')}`;
}

/**
 * Formats a day number to a short name.
 * 0 = Sun, 1 = Mon, ..., 6 = Sat
 */
export function formatDayShort(day: number): string {
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  return days[day] ?? '???';
}

/**
 * Formats preferred/avoid days for display.
 */
export function formatDays(days: number[] | null): string {
  if (!days || days.length === 0) return 'None';
  return days.map(formatDayShort).join(', ');
}
