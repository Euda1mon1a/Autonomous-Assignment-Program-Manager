/**
 * Tests for Swap Marketplace React Query Hooks
 *
 * Tests data fetching, mutations, and cache management
 */

import { renderHook, waitFor } from '@/test-utils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as api from '@/lib/api';
import {
  useSwapMarketplace,
  useMySwapRequests,
  useFacultyPreferences,
  useAvailableWeeks,
  useFacultyMembers,
  useCreateSwapRequest,
  useAcceptSwap,
  useRejectSwap,
  useCancelSwap,
  swapQueryKeys,
} from '@/features/swap-marketplace/hooks';
import { SwapStatus, SwapFilters } from '@/features/swap-marketplace/types';
import React from 'react';

// Mock the API module
jest.mock('@/lib/api');

// Create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('Swap Marketplace Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useSwapMarketplace', () => {
    it('should fetch marketplace data successfully', async () => {
      const mockData = {
        entries: [
          {
            request_id: 'swap-1',
            requesting_faculty_name: 'Dr. Smith',
            week_available: '2025-01-15',
            reason: 'Conference',
            posted_at: '2025-01-10T10:00:00Z',
            is_compatible: true,
          },
        ],
        total: 1,
        my_postings: 0,
      };

      (api.get as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useSwapMarketplace(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual({
        entries: [
          {
            requestId: 'swap-1',
            requestingFacultyName: 'Dr. Smith',
            weekAvailable: '2025-01-15',
            reason: 'Conference',
            postedAt: '2025-01-10T10:00:00Z',
            expiresAt: undefined,
            isCompatible: true,
          },
        ],
        total: 1,
        myPostings: 0,
      });
    });

    it('should pass filters to API call', async () => {
      const filters: SwapFilters = {
        statuses: [SwapStatus.PENDING],
        searchQuery: 'Dr. Smith',
      };

      (api.get as jest.Mock).mockResolvedValue({
        entries: [],
        total: 0,
        my_postings: 0,
      });

      renderHook(() => useSwapMarketplace(filters), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith('/portal/marketplace');
      });
    });

    it('should handle API errors', async () => {
      const error = new Error('Failed to fetch marketplace');
      (api.get as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useSwapMarketplace(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
    });

    it('should use correct query key', () => {
      const filters: SwapFilters = { searchQuery: 'test' };
      const expectedKey = swapQueryKeys.marketplace(filters);

      expect(expectedKey).toEqual(['swaps', 'marketplace', filters]);
    });
  });

  describe('useMySwapRequests', () => {
    it('should fetch my swaps data successfully', async () => {
      const mockData = {
        incoming_requests: [
          {
            id: 'swap-1',
            source_faculty_id: 'faculty-1',
            source_faculty: { name: 'Dr. Smith' },
            source_week: '2025-01-15',
            target_faculty_id: 'user-1',
            target_faculty: { name: 'Dr. Doe' },
            target_week: '2025-01-22',
            swap_type: 'one_to_one',
            status: 'pending',
            requested_at: '2025-01-10T10:00:00Z',
            reason: 'Conference',
          },
        ],
        outgoing_requests: [],
        recent_swaps: [],
      };

      (api.get as jest.Mock).mockResolvedValue(mockData);

      // Pass currentUserId to properly compute isIncoming/canAccept
      const { result } = renderHook(() => useMySwapRequests('user-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.incomingRequests).toHaveLength(1);
      expect(result.current.data?.incomingRequests[0].sourceFacultyName).toBe('Dr. Smith');
      expect(result.current.data?.incomingRequests[0].isIncoming).toBe(true);
      expect(result.current.data?.incomingRequests[0].canAccept).toBe(true);
    });

    it('should handle API errors', async () => {
      const error = new Error('Failed to fetch swap requests');
      (api.get as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useMySwapRequests(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
    });
  });

  describe('useFacultyPreferences', () => {
    it('should fetch faculty preferences successfully', async () => {
      const mockPrefs = {
        faculty_id: 'faculty-1',
        preferred_weeks: ['2025-01-01'],
        blocked_weeks: ['2025-12-25'],
        max_weeks_per_month: 4,
        max_consecutive_weeks: 2,
        min_gap_between_weeks: 7,
        target_weeks_per_year: 48,
        notify_swap_requests: true,
        notify_schedule_changes: true,
        notify_conflict_alerts: true,
        notify_reminder_days: 7,
        notes: 'Prefer weekdays',
        updated_at: '2025-01-01T00:00:00Z',
      };

      (api.get as jest.Mock).mockResolvedValue(mockPrefs);

      const { result } = renderHook(() => useFacultyPreferences(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.facultyId).toBe('faculty-1');
      expect(result.current.data?.maxWeeksPerMonth).toBe(4);
    });
  });

  describe('useAvailableWeeks', () => {
    it('should fetch available weeks successfully', async () => {
      const mockWeeks = {
        weeks: [
          { date: '2025-01-15', hasConflict: false },
          { date: '2025-02-01', hasConflict: true },
        ],
      };

      (api.get as jest.Mock).mockResolvedValue(mockWeeks);

      const { result } = renderHook(() => useAvailableWeeks(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockWeeks.weeks);
    });

    it('should handle empty weeks array', async () => {
      (api.get as jest.Mock).mockResolvedValue({ weeks: [] });

      const { result } = renderHook(() => useAvailableWeeks(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual([]);
    });
  });

  describe('useFacultyMembers', () => {
    it('should fetch faculty members successfully', async () => {
      const mockFaculty = {
        faculty: [
          { id: 'faculty-1', name: 'Dr. Smith' },
          { id: 'faculty-2', name: 'Dr. Doe' },
        ],
      };

      (api.get as jest.Mock).mockResolvedValue(mockFaculty);

      const { result } = renderHook(() => useFacultyMembers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockFaculty.faculty);
    });
  });

  describe('useCreateSwapRequest', () => {
    it('should create swap request successfully', async () => {
      const mockResponse = {
        success: true,
        request_id: 'swap-new',
        message: 'Request created',
        candidates_notified: 5,
      };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useCreateSwapRequest(), {
        wrapper: createWrapper(),
      });

      const request = {
        weekToOffload: '2025-01-15',
        reason: 'Conference',
        autoFindCandidates: true,
      };

      let response: any;
      await waitFor(async () => {
        response = await result.current.mutateAsync(request);
      });

      expect(api.post).toHaveBeenCalledWith('/portal/my/swaps', {
        week_to_offload: '2025-01-15',
        preferred_target_faculty_id: undefined,
        reason: 'Conference',
        auto_find_candidates: true,
      });

      expect(response).toEqual({
        success: true,
        requestId: 'swap-new',
        message: 'Request created',
        candidatesNotified: 5,
      });
    });

    it('should handle creation errors', async () => {
      const error = new Error('Failed to create request');
      (api.post as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useCreateSwapRequest(), {
        wrapper: createWrapper(),
      });

      const request = {
        weekToOffload: '2025-01-15',
        autoFindCandidates: true,
      };

      try {
        await result.current.mutateAsync(request);
      } catch (e) {
        expect(e).toEqual(error);
      }
    });

    it('should invalidate queries after successful creation', async () => {
      const mockResponse = {
        success: true,
        request_id: 'swap-new',
        message: 'Request created',
        candidates_notified: 5,
      };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });

      const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      );

      const { result } = renderHook(() => useCreateSwapRequest(), { wrapper });

      await waitFor(async () => {
        await result.current.mutateAsync({
          weekToOffload: '2025-01-15',
          autoFindCandidates: true,
        });
      });

      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: swapQueryKeys.mySwaps() });
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: swapQueryKeys.marketplace() });
    });
  });

  describe('useAcceptSwap', () => {
    it('should accept swap request successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Swap accepted',
      };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useAcceptSwap('swap-1'), {
        wrapper: createWrapper(),
      });

      let response: any;
      await waitFor(async () => {
        response = await result.current.mutateAsync({ notes: 'Happy to help' });
      });

      expect(api.post).toHaveBeenCalledWith('/portal/my/swaps/swap-1/respond', {
        accept: true,
        notes: 'Happy to help',
      });

      expect(response).toEqual({
        success: true,
        message: 'Swap accepted',
      });
    });

    it('should accept without notes', async () => {
      const mockResponse = {
        success: true,
        message: 'Swap accepted',
      };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useAcceptSwap('swap-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(async () => {
        await result.current.mutateAsync({});
      });

      expect(api.post).toHaveBeenCalledWith('/portal/my/swaps/swap-1/respond', {
        accept: true,
        notes: undefined,
      });
    });
  });

  describe('useRejectSwap', () => {
    it('should reject swap request successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Swap rejected',
      };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useRejectSwap('swap-1'), {
        wrapper: createWrapper(),
      });

      let response: any;
      await waitFor(async () => {
        response = await result.current.mutateAsync({ notes: 'Conflict that week' });
      });

      expect(api.post).toHaveBeenCalledWith('/portal/my/swaps/swap-1/respond', {
        accept: false,
        notes: 'Conflict that week',
      });

      expect(response).toEqual({
        success: true,
        message: 'Swap rejected',
      });
    });
  });

  describe('useCancelSwap', () => {
    it('should cancel swap request successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Swap cancelled',
      };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useCancelSwap('swap-1'), {
        wrapper: createWrapper(),
      });

      let response: any;
      await waitFor(async () => {
        response = await result.current.mutateAsync();
      });

      expect(api.post).toHaveBeenCalledWith('/portal/my/swaps/swap-1/respond', {
        accept: false,
        notes: 'Request cancelled by requester',
      });

      expect(response).toEqual({
        success: true,
        message: 'Swap cancelled',
      });
    });
  });

  describe('Query Keys', () => {
    it('should generate correct query key for all swaps', () => {
      expect(swapQueryKeys.all).toEqual(['swaps']);
    });

    it('should generate correct query key for marketplace without filters', () => {
      expect(swapQueryKeys.marketplace()).toEqual(['swaps', 'marketplace', undefined]);
    });

    it('should generate correct query key for marketplace with filters', () => {
      const filters: SwapFilters = { searchQuery: 'test' };
      expect(swapQueryKeys.marketplace(filters)).toEqual(['swaps', 'marketplace', filters]);
    });

    it('should generate correct query key for my swaps', () => {
      expect(swapQueryKeys.mySwaps()).toEqual(['swaps', 'my-swaps']);
    });

    it('should generate correct query key for specific swap request', () => {
      expect(swapQueryKeys.swapRequest('swap-1')).toEqual(['swaps', 'request', 'swap-1']);
    });

    it('should generate correct query key for preferences', () => {
      expect(swapQueryKeys.preferences()).toEqual(['swaps', 'preferences']);
    });
  });
});
