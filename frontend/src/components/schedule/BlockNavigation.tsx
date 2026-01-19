'use client'

import { useMemo } from 'react'
import { format, addDays, subDays, parseISO } from 'date-fns'
import { AlertTriangle } from 'lucide-react'
import { useBlocks, useBlockRanges } from '@/hooks'

/**
 * Calculate academic year from a Date object.
 * Academic year starts July 1, so:
 * - 2024-07-01 to 2025-06-30 = AY 2024
 * - 2025-07-01 to 2026-06-30 = AY 2025
 */
function getAcademicYear(date: Date): number {
  const month = date.getMonth() + 1 // getMonth() is 0-indexed
  const year = date.getFullYear()
  return month < 7 ? year - 1 : year
}

interface BlockNavigationProps {
  startDate: Date
  endDate: Date
  onDateRangeChange: (start: Date, end: Date) => void
}

/**
 * Navigation controls for the schedule grid
 * Provides Previous/Next block buttons, Today, This Block, and date pickers
 *
 * Block number and date ranges are fetched from the API to ensure accuracy.
 * The API returns actual block boundaries from the database rather than
 * using hardcoded calculations.
 *
 * Gracefully handles authentication errors (401) by showing fallback navigation
 * that works with manual date offsets instead of block data.
 */
export function BlockNavigation({
  startDate,
  endDate,
  onDateRangeChange,
}: BlockNavigationProps) {
  // Format dates for API query
  const startDateStr = format(startDate, 'yyyy-MM-dd')
  const endDateStr = format(endDate, 'yyyy-MM-dd')

  // Fetch blocks for the current date range to get the block number
  // Error handling: On 401, blocksData will be undefined and we fall back to date-based nav
  const { data: blocksData, isLoading: blocksLoading, error: blocksError } = useBlocks({
    startDate: startDateStr,
    endDate: endDateStr,
  })

  // Fetch all block ranges for navigation (to find prev/next blocks and "This Block")
  // Error handling: On 401, blockRanges will be undefined and we use date offsets
  const { data: blockRanges, isLoading: rangesLoading, error: rangesError } = useBlockRanges()

  // Determine if we're in fallback mode (API unavailable or auth error)
  const isFallbackMode = Boolean(blocksError || rangesError)

  // Get the block number from the fetched blocks
  // All blocks in the range should have the same blockNumber (or we take the first one)
  const currentBlockNumber = useMemo(() => {
    if (!blocksData?.items?.length) return null
    // Get unique block numbers from the fetched blocks
    const blockNumbers = [...new Set(blocksData.items.map((b) => b.blockNumber))]
    // If we're viewing a single block, return that number
    // If multiple blocks are in view, return the first one (start of range)
    return blockNumbers[0] ?? null
  }, [blocksData])

  // Find current block range, previous block, and next block
  const { currentBlockRange: _currentBlockRange, previousBlockRange, nextBlockRange, todayBlockRange } = useMemo(() => {
    if (!blockRanges?.length) {
      return {
        currentBlockRange: null,
        previousBlockRange: null,
        nextBlockRange: null,
        todayBlockRange: null,
      }
    }

    // Calculate current academic year from the view's start date
    // This ensures we match the correct block when multiple years have same block numbers
    const currentAY = getAcademicYear(startDate)

    // Find the block range that matches BOTH block number AND academic year
    // Without academicYear check, Block 10 AY2024 could match Block 10 AY2025
    const currentIdx = blockRanges.findIndex(
      (r) => r.blockNumber === currentBlockNumber && r.academicYear === currentAY
    )
    const current = currentIdx >= 0 ? blockRanges[currentIdx] : null
    // Previous/next can cross academic year boundaries (e.g., Block 13 → Block 1)
    const previous = currentIdx > 0 ? blockRanges[currentIdx - 1] : null
    const next = currentIdx >= 0 && currentIdx < blockRanges.length - 1 ? blockRanges[currentIdx + 1] : null

    // Find the block that contains today's date (date-based, not AY-based)
    const today = format(new Date(), 'yyyy-MM-dd')
    const todayBlock = blockRanges.find((r) => r.startDate <= today && r.endDate >= today)

    return {
      currentBlockRange: current,
      previousBlockRange: previous,
      nextBlockRange: next,
      todayBlockRange: todayBlock ?? null,
    }
  }, [blockRanges, currentBlockNumber, startDate])

  // Navigate to previous block using actual block boundaries from API
  const handlePreviousBlock = () => {
    if (previousBlockRange) {
      const newStart = parseISO(previousBlockRange.startDate)
      const newEnd = parseISO(previousBlockRange.endDate)
      onDateRangeChange(newStart, newEnd)
    } else {
      // Fallback: move back 28 days if no previous block data
      const newStart = subDays(startDate, 28)
      const newEnd = subDays(endDate, 28)
      onDateRangeChange(newStart, newEnd)
    }
  }

  // Navigate to next block using actual block boundaries from API
  const handleNextBlock = () => {
    if (nextBlockRange) {
      const newStart = parseISO(nextBlockRange.startDate)
      const newEnd = parseISO(nextBlockRange.endDate)
      onDateRangeChange(newStart, newEnd)
    } else {
      // Fallback: move forward 28 days if no next block data
      const newStart = addDays(startDate, 28)
      const newEnd = addDays(endDate, 28)
      onDateRangeChange(newStart, newEnd)
    }
  }

  // Jump to today's block using actual block boundaries from API
  const handleToday = () => {
    if (todayBlockRange) {
      const newStart = parseISO(todayBlockRange.startDate)
      const newEnd = parseISO(todayBlockRange.endDate)
      onDateRangeChange(newStart, newEnd)
    } else {
      // Fallback: use today's date as start
      const today = new Date()
      onDateRangeChange(today, addDays(today, 27))
    }
  }

  // Jump to current block (same as Today if we're viewing a different range)
  const handleThisBlock = () => {
    handleToday()
  }

  // Show loading skeleton during initial fetch
  const isLoading = blocksLoading || rangesLoading

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
      {/* Block navigation buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={handlePreviousBlock}
          className="btn-secondary flex items-center gap-1"
          aria-label="Previous block"
          disabled={isLoading}
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          {isFallbackMode ? 'Previous' : 'Previous Block'}
        </button>

        <button
          onClick={handleNextBlock}
          className="btn-secondary flex items-center gap-1"
          aria-label="Next block"
          disabled={isLoading}
        >
          {isFallbackMode ? 'Next' : 'Next Block'}
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
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
          disabled={isLoading}
        >
          Today
        </button>
        {!isFallbackMode && (
          <button
            onClick={handleThisBlock}
            className="btn-secondary text-sm"
            aria-label="Jump to this block"
            disabled={isLoading}
          >
            This Block
          </button>
        )}
      </div>

      {/* Date range display (read-only - use navigation buttons to change) */}
      <div className="flex items-center gap-2 text-sm" role="status" aria-live="polite">
        {isLoading ? (
          <span className="font-medium text-gray-400 bg-gray-100 px-3 py-1 rounded animate-pulse">
            Loading...
          </span>
        ) : (
          <span className="font-medium text-gray-900 bg-gray-100 px-3 py-1 rounded">
            {currentBlockNumber !== null && !isFallbackMode ? `Block ${currentBlockNumber} (` : ''}
            {format(startDate, 'MMM d')} - {format(endDate, 'MMM d, yyyy')}
            {currentBlockNumber !== null && !isFallbackMode ? ')' : ''}
          </span>
        )}
      </div>

      {/* Current range display */}
      <div className="text-sm text-gray-600 ml-auto hidden lg:block">
        {format(startDate, 'MMM d, yyyy')} - {format(endDate, 'MMM d, yyyy')}
      </div>

      {/* Block 0 Warning Banner */}
      {currentBlockNumber === 0 && !isFallbackMode && (
        <div className="w-full mt-3 bg-amber-50 border-l-4 border-amber-400 p-3 text-sm rounded-r">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-amber-800">Block 0 (Orientation Period):</strong>
              <span className="text-amber-700 ml-1">
                Variable-length period at the start of the academic year. Duration computed for
                scheduling efficiency. Assignments during this period may differ from standard blocks.
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
