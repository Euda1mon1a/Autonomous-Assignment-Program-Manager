/**
 * Timeline Controls Component
 *
 * Provides filtering and control UI for timeline visualization,
 * including date range, academic year, faculty/rotation filters,
 * and view mode toggles.
 */

import React, { useState } from 'react';
import {
  Calendar,
  Users,
  RotateCw,
  Filter,
  X,
  ChevronDown,
  Briefcase,
} from 'lucide-react';
import type {
  TimelineFilters,
  TimelineViewMode,
  DateRange,
  WorkloadStatus,
} from './types';
import {
  VIEW_MODE_LABELS,
  WORKLOAD_STATUS_LABELS,
} from './types';

export interface TimelineControlsProps {
  filters: TimelineFilters;
  onFiltersChange: (filters: TimelineFilters) => void;
  dateRange: DateRange;
  onDateRangeChange: (dateRange: DateRange) => void;
  viewMode: TimelineViewMode;
  onViewModeChange: (mode: TimelineViewMode) => void;
  availableFaculty?: Array<{ id: string; name: string; specialty: string }>;
  availableRotations?: Array<{ id: string; name: string }>;
  academicYears?: Array<{ id: string; label: string; start_date: string; end_date: string }>;
  selectedAcademicYear?: string | null;
  onAcademicYearChange?: (yearId: string | null) => void;
  isLoading?: boolean;
}

