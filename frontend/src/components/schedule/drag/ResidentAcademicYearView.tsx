'use client'

import { useMemo, useState, useCallback, useRef, useEffect } from 'react'
import { format, eachWeekOfInterval, startOfWeek, addDays, isWeekend, eachDayOfInterval, parseISO, isSameMonth, getMonth } from 'date-fns'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Calendar, Download } from 'lucide-react'
import { get } from '@/lib/api'
import { usePeople, useRotationTemplates, ListResponse } from '@/lib/hooks'
import type { Person, RotationTemplate, Assignment, Block } from '@/types/api'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorAlert } from '@/components/ErrorAlert'
import { EmptyState } from '@/components/EmptyState'
import { ScheduleDragProvider } from './ScheduleDragProvider'
import { DraggableBlockCell, YearViewSeparatorRow } from './DraggableBlockCell'

interface ResidentAcademicYearViewProps {
  academicYear?: number // e.g., 2024 for 2024-2025 academic year
  startMonth?: number // 0-indexed, default 6 (July)
}

interface ProcessedAssignment {
  id: string
  abbreviation: string
  activityType: string
  templateName?: string
  role?: string
  notes?: string
  personId: string
  personName: string
  blockId: string
  rotationTemplateId: string | null
}

interface PersonGroup {
  label: string
  people: Person[]
}

// Academic year typically runs July 1 to June 30
function getAcademicYearDates(year: number, startMonth: number = 6) {
  const startDate = new Date(year, startMonth, 1) // July 1
  const endDate = new Date(year + 1, startMonth - 1 + 12, 0) // June 30 next year (handles month wrap)

  // Actually calculate last day of June next year
  const actualEndDate = new Date(year + 1, 5, 30) // June 30 of next year

  return { startDate, endDate: actualEndDate }
}

// Get month labels for header
function getMonthLabels(startDate: Date, endDate: Date): { month: string; span: number; isOdd: boolean }[] {
  const weeks = eachWeekOfInterval({ start: startDate, end: endDate }, { weekStartsOn: 1 })
  const months: { month: string; span: number; isOdd: boolean }[] = []

  let currentMonth = -1
  let currentSpan = 0
  let currentLabel = ''

  weeks.forEach((weekStart) => {
    const month = getMonth(weekStart)
    if (month !== currentMonth) {
      if (currentSpan > 0) {
        months.push({ month: currentLabel, span: currentSpan, isOdd: currentMonth % 2 === 1 })
      }
      currentMonth = month
      currentLabel = format(weekStart, 'MMM')
      currentSpan = 1
    } else {
      currentSpan++
    }
  })

  // Push last month
  if (currentSpan > 0) {
    months.push({ month: currentLabel, span: currentSpan, isOdd: currentMonth % 2 === 1 })
  }

  return months
}

