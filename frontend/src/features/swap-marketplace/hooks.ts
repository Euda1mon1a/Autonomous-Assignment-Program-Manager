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
  SwapRespondResponse,
  FacultyPreference,
  SwapFilters,
  SwapStatus,
  SwapType,
} from './types';

// Backend API response types
interface SwapRequestApiResponse {
  id: string;
  source_faculty_id: string;
  source_faculty?: { name: string };
  source_week: string;
  target_faculty_id?: string;
  target_faculty?: { name: string };
  target_week?: string;
  swap_type: string;
  status: string;
  requested_at: string;
  requested_by_id: string;
  approved_at?: string;
  approved_by_id?: string;
  executed_at?: string;
  executed_by_id?: string;
  reason?: string;
  notes?: string;
}

interface MarketplaceEntryApiResponse {
  request_id: string;
  requesting_faculty_name: string;
  week_available: string;
  reason?: string;
  posted_at: string;
  expires_at?: string;
  is_compatible?: boolean;
}

interface MarketplaceApiResponse {
  entries: MarketplaceEntryApiResponse[];
  total: number;
  my_postings: number;
}

interface MySwapsApiResponse {
  incoming_requests: SwapRequestApiResponse[];
  outgoing_requests: SwapRequestApiResponse[];
  recent_swaps: SwapRequestApiResponse[];
}

interface FacultyPreferenceApiResponse {
  faculty_id: string;
  preferred_weeks?: string[];
  blocked_weeks?: string[];
  max_weeks_per_month?: number;
  max_consecutive_weeks?: number;
  min_gap_between_weeks?: number;
  target_weeks_per_year?: number;
  notify_swap_requests?: boolean;
  notify_schedule_changes?: boolean;
  notify_conflict_alerts?: boolean;
  notify_reminder_days?: number;
  notes?: string;
  updated_at: string;
}

interface CreateSwapApiResponse {
  success: boolean;
  request_id: string;
  message: string;
  candidates_notified?: number;
}

interface SwapRespondApiResponse {
  success: boolean;
  message: string;
}

interface AvailableWeeksApiResponse {
  weeks: Array<{ date: string; hasConflict: boolean }>;
}

interface FacultyListApiResponse {
  faculty: Array<{ id: string; name: string }>;
}

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
function transformSwapRequest(backendSwap: SwapRequestApiResponse, currentUserId?: string): SwapRequest {
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
    swapType: backendSwap.swap_type as SwapType,
    status: backendSwap.status as SwapStatus,
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
function transformMarketplaceEntry(entry: MarketplaceEntryApiResponse): MarketplaceEntry {
  return {
    requestId: entry.request_id,
    requestingFacultyName: entry.requesting_faculty_name,
    weekAvailable: entry.week_available,
    reason: entry.reason,
    postedAt: entry.posted_at,
    expiresAt: entry.expires_at,
    isCompatible: entry.is_compatible ?? false,
  };
}

/**
 * Transform faculty preference from backend
 */
function transformFacultyPreference(pref: FacultyPreferenceApiResponse): FacultyPreference {
  return {
    facultyId: pref.faculty_id,
    preferredWeeks: pref.preferred_weeks || [],
    blockedWeeks: pref.blocked_weeks || [],
    maxWeeksPerMonth: pref.max_weeks_per_month || 0,
    maxConsecutiveWeeks: pref.max_consecutive_weeks || 0,
    minGapBetweenWeeks: pref.min_gap_between_weeks || 0,
    targetWeeksPerYear: pref.target_weeks_per_year || 0,
    notifySwapRequests: pref.notify_swap_requests ?? false,
    notifyScheduleChanges: pref.notify_schedule_changes ?? false,
    notifyConflictAlerts: pref.notify_conflict_alerts ?? false,
    notifyReminderDays: pref.notify_reminder_days || 0,
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
      const response = await get<MarketplaceApiResponse>('/portal/marketplace');
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
 * @param currentUserId - User ID from AuthContext (required for proper isIncoming/isOutgoing flags)
 * @param options - React Query options
 */
export function useMySwapRequests(
  currentUserId?: string,
  options?: Omit<UseQueryOptions<MySwapsResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<MySwapsResponse, ApiError>({
    queryKey: swapQueryKeys.mySwaps(),
    queryFn: async () => {
      const response = await get<MySwapsApiResponse>('/portal/my/swaps');

      return {
        incomingRequests: response.incoming_requests.map((req: SwapRequestApiResponse) =>
          transformSwapRequest(req, currentUserId)
        ),
        outgoingRequests: response.outgoing_requests.map((req: SwapRequestApiResponse) =>
          transformSwapRequest(req, currentUserId)
        ),
        recentSwaps: response.recent_swaps.map((req: SwapRequestApiResponse) =>
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
      const response = await get<FacultyPreferenceApiResponse>('/portal/my/preferences');
      return transformFacultyPreference(response);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

/**
 * Fetch available weeks for the current user to swap
 */
export function useAvailableWeeks(
  options?: Omit<UseQueryOptions<Array<{ date: string; hasConflict: boolean }>, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Array<{ date: string; hasConflict: boolean }>, ApiError>({
    queryKey: ['swaps', 'available-weeks'] as const,
    queryFn: async () => {
      const response = await get<AvailableWeeksApiResponse>('/portal/my/available-weeks');
      return response.weeks || [];
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  });
}

/**
 * Fetch list of faculty members for targeted swap requests
 */
export function useFacultyMembers(
  options?: Omit<UseQueryOptions<Array<{ id: string; name: string }>, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Array<{ id: string; name: string }>, ApiError>({
    queryKey: ['swaps', 'faculty-members'] as const,
    queryFn: async () => {
      const response = await get<FacultyListApiResponse>('/portal/faculty');
      return response.faculty || [];
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
 * Create a new swap request
 */
export function useCreateSwapRequest() {
  const queryClient = useQueryClient();

  return useMutation<CreateSwapResponse, ApiError, CreateSwapRequest>({
    mutationFn: async (request: CreateSwapRequest) => {
      const response = await post<CreateSwapApiResponse>('/portal/my/swaps', {
        week_to_offload: request.weekToOffload,
        preferred_target_faculty_id: request.preferredTargetFacultyId,
        reason: request.reason,
        auto_find_candidates: request.autoFindCandidates ?? true,
      });

      return {
        success: response.success,
        requestId: response.request_id,
        message: response.message,
        candidatesNotified: response.candidates_notified ?? 0,
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
    mutationFn: async ({ notes }: { notes?: string }) => {
      const response = await post<SwapRespondApiResponse>(`/portal/my/swaps/${swapId}/respond`, {
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
    mutationFn: async ({ notes }: { notes?: string }) => {
      const response = await post<SwapRespondApiResponse>(`/portal/my/swaps/${swapId}/respond`, {
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
      const response = await post<SwapRespondApiResponse>(`/portal/my/swaps/${swapId}/respond`, {
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
