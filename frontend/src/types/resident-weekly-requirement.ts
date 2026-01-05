/**
 * Resident Weekly Requirement Types
 *
 * Types for managing weekly scheduling requirements per rotation template.
 * Controls FM clinic and specialty session frequencies, academic requirements,
 * and protected time slots for resident schedules.
 */

// ============================================================================
// Core Types
// ============================================================================

/**
 * Days of the week as numbers (0 = Sunday, 6 = Saturday)
 */
export type DayOfWeek = 0 | 1 | 2 | 3 | 4 | 5 | 6;

/**
 * Time slot identifiers for protected slots
 */
export type TimeSlot =
  | 'mon_am' | 'mon_pm'
  | 'tue_am' | 'tue_pm'
  | 'wed_am' | 'wed_pm'
  | 'thu_am' | 'thu_pm'
  | 'fri_am' | 'fri_pm'
  | 'sat_am' | 'sat_pm'
  | 'sun_am' | 'sun_pm';

/**
 * Protected slot activity types
 */
export type ProtectedSlotType =
  | 'conference'
  | 'academics'
  | 'didactics'
  | 'research'
  | 'admin'
  | 'wellness';

/**
 * Record of protected time slots mapped to their activity type
 */
export type ProtectedSlots = Partial<Record<TimeSlot, ProtectedSlotType>>;

/**
 * Resident Weekly Requirement - defines scheduling constraints for a rotation
 */
export interface ResidentWeeklyRequirement {
  /** Unique identifier */
  id: string;
  /** Associated rotation template ID */
  rotation_template_id: string;
  /** Minimum FM clinic half-days per week (0-14) */
  fm_clinic_min_per_week: number;
  /** Maximum FM clinic half-days per week (0-14) */
  fm_clinic_max_per_week: number;
  /** Minimum specialty half-days per week */
  specialty_min_per_week: number;
  /** Maximum specialty half-days per week */
  specialty_max_per_week: number;
  /** Whether Wednesday AM academics are required */
  academics_required: boolean;
  /** Protected time slots mapped to activity type */
  protected_slots: ProtectedSlots;
  /** Days of week when clinic sessions are allowed (0=Sun, 1=Mon, ..., 6=Sat) */
  allowed_clinic_days: DayOfWeek[];
  /** Creation timestamp */
  created_at?: string;
  /** Last update timestamp */
  updated_at?: string;
}

// ============================================================================
// API Request/Response Types
// ============================================================================

/**
 * Request to create a new weekly requirement
 */
export interface ResidentWeeklyRequirementCreate {
  rotation_template_id: string;
  fm_clinic_min_per_week: number;
  fm_clinic_max_per_week: number;
  specialty_min_per_week: number;
  specialty_max_per_week: number;
  academics_required?: boolean;
  protected_slots?: ProtectedSlots;
  allowed_clinic_days?: DayOfWeek[];
}

/**
 * Request to update an existing weekly requirement
 */
export interface ResidentWeeklyRequirementUpdate {
  fm_clinic_min_per_week?: number;
  fm_clinic_max_per_week?: number;
  specialty_min_per_week?: number;
  specialty_max_per_week?: number;
  academics_required?: boolean;
  protected_slots?: ProtectedSlots;
  allowed_clinic_days?: DayOfWeek[];
}

// ============================================================================
// Form Types
// ============================================================================

/**
 * Form state for editing weekly requirements
 */
export interface WeeklyRequirementFormData {
  fm_clinic_min_per_week: number;
  fm_clinic_max_per_week: number;
  specialty_min_per_week: number;
  specialty_max_per_week: number;
  academics_required: boolean;
  protected_slots: ProtectedSlots;
  allowed_clinic_days: DayOfWeek[];
}

/**
 * Validation errors for the form
 */
export interface WeeklyRequirementFormErrors {
  fm_clinic?: string;
  specialty?: string;
  general?: string;
}

// ============================================================================
// Display Constants
// ============================================================================

/**
 * Day of week labels for UI display
 */
export const DAY_OF_WEEK_LABELS: Record<DayOfWeek, string> = {
  0: 'Sun',
  1: 'Mon',
  2: 'Tue',
  3: 'Wed',
  4: 'Thu',
  5: 'Fri',
  6: 'Sat',
};

/**
 * Full day of week labels
 */
