/**
 * Weekly Pattern Types for Rotation Template Scheduling
 *
 * Types for representing weekly scheduling patterns used in rotation templates.
 * A weekly pattern defines which rotation templates are assigned to each
 * day/time slot throughout a week.
 */

import type { UUID } from './api';

// ============================================================================
// Core Types
// ============================================================================

/**
 * Time of day for scheduling (AM or PM shift)
 */
export type WeeklyPatternTimeOfDay = 'AM' | 'PM';

/**
 * Day of week (0 = Sunday, 6 = Saturday)
 * Matches backend convention: 0=Sunday, 1=Monday, ..., 6=Saturday
 * (See backend/app/models/weekly_pattern.py)
 */
export type DayOfWeek = 0 | 1 | 2 | 3 | 4 | 5 | 6;

/**
 * Human-readable day names for display
 * Index matches backend: 0=Sunday, 1=Monday, ..., 6=Saturday
 */
export const DAY_NAMES: Record<DayOfWeek, string> = {
  0: 'Sunday',
  1: 'Monday',
  2: 'Tuesday',
  3: 'Wednesday',
  4: 'Thursday',
  5: 'Friday',
  6: 'Saturday',
};

/**
 * Short day names for compact display
 * Index matches backend: 0=Sunday, 1=Monday, ..., 6=Saturday
 */
export const DAY_ABBREVIATIONS: Record<DayOfWeek, string> = {
  0: 'Sun',
  1: 'Mon',
  2: 'Tue',
  3: 'Wed',
  4: 'Thu',
  5: 'Fri',
  6: 'Sat',
};

// ============================================================================
// Weekly Pattern Slot
// ============================================================================

/**
 * Represents a single slot in the weekly pattern grid.
 *
 * Each slot corresponds to a specific day of week and time of day (AM/PM),
 * and can optionally be assigned to a rotation template.
 *
 * @example
 * ```typescript
 * const mondayMorningClinic: WeeklyPatternSlot = {
 *   dayOfWeek: 0,
 *   timeOfDay: 'AM',
 *   rotationTemplateId: 'clinic-template-uuid',
 * };
 *
 * const tuesdayAfternoonOff: WeeklyPatternSlot = {
 *   dayOfWeek: 1,
 *   timeOfDay: 'PM',
 *   rotationTemplateId: null,
 * };
 * ```
 */
/**
 * Week number within a block (1-4)
 * null = same pattern applies to all weeks
 */
export type WeekNumber = 1 | 2 | 3 | 4 | null;

export interface WeeklyPatternSlot {
  /** Day of week (0 = Sunday, 6 = Saturday) */
  dayOfWeek: DayOfWeek;
  /** Time of day (AM or PM shift) */
  timeOfDay: WeeklyPatternTimeOfDay;
  /** ID of assigned rotation template, or null if slot is empty */
  rotationTemplateId: UUID | null;
  /** Week number within block (1-4). null = same pattern all weeks */
  weekNumber?: WeekNumber;
  /** Activity type for the slot (e.g., 'scheduled', 'off', 'conference') */
  activityType?: string | null;
  /** Whether this slot is protected from automatic changes */
  isProtected?: boolean;
  /** Optional notes for this slot */
  notes?: string | null;
}

// ============================================================================
// Weekly Pattern Grid
// ============================================================================

/**
 * Represents a complete weekly pattern as a grid of slots.
 *
 * The grid contains 14 slots (7 days x 2 time periods).
 * Used to define recurring weekly schedules for rotation templates.
 *
 * @example
 * ```typescript
 * const typicalResidentWeek: WeeklyPatternGrid = {
 *   slots: [
 *     { dayOfWeek: 0, timeOfDay: 'AM', rotationTemplateId: 'clinic-uuid' },
 *     { dayOfWeek: 0, timeOfDay: 'PM', rotationTemplateId: 'clinic-uuid' },
 *     { dayOfWeek: 1, timeOfDay: 'AM', rotationTemplateId: 'inpatient-uuid' },
 *     // ... remaining slots
 *   ],
 * };
 * ```
 */
export interface WeeklyPatternGrid {
  /** Array of slots covering Mon-Sun AM/PM. Up to 56 for week-specific patterns. */
  slots: WeeklyPatternSlot[];
  /** If true, all weeks use the same pattern (weekNumber is ignored) */
  samePatternAllWeeks?: boolean;
}

// ============================================================================
// Rotation Template Reference (for display)
// ============================================================================

