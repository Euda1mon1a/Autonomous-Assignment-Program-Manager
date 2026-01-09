'use client'

import React, { useState, useMemo, useCallback } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import {
  format,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  addMonths,
  subMonths,
  getDay,
} from 'date-fns'
import type { Absence, Person } from '@/types/api'

interface AbsenceCalendarProps {
  absences: Absence[]
  people: Person[]
  onAbsenceClick: (absence: Absence) => void
}

const typeColors: Record<string, { bg: string; border: string; text: string }> = {
  // Planned leave
  vacation: { bg: 'bg-green-100', border: 'border-green-500', text: 'text-green-700' },
  conference: { bg: 'bg-blue-100', border: 'border-blue-500', text: 'text-blue-700' },
  // Medical
  sick: { bg: 'bg-red-100', border: 'border-red-500', text: 'text-red-700' },
  medical: { bg: 'bg-red-100', border: 'border-red-500', text: 'text-red-700' },
  convalescent: { bg: 'bg-red-200', border: 'border-red-600', text: 'text-red-800' },
  maternity_paternity: { bg: 'bg-pink-100', border: 'border-pink-500', text: 'text-pink-700' },
  // Emergency (blocking - Hawaii reality)
  family_emergency: { bg: 'bg-purple-100', border: 'border-purple-500', text: 'text-purple-700' },
  emergency_leave: { bg: 'bg-purple-200', border: 'border-purple-600', text: 'text-purple-800' },
  bereavement: { bg: 'bg-gray-200', border: 'border-gray-600', text: 'text-gray-800' },
  // Military
  deployment: { bg: 'bg-orange-100', border: 'border-orange-500', text: 'text-orange-700' },
  tdy: { bg: 'bg-yellow-100', border: 'border-yellow-500', text: 'text-yellow-700' },
  // Fallback
  personal: { bg: 'bg-purple-100', border: 'border-purple-500', text: 'text-purple-700' },
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

// Memoized day cell component to prevent unnecessary re-renders
interface AbsenceDayCellProps {
  day: Date
  dateKey: string
  dayAbsences: Absence[]
  isWeekend: boolean
  isCurrentMonth: boolean
  isToday: boolean
  personMap: Map<string, Person>
  onAbsenceClick: (absence: Absence) => void
}

const AbsenceDayCell = React.memo(function AbsenceDayCell({
  day,
  dateKey,
  dayAbsences,
  isWeekend,
  isCurrentMonth,
  isToday,
  personMap,
  onAbsenceClick,
}: AbsenceDayCellProps) {
  return (
    <div
      className={`min-h-[100px] border-r border-b p-1 ${
        isWeekend ? 'bg-gray-50' : 'bg-white'
      } ${!isCurrentMonth ? 'opacity-50' : ''}`}
    >
      {/* Day Number */}
      <div
        className={`text-sm font-medium mb-1 ${
          isToday
            ? 'bg-blue-600 text-white w-6 h-6 rounded-full flex items-center justify-center'
            : 'text-gray-700 px-1'
        }`}
      >
        {format(day, 'd')}
      </div>

      {/* Absences for this day */}
      <div className="space-y-1">
        {dayAbsences.slice(0, 3).map((absence) => {
          const person = personMap.get(absence.personId)
          const colors = typeColors[absence.absenceType] || typeColors.personal

          return (
            <button
              key={absence.id}
              onClick={() => onAbsenceClick(absence)}
              className={`w-full text-left px-1 py-0.5 text-xs rounded border-l-2 truncate ${colors.bg} ${colors.border} ${colors.text} hover:opacity-80 transition-opacity`}
              title={`${person?.name || 'Unknown'} - ${absence.absenceType}`}
            >
              {person ? getInitials(person.name) : '??'}{' '}
              <span className="capitalize">{absence.absenceType.replace('_', ' ')}</span>
            </button>
          )
        })}
        {dayAbsences.length > 3 && (
          <div className="text-xs text-gray-500 px-1">
            +{dayAbsences.length - 3} more
          </div>
        )}
      </div>
    </div>
  )
})

export function AbsenceCalendar({ absences, people, onAbsenceClick }: AbsenceCalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date())

  // Memoize date calculations
  const { days, blankDays, monthStart } = useMemo(() => {
    const start = startOfMonth(currentDate)
    const end = endOfMonth(currentDate)
    return {
      days: eachDayOfInterval({ start, end }),
      blankDays: Array.from({ length: getDay(start) }, (_, i) => i),
      monthStart: start,
    }
  }, [currentDate])

  // Create a map of person_id to person for quick lookup
  const personMap = useMemo(() => {
    const map = new Map<string, Person>()
    people.forEach((p) => map.set(p.id, p))
    return map
  }, [people])

  // Group absences by day
  const absencesByDay = useMemo(() => {
    const map = new Map<string, Absence[]>()

    absences.forEach((absence) => {
      const startDate = new Date(absence.startDate)
      const endDate = new Date(absence.endDate)

      // Add absence to each day in its range
      days.forEach((day) => {
        if (day >= startDate && day <= endDate) {
          const dateKey = format(day, 'yyyy-MM-dd')
          const existing = map.get(dateKey) || []
          if (!existing.find((a) => a.id === absence.id)) {
            map.set(dateKey, [...existing, absence])
          }
        }
      })
    })

    return map
  }, [absences, days])

  const handlePrevMonth = useCallback(() => setCurrentDate(subMonths(currentDate, 1)), [currentDate])
  const handleNextMonth = useCallback(() => setCurrentDate(addMonths(currentDate, 1)), [currentDate])

  return (
    <div className="card">
      {/* Header with Navigation */}
      <div className="flex items-center justify-between mb-4 px-2">
        <button
          onClick={handlePrevMonth}
          className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          aria-label="Previous month"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <h2 className="text-lg font-semibold text-gray-900">
          {format(currentDate, 'MMMM yyyy')}
        </h2>
        <button
          onClick={handleNextMonth}
          className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          aria-label="Next month"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Day Headers */}
      <div className="grid grid-cols-7 border-b">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
          <div
            key={day}
            className="py-2 text-center text-sm font-medium text-gray-500"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 border-l">
        {/* Blank days for offset */}
        {blankDays.map((i) => (
          <div
            key={`blank-${i}`}
            className="min-h-[100px] border-r border-b bg-gray-50"
          />
        ))}

        {/* Actual days */}
        {days.map((day) => {
          const dateKey = format(day, 'yyyy-MM-dd')
          const dayAbsences = absencesByDay.get(dateKey) || []
          const isWeekend = getDay(day) === 0 || getDay(day) === 6

          return (
            <AbsenceDayCell
              key={dateKey}
              day={day}
              dateKey={dateKey}
              dayAbsences={dayAbsences}
              isWeekend={isWeekend}
              isCurrentMonth={isSameMonth(day, currentDate)}
              isToday={isSameDay(day, new Date())}
              personMap={personMap}
              onAbsenceClick={onAbsenceClick}
            />
          )
        })}
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-3 px-2 text-xs">
        {Object.entries(typeColors).slice(0, 6).map(([type, colors]) => (
          <div key={type} className="flex items-center gap-1">
            <span
              className={`w-3 h-3 rounded border-l-2 ${colors.bg} ${colors.border}`}
            />
            <span className="capitalize text-gray-600">{type.replace('_', ' ')}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
