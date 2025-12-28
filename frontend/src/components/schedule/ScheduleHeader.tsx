'use client'

import { format, isWeekend } from 'date-fns'
import { useMemo } from 'react'

interface ScheduleHeaderProps {
  days: Date[]
}

/**
 * Sticky header row for the schedule grid
 * Shows dates with day-of-week and AM/PM sub-columns
 * Weekend columns are slightly shaded
 */
export function ScheduleHeader({ days }: ScheduleHeaderProps) {
  // Memoize the header cells to prevent recalculation
  const headerCells = useMemo(() => {
    return days.map((day) => {
      const weekend = isWeekend(day)
      const isToday = format(day, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd')

      return {
        date: day,
        dateStr: format(day, 'yyyy-MM-dd'),
        dayName: format(day, 'EEE'),
        dayNumber: format(day, 'd'),
        month: format(day, 'MMM'),
        isWeekend: weekend,
        isToday,
      }
    })
  }, [days])

  return (
    <thead className="bg-gray-50">
      {/* Date row */}
      <tr className="border-b border-gray-200">
        {/* Person column header - spans 2 rows, sticky both top and left (corner cell) */}
        <th
          rowSpan={2}
          className="sticky left-0 top-0 z-30 bg-gray-50 px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-r border-gray-200 min-w-[180px] shadow-[2px_2px_4px_-2px_rgba(0,0,0,0.1)]"
        >
          Person
        </th>

        {/* Date headers - each day spans 2 columns (AM/PM), sticky top */}
        {headerCells.map((cell) => (
          <th
            key={cell.dateStr}
            colSpan={2}
            className={`sticky top-0 z-20 px-2 py-2 text-center border-r border-gray-200 ${
              cell.isWeekend ? 'bg-gray-100' : 'bg-gray-50'
            } ${cell.isToday ? 'bg-blue-50 ring-2 ring-blue-300 ring-inset' : ''}`}
          >
            <div className="flex flex-col items-center">
              <span
                className={`text-xs font-semibold ${
                  cell.isWeekend ? 'text-gray-500' : 'text-gray-700'
                } ${cell.isToday ? 'text-blue-700' : ''}`}
              >
                {cell.dayName}
              </span>
              <span
                className={`text-sm font-medium ${
                  cell.isWeekend ? 'text-gray-400' : 'text-gray-600'
                } ${cell.isToday ? 'text-blue-600' : ''}`}
              >
                {cell.month} {cell.dayNumber}
              </span>
            </div>
          </th>
        ))}
      </tr>

      {/* AM/PM sub-header row - sticky below the date row */}
      <tr className="border-b-2 border-gray-300">
        {headerCells.map((cell) => (
          <th
            key={`${cell.dateStr}-ampm`}
            colSpan={2}
            className={`sticky top-[52px] z-20 border-r border-gray-200 ${
              cell.isWeekend ? 'bg-gray-100' : 'bg-gray-50'
            } ${cell.isToday ? 'bg-blue-50' : ''}`}
          >
            <div className="flex">
              <span
                className={`flex-1 text-[10px] font-medium py-1 border-r border-gray-200 ${
                  cell.isWeekend ? 'text-gray-400' : 'text-gray-500'
                }`}
              >
                AM
              </span>
              <span
                className={`flex-1 text-[10px] font-medium py-1 ${
                  cell.isWeekend ? 'text-gray-400' : 'text-gray-500'
                }`}
              >
                PM
              </span>
            </div>
          </th>
        ))}
      </tr>
    </thead>
  )
}
