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

// Backend API response types
interface AssignmentApiResponse {
  id?: string;
  date: string;
  timeOfDay: string;
  activity: string;
  location: string;
  can_trade?: boolean;
  is_conflict?: boolean;
  conflict_reason?: string;
}

interface SwapApiResponse {
  id: string;
  sourceFacultyId: string;
  sourceFacultyName: string;
  targetFacultyId?: string;
  targetFacultyName?: string;
  sourceWeek: string;
  targetWeek?: string;
  status: string;
  requestedAt: string;
  reason?: string;
}

interface AbsenceApiResponse {
  id: string;
  startDate: string;
  endDate: string;
  reason: string;
  status: string;
  requestedAt: string;
}

interface UserApiResponse {
  id: string;
  name: string;
  role: string;
}

interface DashboardApiResponse {
  user: UserApiResponse;
  upcoming_schedule?: AssignmentApiResponse[];
  pending_swaps?: SwapApiResponse[];
  absences?: AbsenceApiResponse[];
  calendar_sync_url?: string;
  summary?: {
    next_assignment?: string | null;
    workload_next_4_weeks?: number;
    pending_swap_count?: number;
    upcoming_absences?: number;
  };
}

interface CalendarSyncApiResponse {
  success: boolean;
  url: string;
  message: string;
}

interface SwapRequestApiResponse {
  success: boolean;
  message: string;
}

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
function transformAssignment(assignment: AssignmentApiResponse): UpcomingAssignment {
  return {
    id: assignment.id || `${assignment.date}-${assignment.timeOfDay}`,
    date: assignment.date,
    timeOfDay: assignment.timeOfDay as TimeOfDay,
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
function transformPendingSwap(swap: SwapApiResponse, currentUserId?: string): PendingSwapSummary {
  const isIncoming = swap.targetFacultyId === currentUserId;

  return {
    id: swap.id,
    type: isIncoming ? 'incoming' : 'outgoing',
    otherFacultyName: isIncoming ? swap.sourceFacultyName : swap.targetFacultyName || '',
    weekDate: isIncoming ? swap.sourceWeek : swap.targetWeek || '',
    status: swap.status as 'pending' | 'approved' | 'rejected',
    requestedAt: swap.requestedAt,
    reason: swap.reason,
    canRespond: isIncoming && swap.status === 'pending',
  };
}

/**
 * Transform backend absence to frontend format
 */
function transformAbsence(absence: AbsenceApiResponse): AbsenceEntry {
  return {
    id: absence.id,
    startDate: absence.startDate,
    endDate: absence.endDate,
    reason: absence.reason,
    status: absence.status as 'pending' | 'approved' | 'rejected',
    requestedAt: absence.requestedAt,
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

      const response = await get<DashboardApiResponse>(url);

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
        pendingSwaps: (response.pending_swaps || []).map((swap: SwapApiResponse) =>
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
    mutationFn: async (request: CalendarSyncRequest) => {
      const response = await post<CalendarSyncApiResponse>('/portal/my/calendar-sync', {
        format: request.format,
        includeWeeksAhead: request.includeWeeksAhead || 12,
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
    mutationFn: async ({ assignmentId, reason }: { assignmentId: string; reason?: string }) => {
      const response = await post<SwapRequestApiResponse>(`/portal/my/assignments/${assignmentId}/request-swap`, {
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
