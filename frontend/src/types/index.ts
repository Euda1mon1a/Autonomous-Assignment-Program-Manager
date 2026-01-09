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

// Re-export block assignment import types
export * from './block-assignment-import';

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
  startDate: DateString;
  /** End date of the schedule period */
  endDate: DateString;
  /** Schedule organized by date, then by time of day (AM/PM) */
  schedule: Record<DateString, {
    /** Assignments for the morning shift */
    AM: AssignmentDetail[];
    /** Assignments for the afternoon/evening shift */
    PM: AssignmentDetail[];
  }>;
  /** Total number of assignments in the schedule */
  totalAssignments: number;
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
    pgyLevel: number | null;
  };
  /** Role in this assignment */
  role: AssignmentRole;
  /** Activity/rotation name */
  activity: string;
  /** Short abbreviation for display (may include time suffix like C-AM) */
  abbreviation: string;
  /** User-facing abbreviation for schedule grid (short codes like C, FMIT) */
  displayAbbreviation?: string;
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
  pgyLevel: number | null;
  /** Whether credentialed for procedures */
  performsProcedures: boolean;
  /** Medical specialties */
  specialties: string[] | null;
  /** Primary duty assignment */
  primaryDuty: string | null;
  /** Record creation timestamp */
  createdAt: DateTimeString;
  /** Record update timestamp */
  updatedAt: DateTimeString;
  /** Total number of assignments (computed) */
  totalAssignments?: number;
  /** Number of upcoming assignments (computed) */
  upcomingAssignments?: number;
  /** Whether the person has any current absences (computed) */
  hasCurrentAbsence?: boolean;
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
  timeOfDay: TimeOfDay;
  /** Block number */
  blockNumber: number;
  /** Whether this is a weekend */
  isWeekend: boolean;
  /** Whether this is a holiday */
  isHoliday: boolean;
  /** Holiday name if applicable */
  holidayName: string | null;
  /** Number of assignments in this block (computed) */
  assignmentCount?: number;
  /** Whether this block is fully staffed (computed) */
  isFullyStaffed?: boolean;
}
