'use client'

import { useMemo, useState, useEffect } from 'react'
import { format, eachDayOfInterval, isWeekend } from 'date-fns'
import { useQuery, useQueries } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { get } from '@/lib/api'
import { usePeople, useRotationTemplates, ListResponse } from '@/lib/hooks'
import type { Person, RotationTemplate, Assignment, Block } from '@/types/api'
import {
  BLOCKS_STALE_TIME_MS,
  BLOCKS_GC_TIME_MS,
  ASSIGNMENTS_STALE_TIME_MS,
  ASSIGNMENTS_GC_TIME_MS,
  PGY_LEVEL_1,
  PGY_LEVEL_2,
  PGY_LEVEL_3,
  ABBREVIATION_LENGTH,
  SCHEDULE_GRID_MAX_HEIGHT,
  FADE_IN_DURATION,
  ROW_HOVER_TRANSITION_MS,
} from '@/constants/schedule'
import { ScheduleHeader } from './ScheduleHeader'
import { ScheduleCell, ScheduleSeparatorRow } from './ScheduleCell'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorAlert } from '@/components/ErrorAlert'
import { EmptyState } from '@/components/EmptyState'

interface ScheduleGridProps {
  startDate: Date
  endDate: Date
}

interface ProcessedAssignment {
  abbreviation: string
  activityType: string
  fontColor?: string
  backgroundColor?: string
  templateName?: string
  role?: string
  notes?: string
}

// Group people by type/PGY level for display
interface PersonGroup {
  label: string
  people: Person[]
}

/**
 * Custom hook to fetch blocks for a date range
 */
function useBlocks(startDate: string, endDate: string) {
  return useQuery<ListResponse<Block>>({
    queryKey: ['blocks', startDate, endDate],
    queryFn: () =>
      get<ListResponse<Block>>(`/blocks?start_date=${startDate}&end_date=${endDate}`),
    staleTime: BLOCKS_STALE_TIME_MS,
    gcTime: BLOCKS_GC_TIME_MS,
  })
}

/** Maximum page size allowed by backend */
const ASSIGNMENTS_PAGE_SIZE = 500

/**
 * Custom hook to fetch ALL assignments for a date range with automatic pagination.
 *
 * Strategy:
 * 1. First query fetches page 1 to get total count
 * 2. Based on total, calculate number of pages needed
 * 3. Fetch remaining pages in parallel
 * 4. Combine all results
 *
 * For a typical 28-day block with ~1000 assignments (e.g., Block 10 with 992),
 * this fetches 2 pages of 500 each.
 */
function useAssignmentsForRange(startDate: string, endDate: string) {
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
      enabled: pageCount > 1, // Only run if we need more than 1 page
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
  const error = firstPageQuery.error || additionalPageQueries.find((q) => q.error)?.error

  return {
    data: combinedData,
    isLoading,
    error,
  }
}

/**
 * Main schedule grid component
 * Shows all people (grouped by PGY level) with their assignments for each day
 */
