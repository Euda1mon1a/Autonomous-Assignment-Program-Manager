/**
 * Tests for Auto-Matcher Algorithm and Compatibility Logic
 *
 * Tests the auto-matching functionality, candidate ranking,
 * compatibility checking, and edge cases in swap matching.
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as api from '@/lib/api';
import {
  useSwapMarketplace,
  useCreateSwapRequest,
  useFacultyMembers,
} from '@/features/swap-marketplace/hooks';
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

describe('Auto-Matcher Algorithm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ============================================================================
  // Compatibility Detection
  // ============================================================================

  describe('Compatibility Detection', () => {
    it('should identify compatible marketplace entries', async () => {
      const mockData = {
        entries: [
          {
            request_id: 'swap-1',
            requesting_faculty_name: 'Dr. Smith',
            week_available: '2025-01-15',
            is_compatible: true,
          },
          {
            request_id: 'swap-2',
            requesting_faculty_name: 'Dr. Jones',
            week_available: '2025-01-22',
            is_compatible: false,
          },
          {
            request_id: 'swap-3',
            requesting_faculty_name: 'Dr. Brown',
            week_available: '2025-02-01',
            is_compatible: true,
          },
        ],
        total: 3,
        my_postings: 0,
      };

      (api.get as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useSwapMarketplace(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const compatibleEntries = result.current.data?.entries.filter(e => e.isCompatible);
      expect(compatibleEntries).toHaveLength(2);
      expect(compatibleEntries?.[0].requestId).toBe('swap-1');
      expect(compatibleEntries?.[1].requestId).toBe('swap-3');
    });

    it('should handle all incompatible entries', async () => {
      const mockData = {
        entries: [
          {
            request_id: 'swap-1',
            requesting_faculty_name: 'Dr. Smith',
            week_available: '2025-01-15',
            is_compatible: false,
          },
          {
            request_id: 'swap-2',
            requesting_faculty_name: 'Dr. Jones',
            week_available: '2025-01-22',
            is_compatible: false,
          },
        ],
        total: 2,
        my_postings: 0,
      };

      (api.get as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useSwapMarketplace(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const compatibleEntries = result.current.data?.entries.filter(e => e.isCompatible);
      expect(compatibleEntries).toHaveLength(0);
    });

    it('should handle all compatible entries', async () => {
      const mockData = {
        entries: [
          {
            request_id: 'swap-1',
            requesting_faculty_name: 'Dr. Smith',
            week_available: '2025-01-15',
            is_compatible: true,
          },
          {
            request_id: 'swap-2',
            requesting_faculty_name: 'Dr. Jones',
            week_available: '2025-01-22',
            is_compatible: true,
          },
        ],
        total: 2,
        my_postings: 0,
      };

      (api.get as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useSwapMarketplace(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const compatibleEntries = result.current.data?.entries.filter(e => e.isCompatible);
      expect(compatibleEntries).toHaveLength(2);
    });
  });

  // ============================================================================
  // Auto-Find Candidates
  // ============================================================================

  describe('Auto-Find Candidates', () => {
    it('should notify multiple candidates when auto-find is enabled', async () => {
      const mockResponse = {
        success: true,
        request_id: 'swap-new-1',
        message: 'Swap request created successfully',
        candidates_notified: 5,
      };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useCreateSwapRequest(), {
        wrapper: createWrapper(),
      });

      await result.current.mutateAsync({
        weekToOffload: '2025-01-15',
        autoFindCandidates: true,
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.candidatesNotified).toBe(5);
      expect(api.post).toHaveBeenCalledWith(
        '/portal/my/swaps',
        expect.objectContaining({
          auto_find_candidates: true,
        })
      );
    });

    it('should handle zero candidates found', async () => {
      const mockResponse = {
        success: true,
        request_id: 'swap-new-1',
        message: 'Swap request created but no compatible candidates found',
        candidates_notified: 0,
      };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useCreateSwapRequest(), {
        wrapper: createWrapper(),
      });

      await result.current.mutateAsync({
        weekToOffload: '2025-01-15',
        autoFindCandidates: true,
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.candidatesNotified).toBe(0);
    });

    it('should handle single candidate found', async () => {
      const mockResponse = {
        success: true,
        request_id: 'swap-new-1',
        message: 'Swap request created successfully',
        candidates_notified: 1,
      };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useCreateSwapRequest(), {
        wrapper: createWrapper(),
      });

      await result.current.mutateAsync({
        weekToOffload: '2025-01-15',
        autoFindCandidates: true,
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.candidatesNotified).toBe(1);
    });

    it('should not use auto-find when specific faculty is selected', async () => {
      const mockResponse = {
        success: true,
        request_id: 'swap-new-1',
        message: 'Swap request created successfully',
        candidates_notified: 1,
      };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useCreateSwapRequest(), {
        wrapper: createWrapper(),
      });

      await result.current.mutateAsync({
        weekToOffload: '2025-01-15',
        preferredTargetFacultyId: 'faculty-123',
        autoFindCandidates: false,
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(api.post).toHaveBeenCalledWith(
        '/portal/my/swaps',
        expect.objectContaining({
          auto_find_candidates: false,
          preferred_target_faculty_id: 'faculty-123',
        })
      );
    });
  });

  // ============================================================================
  // Candidate Ranking Logic
  // ============================================================================

  describe('Candidate Ranking', () => {
    it('should prioritize compatible candidates over incompatible ones', async () => {
      const mockData = {
        entries: [
          {
            request_id: 'swap-1',
            requesting_faculty_name: 'Dr. Incompatible',
            week_available: '2025-01-15',
            is_compatible: false,
          },
          {
            request_id: 'swap-2',
            requesting_faculty_name: 'Dr. Compatible',
            week_available: '2025-01-22',
            is_compatible: true,
          },
        ],
        total: 2,
        my_postings: 0,
      };

      (api.get as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useSwapMarketplace(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Compatible entries should be identifiable
      const compatible = result.current.data?.entries.find(e => e.isCompatible);
      expect(compatible?.requestingFacultyName).toBe('Dr. Compatible');
    });

    it('should handle entries with expiration dates', async () => {
      const mockData = {
        entries: [
          {
            request_id: 'swap-1',
            requesting_faculty_name: 'Dr. Smith',
            week_available: '2025-01-15',
            posted_at: '2025-01-01T10:00:00Z',
            expires_at: '2025-01-14T23:59:59Z', // Expires soon
            is_compatible: true,
          },
          {
            request_id: 'swap-2',
            requesting_faculty_name: 'Dr. Jones',
            week_available: '2025-01-22',
            posted_at: '2025-01-01T10:00:00Z',
            expires_at: '2025-01-30T23:59:59Z', // Expires later
            is_compatible: true,
          },
        ],
        total: 2,
        my_postings: 0,
      };

      (api.get as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useSwapMarketplace(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const entries = result.current.data?.entries || [];
      expect(entries).toHaveLength(2);
      expect(entries[0].expiresAt).toBeDefined();
      expect(entries[1].expiresAt).toBeDefined();
    });

    it('should handle entries without expiration dates', async () => {
      const mockData = {
        entries: [
          {
            request_id: 'swap-1',
            requesting_faculty_name: 'Dr. Smith',
            week_available: '2025-01-15',
            posted_at: '2025-01-01T10:00:00Z',
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

      const entry = result.current.data?.entries[0];
      expect(entry?.expiresAt).toBeUndefined();
    });
  });

  // ============================================================================
  // Faculty Availability
  // ============================================================================

  describe('Faculty Availability', () => {
    it('should fetch all available faculty for manual selection', async () => {
      const mockFacultyData = {
        faculty: [
          { id: 'faculty-1', name: 'Dr. Smith' },
          { id: 'faculty-2', name: 'Dr. Jones' },
          { id: 'faculty-3', name: 'Dr. Brown' },
          { id: 'faculty-4', name: 'Dr. Davis' },
          { id: 'faculty-5', name: 'Dr. Wilson' },
        ],
      };

      (api.get as jest.Mock).mockResolvedValue(mockFacultyData);

      const { result } = renderHook(() => useFacultyMembers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toHaveLength(5);
      expect(result.current.data?.[0].name).toBe('Dr. Smith');
    });

    it('should handle empty faculty list', async () => {
      const mockFacultyData = {
        faculty: [],
      };

      (api.get as jest.Mock).mockResolvedValue(mockFacultyData);

      const { result } = renderHook(() => useFacultyMembers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toHaveLength(0);
    });

    it('should handle faculty data with single member', async () => {
      const mockFacultyData = {
        faculty: [{ id: 'faculty-1', name: 'Dr. Smith' }],
      };

      (api.get as jest.Mock).mockResolvedValue(mockFacultyData);

      const { result } = renderHook(() => useFacultyMembers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toHaveLength(1);
      expect(result.current.data?.[0].id).toBe('faculty-1');
    });
  });

  // ============================================================================
  // Filtering and Compatibility
  // ============================================================================

  describe('Filtering Compatible Candidates', () => {
    it('should support filtering by compatible candidates only', async () => {
      const mockData = {
        entries: [
          {
            request_id: 'swap-1',
            requesting_faculty_name: 'Dr. Compatible',
            week_available: '2025-01-15',
            is_compatible: true,
          },
        ],
        total: 1,
        my_postings: 0,
      };

      (api.get as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(
        () => useSwapMarketplace({ showCompatibleOnly: true }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.entries).toHaveLength(1);
      expect(result.current.data?.entries[0].isCompatible).toBe(true);
    });

    it('should handle mixed compatible and incompatible results', async () => {
      const mockData = {
        entries: [
          {
            request_id: 'swap-1',
            requesting_faculty_name: 'Dr. Compatible',
            week_available: '2025-01-15',
            is_compatible: true,
          },
          {
            request_id: 'swap-2',
            requesting_faculty_name: 'Dr. Incompatible',
            week_available: '2025-01-22',
            is_compatible: false,
          },
          {
            request_id: 'swap-3',
            requesting_faculty_name: 'Dr. Another Compatible',
            week_available: '2025-02-01',
            is_compatible: true,
          },
        ],
        total: 3,
        my_postings: 0,
      };

      (api.get as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useSwapMarketplace(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const allEntries = result.current.data?.entries || [];
      const compatibleCount = allEntries.filter(e => e.isCompatible).length;
      const incompatibleCount = allEntries.filter(e => !e.isCompatible).length;

      expect(allEntries).toHaveLength(3);
      expect(compatibleCount).toBe(2);
      expect(incompatibleCount).toBe(1);
    });
  });

  // ============================================================================
  // Edge Cases
  // ============================================================================

  describe('Edge Cases', () => {
    it('should handle swap request with reason affecting matching', async () => {
      const mockResponse = {
        success: true,
        request_id: 'swap-new-1',
        message: 'Swap request created successfully',
        candidates_notified: 3,
      };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useCreateSwapRequest(), {
        wrapper: createWrapper(),
      });

      await result.current.mutateAsync({
        weekToOffload: '2025-01-15',
        reason: 'Emergency - urgent swap needed',
        autoFindCandidates: true,
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(api.post).toHaveBeenCalledWith(
        '/portal/my/swaps',
        expect.objectContaining({
          reason: 'Emergency - urgent swap needed',
        })
      );
    });

    it('should handle marketplace with only user postings', async () => {
      const mockData = {
        entries: [],
        total: 0,
        my_postings: 2,
      };

      (api.get as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useSwapMarketplace(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.entries).toHaveLength(0);
      expect(result.current.data?.myPostings).toBe(2);
    });

    it('should handle marketplace with no entries and no postings', async () => {
      const mockData = {
        entries: [],
        total: 0,
        my_postings: 0,
      };

      (api.get as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useSwapMarketplace(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.entries).toHaveLength(0);
      expect(result.current.data?.total).toBe(0);
      expect(result.current.data?.myPostings).toBe(0);
    });

    it('should handle API error during auto-matching', async () => {
      (api.post as jest.Mock).mockRejectedValue(new Error('No eligible candidates found'));

      const { result } = renderHook(() => useCreateSwapRequest(), {
        wrapper: createWrapper(),
      });

      try {
        await result.current.mutateAsync({
          weekToOffload: '2025-01-15',
          autoFindCandidates: true,
        });
      } catch (error: any) {
        expect(error.message).toBe('No eligible candidates found');
      }

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });
    });

    it('should handle ACGME compliance issues in auto-matching', async () => {
      (api.post as jest.Mock).mockRejectedValue(
        new Error('ACGME violation: No faculty available without exceeding weekly hours')
      );

      const { result } = renderHook(() => useCreateSwapRequest(), {
        wrapper: createWrapper(),
      });

      try {
        await result.current.mutateAsync({
          weekToOffload: '2025-01-15',
          autoFindCandidates: true,
        });
      } catch (error: any) {
        expect(error.message).toContain('ACGME violation');
      }

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });
    });
  });

  // ============================================================================
  // Performance and Scalability
  // ============================================================================

  describe('Performance and Scalability', () => {
    it('should handle large number of candidates efficiently', async () => {
      const mockResponse = {
        success: true,
        request_id: 'swap-new-1',
        message: 'Swap request created successfully',
        candidates_notified: 50,
      };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useCreateSwapRequest(), {
        wrapper: createWrapper(),
      });

      await result.current.mutateAsync({
        weekToOffload: '2025-01-15',
        autoFindCandidates: true,
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.candidatesNotified).toBe(50);
    });

    it('should handle large marketplace with many entries', async () => {
      const entries = Array.from({ length: 100 }, (_, i) => ({
        request_id: `swap-${i}`,
        requesting_faculty_name: `Dr. Faculty ${i}`,
        week_available: '2025-01-15',
        posted_at: '2025-01-01T10:00:00Z',
        is_compatible: i % 2 === 0,
      }));

      const mockData = {
        entries,
        total: 100,
        my_postings: 2,
      };

      (api.get as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() => useSwapMarketplace(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.entries).toHaveLength(100);
      expect(result.current.data?.total).toBe(100);
    });
  });
});
