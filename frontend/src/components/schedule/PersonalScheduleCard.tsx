'use client'

import { useMemo } from 'react'
import { format, isToday, parseISO, isAfter, isBefore, startOfDay } from 'date-fns'
import { Calendar, Clock, User } from 'lucide-react'
import type { Person } from '@/types/api'

// Assignment data structure with embedded details
export interface ScheduleAssignment {
  id: string
  date: string
  timeOfDay: 'AM' | 'PM'
  activity: string
  abbreviation: string
  role: 'primary' | 'supervising' | 'backup'
  notes?: string | null
}

export interface PersonalScheduleCardProps {
  person: Person
  assignments: ScheduleAssignment[]
  startDate?: Date
  endDate?: Date
  showHeader?: boolean
}

// Activity type to color mapping
const activityColors: Record<string, { bg: string; text: string; border: string }> = {
  clinic: { bg: 'bg-clinic-light', text: 'text-clinic-dark', border: 'border-clinic' },
  inpatient: { bg: 'bg-inpatient-light', text: 'text-inpatient-dark', border: 'border-inpatient' },
  call: { bg: 'bg-call-light', text: 'text-call-dark', border: 'border-call' },
  leave: { bg: 'bg-leave-light', text: 'text-leave-dark', border: 'border-leave' },
  conference: { bg: 'bg-gray-100', text: 'text-gray-700', border: 'border-gray-400' },
  default: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-400' },
}

function getActivityColors(activity: string): { bg: string; text: string; border: string } {
  const activityLower = activity.toLowerCase()

  for (const [key, colors] of Object.entries(activityColors)) {
    if (activityLower.includes(key)) {
      return colors
    }
  }

  return activityColors.default
}

// Group assignments by date
interface DaySchedule {
  date: string
  dateObj: Date
  am: ScheduleAssignment | null
  pm: ScheduleAssignment | null
}

export function PersonalScheduleCard({
  person,
  assignments,
  startDate,
  endDate,
  showHeader = true,
}: PersonalScheduleCardProps) {
  // Group and sort assignments by date
  const scheduleByDay = useMemo<DaySchedule[]>(() => {
    const dayMap = new Map<string, DaySchedule>()

    assignments.forEach((assignment) => {
      const existing = dayMap.get(assignment.date)
      const dateObj = parseISO(assignment.date)

      if (!existing) {
        dayMap.set(assignment.date, {
          date: assignment.date,
          dateObj,
          am: assignment.timeOfDay === 'AM' ? assignment : null,
          pm: assignment.timeOfDay === 'PM' ? assignment : null,
        })
      } else {
        if (assignment.timeOfDay === 'AM') {
          existing.am = assignment
        } else {
          existing.pm = assignment
        }
      }
    })

    // Filter by date range if provided
    let days = Array.from(dayMap.values())

    if (startDate) {
      const start = startOfDay(startDate)
      days = days.filter((d) => !isBefore(d.dateObj, start))
    }

    if (endDate) {
      const end = startOfDay(endDate)
      days = days.filter((d) => !isAfter(d.dateObj, end))
    }

    return days.sort((a, b) => a.dateObj.getTime() - b.dateObj.getTime())
  }, [assignments, startDate, endDate])

  if (assignments.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {showHeader && (
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
              <User className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{person.name}</h3>
              <p className="text-sm text-gray-500">
                {person.type === 'resident' ? `PGY-${person.pgyLevel}` : 'Faculty'}
              </p>
            </div>
          </div>
        )}
        <div className="text-center py-8 text-gray-500">
          <Calendar className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>No assignments scheduled</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      {showHeader && (
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
              <User className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{person.name}</h3>
              <p className="text-sm text-gray-500">
                {person.type === 'resident' ? `PGY-${person.pgyLevel}` : 'Faculty'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Schedule Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Day
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                AM
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                PM
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {scheduleByDay.map((day) => {
              const isTodayRow = isToday(day.dateObj)
              const isWeekend = day.dateObj.getDay() === 0 || day.dateObj.getDay() === 6

              return (
                <tr
                  key={day.date}
                  className={`
                    transition-colors
                    ${isTodayRow ? 'bg-blue-50 ring-1 ring-inset ring-blue-200' : ''}
                    ${isWeekend && !isTodayRow ? 'bg-gray-50' : ''}
                    ${!isTodayRow && !isWeekend ? 'hover:bg-gray-50' : ''}
                  `}
                >
                  {/* Date */}
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {isTodayRow && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-600 text-white">
                          Today
                        </span>
                      )}
                      <span className={`text-sm ${isTodayRow ? 'font-semibold text-blue-900' : 'text-gray-900'}`}>
                        {format(day.dateObj, 'MMM d, yyyy')}
                      </span>
                    </div>
                  </td>

                  {/* Day of Week */}
                  <td className="px-4 py-3">
                    <span className={`text-sm ${isWeekend ? 'text-gray-500' : 'text-gray-700'}`}>
                      {format(day.dateObj, 'EEEE')}
                    </span>
                  </td>

                  {/* AM Rotation */}
                  <td className="px-4 py-3">
                    <RotationBadge assignment={day.am} />
                  </td>

                  {/* PM Rotation */}
                  <td className="px-4 py-3">
                    <RotationBadge assignment={day.pm} />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Footer with count */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Clock className="w-4 h-4" />
          <span>{scheduleByDay.length} days scheduled</span>
        </div>
      </div>
    </div>
  )
}

interface RotationBadgeProps {
  assignment: ScheduleAssignment | null
}

function RotationBadge({ assignment }: RotationBadgeProps) {
  if (!assignment) {
    return <span className="text-gray-300 text-sm">-</span>
  }

  const colors = getActivityColors(assignment.activity)
  const roleLabel = assignment.role === 'backup' ? ' (Backup)' : assignment.role === 'supervising' ? ' (Sup)' : ''

  return (
    <div
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-sm font-medium
        ${colors.bg} ${colors.text} border ${colors.border}
      `}
      title={`${assignment.activity}${roleLabel}${assignment.notes ? ` - ${assignment.notes}` : ''}`}
    >
      <span>{assignment.abbreviation || assignment.activity}</span>
      {roleLabel && <span className="text-xs opacity-75">{roleLabel}</span>}
    </div>
  )
}

// Export helper type for other components
export type { DaySchedule }
