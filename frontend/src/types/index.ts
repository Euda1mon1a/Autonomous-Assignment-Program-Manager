// Core types for the Residency Scheduler
// Re-exports from api.ts with additional view-specific types

// Re-export all types and enums from api.ts
export * from './api';

// Re-export admin scheduling types
export * from './admin-scheduling';

// Re-export state management types
export * from './state';

// Re-export chat types
export * from './chat';

// Re-export weekly pattern types
export * from './weekly-pattern';

// Import specific types for use in view-specific interfaces
import {
  UUID,
  DateString,
  DateTimeString,
  PersonType,
  TimeOfDay,
  AssignmentRole
} from './api';

// ============================================================================
// View-Specific Types
// ============================================================================

/**
 * Detailed schedule response organized by date and time of day
 * Used for calendar/grid view of the schedule
 */
export interface ScheduleViewResponse {
  /** Start date of the schedule period */
  start_date: DateString;
  /** End date of the schedule period */
  end_date: DateString;
  /** Schedule organized by date, then by time of day (AM/PM) */
  schedule: Record<DateString, {
    /** Assignments for the morning shift */
    AM: AssignmentDetail[];
    /** Assignments for the afternoon/evening shift */
    PM: AssignmentDetail[];
  }>;
  /** Total number of assignments in the schedule */
  total_assignments: number;
}

/**
 * Detailed information about an assignment for display purposes
 * Includes denormalized person information for efficient rendering
 */
export interface AssignmentDetail {
  /** Assignment ID */
  id: UUID;
  /** Person information (denormalized) */
  person: {
    /** Person ID */
    id: UUID;
    /** Full name */
    name: string;
    /** Type of person (resident or faculty) */
    type: PersonType;
    /** Post-graduate year level (for residents) */
    pgy_level: number | null;
  };
  /** Role in this assignment */
  role: AssignmentRole;
  /** Activity/rotation name */
  activity: string;
  /** Short abbreviation for display (may include time suffix like C-AM) */
  abbreviation: string;
  /** User-facing abbreviation for schedule grid (short codes like C, FMIT) */
  display_abbreviation?: string;
}

/**
 * Person information with additional computed fields for display
 */
export interface PersonWithStats {
  /** Person ID */
  id: UUID;
  /** Full name */
  name: string;
  /** Email address */
  email: string | null;
  /** Type of person */
  type: PersonType;
  /** Post-graduate year level */
  pgy_level: number | null;
  /** Whether credentialed for procedures */
  performs_procedures: boolean;
  /** Medical specialties */
  specialties: string[] | null;
  /** Primary duty assignment */
  primary_duty: string | null;
  /** Record creation timestamp */
  created_at: DateTimeString;
  /** Record update timestamp */
  updated_at: DateTimeString;
  /** Total number of assignments (computed) */
  total_assignments?: number;
  /** Number of upcoming assignments (computed) */
  upcoming_assignments?: number;
  /** Whether the person has any current absences (computed) */
  has_current_absence?: boolean;
}

/**
 * Block information with assignment count for display
 */
export interface BlockWithAssignments {
  /** Block ID */
  id: UUID;
  /** Date of the block */
  date: DateString;
  /** Time period */
  time_of_day: TimeOfDay;
  /** Block number */
  block_number: number;
  /** Whether this is a weekend */
  is_weekend: boolean;
  /** Whether this is a holiday */
  is_holiday: boolean;
  /** Holiday name if applicable */
  holiday_name: string | null;
  /** Number of assignments in this block (computed) */
  assignment_count?: number;
  /** Whether this block is fully staffed (computed) */
  is_fully_staffed?: boolean;
}
