/**
 * Multi-Page Assignment Fetching Hook
 *
 * Fetches ALL assignments for a date range with automatic pagination.
 * Solves the issue where large date ranges have more assignments than
 * a single API page can return (e.g., 732 assignments with pageSize=500).
 *
 * Strategy:
 * 1. First query fetches page 1 to get total count
 * 2. Based on total, calculate number of pages needed
 * 3. Fetch remaining pages in parallel
 * 4. Combine all results into a single response
 */

import { useState, useEffect, useMemo } from 'react'
import { useQuery, useQueries } from '@tanstack/react-query'
import { get } from '@/lib/api'
import type { Assignment, Block } from '@/types/api'
import {
  ASSIGNMENTS_STALE_TIME_MS,
  ASSIGNMENTS_GC_TIME_MS,
  BLOCKS_STALE_TIME_MS,
  BLOCKS_GC_TIME_MS,
} from '@/constants/schedule'
import { ListResponse } from '@/lib/hooks'

/** Maximum page size allowed by backend */
export const ASSIGNMENTS_PAGE_SIZE = 500
export const BLOCKS_PAGE_SIZE = 500

/**
 * Custom hook to fetch ALL assignments for a date range with automatic pagination.
 *
 * For a typical month with ~700 assignments, this fetches 2 pages of 500 each.
 * For a year with ~8000 assignments, this fetches 16 pages in parallel after
 * the first page returns the total count.
 *
 * @param startDate - Start date in YYYY-MM-DD format
 * @param endDate - End date in YYYY-MM-DD format
 * @param enabled - Whether to enable the queries (default: true)
 * @returns Combined assignments data, loading state, and error
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useAssignmentsForRange(
 *   '2026-03-01',
 *   '2026-03-31'
 * );
 *
 * // data.items contains ALL assignments for March 2026
 * // data.total shows the actual total from the database
 * ```
 */
export function useAssignmentsForRange(
  startDate: string,
  endDate: string,
  enabled: boolean = true
) {
  const [pageCount, setPageCount] = useState(1)

  // First query to get total count and first page of data
  const firstPageQuery = useQuery<ListResponse<Assignment>>({
    queryKey: ['assignments', startDate, endDate, 'page', 1],
    queryFn: () =>
      get<ListResponse<Assignment>>(
        `/assignments?start_date=${startDate}&end_date=${endDate}&page=1&page_size=${ASSIGNMENTS_PAGE_SIZE}`
      ),
    staleTime: ASSIGNMENTS_STALE_TIME_MS,
    gcTime: ASSIGNMENTS_GC_TIME_MS,
    enabled,
  })

  // Calculate page count when first page loads
  useEffect(() => {
    if (firstPageQuery.data?.total) {
      const total = firstPageQuery.data.total
      const calculatedPages = Math.ceil(total / ASSIGNMENTS_PAGE_SIZE)
      setPageCount(calculatedPages)
    }
  }, [firstPageQuery.data?.total])

  // Generate queries for additional pages (pages 2+)
  const additionalPageQueries = useQueries({
    queries: Array.from({ length: Math.max(0, pageCount - 1) }, (_, i) => ({
      queryKey: ['assignments', startDate, endDate, 'page', i + 2],
      queryFn: () =>
        get<ListResponse<Assignment>>(
          `/assignments?start_date=${startDate}&end_date=${endDate}&page=${i + 2}&page_size=${ASSIGNMENTS_PAGE_SIZE}`
        ),
      staleTime: ASSIGNMENTS_STALE_TIME_MS,
      gcTime: ASSIGNMENTS_GC_TIME_MS,
      enabled: enabled && pageCount > 1, // Only run if we need more than 1 page
    })),
  })

  // Combine results from all pages
  const combinedData = useMemo((): ListResponse<Assignment> | undefined => {
    if (!firstPageQuery.data) return undefined

    // Start with first page items
    const allItems = [...(firstPageQuery.data.items || [])]

    // Add items from additional pages
    for (const query of additionalPageQueries) {
      if (query.data?.items) {
        allItems.push(...query.data.items)
      }
    }

    return {
      items: allItems,
      total: firstPageQuery.data.total,
    }
  }, [firstPageQuery.data, additionalPageQueries])

  // Calculate aggregate loading/error states
  const isLoading = firstPageQuery.isLoading || additionalPageQueries.some((q) => q.isLoading)
  const isFetching = firstPageQuery.isFetching || additionalPageQueries.some((q) => q.isFetching)
  const error = firstPageQuery.error || additionalPageQueries.find((q) => q.error)?.error

  return {
    data: combinedData,
    isLoading,
    isFetching,
    error,
  }
}

