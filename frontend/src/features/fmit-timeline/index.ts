/**
 * FMIT Timeline Feature Module
 *
 * Provides Gantt-style timeline visualization UI components for viewing
 * faculty assignments, workload distribution, and utilization over time.
 *
 * Components:
 * - FMITTimeline: Main timeline visualization component with Gantt-style view
 * - TimelineControls: Filtering and control UI (date range, view modes, filters)
 * - TimelineRow: Individual faculty row with assignment blocks
 * - AssignmentTooltip: Hover tooltip for assignment details
 *
 * Hooks:
 * - useFMITTimeline: Fetch timeline data with filters
 * - useFacultyTimeline: Fetch single faculty timeline
 * - useTimelineMetrics: Fetch aggregate metrics
 * - useAvailableFaculty: Fetch faculty list for filtering
 * - useAvailableRotations: Fetch rotation list for filtering
 * - useAcademicYears: Fetch academic years for year selector
 * - usePrefetchTimeline: Prefetch timeline data
 * - useInvalidateTimeline: Invalidate timeline queries
 */

// Components
export { FMITTimeline, FMITTimelineSkeleton } from './FMITTimeline';
export { TimelineControls } from './TimelineControls';
export { TimelineRow, AssignmentTooltip } from './TimelineRow';

// Hooks
export {
  useFMITTimeline,
  useFacultyTimeline,
  useTimelineMetrics,
  useAvailableFaculty,
  useAvailableRotations,
  useAcademicYears,
  usePrefetchTimeline,
  useInvalidateTimeline,
  timelineQueryKeys,
} from './hooks';

// Types
export type {
  TimelineViewMode,
  WorkloadStatus,
  AssignmentStatus,
  TimelineAssignment,
  FacultyTimelineRow,
  TimelineData,
  TimePeriod,
  TimelineMetrics,
  TimelineFilters,
  TimelineResponse,
  FacultyTimelineResponse,
  AcademicYear,
  DateRange,
  TimelinePageState,
  AssignmentTooltipData,
} from './types';

// Constants
export {
  VIEW_MODE_LABELS,
  WORKLOAD_STATUS_COLORS,
  WORKLOAD_STATUS_LABELS,
  ASSIGNMENT_STATUS_COLORS,
  ACTIVITY_TYPE_COLORS,
  getDefaultDateRange,
  getWeeksInRange,
  getMonthsInRange,
  getQuartersInRange,
} from './types';
