/**
 * Daily Manifest Hooks
 *
 * React Query hooks for fetching daily manifest data showing
 * current location and assignment information.
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { get, ApiError } from '@/lib/api';
import type { DailyManifestData } from './types';

// ============================================================================
// Query Keys
// ============================================================================

export const manifestQueryKeys = {
  all: ['daily-manifest'] as const,
  byDate: (date: string, timeOfDay: string) =>
    ['daily-manifest', date, timeOfDay] as const,
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
<<<<<<< HEAD
  // Only include time_of_day param for AM/PM, omit for ALL (backend returns all if not specified)
  const params = new URLSearchParams({ date });
  if (timeOfDay !== 'ALL') {
    params.set('time_of_day', timeOfDay);
  }
=======
>>>>>>> origin/docs/session-14-summary
  return useQuery<DailyManifestData, ApiError>({
    queryKey: manifestQueryKeys.byDate(date, timeOfDay),
    queryFn: () =>
      get<DailyManifestData>(
<<<<<<< HEAD
        `/daily-manifest?${params.toString()}`
=======
        `/daily-manifest?date=${date}&time_of_day=${timeOfDay}`
>>>>>>> origin/docs/session-14-summary
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
