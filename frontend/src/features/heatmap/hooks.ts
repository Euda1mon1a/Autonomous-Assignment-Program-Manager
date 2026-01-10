/**
 * React Query Hooks for Heatmap Visualization Feature
 *
 * Provides data fetching, caching, and mutation hooks
 * for heatmap visualization operations.
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { get, post, ApiError } from '@/lib/api';
import type {
  HeatmapFilters,
  HeatmapResponse,
  CoverageHeatmapResponse,
  WorkloadHeatmapResponse,
  HeatmapExportConfig,
  DateRange,
} from './types';

// ============================================================================
// Query Keys
// ============================================================================

export const heatmapQueryKeys = {
  all: ['heatmap'] as const,
  coverage: (dateRange?: DateRange) => ['heatmap', 'coverage', dateRange] as const,
  workload: (personIds?: string[], dateRange?: DateRange) =>
    ['heatmap', 'workload', personIds, dateRange] as const,
  custom: (filters?: HeatmapFilters) => ['heatmap', 'custom', filters] as const,
  rotations: () => ['heatmap', 'rotations'] as const,
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Build query string from filters
 */
function buildQueryString(filters?: HeatmapFilters): string {
  if (!filters) return '';

  const params = new URLSearchParams();

  if (filters.startDate) {
    params.set('startDate', filters.startDate);
  }
  if (filters.endDate) {
    params.set('endDate', filters.endDate);
  }
  if (filters.personIds?.length) {
    params.set('personIds', filters.personIds.join(','));
  }
  if (filters.rotationIds?.length) {
    params.set('rotationIds', filters.rotationIds.join(','));
  }
  if (filters.includeFmit !== undefined) {
    params.set('includeFmit', String(filters.includeFmit));
  }
  if (filters.groupBy) {
    params.set('groupBy', filters.groupBy);
  }

  return params.toString();
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetch generic heatmap data with filters
 */
export function useHeatmapData(
  filters: HeatmapFilters,
  options?: Omit<UseQueryOptions<HeatmapResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  const queryString = buildQueryString(filters);

  return useQuery<HeatmapResponse, ApiError>({
    queryKey: heatmapQueryKeys.custom(filters),
    queryFn: () =>
      get<HeatmapResponse>(`/visualization/heatmap${queryString ? `?${queryString}` : ''}`),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Fetch coverage heatmap showing rotation coverage over time
 */
export function useCoverageHeatmap(
  dateRange: DateRange,
  options?: Omit<UseQueryOptions<CoverageHeatmapResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams();
  params.set('startDate', dateRange.start);
  params.set('endDate', dateRange.end);

  return useQuery<CoverageHeatmapResponse, ApiError>({
    queryKey: heatmapQueryKeys.coverage(dateRange),
    queryFn: () => get<CoverageHeatmapResponse>(`/visualization/heatmap/coverage?${params.toString()}`),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Fetch workload heatmap showing person workload distribution
 */
export function useWorkloadHeatmap(
  personIds: string[],
  dateRange: DateRange,
  options?: Omit<UseQueryOptions<WorkloadHeatmapResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams();
  params.set('startDate', dateRange.start);
  params.set('endDate', dateRange.end);
  if (personIds.length > 0) {
    params.set('personIds', personIds.join(','));
  }

  return useQuery<WorkloadHeatmapResponse, ApiError>({
    queryKey: heatmapQueryKeys.workload(personIds, dateRange),
    queryFn: () => get<WorkloadHeatmapResponse>(`/visualization/heatmap/workload?${params.toString()}`),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    enabled: personIds.length > 0, // Only fetch if person IDs are provided
    ...options,
  });
}

/**
 * Fetch rotation coverage comparison (residency vs FMIT)
 */
export function useRotationCoverageComparison(
  dateRange: DateRange,
  rotationIds?: string[],
  options?: Omit<UseQueryOptions<HeatmapResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams();
  params.set('startDate', dateRange.start);
  params.set('endDate', dateRange.end);
  if (rotationIds && rotationIds.length > 0) {
    params.set('rotationIds', rotationIds.join(','));
  }

  return useQuery<HeatmapResponse, ApiError>({
    queryKey: ['heatmap', 'rotation-comparison', dateRange, rotationIds],
    queryFn: () =>
      get<HeatmapResponse>(`/visualization/heatmap/rotation-comparison?${params.toString()}`),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Fetch available rotations for filtering
 */
export function useAvailableRotations(
  options?: Omit<UseQueryOptions<Array<{ id: string; name: string }>, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Array<{ id: string; name: string }>, ApiError>({
    queryKey: heatmapQueryKeys.rotations(),
    queryFn: () => get<Array<{ id: string; name: string }>>('/visualization/rotations'),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Export heatmap as image or data file
 */
export function useExportHeatmap() {
  return useMutation<Blob, ApiError, HeatmapExportConfig>({
    mutationFn: async (config) => {
      const response = await post<Blob>('/visualization/heatmap/export', config, {
        responseType: 'blob',
      });
      return response;
    },
  });
}

/**
 * Generate and download heatmap image
 */
export function useDownloadHeatmap() {
  const exportMutation = useExportHeatmap();

  return {
    ...exportMutation,
    download: async (config: HeatmapExportConfig, filename?: string) => {
      const blob = await exportMutation.mutateAsync(config);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || `heatmap-${new Date().toISOString()}.${config.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  };
}

// ============================================================================
// Utility Hooks
// ============================================================================

/**
 * Prefetch heatmap data for better UX
 */
export function usePrefetchHeatmap() {
  const queryClient = useQueryClient();

  return (filters: HeatmapFilters) => {
    const queryString = buildQueryString(filters);
    queryClient.prefetchQuery({
      queryKey: heatmapQueryKeys.custom(filters),
      queryFn: () =>
        get<HeatmapResponse>(`/visualization/heatmap${queryString ? `?${queryString}` : ''}`),
      staleTime: 60 * 1000,
    });
  };
}

/**
 * Invalidate all heatmap queries (useful after schedule changes)
 */
export function useInvalidateHeatmaps() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: heatmapQueryKeys.all });
  };
}
