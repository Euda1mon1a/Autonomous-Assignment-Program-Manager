/**
 * FMIT Timeline Component
 *
 * Main Gantt-style timeline visualization showing faculty assignments
 * and workload distribution over time.
 */

'use client';

import React, { useState, useMemo } from 'react';
import { Loader2, AlertCircle, Calendar, TrendingUp, Users, Clock } from 'lucide-react';
import { TimelineControls } from './TimelineControls';
import { TimelineRow, AssignmentTooltip } from './TimelineRow';
import {
  useFMITTimeline,
  useTimelineMetrics,
  useAvailableFaculty,
  useAvailableRotations,
  useAcademicYears,
} from './hooks';
import type {
  TimelineViewMode,
  TimelineFilters,
  DateRange,
  AssignmentTooltipData,
} from './types';
import {
  getDefaultDateRange,
  getWeeksInRange,
  getMonthsInRange,
  getQuartersInRange,
} from './types';

export interface FMITTimelineProps {
  initialDateRange?: DateRange;
  initialViewMode?: TimelineViewMode;
  initialFilters?: TimelineFilters;
  height?: string | number;
}

export function FMITTimeline({
  initialDateRange,
  initialViewMode = 'monthly',
  initialFilters = {},
  height = '800px',
}: FMITTimelineProps) {
  // State
  const [dateRange, setDateRange] = useState<DateRange>(
    initialDateRange || getDefaultDateRange()
  );
  const [viewMode, setViewMode] = useState<TimelineViewMode>(initialViewMode);
  const [filters, setFilters] = useState<TimelineFilters>(initialFilters);
  const [hoveredAssignment, setHoveredAssignment] = useState<AssignmentTooltipData | null>(null);
  const [selectedAcademicYear, setSelectedAcademicYear] = useState<string | null>(null);

  // Fetch data
  const {
    data: timelineData,
    isLoading: isTimelineLoading,
    error: timelineError,
  } = useFMITTimeline({
    ...filters,
    startDate: dateRange.start,
    endDate: dateRange.end,
    viewMode: viewMode,
  });

  const { data: metrics, isLoading: isMetricsLoading } = useTimelineMetrics(dateRange);

  const { data: availableFaculty } = useAvailableFaculty();
  const { data: availableRotations } = useAvailableRotations();
  const { data: academicYears } = useAcademicYears();

  // Calculate time periods for timeline header
  const timePeriods = useMemo(() => {
    if (!dateRange.start || !dateRange.end) return [];

    switch (viewMode) {
      case 'weekly':
        return getWeeksInRange(dateRange.start, dateRange.end);
      case 'monthly':
        return getMonthsInRange(dateRange.start, dateRange.end);
      case 'quarterly':
        return getQuartersInRange(dateRange.start, dateRange.end);
      default:
        return [];
    }
  }, [dateRange, viewMode]);

  // Loading state
  if (isTimelineLoading) {
    return (
      <div className="space-y-4">
        <TimelineControls
          filters={filters}
          onFiltersChange={setFilters}
          dateRange={dateRange}
          onDateRangeChange={setDateRange}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          availableFaculty={availableFaculty}
          availableRotations={availableRotations}
          academicYears={academicYears}
          selectedAcademicYear={selectedAcademicYear}
          onAcademicYearChange={setSelectedAcademicYear}
          isLoading={true}
        />
        <div
          className="flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200"
          style={{ height }}
        >
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
            <p className="text-sm text-gray-600">Loading timeline...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (timelineError) {
    return (
      <div className="space-y-4">
        <TimelineControls
          filters={filters}
          onFiltersChange={setFilters}
          dateRange={dateRange}
          onDateRangeChange={setDateRange}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          availableFaculty={availableFaculty}
          availableRotations={availableRotations}
          academicYears={academicYears}
          selectedAcademicYear={selectedAcademicYear}
          onAcademicYearChange={setSelectedAcademicYear}
        />
        <div
          className="flex items-center justify-center bg-red-50 rounded-lg border border-red-200"
          style={{ height }}
        >
          <div className="flex flex-col items-center gap-3 p-6 text-center">
            <AlertCircle className="w-8 h-8 text-red-600" />
            <div>
              <p className="text-sm font-medium text-red-900">Failed to load timeline</p>
              <p className="text-sm text-red-700 mt-1">{timelineError.message}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Empty state
  if (!timelineData?.timeline?.facultyRows || timelineData.timeline.facultyRows.length === 0) {
    return (
      <div className="space-y-4">
        <TimelineControls
          filters={filters}
          onFiltersChange={setFilters}
          dateRange={dateRange}
          onDateRangeChange={setDateRange}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          availableFaculty={availableFaculty}
          availableRotations={availableRotations}
          academicYears={academicYears}
          selectedAcademicYear={selectedAcademicYear}
          onAcademicYearChange={setSelectedAcademicYear}
        />
        <div
          className="flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200"
          style={{ height }}
        >
          <div className="flex flex-col items-center gap-3 p-6 text-center">
            <Calendar className="w-8 h-8 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-900">No faculty assignments found</p>
              <p className="text-sm text-gray-600 mt-1">
                Adjust your filters or date range to view timeline data
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <TimelineControls
        filters={filters}
        onFiltersChange={setFilters}
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        availableFaculty={availableFaculty}
        availableRotations={availableRotations}
        academicYears={academicYears}
        selectedAcademicYear={selectedAcademicYear}
        onAcademicYearChange={setSelectedAcademicYear}
        isLoading={isTimelineLoading}
      />

      {/* Metrics Summary */}
      {metrics && !isMetricsLoading && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <MetricCard
            icon={<Users className="w-4 h-4" />}
            label="Total Faculty"
            value={metrics.totalFaculty}
            color="blue"
          />
          <MetricCard
            icon={<Calendar className="w-4 h-4" />}
            label="Assignments"
            value={metrics.totalAssignments}
            color="purple"
          />
          <MetricCard
            icon={<TrendingUp className="w-4 h-4" />}
            label="Avg Utilization"
            value={`${metrics.averageUtilization}%`}
            color="green"
          />
          <MetricCard
            icon={<AlertCircle className="w-4 h-4" />}
            label="Overloaded"
            value={metrics.overloadedFaculty}
            color="red"
          />
          <MetricCard
            icon={<Clock className="w-4 h-4" />}
            label="Underutilized"
            value={metrics.underutilizedFaculty}
            color="yellow"
          />
          <MetricCard
            icon={<Clock className="w-4 h-4" />}
            label="Total Hours"
            value={metrics.totalHoursScheduled}
            color="cyan"
          />
        </div>
      )}

      {/* Timeline */}
      <div
        className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden"
        style={{ height }}
      >
        <div className="h-full overflow-auto">
          {/* Timeline header */}
          <div className="flex sticky top-0 z-20 bg-gray-50 border-b border-gray-200">
            {/* Faculty column header */}
            <div className="w-64 flex-shrink-0 p-3 border-r border-gray-200 bg-gray-100 sticky left-0 z-30">
              <h3 className="text-sm font-semibold text-gray-900">Faculty</h3>
              <p className="text-xs text-gray-500 mt-0.5">
                {timelineData.timeline.facultyRows.length} members
              </p>
            </div>

            {/* Time periods header */}
            <div className="flex-1 flex">
              {timePeriods.map((period, index) => (
                <div
                  key={index}
                  className={`flex-1 p-3 border-r border-gray-200 text-center ${
                    period.isCurrent ? 'bg-blue-100' : 'bg-gray-50'
                  }`}
                >
                  <div className="text-xs font-medium text-gray-900">{period.label}</div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {new Date(period.startDate).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Faculty rows */}
          <div>
            {timelineData.timeline.facultyRows.map((row) => (
              <TimelineRow
                key={row.facultyId}
                row={row}
                periods={timePeriods}
                onAssignmentHover={setHoveredAssignment}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Assignment tooltip */}
      {hoveredAssignment && <AssignmentTooltip data={hoveredAssignment} />}
    </div>
  );
}

/**
 * Metric Card Component
 */
interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: 'blue' | 'purple' | 'green' | 'red' | 'yellow' | 'cyan';
}

function MetricCard({ icon, label, value, color }: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    purple: 'bg-purple-100 text-purple-600',
    green: 'bg-green-100 text-green-600',
    red: 'bg-red-100 text-red-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    cyan: 'bg-cyan-100 text-cyan-600',
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-2">
        <div className={`p-1.5 rounded ${colorClasses[color]}`}>{icon}</div>
        <span className="text-xs font-medium text-gray-600">{label}</span>
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
    </div>
  );
}

/**
 * Skeleton loader for timeline
 */
export function FMITTimelineSkeleton({ height = '800px' }: { height?: string | number }) {
  return (
    <div className="space-y-4">
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 animate-pulse">
        <div className="h-10 bg-gray-200 rounded w-full" />
      </div>
      <div
        className="bg-gray-50 rounded-lg border border-gray-200 animate-pulse"
        style={{ height }}
      >
        <div className="p-6 space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/4" />
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex gap-4">
              <div className="h-20 bg-gray-200 rounded w-48" />
              <div className="flex-1 h-20 bg-gray-200 rounded" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