export function ResidentAcademicYearView({
  academicYear = new Date().getMonth() >= 6 ? new Date().getFullYear() : new Date().getFullYear() - 1,
  startMonth = 6,
}: ResidentAcademicYearViewProps) {
  const [selectedYear, setSelectedYear] = useState(academicYear)
  const [zoomLevel, setZoomLevel] = useState<'compact' | 'normal'>('compact')
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  // Performance safeguard - require explicit confirmation before rendering 7000+ cells
  const [renderConfirmed, setRenderConfirmed] = useState(false)

  // Calculate date range for academic year
  const { startDate, endDate } = useMemo(
    () => getAcademicYearDates(selectedYear, startMonth),
    [selectedYear, startMonth]
  )

  const startDateStr = format(startDate, 'yyyy-MM-dd')
  const endDateStr = format(endDate, 'yyyy-MM-dd')

  // Fetch all required data
  const { data: blocksData, isLoading: blocksLoading, error: blocksError } = useQuery<ListResponse<Block>>({
    queryKey: ['blocks', startDateStr, endDateStr],
    queryFn: () => get<ListResponse<Block>>(`/blocks?start_date=${startDateStr}&end_date=${endDateStr}`),
    staleTime: 5 * 60 * 1000,
  })

  const { data: assignmentsData, isLoading: assignmentsLoading, error: assignmentsError } = useQuery<ListResponse<Assignment>>({
    queryKey: ['assignments', startDateStr, endDateStr],
    queryFn: () => get<ListResponse<Assignment>>(`/assignments?start_date=${startDateStr}&end_date=${endDateStr}`),
    staleTime: 60 * 1000,
  })

  const { data: peopleData, isLoading: peopleLoading, error: peopleError } = usePeople()
  const { data: templatesData, isLoading: templatesLoading, error: templatesError } = useRotationTemplates()

  // Generate all weeks in the academic year
  const weeks = useMemo(() => {
    return eachWeekOfInterval({ start: startDate, end: endDate }, { weekStartsOn: 1 })
  }, [startDate, endDate])

  // Generate all days for header display (show week start dates)
  const allDays = useMemo(() => {
    return eachDayOfInterval({ start: startDate, end: endDate })
  }, [startDate, endDate])

  // Create lookup maps
  const blockMap = useMemo(() => {
    const map = new Map<string, Block>()
    blocksData?.items?.forEach((block) => {
      map.set(block.id, block)
    })
    return map
  }, [blocksData])

  // Block lookup by date-timeOfDay
  const blockByDateTimeMap = useMemo(() => {
    const map = new Map<string, Block>()
    blocksData?.items?.forEach((block) => {
      map.set(`${block.date}-${block.time_of_day}`, block)
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

      const person = peopleData?.items?.find(p => p.id === assignment.person_id)
      const template = assignment.rotation_template_id
        ? templateMap.get(assignment.rotation_template_id)
        : null

      const processed: ProcessedAssignment = {
        id: assignment.id,
        abbreviation:
          assignment.activity_override ||
          template?.display_abbreviation ||
          template?.abbreviation ||
          template?.name?.substring(0, 3).toUpperCase() ||
          '???',
        activityType: template?.activity_type || 'default',
        templateName: template?.name,
        role: assignment.role,
        notes: assignment.notes || undefined,
        personId: assignment.person_id,
        personName: person?.name || 'Unknown',
        blockId: assignment.block_id,
        rotationTemplateId: assignment.rotation_template_id,
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
  }, [assignmentsData, blockMap, templateMap, peopleData])

  // Group RESIDENTS only by PGY level (filter out faculty)
  const residentGroups = useMemo((): PersonGroup[] => {
    if (!peopleData?.items) return []

    const pgy1: Person[] = []
    const pgy2: Person[] = []
    const pgy3: Person[] = []
    const pgyOther: Person[] = []

    peopleData.items.forEach((person) => {
      if (person.type === 'resident') {
        if (person.pgy_level === 1) {
          pgy1.push(person)
        } else if (person.pgy_level === 2) {
          pgy2.push(person)
        } else if (person.pgy_level === 3) {
          pgy3.push(person)
        } else {
          pgyOther.push(person)
        }
      }
    })

    // Sort each group by name
    const sortByName = (a: Person, b: Person) => a.name.localeCompare(b.name)
    pgy1.sort(sortByName)
    pgy2.sort(sortByName)
    pgy3.sort(sortByName)
    pgyOther.sort(sortByName)

    const groups: PersonGroup[] = []
    if (pgy1.length > 0) groups.push({ label: 'PGY-1', people: pgy1 })
    if (pgy2.length > 0) groups.push({ label: 'PGY-2', people: pgy2 })
    if (pgy3.length > 0) groups.push({ label: 'PGY-3', people: pgy3 })
    if (pgyOther.length > 0) groups.push({ label: 'Residents (Other)', people: pgyOther })

    return groups
  }, [peopleData])

  // Month labels for header
  const monthLabels = useMemo(() => getMonthLabels(startDate, endDate), [startDate, endDate])

  // Get person's assignment for a specific date and time
  const getAssignment = useCallback((
    personId: string,
    dateStr: string,
    timeOfDay: 'AM' | 'PM'
  ): ProcessedAssignment | undefined => {
    return assignmentLookup.get(personId)?.get(dateStr)?.get(timeOfDay)
  }, [assignmentLookup])

  // Check if a date is today
  const todayStr = format(new Date(), 'yyyy-MM-dd')

  // Get block info for a date
  const getBlockInfo = useCallback((dateStr: string) => {
    const block = blockByDateTimeMap.get(`${dateStr}-AM`)
    return {
      isHoliday: block?.is_holiday || false,
      holidayName: block?.holiday_name || undefined,
    }
  }, [blockByDateTimeMap])

  // Scroll to today
  const scrollToToday = useCallback(() => {
    if (scrollContainerRef.current) {
      const todayElement = scrollContainerRef.current.querySelector('[data-today="true"]')
      if (todayElement) {
        todayElement.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
      }
    }
  }, [])

  // Scroll to today on initial load
  useEffect(() => {
    const timer = setTimeout(scrollToToday, 500)
    return () => clearTimeout(timer)
  }, [scrollToToday])

  // Loading state
  const isLoading = blocksLoading || assignmentsLoading || peopleLoading || templatesLoading
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
        <span className="ml-2 text-gray-600">Loading academic year schedule...</span>
      </div>
    )
  }

  // Error state
  const error = blocksError || assignmentsError || peopleError || templatesError
  if (error) {
    return (
      <div className="p-4">
        <ErrorAlert message={error instanceof Error ? error.message : 'Failed to load schedule data'} />
      </div>
    )
  }

  // Performance safeguard - calculate cell count and require confirmation for large renders
  const residentCount = residentGroups.reduce((sum, g) => sum + g.people.length, 0)
  const totalCells = allDays.length * 2 * residentCount // days * AM/PM * residents
  const CELL_THRESHOLD = 5000

  if (!renderConfirmed && totalCells > CELL_THRESHOLD) {
    return (
      <div className="flex flex-col items-center justify-center h-64 p-8 text-center">
        <div className="text-amber-600 text-lg font-semibold mb-2">Large Dataset Warning</div>
        <p className="text-gray-600 mb-4">
          This view would render <strong>{totalCells.toLocaleString()}</strong> cells
          ({residentCount} residents × {allDays.length} days × 2 half-days).
          <br />
          This may cause your browser to slow down or freeze.
        </p>
        <div className="flex gap-3">
          <button
            onClick={() => setRenderConfirmed(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Render Anyway
          </button>
          <button
            onClick={() => {
              localStorage.setItem('schedule-view-preference', 'block')
              window.location.href = '/schedule?view=block'
            }}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Switch to Block View
          </button>
        </div>
      </div>
    )
  }

  // Empty state - no residents
  if (residentGroups.length === 0) {
    return (
      <EmptyState
        title="No Residents Found"
        description="Add residents to see them in the academic year view."
        action={{
          label: 'Add People',
          onClick: () => (window.location.href = '/people'),
        }}
      />
    )
  }

  return (
    <ScheduleDragProvider blockLookup={blockMap}>
      <div className="flex flex-col h-full">
        {/* Controls */}
        <div className="flex-shrink-0 flex items-center justify-between gap-4 mb-4 px-2">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSelectedYear(y => y - 1)}
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              title="Previous academic year"
              aria-label="Previous academic year"
            >
              <ChevronLeft className="w-4 h-4" aria-hidden="true" />
            </button>
            <span className="text-lg font-semibold text-gray-900 min-w-[140px] text-center">
              AY {selectedYear}-{selectedYear + 1}
            </span>
            <button
              onClick={() => setSelectedYear(y => y + 1)}
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              title="Next academic year"
              aria-label="Next academic year"
            >
              <ChevronRight className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={scrollToToday}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors text-sm"
            >
              <Calendar className="w-4 h-4" />
              Today
            </button>
            <div className="flex items-center border border-gray-200 rounded-lg" role="group" aria-label="Zoom controls">
              <button
                onClick={() => setZoomLevel('compact')}
                className={`p-2 rounded-l-lg transition-colors ${zoomLevel === 'compact' ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50'}`}
                title="Compact view"
                aria-label="Compact view"
                aria-pressed={zoomLevel === 'compact'}
              >
                <ZoomOut className="w-4 h-4" aria-hidden="true" />
              </button>
              <button
                onClick={() => setZoomLevel('normal')}
                className={`p-2 rounded-r-lg transition-colors ${zoomLevel === 'normal' ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50'}`}
                title="Normal view"
                aria-label="Normal view"
                aria-pressed={zoomLevel === 'normal'}
              >
                <ZoomIn className="w-4 h-4" aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="flex-shrink-0 flex items-center gap-3 text-xs mb-3 px-2 overflow-x-auto">
          <span className="text-gray-500 font-medium">Legend:</span>
          <span className="inline-flex items-center gap-1 whitespace-nowrap">
            <span className="w-3 h-3 rounded bg-blue-100 border border-blue-300"></span>
            Clinic
          </span>
          <span className="inline-flex items-center gap-1 whitespace-nowrap">
            <span className="w-3 h-3 rounded bg-purple-100 border border-purple-300"></span>
            Inpatient
          </span>
          <span className="inline-flex items-center gap-1 whitespace-nowrap">
            <span className="w-3 h-3 rounded bg-red-100 border border-red-300"></span>
            Procedure
          </span>
          <span className="inline-flex items-center gap-1 whitespace-nowrap">
            <span className="w-3 h-3 rounded bg-orange-100 border border-orange-300"></span>
            Call
          </span>
          <span className="inline-flex items-center gap-1 whitespace-nowrap">
            <span className="w-3 h-3 rounded bg-green-100 border border-green-300"></span>
            Elective
          </span>
          <span className="inline-flex items-center gap-1 whitespace-nowrap">
            <span className="w-3 h-3 rounded bg-amber-100 border border-amber-300"></span>
            Leave
          </span>
        </div>

        {/* Grid Container */}
        <motion.div
          ref={scrollContainerRef}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="flex-1 overflow-auto glass-panel"
        >
          <table className="min-w-full border-collapse">
            {/* Month header row */}
            <thead className="sticky top-0 z-30 bg-white">
              <tr>
                <th
                  className="sticky left-0 z-40 bg-white px-3 py-1 text-left text-xs font-medium text-gray-500 border-b border-r border-gray-200"
                  rowSpan={2}
                >
                  Resident
                </th>
                {monthLabels.map((m, idx) => (
                  <th
                    key={idx}
                    colSpan={m.span * 7 * 2} // Each week has 7 days * 2 (AM/PM)
                    className={`px-2 py-1 text-center text-xs font-semibold border-b border-gray-200 ${
                      m.isOdd ? 'bg-gray-50' : 'bg-white'
                    }`}
                  >
                    {m.month}
                  </th>
                ))}
              </tr>
              {/* Week numbers / dates header */}
              <tr className="bg-gray-50">
                {weeks.map((weekStart, idx) => {
                  const weekNum = idx + 1
                  return (
                    <th
                      key={idx}
                      colSpan={14} // 7 days * 2 (AM/PM)
                      className="px-1 py-0.5 text-center text-[10px] font-normal text-gray-400 border-b border-r border-gray-200"
                      title={`Week ${weekNum}: ${format(weekStart, 'MMM d')} - ${format(addDays(weekStart, 6), 'MMM d')}`}
                    >
                      W{weekNum}
                    </th>
                  )
                })}
              </tr>
            </thead>

            <tbody className="bg-white divide-y divide-gray-100">
              {residentGroups.map((group, groupIndex) => (
                <ResidentGroupRows
                  key={group.label}
                  group={group}
                  days={allDays}
                  todayStr={todayStr}
                  getAssignment={getAssignment}
                  getBlockInfo={getBlockInfo}
                  showSeparator={groupIndex > 0}
                  compact={zoomLevel === 'compact'}
                />
              ))}
            </tbody>
          </table>
        </motion.div>

        {/* Info bar */}
        <div className="flex-shrink-0 mt-2 text-xs text-gray-500 px-2">
          <span>
            Showing {allDays.length} days ({weeks.length} weeks) •
            Drag assignments horizontally to reschedule within a resident&apos;s row
          </span>
        </div>
      </div>
    </ScheduleDragProvider>
  )
}

// Component for rendering a group of residents
interface ResidentGroupRowsProps {
  group: PersonGroup
  days: Date[]
  todayStr: string
  getAssignment: (personId: string, dateStr: string, timeOfDay: 'AM' | 'PM') => ProcessedAssignment | undefined
  getBlockInfo: (dateStr: string) => { isHoliday: boolean; holidayName?: string }
  showSeparator: boolean
  compact: boolean
}

function ResidentGroupRows({
  group,
  days,
  todayStr,
  getAssignment,
  getBlockInfo,
  showSeparator,
  compact,
}: ResidentGroupRowsProps) {
  return (
    <>
      {/* Separator row */}
      {showSeparator && (
        <YearViewSeparatorRow label={group.label} columnCount={days.length} />
      )}

      {/* First group also needs a separator */}
      {!showSeparator && (
        <YearViewSeparatorRow label={group.label} columnCount={days.length} />
      )}

      {/* Person rows */}
      {group.people.map((person) => (
        <ResidentYearRow
          key={person.id}
          person={person}
          days={days}
          todayStr={todayStr}
          getAssignment={getAssignment}
          getBlockInfo={getBlockInfo}
          compact={compact}
        />
      ))}
    </>
  )
}

// Component for a single resident's year row
interface ResidentYearRowProps {
  person: Person
  days: Date[]
  todayStr: string
  getAssignment: (personId: string, dateStr: string, timeOfDay: 'AM' | 'PM') => ProcessedAssignment | undefined
  getBlockInfo: (dateStr: string) => { isHoliday: boolean; holidayName?: string }
  compact: boolean
}

function ResidentYearRow({
  person,
  days,
  todayStr,
  getAssignment,
  getBlockInfo,
  compact,
}: ResidentYearRowProps) {
  return (
    <tr className="hover:bg-gray-50/50">
      {/* Sticky person name column */}
      <td className="sticky left-0 z-10 bg-white px-3 py-1.5 border-r border-gray-200 shadow-[2px_0_4px_-2px_rgba(0,0,0,0.1)] min-w-[140px]">
        <div className="flex flex-col gap-0.5">
          <span className="font-medium text-gray-900 text-sm whitespace-nowrap truncate max-w-[120px]" title={person.name}>
            {person.name}
          </span>
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-100 text-blue-800 w-fit">
            PGY-{person.pgy_level}
          </span>
        </div>
      </td>

      {/* Day cells - AM and PM for each day */}
      {days.map((day) => {
        const dateStr = format(day, 'yyyy-MM-dd')
        const weekend = isWeekend(day)
        const isToday = dateStr === todayStr
        const { isHoliday, holidayName } = getBlockInfo(dateStr)

        const amAssignment = getAssignment(person.id, dateStr, 'AM')
        const pmAssignment = getAssignment(person.id, dateStr, 'PM')

        return (
          <YearDayCells
            key={dateStr}
            person={person}
            dateStr={dateStr}
            isWeekend={weekend}
            isToday={isToday}
            isHoliday={isHoliday}
            holidayName={holidayName}
            amAssignment={amAssignment}
            pmAssignment={pmAssignment}
            compact={compact}
          />
        )
      })}
    </tr>
  )
}

// Component for AM/PM cells for a single day
interface YearDayCellsProps {
  person: Person
  dateStr: string
  isWeekend: boolean
  isToday: boolean
  isHoliday: boolean
  holidayName?: string
  amAssignment?: ProcessedAssignment
  pmAssignment?: ProcessedAssignment
  compact: boolean
}

function YearDayCells({
  person,
  dateStr,
  isWeekend,
  isToday,
  isHoliday,
  holidayName,
  amAssignment,
  pmAssignment,
  compact,
}: YearDayCellsProps) {
  return (
    <>
      <DraggableBlockCell
        assignment={amAssignment}
        personId={person.id}
        personName={person.name}
        date={dateStr}
        timeOfDay="AM"
        isWeekend={isWeekend}
        isToday={isToday}
        isHoliday={isHoliday}
        holidayName={holidayName}
        compact={compact}
      />
      <DraggableBlockCell
        assignment={pmAssignment}
        personId={person.id}
        personName={person.name}
        date={dateStr}
        timeOfDay="PM"
        isWeekend={isWeekend}
        isToday={isToday}
        isHoliday={isHoliday}
        holidayName={holidayName}
        compact={compact}
      />
    </>
  )
}
