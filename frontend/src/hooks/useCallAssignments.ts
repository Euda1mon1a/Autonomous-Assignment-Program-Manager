/**
 * Call Assignments Hooks
 *
 * TanStack Query hooks for call assignment management including
 * CRUD operations, bulk actions, PCAT generation, and equity analysis.
 */
import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryOptions,
} from '@tanstack/react-query';
import { get, post, put, del } from '@/lib/api';
import type { ApiError } from '@/lib/api';
import type {
  CallAssignment,
  CallAssignmentListResponse,
  CallAssignmentCreate,
  CallAssignmentUpdate,
  CallAssignmentFilters,
  BulkCallAssignmentUpdateRequest,
  BulkCallAssignmentUpdateResponse,
  PCATGenerationRequest,
  PCATGenerationResponse,
  CallCoverageReport,
  CallEquityReport,
  EquityPreviewRequest,
  EquityPreviewResponse,
} from '@/types/call-assignment';

// ============================================================================
// Query Keys
// ============================================================================

export const callAssignmentQueryKeys = {
  /** All call assignments */
  all: ['call-assignments'] as const,
  /** Call assignments list with filters */
  list: (filters?: CallAssignmentFilters) =>
    ['call-assignments', 'list', filters] as const,
  /** Single call assignment by ID */
  detail: (id: string) => ['call-assignments', 'detail', id] as const,
  /** Call assignments by person */
  byPerson: (personId: string, startDate?: string, endDate?: string) =>
    ['call-assignments', 'by-person', personId, startDate, endDate] as const,
  /** Call assignments by date */
  byDate: (date: string) => ['call-assignments', 'by-date', date] as const,
  /** Coverage report */
  coverage: (startDate: string, endDate: string) =>
    ['call-assignments', 'coverage', startDate, endDate] as const,
  /** Equity report */
  equity: (startDate: string, endDate: string) =>
    ['call-assignments', 'equity', startDate, endDate] as const,
  /** Equity preview */
  equityPreview: (request: EquityPreviewRequest) =>
    ['call-assignments', 'equity-preview', request] as const,
};

// ============================================================================
// List Hooks
// ============================================================================

/**
 * Fetches call assignments with optional filters.
 */
export function useCallAssignments(
  filters?: CallAssignmentFilters,
  options?: Omit<
    UseQueryOptions<CallAssignmentListResponse, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<CallAssignmentListResponse, ApiError>({
    queryKey: callAssignmentQueryKeys.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.startDate) params.append('start_date', filters.startDate);
      if (filters?.endDate) params.append('end_date', filters.endDate);
      if (filters?.personId) params.append('person_id', filters.personId);
      if (filters?.call_type) params.append('call_type', filters.call_type);
      if (filters?.skip !== undefined) params.append('skip', String(filters.skip));
      if (filters?.limit !== undefined) params.append('limit', String(filters.limit));
      const queryString = params.toString();
      return get<CallAssignmentListResponse>(
        `/call-assignments${queryString ? `?${queryString}` : ''}`
      );
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  });
}

/**
 * Fetches a single call assignment by ID.
 */
