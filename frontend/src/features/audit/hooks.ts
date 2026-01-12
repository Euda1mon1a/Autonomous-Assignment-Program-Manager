/**
 * React Query Hooks for Audit Log Feature
 *
 * Provides data fetching, caching, and mutation hooks
 * for audit log operations.
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { get, post, ApiError } from '@/lib/api';
import type {
  AuditLogEntry,
  AuditLogResponse,
  AuditLogQueryParams,
  AuditLogFilters,
  AuditStatistics,
  AuditExportConfig,
  TimelineEvent,
  DateRange,
} from './types';
import { DEFAULT_PAGE_SIZE, DEFAULT_SORT } from './types';

// ============================================================================
// Query Keys
// ============================================================================

export const auditQueryKeys = {
  all: ['audit'] as const,
  logs: (params?: AuditLogQueryParams) => ['audit', 'logs', params] as const,
  log: (id: string) => ['audit', 'logs', id] as const,
  statistics: (dateRange?: DateRange) => ['audit', 'statistics', dateRange] as const,
  timeline: (params?: AuditLogFilters) => ['audit', 'timeline', params] as const,
  entityHistory: (entityType: string, entityId: string) =>
    ['audit', 'entity-history', entityType, entityId] as const,
  userActivity: (userId: string, dateRange?: DateRange) =>
    ['audit', 'user-activity', userId, dateRange] as const,
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Build query string from filters
 */
function buildQueryString(params?: AuditLogQueryParams): string {
  if (!params) return '';

  const queryParams = new URLSearchParams();

  // Pagination
  const pagination = params.pagination || { page: 1, pageSize: DEFAULT_PAGE_SIZE };
  queryParams.set('page', String(pagination.page));
  queryParams.set('pageSize', String(pagination.pageSize));

  // Sort
  const sort = params.sort || DEFAULT_SORT;
  queryParams.set('sort_by', sort.field);
  queryParams.set('sort_direction', sort.direction);

  // Filters
  if (params.filters) {
    const { filters } = params;

    if (filters.dateRange?.start) {
      queryParams.set('startDate', filters.dateRange.start);
    }
    if (filters.dateRange?.end) {
      queryParams.set('endDate', filters.dateRange.end);
    }
    if (filters.entityTypes?.length) {
      queryParams.set('entityTypes', filters.entityTypes.join(','));
    }
    if (filters.actions?.length) {
      queryParams.set('actions', filters.actions.join(','));
    }
    if (filters.userIds?.length) {
      queryParams.set('userIds', filters.userIds.join(','));
    }
    if (filters.severity?.length) {
      queryParams.set('severity', filters.severity.join(','));
    }
    if (filters.searchQuery) {
      queryParams.set('search', filters.searchQuery);
    }
    if (filters.entityId) {
      queryParams.set('entityId', filters.entityId);
    }
    if (filters.acgmeOverridesOnly) {
      queryParams.set('acgme_overrides_only', 'true');
    }
  }

  return queryParams.toString();
}

/**
 * Transform API response to timeline events
 */
function transformToTimelineEvents(logs: AuditLogEntry[]): TimelineEvent[] {
  return logs.map((log) => ({
    id: log.id,
    timestamp: log.timestamp,
    title: `${log.entityName || log.entityType} ${log.action}`,
    description: log.reason || getActionDescription(log),
    entityType: log.entityType,
    action: log.action,
    severity: log.severity,
    user: log.user,
  }));
}

/**
 * Generate action description from audit entry
 */
