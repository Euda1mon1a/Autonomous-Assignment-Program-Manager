/**
 * My Life Dashboard Feature Module
 *
 * Provides comprehensive personal schedule dashboard UI components
 * for residents to view their upcoming assignments, manage swap requests,
 * track absences, and sync their schedule to external calendars.
 *
 * Components:
 * - MyLifeDashboard: Main dashboard page component
 * - SummaryCard: Metric display card for key statistics
 * - UpcomingSchedule: List of upcoming assignments with swap actions
 * - PendingSwaps: Pending swap requests display
 * - CalendarSync: Calendar synchronization modal
 *
 * Hooks:
 * - useMyDashboard: Fetch complete dashboard data
 * - useCalendarSync: Calendar sync mutation
 * - useRequestSwap: Create swap request for assignment
 * - useCalendarSyncUrl: Fetch calendar subscription URL
 */

// Components
export { MyLifeDashboard } from './MyLifeDashboard';
export { SummaryCard } from './SummaryCard';
export { UpcomingSchedule } from './UpcomingSchedule';
export { PendingSwaps } from './PendingSwaps';
export { CalendarSync } from './CalendarSync';

// Hooks
export {
  useMyDashboard,
  useCalendarSync,
  useRequestSwap,
  useCalendarSyncUrl,
  dashboardQueryKeys,
} from './hooks';

// Types
export type {
  UpcomingAssignment,
  PendingSwapSummary,
  AbsenceEntry,
  DashboardSummary,
  DashboardData,
  DashboardQueryParams,
  CalendarSyncRequest,
  CalendarSyncResponse,
} from './types';

// Enums
export { TimeOfDay, Location } from './types';

// Constants
export {
  TIME_OF_DAY_LABELS,
  LOCATION_LABELS,
  LOCATION_COLORS,
  DEFAULT_DAYS_AHEAD,
  MAX_DAYS_AHEAD,
} from './types';
