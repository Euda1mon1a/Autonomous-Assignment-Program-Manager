'use client'

import { useState, useCallback } from 'react'
import { startOfWeek, addDays } from 'date-fns'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { BlockNavigation } from '@/components/schedule/BlockNavigation'
import { ScheduleGrid } from '@/components/schedule/ScheduleGrid'

/**
 * Schedule Page - The core schedule viewing feature
 *
 * Displays the entire block schedule showing who is assigned where
 * on a half-day (AM/PM) basis. Default view is a 4-week block.
 *
 * Features:
 * - Grid layout with people as rows, days as columns with AM/PM sub-columns
 * - Color-coded rotation types for quick visual identification
 * - Sticky left column (person names) and top header (dates)
 * - Navigation: Previous/Next block, Today, This Block, date pickers
 * - People grouped by PGY level with visual separators
 */
export default function SchedulePage() {
  // Initialize to current 4-week block starting from Monday
  const getInitialDates = () => {
    const today = new Date()
    const monday = startOfWeek(today, { weekStartsOn: 1 })
    return {
      start: monday,
      end: addDays(monday, 27), // 28 days total (4 weeks)
    }
  }

  const [dateRange, setDateRange] = useState(getInitialDates)

  // Handler for date range changes from navigation
  const handleDateRangeChange = useCallback((start: Date, end: Date) => {
    setDateRange({ start, end })
  }, [])

  return (
    <ProtectedRoute>
      <div className="h-screen flex flex-col bg-gray-50">
        {/* Header with title and navigation */}
        <div className="flex-shrink-0 bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-full px-4 py-4">
            {/* Title row */}
            <div className="flex items-center justify-between mb-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Schedule</h1>
                <p className="text-sm text-gray-600 mt-1">
                  View and manage rotation assignments
                </p>
              </div>

              {/* Legend */}
              <div className="hidden xl:flex items-center gap-3 text-xs">
                <span className="text-gray-500 font-medium">Legend:</span>
                <span className="inline-flex items-center gap-1">
                  <span className="w-3 h-3 rounded bg-blue-100 border border-blue-300"></span>
                  Clinic
                </span>
                <span className="inline-flex items-center gap-1">
                  <span className="w-3 h-3 rounded bg-purple-100 border border-purple-300"></span>
                  Inpatient
                </span>
                <span className="inline-flex items-center gap-1">
                  <span className="w-3 h-3 rounded bg-red-100 border border-red-300"></span>
                  Procedure
                </span>
                <span className="inline-flex items-center gap-1">
                  <span className="w-3 h-3 rounded bg-orange-100 border border-orange-300"></span>
                  Call
                </span>
                <span className="inline-flex items-center gap-1">
                  <span className="w-3 h-3 rounded bg-green-100 border border-green-300"></span>
                  Elective
                </span>
                <span className="inline-flex items-center gap-1">
                  <span className="w-3 h-3 rounded bg-gray-100 border border-gray-300"></span>
                  Conference
                </span>
              </div>
            </div>

            {/* Navigation row */}
            <BlockNavigation
              startDate={dateRange.start}
              endDate={dateRange.end}
              onDateRangeChange={handleDateRangeChange}
            />
          </div>
        </div>

        {/* Schedule grid takes remaining space */}
        <div className="flex-1 overflow-auto p-4">
          <ScheduleGrid startDate={dateRange.start} endDate={dateRange.end} />
        </div>

        {/* Footer with keyboard shortcuts hint */}
        <div className="flex-shrink-0 bg-white border-t border-gray-200 px-4 py-2">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>
              Hover over assignments to see details. Click on a cell to view or
              edit.
            </span>
            <span className="hidden sm:inline">
              Showing {Math.ceil((dateRange.end.getTime() - dateRange.start.getTime()) / (1000 * 60 * 60 * 24)) + 1} days
            </span>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}
