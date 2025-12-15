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
