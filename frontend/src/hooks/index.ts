/**
 * React Query Hooks for Residency Scheduler
 *
 * Centralized exports for all domain-specific hooks.
 * Provides data fetching hooks with caching, loading states,
 * and error handling for all API endpoints.
 */

// Import types needed for queryKeys object
import type { AbsenceFilters } from "./useAbsences";
import type { PeopleFilters } from "./usePeople";
import type { AssignmentFilters } from "./useSchedule";
import type { SwapFilters } from "./useSwaps";

// ============================================================================
// Authentication Hooks
// ============================================================================
export {
  authQueryKeys,
  useAuth,
  useAuthCheck,
  useLogin,
  useLogout,
  usePermissions,
  useRole,
  useUser,
  useValidateSession,
  type Permission,
  type UserRole,
} from "./useAuth";

// ============================================================================
// Schedule Hooks
// ============================================================================
export {
  scheduleQueryKeys,
  useAssignments,
  useCreateAssignment,
  useCreateTemplate,
  useDeleteAssignment,
  useDeleteTemplate,
  useGenerateSchedule,
  useRotationTemplate,
  useRotationTemplates,
  useSchedule,
  useUpdateAssignment,
  useUpdateTemplate,
  useValidateSchedule,
  type AssignmentFilters,
  type ScheduleGenerateRequest,
  type ScheduleGenerateResponse,
} from "./useSchedule";

// ============================================================================
// People Hooks
// ============================================================================
export {
  peopleQueryKeys,
  useCertifications,
  useCreatePerson,
  useDeletePerson,
  useFaculty,
  usePeople,
  usePerson,
  useResidents,
  useUpdatePerson,
  type CertificationStatus,
  type CertificationType,
  type PeopleFilters,
  type PersonCertification,
  type PersonStatus,
  type PersonType,
} from "./usePeople";

// ============================================================================
// Absence Hooks
// ============================================================================
export {
  absenceQueryKeys,
  useAbsence,
  useAbsences,
  useAwayComplianceDashboard,
  useCreateAbsence,
  useDeleteAbsence,
  useUpdateAbsence,
  type AbsenceFilters,
} from "./useAbsences";

// ============================================================================
// Block Hooks
// ============================================================================
export {
  blockQueryKeys,
  useBlockRanges,
  useBlocks,
  type BlockFilters,
  type BlockRange,
} from "./useBlocks";

// ============================================================================
// Resilience Hooks
// ============================================================================
export {
  resilienceQueryKeys,
  useBreakerHealth,
  useBurnoutRt,
  useCircuitBreakers,
  useDefenseLevel,
  useEmergencyCoverage,
  useMTFCompliance,
  useSystemHealth,
  useUnifiedCriticalIndex,
  useUtilizationThreshold,
  useVulnerabilityReport,
} from "./useResilience";

// ============================================================================
// Thermodynamics Hooks
// ============================================================================
export {
  useFreeEnergy,
  useEnergyLandscape,
  type FreeEnergyRequest,
  type FreeEnergyResponse,
  type EnergyLandscapeRequest,
  type EnergyLandscapeResponse,
} from "./useThermodynamics";

// ============================================================================
// Health Hooks
// ============================================================================
export {
  healthQueryKeys,
  useHealthDetailed,
  useHealthLive,
  useHealthReady,
  useServiceHealth,
  type HealthDetailedResponse,
  type HealthLiveResponse,
  type HealthReadyResponse,
  type ServiceHealth,
} from "./useHealth";

// ============================================================================
// Swap Hooks
// ============================================================================
export {
  swapQueryKeys,
  SwapStatus,
  SwapType,
  useAutoMatch,
  useSwapApprove,
  useSwapCandidates,
  useSwapCreate,
  useSwapList,
  useSwapReject,
  useSwapRequest,
  type AutoMatchRequest,
  type AutoMatchResponse,
  type SwapActionResponse,
  type SwapApproveRequest,
  type SwapCandidate,
  type SwapCreateRequest,
  type SwapCreateResponse,
  type SwapFilters,
  type SwapRejectRequest,
  type SwapRequest,
} from "./useSwaps";

