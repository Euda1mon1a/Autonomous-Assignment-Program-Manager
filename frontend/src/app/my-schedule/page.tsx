'use client'

import { useState, useMemo } from 'react'
import { format, startOfWeek, addWeeks, addDays, subWeeks, startOfMonth, endOfMonth } from 'date-fns'
import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, Calendar, Download, Printer } from 'lucide-react'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { useAuth } from '@/contexts/AuthContext'
import { PersonalScheduleCard, ScheduleAssignment } from '@/components/schedule/PersonalScheduleCard'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorAlert } from '@/components/ErrorAlert'
import { EmptyState } from '@/components/EmptyState'
import { get } from '@/lib/api'
import { ListResponse, usePeople, useRotationTemplates } from '@/lib/hooks'
import type { Assignment, Block, Person, RotationTemplate } from '@/types/api'

/**
 * My Schedule Page - Personal schedule view for logged-in users
 *
 * Shows the current user's own schedule in a personalized format.
 * Features:
 * - Week/month range selector
 * - Print-friendly layout
 * - Export to CSV/PDF
 */

type ViewRange = 'week' | '2weeks' | 'month'

export default function MySchedulePage() {
  const { user } = useAuth()
  const [viewRange, setViewRange] = useState<ViewRange>('2weeks')
  const [currentDate, setCurrentDate] = useState(() => new Date())

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
  const currentPerson = useMemo<Person | null>(() => {
    if (!user || !peopleData?.items) return null

    // Match by email or by user ID (if person has user_id field)
    return peopleData.items.find(
      (person) => person.email === user.email || person.id === user.id
    ) || null
  }, [user, peopleData])

  // Transform assignments to PersonalScheduleCard format
  const myAssignments = useMemo<ScheduleAssignment[]>(() => {
    if (!currentPerson || !blocksData?.items || !assignmentsData?.items) {
      return []
    }

    const blockMap = new Map<string, Block>()
    blocksData.items.forEach((block) => blockMap.set(block.id, block))

    const templateMap = new Map<string, RotationTemplate>()
    templatesData?.items?.forEach((template) => templateMap.set(template.id, template))

    const assignments: ScheduleAssignment[] = []

    assignmentsData.items
      .filter((assignment) => assignment.person_id === currentPerson.id)
      .forEach((assignment) => {
        const block = blockMap.get(assignment.block_id)
        if (!block) return

        const template = assignment.rotation_template_id
          ? templateMap.get(assignment.rotation_template_id)
          : null

        assignments.push({
          id: assignment.id,
          date: block.date,
          time_of_day: block.time_of_day as 'AM' | 'PM',
          activity: template?.activity_type || 'default',
          abbreviation:
            assignment.activity_override ||
            template?.abbreviation ||
            template?.name?.substring(0, 3).toUpperCase() ||
            '???',
          role: (assignment.role as 'primary' | 'supervising' | 'backup') || 'primary',
          notes: assignment.notes,
        })
      })

    return assignments.sort((a, b) => {
      if (a.date !== b.date) return a.date.localeCompare(b.date)
      return a.time_of_day === 'AM' ? -1 : 1
    })
  }, [currentPerson, blocksData, assignmentsData, templatesData])

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

  const handlePrint = () => window.print()

  const handleExport = () => {
    if (!currentPerson || myAssignments.length === 0) return

    // Create CSV content
    const headers = ['Date', 'Day', 'Time', 'Activity', 'Role', 'Notes']
    const rows = myAssignments.map((a) => [
      a.date,
      format(new Date(a.date), 'EEEE'),
      a.time_of_day,
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
    link.download = `my-schedule-${startDateStr}-to-${endDateStr}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  // Loading state
  const isLoading = blocksLoading || assignmentsLoading || peopleLoading || templatesLoading
  const error = blocksError || assignmentsError || peopleError

  return (
    <ProtectedRoute>
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">My Schedule</h1>
          <p className="text-gray-600 mt-1">
            {user?.username ? `Viewing schedule for ${user.username}` : 'Your personal rotation schedule'}
          </p>
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
            <span className="ml-3 text-gray-600">Loading your schedule...</span>
          </div>
        )}

        {error && (
          <ErrorAlert
            message={error instanceof Error ? error.message : 'Failed to load schedule'}
          />
        )}

        {!isLoading && !error && !currentPerson && (
          <EmptyState
            title="Profile Not Found"
            description="We couldn't find a person profile linked to your account. Please contact your administrator."
            icon={<Calendar className="w-12 h-12 text-gray-300" />}
          />
        )}

        {!isLoading && !error && currentPerson && (
          <PersonalScheduleCard
            person={{
              id: currentPerson.id,
              name: currentPerson.name,
              type: currentPerson.type,
              pgy_level: currentPerson.pgy_level,
            }}
            assignments={myAssignments}
            startDate={dateRange.start}
            endDate={dateRange.end}
            showHeader={false}
          />
        )}

        {/* Summary stats */}
        {!isLoading && !error && currentPerson && myAssignments.length > 0 && (
          <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4">
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
        )}
      </div>
    </ProtectedRoute>
  )
}
