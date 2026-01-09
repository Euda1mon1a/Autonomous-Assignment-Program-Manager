/**
 * Faculty Activity Types for Weekly Templates and Overrides
 *
 * Faculty Weekly Activity Editor:
 * - Templates: Default weekly patterns per faculty member (7x2 grid)
 * - Overrides: Week-specific exceptions to templates
 * - Effective: Merged view of template + overrides for a specific week
 */

import type { UUID } from './api';
import type { Activity } from './activity';

// ============================================================================
// Faculty Roles (from backend enum)
// ============================================================================

/**
 * Faculty role types with specific scheduling constraints.
 */
export type FacultyRole = 'pd' | 'apd' | 'oic' | 'dept_chief' | 'sports_med' | 'core' | 'adjunct';

/**
 * Human-readable labels for faculty roles.
 */
export const FACULTY_ROLE_LABELS: Record<FacultyRole, string> = {
  pd: 'Program Director',
  apd: 'Associate Program Director',
  oic: 'Officer in Charge',
  deptChief: 'Department Chief',
  sportsMed: 'Sports Medicine',
  core: 'Core Faculty',
  adjunct: 'Adjunct Faculty',
};

/**
 * All valid faculty roles.
 */
export const FACULTY_ROLES: FacultyRole[] = [
  'pd',
  'apd',
  'oic',
  'dept_chief',
  'sports_med',
  'core',
  'adjunct',
];

// ============================================================================
// Time Types
// ============================================================================

/**
 * Time of day for a slot.
 */
export type TimeOfDay = 'AM' | 'PM';

/**
 * Days of the week.
 * 0 = Sunday, 6 = Saturday
 */
export type DayOfWeek = 0 | 1 | 2 | 3 | 4 | 5 | 6;

/**
 * Day labels for display.
 */
export const DAY_LABELS: Record<DayOfWeek, string> = {
  0: 'Sunday',
  1: 'Monday',
  2: 'Tuesday',
  3: 'Wednesday',
  4: 'Thursday',
  5: 'Friday',
  6: 'Saturday',
};

/**
 * Short day labels for grid display.
 */
export const DAY_LABELS_SHORT: Record<DayOfWeek, string> = {
  0: 'Sun',
  1: 'Mon',
  2: 'Tue',
  3: 'Wed',
  4: 'Thu',
  5: 'Fri',
  6: 'Sat',
};

// ============================================================================
// Template Slot Types
// ============================================================================

/**
 * A single slot in a faculty's weekly template (7x2 grid).
 */
export interface FacultyTemplateSlot {
  /** Unique identifier */
  id: UUID;
  /** Faculty member's ID */
  personId: UUID;
  /** Day of week (0=Sunday, 6=Saturday) */
  dayOfWeek: DayOfWeek;
  /** Time of day (AM or PM) */
  timeOfDay: TimeOfDay;
  /** Week number 1-4, or null for all weeks */
  weekNumber: 1 | 2 | 3 | 4 | null;
  /** Activity UUID or null for empty */
  activityId: UUID | null;
  /** Nested activity data */
  activity: Activity | null;
  /** HARD constraint - solver cannot change */
  isLocked: boolean;
  /** Soft preference 0-100 */
  priority: number;
  /** Optional notes */
  notes: string | null;
  /** Created timestamp */
  createdAt: string;
  /** Updated timestamp */
  updatedAt: string;
}

/**
 * Request payload for creating/updating a template slot.
 */
export interface FacultyTemplateSlotRequest {
  dayOfWeek: DayOfWeek;
  timeOfDay: TimeOfDay;
  weekNumber?: 1 | 2 | 3 | 4 | null;
  activityId?: UUID | null;
  isLocked?: boolean;
  priority?: number;
  notes?: string | null;
}

/**
 * Request payload for bulk template update.
 */
export interface FacultyTemplateUpdateRequest {
  slots: FacultyTemplateSlotRequest[];
  clearExisting?: boolean;
}

/**
 * Response from faculty template API.
 */
export interface FacultyTemplateResponse {
  personId: UUID;
  personName: string;
  facultyRole: FacultyRole | null;
  slots: FacultyTemplateSlot[];
  totalSlots: number;
}

// ============================================================================
// Override Types
// ============================================================================

/**
 * A week-specific override for a faculty member's template.
 */
export interface FacultyOverride {
  /** Unique identifier */
  id: UUID;
  /** Faculty member's ID */
  personId: UUID;
  /** Monday of the week this override applies to */
  effectiveDate: string;
  /** Day of week (0=Sunday, 6=Saturday) */
  dayOfWeek: DayOfWeek;
  /** Time of day (AM or PM) */
  timeOfDay: TimeOfDay;
  /** Activity UUID or null to clear */
  activityId: UUID | null;
  /** Nested activity data */
  activity: Activity | null;
  /** HARD constraint for this week */
  isLocked: boolean;
  /** Why this override exists */
  overrideReason: string | null;
  /** Who created this override */
  createdBy: UUID | null;
  /** Created timestamp */
  createdAt: string;
}

