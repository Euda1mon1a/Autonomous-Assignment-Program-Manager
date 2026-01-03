/**
 * Conflict Resolution Hooks
 *
 * React Query hooks for conflict detection, resolution, and management.
 * Provides data fetching, mutations, and caching for the conflict UI.
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { get, post, put, ApiError } from '@/lib/api';
import type {
  Conflict,
  ConflictFilters,
  ConflictSortOptions,
  ConflictStatistics,
  ConflictHistoryEntry,
  ConflictPattern,
  ResolutionSuggestion,
  ManualOverride,
  BatchResolutionRequest,
  BatchResolutionResult,
  ConflictStatus,
  ResolutionMethod,
} from './types';

// ============================================================================
// Query Keys
// ============================================================================

export const conflictQueryKeys = {
  all: ['conflicts'] as const,
  list: (filters?: ConflictFilters, sort?: ConflictSortOptions) =>
    ['conflicts', 'list', filters, sort] as const,
  detail: (id: string) => ['conflicts', 'detail', id] as const,
  suggestions: (id: string) => ['conflicts', 'suggestions', id] as const,
  history: (id: string) => ['conflicts', 'history', id] as const,
  statistics: (dateRange?: { start: string; end: string }) =>
    ['conflicts', 'statistics', dateRange] as const,
  patterns: () => ['conflicts', 'patterns'] as const,
  byPerson: (personId: string) => ['conflicts', 'person', personId] as const,
  byDate: (date: string) => ['conflicts', 'date', date] as const,
};

// ============================================================================
// Response Types
// ============================================================================

export interface ConflictListResponse {
  items: Conflict[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ============================================================================
// Conflict List Hooks
// ============================================================================

/**
 * Fetch list of conflicts with optional filtering and sorting
 */
export function useConflicts(
  filters?: ConflictFilters,
  sort?: ConflictSortOptions,
  options?: Omit<UseQueryOptions<ConflictListResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams();

  if (filters?.types?.length) {
    params.set('types', filters.types.join(','));
  }
  if (filters?.severities?.length) {
    params.set('severities', filters.severities.join(','));
  }
  if (filters?.statuses?.length) {
    params.set('statuses', filters.statuses.join(','));
  }
  if (filters?.person_ids?.length) {
    params.set('person_ids', filters.person_ids.join(','));
  }
  if (filters?.date_range) {
    params.set('start_date', filters.date_range.start);
    params.set('end_date', filters.date_range.end);
  }
  if (filters?.search) {
    params.set('search', filters.search);
  }
  if (sort) {
    params.set('sort_by', sort.field);
    params.set('sort_dir', sort.direction);
  }

  const queryString = params.toString();

  return useQuery<ConflictListResponse, ApiError>({
    queryKey: conflictQueryKeys.list(filters, sort),
    queryFn: () =>
      get<ConflictListResponse>(`/conflicts${queryString ? `?${queryString}` : ''}`),
    staleTime: 30 * 1000, // 30 seconds - conflicts change frequently
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
    ...options,
  });
}

/**
 * Fetch a single conflict by ID
 */
export function useConflict(
  id: string,
  options?: Omit<UseQueryOptions<Conflict, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Conflict, ApiError>({
    queryKey: conflictQueryKeys.detail(id),
    queryFn: () => get<Conflict>(`/conflicts/${id}`),
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
    enabled: !!id,
    ...options,
  });
}

/**
 * Fetch conflicts for a specific person
 */
export function useConflictsByPerson(
  personId: string,
  options?: Omit<UseQueryOptions<ConflictListResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ConflictListResponse, ApiError>({
    queryKey: conflictQueryKeys.byPerson(personId),
    queryFn: () => get<ConflictListResponse>(`/conflicts?person_ids=${personId}`),
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
    enabled: !!personId,
    ...options,
  });
}

/**
 * Fetch conflicts for a specific date
 */
export function useConflictsByDate(
  date: string,
  options?: Omit<UseQueryOptions<ConflictListResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ConflictListResponse, ApiError>({
    queryKey: conflictQueryKeys.byDate(date),
    queryFn: () =>
      get<ConflictListResponse>(`/conflicts?start_date=${date}&end_date=${date}`),
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
    enabled: !!date,
    ...options,
  });
}

// ============================================================================
// Resolution Suggestion Hooks
// ============================================================================

/**
 * Fetch resolution suggestions for a conflict
 */
export function useResolutionSuggestions(
  conflictId: string,
  options?: Omit<UseQueryOptions<ResolutionSuggestion[], ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ResolutionSuggestion[], ApiError>({
    queryKey: conflictQueryKeys.suggestions(conflictId),
    queryFn: () => get<ResolutionSuggestion[]>(`/conflicts/${conflictId}/suggestions`),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000,
    enabled: !!conflictId,
    ...options,
  });
}

/**
 * Apply a resolution suggestion
 */
export function useApplyResolution() {
  const queryClient = useQueryClient();

  return useMutation<
    Conflict,
    ApiError,
    { conflictId: string; suggestionId: string; notes?: string }
  >({
    mutationFn: ({ conflictId, suggestionId, notes }) =>
      post<Conflict>(`/conflicts/${conflictId}/resolve`, {
        suggestion_id: suggestionId,
        notes,
      }),
    onSuccess: (data, { conflictId }) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: conflictQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: conflictQueryKeys.detail(conflictId) });
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
      queryClient.invalidateQueries({ queryKey: ['validation'] });
    },
  });
}

// ============================================================================
// Manual Resolution Hooks
// ============================================================================

/**
 * Update conflict status
 */
