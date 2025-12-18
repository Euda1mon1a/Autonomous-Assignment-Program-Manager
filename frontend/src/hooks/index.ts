/**
 * React Query Hooks for Residency Scheduler
 *
 * Centralized exports for all domain-specific hooks.
 * Provides data fetching hooks with caching, loading states,
 * and error handling for all API endpoints.
 */

// ============================================================================
// Schedule Hooks
// ============================================================================
export {
  useSchedule,
  useGenerateSchedule,
  useValidateSchedule,
  useRotationTemplates,
  useRotationTemplate,
  useCreateTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
  useAssignments,
  useCreateAssignment,
  useUpdateAssignment,
  useDeleteAssignment,
  scheduleQueryKeys,
  type ScheduleGenerateRequest,
  type ScheduleGenerateResponse,
  type AssignmentFilters,
} from './useSchedule'

// ============================================================================
// People Hooks
// ============================================================================
export {
  usePeople,
  usePerson,
  useResidents,
  useFaculty,
  useCreatePerson,
  useUpdatePerson,
  useDeletePerson,
  peopleQueryKeys,
  type PeopleFilters,
} from './usePeople'

// ============================================================================
// Absence Hooks
// ============================================================================
export {
  useAbsences,
  useAbsence,
  useCreateAbsence,
  useUpdateAbsence,
  useDeleteAbsence,
  absenceQueryKeys,
  type AbsenceFilters,
} from './useAbsences'

// ============================================================================
// Resilience Hooks
// ============================================================================
export {
  useEmergencyCoverage,
  type EmergencyCoverageRequest,
  type EmergencyCoverageResponse,
} from './useResilience'

// ============================================================================
// Shared Types
// ============================================================================
export type { ListResponse } from './useSchedule'

// ============================================================================
// Query Keys (backward compatibility)
// ============================================================================
export const queryKeys = {
  // Schedule-related keys
  schedule: (startDate: string, endDate: string) => ['schedule', startDate, endDate] as const,
  rotationTemplates: (activityType?: string) => ['rotation-templates', activityType] as const,
  rotationTemplate: (id: string) => ['rotation-templates', id] as const,
  validation: (startDate: string, endDate: string) => ['validation', startDate, endDate] as const,
  assignments: (filters?: AssignmentFilters) => ['assignments', filters] as const,

  // People-related keys
  people: (filters?: PeopleFilters) => ['people', filters] as const,
  person: (id: string) => ['people', id] as const,
  residents: (pgyLevel?: number) => ['residents', pgyLevel] as const,
  faculty: (specialty?: string) => ['faculty', specialty] as const,

  // Absence-related keys
  absences: (filters?: AbsenceFilters) => ['absences', filters] as const,
  absence: (id: string) => ['absences', id] as const,
}
