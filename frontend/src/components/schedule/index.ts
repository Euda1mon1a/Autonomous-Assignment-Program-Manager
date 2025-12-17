// Schedule View Components
// These components provide multiple view options for schedule viewing

export { ViewToggle, useScheduleView } from './ViewToggle'
export type { ScheduleView, ViewToggleProps } from './ViewToggle'

export { DayView } from './DayView'
export type { DayViewProps } from './DayView'

export { WeekView } from './WeekView'
export type { WeekViewProps } from './WeekView'

export { MonthView } from './MonthView'
export type { MonthViewProps } from './MonthView'

/**
 * Assignment Editing Components
 *
 * Components for editing assignments with warning system.
 * Warns but does not block - humans have final authority.
 */

// Modal for editing or creating assignments
export { EditAssignmentModal } from './EditAssignmentModal'
export type { EditAssignmentModalProps } from './EditAssignmentModal'

// Warning display component for assignment conflicts
export { AssignmentWarnings, WarningBadge, generateWarnings } from './AssignmentWarnings'
export type {
  AssignmentWarning,
  WarningType,
  WarningSeverity,
  WarningCheckContext,
} from './AssignmentWarnings'

/**
 * Personal Schedule View Components
 *
 * Components for viewing and filtering individual schedules.
 */

// Person filter dropdown with search and grouping
export { PersonFilter } from './PersonFilter'
export type { PersonFilterProps } from './PersonFilter'

// Personal schedule card for viewing single person's schedule
export { PersonalScheduleCard } from './PersonalScheduleCard'
export type {
  PersonalScheduleCardProps,
  ScheduleAssignment,
  DaySchedule,
} from './PersonalScheduleCard'

// Dashboard widget showing current user's upcoming assignments
export { MyScheduleWidget } from './MyScheduleWidget'

/**
 * On-Call Roster Component
 *
 * Component for displaying on-call schedules with color coding.
 * Designed for nursing staff to quickly identify who to page.
 */

// Call roster for displaying on-call assignments with seniority color coding
export { CallRoster } from './CallRoster'
export type { CallRosterProps } from './CallRoster'
