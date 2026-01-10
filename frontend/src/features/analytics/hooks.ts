/**
 * React Query Hooks for Analytics Feature
 *
 * Provides data fetching, caching, and mutation hooks
 * for analytics operations.
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { get, post, ApiError } from '@/lib/api';
import type {
  ScheduleMetrics,
  FairnessTrendData,
  PgyEquityData,
  VersionComparison,
  WhatIfAnalysisRequest,
  WhatIfAnalysisResult,
  MetricAlert,
  TimePeriod,
  AnalyticsFilters,
} from './types';
import { DEFAULT_TIME_PERIOD } from './types';

// ============================================================================
// Query Keys
// ============================================================================

export const analyticsQueryKeys = {
  all: ['analytics'] as const,
  currentMetrics: () => ['analytics', 'current-metrics'] as const,
  fairnessTrend: (period: TimePeriod) => ['analytics', 'fairness-trend', period] as const,
  pgyEquity: () => ['analytics', 'pgy-equity'] as const,
  versionComparison: (versionA: string, versionB: string) =>
    ['analytics', 'version-comparison', versionA, versionB] as const,
  versions: () => ['analytics', 'versions'] as const,
  alerts: (acknowledged?: boolean) => ['analytics', 'alerts', acknowledged] as const,
  whatIfAnalysis: (requestId: string) => ['analytics', 'what-if', requestId] as const,
};

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetch current schedule metrics
 */
