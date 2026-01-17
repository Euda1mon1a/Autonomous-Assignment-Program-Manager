'use client'

import React, { useMemo } from 'react'
import {
  format,
  addMonths,
  subMonths,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  addDays,
  isSameMonth,
  isToday,
} from 'date-fns'
import { ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react'

interface Person {
  id: string
  name: string
  type: string
  pgyLevel: number | null
}

interface Assignment {
  id: string
  person: Person
  role: string
  activity: string
  abbreviation: string
}

interface ScheduleData {
  [date: string]: {
    AM: Assignment[]
    PM: Assignment[]
  }
}

interface DayIssue {
  type: 'warning' | 'error'
  message: string
}

export interface MonthViewProps {
  currentDate: Date
  schedule: ScheduleData
  onDateChange: (date: Date) => void
  onDayClick: (date: Date) => void
  personFilter?: string[]
  holidays?: Record<string, string>
  issues?: Record<string, DayIssue[]>
}

// US Federal Holidays for reference (can be passed in via holidays prop)
const FEDERAL_HOLIDAYS_2024: Record<string, string> = {
  '2024-01-01': "New Year's Day",
  '2024-01-15': 'Martin Luther King Jr. Day',
  '2024-02-19': "Presidents' Day",
  '2024-05-27': 'Memorial Day',
  '2024-06-19': 'Juneteenth',
  '2024-07-04': 'Independence Day',
  '2024-09-02': 'Labor Day',
  '2024-10-14': 'Columbus Day',
  '2024-11-11': 'Veterans Day',
  '2024-11-28': 'Thanksgiving Day',
  '2024-12-25': 'Christmas Day',
}

/**
 * Activity type colors for mini indicators
 * Matches ScheduleCell rotationColors for consistency across all views
 */
const activityIndicatorColors: Record<string, string> = {
  clinic: 'bg-blue-500',
  inpatient: 'bg-purple-500',
  procedure: 'bg-red-500',
  conference: 'bg-gray-500',
  elective: 'bg-green-500',
  call: 'bg-orange-500',
  off: 'bg-gray-300',
  leave: 'bg-amber-500',
  vacation: 'bg-amber-500',
  default: 'bg-slate-500',
}

function getIndicatorColor(activity: string): string {
  const activityLower = activity.toLowerCase()

  // Check exact match first
  if (activityIndicatorColors[activityLower]) {
    return activityIndicatorColors[activityLower]
  }

  // Check for partial matches
  for (const [key, color] of Object.entries(activityIndicatorColors)) {
    if (activityLower.includes(key)) {
      return color
    }
  }
  return activityIndicatorColors.default
}

export function MonthView({
  currentDate,
  schedule,
  onDateChange,
  onDayClick,
  personFilter,
  holidays = FEDERAL_HOLIDAYS_2024,
  issues = {},
}: MonthViewProps) {
  const monthStart = startOfMonth(currentDate)
  const monthEnd = endOfMonth(currentDate)
  const calendarStart = startOfWeek(monthStart, { weekStartsOn: 0 })
  const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 0 })

  // Generate all days for the calendar grid
  const calendarDays = useMemo(() => {
    const days: Date[] = []
    let currentDay = calendarStart

    while (currentDay <= calendarEnd) {
      days.push(currentDay)
      currentDay = addDays(currentDay, 1)
    }

    return days
  }, [calendarStart, calendarEnd])

  // Calculate assignment counts and activity types for each day
  const dayStats = useMemo(() => {
    const stats: Record<
      string,
      { count: number; activities: Set<string>; hasIssues: boolean }
    > = {}

    calendarDays.forEach((day) => {
      const dateStr = format(day, 'yyyy-MM-dd')
      const daySchedule = schedule[dateStr]
      const activities = new Set<string>()
      let count = 0

      if (daySchedule) {
        const seenPersons = new Set<string>()

        ;['AM', 'PM'].forEach((time) => {
          daySchedule[time as 'AM' | 'PM']?.forEach((assignment) => {
            // Apply person filter
            if (personFilter && personFilter.length > 0) {
              if (!personFilter.includes(assignment.person.id)) return
            }

            if (!seenPersons.has(assignment.person.id)) {
              seenPersons.add(assignment.person.id)
              count++
            }
            activities.add(assignment.activity)
          })
        })
      }

      stats[dateStr] = {
        count,
        activities,
        hasIssues: (issues[dateStr]?.length || 0) > 0,
      }
    })

    return stats
  }, [calendarDays, schedule, personFilter, issues])

  const handlePrevMonth = () => onDateChange(subMonths(currentDate, 1))
  const handleNextMonth = () => onDateChange(addMonths(currentDate, 1))
  const handleThisMonth = () => onDateChange(new Date())

  const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

  return (
    <div className="card">
      {/* Navigation Header */}
      <div className="flex items-center justify-between pb-4 border-b mb-4">
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrevMonth}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Previous month"
            aria-label="Previous month"
          >
            <ChevronLeft className="w-5 h-5 text-gray-600" aria-hidden="true" />
          </button>
          <button
            onClick={handleNextMonth}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Next month"
            aria-label="Next month"
          >
            <ChevronRight className="w-5 h-5 text-gray-600" aria-hidden="true" />
          </button>
          <button
            onClick={handleThisMonth}
            className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            This Month
          </button>
        </div>

        <div className="text-xl font-semibold text-gray-900">
          {format(currentDate, 'MMMM yyyy')}
        </div>

        <div className="w-[140px]"></div>
      </div>

      {/* Calendar Grid */}
      <div className="overflow-x-auto">
        <div className="min-w-[700px]" role="grid" aria-label="Monthly calendar view">
          {/* Weekday Headers */}
          <div className="grid grid-cols-7 gap-px bg-gray-200 border border-gray-200 rounded-t-lg overflow-hidden" role="row">
            {weekdays.map((day, idx) => (
              <div
                key={day}
                role="columnheader"
                className={`p-2 text-center font-semibold text-sm ${
                  idx === 0 || idx === 6 ? 'bg-gray-100 text-gray-500' : 'bg-gray-50 text-gray-700'
                }`}
              >
                {day}
              </div>
            ))}
          </div>

          {/* Calendar Days */}
          <div className="grid grid-cols-7 gap-px bg-gray-200 border-x border-b border-gray-200 rounded-b-lg overflow-hidden">
            {calendarDays.map((day) => {
              const dateStr = format(day, 'yyyy-MM-dd')
              const isCurrentMonth = isSameMonth(day, currentDate)
              const isTodayDate = isToday(day)
              const isWeekendDay = day.getDay() === 0 || day.getDay() === 6
              const holidayName = holidays[dateStr]
              const stats = dayStats[dateStr]
              const dayIssues = issues[dateStr]

              return (
                <div
                  key={dateStr}
                  onClick={() => onDayClick(day)}
                  className={`
                    min-h-[100px] p-2 cursor-pointer transition-colors
                    ${isCurrentMonth ? 'bg-white' : 'bg-gray-50'}
                    ${isWeekendDay && isCurrentMonth ? 'bg-gray-50/50' : ''}
                    ${isTodayDate ? 'ring-2 ring-inset ring-blue-400' : ''}
                    hover:bg-blue-50
                  `}
                >
                  {/* Day Number */}
                  <div className="flex items-start justify-between mb-1">
                    <span
                      className={`
                        text-sm font-medium
                        ${!isCurrentMonth ? 'text-gray-400' : ''}
                        ${isTodayDate ? 'bg-blue-600 text-white w-6 h-6 rounded-full flex items-center justify-center' : ''}
                      `}
                    >
                      {format(day, 'd')}
                    </span>
                    {stats?.hasIssues && (
                      <span title="Has issues">
                        <AlertCircle className="w-4 h-4 text-red-500" aria-hidden="true" />
                      </span>
                    )}
                  </div>

                  {/* Holiday Badge */}
                  {holidayName && isCurrentMonth && (
                    <div className="mb-1 px-1.5 py-0.5 text-[10px] font-medium bg-amber-100 text-amber-700 rounded truncate">
                      {holidayName}
                    </div>
                  )}

                  {/* Assignment Count Badge */}
                  {isCurrentMonth && stats && stats.count > 0 && (
                    <div className="mt-1">
                      <div className="inline-flex items-center px-1.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded">
                        {stats.count} assignment{stats.count !== 1 ? 's' : ''}
                      </div>
                    </div>
                  )}

                  {/* Activity Color Indicators */}
                  {isCurrentMonth && stats && stats.activities.size > 0 && (
                    <div className="flex flex-wrap gap-0.5 mt-1.5" aria-label={`${stats.activities.size} activity types`}>
                      {Array.from(stats.activities)
                        .slice(0, 5)
                        .map((activity, idx) => (
                          <div
                            key={idx}
                            className={`w-2 h-2 rounded-full ${getIndicatorColor(activity)}`}
                            title={activity}
                            aria-hidden="true"
                          />
                        ))}
                      {stats.activities.size > 5 && (
                        <span className="text-[9px] text-gray-400 ml-0.5" aria-hidden="true">
                          +{stats.activities.size - 5}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Issue Indicators */}
                  {isCurrentMonth && dayIssues && dayIssues.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-0.5">
                      {dayIssues.slice(0, 3).map((issue, idx) => (
                        <div
                          key={idx}
                          className={`w-1.5 h-1.5 rounded-full ${
                            issue.type === 'error' ? 'bg-red-500' : 'bg-amber-500'
                          }`}
                          title={issue.message}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t flex flex-wrap items-center gap-4 text-xs text-gray-600" role="region" aria-label="Activity type legend">
        <span className="font-medium text-gray-700">Activity Types:</span>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-blue-500" aria-hidden="true" />
          <span>Clinic</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-purple-500" aria-hidden="true" />
          <span>Inpatient</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-orange-500" aria-hidden="true" />
          <span>Call</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-amber-500" aria-hidden="true" />
          <span>Leave</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-green-500" aria-hidden="true" />
          <span>Elective</span>
        </div>
        <div className="flex items-center gap-1.5 ml-4">
          <AlertCircle className="w-3 h-3 text-red-500" aria-hidden="true" />
          <span>Has Issues</span>
        </div>
      </div>
    </div>
  )
}