export const DAY_OF_WEEK_FULL_LABELS: Record<DayOfWeek, string> = {
  0: 'Sunday',
  1: 'Monday',
  2: 'Tuesday',
  3: 'Wednesday',
  4: 'Thursday',
  5: 'Friday',
  6: 'Saturday',
};

/**
 * Time slot display labels
 */
export const TIME_SLOT_LABELS: Record<TimeSlot, string> = {
  mon_am: 'Mon AM',
  mon_pm: 'Mon PM',
  tue_am: 'Tue AM',
  tue_pm: 'Tue PM',
  wed_am: 'Wed AM',
  wed_pm: 'Wed PM',
  thu_am: 'Thu AM',
  thu_pm: 'Thu PM',
  fri_am: 'Fri AM',
  fri_pm: 'Fri PM',
  sat_am: 'Sat AM',
  sat_pm: 'Sat PM',
  sun_am: 'Sun AM',
  sun_pm: 'Sun PM',
};

/**
 * Protected slot type labels and colors
 */
export const PROTECTED_SLOT_TYPE_CONFIG: Record<
  ProtectedSlotType,
  { label: string; color: string; bgColor: string }
> = {
  conference: {
    label: 'Conference',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/20',
  },
  academics: {
    label: 'Academics',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
  },
  didactics: {
    label: 'Didactics',
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/20',
  },
  research: {
    label: 'Research',
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/20',
  },
  admin: {
    label: 'Admin',
    color: 'text-slate-400',
    bgColor: 'bg-slate-500/20',
  },
  wellness: {
    label: 'Wellness',
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
  },
};

/**
 * All protected slot types as an array for iteration
 */
export const PROTECTED_SLOT_TYPES: ProtectedSlotType[] = [
  'conference',
  'academics',
  'didactics',
  'research',
  'admin',
  'wellness',
];

/**
 * All time slots in order
 */
export const TIME_SLOTS: TimeSlot[] = [
  'sun_am', 'sun_pm',
  'mon_am', 'mon_pm',
  'tue_am', 'tue_pm',
  'wed_am', 'wed_pm',
  'thu_am', 'thu_pm',
  'fri_am', 'fri_pm',
  'sat_am', 'sat_pm',
];

/**
 * Default values for a new weekly requirement
 */
export const DEFAULT_WEEKLY_REQUIREMENT: WeeklyRequirementFormData = {
  fm_clinic_min_per_week: 0,
  fm_clinic_max_per_week: 4,
  specialty_min_per_week: 0,
  specialty_max_per_week: 4,
  academics_required: true,
  protected_slots: { wed_am: 'conference' },
  allowed_clinic_days: [1, 2, 3, 4, 5], // Mon-Fri
};

// ============================================================================
// Validation Helpers
// ============================================================================

/**
 * Validates min <= max constraint
 */
export function validateMinMax(min: number, max: number): boolean {
  return min <= max;
}

/**
 * Validates half-day count is within valid range (0-14)
 */
export function validateHalfDayRange(value: number): boolean {
  return value >= 0 && value <= 14;
}

/**
 * Validates the entire form data
 */
export function validateWeeklyRequirement(
  data: WeeklyRequirementFormData
): WeeklyRequirementFormErrors {
  const errors: WeeklyRequirementFormErrors = {};

  // FM Clinic validation
  if (!validateHalfDayRange(data.fm_clinic_min_per_week) ||
      !validateHalfDayRange(data.fm_clinic_max_per_week)) {
    errors.fm_clinic = 'FM clinic values must be between 0 and 14';
  } else if (!validateMinMax(data.fm_clinic_min_per_week, data.fm_clinic_max_per_week)) {
    errors.fm_clinic = 'FM clinic minimum cannot exceed maximum';
  }

  // Specialty validation
  if (!validateHalfDayRange(data.specialty_min_per_week) ||
      !validateHalfDayRange(data.specialty_max_per_week)) {
    errors.specialty = 'Specialty values must be between 0 and 14';
  } else if (!validateMinMax(data.specialty_min_per_week, data.specialty_max_per_week)) {
    errors.specialty = 'Specialty minimum cannot exceed maximum';
  }

  return errors;
}

/**
 * Checks if form data has validation errors
 */
export function hasValidationErrors(errors: WeeklyRequirementFormErrors): boolean {
  return Object.keys(errors).length > 0;
}