/**
 * Minimal rotation template info for display in the grid editor.
 * Contains only the fields needed for rendering.
 */
export interface RotationTemplateRef {
  /** Template ID */
  id: UUID;
  /** Full name of the rotation */
  name: string;
  /** Short code for display (e.g., "C" for Clinic) */
  displayAbbreviation: string | null;
  /** Background color class (Tailwind) */
  backgroundColor: string | null;
  /** Text color class (Tailwind) */
  fontColor: string | null;
}

// ============================================================================
// API Types
// ============================================================================

/**
 * Request to update a weekly pattern
 */
export interface WeeklyPatternUpdateRequest {
  /** Template ID this pattern belongs to */
  templateId: UUID;
  /** Updated pattern grid */
  pattern: WeeklyPatternGrid;
}

/**
 * Response from weekly pattern API
 */
export interface WeeklyPatternResponse {
  /** Template ID */
  templateId: UUID;
  /** Current pattern grid */
  pattern: WeeklyPatternGrid;
  /** When the pattern was last updated */
  updatedAt: string;
}

// ============================================================================
// Bulk Pattern Update Types
// ============================================================================

/**
 * Single slot definition for batch pattern updates.
 */
export interface BatchPatternSlot {
  /** Day of week (0=Sunday, 6=Saturday) */
  day_of_week: DayOfWeek;
  /** Time of day (AM or PM) */
  time_of_day: WeeklyPatternTimeOfDay;
  /** Template ID to assign to this slot (null to clear) */
  linked_template_id?: UUID | null;
  /** Activity type override */
  activity_type?: string | null;
  /** Protected status */
  is_protected?: boolean;
  /** Slot notes */
  notes?: string | null;
}

/**
 * Request schema for bulk updating weekly patterns across multiple templates.
 */
export interface BatchPatternUpdateRequest {
  /** Template IDs to update */
  template_ids: UUID[];
  /** Update mode: overlay (merge with existing) or replace (overwrite all) */
  mode: 'overlay' | 'replace';
  /** Slots to apply (max 14 per week) */
  slots: BatchPatternSlot[];
  /** Weeks to apply to (1-4). null = all weeks */
  week_numbers?: number[] | null;
  /** Preview changes without applying */
  dry_run?: boolean;
}

/**
 * Result for a single template in batch update.
 */
export interface BatchPatternUpdateResult {
  /** Template ID */
  template_id: UUID;
  /** Template name */
  template_name: string;
  /** Whether update succeeded */
  success: boolean;
  /** Number of slots modified */
  slots_modified: number;
  /** Error message if failed */
  error?: string | null;
}

/**
 * Response from batch pattern update API.
 */