export function useCurrentMetrics(
  options?: Omit<UseQueryOptions<ScheduleMetrics, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ScheduleMetrics, ApiError>({
    queryKey: analyticsQueryKeys.currentMetrics(),
    queryFn: () => get<ScheduleMetrics>('/analytics/metrics/current'),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Fetch fairness trend data over a time period
 */
export function useFairnessTrend(
  months?: number,
  options?: Omit<UseQueryOptions<FairnessTrendData, ApiError>, 'queryKey' | 'queryFn'>
) {
  // Convert months to TimePeriod for backward compatibility
  const period: TimePeriod = months
    ? months <= 3
      ? '90d'
      : months <= 6
      ? '180d'
      : '1y'
    : DEFAULT_TIME_PERIOD;

  return useQuery<FairnessTrendData, ApiError>({
    queryKey: analyticsQueryKeys.fairnessTrend(period),
    queryFn: () => get<FairnessTrendData>(`/analytics/trends/fairness?period=${period}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

/**
 * Fetch PGY equity comparison data
 */
export function usePgyEquity(
  options?: Omit<UseQueryOptions<PgyEquityData[], ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<PgyEquityData[], ApiError>({
    queryKey: analyticsQueryKeys.pgyEquity(),
    queryFn: () => get<PgyEquityData[]>('/analytics/equity/pgy'),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

/**
 * Fetch version comparison between two schedule versions
 */
export function useVersionComparison(
  versionA: string,
  versionB: string,
  options?: Omit<UseQueryOptions<VersionComparison, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<VersionComparison, ApiError>({
    queryKey: analyticsQueryKeys.versionComparison(versionA, versionB),
    queryFn: () =>
      get<VersionComparison>(`/analytics/versions/compare?version_a=${versionA}&version_b=${versionB}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!versionA && !!versionB,
    ...options,
  });
}

/**
 * Fetch available schedule versions
 */
export function useScheduleVersions(
  options?: Omit<
    UseQueryOptions<{ id: string; name: string; createdAt: string; status: string }[], ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<{ id: string; name: string; createdAt: string; status: string }[], ApiError>({
    queryKey: analyticsQueryKeys.versions(),
    queryFn: () => get<{ id: string; name: string; createdAt: string; status: string }[]>('/analytics/versions'),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  });
}

/**
 * Fetch metric threshold alerts
 */
export function useMetricAlerts(
  acknowledged?: boolean,
  options?: Omit<UseQueryOptions<MetricAlert[], ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = acknowledged !== undefined ? `?acknowledged=${acknowledged}` : '';

  return useQuery<MetricAlert[], ApiError>({
    queryKey: analyticsQueryKeys.alerts(acknowledged),
    queryFn: () => get<MetricAlert[]>(`/analytics/alerts${params}`),
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Fetch what-if analysis result
 */
export function useWhatIfAnalysisResult(
  requestId: string,
  options?: Omit<UseQueryOptions<WhatIfAnalysisResult, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<WhatIfAnalysisResult, ApiError>({
    queryKey: analyticsQueryKeys.whatIfAnalysis(requestId),
    queryFn: () => get<WhatIfAnalysisResult>(`/analytics/what-if/${requestId}`),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: !!requestId,
    ...options,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Submit what-if analysis request
 */
export function useWhatIfAnalysis() {
  const queryClient = useQueryClient();

  return useMutation<WhatIfAnalysisResult, ApiError, WhatIfAnalysisRequest>({
    mutationFn: async (request) => {
      const result = await post<WhatIfAnalysisResult>('/analytics/what-if', request);
      return result;
    },
    onSuccess: (result) => {
      // Cache the result
      queryClient.setQueryData(analyticsQueryKeys.whatIfAnalysis(result.requestId), result);
    },
  });
}

/**
 * Acknowledge metric alert
 */
export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, { alertId: string; notes?: string }>({
    mutationFn: async ({ alertId, notes }) => {
      await post(`/analytics/alerts/${alertId}/acknowledge`, { notes });
    },
    onSuccess: () => {
      // Invalidate alerts to refetch
      queryClient.invalidateQueries({ queryKey: analyticsQueryKeys.alerts() });
    },
  });
}

/**
 * Dismiss metric alert
 */
export function useDismissAlert() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: async (alertId) => {
      await post(`/analytics/alerts/${alertId}/dismiss`, {});
    },
    onSuccess: () => {
      // Invalidate alerts to refetch
      queryClient.invalidateQueries({ queryKey: analyticsQueryKeys.alerts() });
    },
  });
}

/**
 * Export analytics data
 */
export function useExportAnalytics() {
  return useMutation<
    Blob,
    ApiError,
    {
      format: 'csv' | 'json' | 'pdf';
      filters?: AnalyticsFilters;
      includeCharts?: boolean;
    }
  >({
    mutationFn: async ({ format, filters, includeCharts }) => {
      const response = await post<Blob>(
        '/analytics/export',
        {
          format,
          filters,
          includeCharts: includeCharts,
        },
        {
          responseType: 'blob',
        }
      );
      return response;
    },
  });
}

/**
 * Refresh metrics (force recalculation)
 */
export function useRefreshMetrics() {
  const queryClient = useQueryClient();

  return useMutation<ScheduleMetrics, ApiError, void>({
    mutationFn: async () => {
      const result = await post<ScheduleMetrics>('/analytics/metrics/refresh', {});
      return result;
    },
    onSuccess: (result) => {
      // Update cached metrics
      queryClient.setQueryData(analyticsQueryKeys.currentMetrics(), result);
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: analyticsQueryKeys.fairnessTrend(DEFAULT_TIME_PERIOD) });
      queryClient.invalidateQueries({ queryKey: analyticsQueryKeys.alerts() });
    },
  });
}

// ============================================================================
// Utility Hooks
// ============================================================================

/**
 * Prefetch fairness trend for better UX
 */
export function usePrefetchFairnessTrend() {
  const queryClient = useQueryClient();

  return (period: TimePeriod) => {
    queryClient.prefetchQuery({
      queryKey: analyticsQueryKeys.fairnessTrend(period),
      queryFn: () => get<FairnessTrendData>(`/analytics/trends/fairness?period=${period}`),
      staleTime: 5 * 60 * 1000,
    });
  };
}

/**
 * Prefetch version comparison
 */
export function usePrefetchVersionComparison() {
  const queryClient = useQueryClient();

  return (versionA: string, versionB: string) => {
    if (versionA && versionB) {
      queryClient.prefetchQuery({
        queryKey: analyticsQueryKeys.versionComparison(versionA, versionB),
        queryFn: () =>
          get<VersionComparison>(`/analytics/versions/compare?version_a=${versionA}&version_b=${versionB}`),
        staleTime: 5 * 60 * 1000,
      });
    }
  };
}
