'use client'

import { useMemo, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { format, startOfMonth, endOfMonth, addMonths, subMonths } from 'date-fns'
import { ArrowLeft, Calendar, ChevronLeft, ChevronRight, Download, User } from 'lucide-react'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { PersonalScheduleCard, ScheduleAssignment } from '@/components/schedule/PersonalScheduleCard'
import { usePerson, useAssignments, useRotationTemplates } from '@/lib/hooks'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorAlert } from '@/components/ErrorAlert'

export default function PersonSchedulePage() {
  const params = useParams()
  const router = useRouter()
  const personId = params.personId as string

  // Month navigation state
  const [currentMonth, setCurrentMonth] = useState(() => new Date())

  // Calculate date range for the current month view
  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const startDateStr = format(monthStart, 'yyyy-MM-dd')
  const endDateStr = format(monthEnd, 'yyyy-MM-dd')

  // Fetch data
  const {
    data: person,
    isLoading: personLoading,
    error: personError
  } = usePerson(personId)

  const {
    data: assignmentsData,
    isLoading: assignmentsLoading
  } = useAssignments(
    { personId: personId, startDate: startDateStr, endDate: endDateStr },
    { enabled: !!personId }
  )

  const {
    data: templatesData,
    isLoading: templatesLoading
  } = useRotationTemplates()

  const isLoading = personLoading || assignmentsLoading || templatesLoading

  // Build rotation template lookup
  const templateMap = useMemo(() => {
    const map = new Map<string, { name: string; abbreviation: string; activityType: string }>()
    templatesData?.items?.forEach((t) => {
      map.set(t.id, {
        name: t.name,
        abbreviation: t.displayAbbreviation || t.abbreviation || t.name.substring(0, 3).toUpperCase(),
        activityType: t.activityType,
      })
    })
    return map
  }, [templatesData])

  // Transform assignments to the format expected by PersonalScheduleCard
  const scheduleAssignments = useMemo<ScheduleAssignment[]>(() => {
    if (!assignmentsData?.items) return []

    return assignmentsData.items.map((assignment) => {
      const template = assignment.rotationTemplateId
        ? templateMap.get(assignment.rotationTemplateId)
        : null

      // In production, block data would provide date and timeOfDay
      // For now, extract from createdAt or use block lookup
      const dateStr = assignment.createdAt.split('T')[0]

      return {
        id: assignment.id,
        date: dateStr,
        timeOfDay: 'AM' as const, // Would come from block data
        activity: assignment.activityOverride || template?.activityType || 'Assignment',
        abbreviation: template?.abbreviation || 'ASN',
        role: assignment.role,
        notes: assignment.notes,
      }
    })
  }, [assignmentsData, templateMap])

  // Navigation handlers
  const goToPreviousMonth = () => {
    setCurrentMonth((prev) => subMonths(prev, 1))
  }

  const goToNextMonth = () => {
    setCurrentMonth((prev) => addMonths(prev, 1))
  }

  const goToToday = () => {
    setCurrentMonth(new Date())
  }

  // Export to CSV
  const handleExport = () => {
    if (!person || scheduleAssignments.length === 0) return

    const headers = ['Date', 'Day', 'Time', 'Rotation', 'Role', 'Notes']
    const rows = scheduleAssignments.map((a) => {
      const date = new Date(a.date)
      return [
        format(date, 'yyyy-MM-dd'),
        format(date, 'EEEE'),
        a.timeOfDay,
        a.activity,
        a.role,
        a.notes || '',
      ]
    })

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `schedule-${person.name.replace(/\s+/g, '-').toLowerCase()}-${format(currentMonth, 'yyyy-MM')}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <ProtectedRoute>
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Back Navigation */}
        <div className="mb-6">
          <Link
            href="/schedule"
            className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Full Schedule
          </Link>
        </div>

        {/* Error State */}
        {personError && (
          <ErrorAlert
            message="Error loading person: Unable to load person details. Please try again."
            onRetry={() => router.refresh()}
          />
        )}

        {/* Loading State */}
        {isLoading && !person && (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {/* Content */}
        {person && (
          <>
            {/* Page Header */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center">
                    <User className="w-8 h-8 text-blue-600" />
                  </div>
                  <div>
                    <h1 className="text-2xl font-bold text-gray-900">{person.name}</h1>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        {person.type === 'resident' ? `PGY-${person.pgyLevel}` : 'Faculty'}
                      </span>
                      {person.email && (
                        <span className="text-sm text-gray-500">{person.email}</span>
                      )}
                    </div>
                    {person.specialties && person.specialties.length > 0 && (
                      <div className="flex items-center gap-2 mt-2">
                        {person.specialties.map((specialty) => (
                          <span
                            key={specialty}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700"
                          >
                            {specialty}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Export Button */}
                <button
                  onClick={handleExport}
                  disabled={scheduleAssignments.length === 0}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Download className="w-4 h-4" />
                  Export CSV
                </button>
              </div>
            </div>

            {/* Month Navigation */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <button
                  onClick={goToPreviousMonth}
                  className="p-2 hover:bg-gray-100 rounded-md transition-colors"
                  aria-label="Previous month"
                >
                  <ChevronLeft className="w-5 h-5 text-gray-600" />
                </button>
                <button
                  onClick={goToNextMonth}
                  className="p-2 hover:bg-gray-100 rounded-md transition-colors"
                  aria-label="Next month"
                >
                  <ChevronRight className="w-5 h-5 text-gray-600" />
                </button>
                <h2 className="text-lg font-semibold text-gray-900 ml-2">
                  {format(currentMonth, 'MMMM yyyy')}
                </h2>
              </div>

              <button
                onClick={goToToday}
                className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
              >
                <Calendar className="w-4 h-4" />
                Today
              </button>
            </div>

            {/* Schedule Card */}
            {isLoading ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 flex items-center justify-center">
                <LoadingSpinner />
              </div>
            ) : (
              <PersonalScheduleCard
                person={person}
                assignments={scheduleAssignments}
                startDate={monthStart}
                endDate={monthEnd}
                showHeader={false}
              />
            )}

            {/* Quick Stats */}
            {scheduleAssignments.length > 0 && (
              <div className="mt-6 grid grid-cols-3 gap-4">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {scheduleAssignments.length}
                  </div>
                  <div className="text-sm text-gray-500">Total Assignments</div>
                </div>
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {new Set(scheduleAssignments.map((a) => a.date)).size}
                  </div>
                  <div className="text-sm text-gray-500">Days Scheduled</div>
                </div>
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {new Set(scheduleAssignments.map((a) => a.activity)).size}
                  </div>
                  <div className="text-sm text-gray-500">Rotation Types</div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </ProtectedRoute>
  )
}
