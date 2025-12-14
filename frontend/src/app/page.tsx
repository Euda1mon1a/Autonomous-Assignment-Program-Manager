'use client'

import { useState } from 'react'
import { format, startOfWeek, addDays, addWeeks, subWeeks } from 'date-fns'
import { ChevronLeft, ChevronRight, Calendar, Users, Settings, RefreshCw } from 'lucide-react'
import { ScheduleCalendar } from '@/components/ScheduleCalendar'
import { useSchedule, useValidateSchedule } from '@/lib/hooks'
import { CalendarSkeleton } from '@/components/skeletons'
import { GenerateScheduleDialog } from '@/components/GenerateScheduleDialog'

export default function HomePage() {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [isGenerateDialogOpen, setIsGenerateDialogOpen] = useState(false)
  const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 }) // Monday
  const weekEnd = addDays(weekStart, 6)

  const { data: schedule, isLoading, isError, error, refetch } = useSchedule(
    weekStart,
    weekEnd
  )

  // Get validation data for ACGME status
  const startDateStr = format(weekStart, 'yyyy-MM-dd')
  const endDateStr = format(weekEnd, 'yyyy-MM-dd')
  const { data: validation } = useValidateSchedule(startDateStr, endDateStr)

  const goToPreviousWeek = () => setCurrentDate(subWeeks(currentDate, 1))
  const goToNextWeek = () => setCurrentDate(addWeeks(currentDate, 1))
  const goToToday = () => setCurrentDate(new Date())

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Schedule</h1>
          <p className="text-gray-600">
            {format(weekStart, 'MMM d')} - {format(weekEnd, 'MMM d, yyyy')}
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* Week Navigation */}
          <div className="flex items-center gap-2">
            <button
              onClick={goToPreviousWeek}
              className="p-2 hover:bg-gray-100 rounded-md"
              aria-label="Previous week"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={goToToday}
              className="btn-secondary text-sm"
            >
              Today
            </button>
            <button
              onClick={goToNextWeek}
              className="p-2 hover:bg-gray-100 rounded-md"
              aria-label="Next week"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          {/* Generate Schedule */}
          <button
            onClick={() => setIsGenerateDialogOpen(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Calendar className="w-4 h-4" />
            Generate Schedule
          </button>
        </div>
      </div>

      {/* Generate Schedule Dialog */}
      <GenerateScheduleDialog
        isOpen={isGenerateDialogOpen}
        onClose={() => setIsGenerateDialogOpen(false)}
        defaultStartDate={startDateStr}
        defaultEndDate={endDateStr}
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Total Assignments"
          value={schedule?.total ?? 0}
          icon={<Calendar className="w-5 h-5 text-blue-600" />}
        />
        <StatCard
          title="Residents Scheduled"
          value={schedule?.items ? new Set(schedule.items.map(a => a.person_id)).size : 0}
          icon={<Users className="w-5 h-5 text-green-600" />}
        />
        <StatCard
          title="Coverage Rate"
          value={validation?.coverage_rate ? `${validation.coverage_rate.toFixed(0)}%` : '--'}
          icon={<Settings className="w-5 h-5 text-purple-600" />}
        />
        <StatCard
          title="ACGME Status"
          value={validation?.valid ? 'Valid' : validation ? `${validation.total_violations} Issues` : '--'}
          icon={validation?.valid !== false ? <CheckIcon /> : <WarningIcon />}
          valueColor={validation?.valid !== false ? 'text-green-600' : 'text-amber-600'}
        />
      </div>

      {/* Schedule Calendar */}
      {isLoading ? (
        <CalendarSkeleton />
      ) : isError ? (
        <div className="card flex flex-col items-center justify-center h-96 text-center">
          <div className="text-red-500 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-gray-600 mb-4">
            {error?.message || 'Failed to load schedule'}
          </p>
          <button
            onClick={() => refetch()}
            className="btn-primary flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </button>
        </div>
      ) : (
        <ScheduleCalendar
          weekStart={weekStart}
          schedule={{}}
        />
      )}
    </div>
  )
}

function StatCard({
  title,
  value,
  icon,
  valueColor = 'text-gray-900',
}: {
  title: string
  value: string | number
  icon: React.ReactNode
  valueColor?: string
}) {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className={`text-2xl font-bold ${valueColor}`}>{value}</p>
        </div>
        {icon}
      </div>
    </div>
  )
}

function CheckIcon() {
  return (
    <svg
      className="w-5 h-5 text-green-600"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M5 13l4 4L19 7"
      />
    </svg>
  )
}

function WarningIcon() {
  return (
    <svg
      className="w-5 h-5 text-amber-600"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
      />
    </svg>
  )
}
