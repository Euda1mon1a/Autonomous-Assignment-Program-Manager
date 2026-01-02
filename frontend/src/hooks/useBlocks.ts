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
  start_date?: string
  end_date?: string
  block_number?: number
}

/**
 * Represents a block range with start and end dates
 */
export interface BlockRange {
  block_number: number
  start_date: string
  end_date: string
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
 *     start_date: '2024-01-01',
 *     end_date: '2024-01-31'
 *   });
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return (
 *     <ul>
 *       {data.items.map(block => (
 *         <li key={block.id}>
 *           {block.date} {block.time_of_day} - Block {block.block_number}
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
  if (filters?.start_date) params.set('start_date', filters.start_date)
  if (filters?.end_date) params.set('end_date', filters.end_date)
  if (filters?.block_number) params.set('block_number', filters.block_number.toString())
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
 * The hook queries the backend for all blocks, then groups them by block_number
 * to calculate the actual date ranges from the database rather than using
 * local date math.
 *
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: Array of block ranges with block_number, start_date, end_date
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
 *         <option key={range.block_number} value={range.block_number}>
 *           Block {range.block_number}: {range.start_date} - {range.end_date}
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
      // Fetch all blocks (no date filter)
      const response = await get<ListResponse<Block>>('/blocks')

      // Group blocks by block_number and calculate date ranges
      const blockMap = new Map<number, { minDate: string; maxDate: string }>()

      response.items.forEach((block) => {
        const existing = blockMap.get(block.block_number)
        if (!existing) {
          blockMap.set(block.block_number, {
            minDate: block.date,
            maxDate: block.date,
          })
        } else {
          if (block.date < existing.minDate) {
            existing.minDate = block.date
          }
          if (block.date > existing.maxDate) {
            existing.maxDate = block.date
          }
        }
      })

      // Convert to BlockRange array and sort by block_number
      const ranges: BlockRange[] = Array.from(blockMap.entries())
        .map(([block_number, { minDate, maxDate }]) => ({
          block_number,
          start_date: minDate,
          end_date: maxDate,
        }))
        .sort((a, b) => a.block_number - b.block_number)

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
