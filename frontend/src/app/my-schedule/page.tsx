'use client'

import { useState, useMemo, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { format, startOfWeek, addWeeks, addDays, subWeeks, startOfMonth, endOfMonth } from 'date-fns'
import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, Calendar, Download, Printer } from 'lucide-react'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { useAuth } from '@/contexts/AuthContext'
import { RiskBar } from '@/components/ui/RiskBar'
import { PersonSelector } from '@/components/schedule/PersonSelector'
import { PersonalScheduleCard, ScheduleAssignment } from '@/components/schedule/PersonalScheduleCard'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorAlert } from '@/components/ErrorAlert'
import { EmptyState } from '@/components/EmptyState'
import { ScheduleLegend } from '@/components/schedule/ScheduleLegend'
import { WorkHoursCalculator } from '@/components/schedule/WorkHoursCalculator'
import { PageBreadcrumbs } from '@/components/common/Breadcrumbs'
import { CopyUrlButton } from '@/components/common/CopyToClipboard'
import { useKeyboardShortcut } from '@/components/common/KeyboardShortcutHelp'
import { get } from '@/lib/api'
import { ListResponse, usePeople, useRotationTemplates } from '@/lib/hooks'
import { calculateTierFromRole, getRiskBarTooltip, getRiskBarLabel } from '@/lib/tierUtils'
import type { Assignment, Block, Person, RotationTemplate } from '@/types/api'

/**
 * My Schedule Page - Personal Schedule Hub
 *
 * Unified schedule viewing hub that consolidates:
 * - /my-schedule (personal schedule)
 * - /schedule/[personId] (viewing other's schedule)
 *
 * Access Control (Tier Model):
 * - Tier 0 (Resident/Faculty): View own schedule only, no person selector
 * - Tier 1 (Coordinator): Can view and export others' schedules via selector
 * - Tier 2 (Admin): Full access with high-impact indicator
 *
 * The person selector is NOT CSS-hidden for Tier 0 - it simply doesn't render.
 * This follows security best practices (no client-side security through obscurity).
 *
 * URL Parameters:
 * - ?person={personId} - View specific person's schedule (Tier 1+ only)
 */

type ViewRange = 'week' | '2weeks' | 'month'

