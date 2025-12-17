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
  assignment_id: string;
  faculty_id: string;
  faculty_name: string;
  rotation_name: string;
  rotation_id: string;
  start_date: string;
  end_date: string;
  status: AssignmentStatus;
  activity_type: string;
  hours_per_week: number;
  color: string;
  notes?: string;
}

/**
 * Faculty row data for timeline
 */
export interface FacultyTimelineRow {
  faculty_id: string;
  faculty_name: string;
  specialty: string;
  workload_status: WorkloadStatus;
  total_hours: number;
  assignments: TimelineAssignment[];
  utilization_percentage: number;
}

/**
 * Timeline data structure
 */
export interface TimelineData {
  start_date: string;
  end_date: string;
  view_mode: TimelineViewMode;
  faculty_rows: FacultyTimelineRow[];
  time_periods: TimePeriod[];
}

/**
 * Time period for X-axis
 */
export interface TimePeriod {
  label: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
}

/**
 * Timeline metrics
 */
export interface TimelineMetrics {
  total_faculty: number;
  total_assignments: number;
  average_utilization: number;
  overloaded_faculty: number;
  underutilized_faculty: number;
  total_hours_scheduled: number;
}

// ============================================================================
// API Request/Response Types
// ============================================================================

/**
 * Timeline filters
 */
export interface TimelineFilters {
  start_date?: string;
  end_date?: string;
  faculty_ids?: string[];
  rotation_ids?: string[];
  specialty?: string;
  workload_status?: WorkloadStatus[];
  view_mode?: TimelineViewMode;
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
    total_assignments: number;
    total_hours: number;
    utilization_percentage: number;
    busiest_week: string;
  };
}

/**
 * Academic year
 */
export interface AcademicYear {
  id: string;
  label: string;
  start_date: string;
  end_date: string;
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
 * Get weeks in date range
 */
export function getWeeksInRange(startDate: string, endDate: string): TimePeriod[] {
  const periods: TimePeriod[] = [];
  const start = new Date(startDate);
  const end = new Date(endDate);
  const today = new Date();

  let current = new Date(start);
  let weekNum = 1;

  while (current <= end) {
    const weekStart = new Date(current);
    const weekEnd = new Date(current);
    weekEnd.setDate(weekEnd.getDate() + 6);

    const isCurrent = today >= weekStart && today <= weekEnd;

    periods.push({
      label: `Week ${weekNum}`,
      start_date: weekStart.toISOString().split('T')[0],
      end_date: (weekEnd > end ? end : weekEnd).toISOString().split('T')[0],
      is_current: isCurrent,
    });

    current.setDate(current.getDate() + 7);
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

  let current = new Date(start.getFullYear(), start.getMonth(), 1);

  while (current <= end) {
    const monthStart = new Date(current);
    const monthEnd = new Date(current.getFullYear(), current.getMonth() + 1, 0);

    const isCurrent =
      today.getMonth() === monthStart.getMonth() &&
      today.getFullYear() === monthStart.getFullYear();

    periods.push({
      label: monthStart.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
      start_date: (monthStart < start ? start : monthStart).toISOString().split('T')[0],
      end_date: (monthEnd > end ? end : monthEnd).toISOString().split('T')[0],
      is_current: isCurrent,
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

  let current = new Date(start.getFullYear(), Math.floor(start.getMonth() / 3) * 3, 1);

  while (current <= end) {
    const quarterStart = new Date(current);
    const quarterEnd = new Date(current.getFullYear(), current.getMonth() + 3, 0);

    const isCurrent =
      today >= quarterStart && today <= quarterEnd;

    const quarter = Math.floor(quarterStart.getMonth() / 3) + 1;

    periods.push({
      label: `Q${quarter} ${quarterStart.getFullYear()}`,
      start_date: (quarterStart < start ? start : quarterStart).toISOString().split('T')[0],
      end_date: (quarterEnd > end ? end : quarterEnd).toISOString().split('T')[0],
      is_current: isCurrent,
    });

    current.setMonth(current.getMonth() + 3);
  }

  return periods;
}
