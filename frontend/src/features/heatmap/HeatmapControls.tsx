/**
 * Heatmap Controls Component
 *
 * Provides filtering and control UI for heatmap visualization,
 * including date range, person/rotation filters, grouping, and export.
 */

import React, { useState, useMemo, useCallback } from 'react';
import { format, startOfWeek, addDays, subDays, parseISO } from 'date-fns';
import { Calendar, Users, RotateCw, Download, Filter, X } from 'lucide-react';
import type { HeatmapFilters, HeatmapGroupBy, DateRange } from './types';
import { GROUP_BY_LABELS } from './types';

export interface HeatmapControlsProps {
  filters: HeatmapFilters;
  onFiltersChange: (filters: HeatmapFilters) => void;
  dateRange: DateRange;
  onDateRangeChange: (dateRange: DateRange) => void;
  availablePersons?: Array<{ id: string; name: string }>;
  availableRotations?: Array<{ id: string; name: string }>;
  onExport?: () => void;
  isLoading?: boolean;
}

export function HeatmapControls({
  filters,
  onFiltersChange,
  dateRange,
  onDateRangeChange,
  availablePersons = [],
  availableRotations = [],
  onExport,
  isLoading = false,
}: HeatmapControlsProps) {
  const [showFilters, setShowFilters] = useState(false);

  // Convert string dates to Date objects for display/navigation
  const startDateObj = useMemo(() => parseISO(dateRange.start), [dateRange.start]);
  const endDateObj = useMemo(() => parseISO(dateRange.end), [dateRange.end]);

  // Helper to validate Date objects
  const isValidDate = (d: Date): boolean => d instanceof Date && !isNaN(d.getTime());

  // Navigate to previous 4-week block
  const handlePreviousBlock = useCallback(() => {
    const newStart = subDays(startDateObj, 28);
    const newEnd = subDays(endDateObj, 28);
    onDateRangeChange({
      start: format(newStart, 'yyyy-MM-dd'),
      end: format(newEnd, 'yyyy-MM-dd'),
    });
  }, [startDateObj, endDateObj, onDateRangeChange]);

  // Navigate to next 4-week block
  const handleNextBlock = useCallback(() => {
    const newStart = addDays(startDateObj, 28);
    const newEnd = addDays(endDateObj, 28);
    onDateRangeChange({
      start: format(newStart, 'yyyy-MM-dd'),
      end: format(newEnd, 'yyyy-MM-dd'),
    });
  }, [startDateObj, endDateObj, onDateRangeChange]);

  // Jump to today's date (centered in a 4-week block)
  const handleToday = useCallback(() => {
    const today = new Date();
    const monday = startOfWeek(today, { weekStartsOn: 1 });
    onDateRangeChange({
      start: format(monday, 'yyyy-MM-dd'),
      end: format(addDays(monday, 27), 'yyyy-MM-dd'),
    });
  }, [onDateRangeChange]);

  // Jump to current 4-week block
  const handleThisBlock = useCallback(() => {
    const today = new Date();
    const monday = startOfWeek(today, { weekStartsOn: 1 });
    onDateRangeChange({
      start: format(monday, 'yyyy-MM-dd'),
      end: format(addDays(monday, 27), 'yyyy-MM-dd'),
    });
  }, [onDateRangeChange]);

  const handleDateRangeChange = (field: 'start' | 'end', value: string) => {
    onDateRangeChange({
      ...dateRange,
      [field]: value,
    });
  };

  const handlePersonSelect = (personId: string) => {
    const currentPersonIds = filters.person_ids || [];
    const newPersonIds = currentPersonIds.includes(personId)
      ? currentPersonIds.filter((id) => id !== personId)
      : [...currentPersonIds, personId];

    onFiltersChange({
      ...filters,
      person_ids: newPersonIds,
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

  const handleGroupByChange = (groupBy: HeatmapGroupBy) => {
    onFiltersChange({
      ...filters,
      group_by: groupBy,
    });
  };

  const handleIncludeFmitToggle = () => {
    onFiltersChange({
      ...filters,
      include_fmit: !filters.include_fmit,
    });
  };

  const clearFilters = () => {
    onFiltersChange({
      group_by: 'person',
      include_fmit: true,
    });
  };

  const activeFilterCount = [
    filters.person_ids?.length || 0,
    filters.rotation_ids?.length || 0,
  ].reduce((sum, count) => sum + count, 0);

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* Block navigation bar */}
      <div className="p-4 border-b border-gray-200">
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
              disabled={isLoading}
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
              disabled={isLoading}
            >
              Today
            </button>
            <button
              onClick={handleThisBlock}
              className="btn-secondary text-sm"
              aria-label="Jump to this block"
              disabled={isLoading}
            >
              This Block
            </button>
          </div>

          {/* Date range display (read-only) */}
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-600">Block:</span>
            <span className="font-medium text-gray-900 bg-gray-100 px-3 py-1 rounded">
              {isValidDate(startDateObj) && isValidDate(endDateObj)
                ? `${format(startDateObj, 'MMM d')} - ${format(endDateObj, 'MMM d, yyyy')}`
                : 'Select dates'}
            </span>
          </div>
        </div>
      </div>

      {/* Main controls bar */}
      <div className="p-4 flex flex-wrap gap-4 items-center">
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

        {/* Group by selector */}
        <div className="flex items-center gap-2">
          <RotateCw className="w-4 h-4 text-gray-500" />
          <label className="text-sm font-medium text-gray-700">Group by:</label>
          <select
            value={filters.group_by || 'person'}
            onChange={(e) => handleGroupByChange(e.target.value as HeatmapGroupBy)}
            className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          >
            {Object.entries(GROUP_BY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* Include FMIT toggle */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.include_fmit ?? true}
            onChange={handleIncludeFmitToggle}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            disabled={isLoading}
          />
          <span className="text-sm font-medium text-gray-700">Include FMIT</span>
        </label>

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

        {/* Export button */}
        {onExport && (
          <button
            onClick={onExport}
            className="flex items-center gap-2 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-colors"
            disabled={isLoading}
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        )}
      </div>

      {/* Expandable filters panel */}
      {showFilters && (
        <div className="px-4 pb-4 border-t border-gray-200">
          <div className="pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Person multi-select */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  People
                </label>
                {filters.person_ids && filters.person_ids.length > 0 && (
                  <button
                    onClick={() => onFiltersChange({ ...filters, person_ids: [] })}
                    className="text-xs text-blue-600 hover:text-blue-700"
                  >
                    Clear
                  </button>
                )}
              </div>
              <div className="border border-gray-300 rounded-md max-h-48 overflow-y-auto">
                {availablePersons.length === 0 ? (
                  <div className="p-3 text-sm text-gray-500">No people available</div>
                ) : (
                  availablePersons.map((person) => (
                    <label
                      key={person.id}
                      className="flex items-center gap-2 p-2 hover:bg-gray-50 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={filters.person_ids?.includes(person.id) || false}
                        onChange={() => handlePersonSelect(person.id)}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{person.name}</span>
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
            <div className="mt-4 flex justify-end">
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
      )}
    </div>
  );
}
