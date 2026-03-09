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
  sourceFacultyId: string;
  sourceFaculty?: { name: string };
  sourceWeek: string;
  targetFacultyId?: string;
  targetFaculty?: { name: string };
  targetWeek?: string;
  swapType: string;
  status: string;
  requestedAt: string;
  requestedById: string;
  approvedAt?: string;
  approvedById?: string;
  executedAt?: string;
  executedById?: string;
  reason?: string;
  notes?: string;
}

interface MarketplaceEntryApiResponse {
  requestId: string;
  requestingFacultyName: string;
  weekAvailable: string;
  reason?: string;
  postedAt: string;
  expiresAt?: string;
  isCompatible?: boolean;
}

interface MarketplaceApiResponse {
  entries: MarketplaceEntryApiResponse[];
  total: number;
  myPostings: number;
}

interface MySwapsApiResponse {
  incomingRequests: SwapRequestApiResponse[];
  outgoingRequests: SwapRequestApiResponse[];
  recentSwaps: SwapRequestApiResponse[];
}

interface FacultyPreferenceApiResponse {
  facultyId: string;
  preferredWeeks?: string[];
  blockedWeeks?: string[];
  maxWeeksPerMonth?: number;
  maxConsecutiveWeeks?: number;
  minGapBetweenWeeks?: number;
  targetWeeksPerYear?: number;
  notifySwapRequests?: boolean;
  notifyScheduleChanges?: boolean;
  notifyConflictAlerts?: boolean;
  notifyReminderDays?: number;
  notes?: string;
  updatedAt: string;
}

interface CreateSwapApiResponse {
  success: boolean;
  requestId: string;
  message: string;
  candidatesNotified?: number;
}

interface SwapRespondApiResponse {
  success: boolean;
  message: string;
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
  const isIncoming = backendSwap.targetFacultyId === currentUserId;
  const isOutgoing = backendSwap.sourceFacultyId === currentUserId;

  return {
    id: backendSwap.id,
    sourceFacultyId: backendSwap.sourceFacultyId,
    sourceFacultyName: backendSwap.sourceFaculty?.name || 'Unknown',
    sourceWeek: backendSwap.sourceWeek,
    targetFacultyId: backendSwap.targetFacultyId,
    targetFacultyName: backendSwap.targetFaculty?.name,
    targetWeek: backendSwap.targetWeek,
    swapType: backendSwap.swapType as SwapType,
    status: backendSwap.status as SwapStatus,
    requestedAt: backendSwap.requestedAt,
    requestedById: backendSwap.requestedById,
    approvedAt: backendSwap.approvedAt,
    approvedById: backendSwap.approvedById,
    executedAt: backendSwap.executedAt,
    executedById: backendSwap.executedById,
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
    requestId: entry.requestId,
    requestingFacultyName: entry.requestingFacultyName,
    weekAvailable: entry.weekAvailable,
    reason: entry.reason,
    postedAt: entry.postedAt,
    expiresAt: entry.expiresAt,
    isCompatible: entry.isCompatible ?? false,
  };
}

/**
 * Transform faculty preference from backend
 */
function transformFacultyPreference(pref: FacultyPreferenceApiResponse): FacultyPreference {
  return {
    facultyId: pref.facultyId,
    preferredWeeks: pref.preferredWeeks || [],
    blockedWeeks: pref.blockedWeeks || [],
    maxWeeksPerMonth: pref.maxWeeksPerMonth || 0,
    maxConsecutiveWeeks: pref.maxConsecutiveWeeks || 0,
    minGapBetweenWeeks: pref.minGapBetweenWeeks || 0,
    targetWeeksPerYear: pref.targetWeeksPerYear || 0,
    notifySwapRequests: pref.notifySwapRequests ?? false,
    notifyScheduleChanges: pref.notifyScheduleChanges ?? false,
    notifyConflictAlerts: pref.notifyConflictAlerts ?? false,
    notifyReminderDays: pref.notifyReminderDays || 0,
    notes: pref.notes,
    updatedAt: pref.updatedAt,
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
        myPostings: response.myPostings,
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
        incomingRequests: response.incomingRequests.map((req: SwapRequestApiResponse) =>
          transformSwapRequest(req, currentUserId)
        ),
        outgoingRequests: response.outgoingRequests.map((req: SwapRequestApiResponse) =>
          transformSwapRequest(req, currentUserId)
        ),
        recentSwaps: response.recentSwaps.map((req: SwapRequestApiResponse) =>
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
 * Fetch available weeks for the current user to swap.
 *
 * Derives data from the existing /portal/my/schedule endpoint, which returns
 * FMIT weeks with conflict and swap-eligibility metadata. Only weeks where
 * canRequestSwap is true are included.
 */
export function useAvailableWeeks(
  options?: Omit<UseQueryOptions<Array<{ date: string; hasConflict: boolean }>, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Array<{ date: string; hasConflict: boolean }>, ApiError>({
    queryKey: ['swaps', 'available-weeks'] as const,
    queryFn: async () => {
      const response = await get<{
        fmitWeeks: Array<{
          weekStart: string;
          hasConflict: boolean;
          canRequestSwap: boolean;
        }>;
      }>('/portal/my/schedule');
      return (response.fmitWeeks || [])
        .filter((w) => w.canRequestSwap)
        .map((w) => ({ date: w.weekStart, hasConflict: w.hasConflict }));
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  });
}

/**
 * Fetch list of faculty members for targeted swap requests.
 *
 * Uses the existing /people/faculty endpoint which returns PersonListResponse
 * with items containing id and name.
 */
export function useFacultyMembers(
  options?: Omit<UseQueryOptions<Array<{ id: string; name: string }>, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Array<{ id: string; name: string }>, ApiError>({
    queryKey: ['swaps', 'faculty-members'] as const,
    queryFn: async () => {
      const response = await get<{ items: Array<{ id: string; name: string }>; total: number }>('/people/faculty');
      return (response.items || []).map((p) => ({ id: p.id, name: p.name }));
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
        weekToOffload: request.weekToOffload,
        preferredTargetFacultyId: request.preferredTargetFacultyId,
        reason: request.reason,
        autoFindCandidates: request.autoFindCandidates ?? true,
      });

      return {
        success: response.success,
        requestId: response.requestId,
        message: response.message,
        candidatesNotified: response.candidatesNotified ?? 0,
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
