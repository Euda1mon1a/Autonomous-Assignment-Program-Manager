/**
 * FMIT Timeline Types and Interfaces
 *
 * Defines the data structures for Gantt-style timeline visualization
 * showing faculty assignments and workload over time.
 */

// ============================================================================
// Core Timeline Types
// ============================================================================

/**
 * Timeline view mode
 */
export type TimelineViewMode = 'weekly' | 'monthly' | 'quarterly';

/**
 * Workload status indicator
 */
export type WorkloadStatus = 'on-track' | 'overloaded' | 'underutilized';

/**
 * Assignment status
 */
export type AssignmentStatus = 'scheduled' | 'in-progress' | 'completed' | 'cancelled';

/**
 * Assignment block on timeline
 */
export interface TimelineAssignment {
  id: string;
  assignmentId: string;
  facultyId: string;
  facultyName: string;
  rotationName: string;
  rotationId: string;
  startDate: string;
  endDate: string;
  status: AssignmentStatus;
  activityType: string;
  hoursPerWeek: number;
  color: string;
  notes?: string;
}

/**
 * Faculty row data for timeline
 */
export interface FacultyTimelineRow {
  facultyId: string;
  facultyName: string;
  specialty: string;
  workloadStatus: WorkloadStatus;
  totalHours: number;
  assignments: TimelineAssignment[];
  utilizationPercentage: number;
}

/**
 * Timeline data structure
 */
export interface TimelineData {
  startDate: string;
  endDate: string;
  viewMode: TimelineViewMode;
  facultyRows: FacultyTimelineRow[];
  timePeriods: TimePeriod[];
}

/**
 * Time period for X-axis
 */
export interface TimePeriod {
  label: string;
  startDate: string;
  endDate: string;
  isCurrent: boolean;
}

/**
 * Timeline metrics
 */
export interface TimelineMetrics {
  totalFaculty: number;
  totalAssignments: number;
  averageUtilization: number;
  overloadedFaculty: number;
  underutilizedFaculty: number;
  totalHoursScheduled: number;
}

// ============================================================================
// API Request/Response Types
// ============================================================================

/**
 * Timeline filters
 */
export interface TimelineFilters {
  startDate?: string;
  endDate?: string;
  facultyIds?: string[];
  rotationIds?: string[];
  specialty?: string;
  workloadStatus?: WorkloadStatus[];
  viewMode?: TimelineViewMode;
}

/**
 * Timeline response from API
 */
export interface TimelineResponse {
  timeline: TimelineData;
  metrics: TimelineMetrics;
}

/**
 * Faculty timeline response (single faculty)
 */
export interface FacultyTimelineResponse {
  faculty: {
    id: string;
    name: string;
    specialty: string;
  };
  timeline: FacultyTimelineRow;
  metrics: {
    totalAssignments: number;
    totalHours: number;
    utilizationPercentage: number;
    busiestWeek: string;
  };
}

/**
 * Academic year
 */
export interface AcademicYear {
  id: string;
  label: string;
  startDate: string;
  endDate: string;
}

// ============================================================================
// UI State Types
// ============================================================================

/**
 * Date range for filtering
 */
export interface DateRange {
  start: string;
  end: string;
}

/**
 * Timeline page state
 */
export interface TimelinePageState {
  viewMode: TimelineViewMode;
  filters: TimelineFilters;
  dateRange: DateRange;
  selectedFacultyIds: string[];
  selectedRotationIds: string[];
  isFilterPanelOpen: boolean;
  hoveredAssignment: string | null;
  selectedAcademicYear: string | null;
}

/**
 * Assignment tooltip data
 */
export interface AssignmentTooltipData {
  assignment: TimelineAssignment;
  position: { x: number; y: number };
}

// ============================================================================
// Constants
// ============================================================================

/**
 * Display labels for view modes
 */
export const VIEW_MODE_LABELS: Record<TimelineViewMode, string> = {
  weekly: 'Weekly View',
  monthly: 'Monthly View',
  quarterly: 'Quarterly View',
};

/**
 * Workload status colors
 */
export const WORKLOAD_STATUS_COLORS: Record<WorkloadStatus, string> = {
  'on-track': '#22c55e', // green
  'overloaded': '#ef4444', // red
  'underutilized': '#fbbf24', // yellow
};

/**
 * Workload status labels
 */
export const WORKLOAD_STATUS_LABELS: Record<WorkloadStatus, string> = {
  'on-track': 'On Track',
  'overloaded': 'Overloaded',
  'underutilized': 'Underutilized',
};

/**
 * Assignment status colors
 */
export const ASSIGNMENT_STATUS_COLORS: Record<AssignmentStatus, string> = {
  'scheduled': '#3b82f6', // blue
  'in-progress': '#10b981', // green
  'completed': '#6b7280', // gray
  'cancelled': '#ef4444', // red
};

/**
 * Activity type colors for assignment blocks
 */
export const ACTIVITY_TYPE_COLORS: Record<string, string> = {
  'Clinical': '#3b82f6', // blue
  'Research': '#06b6d4', // cyan
  'Education': '#ec4899', // pink
  'Administrative': '#8b5cf6', // purple
  'FMIT': '#10b981', // green
  'Residency': '#f59e0b', // amber
  'default': '#6b7280', // gray
};

/**
 * Default date range (current academic year)
 */