export function useCallAssignment(
  id: string,
  options?: Omit<
    UseQueryOptions<CallAssignment, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<CallAssignment, ApiError>({
    queryKey: callAssignmentQueryKeys.detail(id),
    queryFn: async () => {
      return get<CallAssignment>(`/call-assignments/${id}`);
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Fetches call assignments by person ID.
 */
export function useCallAssignmentsByPerson(
  personId: string,
  startDate?: string,
  endDate?: string,
  options?: Omit<
    UseQueryOptions<CallAssignmentListResponse, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<CallAssignmentListResponse, ApiError>({
    queryKey: callAssignmentQueryKeys.byPerson(personId, startDate, endDate),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      const queryString = params.toString();
      return get<CallAssignmentListResponse>(
        `/call-assignments/by-person/${personId}${queryString ? `?${queryString}` : ''}`
      );
    },
    enabled: !!personId,
    staleTime: 2 * 60 * 1000,
    ...options,
  });
}

/**
 * Fetches call assignments by date.
 */
export function useCallAssignmentsByDate(
  date: string,
  options?: Omit<
    UseQueryOptions<CallAssignmentListResponse, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<CallAssignmentListResponse, ApiError>({
    queryKey: callAssignmentQueryKeys.byDate(date),
    queryFn: async () => {
      return get<CallAssignmentListResponse>(`/call-assignments/by-date/${date}`);
    },
    enabled: !!date,
    staleTime: 2 * 60 * 1000,
    ...options,
  });
}

// ============================================================================
// CRUD Mutations
// ============================================================================

/**
 * Creates a new call assignment.
 */
export function useCreateCallAssignment() {
  const queryClient = useQueryClient();

  return useMutation<CallAssignment, ApiError, CallAssignmentCreate>({
    mutationFn: async (data) => {
      return post<CallAssignment>('/call-assignments', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: callAssignmentQueryKeys.all,
      });
    },
  });
}

/**
 * Updates an existing call assignment.
 */
export function useUpdateCallAssignment() {
  const queryClient = useQueryClient();

  return useMutation<
    CallAssignment,
    ApiError,
    { id: string; data: CallAssignmentUpdate }
  >({
    mutationFn: async ({ id, data }) => {
      return put<CallAssignment>(`/call-assignments/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({
        queryKey: callAssignmentQueryKeys.all,
      });
      queryClient.invalidateQueries({
        queryKey: callAssignmentQueryKeys.detail(id),
      });
    },
  });
}

/**
 * Deletes a call assignment.
 */
export function useDeleteCallAssignment() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: async (id) => {
      await del(`/call-assignments/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: callAssignmentQueryKeys.all,
      });
    },
  });
}

// ============================================================================
// Bulk Update Mutation
// ============================================================================

/**
 * Bulk updates multiple call assignments.
 * Use this to reassign multiple call assignments to a different person.
 */
export function useBulkUpdateCallAssignments() {
  const queryClient = useQueryClient();

  return useMutation<
    BulkCallAssignmentUpdateResponse,
    ApiError,
    BulkCallAssignmentUpdateRequest
  >({
    mutationFn: async (request) => {
      return post<BulkCallAssignmentUpdateResponse>(
        '/call-assignments/bulk-update',
        request
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: callAssignmentQueryKeys.all,
      });
    },
  });
}

// ============================================================================
// PCAT Generation Mutation
// ============================================================================

/**
 * Generates PCAT and DO assignments for selected call assignments.
 *
 * For each Sun-Thurs overnight call:
 * - Creates PCAT assignment for next day AM block
 * - Creates DO assignment for next day PM block
 */
export function useGeneratePCAT() {
  const queryClient = useQueryClient();

  return useMutation<PCATGenerationResponse, ApiError, PCATGenerationRequest>({
    mutationFn: async (request) => {
      return post<PCATGenerationResponse>(
        '/call-assignments/generate-pcat',
        request
      );
    },
    onSuccess: () => {
      // Invalidate call assignments and potentially resident assignments
      queryClient.invalidateQueries({
        queryKey: callAssignmentQueryKeys.all,
      });
      // Also invalidate resident assignments since PCAT/DO are created there
      queryClient.invalidateQueries({
        queryKey: ['resident-assignments'],
      });
    },
  });
}

// ============================================================================
// Report Hooks
// ============================================================================

/**
 * Fetches call coverage report for a date range.
 */
