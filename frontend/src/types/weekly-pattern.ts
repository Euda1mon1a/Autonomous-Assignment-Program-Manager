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
 * Day of week (0 = Monday, 6 = Sunday)
 * Follows ISO 8601 weekday numbering where Monday = 0
 */
export type DayOfWeek = 0 | 1 | 2 | 3 | 4 | 5 | 6;

/**
 * Human-readable day names for display
 */
export const DAY_NAMES: Record<DayOfWeek, string> = {
  0: 'Monday',
  1: 'Tuesday',
  2: 'Wednesday',
  3: 'Thursday',
  4: 'Friday',
  5: 'Saturday',
  6: 'Sunday',
};

/**
 * Short day names for compact display
 */
export const DAY_ABBREVIATIONS: Record<DayOfWeek, string> = {
  0: 'Mon',
  1: 'Tue',
  2: 'Wed',
  3: 'Thu',
  4: 'Fri',
  5: 'Sat',
  6: 'Sun',
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
export interface WeeklyPatternSlot {
  /** Day of week (0 = Monday, 6 = Sunday) */
  dayOfWeek: DayOfWeek;
  /** Time of day (AM or PM shift) */
  timeOfDay: WeeklyPatternTimeOfDay;
  /** ID of assigned rotation template, or null if slot is empty */
  rotationTemplateId: UUID | null;
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
  /** Array of 14 slots covering Mon-Sun AM/PM */
  slots: WeeklyPatternSlot[];
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
 * Gets a specific slot from a pattern grid.
 *
 * @param pattern - The weekly pattern grid
 * @param dayOfWeek - Day of week (0-6)
 * @param timeOfDay - Time of day ('AM' or 'PM')
 * @returns The matching slot, or undefined if not found
 */
export function getSlot(
  pattern: WeeklyPatternGrid,
  dayOfWeek: DayOfWeek,
  timeOfDay: WeeklyPatternTimeOfDay
): WeeklyPatternSlot | undefined {
  return pattern.slots.find(
    (slot) => slot.dayOfWeek === dayOfWeek && slot.timeOfDay === timeOfDay
  );
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
