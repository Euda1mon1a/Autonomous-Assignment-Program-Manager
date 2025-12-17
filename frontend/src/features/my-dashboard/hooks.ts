/**
 * React Query Hooks for My Life Dashboard Feature
 *
 * Provides data fetching, caching, and mutation hooks
 * for personal schedule dashboard operations.
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { get, post, ApiError } from '@/lib/api';
import type {
  DashboardData,
  DashboardQueryParams,
  CalendarSyncRequest,
  CalendarSyncResponse,
  UpcomingAssignment,
  PendingSwapSummary,
  AbsenceEntry,
  TimeOfDay,
  Location,
} from './types';

// ============================================================================
// Query Keys
// ============================================================================

export const dashboardQueryKeys = {
  all: ['my-dashboard'] as const,
  dashboard: (params?: DashboardQueryParams) => ['my-dashboard', 'data', params] as const,
  calendarUrl: () => ['my-dashboard', 'calendar-url'] as const,
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Transform backend assignment to frontend format
 */
function transformAssignment(assignment: any): UpcomingAssignment {
  return {
    id: assignment.id || `${assignment.date}-${assignment.time_of_day}`,
    date: assignment.date,
    timeOfDay: assignment.time_of_day as TimeOfDay,
    activity: assignment.activity,
    location: assignment.location as Location,
    canTrade: assignment.can_trade ?? true,
    isConflict: assignment.is_conflict,
    conflictReason: assignment.conflict_reason,
  };
}

/**
 * Transform backend pending swap to frontend format
 */
function transformPendingSwap(swap: any, currentUserId?: string): PendingSwapSummary {
  const isIncoming = swap.target_faculty_id === currentUserId;
  const isOutgoing = swap.source_faculty_id === currentUserId;

  return {
    id: swap.id,
    type: isIncoming ? 'incoming' : 'outgoing',
    otherFacultyName: isIncoming ? swap.source_faculty_name : swap.target_faculty_name,
    weekDate: isIncoming ? swap.source_week : swap.target_week,
    status: swap.status,
    requestedAt: swap.requested_at,
    reason: swap.reason,
    canRespond: isIncoming && swap.status === 'pending',
  };
}

/**
 * Transform backend absence to frontend format
 */
function transformAbsence(absence: any): AbsenceEntry {
  return {
    id: absence.id,
    startDate: absence.start_date,
    endDate: absence.end_date,
    reason: absence.reason,
    status: absence.status,
    requestedAt: absence.requested_at,
  };
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetch complete dashboard data for current user
 */
export function useMyDashboard(
  params?: DashboardQueryParams,
  options?: Omit<UseQueryOptions<DashboardData, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<DashboardData, ApiError>({
    queryKey: dashboardQueryKeys.dashboard(params),
    queryFn: async () => {
      const queryParams = new URLSearchParams();
      if (params?.daysAhead) queryParams.append('days_ahead', params.daysAhead.toString());
      if (params?.includeSwaps !== undefined) queryParams.append('include_swaps', params.includeSwaps.toString());
      if (params?.includeAbsences !== undefined) queryParams.append('include_absences', params.includeAbsences.toString());

      const queryString = queryParams.toString();
      const url = `/portal/my/dashboard${queryString ? `?${queryString}` : ''}`;

      const response = await get<any>(url);

      // Get current user ID from localStorage if available
      let currentUserId: string | undefined;
      if (typeof window !== 'undefined') {
        const userStr = localStorage.getItem('user');
        if (userStr) {
          const user = JSON.parse(userStr);
          currentUserId = user.id;
        }
      }

      return {
        user: {
          id: response.user.id,
          name: response.user.name,
          role: response.user.role,
        },
        upcomingSchedule: (response.upcoming_schedule || []).map(transformAssignment),
        pendingSwaps: (response.pending_swaps || []).map((swap: any) =>
          transformPendingSwap(swap, currentUserId)
        ),
        absences: (response.absences || []).map(transformAbsence),
        calendarSyncUrl: response.calendar_sync_url || '',
        summary: {
          nextAssignment: response.summary?.next_assignment || null,
          workloadNext4Weeks: response.summary?.workload_next_4_weeks || 0,
          pendingSwapCount: response.summary?.pending_swap_count || 0,
          upcomingAbsences: response.summary?.upcoming_absences || 0,
        },
      };
    },
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Fetch calendar sync URL for current user
 */
export function useCalendarSyncUrl(
  options?: Omit<UseQueryOptions<string, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<string, ApiError>({
    queryKey: dashboardQueryKeys.calendarUrl(),
    queryFn: async () => {
      const response = await get<{ url: string }>('/portal/my/calendar-sync-url');
      return response.url;
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Request calendar sync/export
 */
export function useCalendarSync() {
  const queryClient = useQueryClient();

  return useMutation<CalendarSyncResponse, ApiError, CalendarSyncRequest>({
    mutationFn: async (request) => {
      const response = await post<any>('/portal/my/calendar-sync', {
        format: request.format,
        include_weeks_ahead: request.includeWeeksAhead || 12,
      });

      return {
        success: response.success,
        url: response.url,
        message: response.message,
      };
    },
    onSuccess: () => {
      // Invalidate calendar URL cache
      queryClient.invalidateQueries({ queryKey: dashboardQueryKeys.calendarUrl() });
    },
  });
}

/**
 * Request to swap a specific assignment
 */
export function useRequestSwap() {
  const queryClient = useQueryClient();

  return useMutation<{ success: boolean; message: string }, ApiError, { assignmentId: string; reason?: string }>({
    mutationFn: async ({ assignmentId, reason }) => {
      const response = await post<any>(`/portal/my/assignments/${assignmentId}/request-swap`, {
        reason,
      });

      return {
        success: response.success,
        message: response.message || 'Swap request created successfully',
      };
    },
    onSuccess: () => {
      // Invalidate dashboard to refresh data
      queryClient.invalidateQueries({ queryKey: dashboardQueryKeys.all });
    },
  });
}
