'use client'

import React, { useMemo } from 'react'
import Link from 'next/link'
import { format, addDays } from 'date-fns'
import { DayCell } from './DayCell'

interface Assignment {
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
    AM: Assignment[]
    PM: Assignment[]
  }
}

interface ScheduleCalendarProps {
  weekStart: Date
  schedule: ScheduleData
  /** Optional callback when Generate Schedule is clicked. If not provided, navigates to /admin/scheduling */
  onGenerateSchedule?: () => void
}

export function ScheduleCalendar({ weekStart, schedule, onGenerateSchedule }: ScheduleCalendarProps) {
  // Memoize days array to prevent recalculation on each render
  const days = useMemo(() =>
    Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)),
    [weekStart]
  )

  // Memoize people extraction and sorting
  const people = useMemo(() => {
    const allPeople = new Map<string, { name: string; type: string; pgyLevel: number | null }>()

    Object.values(schedule).forEach((dayData) => {
      ;['AM', 'PM'].forEach((time) => {
        dayData[time as 'AM' | 'PM']?.forEach((assignment) => {
          if (!allPeople.has(assignment.person.id)) {
            allPeople.set(assignment.person.id, assignment.person)
          }
        })
      })
    })

    return Array.from(allPeople.entries()).sort((a, b) => {
      // Sort residents by PGY level, then faculty, then by name
      const aLevel = a[1].pgyLevel || 99
      const bLevel = b[1].pgyLevel || 99
      if (aLevel !== bLevel) return aLevel - bLevel
      return a[1].name.localeCompare(b[1].name)
    })
  }, [schedule])

  return (
    <div className="card overflow-hidden">
      {/* Header Row */}
      <div className="grid grid-cols-8 border-b bg-gray-50">
        <div className="p-3 font-semibold text-gray-700">Person</div>
        {days.map((day) => (
          <div
            key={day.toISOString()}
            className={`p-3 text-center ${
              day.getDay() === 0 || day.getDay() === 6
                ? 'bg-gray-100 text-gray-500'
                : ''
            }`}
          >
            <div className="font-semibold">{format(day, 'EEE')}</div>
            <div className="text-sm text-gray-500">{format(day, 'MMM d')}</div>
          </div>
        ))}
      </div>

      {/* Person Rows */}
      {people.length === 0 ? (
        <div className="p-8 text-center text-gray-500">
          No schedule data for this week.
          <br />
          {onGenerateSchedule ? (
            <button
              className="btn-primary mt-4"
              onClick={onGenerateSchedule}
            >
              Generate Schedule
            </button>
          ) : (
            <Link href="/admin/scheduling" className="btn-primary mt-4 inline-block">
              Generate Schedule
            </Link>
          )}
        </div>
      ) : (
        people.map(([personId, person]) => (
          <div key={personId} className="grid grid-cols-8 border-b hover:bg-gray-50">
            {/* Person Info */}
            <div className="p-3 border-r">
              <div className="font-medium text-gray-900">{person.name}</div>
              <div className="text-xs text-gray-500">
                {person.type === 'resident'
                  ? `PGY-${person.pgyLevel}`
                  : 'Faculty'}
              </div>
            </div>

            {/* Day Cells */}
            {days.map((day) => {
              const dateStr = format(day, 'yyyy-MM-dd')
              const daySchedule = schedule[dateStr]

              // Find assignments for this person on this day
              const amAssignment = daySchedule?.AM?.find(
                (a) => a.person.id === personId
              )
              const pmAssignment = daySchedule?.PM?.find(
                (a) => a.person.id === personId
              )

              return (
                <DayCell
                  key={dateStr}
                  date={day}
                  amAssignment={amAssignment}
                  pmAssignment={pmAssignment}
                />
              )
            })}
          </div>
        ))
      )}
    </div>
  )
}