function MyScheduleContent() {
  const { user } = useAuth()
  const searchParams = useSearchParams()
  const [viewRange, setViewRange] = useState<ViewRange>('2weeks')
  const [currentDate, setCurrentDate] = useState(() => new Date())

  // Calculate tier based on user role
  const tier = useMemo(() => calculateTierFromRole(user?.role), [user?.role])

  // Get person ID from URL if provided (for Tier 1+ users)
  const urlPersonId = searchParams.get('person')

  // Track if user is selecting a different person
  const [selectedPersonId, setSelectedPersonId] = useState<string | null>(urlPersonId)

  // Calculate date range based on selected view
  const dateRange = useMemo(() => {
    const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 })

    switch (viewRange) {
      case 'week':
        return { start: weekStart, end: addDays(weekStart, 6) }
      case '2weeks':
        return { start: weekStart, end: addDays(weekStart, 13) }
      case 'month':
        return { start: startOfMonth(currentDate), end: endOfMonth(currentDate) }
    }
  }, [viewRange, currentDate])

  const startDateStr = format(dateRange.start, 'yyyy-MM-dd')
  const endDateStr = format(dateRange.end, 'yyyy-MM-dd')

  // Fetch data
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
  const { data: templatesData, isLoading: templatesLoading } = useRotationTemplates()

  // Find the current user's person record
  const currentUserPerson = useMemo<Person | null>(() => {
    if (!user || !peopleData?.items) return null

    // Match by email or by user ID (if person has userId field)
    return peopleData.items.find(
      (person) => person.email === user.email || person.id === user.id
    ) || null
  }, [user, peopleData])

  // Determine which person to display:
  // - Tier 0: Always show current user (ignore URL param)
  // - Tier 1+: Show selected person or current user
  const displayPerson = useMemo<Person | null>(() => {
    if (tier === 0) return currentUserPerson

    // For tier 1+, check if a different person is selected
    const personIdToShow = selectedPersonId || currentUserPerson?.id
    if (!personIdToShow || !peopleData?.items) return currentUserPerson

    return peopleData.items.find((p) => p.id === personIdToShow) || currentUserPerson
  }, [tier, selectedPersonId, currentUserPerson, peopleData])

  // Check if viewing another person's schedule
  const isViewingOther = displayPerson?.id !== currentUserPerson?.id

  // Transform assignments to PersonalScheduleCard format
  const myAssignments = useMemo<ScheduleAssignment[]>(() => {
    if (!displayPerson || !blocksData?.items || !assignmentsData?.items) {
      return []
    }

    const blockMap = new Map<string, Block>()
    blocksData.items.forEach((block) => blockMap.set(block.id, block))

    const templateMap = new Map<string, RotationTemplate>()
    templatesData?.items?.forEach((template) => templateMap.set(template.id, template))

    const assignments: ScheduleAssignment[] = []

    assignmentsData.items
      .filter((assignment) => assignment.personId === displayPerson.id)
      .forEach((assignment) => {
        const block = blockMap.get(assignment.blockId)
        if (!block) return

        const template = assignment.rotationTemplateId
          ? templateMap.get(assignment.rotationTemplateId)
          : null

        assignments.push({
          id: assignment.id,
          date: block.date,
          timeOfDay: block.timeOfDay as 'AM' | 'PM',
          activity: template?.activityType || 'default',
          abbreviation:
            assignment.activityOverride ||
            template?.displayAbbreviation ||
            template?.abbreviation ||
            template?.name?.substring(0, 3).toUpperCase() ||
            '???',
          role: (assignment.role as 'primary' | 'supervising' | 'backup') || 'primary',
          notes: assignment.notes,
        })
      })

    return assignments.sort((a, b) => {
      if (a.date !== b.date) return a.date.localeCompare(b.date)
      return a.timeOfDay === 'AM' ? -1 : 1
    })
  }, [displayPerson, blocksData, assignmentsData, templatesData])

  // Navigation handlers
  const handlePrev = () => {
    switch (viewRange) {
      case 'week':
        setCurrentDate((d) => subWeeks(d, 1))
        break
      case '2weeks':
        setCurrentDate((d) => subWeeks(d, 2))
        break
      case 'month':
        setCurrentDate((d) => new Date(d.getFullYear(), d.getMonth() - 1, 1))
        break
    }
  }

  const handleNext = () => {
    switch (viewRange) {
      case 'week':
        setCurrentDate((d) => addWeeks(d, 1))
        break
      case '2weeks':
        setCurrentDate((d) => addWeeks(d, 2))
        break
      case 'month':
        setCurrentDate((d) => new Date(d.getFullYear(), d.getMonth() + 1, 1))
        break
    }
  }

  const handleToday = () => setCurrentDate(new Date())

  // Listen for keyboard shortcut to go to today
  useKeyboardShortcut('go-to-today', handleToday)

  const handlePrint = () => window.print()

  const handleExport = () => {
    if (!displayPerson || myAssignments.length === 0) return

    // Create CSV content
    const headers = ['Date', 'Day', 'Time', 'Activity', 'Role', 'Notes']
    const rows = myAssignments.map((a) => [
      a.date,
      format(new Date(a.date), 'EEEE'),
      a.timeOfDay,
      a.activity,
      a.role,
      a.notes || '',
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const personName = displayPerson.name.replace(/\s+/g, '-').toLowerCase()
    link.download = `schedule-${personName}-${startDateStr}-to-${endDateStr}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  // Handle person selection
  const handlePersonSelect = (personId: string | null) => {
    setSelectedPersonId(personId)
  }

  // Page title based on context
  const pageTitle = isViewingOther && displayPerson
    ? `${displayPerson.name}'s Schedule`
    : 'My Schedule'

  // Loading state
  const isLoading = blocksLoading || assignmentsLoading || peopleLoading || templatesLoading
  const error = blocksError || assignmentsError || peopleError

  return (
    <ProtectedRoute>
      {/* Risk Bar - always visible, color based on tier */}
      <RiskBar
        tier={tier}
        label={getRiskBarLabel(tier, isViewingOther)}
        tooltip={getRiskBarTooltip(tier, isViewingOther)}
      />

      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Breadcrumbs */}
        <PageBreadcrumbs className="mb-4" />

        {/* Header */}
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{pageTitle}</h1>
              <p className="text-gray-600 mt-1">
                {isViewingOther && displayPerson
                  ? `${displayPerson.type === 'resident' ? `PGY-${displayPerson.pgyLevel}` : 'Faculty'} rotation schedule`
                  : user?.username
                    ? `Viewing schedule for ${user.username}`
                    : 'Your personal rotation schedule'}
              </p>
            </div>

            {/* Person Selector - only renders for tier 1+ (no CSS hiding) */}
            <PersonSelector
              people={peopleData?.items || []}
              selectedPersonId={selectedPersonId || currentUserPerson?.id || null}
              onSelect={handlePersonSelect}
              tier={tier}
              isLoading={peopleLoading}
            />
          </div>
          <div className="flex items-center gap-2">
            <CopyUrlButton label="Share" size="sm" variant="outline" />
          </div>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            {/* Navigation */}
            <div className="flex items-center gap-2">
              <button
                onClick={handlePrev}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Previous"
              >
                <ChevronLeft className="w-5 h-5 text-gray-600" />
              </button>
              <button
                onClick={handleNext}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Next"
              >
                <ChevronRight className="w-5 h-5 text-gray-600" />
              </button>
              <button
                onClick={handleToday}
                className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                Today
              </button>
              <span className="text-gray-300 mx-2">|</span>
              <span className="font-medium text-gray-900">
                {format(dateRange.start, 'MMM d')} - {format(dateRange.end, 'MMM d, yyyy')}
              </span>
            </div>

            {/* Range selector and actions */}
            <div className="flex items-center gap-3">
              {/* Range toggle */}
              <div className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-1">
                {(['week', '2weeks', 'month'] as ViewRange[]).map((range) => (
                  <button
                    key={range}
                    onClick={() => setViewRange(range)}
                    className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                      viewRange === range
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {range === 'week' ? '1 Week' : range === '2weeks' ? '2 Weeks' : 'Month'}
                  </button>
                ))}
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1">
                <button
                  onClick={handleExport}
                  disabled={myAssignments.length === 0}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Export to CSV"
                >
                  <Download className="w-5 h-5 text-gray-600" />
                </button>
                <button
                  onClick={handlePrint}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors print:hidden"
                  title="Print"
                >
                  <Printer className="w-5 h-5 text-gray-600" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
            <span className="ml-3 text-gray-600">Loading schedule...</span>
          </div>
        )}

        {error && (
          <ErrorAlert
            message={error instanceof Error ? error.message : 'Failed to load schedule'}
          />
        )}

        {!isLoading && !error && !displayPerson && (
          <EmptyState
            title="Profile Not Found"
            description="We couldn't find a person profile linked to your account. Please contact your administrator."
            icon={Calendar}
          />
        )}

        {!isLoading && !error && displayPerson && (
          <>
            {/* Schedule Legend */}
            <ScheduleLegend compact className="mb-4" />

            <PersonalScheduleCard
              person={displayPerson}
              assignments={myAssignments}
              startDate={dateRange.start}
              endDate={dateRange.end}
              showHeader={false}
            />
          </>
        )}

        {/* Work Hours & Summary Stats */}
        {!isLoading && !error && displayPerson && myAssignments.length > 0 && (
          <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Work Hours Calculator */}
            <div className="lg:col-span-1">
              <WorkHoursCalculator
                assignments={myAssignments}
                showDetails={true}
              />
            </div>

            {/* Summary stats grid */}
            <div className="lg:col-span-2 grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="text-2xl font-bold text-gray-900">
                  {myAssignments.length}
                </div>
                <div className="text-sm text-gray-500">Total assignments</div>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="text-2xl font-bold text-blue-600">
                  {myAssignments.filter((a) => a.activity.toLowerCase().includes('clinic')).length}
                </div>
                <div className="text-sm text-gray-500">Clinic sessions</div>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="text-2xl font-bold text-purple-600">
                  {myAssignments.filter((a) => a.activity.toLowerCase().includes('inpatient')).length}
                </div>
                <div className="text-sm text-gray-500">Inpatient sessions</div>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <div className="text-2xl font-bold text-orange-600">
                  {myAssignments.filter((a) => a.activity.toLowerCase().includes('call')).length}
                </div>
                <div className="text-sm text-gray-500">Call shifts</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  )
}

export default function MySchedulePage() {
  return (
    <Suspense fallback={<div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>}>
      <MyScheduleContent />
    </Suspense>
  )
}
