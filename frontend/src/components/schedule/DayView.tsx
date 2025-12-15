'use client'

import React, { useMemo, useState } from 'react'
import { format, addDays, subDays, isToday, isWeekend } from 'date-fns'
import { ChevronLeft, ChevronRight, Calendar } from 'lucide-react'

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

export interface DayViewProps {
  currentDate: Date
  schedule: ScheduleData
  onDateChange: (date: Date) => void
  onCellClick?: (personId: string, date: Date, timeOfDay: 'AM' | 'PM', assignment?: Assignment) => void
  personFilter?: string[]
  holidays?: Record<string, string>
}

// Activity type to color mapping
const activityColors: Record<string, string> = {
  clinic: 'bg-clinic-light text-clinic-dark border-clinic',
  inpatient: 'bg-inpatient-light text-inpatient-dark border-inpatient',
  call: 'bg-call-light text-call-dark border-call',
  leave: 'bg-leave-light text-leave-dark border-leave',
  conference: 'bg-gray-100 text-gray-700 border-gray-300',
  default: 'bg-blue-50 text-blue-700 border-blue-300',
}

function getActivityColor(activity: string): string {
  const activityLower = activity.toLowerCase()
  for (const [key, color] of Object.entries(activityColors)) {
    if (activityLower.includes(key)) {
      return color
    }
  }
  return activityColors.default
}

export function DayView({
  currentDate,
  schedule,
  onDateChange,
  onCellClick,
  personFilter,
  holidays = {},
}: DayViewProps) {
  const [showDatePicker, setShowDatePicker] = useState(false)

  const dateStr = format(currentDate, 'yyyy-MM-dd')
  const daySchedule = schedule[dateStr]
  const holidayName = holidays[dateStr]

  // Extract and sort people for this day
  const people = useMemo(() => {
    const allPeople = new Map<string, Person>()

    if (daySchedule) {
      ;['AM', 'PM'].forEach((time) => {
        daySchedule[time as 'AM' | 'PM']?.forEach((assignment) => {
          if (!allPeople.has(assignment.person.id)) {
            allPeople.set(assignment.person.id, assignment.person)
          }
        })
      })
    }

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
  }, [daySchedule, personFilter])

  const handlePrevDay = () => onDateChange(subDays(currentDate, 1))
  const handleNextDay = () => onDateChange(addDays(currentDate, 1))
  const handleToday = () => onDateChange(new Date())

  const handleDateInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = new Date(e.target.value + 'T12:00:00')
    if (!isNaN(newDate.getTime())) {
      onDateChange(newDate)
      setShowDatePicker(false)
    }
  }

  const renderAssignmentCell = (
    assignment: Assignment | undefined,
    personId: string,
    timeOfDay: 'AM' | 'PM'
  ) => {
    const handleClick = () => {
      onCellClick?.(personId, currentDate, timeOfDay, assignment)
    }

    if (!assignment) {
      return (
        <div
          onClick={handleClick}
          className="flex-1 p-4 bg-gray-50 rounded-lg border border-dashed border-gray-200 cursor-pointer hover:bg-gray-100 hover:border-gray-300 transition-colors min-h-[80px] flex items-center justify-center"
        >
          <span className="text-gray-400 text-sm">No assignment</span>
        </div>
      )
    }

    return (
      <div
        onClick={handleClick}
        className={`flex-1 p-4 rounded-lg border-l-4 cursor-pointer hover:ring-2 hover:ring-blue-400 transition-all min-h-[80px] ${getActivityColor(
          assignment.activity
        )}`}
      >
        <div className="font-semibold text-lg">{assignment.activity}</div>
        <div className="text-sm opacity-80 mt-1">
          {assignment.abbreviation} &bull; {assignment.role}
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      {/* Navigation Header */}
      <div className="flex items-center justify-between pb-4 border-b mb-4">
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrevDay}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Previous day"
          >
            <ChevronLeft className="w-5 h-5 text-gray-600" />
          </button>
          <button
            onClick={handleNextDay}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Next day"
          >
            <ChevronRight className="w-5 h-5 text-gray-600" />
          </button>
          <button
            onClick={handleToday}
            className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            Today
          </button>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {format(currentDate, 'EEEE, MMMM d, yyyy')}
            </div>
            <div className="flex items-center justify-center gap-2 mt-1">
              {isToday(currentDate) && (
                <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
                  Today
                </span>
              )}
              {isWeekend(currentDate) && (
                <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">
                  Weekend
                </span>
              )}
              {holidayName && (
                <span className="px-2 py-0.5 text-xs font-medium bg-amber-100 text-amber-700 rounded-full">
                  {holidayName}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="relative">
          <button
            onClick={() => setShowDatePicker(!showDatePicker)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Jump to date"
          >
            <Calendar className="w-5 h-5 text-gray-600" />
          </button>
          {showDatePicker && (
            <div className="absolute right-0 top-full mt-2 p-2 bg-white border rounded-lg shadow-lg z-10">
              <input
                type="date"
                value={format(currentDate, 'yyyy-MM-dd')}
                onChange={handleDateInput}
                className="input-field"
                autoFocus
              />
            </div>
          )}
        </div>
      </div>

      {/* AM/PM Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AM Section */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
            <h3 className="text-lg font-semibold text-gray-700">Morning (AM)</h3>
          </div>
          <div className="space-y-3">
            {people.length === 0 ? (
              <div className="text-gray-500 text-center py-8">
                No assignments for this day
              </div>
            ) : (
              people.map(([personId, person]) => {
                const amAssignment = daySchedule?.AM?.find(
                  (a) => a.person.id === personId
                )
                return (
                  <div key={`am-${personId}`} className="flex items-stretch gap-3">
                    <div className="w-36 py-4 flex flex-col justify-center">
                      <div className="font-medium text-gray-900">{person.name}</div>
                      <div className="text-xs text-gray-500">
                        {person.type === 'resident'
                          ? `PGY-${person.pgy_level}`
                          : 'Faculty'}
                      </div>
                    </div>
                    {renderAssignmentCell(amAssignment, personId, 'AM')}
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* PM Section */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-3 h-3 rounded-full bg-indigo-500"></div>
            <h3 className="text-lg font-semibold text-gray-700">Afternoon (PM)</h3>
          </div>
          <div className="space-y-3">
            {people.length === 0 ? (
              <div className="text-gray-500 text-center py-8">
                No assignments for this day
              </div>
            ) : (
              people.map(([personId, person]) => {
                const pmAssignment = daySchedule?.PM?.find(
                  (a) => a.person.id === personId
                )
                return (
                  <div key={`pm-${personId}`} className="flex items-stretch gap-3">
                    <div className="w-36 py-4 flex flex-col justify-center">
                      <div className="font-medium text-gray-900">{person.name}</div>
                      <div className="text-xs text-gray-500">
                        {person.type === 'resident'
                          ? `PGY-${person.pgy_level}`
                          : 'Faculty'}
                      </div>
                    </div>
                    {renderAssignmentCell(pmAssignment, personId, 'PM')}
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