export function TimelineControls({
  filters,
  onFiltersChange,
  dateRange,
  onDateRangeChange,
  viewMode,
  onViewModeChange,
  availableFaculty = [],
  availableRotations = [],
  academicYears = [],
  selectedAcademicYear,
  onAcademicYearChange,
  isLoading = false,
}: TimelineControlsProps) {
  const [showFilters, setShowFilters] = useState(false);

  const handleDateRangeChange = (field: 'start' | 'end', value: string) => {
    onDateRangeChange({
      ...dateRange,
      [field]: value,
    });
  };

  const handleAcademicYearChange = (yearId: string) => {
    if (!onAcademicYearChange) return;

    if (yearId === '') {
      onAcademicYearChange(null);
      return;
    }

    const year = academicYears.find((y) => y.id === yearId);
    if (year) {
      onAcademicYearChange(yearId);
      onDateRangeChange({
        start: year.start_date,
        end: year.end_date,
      });
    }
  };

  const handleFacultySelect = (facultyId: string) => {
    const currentFacultyIds = filters.faculty_ids || [];
    const newFacultyIds = currentFacultyIds.includes(facultyId)
      ? currentFacultyIds.filter((id) => id !== facultyId)
      : [...currentFacultyIds, facultyId];

    onFiltersChange({
      ...filters,
      faculty_ids: newFacultyIds,
    });
  };

  const handleRotationSelect = (rotationId: string) => {
    const currentRotationIds = filters.rotation_ids || [];
    const newRotationIds = currentRotationIds.includes(rotationId)
      ? currentRotationIds.filter((id) => id !== rotationId)
      : [...currentRotationIds, rotationId];

    onFiltersChange({
      ...filters,
      rotation_ids: newRotationIds,
    });
  };

  const handleWorkloadStatusToggle = (status: WorkloadStatus) => {
    const currentStatuses = filters.workload_status || [];
    const newStatuses = currentStatuses.includes(status)
      ? currentStatuses.filter((s) => s !== status)
      : [...currentStatuses, status];

    onFiltersChange({
      ...filters,
      workload_status: newStatuses.length > 0 ? newStatuses : undefined,
    });
  };

  const clearFilters = () => {
    onFiltersChange({
      view_mode: viewMode,
    });
  };

  const activeFilterCount = [
    filters.faculty_ids?.length || 0,
    filters.rotation_ids?.length || 0,
    filters.workload_status?.length || 0,
  ].reduce((sum, count) => sum + count, 0);

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* Main controls bar */}
      <div className="p-4 flex flex-wrap gap-4 items-center">
        {/* Academic year selector */}
        {academicYears.length > 0 && onAcademicYearChange && (
          <div className="flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-gray-500" />
            <label className="text-sm font-medium text-gray-700">Academic Year:</label>
            <div className="relative">
              <select
                value={selectedAcademicYear || ''}
                onChange={(e) => handleAcademicYearChange(e.target.value)}
                className="pl-3 pr-8 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none bg-white"
                disabled={isLoading}
              >
                <option value="">Custom Range</option>
                {academicYears.map((year) => (
                  <option key={year.id} value={year.id}>
                    {year.label}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
          </div>
        )}

        {/* Date range picker */}
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-500" />
          <label className="text-sm font-medium text-gray-700">From:</label>
          <input
            type="date"
            value={dateRange.start}
            onChange={(e) => handleDateRangeChange('start', e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <label className="text-sm font-medium text-gray-700">To:</label>
          <input
            type="date"
            value={dateRange.end}
            onChange={(e) => handleDateRangeChange('end', e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
        </div>

        {/* View mode toggle */}
        <div className="flex items-center gap-2">
          <RotateCw className="w-4 h-4 text-gray-500" />
          <label className="text-sm font-medium text-gray-700">View:</label>
          <div className="flex rounded-md shadow-sm">
            {(Object.keys(VIEW_MODE_LABELS) as TimelineViewMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => onViewModeChange(mode)}
                className={`px-3 py-1.5 text-sm font-medium transition-colors first:rounded-l-md last:rounded-r-md border ${
                  viewMode === mode
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
                disabled={isLoading}
              >
                {VIEW_MODE_LABELS[mode].replace(' View', '')}
              </button>
            ))}
          </div>
        </div>

        {/* Filters toggle button */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="ml-auto flex items-center gap-2 px-4 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md text-sm font-medium transition-colors"
          disabled={isLoading}
        >
          <Filter className="w-4 h-4" />
          Filters
          {activeFilterCount > 0 && (
            <span className="px-2 py-0.5 bg-blue-600 text-white text-xs rounded-full">
              {activeFilterCount}
            </span>
          )}
        </button>
      </div>

      {/* Expandable filters panel */}
      {showFilters && (
        <div className="px-4 pb-4 border-t border-gray-200">
          <div className="pt-4 space-y-4">
            {/* Workload status filters */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Workload Status
              </label>
              <div className="flex flex-wrap gap-2">
                {(Object.entries(WORKLOAD_STATUS_LABELS) as [WorkloadStatus, string][]).map(
                  ([status, label]) => (
                    <button
                      key={status}
                      onClick={() => handleWorkloadStatusToggle(status)}
                      className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors border ${
                        filters.workload_status?.includes(status)
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {label}
                    </button>
                  )
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Faculty multi-select */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    Faculty
                  </label>
                  {filters.faculty_ids && filters.faculty_ids.length > 0 && (
                    <button
                      onClick={() => onFiltersChange({ ...filters, faculty_ids: [] })}
                      className="text-xs text-blue-600 hover:text-blue-700"
                    >
                      Clear
                    </button>
                  )}
                </div>
                <div className="border border-gray-300 rounded-md max-h-48 overflow-y-auto">
                  {availableFaculty.length === 0 ? (
                    <div className="p-3 text-sm text-gray-500">No faculty available</div>
                  ) : (
                    availableFaculty.map((faculty) => (
                      <label
                        key={faculty.id}
                        className="flex items-center gap-2 p-2 hover:bg-gray-50 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={filters.faculty_ids?.includes(faculty.id) || false}
                          onChange={() => handleFacultySelect(faculty.id)}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <div className="flex-1 min-w-0">
                          <span className="text-sm text-gray-700 block truncate">
                            {faculty.name}
                          </span>
                          <span className="text-xs text-gray-500 block truncate">
                            {faculty.specialty}
                          </span>
                        </div>
                      </label>
                    ))
                  )}
                </div>
              </div>

              {/* Rotation multi-select */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <RotateCw className="w-4 h-4" />
                    Rotations
                  </label>
                  {filters.rotation_ids && filters.rotation_ids.length > 0 && (
                    <button
                      onClick={() => onFiltersChange({ ...filters, rotation_ids: [] })}
                      className="text-xs text-blue-600 hover:text-blue-700"
                    >
                      Clear
                    </button>
                  )}
                </div>
                <div className="border border-gray-300 rounded-md max-h-48 overflow-y-auto">
                  {availableRotations.length === 0 ? (
                    <div className="p-3 text-sm text-gray-500">No rotations available</div>
                  ) : (
                    availableRotations.map((rotation) => (
                      <label
                        key={rotation.id}
                        className="flex items-center gap-2 p-2 hover:bg-gray-50 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={filters.rotation_ids?.includes(rotation.id) || false}
                          onChange={() => handleRotationSelect(rotation.id)}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">{rotation.name}</span>
                      </label>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Clear all filters */}
            {activeFilterCount > 0 && (
              <div className="flex justify-end pt-2">
                <button
                  onClick={clearFilters}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800"
                >
                  <X className="w-4 h-4" />
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
