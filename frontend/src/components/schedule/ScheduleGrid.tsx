'use client'

import { useMemo } from 'react'
import { format, eachDayOfInterval, isWeekend } from 'date-fns'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { get } from '@/lib/api'
import { usePeople, useRotationTemplates, ListResponse } from '@/lib/hooks'
import { useAssignmentsForRange } from '@/hooks/useAssignmentsForRange'
import { useHalfDayAssignments } from '@/hooks/useHalfDayAssignments'
import type { Person, RotationTemplate, Block } from '@/types/api'
import {
  ABBREVIATION_LENGTH,
  BLOCKS_STALE_TIME_MS,
  BLOCKS_GC_TIME_MS,
  PGY_LEVEL_1,
  PGY_LEVEL_2,
  PGY_LEVEL_3,
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
  /** Optional set of person IDs to filter to. If empty/undefined, shows all people. */
  personFilter?: Set<string>
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
 * Format faculty role for display in schedule grid
 */
function formatFacultyRole(role: string): string {
  const roleMap: Record<string, string> = {
    pd: 'PD',
    apd: 'APD',
    oic: 'OIC',
    dept_chief: 'Chief',
    deptChief: 'Chief', // Handle both snake_case and camelCase
    sports_med: 'SM',
    sportsMed: 'SM',
    core: 'Core',
    adjunct: 'Adj',
  }
  return roleMap[role] || role.toUpperCase()
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

/**
 * Main schedule grid component
 * Shows all people (grouped by PGY level) with their assignments for each day
 */
export function ScheduleGrid({ startDate, endDate, personFilter }: ScheduleGridProps) {
  const startDateStr = format(startDate, 'yyyy-MM-dd')
  const endDateStr = format(endDate, 'yyyy-MM-dd')

  // Fetch all required data
  const { data: blocksData, isLoading: blocksLoading, error: blocksError } = useBlocks(startDateStr, endDateStr)
  const { data: assignmentsData, isLoading: assignmentsLoading, error: assignmentsError } = useAssignmentsForRange(startDateStr, endDateStr)
  const { data: peopleData, isLoading: peopleLoading, error: peopleError } = usePeople()
  const { data: templatesData, isLoading: templatesLoading, error: templatesError } = useRotationTemplates()

  // Fetch half-day assignments (expanded schedule with day-specific patterns)
  // Note: halfDayLoading/halfDayError intentionally unused - we fall back gracefully to block-level data
  const { data: halfDayData } = useHalfDayAssignments({
    startDate: startDateStr,
    endDate: endDateStr,
  })

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

  // Create person lookup for role/template fallback
  const personMap = useMemo(() => {
    const map = new Map<string, Person>()
    peopleData?.items?.forEach((person) => {
      map.set(person.id, person)
    })
    return map
  }, [peopleData])

  // Create assignment lookup: personId -> date -> timeOfDay -> assignment
  // PRIORITY: half-day assignments (expanded) > block-level assignments (raw)
  const assignmentLookup = useMemo(() => {
    const lookup = new Map<string, Map<string, Map<string, ProcessedAssignment>>>()

    // First, populate from block-level assignments (fallback data)
    assignmentsData?.items?.forEach((assignment) => {
      const block = blockMap.get(assignment.blockId)
      if (!block) return

      const template = assignment.rotationTemplateId
        ? templateMap.get(assignment.rotationTemplateId)
        : null

      const processed: ProcessedAssignment = {
        abbreviation:
          assignment.activityOverride ||
          template?.displayAbbreviation ||
          template?.abbreviation ||
          template?.name?.substring(0, ABBREVIATION_LENGTH).toUpperCase() ||
          '???',
        activityType: template?.activityType || 'default',
        fontColor: template?.fontColor || undefined,
        backgroundColor: template?.backgroundColor || undefined,
        templateName: template?.name,
        role: assignment.role,
        notes: assignment.notes || undefined,
      }

      // Get or create person map
      if (!lookup.has(assignment.personId)) {
        lookup.set(assignment.personId, new Map())
      }
      const personMap = lookup.get(assignment.personId)!

      // Get or create date map
      const dateStr = block.date
      if (!personMap.has(dateStr)) {
        personMap.set(dateStr, new Map())
      }
      const dateMap = personMap.get(dateStr)!

      // Set assignment for time of day
      dateMap.set(block.timeOfDay, processed)
    })

    // THEN, override with half-day assignments ONLY when they have an activity
    // This ensures day-specific patterns (LEC, intern continuity, KAP patterns) are shown
    // but we fall back to block-level rotation templates for slots without specific activities
    halfDayData?.assignments?.forEach((hda) => {
      // Only override if half-day has an actual activity code
      if (!hda.activityCode) return

      const processed: ProcessedAssignment = {
        abbreviation: hda.activityCode,
        activityType: 'default', // Could map from activity if needed
        templateName: hda.activityName || undefined,
        // Note: half-day assignments don't have colors yet, could be added
      }

      // Get or create person map
      if (!lookup.has(hda.personId)) {
        lookup.set(hda.personId, new Map())
      }
      const personMap = lookup.get(hda.personId)!

      // Get or create date map
      if (!personMap.has(hda.date)) {
        personMap.set(hda.date, new Map())
      }
      const dateMap = personMap.get(hda.date)!

      // Override with half-day data
      dateMap.set(hda.timeOfDay, processed)
    })

    // FINALLY, fill in faculty role fallback for empty slots
    // Faculty without specific activities show their role (PD, Core, Adj, etc.)
    personMap.forEach((person, personId) => {
      if (person.type !== 'faculty' || !person.facultyRole) return

      days.forEach((day) => {
        const dateStr = format(day, 'yyyy-MM-dd')
        const timesOfDay: Array<'AM' | 'PM'> = ['AM', 'PM']

        timesOfDay.forEach((timeOfDay) => {
          // Skip if already has an assignment
          if (lookup.get(personId)?.get(dateStr)?.get(timeOfDay)) return

          // Get or create person lookup map
          if (!lookup.has(personId)) {
            lookup.set(personId, new Map())
          }
          const personLookup = lookup.get(personId)!

          // Get or create date map
          if (!personLookup.has(dateStr)) {
            personLookup.set(dateStr, new Map())
          }
          const dateMap = personLookup.get(dateStr)!

          // Faculty: show role as fallback
          dateMap.set(timeOfDay, {
            abbreviation: formatFacultyRole(person.facultyRole!),
            activityType: 'admin',
          })
        })
      })
    })

    return lookup
  }, [assignmentsData, blockMap, templateMap, halfDayData, personMap, days])

  // Group people by PGY level (with optional filtering)
  const personGroups = useMemo((): PersonGroup[] => {
    if (!peopleData?.items) return []

    // Apply person filter if provided and non-empty
    const hasFilter = personFilter && personFilter.size > 0
    const people = hasFilter
      ? peopleData.items.filter((p) => personFilter.has(p.id))
      : peopleData.items

    const pgy1: Person[] = []
    const pgy2: Person[] = []
    const pgy3: Person[] = []
    const pgyOther: Person[] = []
    const faculty: Person[] = []

    people.forEach((person) => {
      if (person.type === 'faculty') {
        faculty.push(person)
      } else if (person.pgyLevel === PGY_LEVEL_1) {
        pgy1.push(person)
      } else if (person.pgyLevel === PGY_LEVEL_2) {
        pgy2.push(person)
      } else if (person.pgyLevel === PGY_LEVEL_3) {
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
  }, [peopleData, personFilter])

  // Loading state (half-day data is optional - don't block on it)
  const isLoading = blocksLoading || assignmentsLoading || peopleLoading || templatesLoading
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64" role="status" aria-live="polite" aria-busy="true">
        <LoadingSpinner />
        <span className="ml-2 text-gray-600">Loading schedule...</span>
      </div>
    )
  }

  // Error state (half-day error is non-fatal - fall back to block-level data)
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
        PGY-{person.pgyLevel}
      </span>
    )
  }, [person.type, person.pgyLevel])

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
