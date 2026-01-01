'use client'

import { useMemo, useCallback } from 'react'
import { format, parseISO } from 'date-fns'
import { useBlockRanges, BlockRange } from '@/hooks/useBlocks'

interface BlockNavigationProps {
  startDate: Date
  endDate: Date
  onDateRangeChange: (start: Date, end: Date) => void
}

/**
 * Navigation controls for the schedule grid
 * Provides Previous/Next block buttons, Today, This Block, and date pickers
 *
 * Uses actual block dates from the database via useBlockRanges hook
 * instead of hardcoded 28-day calculations.
 */
export function BlockNavigation({
  startDate,
  endDate,
  onDateRangeChange,
}: BlockNavigationProps) {
  // Fetch actual block ranges from the database
  const { data: blockRanges, isLoading } = useBlockRanges()

  // Find current block based on the startDate
  const currentBlockInfo = useMemo(() => {
    if (!blockRanges || blockRanges.length === 0) {
      return null
    }

    const startDateStr = format(startDate, 'yyyy-MM-dd')

    // Find the block that contains the current startDate
    const matchingBlock = blockRanges.find(
      (range) => range.start_date <= startDateStr && startDateStr <= range.end_date
    )

    if (matchingBlock) {
      return matchingBlock
    }

    // If no exact match, find the closest block by start_date
    const closestBlock = blockRanges.reduce((closest, range) => {
      const rangeStart = parseISO(range.start_date)
      const closestStart = parseISO(closest.start_date)
      const startDiff = Math.abs(rangeStart.getTime() - startDate.getTime())
      const closestDiff = Math.abs(closestStart.getTime() - startDate.getTime())
      return startDiff < closestDiff ? range : closest
    }, blockRanges[0])

    return closestBlock
  }, [blockRanges, startDate])

  // Find adjacent blocks for navigation
  const { previousBlock, nextBlock } = useMemo(() => {
    if (!blockRanges || !currentBlockInfo) {
      return { previousBlock: null, nextBlock: null }
    }

    const currentIndex = blockRanges.findIndex(
      (range) => range.block_number === currentBlockInfo.block_number
    )

    return {
      previousBlock: currentIndex > 0 ? blockRanges[currentIndex - 1] : null,
      nextBlock: currentIndex < blockRanges.length - 1 ? blockRanges[currentIndex + 1] : null,
    }
  }, [blockRanges, currentBlockInfo])

  // Navigate to a specific block
  const navigateToBlock = useCallback(
    (block: BlockRange) => {
      const newStart = parseISO(block.start_date)
      const newEnd = parseISO(block.end_date)
      onDateRangeChange(newStart, newEnd)
    },
    [onDateRangeChange]
  )

  // Navigate to previous block
  const handlePreviousBlock = useCallback(() => {
    if (previousBlock) {
      navigateToBlock(previousBlock)
    }
  }, [previousBlock, navigateToBlock])

  // Navigate to next block
  const handleNextBlock = useCallback(() => {
    if (nextBlock) {
      navigateToBlock(nextBlock)
    }
  }, [nextBlock, navigateToBlock])

  // Find and jump to today's block
  const handleToday = useCallback(() => {
    if (!blockRanges || blockRanges.length === 0) return

    const todayStr = format(new Date(), 'yyyy-MM-dd')

    // Find the block that contains today
    const todaysBlock = blockRanges.find(
      (range) => range.start_date <= todayStr && todayStr <= range.end_date
    )

    if (todaysBlock) {
      navigateToBlock(todaysBlock)
    } else {
      // If today is not in any block, find the closest upcoming block
      const upcomingBlock = blockRanges.find((range) => range.start_date > todayStr)
      if (upcomingBlock) {
        navigateToBlock(upcomingBlock)
      } else {
        // Fall back to the last block
        navigateToBlock(blockRanges[blockRanges.length - 1])
      }
    }
  }, [blockRanges, navigateToBlock])

  // Jump to current block (same as today)
  const handleThisBlock = handleToday

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center gap-4 animate-pulse">
        <div className="h-9 w-32 bg-gray-200 rounded"></div>
        <div className="h-9 w-28 bg-gray-200 rounded"></div>
        <div className="h-6 w-48 bg-gray-200 rounded"></div>
      </div>
    )
  }

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
      {/* Block number display - prominent and clear */}
      {currentBlockInfo && (
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold text-blue-600">
            Block {currentBlockInfo.block_number}
          </span>
        </div>
      )}

      {/* Block navigation buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={handlePreviousBlock}
          disabled={!previousBlock}
          className="btn-secondary flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
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
          Previous
        </button>

        <button
          onClick={handleNextBlock}
          disabled={!nextBlock}
          className="btn-secondary flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Next block"
        >
          Next
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
          aria-label="Jump to today's block"
        >
          Today
        </button>
        <button
          onClick={handleThisBlock}
          className="btn-secondary text-sm"
          aria-label="Jump to current block"
        >
          This Block
        </button>
      </div>

      {/* Date range display - shows actual dates from database */}
      <div className="flex items-center gap-2 text-sm">
        <span className="font-medium text-gray-900 bg-gray-100 px-3 py-1 rounded">
          {format(startDate, 'MMM d')} - {format(endDate, 'MMM d, yyyy')}
        </span>
      </div>

      {/* Full date range display */}
      <div className="text-sm text-gray-600 ml-auto hidden lg:block">
        {format(startDate, 'MMM d, yyyy')} - {format(endDate, 'MMM d, yyyy')}
      </div>
    </div>
  )
}