export function ScheduleGrid({ startDate, endDate }: ScheduleGridProps) {
  const startDateStr = format(startDate, 'yyyy-MM-dd')
  const endDateStr = format(endDate, 'yyyy-MM-dd')

  // Fetch all required data
  const { data: blocksData, isLoading: blocksLoading, error: blocksError } = useBlocks(startDateStr, endDateStr)
  const { data: assignmentsData, isLoading: assignmentsLoading, error: assignmentsError } = useAssignmentsForRange(startDateStr, endDateStr)
  const { data: peopleData, isLoading: peopleLoading, error: peopleError } = usePeople()
  const { data: templatesData, isLoading: templatesLoading, error: templatesError } = useRotationTemplates()

  // Generate array of days in the range
  const days = useMemo(() => {
    return eachDayOfInterval({ start: startDate, end: endDate })
  }, [startDate, endDate])

  // Create lookup maps for efficient data access
  const blockMap = useMemo(() => {
    const map = new Map<string, Block>()
    blocksData?.items?.forEach((block) => {
      map.set(block.id, block)
    })
    return map
  }, [blocksData])

  const templateMap = useMemo(() => {
    const map = new Map<string, RotationTemplate>()
    templatesData?.items?.forEach((template) => {
      map.set(template.id, template)
    })
    return map
  }, [templatesData])

  // Create assignment lookup: personId -> date -> timeOfDay -> assignment
  const assignmentLookup = useMemo(() => {
    const lookup = new Map<string, Map<string, Map<string, ProcessedAssignment>>>()

    assignmentsData?.items?.forEach((assignment) => {
      const block = blockMap.get(assignment.block_id)
      if (!block) return

      const template = assignment.rotation_template_id
        ? templateMap.get(assignment.rotation_template_id)
        : null

      const processed: ProcessedAssignment = {
        abbreviation:
          assignment.activity_override ||
          template?.display_abbreviation ||
          template?.abbreviation ||
          template?.name?.substring(0, ABBREVIATION_LENGTH).toUpperCase() ||
          '???',
        activityType: template?.activity_type || 'default',
        fontColor: template?.font_color || undefined,
        backgroundColor: template?.background_color || undefined,
        templateName: template?.name,
        role: assignment.role,
        notes: assignment.notes || undefined,
      }

      // Get or create person map
      if (!lookup.has(assignment.person_id)) {
        lookup.set(assignment.person_id, new Map())
      }
      const personMap = lookup.get(assignment.person_id)!

      // Get or create date map
      const dateStr = block.date
      if (!personMap.has(dateStr)) {
        personMap.set(dateStr, new Map())
      }
      const dateMap = personMap.get(dateStr)!

      // Set assignment for time of day
      dateMap.set(block.time_of_day, processed)
    })

    return lookup
  }, [assignmentsData, blockMap, templateMap])

  // Group people by PGY level
  const personGroups = useMemo((): PersonGroup[] => {
    if (!peopleData?.items) return []

    const pgy1: Person[] = []
    const pgy2: Person[] = []
    const pgy3: Person[] = []
    const pgyOther: Person[] = []
    const faculty: Person[] = []

    peopleData.items.forEach((person) => {
      if (person.type === 'faculty') {
        faculty.push(person)
      } else if (person.pgy_level === PGY_LEVEL_1) {
        pgy1.push(person)
      } else if (person.pgy_level === PGY_LEVEL_2) {
        pgy2.push(person)
      } else if (person.pgy_level === PGY_LEVEL_3) {
        pgy3.push(person)
      } else {
        pgyOther.push(person)
      }
    })

    // Sort each group by name
    const sortByName = (a: Person, b: Person) => a.name.localeCompare(b.name)
    pgy1.sort(sortByName)
    pgy2.sort(sortByName)
    pgy3.sort(sortByName)
    pgyOther.sort(sortByName)
    faculty.sort(sortByName)

    const groups: PersonGroup[] = []
    if (pgy1.length > 0) groups.push({ label: 'PGY-1', people: pgy1 })
    if (pgy2.length > 0) groups.push({ label: 'PGY-2', people: pgy2 })
    if (pgy3.length > 0) groups.push({ label: 'PGY-3', people: pgy3 })
    if (pgyOther.length > 0) groups.push({ label: 'Residents (Other)', people: pgyOther })
    if (faculty.length > 0) groups.push({ label: 'Faculty', people: faculty })

    return groups
  }, [peopleData])

  // Loading state
  const isLoading = blocksLoading || assignmentsLoading || peopleLoading || templatesLoading
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64" role="status" aria-live="polite" aria-busy="true">
        <LoadingSpinner />
        <span className="ml-2 text-gray-600">Loading schedule...</span>
      </div>
    )
  }

  // Error state
  const error = blocksError || assignmentsError || peopleError || templatesError
  if (error) {
    return (
      <div className="p-4">
        <ErrorAlert
          message={error instanceof Error ? error.message : 'Failed to load schedule data'}
        />
      </div>
    )
  }

  // Empty state - no people
  if (personGroups.length === 0) {
    return (
      <EmptyState
        title="No People Found"
        description="Add residents and faculty to see them in the schedule."
        action={{
          label: 'Add People',
          onClick: () => (window.location.href = '/people'),
        }}
      />
    )
  }

  // Get person's assignment for a specific date and time
  const getAssignment = (
    personId: string,
    dateStr: string,
    timeOfDay: 'AM' | 'PM'
  ): ProcessedAssignment | undefined => {
    return assignmentLookup.get(personId)?.get(dateStr)?.get(timeOfDay)
  }

  // Check if a date is today
  const todayStr = format(new Date(), 'yyyy-MM-dd')

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: FADE_IN_DURATION, ease: 'easeOut' }}
      className={`glass-panel overflow-auto max-h-[${SCHEDULE_GRID_MAX_HEIGHT}]`}
    >
      <table className="min-w-full divide-y divide-gray-200/50 schedule-grid-table" role="grid" aria-label="Schedule grid showing assignments by person and date">
        <ScheduleHeader days={days} />

        <tbody className="bg-white/50 divide-y divide-gray-200/50">
          {personGroups.map((group, groupIndex) => (
            <PersonGroupRows
              key={group.label}
              group={group}
              groupIndex={groupIndex}
              days={days}
              todayStr={todayStr}
              getAssignment={getAssignment}
              showSeparator={groupIndex > 0}
            />
          ))}
        </tbody>
      </table>
    </motion.div>
  )
}

