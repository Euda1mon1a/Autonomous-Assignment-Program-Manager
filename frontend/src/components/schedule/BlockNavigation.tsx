'use client'

import { format, startOfWeek, addDays, subDays } from 'date-fns'

interface BlockNavigationProps {
  startDate: Date
  endDate: Date
  onDateRangeChange: (start: Date, end: Date) => void
}

/**
 * Navigation controls for the schedule grid
 * Provides Previous/Next block buttons, Today, This Block, and date pickers
 */
export function BlockNavigation({
  startDate,
  endDate,
  onDateRangeChange,
}: BlockNavigationProps) {
  // Get the start of the current 4-week block (starts on Monday)
  const getCurrentBlockStart = () => {
    const today = new Date()
    const monday = startOfWeek(today, { weekStartsOn: 1 })
    return monday
  }

  // Navigate to previous 4-week block
  const handlePreviousBlock = () => {
    const newStart = subDays(startDate, 28)
    const newEnd = subDays(endDate, 28)
    onDateRangeChange(newStart, newEnd)
  }

  // Navigate to next 4-week block
  const handleNextBlock = () => {
    const newStart = addDays(startDate, 28)
    const newEnd = addDays(endDate, 28)
    onDateRangeChange(newStart, newEnd)
  }

  // Jump to today's date (centered in a 4-week block)
  const handleToday = () => {
    const today = new Date()
    const monday = startOfWeek(today, { weekStartsOn: 1 })
    onDateRangeChange(monday, addDays(monday, 27))
  }

  // Jump to current 4-week block
  const handleThisBlock = () => {
    const blockStart = getCurrentBlockStart()
    onDateRangeChange(blockStart, addDays(blockStart, 27))
  }

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
      {/* Block navigation buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={handlePreviousBlock}
          className="btn-secondary flex items-center gap-1"
          aria-label="Previous block"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Previous Block
        </button>

        <button
          onClick={handleNextBlock}
          className="btn-secondary flex items-center gap-1"
          aria-label="Next block"
        >
          Next Block
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>

      {/* Quick navigation buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleToday}
          className="btn-secondary text-sm"
          aria-label="Jump to today"
        >
          Today
        </button>
        <button
          onClick={handleThisBlock}
          className="btn-secondary text-sm"
          aria-label="Jump to this block"
        >
          This Block
        </button>
      </div>

      {/* Date range display (read-only - use navigation buttons to change) */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-600">Block:</span>
        <span className="font-medium text-gray-900 bg-gray-100 px-3 py-1 rounded">
          {format(startDate, 'MMM d')} - {format(endDate, 'MMM d, yyyy')}
        </span>
      </div>

      {/* Current range display */}
      <div className="text-sm text-gray-600 ml-auto hidden lg:block">
        {format(startDate, 'MMM d, yyyy')} - {format(endDate, 'MMM d, yyyy')}
      </div>
    </div>
  )
}
