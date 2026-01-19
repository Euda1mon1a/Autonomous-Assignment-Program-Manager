/**
 * Block Management Hooks
 *
 * Hooks for fetching and managing academic blocks with React Query caching.
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query'
import { get, ApiError } from '@/lib/api'
import type { Block } from '@/types/api'

// ============================================================================
// Types
// ============================================================================

export interface ListResponse<T> {
  items: T[]
  total: number
}

export interface BlockFilters {
  startDate?: string
  endDate?: string
  blockNumber?: number
}

/**
 * Represents a block range with start and end dates
 */
export interface BlockRange {
  blockNumber: number
  startDate: string
  endDate: string
}

// ============================================================================
// Query Keys
// ============================================================================

export const blockQueryKeys = {
  blocks: (filters?: BlockFilters) => ['blocks', filters] as const,
  blockRanges: () => ['block-ranges'] as const,
}

// ============================================================================
// Block Hooks
// ============================================================================

/**
 * Fetches blocks for a specified date range or block number.
 *
 * This hook retrieves all blocks (AM/PM schedule slots) within the given
 * time period or for a specific academic block number. It uses React Query
 * for automatic caching and background refetching.
 *
 * @param filters - Optional filters for date range or block number
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: List response with blocks and total count
 *   - `isLoading`: Whether the initial fetch is in progress
 *   - `isFetching`: Whether any fetch is in progress (including background)
 *   - `error`: Any error that occurred during fetch
 *   - `refetch`: Function to manually refetch blocks
 *
 * @example
 * ```tsx
 * function BlockList() {
 *   const { data, isLoading } = useBlocks({
 *     startDate: '2024-01-01',
 *     endDate: '2024-01-31'
 *   });
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return (
 *     <ul>
 *       {data.items.map(block => (
 *         <li key={block.id}>
 *           {block.date} {block.timeOfDay} - Block {block.blockNumber}
 *         </li>
 *       ))}
 *     </ul>
 *   );
 * }
 * ```
 *
 * @see useBlockRanges - For fetching aggregated block date ranges
 */
export function useBlocks(
  filters?: BlockFilters,
  options?: Omit<UseQueryOptions<ListResponse<Block>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams()
  if (filters?.startDate) params.set('startDate', filters.startDate)
  if (filters?.endDate) params.set('endDate', filters.endDate)
  if (filters?.blockNumber) params.set('blockNumber', filters.blockNumber.toString())
  const queryString = params.toString()

  return useQuery<ListResponse<Block>, ApiError>({
    queryKey: blockQueryKeys.blocks(filters),
    queryFn: () => get<ListResponse<Block>>(`/blocks${queryString ? `?${queryString}` : ''}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    refetchOnWindowFocus: true,
    // Don't retry on 401 errors - the API client handles redirect to login
    // This prevents infinite retry loops when user is not authenticated
    retry: (failureCount, error) => {
      // Don't retry on auth errors (401/403)
      if (error.status === 401 || error.status === 403) {
        return false
      }
      // Retry up to 3 times for other errors
      return failureCount < 3
    },
    ...options,
  })
}

/**
 * Fetches aggregated block ranges for all academic blocks.
 *
 * This hook computes the start and end dates for each academic block number
 * by grouping blocks and finding the min/max dates. This is useful for
 * navigation components that need to jump between blocks or display block
 * date ranges.
 *
 * The hook queries the backend for all blocks, then groups them by blockNumber
 * to calculate the actual date ranges from the database rather than using
 * local date math.
 *
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: Array of block ranges with blockNumber, startDate, endDate
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually refetch block ranges
 *
 * @example
 * ```tsx
 * function BlockSelector() {
 *   const { data: blockRanges, isLoading } = useBlockRanges();
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <select>
 *       {blockRanges.map(range => (
 *         <option key={range.blockNumber} value={range.blockNumber}>
 *           Block {range.blockNumber}: {range.startDate} - {range.endDate}
 *         </option>
 *       ))}
 *     </select>
 *   );
 * }
 * ```
 *
 * @see useBlocks - For fetching individual blocks
 */
export function useBlockRanges(
  options?: Omit<UseQueryOptions<BlockRange[], ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<BlockRange[], ApiError>({
    queryKey: blockQueryKeys.blockRanges(),
    queryFn: async () => {
      // Fetch ALL blocks with pagination (API returns paginated results)
      // Without this loop, only the first page (~100 blocks) is fetched,
      // causing navigation to only see Block 0 out of 1,516+ blocks
      let allBlocks: Block[] = []
      let page = 1
      const MAX_PAGES = 100 // Safety limit to prevent infinite loops
      let previousCount = 0

      while (page <= MAX_PAGES) {
        const response = await get<ListResponse<Block>>(`/blocks?page=${page}&limit=500`)
        allBlocks = [...allBlocks, ...response.items]

        // Stop if: no items returned, less than limit (last page), or no new items added
        // The "no new items" check handles backends that don't support pagination
        // and return the full list every time
        if (
          response.items.length === 0 ||
          response.items.length < 500 ||
          allBlocks.length === previousCount
        ) {
          break
        }

        previousCount = allBlocks.length
        page++
      }
      // Group blocks by blockNumber and calculate date ranges
      // Handle both camelCase (from interceptor) and snake_case (fallback) property names
      const blockMap = new Map<number, { minDate: string; maxDate: string }>()

      allBlocks.forEach((block) => {
        // Handle both camelCase and snake_case property names for robustness
        const rawBlock = block as unknown as Record<string, unknown>
        const blockNum = (block.blockNumber ?? rawBlock.block_number) as number
        const blockDate = (block.date ?? rawBlock.date) as string

        if (blockNum === undefined || blockNum === null) {
          console.warn('[useBlockRanges] Block missing blockNumber:', block)
          return
        }

        const existing = blockMap.get(blockNum)
        if (!existing) {
          blockMap.set(blockNum, {
            minDate: blockDate,
            maxDate: blockDate,
          })
        } else {
          if (blockDate < existing.minDate) {
            existing.minDate = blockDate
          }
          if (blockDate > existing.maxDate) {
            existing.maxDate = blockDate
          }
        }
      })

      // Convert to BlockRange array and sort by blockNumber
      const ranges: BlockRange[] = Array.from(blockMap.entries())
        .map(([blockNumber, { minDate, maxDate }]) => ({
          blockNumber,
          startDate: minDate,
          endDate: maxDate,
        }))
        .sort((a, b) => a.blockNumber - b.blockNumber)

      return ranges
    },
    staleTime: 10 * 60 * 1000, // 10 minutes (blocks don't change often)
    gcTime: 60 * 60 * 1000, // 1 hour
    refetchOnWindowFocus: false, // Don't refetch on focus (stable data)
    // Don't retry on 401 errors - the API client handles redirect to login
    // This prevents infinite retry loops when user is not authenticated
    retry: (failureCount, error) => {
      // Don't retry on auth errors (401/403)
      if (error.status === 401 || error.status === 403) {
        return false
      }
      // Retry up to 3 times for other errors
      return failureCount < 3
    },
    ...options,
  })
}
