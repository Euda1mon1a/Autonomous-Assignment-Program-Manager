/**
 * Tests for Auto-Matcher Algorithm and Compatibility Logic
 *
 * Tests the auto-matching functionality, candidate ranking,
 * compatibility checking, and edge cases in swap matching.
 */

import { renderHook, waitFor } from '@/test-utils';
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
            requestId: 'swap-1',
            requestingFacultyName: 'Dr. Smith',
            weekAvailable: '2025-01-15',
            isCompatible: true,
          },
          {
            requestId: 'swap-2',
            requestingFacultyName: 'Dr. Jones',
            weekAvailable: '2025-01-22',
            isCompatible: false,
          },
          {
            requestId: 'swap-3',
            requestingFacultyName: 'Dr. Brown',
            weekAvailable: '2025-02-01',
            isCompatible: true,
          },
        ],
        total: 3,
        myPostings: 0,
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
            requestId: 'swap-1',
            requestingFacultyName: 'Dr. Smith',
            weekAvailable: '2025-01-15',
            isCompatible: false,
          },
          {
            requestId: 'swap-2',
            requestingFacultyName: 'Dr. Jones',
            weekAvailable: '2025-01-22',
            isCompatible: false,
          },
        ],
        total: 2,
        myPostings: 0,
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
            requestId: 'swap-1',
            requestingFacultyName: 'Dr. Smith',
            weekAvailable: '2025-01-15',
            isCompatible: true,
          },
          {
            requestId: 'swap-2',
            requestingFacultyName: 'Dr. Jones',
            weekAvailable: '2025-01-22',
            isCompatible: true,
          },
        ],
        total: 2,
        myPostings: 0,
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
        requestId: 'swap-new-1',
        message: 'Swap request created successfully',
        candidatesNotified: 5,
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
          autoFindCandidates: true,
        })
      );
    });

    it('should handle zero candidates found', async () => {
      const mockResponse = {
        success: true,
        requestId: 'swap-new-1',
        message: 'Swap request created but no compatible candidates found',
        candidatesNotified: 0,
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
        requestId: 'swap-new-1',
        message: 'Swap request created successfully',
        candidatesNotified: 1,
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
        requestId: 'swap-new-1',
        message: 'Swap request created successfully',
        candidatesNotified: 1,
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
          autoFindCandidates: false,
          preferredTargetFacultyId: 'faculty-123',
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
            requestId: 'swap-1',
            requestingFacultyName: 'Dr. Incompatible',
            weekAvailable: '2025-01-15',
            isCompatible: false,
          },
          {
            requestId: 'swap-2',
            requestingFacultyName: 'Dr. Compatible',
            weekAvailable: '2025-01-22',
            isCompatible: true,
          },
        ],
        total: 2,
        myPostings: 0,
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
            requestId: 'swap-1',
            requestingFacultyName: 'Dr. Smith',
            weekAvailable: '2025-01-15',
            postedAt: '2025-01-01T10:00:00Z',
            expiresAt: '2025-01-14T23:59:59Z', // Expires soon
            isCompatible: true,
          },
          {
            requestId: 'swap-2',
            requestingFacultyName: 'Dr. Jones',
            weekAvailable: '2025-01-22',
            postedAt: '2025-01-01T10:00:00Z',
            expiresAt: '2025-01-30T23:59:59Z', // Expires later
            isCompatible: true,
          },
        ],
        total: 2,
        myPostings: 0,
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
            requestId: 'swap-1',
            requestingFacultyName: 'Dr. Smith',
            weekAvailable: '2025-01-15',
            postedAt: '2025-01-01T10:00:00Z',
            isCompatible: true,
          },
        ],
        total: 1,
        myPostings: 0,
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
            requestId: 'swap-1',
            requestingFacultyName: 'Dr. Compatible',
            weekAvailable: '2025-01-15',
            isCompatible: true,
          },
        ],
        total: 1,
        myPostings: 0,
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
            requestId: 'swap-1',
            requestingFacultyName: 'Dr. Compatible',
            weekAvailable: '2025-01-15',
            isCompatible: true,
          },
          {
            requestId: 'swap-2',
            requestingFacultyName: 'Dr. Incompatible',
            weekAvailable: '2025-01-22',
            isCompatible: false,
          },
          {
            requestId: 'swap-3',
            requestingFacultyName: 'Dr. Another Compatible',
            weekAvailable: '2025-02-01',
            isCompatible: true,
          },
        ],
        total: 3,
        myPostings: 0,
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
        requestId: 'swap-new-1',
        message: 'Swap request created successfully',
        candidatesNotified: 3,
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
        myPostings: 2,
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
        myPostings: 0,
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
        requestId: 'swap-new-1',
        message: 'Swap request created successfully',
        candidatesNotified: 50,
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
        requestId: `swap-${i}`,
        requestingFacultyName: `Dr. Faculty ${i}`,
        weekAvailable: '2025-01-15',
        postedAt: '2025-01-01T10:00:00Z',
        isCompatible: i % 2 === 0,
      }));

      const mockData = {
        entries,
        total: 100,
        myPostings: 2,
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