export interface BatchPatternUpdateResponse {
  /** Total templates processed */
  total_templates: number;
  /** Number of successful updates */
  successful: number;
  /** Number of failed updates */
  failed: number;
  /** Individual results per template */
  results: BatchPatternUpdateResult[];
  /** Whether this was a dry run */
  dry_run: boolean;
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Creates an empty weekly pattern grid with all slots set to null.
 *
 * @returns A WeeklyPatternGrid with 14 empty slots
 *
 * @example
 * ```typescript
 * const emptyPattern = createEmptyPattern();
 * // Returns grid with 14 slots, all rotationTemplateId = null
 * ```
 */
export function createEmptyPattern(): WeeklyPatternGrid {
  const slots: WeeklyPatternSlot[] = [];

  // Create slots for each day (0=Sunday through 6=Saturday) and time period
  for (let day = 0; day <= 6; day++) {
    slots.push({
      dayOfWeek: day as DayOfWeek,
      timeOfDay: 'AM',
      rotationTemplateId: null,
    });
    slots.push({
      dayOfWeek: day as DayOfWeek,
      timeOfDay: 'PM',
      rotationTemplateId: null,
    });
  }

  return { slots };
}

/**
 * Ensures a pattern has all 14 slots, filling in missing ones.
 * Use this when receiving sparse data from the backend.
 *
 * @param pattern - Potentially sparse pattern from backend
 * @returns Complete WeeklyPatternGrid with all 14 slots
 */
export function ensureCompletePattern(pattern: WeeklyPatternGrid): WeeklyPatternGrid {
  const complete = createEmptyPattern();

  // Overlay existing slots onto the complete grid
  for (const slot of pattern.slots) {
    const index = complete.slots.findIndex(
      (s) => s.dayOfWeek === slot.dayOfWeek && s.timeOfDay === slot.timeOfDay
    );
    if (index !== -1) {
      complete.slots[index] = slot;
    }
  }

  return complete;
}

/**
 * Gets a specific slot from a pattern grid.
 *
 * @param pattern - The weekly pattern grid
 * @param dayOfWeek - Day of week (0-6)
 * @param timeOfDay - Time of day ('AM' or 'PM')
 * @param weekNumber - Week number (1-4) or null for "all weeks" pattern
 * @returns The matching slot, or undefined if not found
 */
export function getSlot(
  pattern: WeeklyPatternGrid,
  dayOfWeek: DayOfWeek,
  timeOfDay: WeeklyPatternTimeOfDay,
  weekNumber?: WeekNumber
): WeeklyPatternSlot | undefined {
  return pattern.slots.find(
    (slot) =>
      slot.dayOfWeek === dayOfWeek &&
      slot.timeOfDay === timeOfDay &&
      (weekNumber === undefined || slot.weekNumber === weekNumber)
  );
}

/**
 * Gets all slots for a specific week.
 *
 * @param pattern - The weekly pattern grid
 * @param weekNumber - Week number (1-4) or null for "all weeks" patterns
 * @returns Array of slots for that week
 */
export function getSlotsForWeek(
  pattern: WeeklyPatternGrid,
  weekNumber: WeekNumber
): WeeklyPatternSlot[] {
  return pattern.slots.filter((slot) => slot.weekNumber === weekNumber);
}

/**
 * Checks if a pattern has week-specific variations.
 *
 * @param pattern - The weekly pattern grid
 * @returns True if any slots have a specific weekNumber
 */
export function hasWeekSpecificPatterns(pattern: WeeklyPatternGrid): boolean {
  return pattern.slots.some((slot) => slot.weekNumber !== null && slot.weekNumber !== undefined);
}

/**
 * Updates a specific slot in a pattern grid (immutably).
 *
 * @param pattern - The current weekly pattern grid
 * @param dayOfWeek - Day of week to update (0-6)
 * @param timeOfDay - Time of day to update ('AM' or 'PM')
 * @param rotationTemplateId - New rotation template ID (or null to clear)
 * @returns A new WeeklyPatternGrid with the updated slot
 */
export function updateSlot(
  pattern: WeeklyPatternGrid,
  dayOfWeek: DayOfWeek,
  timeOfDay: WeeklyPatternTimeOfDay,
  rotationTemplateId: UUID | null
): WeeklyPatternGrid {
  return {
    slots: pattern.slots.map((slot) =>
      slot.dayOfWeek === dayOfWeek && slot.timeOfDay === timeOfDay
        ? { ...slot, rotationTemplateId }
        : slot
    ),
  };
}

/**
 * Toggles the protected status of a specific slot in a pattern grid (immutably).
 *
 * @param pattern - The current weekly pattern grid
 * @param dayOfWeek - Day of week to update (0-6)
 * @param timeOfDay - Time of day to update ('AM' or 'PM')
 * @returns A new WeeklyPatternGrid with the toggled slot protection
 */
export function toggleSlotProtected(
  pattern: WeeklyPatternGrid,
  dayOfWeek: DayOfWeek,
  timeOfDay: WeeklyPatternTimeOfDay
): WeeklyPatternGrid {
  return {
    ...pattern,
    slots: pattern.slots.map((slot) =>
      slot.dayOfWeek === dayOfWeek && slot.timeOfDay === timeOfDay
        ? { ...slot, isProtected: !slot.isProtected }
        : slot
    ),
  };
}

/**
 * Updates slot details (notes, activity type) immutably.
 *
 * @param pattern - The current weekly pattern grid
 * @param dayOfWeek - Day of week to update (0-6)
 * @param timeOfDay - Time of day to update ('AM' or 'PM')
 * @param updates - Partial slot updates (notes, activityType)
 * @returns A new WeeklyPatternGrid with the updated slot
 */
export function updateSlotDetails(
  pattern: WeeklyPatternGrid,
  dayOfWeek: DayOfWeek,
  timeOfDay: WeeklyPatternTimeOfDay,
  updates: { notes?: string | null; activityType?: string | null }
): WeeklyPatternGrid {
  return {
    ...pattern,
    slots: pattern.slots.map((slot) =>
      slot.dayOfWeek === dayOfWeek && slot.timeOfDay === timeOfDay
        ? { ...slot, ...updates }
        : slot
    ),
  };
}
