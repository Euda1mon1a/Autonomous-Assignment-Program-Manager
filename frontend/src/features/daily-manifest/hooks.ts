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
        `/assignments/daily-manifest?${params.toString()}`
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
 *
 * Note: The /blocks API returns items sorted ascending by date, time_of_day.
 * It only supports start_date, end_date, and block_number query params.
 */
export function useScheduleDateRange(
  options?: Omit<UseQueryOptions<ScheduleDateRange, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ScheduleDateRange, ApiError>({
    queryKey: manifestQueryKeys.dateRange(),
    queryFn: async () => {
      // Fetch all blocks - the API returns them sorted ascending by date
      const response = await get<{ items: Array<{ date: string }> }>('/blocks');

      // If no blocks exist, return null range
      if (!response.items || response.items.length === 0) {
        return { start_date: null, end_date: null, has_data: false };
      }

      // First item is earliest (ascending order), last item is latest
      const startDate = response.items[0]?.date || null;
      const endDate = response.items[response.items.length - 1]?.date || null;

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
