/**
 * CallRoster Component - Example Usage
 *
 * This file demonstrates how to use the CallRoster component
 * to display on-call schedules with color-coded seniority levels.
 */

import { useState } from 'react'
import { CallRoster } from './CallRoster'
import { addDays, startOfWeek, endOfWeek } from 'date-fns'

/**
 * Example 1: Display current week's on-call roster
 */
export function CurrentWeekCallRoster() {
  const today = new Date()
  const weekStart = startOfWeek(today)
  const weekEnd = endOfWeek(today)

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">This Week's On-Call Roster</h1>
      <CallRoster
        startDate={weekStart}
        endDate={weekEnd}
        showOnlyOnCall={true}
      />
    </div>
  )
}

/**
 * Example 2: Display next 7 days with all assignments
 */
export function NextWeekCallRoster() {
  const today = new Date()
  const nextWeek = addDays(today, 7)

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Next 7 Days - All Assignments</h1>
      <CallRoster
        startDate={today}
        endDate={nextWeek}
        showOnlyOnCall={false} // Show all assignments, not just on-call
      />
    </div>
  )
}

/**
 * Example 3: Display custom date range
 */
export function CustomDateRangeRoster() {
  const startDate = new Date('2025-01-01')
  const endDate = new Date('2025-01-31')

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">January 2025 On-Call Roster</h1>
      <CallRoster
        startDate={startDate}
        endDate={endDate}
      />
    </div>
  )
}

/**
 * Example 4: Embedded in a page with user-controlled date picker
 */
export function InteractiveCallRoster() {
  const [startDate, setStartDate] = useState(new Date())
  const [endDate, setEndDate] = useState(addDays(new Date(), 30))

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold mb-2">On-Call Roster</h1>
        <p className="text-gray-600">Quick reference for nursing staff</p>
      </div>

      {/* Date range selector */}
      <div className="flex gap-4 items-center">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Start Date
          </label>
          <input
            type="date"
            value={startDate.toISOString().split('T')[0]}
            onChange={(e) => setStartDate(new Date(e.target.value))}
            className="border border-gray-300 rounded px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            End Date
          </label>
          <input
            type="date"
            value={endDate.toISOString().split('T')[0]}
            onChange={(e) => setEndDate(new Date(e.target.value))}
            className="border border-gray-300 rounded px-3 py-2"
          />
        </div>
      </div>

      {/* Call Roster */}
      <CallRoster
        startDate={startDate}
        endDate={endDate}
        showOnlyOnCall={true}
      />

      {/* Legend */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Color Coding Legend</h3>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-red-500"></div>
            <span>Red = Attending Physician</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-blue-500"></div>
            <span>Blue = Senior Resident (PGY-2+)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-green-500"></div>
            <span>Green = Intern (PGY-1)</span>
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Example 5: Mobile-friendly view for quick reference
 */
export function MobileCallRoster() {
  const today = new Date()
  const tomorrow = addDays(today, 1)

  return (
    <div className="max-w-md mx-auto p-4">
      <h2 className="text-xl font-bold mb-4">Who's On Call Today?</h2>
      <CallRoster
        startDate={today}
        endDate={tomorrow}
        showOnlyOnCall={true}
      />
    </div>
  )
}
