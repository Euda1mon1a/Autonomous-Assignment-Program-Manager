'use client'

import { useState } from 'react'
import { HeatmapView, HeatmapControls, HeatmapLegend, getDefaultDateRange } from '@/features/heatmap'
import type { HeatmapFilters, HeatmapViewMode, DateRange } from '@/features/heatmap'
import { ProtectedRoute } from '@/components/ProtectedRoute'

export default function HeatmapPage() {
  const defaultDateRange = getDefaultDateRange()
  const [dateRange, setDateRange] = useState<DateRange>(defaultDateRange)
  const [filters, setFilters] = useState<HeatmapFilters>({
    start_date: defaultDateRange.start,
    end_date: defaultDateRange.end,
    group_by: 'day',
  })
  const [viewMode, setViewMode] = useState<HeatmapViewMode>('coverage')

  // Sync date range changes to filters
  const handleDateRangeChange = (newDateRange: DateRange) => {
    setDateRange(newDateRange)
    setFilters(prev => ({
      ...prev,
      start_date: newDateRange.start,
      end_date: newDateRange.end,
    }))
  }

  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Schedule Heatmap</h1>
          <p className="text-gray-600">Visualize coverage and workload distribution</p>
        </div>

        <div className="space-y-6">
          {/* Controls */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <HeatmapControls
              filters={filters}
              onFiltersChange={setFilters}
              dateRange={dateRange}
              onDateRangeChange={handleDateRangeChange}
            />
          </div>

          {/* Heatmap Visualization */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <HeatmapView
              filters={filters}
              viewMode={viewMode}
            />
          </div>

          {/* Legend */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <HeatmapLegend viewMode={viewMode} />
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}
