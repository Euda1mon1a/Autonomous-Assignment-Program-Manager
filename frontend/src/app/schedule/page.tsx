'use client'

import { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { startOfWeek, addDays, format, startOfMonth, endOfMonth, eachDayOfInterval, parseISO } from 'date-fns'
import { useQueryClient } from '@tanstack/react-query'
import { Upload, Download } from 'lucide-react'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { BlockNavigation } from '@/components/schedule/BlockNavigation'
import { ScheduleGrid } from '@/components/schedule/ScheduleGrid'
import { ViewToggle, useScheduleView } from '@/components/schedule/ViewToggle'
import { MonthView } from '@/components/schedule/MonthView'
import { WeekView } from '@/components/schedule/WeekView'
import { DayView } from '@/components/schedule/DayView'
import { BlockAnnualView } from '@/components/schedule/BlockAnnualView'
import { BlockWeekView } from '@/components/schedule/BlockWeekView'
import { MultiSelectPersonFilter } from '@/components/schedule/MultiSelectPersonFilter'
import { ResidentAcademicYearView, FacultyInpatientWeeksView } from '@/components/schedule/drag'
import { BlockAssignmentImportModal } from '@/components/admin/BlockAssignmentImportModal'
import { BlockAssignmentExportModal } from '@/components/admin/BlockAssignmentExportModal'
import { usePeople, useRotationTemplates, useBlockRanges } from '@/lib/hooks'
import { useAssignmentsForRange, useBlocksForRange } from '@/hooks/useAssignmentsForRange'
import { useRole } from '@/hooks/useAuth'
import { useScheduleWebSocket } from '@/hooks/useWebSocket'
import { WebSocketStatus } from '@/components/ui/WebSocketStatus'
import type { Block, RotationTemplate } from '@/types/api'

/**
 * Schedule Page - The core schedule viewing feature
 *
 * Displays the entire block schedule showing who is assigned where
 * on a half-day (AM/PM) basis. Supports multiple views: Day, Week, Month, Block.
 *
 * Features:
 * - Multiple view modes (Day, Week, Month, Block)
 * - Grid layout with people as rows, days as columns with AM/PM sub-columns
 * - Color-coded rotation types for quick visual identification
 * - Sticky left column (person names) and top header (dates)
 * - Navigation: Previous/Next, Today, date pickers
 * - People grouped by PGY level with visual separators
 */

// Schedule data format for Day/Week/Month views
interface ViewAssignment {
  id: string
  person: {
    id: string
    name: string
    type: string
    pgyLevel: number | null
  }
  role: string
  activity: string
  abbreviation: string
}

interface ScheduleData {
  [date: string]: {
    AM: ViewAssignment[]
    PM: ViewAssignment[]
  }
}

export default function SchedulePage() {
  // View state with localStorage persistence
  const [currentView, setCurrentView] = useScheduleView('block')

  // Current date for Day/Week/Month views
  const [currentDate, setCurrentDate] = useState(() => new Date())

  // Person filter for comparing schedules (multi-select)
  const [selectedPersonIds, setSelectedPersonIds] = useState<Set<string>>(new Set())

  // Import/Export modal state
  const [showImportModal, setShowImportModal] = useState(false)
  const [showExportModal, setShowExportModal] = useState(false)

  // Role check for admin/coordinator features
  const { isAdmin, isCoordinator } = useRole()
  const canManageAssignments = isAdmin || isCoordinator

  // WebSocket for live updates - invalidate queries when schedule changes
  // Backend now supports both token query param AND httpOnly cookie auth
  const queryClient = useQueryClient()
  const { connectionState, reconnectAttempts } = useScheduleWebSocket(undefined, {
    onMessage: (event) => {
      if (event.eventType === 'schedule_updated' || event.eventType === 'assignment_changed') {
        // Invalidate all schedule-related queries to trigger refetch
        queryClient.invalidateQueries({ queryKey: ['blocks'] })
        queryClient.invalidateQueries({ queryKey: ['assignments'] })
        queryClient.invalidateQueries({ queryKey: ['block-assignments'] })
      }
    },
  })

  // Fetch block ranges from API to get actual block boundaries
  const { data: blockRanges } = useBlockRanges()

  // Track if we've already initialized from API data
  const hasInitializedFromApi = useRef(false)

  // Initialize with a temporary fallback (will be updated once API data arrives)
  // Using today's date as a reasonable starting point before API data loads
  const getInitialDates = () => {
    const today = new Date()
    // Temporary fallback: start from today, show 28 days
    // This will be replaced by actual block data from the API
    return {
      start: today,
      end: addDays(today, 27),
    }
  }

  const [dateRange, setDateRange] = useState(getInitialDates)

  // Update date range once we have block data from the API
  // Find the block that contains today's date and use its actual boundaries
  useEffect(() => {
    if (blockRanges?.length && !hasInitializedFromApi.current) {
      const today = format(new Date(), 'yyyy-MM-dd')
      const todayBlock = blockRanges.find(
        (range) => range.startDate <= today && range.endDate >= today
      )

      if (todayBlock) {
        hasInitializedFromApi.current = true
        setDateRange({
          start: parseISO(todayBlock.startDate),
          end: parseISO(todayBlock.endDate),
        })
      }
    }
  }, [blockRanges])

  // Calculate date range based on current view
  const viewDateRange = useMemo(() => {
    switch (currentView) {
      case 'day':
        return { start: currentDate, end: currentDate }
      case 'week':
        const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 })
        return { start: weekStart, end: addDays(weekStart, 6) }
      case 'month':
        return { start: startOfMonth(currentDate), end: endOfMonth(currentDate) }
      case 'block':
      default:
        return dateRange
    }
  }, [currentView, currentDate, dateRange])

  // Fetch data for Day/Week/Month views
  const startDateStr = format(viewDateRange.start, 'yyyy-MM-dd')
  const endDateStr = format(viewDateRange.end, 'yyyy-MM-dd')

  // Use multi-page pagination hooks for Month/Week/Day views
  // These fetch ALL assignments/blocks, not just the first page
  const enableFetch = currentView !== 'block'
  const { data: blocksData } = useBlocksForRange(startDateStr, endDateStr, enableFetch)
  const { data: assignmentsData } = useAssignmentsForRange(startDateStr, endDateStr, enableFetch)

  const { data: peopleData } = usePeople()
  const { data: templatesData } = useRotationTemplates()

  // Transform data into format for Day/Week/Month views
  const scheduleData = useMemo<ScheduleData>(() => {
    if (!blocksData?.items || !assignmentsData?.items || !peopleData?.items) {
      return {}
    }

    const blockMap = new Map<string, Block>()
    blocksData.items.forEach((block) => blockMap.set(block.id, block))

    const templateMap = new Map<string, RotationTemplate>()
    templatesData?.items?.forEach((template) => templateMap.set(template.id, template))

    const personMap = new Map<string, typeof peopleData.items[0]>()
    peopleData.items.forEach((person) => personMap.set(person.id, person))

    const schedule: ScheduleData = {}

    // Initialize all dates in range
    const days = eachDayOfInterval({ start: viewDateRange.start, end: viewDateRange.end })
    days.forEach((day) => {
      const dateStr = format(day, 'yyyy-MM-dd')
      schedule[dateStr] = { AM: [], PM: [] }
    })

    // Populate assignments
    assignmentsData.items.forEach((assignment) => {
      const block = blockMap.get(assignment.blockId)
      if (!block) return

      const person = personMap.get(assignment.personId)
      if (!person) return

      const template = assignment.rotationTemplateId
        ? templateMap.get(assignment.rotationTemplateId)
        : null

      const viewAssignment: ViewAssignment = {
        id: assignment.id,
        person: {
          id: person.id,
          name: person.name,
          type: person.type,
          pgyLevel: person.pgyLevel,
        },
        role: assignment.role || 'primary',
        activity: template?.activityType || 'default',
        abbreviation:
          assignment.activityOverride ||
          template?.displayAbbreviation ||
          template?.abbreviation ||
          template?.name?.substring(0, 3).toUpperCase() ||
          '???',
      }

      const dateStr = block.date
      if (schedule[dateStr]) {
        schedule[dateStr][block.timeOfDay as 'AM' | 'PM'].push(viewAssignment)
      }
    })

    return schedule
  }, [blocksData, assignmentsData, peopleData, templatesData, viewDateRange])

  // Handler for date range changes from block navigation
  const handleDateRangeChange = useCallback((start: Date, end: Date) => {
    setDateRange({ start, end })
  }, [])

  // Handler for date changes from other views
  const handleDateChange = useCallback((date: Date) => {
    setCurrentDate(date)
  }, [])

  // Handler for day click (switch to day view)
  const handleDayClick = useCallback((date: Date) => {
    setCurrentDate(date)
    setCurrentView('day')
  }, [setCurrentView])

  return (
    <ProtectedRoute>
      <div className="h-screen flex flex-col bg-gray-50">
        {/* Header with title and navigation */}
        <div className="flex-shrink-0 bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-full px-4 py-4">
            {/* Title row */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-4">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Schedule</h1>
                  <p className="text-sm text-gray-600 mt-1">
                    View and manage rotation assignments
                  </p>
                </div>

                {/* WebSocket connection status */}
                <WebSocketStatus
                  connectionState={connectionState}
                  reconnectAttempts={reconnectAttempts}
                />

                {/* Person Filter - show for block-annual, block, and block-week views */}
                {['block-annual', 'block', 'block-week'].includes(currentView) && (
                  <MultiSelectPersonFilter
                    selectedPersonIds={selectedPersonIds}
                    onSelectionChange={setSelectedPersonIds}
                    residentsOnly={currentView === 'block-annual'}
                    emptyLabel={currentView === 'block-annual' ? 'All Residents' : 'All People'}
                  />
                )}

                {/* Import/Export buttons - admin/coordinator only, block views only */}
                {canManageAssignments && ['block-annual', 'block', 'block-week'].includes(currentView) && (
                  <div className="flex items-center gap-2 ml-4 pl-4 border-l border-gray-300">
                    <button
                      onClick={() => setShowImportModal(true)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                    >
                      <Upload className="w-4 h-4" />
                      Import
                    </button>
                    <button
                      onClick={() => setShowExportModal(true)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                    >
                      <Download className="w-4 h-4" />
                      Export
                    </button>
                  </div>
                )}
              </div>

              {/* View Toggle */}
              <ViewToggle currentView={currentView} onChange={setCurrentView} />

              {/* Legend - only show for block view */}
              {currentView === 'block' && (
                <div className="hidden xl:flex items-center gap-3 text-xs">
                  <span className="text-gray-500 font-medium">Legend:</span>
                  <span className="inline-flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-blue-100 border border-blue-300"></span>
                    Clinic
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-purple-100 border border-purple-300"></span>
                    Inpatient
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-red-100 border border-red-300"></span>
                    Procedure
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-orange-100 border border-orange-300"></span>
                    Call
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-green-100 border border-green-300"></span>
                    Elective
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-gray-100 border border-gray-300"></span>
                    Conference
                  </span>
                </div>
              )}
            </div>

            {/* Navigation row - for block and block-week views */}
            {['block', 'block-week'].includes(currentView) && (
              <BlockNavigation
                startDate={dateRange.start}
                endDate={dateRange.end}
                onDateRangeChange={handleDateRangeChange}
              />
            )}
          </div>
        </div>

        {/* Schedule content */}
        <div className="flex-1 overflow-auto p-4">
          {currentView === 'block-annual' && (
            <BlockAnnualView
              personFilter={selectedPersonIds}
              onBlockClick={(blockNumber) => {
                // Navigate to block view for the clicked block
                if (blockRanges) {
                  const range = blockRanges.find((r) => r.blockNumber === blockNumber)
                  if (range) {
                    setDateRange({
                      start: parseISO(range.startDate),
                      end: parseISO(range.endDate),
                    })
                    setCurrentView('block')
                  }
                }
              }}
            />
          )}
          {currentView === 'block' && (
            <ScheduleGrid
              startDate={dateRange.start}
              endDate={dateRange.end}
              personFilter={selectedPersonIds}
            />
          )}
          {currentView === 'block-week' && (
            <BlockWeekView
              blockStartDate={dateRange.start}
              blockEndDate={dateRange.end}
              blockNumber={
                blockRanges?.find(
                  (r) =>
                    r.startDate === format(dateRange.start, 'yyyy-MM-dd') &&
                    r.endDate === format(dateRange.end, 'yyyy-MM-dd')
                )?.blockNumber ?? null
              }
              personFilter={selectedPersonIds}
            />
          )}
          {currentView === 'month' && (
            <MonthView
              currentDate={currentDate}
              schedule={scheduleData}
              onDateChange={handleDateChange}
              onDayClick={handleDayClick}
            />
          )}
          {currentView === 'week' && (
            <WeekView
              currentDate={currentDate}
              schedule={scheduleData}
              onDateChange={handleDateChange}
              onDayClick={handleDayClick}
            />
          )}
          {currentView === 'day' && (
            <DayView
              currentDate={currentDate}
              schedule={scheduleData}
              onDateChange={handleDateChange}
            />
          )}
          {currentView === 'resident-year' && (
            <ResidentAcademicYearView />
          )}
          {currentView === 'faculty-inpatient' && (
            <FacultyInpatientWeeksView />
          )}
        </div>

        {/* Footer - only show for standard views, block-week and annual views have their own */}
        {!['block-annual', 'block-week', 'resident-year', 'faculty-inpatient'].includes(currentView) && (
          <div className="flex-shrink-0 bg-white border-t border-gray-200 px-4 py-2">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>
                {currentView === 'block'
                  ? 'Hover over assignments to see details. Click on a cell to view or edit.'
                  : 'Click on a day to view details. Use the view toggle to switch between views.'}
              </span>
              <span className="hidden sm:inline">
                {currentView === 'block' && (
                  <>Showing {Math.ceil((dateRange.end.getTime() - dateRange.start.getTime()) / (1000 * 60 * 60 * 24)) + 1} days</>
                )}
                {currentView === 'month' && format(currentDate, 'MMMM yyyy')}
                {currentView === 'week' && `Week of ${format(startOfWeek(currentDate, { weekStartsOn: 1 }), 'MMM d')}`}
                {currentView === 'day' && format(currentDate, 'EEEE, MMMM d, yyyy')}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Import/Export Modals */}
      <BlockAssignmentImportModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
      />
      <BlockAssignmentExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
      />
    </ProtectedRoute>
  )
}
