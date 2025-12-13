'use client'

import { useState } from 'react'
import { format, startOfWeek, addDays, addWeeks, subWeeks } from 'date-fns'
import { ChevronLeft, ChevronRight, Calendar, Users, Settings } from 'lucide-react'
import { ScheduleCalendar } from '@/components/ScheduleCalendar'
import { useSchedule } from '@/lib/hooks'

export default function HomePage() {
  const [currentDate, setCurrentDate] = useState(new Date())
  const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 }) // Monday
  const weekEnd = addDays(weekStart, 6)

  const { data: schedule, isLoading } = useSchedule(
    format(weekStart, 'yyyy-MM-dd'),
    format(weekEnd, 'yyyy-MM-dd')
  )

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
          <button className="btn-primary flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Generate Schedule
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Total Assignments"
          value={schedule?.total_assignments || 0}
          icon={<Calendar className="w-5 h-5 text-blue-600" />}
        />
        <StatCard
          title="Residents Scheduled"
          value={schedule?.schedule ? Object.keys(schedule.schedule).length : 0}
          icon={<Users className="w-5 h-5 text-green-600" />}
        />
        <StatCard
          title="Coverage Rate"
          value="--"
          icon={<Settings className="w-5 h-5 text-purple-600" />}
        />
        <StatCard
          title="ACGME Status"
          value="Valid"
          icon={<CheckIcon />}
          valueColor="text-green-600"
        />
      </div>

      {/* Schedule Calendar */}
      {isLoading ? (
        <div className="card flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <ScheduleCalendar
          weekStart={weekStart}
          schedule={schedule?.schedule || {}}
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