/**
 * Custom hook to fetch ALL blocks for a date range with automatic pagination.
 *
 * Uses the same strategy as useAssignmentsForRange - fetch first page to get total,
 * then fetch remaining pages in parallel.
 *
 * @param startDate - Start date in YYYY-MM-DD format
 * @param endDate - End date in YYYY-MM-DD format
 * @param enabled - Whether to enable the queries (default: true)
 * @returns Combined blocks data, loading state, and error
 */
export function useBlocksForRange(
  startDate: string,
  endDate: string,
  enabled: boolean = true
) {
  const [pageCount, setPageCount] = useState(1)

  // First query to get total count and first page of data
  const firstPageQuery = useQuery<ListResponse<Block>>({
    queryKey: ['blocks', startDate, endDate, 'page', 1],
    queryFn: () =>
      get<ListResponse<Block>>(
        `/blocks?start_date=${startDate}&end_date=${endDate}&page=1&page_size=${BLOCKS_PAGE_SIZE}`
      ),
    staleTime: BLOCKS_STALE_TIME_MS,
    gcTime: BLOCKS_GC_TIME_MS,
    enabled,
  })

  // Calculate page count when first page loads
  useEffect(() => {
    if (firstPageQuery.data?.total) {
      const total = firstPageQuery.data.total
      const calculatedPages = Math.ceil(total / BLOCKS_PAGE_SIZE)
      setPageCount(calculatedPages)
    }
  }, [firstPageQuery.data?.total])

  // Generate queries for additional pages (pages 2+)
  const additionalPageQueries = useQueries({
    queries: Array.from({ length: Math.max(0, pageCount - 1) }, (_, i) => ({
      queryKey: ['blocks', startDate, endDate, 'page', i + 2],
      queryFn: () =>
        get<ListResponse<Block>>(
          `/blocks?start_date=${startDate}&end_date=${endDate}&page=${i + 2}&page_size=${BLOCKS_PAGE_SIZE}`
        ),
      staleTime: BLOCKS_STALE_TIME_MS,
      gcTime: BLOCKS_GC_TIME_MS,
      enabled: enabled && pageCount > 1, // Only run if we need more than 1 page
    })),
  })

  // Combine results from all pages
  const combinedData = useMemo((): ListResponse<Block> | undefined => {
    if (!firstPageQuery.data) return undefined

    // Start with first page items
    const allItems = [...(firstPageQuery.data.items || [])]

    // Add items from additional pages
    for (const query of additionalPageQueries) {
      if (query.data?.items) {
        allItems.push(...query.data.items)
      }
    }

    return {
      items: allItems,
      total: firstPageQuery.data.total,
    }
  }, [firstPageQuery.data, additionalPageQueries])

  // Calculate aggregate loading/error states
  const isLoading = firstPageQuery.isLoading || additionalPageQueries.some((q) => q.isLoading)
  const isFetching = firstPageQuery.isFetching || additionalPageQueries.some((q) => q.isFetching)
  const error = firstPageQuery.error || additionalPageQueries.find((q) => q.error)?.error

  return {
    data: combinedData,
    isLoading,
    isFetching,
    error,
  }
}
