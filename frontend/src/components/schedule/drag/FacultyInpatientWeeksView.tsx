'use client'

import { useMemo, useState, useCallback, useRef, useEffect } from 'react'
import { format, eachWeekOfInterval, addDays, isWeekend, eachDayOfInterval, getMonth } from 'date-fns'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Calendar, Users } from 'lucide-react'
import { get } from '@/lib/api'
import { usePeople, useRotationTemplates, ListResponse } from '@/lib/hooks'
import type { Person, RotationTemplate, Assignment, Block } from '@/types/api'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorAlert } from '@/components/ErrorAlert'
import { EmptyState } from '@/components/EmptyState'
import { ScheduleDragProvider } from './ScheduleDragProvider'
import { DraggableBlockCell, YearViewSeparatorRow } from './DraggableBlockCell'

interface FacultyInpatientWeeksViewProps {
  // Initial date range (default: current academic year)
  academicYear?: number
  startMonth?: number
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

// Academic year typically runs July 1 to June 30
function getAcademicYearDates(year: number, startMonth: number = 6) {
  const startDate = new Date(year, startMonth, 1)
  const endDate = new Date(year + 1, 5, 30) // June 30 of next year
  return { startDate, endDate }
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

  if (currentSpan > 0) {
    months.push({ month: currentLabel, span: currentSpan, isOdd: currentMonth % 2 === 1 })
  }

  return months
}

// Count inpatient weeks for a faculty member
function countInpatientWeeks(
  facultyId: string,
  assignmentLookup: Map<string, Map<string, Map<string, ProcessedAssignment>>>,
  weeks: Date[]
): number {
  let count = 0
  const personMap = assignmentLookup.get(facultyId)
  if (!personMap) return 0

  weeks.forEach((weekStart) => {
    // Check if any day in the week has an inpatient assignment
    for (let i = 0; i < 7; i++) {
      const dateStr = format(addDays(weekStart, i), 'yyyy-MM-dd')
      const dateMap = personMap.get(dateStr)
      if (dateMap) {
        const am = dateMap.get('AM')
        const pm = dateMap.get('PM')
        if (
          (am && am.activityType?.toLowerCase() === 'inpatient') ||
          (pm && pm.activityType?.toLowerCase() === 'inpatient')
        ) {
          count++
          break // Count this as one inpatient week
        }
      }
    }
  })

  return count
}

export function FacultyInpatientWeeksView({
  academicYear = new Date().getMonth() >= 6 ? new Date().getFullYear() : new Date().getFullYear() - 1,
  startMonth = 6,
}: FacultyInpatientWeeksViewProps) {
  const [selectedYear, setSelectedYear] = useState(academicYear)
  const [zoomLevel, setZoomLevel] = useState<'compact' | 'normal'>('compact')
  const [showAllActivities, setShowAllActivities] = useState(false)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

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

  // Generate all days
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

  // Create assignment lookup
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

      if (!lookup.has(assignment.person_id)) {
        lookup.set(assignment.person_id, new Map())
      }
      const personMap = lookup.get(assignment.person_id)!

      const dateStr = block.date
      if (!personMap.has(dateStr)) {
        personMap.set(dateStr, new Map())
      }
      const dateMap = personMap.get(dateStr)!

      dateMap.set(block.time_of_day, processed)
    })

    return lookup
  }, [assignmentsData, blockMap, templateMap, peopleData])

  // Get FACULTY only, sorted by inpatient weeks (descending)
  const facultyMembers = useMemo((): (Person & { inpatientWeeks: number })[] => {
    if (!peopleData?.items) return []

    const faculty = peopleData.items
      .filter(person => person.type === 'faculty')
      .map(person => ({
        ...person,
        inpatientWeeks: countInpatientWeeks(person.id, assignmentLookup, weeks),
      }))
      .sort((a, b) => b.inpatientWeeks - a.inpatientWeeks)

    return faculty
  }, [peopleData, assignmentLookup, weeks])

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

  const todayStr = format(new Date(), 'yyyy-MM-dd')

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

  useEffect(() => {
    const timer = setTimeout(scrollToToday, 500)
    return () => clearTimeout(timer)
  }, [scrollToToday])

  // Calculate summary stats
  const stats = useMemo(() => {
    const totalInpatientWeeks = facultyMembers.reduce((sum, f) => sum + f.inpatientWeeks, 0)
    const avgInpatientWeeks = facultyMembers.length > 0 ? totalInpatientWeeks / facultyMembers.length : 0
    const maxInpatientWeeks = facultyMembers.length > 0 ? Math.max(...facultyMembers.map(f => f.inpatientWeeks)) : 0
    const minInpatientWeeks = facultyMembers.length > 0 ? Math.min(...facultyMembers.map(f => f.inpatientWeeks)) : 0
    return { totalInpatientWeeks, avgInpatientWeeks, maxInpatientWeeks, minInpatientWeeks }
  }, [facultyMembers])

  // Loading state
  const isLoading = blocksLoading || assignmentsLoading || peopleLoading || templatesLoading
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
        <span className="ml-2 text-gray-600">Loading faculty inpatient schedule...</span>
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

  // Empty state - no faculty
  if (facultyMembers.length === 0) {
    return (
      <EmptyState
        title="No Faculty Found"
        description="Add faculty members to see their inpatient schedule."
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
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-lg font-semibold text-gray-900 min-w-[140px] text-center">
              AY {selectedYear}-{selectedYear + 1}
            </span>
            <button
              onClick={() => setSelectedYear(y => y + 1)}
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              title="Next academic year"
            >
              <ChevronRight className="w-4 h-4" />
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
            <button
              onClick={() => setShowAllActivities(v => !v)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-colors text-sm ${
                showAllActivities ? 'bg-purple-50 border-purple-300 text-purple-700' : 'border-gray-200 hover:bg-gray-50'
              }`}
              title={showAllActivities ? 'Show all activities' : 'Show inpatient only'}
            >
              <Users className="w-4 h-4" />
              {showAllActivities ? 'All' : 'Inpatient'}
            </button>
            <div className="flex items-center border border-gray-200 rounded-lg">
              <button
                onClick={() => setZoomLevel('compact')}
                className={`p-2 rounded-l-lg transition-colors ${zoomLevel === 'compact' ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50'}`}
                title="Compact view"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <button
                onClick={() => setZoomLevel('normal')}
                className={`p-2 rounded-r-lg transition-colors ${zoomLevel === 'normal' ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50'}`}
                title="Normal view"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="flex-shrink-0 grid grid-cols-4 gap-3 mb-4 px-2">
          <div className="bg-purple-50 border border-purple-200 rounded-lg px-3 py-2">
            <div className="text-xs text-purple-600 font-medium">Total Inpatient Wks</div>
            <div className="text-xl font-bold text-purple-800">{stats.totalInpatientWeeks}</div>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
            <div className="text-xs text-blue-600 font-medium">Avg per Faculty</div>
            <div className="text-xl font-bold text-blue-800">{stats.avgInpatientWeeks.toFixed(1)}</div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg px-3 py-2">
            <div className="text-xs text-green-600 font-medium">Max Weeks</div>
            <div className="text-xl font-bold text-green-800">{stats.maxInpatientWeeks}</div>
          </div>
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
            <div className="text-xs text-amber-600 font-medium">Min Weeks</div>
            <div className="text-xl font-bold text-amber-800">{stats.minInpatientWeeks}</div>
          </div>
        </div>

        {/* Legend */}
        <div className="flex-shrink-0 flex items-center gap-3 text-xs mb-3 px-2 overflow-x-auto">
          <span className="text-gray-500 font-medium">Legend:</span>
          <span className="inline-flex items-center gap-1 whitespace-nowrap">
            <span className="w-3 h-3 rounded bg-purple-100 border border-purple-300"></span>
            Inpatient
          </span>
          {showAllActivities && (
            <>
              <span className="inline-flex items-center gap-1 whitespace-nowrap">
                <span className="w-3 h-3 rounded bg-blue-100 border border-blue-300"></span>
                Clinic
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
                <span className="w-3 h-3 rounded bg-amber-100 border border-amber-300"></span>
                Leave
              </span>
            </>
          )}
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
                  className="sticky left-0 z-40 bg-white px-3 py-1 text-left text-xs font-medium text-gray-500 border-b border-r border-gray-200 min-w-[160px]"
                  rowSpan={2}
                >
                  <div className="flex flex-col gap-0.5">
                    <span>Faculty</span>
                    <span className="text-[10px] text-gray-400 font-normal">Inpt. Weeks</span>
                  </div>
                </th>
                {monthLabels.map((m, idx) => (
                  <th
                    key={idx}
                    colSpan={m.span * 7 * 2}
                    className={`px-2 py-1 text-center text-xs font-semibold border-b border-gray-200 ${
                      m.isOdd ? 'bg-gray-50' : 'bg-white'
                    }`}
                  >
                    {m.month}
                  </th>
                ))}
              </tr>
              {/* Week numbers header */}
              <tr className="bg-gray-50">
                {weeks.map((weekStart, idx) => {
                  const weekNum = idx + 1
                  return (
                    <th
                      key={idx}
                      colSpan={14}
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
              {/* Section header */}
              <YearViewSeparatorRow
                label={`Faculty (${facultyMembers.length})`}
                columnCount={allDays.length}
              />

              {/* Faculty rows */}
              {facultyMembers.map((faculty) => (
                <FacultyYearRow
                  key={faculty.id}
                  faculty={faculty}
                  days={allDays}
                  todayStr={todayStr}
                  getAssignment={getAssignment}
                  getBlockInfo={getBlockInfo}
                  compact={zoomLevel === 'compact'}
                  showAllActivities={showAllActivities}
                />
              ))}
            </tbody>
          </table>
        </motion.div>

        {/* Info bar */}
        <div className="flex-shrink-0 mt-2 text-xs text-gray-500 px-2">
          <span>
            Showing {weeks.length} weeks • {facultyMembers.length} faculty members •
            Drag inpatient assignments horizontally to reschedule
          </span>
        </div>
      </div>
    </ScheduleDragProvider>
  )
}

// Component for a single faculty member's year row
interface FacultyYearRowProps {
  faculty: Person & { inpatientWeeks: number }
  days: Date[]
  todayStr: string
  getAssignment: (personId: string, dateStr: string, timeOfDay: 'AM' | 'PM') => ProcessedAssignment | undefined
  getBlockInfo: (dateStr: string) => { isHoliday: boolean; holidayName?: string }
  compact: boolean
  showAllActivities: boolean
}

function FacultyYearRow({
  faculty,
  days,
  todayStr,
  getAssignment,
  getBlockInfo,
  compact,
  showAllActivities,
}: FacultyYearRowProps) {
  return (
    <tr className="hover:bg-gray-50/50">
      {/* Sticky faculty name column with inpatient week count */}
      <td className="sticky left-0 z-10 bg-white px-3 py-1.5 border-r border-gray-200 shadow-[2px_0_4px_-2px_rgba(0,0,0,0.1)] min-w-[160px]">
        <div className="flex items-center justify-between gap-2">
          <div className="flex flex-col gap-0.5">
            <span className="font-medium text-gray-900 text-sm whitespace-nowrap truncate max-w-[100px]" title={faculty.name}>
              {faculty.name}
            </span>
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-indigo-100 text-indigo-800 w-fit">
              Faculty
            </span>
          </div>
          <span
            className={`text-lg font-bold ${
              faculty.inpatientWeeks > 0 ? 'text-purple-600' : 'text-gray-300'
            }`}
            title={`${faculty.inpatientWeeks} inpatient weeks`}
          >
            {faculty.inpatientWeeks}
          </span>
        </div>
      </td>

      {/* Day cells */}
      {days.map((day) => {
        const dateStr = format(day, 'yyyy-MM-dd')
        const weekend = isWeekend(day)
        const isToday = dateStr === todayStr
        const { isHoliday, holidayName } = getBlockInfo(dateStr)

        const amAssignment = getAssignment(faculty.id, dateStr, 'AM')
        const pmAssignment = getAssignment(faculty.id, dateStr, 'PM')

        // Filter to inpatient only unless showing all
        const filteredAm = showAllActivities || amAssignment?.activityType?.toLowerCase() === 'inpatient' ? amAssignment : undefined
        const filteredPm = showAllActivities || pmAssignment?.activityType?.toLowerCase() === 'inpatient' ? pmAssignment : undefined

        return (
          <FacultyDayCells
            key={dateStr}
            faculty={faculty}
            dateStr={dateStr}
            isWeekend={weekend}
            isToday={isToday}
            isHoliday={isHoliday}
            holidayName={holidayName}
            amAssignment={filteredAm}
            pmAssignment={filteredPm}
            compact={compact}
          />
        )
      })}
    </tr>
  )
}

// Component for AM/PM cells for a faculty member's day
interface FacultyDayCellsProps {
  faculty: Person
  dateStr: string
  isWeekend: boolean
  isToday: boolean
  isHoliday: boolean
  holidayName?: string
  amAssignment?: ProcessedAssignment
  pmAssignment?: ProcessedAssignment
  compact: boolean
}

function FacultyDayCells({
  faculty,
  dateStr,
  isWeekend,
  isToday,
  isHoliday,
  holidayName,
  amAssignment,
  pmAssignment,
  compact,
}: FacultyDayCellsProps) {
  return (
    <>
      <DraggableBlockCell
        assignment={amAssignment}
        personId={faculty.id}
        personName={faculty.name}
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
        personId={faculty.id}
        personName={faculty.name}
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
