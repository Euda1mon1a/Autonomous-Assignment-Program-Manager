/**
 * Proxy Coverage Hooks
 *
 * React Query hooks for fetching proxy coverage data showing
 * "who is covering for whom" across the scheduling system.
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { get, ApiError } from '@/lib/api';
import type { ProxyCoverageResponse, ProxyCoverageFilters } from './types';

// ============================================================================
// Query Keys
// ============================================================================

export const proxyCoverageQueryKeys = {
  all: ['proxy-coverage'] as const,
  byDate: (date: string) => ['proxy-coverage', date] as const,
  filtered: (date: string, filters: ProxyCoverageFilters) =>
    ['proxy-coverage', date, filters] as const,
};

// ============================================================================
// Hooks
// ============================================================================

/**
 * Fetch proxy coverage data for a specific date
 */
export function useProxyCoverage(
  date: string,
  options?: Omit<UseQueryOptions<ProxyCoverageResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ProxyCoverageResponse, ApiError>({
    queryKey: proxyCoverageQueryKeys.byDate(date),
    queryFn: () => get<ProxyCoverageResponse>(`/proxy-coverage?date=${date}`),
    staleTime: 60 * 1000, // 1 minute - coverage changes less frequently
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
    enabled: !!date,
    ...options,
  });
}

/**
 * Fetch today's proxy coverage (convenience hook)
 */
export function useTodayProxyCoverage(
  options?: Omit<UseQueryOptions<ProxyCoverageResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  const today = new Date().toISOString().split('T')[0];
  return useProxyCoverage(today, options);
}

/**
 * Fetch proxy coverage with filters
 */
export function useFilteredProxyCoverage(
  date: string,
  filters: ProxyCoverageFilters,
  options?: Omit<UseQueryOptions<ProxyCoverageResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  // Build query params from filters
  const params = new URLSearchParams({ date });
  if (filters.coverageType && filters.coverageType !== 'all') {
    params.set('coverage_type', filters.coverageType);
  }
  if (filters.status && filters.status !== 'all') {
    params.set('status', filters.status);
  }
  if (filters.personId) {
    params.set('person_id', filters.personId);
  }
  if (filters.startDate) {
    params.set('start_date', filters.startDate);
  }
  if (filters.endDate) {
    params.set('end_date', filters.endDate);
  }

  return useQuery<ProxyCoverageResponse, ApiError>({
    queryKey: proxyCoverageQueryKeys.filtered(date, filters),
    queryFn: () => get<ProxyCoverageResponse>(`/proxy-coverage?${params.toString()}`),
    staleTime: 60 * 1000,
    gcTime: 5 * 60 * 1000,
    refetchOnWindowFocus: true,
    enabled: !!date,
    ...options,
  });
}
