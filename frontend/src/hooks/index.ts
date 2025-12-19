/**
 * React Query Hooks for Residency Scheduler
 *
 * Centralized exports for all domain-specific hooks.
 * Provides data fetching hooks with caching, loading states,
 * and error handling for all API endpoints.
 */

// Import types needed for queryKeys object
import type { AssignmentFilters } from './useSchedule'
import type { PeopleFilters } from './usePeople'
import type { AbsenceFilters } from './useAbsences'
import type { SwapFilters } from './useSwaps'

// ============================================================================
// Authentication Hooks
// ============================================================================
export {
  useAuth,
  useLogin,
  useLogout,
  useUser,
  useAuthCheck,
  useValidateSession,
  usePermissions,
  useRole,
  authQueryKeys,
  type UserRole,
  type Permission,
} from './useAuth'

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
  useCertifications,
  peopleQueryKeys,
  type PeopleFilters,
  type PersonType,
  type PersonStatus,
  type CertificationStatus,
  type CertificationType,
  type PersonCertification,
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
// Swap Hooks
// ============================================================================
export {
  useSwapRequest,
  useSwapList,
  useSwapCandidates,
  useSwapCreate,
  useSwapApprove,
  useSwapReject,
  useAutoMatch,
  swapQueryKeys,
  SwapStatus,
  SwapType,
  type SwapRequest,
  type SwapCreateRequest,
  type SwapCreateResponse,
  type SwapApproveRequest,
  type SwapRejectRequest,
  type SwapActionResponse,
  type SwapCandidate,
  type AutoMatchRequest,
  type AutoMatchResponse,
  type SwapFilters,
} from './useSwaps'

// ============================================================================
// Shared Types
// ============================================================================
export type { ListResponse } from './useSchedule'

// ============================================================================
// Query Keys (backward compatibility)
// ============================================================================
export const queryKeys = {
  // Auth-related keys
  authUser: () => ['auth', 'user'] as const,
  authCheck: () => ['auth', 'check'] as const,
  authValidate: () => ['auth', 'validate'] as const,

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
  certifications: (personId: string) => ['certifications', 'person', personId] as const,

  // Absence-related keys
  absences: (filters?: AbsenceFilters) => ['absences', filters] as const,
  absence: (id: string) => ['absences', id] as const,

  // Swap-related keys
  swaps: (filters?: SwapFilters) => ['swaps', 'list', filters] as const,
  swap: (id: string) => ['swaps', 'detail', id] as const,
  swapCandidates: (sourceId: string, sourceWeek: string) =>
    ['swaps', 'candidates', sourceId, sourceWeek] as const,
}