export function useUpdateConflictStatus() {
  const queryClient = useQueryClient();

  return useMutation<
    Conflict,
    ApiError,
    { conflictId: string; status: ConflictStatus; notes?: string }
  >({
    mutationFn: ({ conflictId, status, notes }) =>
      put<Conflict>(`/conflicts/${conflictId}/status`, { status, notes }),
    onSuccess: (data, { conflictId }) => {
      queryClient.invalidateQueries({ queryKey: conflictQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: conflictQueryKeys.detail(conflictId) });
    },
  });
}

/**
 * Create a manual override for a conflict
 */
export function useCreateOverride() {
  const queryClient = useQueryClient();

  return useMutation<Conflict, ApiError, ManualOverride>({
    mutationFn: (override) =>
      post<Conflict>(`/conflicts/${override.conflict_id}/override`, override),
    onSuccess: (data, { conflict_id }) => {
      queryClient.invalidateQueries({ queryKey: conflictQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: conflictQueryKeys.detail(conflict_id) });
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      queryClient.invalidateQueries({ queryKey: ['validation'] });
    },
  });
}

/**
 * Resolve a conflict manually
 */
export function useResolveManually() {
  const queryClient = useQueryClient();

  return useMutation<
    Conflict,
    ApiError,
    {
      conflictId: string;
      method: ResolutionMethod;
      changes: Array<{
        type: 'reassign' | 'remove' | 'add' | 'modify';
        entity_type: string;
        entity_id: string;
        data?: Record<string, unknown>;
      }>;
      notes?: string;
    }
  >({
    mutationFn: ({ conflictId, method, changes, notes }) =>
      post<Conflict>(`/conflicts/${conflictId}/resolve-manual`, {
        method,
        changes,
        notes,
      }),
    onSuccess: (data, { conflictId }) => {
      queryClient.invalidateQueries({ queryKey: conflictQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: conflictQueryKeys.detail(conflictId) });
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
      queryClient.invalidateQueries({ queryKey: ['validation'] });
    },
  });
}

// ============================================================================
// Batch Resolution Hooks
// ============================================================================

/**
 * Resolve multiple conflicts at once
 */
export function useBatchResolve() {
  const queryClient = useQueryClient();

  return useMutation<BatchResolutionResult, ApiError, BatchResolutionRequest>({
    mutationFn: (request) => post<BatchResolutionResult>('/conflicts/batch-resolve', request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: conflictQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
      queryClient.invalidateQueries({ queryKey: ['validation'] });
    },
  });
}

/**
 * Ignore multiple conflicts
 */
export function useBatchIgnore() {
  const queryClient = useQueryClient();

  return useMutation<
    { success: number; failed: number },
    ApiError,
    { conflictIds: string[]; reason: string }
  >({
    mutationFn: ({ conflictIds, reason }) =>
      post<{ success: number; failed: number }>('/conflicts/batch-ignore', {
        conflict_ids: conflictIds,
        reason,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: conflictQueryKeys.all });
    },
  });
}

// ============================================================================
// History Hooks
// ============================================================================

/**
 * Fetch history for a specific conflict
 */
export function useConflictHistory(
  conflictId: string,
  options?: Omit<UseQueryOptions<ConflictHistoryEntry[], ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ConflictHistoryEntry[], ApiError>({
    queryKey: conflictQueryKeys.history(conflictId),
    queryFn: () => get<ConflictHistoryEntry[]>(`/conflicts/${conflictId}/history`),
    staleTime: 60 * 1000,
    gcTime: 5 * 60 * 1000,
    enabled: !!conflictId,
    ...options,
  });
}

/**
 * Fetch conflict patterns (recurring issues)
 */
export function useConflictPatterns(
  options?: Omit<UseQueryOptions<ConflictPattern[], ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ConflictPattern[], ApiError>({
    queryKey: conflictQueryKeys.patterns(),
    queryFn: () => get<ConflictPattern[]>('/conflicts/patterns'),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000,
    ...options,
  });
}

// ============================================================================
// Statistics Hooks
// ============================================================================

/**
 * Fetch conflict statistics
 */
export function useConflictStatistics(
  dateRange?: { start: string; end: string },
  options?: Omit<UseQueryOptions<ConflictStatistics, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams();
  if (dateRange) {
    params.set('start_date', dateRange.start);
    params.set('end_date', dateRange.end);
  }
  const queryString = params.toString();

  return useQuery<ConflictStatistics, ApiError>({
    queryKey: conflictQueryKeys.statistics(dateRange),
    queryFn: () =>
      get<ConflictStatistics>(`/conflicts/statistics${queryString ? `?${queryString}` : ''}`),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000,
    ...options,
  });
}

// ============================================================================
// Conflict Detection Hooks
// ============================================================================

/**
 * Trigger conflict detection for a date range
 */
export function useDetectConflicts() {
  const queryClient = useQueryClient();

  return useMutation<
    { detected: number; new_conflicts: number },
    ApiError,
    { start_date: string; end_date: string }
  >({
    mutationFn: (params) => post<{ detected: number; new_conflicts: number }>(
      '/conflicts/detect',
      params
    ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: conflictQueryKeys.all });
    },
  });
}

/**
 * Validate and detect conflicts for a specific assignment
 */
export function useValidateAssignment() {
  return useMutation<
    { conflicts: Conflict[]; warnings: string[] },
    ApiError,
    {
      person_id: string;
      block_id: string;
      rotation_template_id?: string;
      role: string;
    }
  >({
    mutationFn: (assignment) =>
      post<{ conflicts: Conflict[]; warnings: string[] }>(
        '/conflicts/validate-assignment',
        assignment
      ),
  });
}