export function getDefaultDateRange(): DateRange {
  const now = new Date();
  const currentMonth = now.getMonth();

  // Academic year starts in July (month 6)
  let startYear = now.getFullYear();
  if (currentMonth < 6) {
    startYear -= 1;
  }

  const start = new Date(startYear, 6, 1); // July 1
  const end = new Date(startYear + 1, 5, 30); // June 30

  return {
    start: start.toISOString().split('T')[0],
    end: end.toISOString().split('T')[0],
  };
}

/**
 * Get the Friday-Thursday FMIT week containing the given date.
 *
 * FMIT weeks run from Friday to Thursday, independent of calendar weeks.
 * This aligns with backend constraint logic in backend/app/scheduling/constraints/fmit.py
 *
 * Note: Uses UTC methods to avoid timezone issues when dates are parsed from
 * ISO date strings (which are interpreted as UTC midnight).
 *
 * @param date - Any date within the desired FMIT week
 * @returns Object with friday (week start) and thursday (week end) dates
 */
export function getFmitWeekDates(date: Date): { friday: Date; thursday: Date } {
  // Use UTC day to avoid timezone issues with ISO date strings
  const dayOfWeek = date.getUTCDay(); // 0=Sun, 1=Mon, ..., 5=Fri, 6=Sat

  // Calculate days since last Friday
  // Friday (5) -> 0, Saturday (6) -> 1, Sunday (0) -> 2, Monday (1) -> 3, etc.
  let daysSinceFriday: number;
  if (dayOfWeek >= 5) {
    // Friday (5) or Saturday (6)
    daysSinceFriday = dayOfWeek - 5;
  } else {
    // Sunday (0) through Thursday (4)
    daysSinceFriday = dayOfWeek + 2;
  }

  const friday = new Date(date);
  friday.setUTCDate(friday.getUTCDate() - daysSinceFriday);

  const thursday = new Date(friday);
  thursday.setUTCDate(thursday.getUTCDate() + 6);

  return { friday, thursday };
}

/**
 * Get weeks in date range using FMIT Friday-Thursday boundaries.
 *
 * FMIT (Faculty Management Information Timeline) weeks align with
 * the backend constraint system where weeks run Friday to Thursday.
 *
 * Note: Uses UTC methods consistently to avoid timezone issues when
 * dates are parsed from ISO date strings.
 */
export function getWeeksInRange(startDate: string, endDate: string): TimePeriod[] {
  const periods: TimePeriod[] = [];
  const start = new Date(startDate);
  const end = new Date(endDate);
  const today = new Date();

  // Adjust start to the Friday of the FMIT week containing the start date
  const { friday: firstFriday } = getFmitWeekDates(start);
  const current = new Date(firstFriday);
  let weekNum = 1;

  while (current <= end) {
    const weekStart = new Date(current); // Friday
    const weekEnd = new Date(current);
    weekEnd.setUTCDate(weekEnd.getUTCDate() + 6); // Thursday

    const isCurrent = today >= weekStart && today <= weekEnd;

    periods.push({
      label: `Week ${weekNum}`,
      startDate: weekStart.toISOString().split('T')[0],
      endDate: (weekEnd > end ? end : weekEnd).toISOString().split('T')[0],
      isCurrent: isCurrent,
    });

    current.setUTCDate(current.getUTCDate() + 7); // Next Friday
    weekNum++;
  }

  return periods;
}

/**
 * Get months in date range
 */
export function getMonthsInRange(startDate: string, endDate: string): TimePeriod[] {
  const periods: TimePeriod[] = [];
  const start = new Date(startDate);
  const end = new Date(endDate);
  const today = new Date();

  const current = new Date(start.getFullYear(), start.getMonth(), 1);

  while (current <= end) {
    const monthStart = new Date(current);
    const monthEnd = new Date(current.getFullYear(), current.getMonth() + 1, 0);

    const isCurrent =
      today.getMonth() === monthStart.getMonth() &&
      today.getFullYear() === monthStart.getFullYear();

    periods.push({
      label: monthStart.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
      startDate: (monthStart < start ? start : monthStart).toISOString().split('T')[0],
      endDate: (monthEnd > end ? end : monthEnd).toISOString().split('T')[0],
      isCurrent: isCurrent,
    });

    current.setMonth(current.getMonth() + 1);
  }

  return periods;
}

/**
 * Get quarters in date range
 */
export function getQuartersInRange(startDate: string, endDate: string): TimePeriod[] {
  const periods: TimePeriod[] = [];
  const start = new Date(startDate);
  const end = new Date(endDate);
  const today = new Date();

  const current = new Date(start.getFullYear(), Math.floor(start.getMonth() / 3) * 3, 1);

  while (current <= end) {
    const quarterStart = new Date(current);
    const quarterEnd = new Date(current.getFullYear(), current.getMonth() + 3, 0);

    const isCurrent =
      today >= quarterStart && today <= quarterEnd;

    const quarter = Math.floor(quarterStart.getMonth() / 3) + 1;

    periods.push({
      label: `Q${quarter} ${quarterStart.getFullYear()}`,
      startDate: (quarterStart < start ? start : quarterStart).toISOString().split('T')[0],
      endDate: (quarterEnd > end ? end : quarterEnd).toISOString().split('T')[0],
      isCurrent: isCurrent,
    });

    current.setMonth(current.getMonth() + 3);
  }

  return periods;
}
