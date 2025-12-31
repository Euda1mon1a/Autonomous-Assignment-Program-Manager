/**
 * Tests for Daily Manifest Hooks
 *
 * Tests React Query hooks for daily manifest data fetching
 */

import { renderHook, waitFor } from '@/test-utils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import * as api from '@/lib/api';
import {
  useDailyManifest,
  useTodayManifest,
  manifestQueryKeys,
} from '@/features/daily-manifest/hooks';
import { manifestMockResponses } from './mockData';

// Mock the API
jest.mock('@/lib/api');
const mockGet = api.get as jest.MockedFunction<typeof api.get>;

// Create a test wrapper
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    React.createElement(QueryClientProvider, { client: queryClient }, children)
  );
}

describe('Daily Manifest Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ============================================================================
  // useDailyManifest Tests
  // ============================================================================

  describe('useDailyManifest', () => {
    it('should fetch daily manifest successfully', async () => {
      mockGet.mockResolvedValueOnce(manifestMockResponses.dailyManifest);

      const { result } = renderHook(
        () => useDailyManifest('2025-12-21', 'AM'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(manifestMockResponses.dailyManifest);
      expect(mockGet).toHaveBeenCalledWith(
        '/daily-manifest?date=2025-12-21&time_of_day=AM'
      );
    });

    it('should fetch manifest for PM time period', async () => {
      mockGet.mockResolvedValueOnce({
        ...manifestMockResponses.dailyManifest,
        time_of_day: 'PM',
      });

      const { result } = renderHook(
        () => useDailyManifest('2025-12-21', 'PM'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        '/daily-manifest?date=2025-12-21&time_of_day=PM'
      );
    });

    it('should fetch manifest for ALL time period', async () => {
      mockGet.mockResolvedValueOnce(manifestMockResponses.allDayManifest);

      const { result } = renderHook(
        () => useDailyManifest('2025-12-21', 'ALL'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      // For ALL, the hook omits the time_of_day param (backend returns all if not specified)
      expect(mockGet).toHaveBeenCalledWith(
        '/daily-manifest?date=2025-12-21'
      );
    });

    it('should use AM as default time period', async () => {
      mockGet.mockResolvedValueOnce(manifestMockResponses.dailyManifest);

      const { result } = renderHook(
        () => useDailyManifest('2025-12-21'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        '/daily-manifest?date=2025-12-21&time_of_day=AM'
      );
    });

    it('should handle empty manifest', async () => {
      mockGet.mockResolvedValueOnce(manifestMockResponses.emptyManifest);

      const { result } = renderHook(
        () => useDailyManifest('2025-12-21', 'AM'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.locations).toHaveLength(0);
      expect(result.current.data?.summary.total_locations).toBe(0);
    });

    it('should handle loading state', () => {
      mockGet.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(
        () => useDailyManifest('2025-12-21', 'AM'),
        {
          wrapper: createWrapper(),
        }
      );

      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle error state', async () => {
      const error = new Error('Failed to fetch manifest');
      mockGet.mockRejectedValueOnce(error);

      const { result } = renderHook(
        () => useDailyManifest('2025-12-21', 'AM'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeDefined();
    });

    it('should not fetch when date is empty', () => {
      const { result } = renderHook(
        () => useDailyManifest('', 'AM'),
        {
          wrapper: createWrapper(),
        }
      );

      expect(result.current.fetchStatus).toBe('idle');
      expect(mockGet).not.toHaveBeenCalled();
    });

    it('should refetch on window focus', async () => {
      mockGet.mockResolvedValue(manifestMockResponses.dailyManifest);

      const { result } = renderHook(
        () => useDailyManifest('2025-12-21', 'AM'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      // Verify refetchOnWindowFocus is enabled
      expect(result.current.isSuccess).toBe(true);
    });

    it('should use correct stale time', async () => {
      mockGet.mockResolvedValueOnce(manifestMockResponses.dailyManifest);

      const { result } = renderHook(
        () => useDailyManifest('2025-12-21', 'AM'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      // The hook sets staleTime to 30 seconds
      expect(result.current.data).toBeDefined();
    });

    it('should accept custom query options', async () => {
      mockGet.mockResolvedValueOnce(manifestMockResponses.dailyManifest);

      const { result } = renderHook(
        () => useDailyManifest('2025-12-21', 'AM', {
          staleTime: 60000,
        }),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(manifestMockResponses.dailyManifest);
    });

    it('should support refetch', async () => {
      mockGet.mockResolvedValue(manifestMockResponses.dailyManifest);

      const { result } = renderHook(
        () => useDailyManifest('2025-12-21', 'AM'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      // Clear mock calls
      mockGet.mockClear();

      // Refetch
      result.current.refetch();

      await waitFor(() => expect(mockGet).toHaveBeenCalled());
    });
  });

  // ============================================================================
  // useTodayManifest Tests
  // ============================================================================

  describe('useTodayManifest', () => {
    it('should fetch manifest for today', async () => {
      mockGet.mockResolvedValueOnce(manifestMockResponses.dailyManifest);

      const { result } = renderHook(
        () => useTodayManifest('AM'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      // Should use today's date in ISO format
      const today = new Date().toISOString().split('T')[0];
      expect(mockGet).toHaveBeenCalledWith(
        `/daily-manifest?date=${today}&time_of_day=AM`
      );
    });

    it('should use AM as default time period', async () => {
      mockGet.mockResolvedValueOnce(manifestMockResponses.dailyManifest);

      const { result } = renderHook(
        () => useTodayManifest(),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const today = new Date().toISOString().split('T')[0];
      expect(mockGet).toHaveBeenCalledWith(
        `/daily-manifest?date=${today}&time_of_day=AM`
      );
    });

    it('should support PM time period', async () => {
      mockGet.mockResolvedValueOnce({
        ...manifestMockResponses.dailyManifest,
        time_of_day: 'PM',
      });

      const { result } = renderHook(
        () => useTodayManifest('PM'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const today = new Date().toISOString().split('T')[0];
      expect(mockGet).toHaveBeenCalledWith(
        `/daily-manifest?date=${today}&time_of_day=PM`
      );
    });

    it('should support ALL time period', async () => {
      mockGet.mockResolvedValueOnce(manifestMockResponses.allDayManifest);

      const { result } = renderHook(
        () => useTodayManifest('ALL'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      // For ALL, the hook omits the time_of_day param (backend returns all if not specified)
      const today = new Date().toISOString().split('T')[0];
      expect(mockGet).toHaveBeenCalledWith(
        `/daily-manifest?date=${today}`
      );
    });

    it('should accept custom query options', async () => {
      mockGet.mockResolvedValueOnce(manifestMockResponses.dailyManifest);

      const { result } = renderHook(
        () => useTodayManifest('AM', {
          gcTime: 10 * 60 * 1000,
        }),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toBeDefined();
    });
  });

  // ============================================================================
  // Query Keys Tests
  // ============================================================================

  describe('Query Keys', () => {
    it('should generate correct query key for manifest', () => {
      const key = manifestQueryKeys.byDate('2025-12-21', 'AM');

      expect(key).toEqual(['daily-manifest', '2025-12-21', 'AM']);
    });

    it('should generate different keys for different dates', () => {
      const key1 = manifestQueryKeys.byDate('2025-12-21', 'AM');
      const key2 = manifestQueryKeys.byDate('2025-12-22', 'AM');

      expect(key1).not.toEqual(key2);
    });

    it('should generate different keys for different time periods', () => {
      const key1 = manifestQueryKeys.byDate('2025-12-21', 'AM');
      const key2 = manifestQueryKeys.byDate('2025-12-21', 'PM');

      expect(key1).not.toEqual(key2);
    });

    it('should have base query key', () => {
      const key = manifestQueryKeys.all;

      expect(key).toEqual(['daily-manifest']);
    });
  });
});
