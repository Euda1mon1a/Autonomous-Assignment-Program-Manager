/**
 * Admin Dashboard Hooks
 *
 * React Query hooks for admin dashboard metrics.
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { ApiError, get } from '@/lib/api';

// ============================================================================
// Types
// ============================================================================

export interface BreakGlassUsageResponse {
  windowStart: string;
  windowEnd: string;
  count: number;
  lastUsedAt?: string | null;
}

// ============================================================================
// Query Keys
// ============================================================================

export const adminDashboardQueryKeys = {
  all: ['admin-dashboard'] as const,
  breakGlass: () => ['admin-dashboard', 'break-glass'] as const,
};

// ============================================================================
// Query Hooks
// ============================================================================

export function useBreakGlassUsage(
  options?: Omit<
    UseQueryOptions<BreakGlassUsageResponse, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<BreakGlassUsageResponse, ApiError>({
    queryKey: adminDashboardQueryKeys.breakGlass(),
    queryFn: () => get<BreakGlassUsageResponse>('/admin/dashboard/break-glass'),
    staleTime: 60 * 1000,
    gcTime: 5 * 60 * 1000,
    ...options,
  });
}