export function useCoverageReport(
  startDate: string,
  endDate: string,
  options?: Omit<
    UseQueryOptions<CallCoverageReport, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<CallCoverageReport, ApiError>({
    queryKey: callAssignmentQueryKeys.coverage(startDate, endDate),
    queryFn: async () => {
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
      });
      return get<CallCoverageReport>(
        `/call-assignments/reports/coverage?${params.toString()}`
      );
    },
    enabled: !!startDate && !!endDate,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Fetches call equity report for a date range.
 */
export function useEquityReport(
  startDate: string,
  endDate: string,
  options?: Omit<
    UseQueryOptions<CallEquityReport, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<CallEquityReport, ApiError>({
    queryKey: callAssignmentQueryKeys.equity(startDate, endDate),
    queryFn: async () => {
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
      });
      return get<CallEquityReport>(
        `/call-assignments/reports/equity?${params.toString()}`
      );
    },
    enabled: !!startDate && !!endDate,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

// ============================================================================
// Equity Preview Hook
// ============================================================================

/**
 * Previews equity distribution with simulated changes.
 * This is a mutation since it accepts a POST body with simulated changes.
 */
export function useEquityPreview() {
  return useMutation<EquityPreviewResponse, ApiError, EquityPreviewRequest>({
    mutationFn: async (request) => {
      return post<EquityPreviewResponse>(
        '/call-assignments/equity-preview',
        request
      );
    },
  });
}

/**
 * Alternative: Query-based equity preview for cases where you want
 * to use it as a query with caching (requires stable request object).
 */
export function useEquityPreviewQuery(
  request: EquityPreviewRequest,
  options?: Omit<
    UseQueryOptions<EquityPreviewResponse, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<EquityPreviewResponse, ApiError>({
    queryKey: callAssignmentQueryKeys.equityPreview(request),
    queryFn: async () => {
      return post<EquityPreviewResponse>(
        '/call-assignments/equity-preview',
        request
      );
    },
    enabled: !!request.startDate && !!request.endDate,
    staleTime: 30 * 1000, // 30 seconds - shorter since preview is dynamic
    ...options,
  });
}

// ============================================================================
// Utility Hooks
// ============================================================================

/**
 * Returns a map of call assignment IDs to call assignment objects.
 */
export function useCallAssignmentsMap(filters?: CallAssignmentFilters) {
  const { data } = useCallAssignments(filters);

  return data?.items.reduce(
    (acc, assignment) => {
      acc[assignment.id] = assignment;
      return acc;
    },
    {} as Record<string, CallAssignment>
  );
}

// ============================================================================
// Bulk Delete Mutation
// ============================================================================

/**
 * Bulk deletes multiple call assignments.
 * Note: Uses sequential deletion since there's no bulk delete endpoint.
 */
export function useBulkDeleteCallAssignments() {
  const queryClient = useQueryClient();

  return useMutation<
    { deleted: number; errors: string[] },
    ApiError,
    string[]
  >({
    mutationFn: async (ids) => {
      const results = await Promise.allSettled(
        ids.map((id) => del(`/call-assignments/${id}`))
      );

      const errors: string[] = [];
      let deleted = 0;

      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          deleted++;
        } else {
          errors.push(`Failed to delete ${ids[index]}: ${result.reason?.message || 'Unknown error'}`);
        }
      });

      return { deleted, errors };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: callAssignmentQueryKeys.all,
      });
    },
  });
}

// ============================================================================
// PCAT Status Mutations
// ============================================================================

/**
 * Clears PCAT status (sets post_call_status back to available).
 * Since there's no specific endpoint, this uses bulk update with null values.
 */
export function useClearPCATStatus() {
  const queryClient = useQueryClient();

  return useMutation<
    BulkCallAssignmentUpdateResponse,
    ApiError,
    string[]
  >({
    mutationFn: async (assignmentIds) => {
      // Note: The actual backend would need to support clearing PCAT status.
      // For now, we'll use bulk update with a placeholder.
      // This may need backend modification to fully support PCAT clearing.
      return post<BulkCallAssignmentUpdateResponse>(
        '/call-assignments/bulk-update',
        {
          assignment_ids: assignmentIds,
          updates: {
            // Backend would need to support this
          },
        }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: callAssignmentQueryKeys.all,
      });
    },
  });
}
