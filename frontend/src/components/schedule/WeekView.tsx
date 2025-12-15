'use client'

import React, { useMemo } from 'react'
import {
  format,
  addWeeks,
  subWeeks,
  startOfWeek,
  endOfWeek,
  addDays,
  getWeek,
  isToday,
} from 'date-fns'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface Person {
  id: string
  name: string
  type: string
  pgy_level: number | null
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

export interface WeekViewProps {
  currentDate: Date
  schedule: ScheduleData
  onDateChange: (date: Date) => void
  onCellClick?: (personId: string, date: Date, timeOfDay: 'AM' | 'PM', assignment?: Assignment) => void
  onDayClick?: (date: Date) => void
  personFilter?: string[]
  holidays?: Record<string, string>
}

/**
 * Color coding for rotation types
 * Matches ScheduleCell rotationColors for consistency across all views
 */
const rotationColors: Record<string, string> = {
  clinic: 'bg-blue-100 text-blue-800',
  inpatient: 'bg-purple-100 text-purple-800',
  procedure: 'bg-red-100 text-red-800',
  conference: 'bg-gray-100 text-gray-800',
  elective: 'bg-green-100 text-green-800',
  call: 'bg-orange-100 text-orange-800',
  off: 'bg-white text-gray-400',
  leave: 'bg-amber-100 text-amber-800',
  vacation: 'bg-amber-100 text-amber-800',
  default: 'bg-slate-100 text-slate-700',
}

function getActivityColor(activity: string): string {
  const activityLower = activity.toLowerCase()

  // Check exact match first
  if (rotationColors[activityLower]) {
    return rotationColors[activityLower]
  }

  // Check for partial matches
  for (const [key, color] of Object.entries(rotationColors)) {
    if (activityLower.includes(key)) {
      return color
    }
  }
  return rotationColors.default
}

export function WeekView({
  currentDate,
  schedule,
  onDateChange,
  onCellClick,
  onDayClick,
  personFilter,
  holidays = {},
}: WeekViewProps) {
  // Get Monday-Sunday of current week
  const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 })
  const weekEnd = endOfWeek(currentDate, { weekStartsOn: 1 })
  const weekNumber = getWeek(currentDate, { weekStartsOn: 1 })

  const days = useMemo(
    () => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)),
    [weekStart]
  )

  // Extract and sort people for this week
  const people = useMemo(() => {
    const allPeople = new Map<string, Person>()

    days.forEach((day) => {
      const dateStr = format(day, 'yyyy-MM-dd')
      const daySchedule = schedule[dateStr]

      if (daySchedule) {
        ;['AM', 'PM'].forEach((time) => {
          daySchedule[time as 'AM' | 'PM']?.forEach((assignment) => {
            if (!allPeople.has(assignment.person.id)) {
              allPeople.set(assignment.person.id, assignment.person)
            }
          })
        })
      }
    })

    let peopleArray = Array.from(allPeople.entries())

    // Apply person filter if provided
    if (personFilter && personFilter.length > 0) {
      peopleArray = peopleArray.filter(([id]) => personFilter.includes(id))
    }

    // Sort by PGY level then name
    return peopleArray.sort((a, b) => {
      const aLevel = a[1].pgy_level || 99
      const bLevel = b[1].pgy_level || 99
      if (aLevel !== bLevel) return aLevel - bLevel
      return a[1].name.localeCompare(b[1].name)
    })
  }, [schedule, days, personFilter])

  const handlePrevWeek = () => onDateChange(subWeeks(currentDate, 1))
  const handleNextWeek = () => onDateChange(addWeeks(currentDate, 1))
  const handleThisWeek = () => onDateChange(new Date())

  const renderCell = (
    day: Date,
    personId: string,
    amAssignment?: Assignment,
    pmAssignment?: Assignment
  ) => {
    const isWeekendDay = day.getDay() === 0 || day.getDay() === 6
    const isSameActivity =
      amAssignment &&
      pmAssignment &&
      amAssignment.activity === pmAssignment.activity

    const handleCellClick = (timeOfDay: 'AM' | 'PM', assignment?: Assignment) => {
      onCellClick?.(personId, day, timeOfDay, assignment)
    }

    // Empty cell
    if (!amAssignment && !pmAssignment) {
      return (
        <div
          className={`schedule-cell min-h-[52px] ${isWeekendDay ? 'bg-gray-50' : 'bg-white'}`}
          onClick={() => handleCellClick('AM')}
        >
          <div className="text-center text-gray-300 text-xs">-</div>
        </div>
      )
    }

    // Same activity all day
    if (isSameActivity) {
      return (
        <div
          className={`schedule-cell min-h-[52px] ${getActivityColor(amAssignment.activity)}`}
          title={amAssignment.activity}
          onClick={() => handleCellClick('AM', amAssignment)}
        >
          <div className="text-center">
            <div className="font-medium text-xs">{amAssignment.abbreviation}</div>
          </div>
        </div>
      )
    }

    // Different AM/PM activities
    return (
      <div className={`schedule-cell min-h-[52px] ${isWeekendDay ? 'bg-gray-50' : 'bg-white'}`}>
        <div
          className={`rounded px-0.5 py-0.5 mb-0.5 text-xs text-center ${
            amAssignment ? getActivityColor(amAssignment.activity) : ''
          }`}
          title={amAssignment?.activity}
          onClick={() => handleCellClick('AM', amAssignment)}
        >
          {amAssignment ? (
            <span className="font-medium text-[10px]">{amAssignment.abbreviation}</span>
          ) : (
            <span className="text-gray-300">-</span>
          )}
        </div>
        <div
          className={`rounded px-0.5 py-0.5 text-xs text-center ${
            pmAssignment ? getActivityColor(pmAssignment.activity) : ''
          }`}
          title={pmAssignment?.activity}
          onClick={() => handleCellClick('PM', pmAssignment)}
        >
          {pmAssignment ? (
            <span className="font-medium text-[10px]">{pmAssignment.abbreviation}</span>
          ) : (
            <span className="text-gray-300">-</span>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="card overflow-hidden">
      {/* Navigation Header */}
      <div className="flex items-center justify-between pb-4 border-b mb-4">
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrevWeek}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Previous week"
          >
            <ChevronLeft className="w-5 h-5 text-gray-600" />
          </button>
          <button
            onClick={handleNextWeek}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Next week"
          >
            <ChevronRight className="w-5 h-5 text-gray-600" />
          </button>
          <button
            onClick={handleThisWeek}
            className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            This Week
          </button>
        </div>

        <div className="text-center">
          <div className="text-lg font-semibold text-gray-900">
            {format(weekStart, 'MMM d')} - {format(weekEnd, 'MMM d, yyyy')}
          </div>
          <div className="text-sm text-gray-500">Week {weekNumber}</div>
        </div>

        <div className="w-[140px]"></div>
      </div>

      {/* Grid */}
      <div className="overflow-x-auto">
        <div className="min-w-[800px]">
          {/* Header Row */}
          <div className="grid grid-cols-8 border-b bg-gray-50">
            <div className="p-2 font-semibold text-gray-700 text-sm">Person</div>
            {days.map((day) => {
              const dateStr = format(day, 'yyyy-MM-dd')
              const holidayName = holidays[dateStr]
              const isTodayDate = isToday(day)
              const isWeekendDay = day.getDay() === 0 || day.getDay() === 6

              return (
                <div
                  key={day.toISOString()}
                  className={`p-2 text-center cursor-pointer hover:bg-gray-200 transition-colors ${
                    isWeekendDay ? 'bg-gray-100' : ''
                  } ${isTodayDate ? 'ring-2 ring-inset ring-blue-400' : ''}`}
                  onClick={() => onDayClick?.(day)}
                  title={holidayName || undefined}
                >
                  <div className={`font-semibold text-sm ${isTodayDate ? 'text-blue-600' : ''}`}>
                    {format(day, 'EEE')}
                  </div>
                  <div className="text-xs text-gray-500">{format(day, 'M/d')}</div>
                  {holidayName && (
                    <div className="text-[9px] text-amber-600 truncate mt-0.5">
                      {holidayName}
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Person Rows */}
          {people.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No schedule data for this week.
            </div>
          ) : (
            people.map(([personId, person]) => (
              <div key={personId} className="grid grid-cols-8 border-b hover:bg-gray-50/50">
                {/* Person Info */}
                <div className="p-2 border-r">
                  <div className="font-medium text-gray-900 text-sm truncate">
                    {person.name}
                  </div>
                  <div className="text-xs text-gray-500">
                    {person.type === 'resident' ? `PGY-${person.pgy_level}` : 'Faculty'}
                  </div>
                </div>

                {/* Day Cells */}
                {days.map((day) => {
                  const dateStr = format(day, 'yyyy-MM-dd')
                  const daySchedule = schedule[dateStr]
                  const amAssignment = daySchedule?.AM?.find((a) => a.person.id === personId)
                  const pmAssignment = daySchedule?.PM?.find((a) => a.person.id === personId)

                  return (
                    <React.Fragment key={dateStr}>
                      {renderCell(day, personId, amAssignment, pmAssignment)}
                    </React.Fragment>
                  )
                })}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