// ============================================================================
// Admin Scheduling Hooks
// ============================================================================
export {
  adminSchedulingKeys,
  useCancelExperiment,
  useConstraintConfigs,
  useCreateEmergencyHoliday,
  useCreateRollbackPoint,
  useDeleteEmergencyHoliday,
  useEmergencyHolidays,
  useGenerateScheduleRun,
  useLockAssignment,
  useLockedAssignments,
  useMetricsTrend,
  useQueueExperiments,
  useRevertToRollbackPoint,
  useRollbackPoints,
  useRunComparison,
  useRunQueue,
  useScenarioPresets,
  useScheduleMetrics,
  useScheduleRun,
  useScheduleRuns,
  useSeedCleanup,
  useSyncMetadata,
  useTriggerSync,
  useUnlockAssignment,
  useValidateConfiguration,
} from "./useAdminScheduling";

// ============================================================================
// Admin User Management Hooks
// ============================================================================
export {
  adminUsersQueryKeys,
  useUser as useAdminUser,
  useBulkUserAction,
  useCreateUser,
  useDeleteUser,
  useResendInvite,
  useToggleUserLock,
  useUpdateUser,
  useUsers,
  type AdminUserFilters,
  type BulkActionResponse,
  type LockUserResponse,
  type ResendInviteResponse,
} from "./useAdminUsers";

// ============================================================================
// Procedure Credentialing Hooks
// ============================================================================
export {
  credentialKeys,
  procedureKeys,
  useCreateCredential,
  useCreateProcedure,
  useCredential,
  useCredentials,
  useDeleteCredential,
  useFacultyCredentials,
  useProcedure,
  useProcedures,
  useQualifiedFaculty,
  useUpdateCredential,
  useUpdateProcedure,
  type Credential,
  type CredentialWithProcedure,
  type FacultyCredentialSummary,
  type Procedure,
} from "./useProcedures";

// ============================================================================
// RAG Hooks
// ============================================================================
export {
  ragQueryKeys,
  useRAGHealth,
  useRAGSearch,
  type RAGCategory,
  type RAGChunk,
  type RAGHealthResponse,
  type RAGRetrieveRequest,
  type RAGRetrieveResponse,
} from "./useRAG";

// ============================================================================
// Weekly Pattern Hooks
// ============================================================================
export {
  weeklyPatternQueryKeys,
  useWeeklyPattern,
  useUpdateWeeklyPattern,
  useAvailableTemplates,
} from "./useWeeklyPattern";

// ============================================================================
// Half-Day Requirements Hooks
// ============================================================================
export {
  halfDayRequirementsQueryKeys,
  useHalfDayRequirements,
  useUpdateHalfDayRequirements,
  calculateTotalHalfdays,
  isRequirementsBalanced,
  DEFAULT_HALFDAY_REQUIREMENTS,
  type HalfDayRequirementsUpdateRequest,
} from "./useHalfDayRequirements";

// ============================================================================
// WebSocket Hooks
// ============================================================================
export {
  usePersonWebSocket,
  useScheduleWebSocket,
  useWebSocket,
  type AnyWebSocketEvent,
  type AssignmentChangedEvent,
  type ClientAction,
  type ClientMessage,
  type ConflictDetectedEvent,
  type ConnectionAckEvent,
  type ConnectionState,
  type EventType,
  type ResilienceAlertEvent,
  type ScheduleUpdatedEvent,
  type SwapApprovedEvent,
  type SwapRequestedEvent,
  type UseWebSocketOptions,
  type UseWebSocketReturn,
  type WebSocketEvent,
} from "./useWebSocket";

