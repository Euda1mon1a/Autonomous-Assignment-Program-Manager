/**
 * Admin Scheduling Hooks
 *
 * React Query hooks for the admin scheduling laboratory interface.
 * Provides data fetching and mutations for run configuration,
 * experimentation, metrics, and manual overrides.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, post, put, del, ApiError } from '@/lib/api';
import type {
  RunConfiguration,
  RunResult,
  RunLogEntry,
  RunLogFilters,
  ScheduleRunsResponse,
  RunComparisonResponse,
  ValidationResponse,
  LockedAssignment,
  EmergencyHoliday,
  RollbackPoint,
  RevertRequest,
  ExperimentRun,
  RunQueue,
  ConstraintConfig,
  ScenarioPreset,
  MetricsTrend,
  SyncMetadata,
} from '@/types/admin-scheduling';

// ============================================================================
// Query Keys
// ============================================================================

export const adminSchedulingKeys = {
  runs: (filters?: RunLogFilters) => ['admin-scheduling', 'runs', filters] as const,
  run: (id: string) => ['admin-scheduling', 'run', id] as const,
  comparison: (runAId: string, runBId: string) => ['admin-scheduling', 'comparison', runAId, runBId] as const,
  constraints: () => ['admin-scheduling', 'constraints'] as const,
  scenarios: () => ['admin-scheduling', 'scenarios'] as const,
  queue: () => ['admin-scheduling', 'queue'] as const,
  metrics: (dateRange?: { start: string; end: string }) => ['admin-scheduling', 'metrics', dateRange] as const,
  metricsTrends: (metric: string) => ['admin-scheduling', 'metrics-trends', metric] as const,
  lockedAssignments: () => ['admin-scheduling', 'locked-assignments'] as const,
  holidays: () => ['admin-scheduling', 'holidays'] as const,
  rollbackPoints: () => ['admin-scheduling', 'rollback-points'] as const,
  syncMetadata: () => ['admin-scheduling', 'sync-metadata'] as const,
  validation: (config: RunConfiguration) => ['admin-scheduling', 'validation', config] as const,
};

// ============================================================================
// Run History Hooks
// ============================================================================

/**
 * Fetches schedule run history with optional filtering.
 */
