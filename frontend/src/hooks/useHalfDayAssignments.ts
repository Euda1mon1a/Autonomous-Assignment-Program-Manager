/**
 * Half-Day Assignment Hooks
 *
 * Hooks for fetching expanded half-day schedule data with React Query caching.
 * This provides the day-specific patterns (LEC, intern continuity, etc.)
 * that are missing from block-level assignment data.
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query'
import { get, ApiError } from '@/lib/api'

// ============================================================================
// Types
// ============================================================================

export interface HalfDayAssignment {
  id: string
  personId: string
  personName: string | null
  personType: string | null
  pgyLevel: number | null
  date: string
  timeOfDay: 'AM' | 'PM'
  activityId: string | null
  activityCode: string | null
  activityName: string | null
  source: 'preload' | 'manual' | 'solver' | 'template'
  isLocked: boolean
  createdAt: string
  updatedAt: string
}

export interface HalfDayAssignmentListResponse {
  assignments: HalfDayAssignment[]
  total: number
  blockNumber: number | null
  academicYear: number | null
  startDate: string | null
  endDate: string | null
}

export interface HalfDayAssignmentFilters {
  blockNumber?: number
  academicYear?: number
  startDate?: string
  endDate?: string
  personType?: 'resident' | 'faculty'
}

// ============================================================================
// Query Keys
// ============================================================================

export const halfDayAssignmentQueryKeys = {
  all: ['half-day-assignments'] as const,
  list: (filters?: HalfDayAssignmentFilters) =>
    ['half-day-assignments', 'list', filters] as const,
  byBlock: (blockNumber: number, academicYear: number) =>
    ['half-day-assignments', 'block', blockNumber, academicYear] as const,
}

// ============================================================================
// Hooks
// ============================================================================

/**
 * Fetches expanded half-day assignments for a block or date range.
 *
 * This hook retrieves the day-specific schedule data that includes:
 * - LEC (Lecture) on Wednesday PM for all residents
 * - Intern continuity clinic on Wednesday AM for PGY-1
 * - Kapiolani rotation patterns (Mon PM OFF, Tue OFF/OFF, Wed AM C)
 * - Mid-block rotation transitions
 * - Post-call patterns (PCAT/DO)
 *
 * @param filters - Block/date filters
 * @param options - Optional React Query configuration
 * @returns Query result with half-day assignments
 *
 * @example
 * ```tsx
 * function ScheduleGrid({ blockNumber, academicYear }: Props) {
 *   const { data, isLoading } = useHalfDayAssignments({
 *     blockNumber,
 *     academicYear,
 *   });
 *
 *   if (isLoading) return <Spinner />;
 *
 *   // Build lookup by personId+date+timeOfDay
 *   const assignmentMap = new Map(
 *     data.assignments.map(a => [`${a.personId}_${a.date}_${a.timeOfDay}`, a])
 *   );
 *
 *   return <Grid data={assignmentMap} />;
 * }
 * ```
 */
export function useHalfDayAssignments(
  filters?: HalfDayAssignmentFilters,
  options?: Omit<
    UseQueryOptions<HalfDayAssignmentListResponse, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  const params = new URLSearchParams()

  // URL query params MUST use snake_case (Couatl Killer)
  if (filters?.blockNumber !== undefined) {
    params.set('block_number', filters.blockNumber.toString())
  }
  if (filters?.academicYear !== undefined) {
    params.set('academic_year', filters.academicYear.toString())
  }
  if (filters?.startDate) {
    params.set('start_date', filters.startDate)
  }
  if (filters?.endDate) {
    params.set('end_date', filters.endDate)
  }
  if (filters?.personType) {
    params.set('person_type', filters.personType)
  }

  const queryString = params.toString()

  // Don't fetch if we don't have enough parameters
  const hasBlockParams =
    filters?.blockNumber !== undefined && filters?.academicYear !== undefined
  const hasDateParams = !!(filters?.startDate && filters?.endDate)
  const enabled = hasBlockParams || hasDateParams

  return useQuery<HalfDayAssignmentListResponse, ApiError>({
    queryKey: halfDayAssignmentQueryKeys.list(filters),
    queryFn: () =>
      get<HalfDayAssignmentListResponse>(
        `/half-day-assignments${queryString ? `?${queryString}` : ''}`
      ),
    staleTime: 2 * 60 * 1000, // 2 minutes (schedules can change)
    gcTime: 15 * 60 * 1000, // 15 minutes
    refetchOnWindowFocus: true,
    enabled,
    retry: (failureCount, error) => {
      // Don't retry on auth errors
      if (error.status === 401 || error.status === 403) {
        return false
      }
      return failureCount < 3
    },
    ...options,
  })
}

/**
 * Convenience hook for fetching half-day assignments by block.
 *
 * @param blockNumber - Block number (1-13)
 * @param academicYear - Academic year (e.g., 2025 for AY 2025-2026)
 * @param personType - Optional filter by person type
 */
export function useHalfDayAssignmentsByBlock(
  blockNumber: number,
  academicYear: number,
  personType?: 'resident' | 'faculty'
) {
  return useHalfDayAssignments({
    blockNumber,
    academicYear,
    personType,
  })
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Build a lookup map from half-day assignments.
 *
 * @param assignments - Array of half-day assignments
 * @returns Map keyed by "personId_date_timeOfDay"
 */
export function buildHalfDayAssignmentMap(
  assignments: HalfDayAssignment[]
): Map<string, HalfDayAssignment> {
  return new Map(
    assignments.map((a) => [`${a.personId}_${a.date}_${a.timeOfDay}`, a])
  )
}

/**
 * Get assignment for a specific slot.
 *
 * @param map - Assignment map from buildHalfDayAssignmentMap
 * @param personId - Person UUID
 * @param date - Date string (YYYY-MM-DD)
 * @param timeOfDay - 'AM' or 'PM'
 */
export function getSlotAssignment(
  map: Map<string, HalfDayAssignment>,
  personId: string,
  date: string,
  timeOfDay: 'AM' | 'PM'
): HalfDayAssignment | undefined {
  return map.get(`${personId}_${date}_${timeOfDay}`)
}