/**
 * Request payload for creating an override.
 */
export interface FacultyOverrideRequest {
  effectiveDate: string;
  dayOfWeek: DayOfWeek;
  timeOfDay: TimeOfDay;
  activityId?: UUID | null;
  isLocked?: boolean;
  overrideReason?: string | null;
}

/**
 * Response from faculty overrides list API.
 */
export interface FacultyOverridesResponse {
  personId: UUID;
  weekStart: string;
  overrides: FacultyOverride[];
  total: number;
}

// ============================================================================
// Effective Week Types
// ============================================================================

/**
 * Source of an effective slot value.
 */
export type SlotSource = 'template' | 'override' | null;

/**
 * An effective slot (merged template + override).
 */
export interface EffectiveSlot {
  /** Day of week (0=Sunday, 6=Saturday) */
  dayOfWeek: DayOfWeek;
  /** Time of day (AM or PM) */
  timeOfDay: TimeOfDay;
  /** Activity UUID or null */
  activityId: UUID | null;
  /** Nested activity data */
  activity: Activity | null;
  /** Whether this slot is locked */
  isLocked: boolean;
  /** Soft preference priority */
  priority: number;
  /** Where this value came from */
  source: SlotSource;
  /** Notes (from template or override reason) */
  notes: string | null;
}

/**
 * Response from effective week API.
 */
export interface EffectiveWeekResponse {
  personId: UUID;
  personName: string;
  facultyRole: FacultyRole | null;
  weekStart: string;
  weekNumber: number;
  slots: EffectiveSlot[];
}

// ============================================================================
// Permission Types
// ============================================================================

/**
 * Response from permitted activities API.
 */
export interface PermittedActivitiesResponse {
  facultyRole: FacultyRole;
  activities: Activity[];
  defaultActivities: Activity[];
}

// ============================================================================
// Matrix View Types
// ============================================================================

/**
 * A single week's slots for one faculty member in the matrix.
 */
export interface FacultyWeekSlots {
  weekStart: string;
  slots: EffectiveSlot[];
}

/**
 * A single faculty member's row in the matrix.
 */
export interface FacultyMatrixRow {
  personId: UUID;
  name: string;
  facultyRole: FacultyRole | null;
  weeks: FacultyWeekSlots[];
}

/**
 * Response from faculty matrix API.
 */
export interface FacultyMatrixResponse {
  startDate: string;
  endDate: string;
  faculty: FacultyMatrixRow[];
  totalFaculty: number;
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Gets a unique key for a slot position.
 */
export function getSlotKey(dayOfWeek: DayOfWeek, timeOfDay: TimeOfDay): string {
  return `${dayOfWeek}_${timeOfDay}`;
}

/**
 * Parses a slot key back to day/time.
 */
export function parseSlotKey(key: string): { dayOfWeek: DayOfWeek; timeOfDay: TimeOfDay } {
  const [day, time] = key.split('_');
  return {
    dayOfWeek: parseInt(day, 10) as DayOfWeek,
    timeOfDay: time as TimeOfDay,
  };
}

/**
 * Formats a slot position for display.
 */
export function formatSlotPosition(dayOfWeek: DayOfWeek, timeOfDay: TimeOfDay): string {
  return `${DAY_LABELS_SHORT[dayOfWeek]} ${timeOfDay}`;
}

/**
 * Generates all 14 slot keys for a week.
 */
export function getAllSlotKeys(): string[] {
  const keys: string[] = [];
  for (let day = 0; day <= 6; day++) {
    keys.push(getSlotKey(day as DayOfWeek, 'AM'));
    keys.push(getSlotKey(day as DayOfWeek, 'PM'));
  }
  return keys;
}

/**
 * Creates an empty effective slot.
 */
export function createEmptySlot(dayOfWeek: DayOfWeek, timeOfDay: TimeOfDay): EffectiveSlot {
  return {
    dayOfWeek,
    timeOfDay,
    activityId: null,
    activity: null,
    isLocked: false,
    priority: 50,
    source: null,
    notes: null,
  };
}

/**
 * Converts slots array to a map keyed by slot position.
 */
export function slotsToMap<T extends { dayOfWeek: DayOfWeek; timeOfDay: TimeOfDay }>(
  slots: T[]
): Map<string, T> {
  const map = new Map<string, T>();
  for (const slot of slots) {
    map.set(getSlotKey(slot.dayOfWeek, slot.timeOfDay), slot);
  }
  return map;
}

/**
 * Checks if a day is a weekend.
 */
export function isWeekend(dayOfWeek: DayOfWeek): boolean {
  return dayOfWeek === 0 || dayOfWeek === 6;
}

/**
 * Gets the faculty role label.
 */
export function getFacultyRoleLabel(role: FacultyRole | null): string {
  if (!role) return 'Unknown';
  return FACULTY_ROLE_LABELS[role] ?? role;
}
