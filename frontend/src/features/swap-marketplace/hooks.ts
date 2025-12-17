/**
 * React Query Hooks for Swap Marketplace Feature
 *
 * Provides data fetching, caching, and mutation hooks
 * for swap marketplace operations.
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { get, post, ApiError } from '@/lib/api';
import type {
  SwapRequest,
  MarketplaceResponse,
  MarketplaceEntry,
  MySwapsResponse,
  CreateSwapRequest,
  CreateSwapResponse,
  SwapRespondRequest,
  SwapRespondResponse,
  FacultyPreference,
  SwapFilters,
} from './types';

// ============================================================================
// Query Keys
// ============================================================================

export const swapQueryKeys = {
  all: ['swaps'] as const,
  marketplace: (filters?: SwapFilters) => ['swaps', 'marketplace', filters] as const,
  mySwaps: () => ['swaps', 'my-swaps'] as const,
  swapRequest: (id: string) => ['swaps', 'request', id] as const,
  preferences: () => ['swaps', 'preferences'] as const,
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Transform backend swap request to frontend format
 */
function transformSwapRequest(backendSwap: any, currentUserId?: string): SwapRequest {
  const isIncoming = backendSwap.target_faculty_id === currentUserId;
  const isOutgoing = backendSwap.source_faculty_id === currentUserId;

  return {
    id: backendSwap.id,
    sourceFacultyId: backendSwap.source_faculty_id,
    sourceFacultyName: backendSwap.source_faculty?.name || 'Unknown',
    sourceWeek: backendSwap.source_week,
    targetFacultyId: backendSwap.target_faculty_id,
    targetFacultyName: backendSwap.target_faculty?.name,
    targetWeek: backendSwap.target_week,
    swapType: backendSwap.swap_type,
    status: backendSwap.status,
    requestedAt: backendSwap.requested_at,
    requestedById: backendSwap.requested_by_id,
    approvedAt: backendSwap.approved_at,
    approvedById: backendSwap.approved_by_id,
    executedAt: backendSwap.executed_at,
    executedById: backendSwap.executed_by_id,
    reason: backendSwap.reason,
    notes: backendSwap.notes,
    isIncoming,
    isOutgoing,
    canAccept: isIncoming && backendSwap.status === 'pending',
    canReject: isIncoming && backendSwap.status === 'pending',
    canCancel: isOutgoing && backendSwap.status === 'pending',
  };
}

/**
 * Transform marketplace entry from backend
 */
function transformMarketplaceEntry(entry: any): MarketplaceEntry {
  return {
    requestId: entry.request_id,
    requestingFacultyName: entry.requesting_faculty_name,
    weekAvailable: entry.week_available,
    reason: entry.reason,
    postedAt: entry.posted_at,
    expiresAt: entry.expires_at,
    isCompatible: entry.is_compatible,
  };
}

/**
 * Transform faculty preference from backend
 */