// ============================================================================
// Keyboard Shortcuts Hooks
// ============================================================================
export {
  useKeyboardShortcuts,
  useKeyboardShortcut,
  getShortcutDisplay,
  type KeyboardShortcut,
  type ModifierKey,
  type UseKeyboardShortcutsOptions,
} from "./useKeyboardShortcuts";

// ============================================================================
// Debounce Hooks
// ============================================================================
export {
  useDebounce,
  useDebouncedCallback,
  useDebouncedState,
} from "./useDebounce";

// ============================================================================
// Backup Hooks
// ============================================================================
export {
  backupQueryKeys,
  useSnapshots,
  useCreateSnapshot,
  useRestoreSnapshot,
  useWithBackup,
  type SnapshotRequest,
  type SnapshotResponse,
  type SnapshotListResponse,
  type RestoreRequest,
  type RestoreResponse,
} from "./useBackup";

// ============================================================================
// Impersonation Hooks
// ============================================================================
export {
  impersonationQueryKeys,
  useImpersonation,
  useImpersonationStatus,
  useStartImpersonation,
  useEndImpersonation,
  getImpersonationToken,
  type ImpersonatedUser,
  type ImpersonationStatusResponse,
  type StartImpersonationResponse,
  type EndImpersonationResponse,
} from "./useImpersonation";

// ============================================================================
// Shared Types
// ============================================================================
export type { ListResponse } from "./useSchedule";

// ============================================================================
// Query Keys (backward compatibility)
// ============================================================================

/**
 * Centralized query key factory for React Query cache management.
 *
 * This object provides type-safe query keys for all domain entities in the
 * residency scheduler. Using consistent query keys enables React Query to
 * properly cache, invalidate, and refetch data across the application.
 *
 * @deprecated Use domain-specific query key factories instead:
 * - `authQueryKeys` from './useAuth'
 * - `scheduleQueryKeys` from './useSchedule'
 * - `peopleQueryKeys` from './usePeople'
 * - `absenceQueryKeys` from './useAbsences'
 * - `swapQueryKeys` from './useSwaps'
 *
 * @example
 * ```tsx
 * // Invalidate all schedule queries
 * queryClient.invalidateQueries({ queryKey: queryKeys.schedule('2024-01-01', '2024-01-31') });
 *
 * // Invalidate all people queries
 * queryClient.invalidateQueries({ queryKey: ['people'] });
 * ```
 */
export const queryKeys = {
  // Auth-related keys
  authUser: () => ["auth", "user"] as const,
  authCheck: () => ["auth", "check"] as const,
  authValidate: () => ["auth", "validate"] as const,

  // Schedule-related keys
  schedule: (startDate: string, endDate: string) =>
    ["schedule", startDate, endDate] as const,
  rotationTemplates: (activityType?: string) =>
    ["rotation-templates", activityType] as const,
  rotationTemplate: (id: string) => ["rotation-templates", id] as const,
  validation: (startDate: string, endDate: string) =>
    ["validation", startDate, endDate] as const,
  assignments: (filters?: AssignmentFilters) =>
    ["assignments", filters] as const,

  // People-related keys
  people: (filters?: PeopleFilters) => ["people", filters] as const,
  person: (id: string) => ["people", id] as const,
  residents: (pgyLevel?: number) => ["residents", pgyLevel] as const,
  faculty: (specialty?: string) => ["faculty", specialty] as const,
  certifications: (personId: string) =>
    ["certifications", "person", personId] as const,

  // Absence-related keys
  absences: (filters?: AbsenceFilters) => ["absences", filters] as const,
  absence: (id: string) => ["absences", id] as const,

  // Swap-related keys
  swaps: (filters?: SwapFilters) => ["swaps", "list", filters] as const,
  swap: (id: string) => ["swaps", "detail", id] as const,
  swapCandidates: (sourceId: string, sourceWeek: string) =>
    ["swaps", "candidates", sourceId, sourceWeek] as const,
};
