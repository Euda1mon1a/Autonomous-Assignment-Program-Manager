/**
 * Custom hook for infinite scrolling with TanStack Query.
 *
 * Provides efficient infinite scroll implementation with automatic
 * data fetching and caching.
 */

import { useInfiniteQuery as useTanStackInfiniteQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useRef } from 'react';

export interface InfiniteQueryOptions<T> {
  /** Query key for caching */
  queryKey: string[];
  /** Fetch function that returns page of data */
  fetchFn: (page: number, pageSize: number) => Promise<{
    data: T[];
    total: number;
    hasMore: boolean;
  }>;
  /** Items per page */
  pageSize?: number;
  /** Enable query */
  enabled?: boolean;
  /** Stale time in milliseconds */
  staleTime?: number;
}

export interface InfiniteQueryResult<T> {
  /** All loaded items */
  items: T[];
  /** Is loading first page */
  isLoading: boolean;
  /** Is loading more pages */
  isFetchingNextPage: boolean;
  /** Has more pages to load */
  hasNextPage: boolean;
  /** Fetch next page */
  fetchNextPage: () => void;
  /** Refetch all pages */
  refetch: () => void;
  /** Error if any */
  error: Error | null;
  /** Total item count */
  totalCount: number;
}

/**
 * Infinite scroll hook with TanStack Query integration.
 */
export function useInfiniteQuery<T>({
  queryKey,
  fetchFn,
  pageSize = 20,
  enabled = true,
  staleTime = 5 * 60 * 1000, // 5 minutes
}: InfiniteQueryOptions<T>): InfiniteQueryResult<T> {
  const {
    data,
    isLoading,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
    refetch,
    error,
  } = useTanStackInfiniteQuery({
    queryKey,
    queryFn: async ({ pageParam }: { pageParam: number }) => {
      return fetchFn(pageParam, pageSize);
    },
    getNextPageParam: (lastPage, allPages) => {
      return lastPage.hasMore ? allPages.length : undefined;
    },
    initialPageParam: 0,
    enabled,
    staleTime,
  });

  // Flatten all pages into single array
  const items = data?.pages.flatMap((page) => page.data) ?? [];
  const totalCount = data?.pages[0]?.total ?? 0;

  return {
    items,
    isLoading,
    isFetchingNextPage,
    hasNextPage: hasNextPage ?? false,
    fetchNextPage,
    refetch,
    error: error as Error | null,
    totalCount,
  };
}

/**
 * Hook to automatically fetch next page when scrolling near bottom.
 */
export function useInfiniteScroll(
  fetchNextPage: () => void,
  hasNextPage: boolean,
  isFetchingNextPage: boolean,
  threshold = 0.8 // Fetch when 80% scrolled
) {
  const observerRef = useRef<IntersectionObserver>();
  const loadMoreRef = useRef<HTMLDivElement>(null);

  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries;
      if (entry.isIntersecting && hasNextPage && !isFetchingNextPage) {
        fetchNextPage();
      }
    },
    [fetchNextPage, hasNextPage, isFetchingNextPage]
  );

  useEffect(() => {
    const element = loadMoreRef.current;
    if (!element) return;

    observerRef.current = new IntersectionObserver(handleObserver, {
      root: null,
      rootMargin: '0px',
      threshold,
    });

    observerRef.current.observe(element);

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [handleObserver, threshold]);

  return loadMoreRef;
}

/**
 * Combined infinite query + scroll hook.
 */
export function useInfiniteScrollQuery<T>(
  options: InfiniteQueryOptions<T>
) {
  const queryResult = useInfiniteQuery(options);

  const loadMoreRef = useInfiniteScroll(
    queryResult.fetchNextPage,
    queryResult.hasNextPage,
    queryResult.isFetchingNextPage
  );

  return {
    ...queryResult,
    loadMoreRef,
  };
}

/**
 * Bidirectional infinite scroll (load both up and down).
 */
export interface BidirectionalInfiniteQueryOptions<T> {
  queryKey: string[];
  fetchFn: (page: number, pageSize: number, direction: 'up' | 'down') => Promise<{
    data: T[];
    hasMore: boolean;
  }>;
  pageSize?: number;
  initialPage?: number;
}

export function useBidirectionalInfiniteQuery<T>({
  queryKey,
  fetchFn,
  pageSize = 20,
  initialPage: _initialPage = 0,
}: BidirectionalInfiniteQueryOptions<T>) {
  const downQuery = useInfiniteQuery({
    queryKey: [...queryKey, 'down'],
    fetchFn: async (page: number) => {
      const result = await fetchFn(page, pageSize, 'down');
      return { ...result, total: 0 };
    },
    pageSize,
  });

  const upQuery = useInfiniteQuery({
    queryKey: [...queryKey, 'up'],
    fetchFn: async (page: number) => {
      const result = await fetchFn(page, pageSize, 'up');
      return { ...result, total: 0 };
    },
    pageSize,
  });

  // Combine items from both directions
  const items = [
    ...(upQuery.items || []).reverse(),
    ...(downQuery.items || []),
  ];

  return {
    items,
    isLoading: downQuery.isLoading || upQuery.isLoading,
    hasNextPageDown: downQuery.hasNextPage,
    hasNextPageUp: upQuery.hasNextPage,
    fetchNextPageDown: downQuery.fetchNextPage,
    fetchNextPageUp: upQuery.fetchNextPage,
    isFetchingDown: downQuery.isFetchingNextPage,
    isFetchingUp: upQuery.isFetchingNextPage,
  };
}

/**
 * Performance monitoring for infinite scroll.
 */
export class InfiniteScrollMonitor {
  private stats = {
    totalPages: 0,
    totalItems: 0,
    fetchTimes: [] as number[],
  };

  recordPageFetch(itemCount: number, fetchTime: number): void {
    this.stats.totalPages++;
    this.stats.totalItems += itemCount;
    this.stats.fetchTimes.push(fetchTime);

    // Keep only last 20 measurements
    if (this.stats.fetchTimes.length > 20) {
      this.stats.fetchTimes.shift();
    }
  }

  getAverageFetchTime(): number {
    if (this.stats.fetchTimes.length === 0) return 0;
    return (
      this.stats.fetchTimes.reduce((a, b) => a + b, 0) /
      this.stats.fetchTimes.length
    );
  }

  getStats() {
    return {
      ...this.stats,
      averageFetchTime: this.getAverageFetchTime(),
      averageItemsPerPage:
        this.stats.totalPages > 0
          ? this.stats.totalItems / this.stats.totalPages
          : 0,
    };
  }
}
