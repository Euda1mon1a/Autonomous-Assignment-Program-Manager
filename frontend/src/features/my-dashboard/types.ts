/**
 * My Life Dashboard Types and Interfaces
 *
 * Defines the data structures for personal schedule dashboard,
 * including upcoming assignments, pending swaps, and absences.
 */

// ============================================================================
// Core Dashboard Types
// ============================================================================

/**
 * Time of day for an assignment
 */
export enum TimeOfDay {
  AM = 'AM',
  PM = 'PM',
  NIGHT = 'Night',
  FULL_DAY = '24h',
}

/**
 * Assignment location/service type
 */
export enum Location {
  ER = 'ER',
  ICU = 'ICU',
  WARD = 'Ward',
  CLINIC = 'Clinic',
  OR = 'OR',
  HOME_CALL = 'Home Call',
}

/**
 * Single upcoming assignment entry
 */
export interface UpcomingAssignment {
  id: string;
  date: string; // ISO date string
  timeOfDay: TimeOfDay;
  activity: string;
  location: Location;
  canTrade: boolean;
  isConflict?: boolean;
  conflictReason?: string;
}

/**
 * Pending swap request summary
 */
export interface PendingSwapSummary {
  id: string;
  type: 'incoming' | 'outgoing';
  otherFacultyName: string;
  weekDate: string; // ISO date string
  status: 'pending' | 'approved' | 'rejected';
  requestedAt: string; // ISO datetime string
  reason?: string;
  canRespond: boolean;
}

/**
 * Absence entry
 */
export interface AbsenceEntry {
  id: string;
  startDate: string; // ISO date string
  endDate: string; // ISO date string
  reason: string;
  status: 'pending' | 'approved' | 'rejected';
  requestedAt: string; // ISO datetime string
}

/**
 * Dashboard summary statistics
 */
export interface DashboardSummary {
  nextAssignment: string | null; // Human-readable text like "Today at 8 AM" or "Dec 25 (AM)"
  workloadNext4Weeks: number; // Number of shifts/assignments
  pendingSwapCount: number;
  upcomingAbsences: number;
}

/**
 * Complete dashboard data response
 */
export interface DashboardData {
  user: {
    id: string;
    name: string;
    role: string;
  };
  upcomingSchedule: UpcomingAssignment[];
  pendingSwaps: PendingSwapSummary[];
  absences: AbsenceEntry[];
  calendarSyncUrl: string;
  summary: DashboardSummary;
}

// ============================================================================
// Request/Response Types
// ============================================================================

/**
 * Query parameters for fetching dashboard data
 */
export interface DashboardQueryParams {
  daysAhead?: number; // How many days ahead to fetch (default 30)
  includeSwaps?: boolean; // Include pending swap requests (default true)
  includeAbsences?: boolean; // Include absence info (default true)
}

/**
 * Calendar sync request
 */
export interface CalendarSyncRequest {
  format: 'ics' | 'google' | 'outlook';
  includeWeeksAhead?: number; // Default 12 weeks
}

/**
 * Calendar sync response
 */
export interface CalendarSyncResponse {
  success: boolean;
  url?: string; // For ICS download or calendar subscription URL
  message?: string;
}

// ============================================================================
// Constants
// ============================================================================

export const TIME_OF_DAY_LABELS: Record<TimeOfDay, string> = {
  [TimeOfDay.AM]: 'Morning',
  [TimeOfDay.PM]: 'Afternoon',
  [TimeOfDay.NIGHT]: 'Night',
  [TimeOfDay.FULL_DAY]: '24 Hour',
};

export const LOCATION_LABELS: Record<Location, string> = {
  [Location.ER]: 'Emergency Room',
  [Location.ICU]: 'Intensive Care Unit',
  [Location.WARD]: 'Ward',
  [Location.CLINIC]: 'Clinic',
  [Location.OR]: 'Operating Room',
  [Location.HOME_CALL]: 'Home Call',
};

export const LOCATION_COLORS: Record<Location, string> = {
  [Location.ER]: 'red',
  [Location.ICU]: 'orange',
  [Location.WARD]: 'blue',
  [Location.CLINIC]: 'green',
  [Location.OR]: 'purple',
  [Location.HOME_CALL]: 'gray',
};

export const DEFAULT_DAYS_AHEAD = 30;
export const MAX_DAYS_AHEAD = 365;