export function useScheduleRuns(filters?: RunLogFilters) {
  return useQuery<ScheduleRunsResponse, ApiError>({
    queryKey: adminSchedulingKeys.runs(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.runId) params.set('run_id', filters.runId);
      if (filters?.algorithms?.length) params.set('algorithms', filters.algorithms.join(','));
      if (filters?.dateRange?.start) params.set('start_date', filters.dateRange.start);
      if (filters?.dateRange?.end) params.set('end_date', filters.dateRange.end);
      if (filters?.status?.length) params.set('status', filters.status.join(','));
      if (filters?.tags?.length) params.set('tags', filters.tags.join(','));

      const queryString = params.toString();
      return get<ScheduleRunsResponse>(`/schedule/runs${queryString ? `?${queryString}` : ''}`);
    },
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Fetches a single schedule run by ID.
 */
export function useScheduleRun(id: string) {
  return useQuery<RunLogEntry, ApiError>({
    queryKey: adminSchedulingKeys.run(id),
    queryFn: () => get<RunLogEntry>(`/schedule/runs/${id}`),
    enabled: !!id,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Compares two schedule runs side-by-side.
 */
export function useRunComparison(runAId: string, runBId: string) {
  return useQuery<RunComparisonResponse, ApiError>({
    queryKey: adminSchedulingKeys.comparison(runAId, runBId),
    queryFn: () => get<RunComparisonResponse>(`/schedule/runs/compare?run_a=${runAId}&run_b=${runBId}`),
    enabled: !!runAId && !!runBId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// ============================================================================
// Configuration Hooks
// ============================================================================

/**
 * Fetches available constraint configurations.
 */
export function useConstraintConfigs() {
  return useQuery<ConstraintConfig[], ApiError>({
    queryKey: adminSchedulingKeys.constraints(),
    queryFn: () => get<ConstraintConfig[]>('/schedule/constraints'),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Validates a run configuration before execution.
 */
export function useValidateConfiguration() {
  return useMutation<ValidationResponse, ApiError, RunConfiguration>({
    mutationFn: (config) => post<ValidationResponse>('/schedule/validate-config', config),
  });
}

/**
 * Triggers a schedule generation run.
 */
export function useGenerateScheduleRun() {
  const queryClient = useQueryClient();

  return useMutation<RunResult, ApiError, RunConfiguration>({
    mutationFn: (config) => post<RunResult>('/schedule/generate', {
      start_date: getBlockStartDate(config.blockRange.start, config.academicYear),
      end_date: getBlockEndDate(config.blockRange.end, config.academicYear),
      algorithm: config.algorithm,
      timeout_seconds: config.timeoutSeconds,
      dry_run: config.dryRun,
      preserve_fmit: config.preserveFMIT,
      nf_post_call: config.nfPostCallEnabled,
      constraint_ids: config.constraints.filter(c => c.enabled).map(c => c.id),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-scheduling', 'runs'] });
      queryClient.invalidateQueries({ queryKey: ['admin-scheduling', 'queue'] });
      queryClient.invalidateQueries({ queryKey: ['admin-scheduling', 'metrics'] });
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      queryClient.invalidateQueries({ queryKey: ['validation'] });
    },
  });
}

// ============================================================================
// Experimentation Hooks
// ============================================================================

/**
 * Fetches available scenario presets.
 */
export function useScenarioPresets() {
  return useQuery<ScenarioPreset[], ApiError>({
    queryKey: adminSchedulingKeys.scenarios(),
    queryFn: () => get<ScenarioPreset[]>('/schedule/scenarios'),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Fetches the current run queue.
 */
export function useRunQueue() {
  return useQuery<RunQueue, ApiError>({
    queryKey: adminSchedulingKeys.queue(),
    queryFn: () => get<RunQueue>('/schedule/queue'),
    staleTime: 5 * 1000, // 5 seconds - refresh frequently
    refetchInterval: 5 * 1000, // Auto-refresh every 5 seconds
  });
}

/**
 * Queues multiple experiment runs (permutation runner).
 */
export function useQueueExperiments() {
  const queryClient = useQueryClient();

  return useMutation<ExperimentRun[], ApiError, RunConfiguration[]>({
    mutationFn: (configs) => post<ExperimentRun[]>('/schedule/queue/batch', { configurations: configs }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminSchedulingKeys.queue() });
    },
  });
}

/**
 * Cancels a queued or running experiment.
 */
export function useCancelExperiment() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: (runId) => del(`/schedule/queue/${runId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminSchedulingKeys.queue() });
    },
  });
}

// ============================================================================
// Metrics Hooks
// ============================================================================

/**
 * Fetches metrics summary for a date range.
 */
export function useScheduleMetrics(dateRange?: { start: string; end: string }) {
  return useQuery<RunResult, ApiError>({
    queryKey: adminSchedulingKeys.metrics(dateRange),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (dateRange?.start) params.set('start_date', dateRange.start);
      if (dateRange?.end) params.set('end_date', dateRange.end);
      const queryString = params.toString();
      return get<RunResult>(`/schedule/metrics${queryString ? `?${queryString}` : ''}`);
    },
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Fetches trend data for a specific metric.
 */
export function useMetricsTrend(metric: string) {
  return useQuery<MetricsTrend, ApiError>({
    queryKey: adminSchedulingKeys.metricsTrends(metric),
    queryFn: () => get<MetricsTrend>(`/schedule/metrics/trends/${metric}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!metric,
  });
}

// ============================================================================
// Manual Override Hooks
// ============================================================================

/**
 * Fetches all locked assignments.
 */
export function useLockedAssignments() {
  return useQuery<LockedAssignment[], ApiError>({
    queryKey: adminSchedulingKeys.lockedAssignments(),
    queryFn: () => get<LockedAssignment[]>('/schedule/locks'),
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Locks an assignment to prevent changes.
 */
export function useLockAssignment() {
  const queryClient = useQueryClient();

  return useMutation<LockedAssignment, ApiError, { assignmentId: string; reason: string; expiresAt?: string }>({
    mutationFn: (data) => post<LockedAssignment>('/schedule/locks', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminSchedulingKeys.lockedAssignments() });
    },
  });
}

/**
 * Unlocks a locked assignment.
 */
export function useUnlockAssignment() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: (lockId) => del(`/schedule/locks/${lockId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminSchedulingKeys.lockedAssignments() });
    },
  });
}

/**
 * Fetches emergency holidays.
 */
export function useEmergencyHolidays() {
  return useQuery<EmergencyHoliday[], ApiError>({
    queryKey: adminSchedulingKeys.holidays(),
    queryFn: () => get<EmergencyHoliday[]>('/schedule/holidays'),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Creates an emergency holiday.
 */
export function useCreateEmergencyHoliday() {
  const queryClient = useQueryClient();

  return useMutation<EmergencyHoliday, ApiError, Omit<EmergencyHoliday, 'id' | 'createdAt' | 'createdBy'>>({
    mutationFn: (data) => post<EmergencyHoliday>('/schedule/holidays', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminSchedulingKeys.holidays() });
    },
  });
}

/**
 * Deletes an emergency holiday.
 */
export function useDeleteEmergencyHoliday() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: (holidayId) => del(`/schedule/holidays/${holidayId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminSchedulingKeys.holidays() });
    },
  });
}

/**
 * Fetches available rollback points.
 */
export function useRollbackPoints() {
  return useQuery<RollbackPoint[], ApiError>({
    queryKey: adminSchedulingKeys.rollbackPoints(),
    queryFn: () => get<RollbackPoint[]>('/schedule/rollback-points'),
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Creates a rollback point (snapshot).
 */
export function useCreateRollbackPoint() {
  const queryClient = useQueryClient();

  return useMutation<RollbackPoint, ApiError, { description: string }>({
    mutationFn: (data) => post<RollbackPoint>('/schedule/rollback-points', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminSchedulingKeys.rollbackPoints() });
    },
  });
}

/**
 * Reverts to a rollback point.
 */
export function useRevertToRollbackPoint() {
  const queryClient = useQueryClient();

  return useMutation<{ assignmentsReverted: number }, ApiError, RevertRequest>({
    mutationFn: (request) => post<{ assignmentsReverted: number }>(`/schedule/rollback-points/${request.rollbackPointId}/revert`, {
      reason: request.reason,
      dry_run: request.dryRun,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-scheduling'] });
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
    },
  });
}

// ============================================================================
// Data Provenance Hooks
// ============================================================================

/**
 * Fetches sync metadata.
 */
export function useSyncMetadata() {
  return useQuery<SyncMetadata, ApiError>({
    queryKey: adminSchedulingKeys.syncMetadata(),
    queryFn: () => get<SyncMetadata>('/schedule/sync-metadata'),
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Triggers a sync operation.
 */
export function useTriggerSync() {
  const queryClient = useQueryClient();

  return useMutation<SyncMetadata, ApiError, void>({
    mutationFn: () => post<SyncMetadata>('/schedule/sync', {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminSchedulingKeys.syncMetadata() });
    },
  });
}

/**
 * Performs seed data cleanup.
 */
export function useSeedCleanup() {
  const queryClient = useQueryClient();

  return useMutation<{ recordsCleaned: number }, ApiError, { mode: 'soft' | 'hard' }>({
    mutationFn: (data) => post<{ recordsCleaned: number }>('/schedule/seed-cleanup', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-scheduling'] });
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
    },
  });
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Converts a block number to a start date for a given academic year.
 */
function getBlockStartDate(blockNumber: number, academicYear: string): string {
  const [startYear] = academicYear.split('-').map(Number);
  const baseDate = new Date(startYear, 6, 1); // July 1st
  const daysOffset = (blockNumber - 1) * 0.5; // Each block is half a day
  baseDate.setDate(baseDate.getDate() + Math.floor(daysOffset));
  return baseDate.toISOString().split('T')[0];
}

/**
 * Converts a block number to an end date for a given academic year.
 */
function getBlockEndDate(blockNumber: number, academicYear: string): string {
  const [startYear] = academicYear.split('-').map(Number);
  const baseDate = new Date(startYear, 6, 1); // July 1st
  const daysOffset = blockNumber * 0.5; // Each block is half a day
  baseDate.setDate(baseDate.getDate() + Math.floor(daysOffset));
  return baseDate.toISOString().split('T')[0];
}