function getActionDescription(log: AuditLogEntry): string {
  const changesCount = log.changes?.length || 0;

  switch (log.action) {
    case 'create':
      return `Created new ${log.entityType}`;
    case 'update':
      return `Updated ${changesCount} field${changesCount !== 1 ? 's' : ''}`;
    case 'delete':
      return `Deleted ${log.entityType}`;
    case 'override':
      return log.acgmeJustification || 'ACGME rule override';
    case 'scheduleGenerate':
      return 'Generated schedule';
    case 'bulkImport':
      return `Imported ${log.metadata?.count || 'multiple'} records`;
    default:
      return log.action.replace(/_/g, ' ');
  }
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetch paginated audit logs with filters
 */
export function useAuditLogs(
  params?: AuditLogQueryParams,
  options?: Omit<UseQueryOptions<AuditLogResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  const queryString = buildQueryString(params);

  return useQuery<AuditLogResponse, ApiError>({
    queryKey: auditQueryKeys.logs(params),
    queryFn: () => get<AuditLogResponse>(`/audit/logs${queryString ? `?${queryString}` : ''}`),
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Fetch single audit log entry by ID
 */
export function useAuditLogEntry(
  id: string,
  options?: Omit<UseQueryOptions<AuditLogEntry, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AuditLogEntry, ApiError>({
    queryKey: auditQueryKeys.log(id),
    queryFn: () => get<AuditLogEntry>(`/audit/logs/${id}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!id,
    ...options,
  });
}

/**
 * Fetch audit statistics
 */
export function useAuditStatistics(
  dateRange?: DateRange,
  options?: Omit<UseQueryOptions<AuditStatistics, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams();
  if (dateRange?.start) params.set('startDate', dateRange.start);
  if (dateRange?.end) params.set('endDate', dateRange.end);
  const queryString = params.toString();

  return useQuery<AuditStatistics, ApiError>({
    queryKey: auditQueryKeys.statistics(dateRange),
    queryFn: () => get<AuditStatistics>(`/audit/statistics${queryString ? `?${queryString}` : ''}`),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  });
}

/**
 * Fetch timeline events with filtering
 */
export function useAuditTimeline(
  filters?: AuditLogFilters,
  options?: Omit<UseQueryOptions<TimelineEvent[], ApiError>, 'queryKey' | 'queryFn'>
) {
  const params: AuditLogQueryParams = {
    filters,
    pagination: { page: 1, pageSize: 100 }, // Timeline shows more items
    sort: { field: 'timestamp', direction: 'desc' },
  };
  const queryString = buildQueryString(params);

  return useQuery<TimelineEvent[], ApiError>({
    queryKey: auditQueryKeys.timeline(filters),
    queryFn: async () => {
      const response = await get<AuditLogResponse>(`/audit/logs${queryString ? `?${queryString}` : ''}`);
      return transformToTimelineEvents(response.items);
    },
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Fetch audit history for a specific entity
 */
export function useEntityAuditHistory(
  entityType: string,
  entityId: string,
  options?: Omit<UseQueryOptions<AuditLogEntry[], ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AuditLogEntry[], ApiError>({
    queryKey: auditQueryKeys.entityHistory(entityType, entityId),
    queryFn: async () => {
      const response = await get<AuditLogResponse>(
        `/audit/logs?entity_type=${entityType}&entity_id=${entityId}&sort_by=timestamp&sort_direction=desc`
      );
      return response.items;
    },
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!entityType && !!entityId,
    ...options,
  });
}

/**
 * Fetch user activity audit logs
 */
export function useUserAuditActivity(
  userId: string,
  dateRange?: DateRange,
  options?: Omit<UseQueryOptions<AuditLogEntry[], ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams();
  params.set('userIds', userId);
  if (dateRange?.start) params.set('startDate', dateRange.start);
  if (dateRange?.end) params.set('endDate', dateRange.end);
  params.set('sort_by', 'timestamp');
  params.set('sort_direction', 'desc');

  return useQuery<AuditLogEntry[], ApiError>({
    queryKey: auditQueryKeys.userActivity(userId, dateRange),
    queryFn: async () => {
      const response = await get<AuditLogResponse>(`/audit/logs?${params.toString()}`);
      return response.items;
    },
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!userId,
    ...options,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Export audit logs
 */
export function useExportAuditLogs() {
  return useMutation<Blob, ApiError, AuditExportConfig>({
    mutationFn: async (config) => {
      const response = await post<Blob>('/audit/export', config, {
        responseType: 'blob',
      });
      return response;
    },
  });
}

/**
 * Mark audit entries as reviewed (for ACGME compliance tracking)
 */
export function useMarkAuditReviewed() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, { ids: string[]; reviewedBy: string; notes?: string }>({
    mutationFn: async ({ ids, reviewedBy, notes }) => {
      await post('/audit/mark-reviewed', { ids, reviewedBy: reviewedBy, notes });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditQueryKeys.all });
    },
  });
}

// ============================================================================
// Utility Hooks
// ============================================================================

/**
 * Hook to get available users for filtering
 */
export function useAuditUsers(
  options?: Omit<UseQueryOptions<AuditUser[], ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AuditUser[], ApiError>({
    queryKey: ['audit', 'users'],
    queryFn: () => get<AuditUser[]>('/audit/users'),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

interface AuditUser {
  id: string;
  name: string;
  email?: string;
}

/**
 * Prefetch audit logs for better UX
 */
export function usePrefetchAuditLogs() {
  const queryClient = useQueryClient();

  return (params: AuditLogQueryParams) => {
    queryClient.prefetchQuery({
      queryKey: auditQueryKeys.logs(params),
      queryFn: () => {
        const queryString = buildQueryString(params);
        return get<AuditLogResponse>(`/audit/logs${queryString ? `?${queryString}` : ''}`);
      },
      staleTime: 30 * 1000,
    });
  };
}
