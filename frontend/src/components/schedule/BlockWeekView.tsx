'use client'

import { useState, useMemo, useCallback } from 'react'
import { format, addDays, startOfWeek, isWithinInterval, isBefore, isAfter } from 'date-fns'
import { ChevronLeft, ChevronRight, Calendar } from 'lucide-react'
import { ScheduleGrid } from './ScheduleGrid'

interface BlockWeekViewProps {
  /** Block start date */
  blockStartDate: Date
  /** Block end date */
  blockEndDate: Date
  /** Current block number (for display) */
  blockNumber: number | null
  /** Optional person filter */
  personFilter?: Set<string>
}

/**
 * BlockWeekView - Shows a week within a block's boundaries
 *
 * Unlike the Calendar Week view which shows Mon-Sun, this shows
 * a week within the context of the selected block. Navigation
 * is constrained to stay within the block boundaries.
 */
export function BlockWeekView({
  blockStartDate,
  blockEndDate,
  blockNumber,
  personFilter,
}: BlockWeekViewProps) {
  // Initialize to the week containing today if within block, otherwise first week of block
  const [currentWeekStart, setCurrentWeekStart] = useState<Date>(() => {
    const today = new Date()
    const blockStart = blockStartDate
    const blockEnd = blockEndDate

    // If today is within the block, start from today's week
    if (isWithinInterval(today, { start: blockStart, end: blockEnd })) {
      // Get Monday of this week (or the block start if it's later)
      const weekStart = startOfWeek(today, { weekStartsOn: 1 })
      return isBefore(weekStart, blockStart) ? blockStart : weekStart
    }

    // Otherwise start from the block's start date
    return blockStart
  })

  // Calculate the week end (6 days after start, but not past block end)
  const currentWeekEnd = useMemo(() => {
    const weekEnd = addDays(currentWeekStart, 6)
    return isAfter(weekEnd, blockEndDate) ? blockEndDate : weekEnd
  }, [currentWeekStart, blockEndDate])

  // Calculate available weeks within the block
  const weeksInBlock = useMemo(() => {
    const weeks: { start: Date; end: Date; label: string }[] = []
    let weekStart = blockStartDate
    let weekNum = 1

    while (isBefore(weekStart, blockEndDate) || weekStart.getTime() === blockEndDate.getTime()) {
      const weekEnd = addDays(weekStart, 6)
      const actualEnd = isAfter(weekEnd, blockEndDate) ? blockEndDate : weekEnd

      weeks.push({
        start: weekStart,
        end: actualEnd,
        label: `Week ${weekNum}`,
      })

      weekStart = addDays(weekStart, 7)
      weekNum++

      // Safety: max 6 weeks in a block
      if (weekNum > 6) break
    }

    return weeks
  }, [blockStartDate, blockEndDate])

  // Current week index
  const currentWeekIndex = useMemo(() => {
    return weeksInBlock.findIndex(
      (w) => w.start.getTime() === currentWeekStart.getTime()
    )
  }, [weeksInBlock, currentWeekStart])

  // Navigation handlers
  const handlePreviousWeek = useCallback(() => {
    if (currentWeekIndex > 0) {
      setCurrentWeekStart(weeksInBlock[currentWeekIndex - 1].start)
    }
  }, [currentWeekIndex, weeksInBlock])

  const handleNextWeek = useCallback(() => {
    if (currentWeekIndex < weeksInBlock.length - 1) {
      setCurrentWeekStart(weeksInBlock[currentWeekIndex + 1].start)
    }
  }, [currentWeekIndex, weeksInBlock])

  const handleWeekSelect = useCallback(
    (weekIndex: number) => {
      if (weekIndex >= 0 && weekIndex < weeksInBlock.length) {
        setCurrentWeekStart(weeksInBlock[weekIndex].start)
      }
    },
    [weeksInBlock]
  )

  // Jump to today's week if within block
  const handleToday = useCallback(() => {
    const today = new Date()
    if (isWithinInterval(today, { start: blockStartDate, end: blockEndDate })) {
      const todayWeek = weeksInBlock.find(
        (w) => isWithinInterval(today, { start: w.start, end: w.end })
      )
      if (todayWeek) {
        setCurrentWeekStart(todayWeek.start)
      }
    }
  }, [blockStartDate, blockEndDate, weeksInBlock])

  // Check if today is in the current week
  const isTodayInCurrentWeek = useMemo(() => {
    const today = new Date()
    return isWithinInterval(today, { start: currentWeekStart, end: currentWeekEnd })
  }, [currentWeekStart, currentWeekEnd])

  // Check if today is in this block
  const isTodayInBlock = useMemo(() => {
    const today = new Date()
    return isWithinInterval(today, { start: blockStartDate, end: blockEndDate })
  }, [blockStartDate, blockEndDate])

  return (
    <div className="h-full flex flex-col">
      {/* Navigation Header */}
      <div className="flex items-center justify-between mb-4 bg-white rounded-lg p-3 shadow-sm border border-gray-200">
        <div className="flex items-center gap-3">
          {/* Block info */}
          <div className="text-sm text-gray-600">
            <span className="font-medium text-gray-900">
              {blockNumber !== null ? `Block ${blockNumber}` : 'Block'}
            </span>
            <span className="mx-2 text-gray-400">|</span>
            <span>
              {format(blockStartDate, 'MMM d')} - {format(blockEndDate, 'MMM d, yyyy')}
            </span>
          </div>
        </div>

        {/* Week Navigation */}
        <div className="flex items-center gap-2">
          <button
            onClick={handlePreviousWeek}
            disabled={currentWeekIndex === 0}
            className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label="Previous week"
          >
            <ChevronLeft className="w-5 h-5 text-gray-600" />
          </button>

          {/* Week selector dropdown */}
          <select
            value={currentWeekIndex}
            onChange={(e) => handleWeekSelect(parseInt(e.target.value))}
            className="px-3 py-1.5 text-sm font-medium border border-gray-200 rounded-md bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {weeksInBlock.map((week, idx) => (
              <option key={idx} value={idx}>
                {week.label}: {format(week.start, 'MMM d')} - {format(week.end, 'MMM d')}
              </option>
            ))}
          </select>

          <button
            onClick={handleNextWeek}
            disabled={currentWeekIndex === weeksInBlock.length - 1}
            className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label="Next week"
          >
            <ChevronRight className="w-5 h-5 text-gray-600" />
          </button>

          {/* Today button */}
          {isTodayInBlock && !isTodayInCurrentWeek && (
            <button
              onClick={handleToday}
              className="ml-2 px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-md flex items-center gap-1"
            >
              <Calendar className="w-4 h-4" />
              Today
            </button>
          )}
        </div>

        {/* Current week dates */}
        <div className="text-sm font-medium text-gray-900 bg-gray-100 px-3 py-1.5 rounded">
          {format(currentWeekStart, 'MMM d')} - {format(currentWeekEnd, 'MMM d, yyyy')}
        </div>
      </div>

      {/* Schedule Grid for the week */}
      <div className="flex-1">
        <ScheduleGrid
          startDate={currentWeekStart}
          endDate={currentWeekEnd}
          personFilter={personFilter}
        />
      </div>
    </div>
  )
}

export default BlockWeekView