function transformFacultyPreference(pref: any): FacultyPreference {
  return {
    facultyId: pref.faculty_id,
    preferredWeeks: pref.preferred_weeks || [],
    blockedWeeks: pref.blocked_weeks || [],
    maxWeeksPerMonth: pref.max_weeks_per_month,
    maxConsecutiveWeeks: pref.max_consecutive_weeks,
    minGapBetweenWeeks: pref.min_gap_between_weeks,
    targetWeeksPerYear: pref.target_weeks_per_year,
    notifySwapRequests: pref.notify_swap_requests,
    notifyScheduleChanges: pref.notify_schedule_changes,
    notifyConflictAlerts: pref.notify_conflict_alerts,
    notifyReminderDays: pref.notify_reminder_days,
    notes: pref.notes,
    updatedAt: pref.updated_at,
  };
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetch marketplace entries (available swap requests)
 */
export function useSwapMarketplace(
  filters?: SwapFilters,
  options?: Omit<UseQueryOptions<MarketplaceResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<MarketplaceResponse, ApiError>({
    queryKey: swapQueryKeys.marketplace(filters),
    queryFn: async () => {
      const response = await get<any>('/portal/marketplace');
      return {
        entries: response.entries.map(transformMarketplaceEntry),
        total: response.total,
        myPostings: response.my_postings,
      };
    },
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Fetch current user's swap requests (incoming, outgoing, recent)
 */
export function useMySwapRequests(
  options?: Omit<UseQueryOptions<MySwapsResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<MySwapsResponse, ApiError>({
    queryKey: swapQueryKeys.mySwaps(),
    queryFn: async () => {
      const response = await get<any>('/portal/my/swaps');

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
        incomingRequests: response.incoming_requests.map((req: any) =>
          transformSwapRequest(req, currentUserId)
        ),
        outgoingRequests: response.outgoing_requests.map((req: any) =>
          transformSwapRequest(req, currentUserId)
        ),
        recentSwaps: response.recent_swaps.map((req: any) =>
          transformSwapRequest(req, currentUserId)
        ),
      };
    },
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Fetch faculty preferences for the current user
 */
export function useFacultyPreferences(
  options?: Omit<UseQueryOptions<FacultyPreference, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<FacultyPreference, ApiError>({
    queryKey: swapQueryKeys.preferences(),
    queryFn: async () => {
      const response = await get<any>('/portal/my/preferences');
      return transformFacultyPreference(response);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Create a new swap request
 */
export function useCreateSwapRequest() {
  const queryClient = useQueryClient();

  return useMutation<CreateSwapResponse, ApiError, CreateSwapRequest>({
    mutationFn: async (request) => {
      const response = await post<any>('/portal/my/swaps', {
        week_to_offload: request.weekToOffload,
        preferred_target_faculty_id: request.preferredTargetFacultyId,
        reason: request.reason,
        auto_find_candidates: request.autoFindCandidates ?? true,
      });

      return {
        success: response.success,
        requestId: response.request_id,
        message: response.message,
        candidatesNotified: response.candidates_notified,
      };
    },
    onSuccess: () => {
      // Invalidate relevant queries to refresh data
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.mySwaps() });
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.marketplace() });
    },
  });
}

/**
 * Accept a swap request
 */
export function useAcceptSwap(swapId: string) {
  const queryClient = useQueryClient();

  return useMutation<SwapRespondResponse, ApiError, { notes?: string }>({
    mutationFn: async ({ notes }) => {
      const response = await post<any>(`/portal/my/swaps/${swapId}/respond`, {
        accept: true,
        notes,
      });

      return {
        success: response.success,
        message: response.message,
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.mySwaps() });
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.marketplace() });
    },
  });
}

/**
 * Reject a swap request
 */
export function useRejectSwap(swapId: string) {
  const queryClient = useQueryClient();

  return useMutation<SwapRespondResponse, ApiError, { notes?: string }>({
    mutationFn: async ({ notes }) => {
      const response = await post<any>(`/portal/my/swaps/${swapId}/respond`, {
        accept: false,
        notes,
      });

      return {
        success: response.success,
        message: response.message,
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.mySwaps() });
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.marketplace() });
    },
  });
}

/**
 * Cancel a swap request (for outgoing requests)
 */
export function useCancelSwap(swapId: string) {
  const queryClient = useQueryClient();

  return useMutation<SwapRespondResponse, ApiError, void>({
    mutationFn: async () => {
      // Cancel is implemented as a DELETE or status update
      // Using respond endpoint with cancel flag for now
      const response = await post<any>(`/portal/my/swaps/${swapId}/respond`, {
        accept: false,
        notes: 'Request cancelled by requester',
      });

      return {
        success: response.success,
        message: response.message,
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.mySwaps() });
      queryClient.invalidateQueries({ queryKey: swapQueryKeys.marketplace() });
    },
  });
}