/**
 * Renders rows for a group of people (e.g., all PGY-1 residents)
 */
interface PersonGroupRowsProps {
  group: PersonGroup
  groupIndex: number
  days: Date[]
  todayStr: string
  getAssignment: (
    personId: string,
    dateStr: string,
    timeOfDay: 'AM' | 'PM'
  ) => ProcessedAssignment | undefined
  showSeparator: boolean
}

function PersonGroupRows({
  group,
  groupIndex,
  days,
  todayStr,
  getAssignment,
  showSeparator,
}: PersonGroupRowsProps) {
  return (
    <>
      {/* Separator row between groups */}
      {showSeparator && (
        <ScheduleSeparatorRow label={group.label} columnCount={days.length} />
      )}

      {/* First person row includes group label if no separator */}
      {!showSeparator && groupIndex === 0 && (
        <ScheduleSeparatorRow label={group.label} columnCount={days.length} />
      )}

      {/* Person rows */}
      {group.people.map((person) => (
        <PersonRow
          key={person.id}
          person={person}
          days={days}
          todayStr={todayStr}
          getAssignment={getAssignment}
        />
      ))}
    </>
  )
}

/**
 * Renders a single person's row with all their assignments
 */
interface PersonRowProps {
  person: Person
  days: Date[]
  todayStr: string
  getAssignment: (
    personId: string,
    dateStr: string,
    timeOfDay: 'AM' | 'PM'
  ) => ProcessedAssignment | undefined
}

function PersonRow({ person, days, todayStr, getAssignment }: PersonRowProps) {
  // Memoize person badge
  const personBadge = useMemo(() => {
    if (person.type === 'faculty') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
          Faculty
        </span>
      )
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
        PGY-{person.pgy_level}
      </span>
    )
  }, [person.type, person.pgy_level])

  return (
    <tr className={`group hover:bg-blue-50/30 transition-colors duration-[${ROW_HOVER_TRANSITION_MS}ms]`} role="row">
      {/* Sticky person name column */}
      <th scope="row" className="sticky left-0 z-10 bg-white group-hover:bg-blue-50/50 px-4 py-2 border-r border-gray-200 shadow-[2px_0_4px_-2px_rgba(0,0,0,0.1)] transition-colors duration-150 text-left font-normal" role="rowheader">
        <div className="flex flex-col gap-1">
          <span className="font-medium text-gray-900 text-sm whitespace-nowrap">
            {person.name}
          </span>
          {personBadge}
        </div>
      </th>

      {/* Day cells - AM and PM for each day */}
      {days.map((day) => {
        const dateStr = format(day, 'yyyy-MM-dd')
        const weekend = isWeekend(day)
        const isToday = dateStr === todayStr

        return (
          <DayCells
            key={dateStr}
            personId={person.id}
            dateStr={dateStr}
            isWeekend={weekend}
            isToday={isToday}
            getAssignment={getAssignment}
          />
        )
      })}
    </tr>
  )
}

/**
 * Renders AM and PM cells for a single day
 */
interface DayCellsProps {
  personId: string
  dateStr: string
  isWeekend: boolean
  isToday: boolean
  getAssignment: (
    personId: string,
    dateStr: string,
    timeOfDay: 'AM' | 'PM'
  ) => ProcessedAssignment | undefined
}

function DayCells({
  personId,
  dateStr,
  isWeekend,
  isToday,
  getAssignment,
}: DayCellsProps) {
  const amAssignment = getAssignment(personId, dateStr, 'AM')
  const pmAssignment = getAssignment(personId, dateStr, 'PM')

  return (
    <>
      <ScheduleCell
        assignment={amAssignment}
        isWeekend={isWeekend}
        isToday={isToday}
        timeOfDay="AM"
      />
      <ScheduleCell
        assignment={pmAssignment}
        isWeekend={isWeekend}
        isToday={isToday}
        timeOfDay="PM"
      />
    </>
  )
}
