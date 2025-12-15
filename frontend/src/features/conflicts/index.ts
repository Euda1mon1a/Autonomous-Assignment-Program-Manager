/**
 * Conflict Resolution Feature
 *
 * This module provides a comprehensive conflict resolution UI for the
 * Residency Scheduler application. It includes:
 *
 * - Visual conflict detection and highlighting
 * - AI-powered resolution suggestions
 * - Manual override interface with ACGME compliance tracking
 * - Conflict history and pattern analysis
 * - Batch conflict resolution
 *
 * @module features/conflicts
 */

// ============================================================================
// Components
// ============================================================================

export { ConflictCard, getSeverityStyles, getSeverityIcon, getTypeLabel, getStatusLabel } from './ConflictCard';
export { ConflictList } from './ConflictList';
export { ConflictResolutionSuggestions } from './ConflictResolutionSuggestions';
export { ManualOverrideModal } from './ManualOverrideModal';
export { ConflictHistory, ConflictHistoryTimeline, ConflictPatternsView } from './ConflictHistory';
export { BatchResolution } from './BatchResolution';
export { ConflictDashboard } from './ConflictDashboard';

// ============================================================================
// Hooks
// ============================================================================

export {
  // Query keys
  conflictQueryKeys,
  // List hooks
  useConflicts,
  useConflict,
  useConflictsByPerson,
  useConflictsByDate,
  // Resolution hooks
  useResolutionSuggestions,
  useApplyResolution,
  useUpdateConflictStatus,
  useCreateOverride,
  useResolveManually,
  // Batch hooks
  useBatchResolve,
  useBatchIgnore,
  // History hooks
  useConflictHistory,
  useConflictPatterns,
  // Statistics hooks
  useConflictStatistics,
  // Detection hooks
  useDetectConflicts,
  useValidateAssignment,
} from './hooks';

export type { ConflictListResponse } from './hooks';

// ============================================================================
// Types
// ============================================================================

export type {
  // Core types
  Conflict,
  ConflictSeverity,
  ConflictType,
  ConflictStatus,
  ConflictDetails,
  // Resolution types
  ResolutionMethod,
  ResolutionSuggestion,
  ResolutionChange,
  // Override types
  ManualOverride,
  // History types
  ConflictHistoryEntry,
  ConflictPattern,
  // Batch types
  BatchResolutionRequest,
  BatchResolutionResult,
  // Filter and sort types
  ConflictFilters,
  ConflictSortOptions,
  ConflictSortField,
  SortDirection,
  // Statistics
  ConflictStatistics,
  // Detail types
  SchedulingOverlapDetails,
  ACGMEViolationDetails,
  SupervisionMissingDetails,
  CapacityExceededDetails,
  AbsenceConflictDetails,
  QualificationMismatchDetails,
  CoverageGapDetails,
} from './types';
