/**
 * Call Roster Feature Module
 *
 * Provides a comprehensive on-call roster view showing who is on call
 * and their contact information. Critical for nurses to know who to page.
 *
 * Components:
 * - CallRoster: Main calendar/list view component
 * - CallCard: Individual call entry card with contact details
 * - CallCalendarDay: Calendar day cell for month view
 * - ContactInfo: Phone/pager/email display with copy functionality
 *
 * Hooks:
 * - useOnCallAssignments: Fetch on-call assignments for date range
 * - useMonthlyOnCallRoster: Fetch on-call roster for a specific month
 * - useTodayOnCall: Fetch today's on-call assignments
 * - usePersonOnCallAssignments: Fetch on-call shifts for specific person
 * - useOnCallByDate: Group on-call assignments by date
 *
 * Features:
 * - Month view calendar with color-coded roles (Red=Attending, Blue=Senior, Green=Intern)
 * - List view for detailed information
 * - Today's on-call highlight section
 * - Click-to-call phone numbers
 * - Copy pager/phone numbers to clipboard
 * - Role filtering
 * - Hover tooltips with contact information
 */

// ============================================================================
// Components
// ============================================================================

export { CallRoster } from './CallRoster';
export {
  CallCard,
  CallCardCompact,
  CallListItem,
} from './CallCard';
export {
  CallCalendarDay,
  CalendarDayHeader,
  EmptyCalendarDay,
} from './CallCalendarDay';
export {
  ContactInfo,
  ContactBadge,
} from './ContactInfo';

// ============================================================================
// Hooks
// ============================================================================

export {
  useOnCallAssignments,
  useMonthlyOnCallRoster,
  useTodayOnCall,
  usePersonOnCallAssignments,
  useOnCallByDate,
  callRosterQueryKeys,
} from './hooks';

// ============================================================================
// Types
// ============================================================================

export type {
  RoleType,
  OnCallPerson,
  CallAssignment,
  CallRosterEntry,
  Assignment,
  AssignmentsResponse,
  CallRosterFilters,
  ViewMode,
  DateRange,
  CalendarDay,
  CalendarWeek,
} from './types';

// ============================================================================
// Constants
// ============================================================================

export {
  ROLE_COLORS,
  ROLE_LABELS,
  SHIFT_LABELS,
  getRoleType,
  getPersonName,
  isOnCallTemplate,
  getShiftType,
} from './types';
