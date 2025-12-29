/**
 * Daily Manifest Hooks
 *
 * React Query hooks for fetching daily manifest data showing
 * current location and assignment information.
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { get, ApiError } from '@/lib/api';
import type { DailyManifestData, ScheduleDateRange } from './types';

// ============================================================================
// Query Keys
// ============================================================================

export const manifestQueryKeys = {
  all: ['daily-manifest'] as const,
  byDate: (date: string, timeOfDay: string) =>
    ['daily-manifest', date, timeOfDay] as const,
  dateRange: () => ['daily-manifest', 'date-range'] as const,
};

// ============================================================================
// Hooks
// ============================================================================

/**
 * Fetch daily manifest for a specific date and time
 */
export function useDailyManifest(
  date: string,
  timeOfDay: 'AM' | 'PM' | 'ALL' = 'AM',
  options?: Omit<UseQueryOptions<DailyManifestData, ApiError>, 'queryKey' | 'queryFn'>
) {
  // Only include time_of_day param for AM/PM, omit for ALL (backend returns all if not specified)
  const params = new URLSearchParams({ date });
  if (timeOfDay !== 'ALL') {
    params.set('time_of_day', timeOfDay);
  }
  return useQuery<DailyManifestData, ApiError>({
    queryKey: manifestQueryKeys.byDate(date, timeOfDay),
    queryFn: () =>
      get<DailyManifestData>(
        `/daily-manifest?${params.toString()}`
      ),
    staleTime: 30 * 1000, // 30 seconds - manifest changes frequently
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
    enabled: !!date,
    ...options,
  });
}

/**
 * Fetch today's manifest (convenience hook)
 */
export function useTodayManifest(
  timeOfDay: 'AM' | 'PM' | 'ALL' = 'AM',
  options?: Omit<UseQueryOptions<DailyManifestData, ApiError>, 'queryKey' | 'queryFn'>
) {
  const today = new Date().toISOString().split('T')[0];
  return useDailyManifest(today, timeOfDay, options);
}

/**
 * Fetch the date range where schedule data is available
 * Uses the blocks endpoint to determine min/max dates
 */
export function useScheduleDateRange(
  options?: Omit<UseQueryOptions<ScheduleDateRange, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ScheduleDateRange, ApiError>({
    queryKey: manifestQueryKeys.dateRange(),
    queryFn: async () => {
      // Fetch blocks to determine date range
      // The blocks endpoint returns a list of blocks with dates
      const response = await get<{ items: Array<{ date: string }> }>('/blocks?limit=1');

      // If no blocks exist, return null range
      if (!response.items || response.items.length === 0) {
        return { start_date: null, end_date: null, has_data: false };
      }

      // Fetch again with date range to get actual bounds
      // Get earliest block
      const earliestResponse = await get<{ items: Array<{ date: string }> }>(
        '/blocks?limit=1&order_by=date&order=asc'
      );
      // Get latest block
      const latestResponse = await get<{ items: Array<{ date: string }> }>(
        '/blocks?limit=1&order_by=date&order=desc'
      );

      const startDate = earliestResponse.items?.[0]?.date || null;
      const endDate = latestResponse.items?.[0]?.date || null;

      return {
        start_date: startDate,
        end_date: endDate,
        has_data: !!(startDate && endDate),
      };
    },
    staleTime: 5 * 60 * 1000, // 5 minutes - date range changes infrequently
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}
