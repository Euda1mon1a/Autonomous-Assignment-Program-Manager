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

  // Handle date input changes
  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newStart = new Date(e.target.value + 'T00:00:00')
    if (!isNaN(newStart.getTime())) {
      // Keep the same duration (28 days)
      onDateRangeChange(newStart, addDays(newStart, 27))
    }
  }

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEnd = new Date(e.target.value + 'T00:00:00')
    if (!isNaN(newEnd.getTime()) && newEnd > startDate) {
      onDateRangeChange(startDate, newEnd)
    }
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

      {/* Date range picker */}
      <div className="flex items-center gap-2 text-sm">
        <label className="text-gray-600">From:</label>
        <input
          type="date"
          value={format(startDate, 'yyyy-MM-dd')}
          onChange={handleStartDateChange}
          className="input-field text-sm py-1 px-2"
          aria-label="Start date"
        />
        <label className="text-gray-600">To:</label>
        <input
          type="date"
          value={format(endDate, 'yyyy-MM-dd')}
          onChange={handleEndDateChange}
          className="input-field text-sm py-1 px-2"
          aria-label="End date"
        />
      </div>

      {/* Current range display */}
      <div className="text-sm text-gray-600 ml-auto hidden lg:block">
        {format(startDate, 'MMM d, yyyy')} - {format(endDate, 'MMM d, yyyy')}
      </div>
    </div>
  )
}
