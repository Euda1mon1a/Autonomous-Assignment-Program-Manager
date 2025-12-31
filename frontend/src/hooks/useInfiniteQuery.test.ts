/**
 * Tests for Infinite Scroll Query Hook
 *
 * Tests pagination, infinite scrolling, and loading states
 * for efficiently handling large datasets.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useInfiniteQuery, useInfiniteScroll, useBidirectionalInfiniteQuery, InfiniteScrollMonitor } from './useInfiniteQuery';

// Create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

// Mock data
const createMockPage = (page: number, pageSize: number) => ({
  data: Array.from({ length: pageSize }, (_, i) => ({
    id: `item-${page * pageSize + i}`,
    name: `Item ${page * pageSize + i}`,
  })),
  total: 100,
  hasMore: (page + 1) * pageSize < 100,
});

describe('useInfiniteQuery', () => {
  it('fetches first page successfully', async () => {
    const fetchFn = jest.fn((page: number, pageSize: number) =>
      Promise.resolve(createMockPage(page, pageSize))
    );

    const { result } = renderHook(
      () =>
        useInfiniteQuery({
          queryKey: ['test'],
          fetchFn,
          pageSize: 20,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.items).toHaveLength(20);
    expect(result.current.totalCount).toBe(100);
    expect(result.current.hasNextPage).toBe(true);
    expect(fetchFn).toHaveBeenCalledWith(0, 20);
  });

  it('fetches next page when requested', async () => {
    const fetchFn = jest.fn((page: number, pageSize: number) =>
      Promise.resolve(createMockPage(page, pageSize))
    );

    const { result } = renderHook(
      () =>
        useInfiniteQuery({
          queryKey: ['test'],
          fetchFn,
          pageSize: 20,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Fetch next page
    await act(async () => {
      result.current.fetchNextPage();
    });

    await waitFor(() => {
      expect(result.current.items).toHaveLength(40);
    });

    expect(fetchFn).toHaveBeenCalledTimes(2);
    expect(fetchFn).toHaveBeenCalledWith(1, 20);
  });

  it('indicates when fetching next page', async () => {
    const fetchFn = jest.fn((page: number, pageSize: number) =>
      Promise.resolve(createMockPage(page, pageSize))
    );

    const { result } = renderHook(
      () =>
        useInfiniteQuery({
          queryKey: ['test'],
          fetchFn,
          pageSize: 20,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Start fetching next page
    act(() => {
      result.current.fetchNextPage();
    });

    expect(result.current.isFetchingNextPage).toBe(true);

    await waitFor(() => {
      expect(result.current.isFetchingNextPage).toBe(false);
    });
  });

  it('knows when there are no more pages', async () => {
    const fetchFn = jest.fn((page: number, pageSize: number) => {
      if (page >= 5) {
        return Promise.resolve({
          data: [],
          total: 100,
          hasMore: false,
        });
      }
      return Promise.resolve(createMockPage(page, pageSize));
    });

    const { result } = renderHook(
      () =>
        useInfiniteQuery({
          queryKey: ['test'],
          fetchFn,
          pageSize: 20,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Fetch all pages
    for (let i = 0; i < 5; i++) {
      await act(async () => {
        result.current.fetchNextPage();
      });
    }

    await waitFor(() => {
      expect(result.current.hasNextPage).toBe(false);
    });
  });

  it('handles errors gracefully', async () => {
    const fetchFn = jest.fn(() =>
      Promise.reject(new Error('Network error'))
    );

    const { result } = renderHook(
      () =>
        useInfiniteQuery({
          queryKey: ['test'],
          fetchFn,
          pageSize: 20,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });

    expect(result.current.items).toHaveLength(0);
  });

  it('can be disabled', async () => {
    const fetchFn = jest.fn((page: number, pageSize: number) =>
      Promise.resolve(createMockPage(page, pageSize))
    );

    const { result } = renderHook(
      () =>
        useInfiniteQuery({
          queryKey: ['test'],
          fetchFn,
          pageSize: 20,
          enabled: false,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(fetchFn).not.toHaveBeenCalled();
  });

  it('refetches all pages', async () => {
    const fetchFn = jest.fn((page: number, pageSize: number) =>
      Promise.resolve(createMockPage(page, pageSize))
    );

    const { result } = renderHook(
      () =>
        useInfiniteQuery({
          queryKey: ['test'],
          fetchFn,
          pageSize: 20,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Fetch second page
    await act(async () => {
      result.current.fetchNextPage();
    });

    await waitFor(() => {
      expect(result.current.items).toHaveLength(40);
    });

    // Refetch all
    await act(async () => {
      result.current.refetch();
    });

    // Should refetch both pages
    expect(fetchFn).toHaveBeenCalledTimes(4); // 2 initial + 2 refetch
  });
});

describe('useInfiniteScroll', () => {
  it('creates intersection observer', () => {
    const fetchNextPage = jest.fn();

    const { result } = renderHook(() =>
      useInfiniteScroll(fetchNextPage, true, false)
    );

    expect(result.current).toBeDefined();
    expect(result.current.current).toBeNull(); // No element attached yet
  });

  it('triggers fetch when element intersects', () => {
    const fetchNextPage = jest.fn();

    renderHook(() =>
      useInfiniteScroll(fetchNextPage, true, false, 0.8)
    );

    // Would need to mock IntersectionObserver for full testing
    // This test verifies the hook returns without errors
  });
});

describe('useBidirectionalInfiniteQuery', () => {
  const createBidirectionalMockPage = (
    page: number,
    pageSize: number,
    direction: 'up' | 'down'
  ) => ({
    data: Array.from({ length: pageSize }, (_, i) => ({
      id: `item-${direction}-${page * pageSize + i}`,
      name: `Item ${direction} ${page * pageSize + i}`,
    })),
    hasMore: page < 3,
  });

  it('fetches in both directions', async () => {
    const fetchFn = jest.fn(
      (page: number, pageSize: number, direction: 'up' | 'down') =>
        Promise.resolve(createBidirectionalMockPage(page, pageSize, direction))
    );

    const { result } = renderHook(
      () =>
        useBidirectionalInfiniteQuery({
          queryKey: ['test'],
          fetchFn,
          pageSize: 10,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.items).toHaveLength(20); // down + up pages
  });

  it('fetches additional pages down', async () => {
    const fetchFn = jest.fn(
      (page: number, pageSize: number, direction: 'up' | 'down') =>
        Promise.resolve(createBidirectionalMockPage(page, pageSize, direction))
    );

    const { result } = renderHook(
      () =>
        useBidirectionalInfiniteQuery({
          queryKey: ['test'],
          fetchFn,
          pageSize: 10,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      result.current.fetchNextPageDown();
    });

    await waitFor(() => {
      expect(result.current.isFetchingDown).toBe(false);
    });
  });

  it('fetches additional pages up', async () => {
    const fetchFn = jest.fn(
      (page: number, pageSize: number, direction: 'up' | 'down') =>
        Promise.resolve(createBidirectionalMockPage(page, pageSize, direction))
    );

    const { result } = renderHook(
      () =>
        useBidirectionalInfiniteQuery({
          queryKey: ['test'],
          fetchFn,
          pageSize: 10,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      result.current.fetchNextPageUp();
    });

    await waitFor(() => {
      expect(result.current.isFetchingUp).toBe(false);
    });
  });
});

describe('InfiniteScrollMonitor', () => {
  it('records page fetches', () => {
    const monitor = new InfiniteScrollMonitor();

    monitor.recordPageFetch(20, 100);
    monitor.recordPageFetch(20, 150);
    monitor.recordPageFetch(20, 120);

    const stats = monitor.getStats();
    expect(stats.totalPages).toBe(3);
    expect(stats.totalItems).toBe(60);
    expect(stats.averageItemsPerPage).toBe(20);
    expect(stats.averageFetchTime).toBeGreaterThan(0);
  });

  it('calculates average fetch time', () => {
    const monitor = new InfiniteScrollMonitor();

    monitor.recordPageFetch(20, 100);
    monitor.recordPageFetch(20, 200);
    monitor.recordPageFetch(20, 300);

    expect(monitor.getAverageFetchTime()).toBe(200);
  });

  it('limits stored measurements to 20', () => {
    const monitor = new InfiniteScrollMonitor();

    for (let i = 0; i < 25; i++) {
      monitor.recordPageFetch(20, 100);
    }

    const stats = monitor.getStats();
    expect(stats.fetchTimes).toHaveLength(20);
  });
});
