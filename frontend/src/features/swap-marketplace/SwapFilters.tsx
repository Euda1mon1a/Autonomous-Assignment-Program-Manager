'use client';

/**
 * SwapFilters Component
 *
 * Provides filtering capabilities for the swap marketplace
 * including date range, status, swap type, and faculty filters.
 */

import { useState } from 'react';
import { format, subDays, startOfMonth, endOfMonth } from 'date-fns';
import {
  Filter,
  X,
  Calendar,
  ChevronDown,
  RotateCcw,
} from 'lucide-react';
import type {
  SwapFilters as Filters,
  SwapStatus,
  SwapType,
  DateRange,
} from './types';
import {
  SWAP_STATUS_LABELS,
  SWAP_TYPE_LABELS,
} from './types';

// ============================================================================
// Types
// ============================================================================

interface SwapFiltersProps {
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
  isLoading?: boolean;
}

interface QuickDateRange {
  label: string;
  getValue: () => DateRange;
}

// ============================================================================
// Constants
// ============================================================================

const STATUS_OPTIONS: SwapStatus[] = [
  'pending',
  'approved',
  'rejected',
  'executed',
  'cancelled',
];

const SWAP_TYPE_OPTIONS: SwapType[] = ['one_to_one', 'absorb'];

const QUICK_DATE_RANGES: QuickDateRange[] = [
  {
    label: 'Next 7 days',
    getValue: () => ({
      start: format(new Date(), 'yyyy-MM-dd'),
      end: format(subDays(new Date(), -7), 'yyyy-MM-dd'),
    }),
  },
  {
    label: 'Next 30 days',
    getValue: () => ({
      start: format(new Date(), 'yyyy-MM-dd'),
      end: format(subDays(new Date(), -30), 'yyyy-MM-dd'),
    }),
  },
  {
    label: 'This month',
    getValue: () => ({
      start: format(startOfMonth(new Date()), 'yyyy-MM-dd'),
      end: format(endOfMonth(new Date()), 'yyyy-MM-dd'),
    }),
  },
];

// ============================================================================
// Component
// ============================================================================

export function SwapFilters({ filters, onFiltersChange, isLoading }: SwapFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const hasActiveFilters =
    filters.dateRange ||
    (filters.statuses && filters.statuses.length > 0) ||
    (filters.swapTypes && filters.swapTypes.length > 0) ||
    filters.searchQuery ||
    filters.showMyPostingsOnly ||
    filters.showCompatibleOnly;

  const handleDateRangeChange = (range: DateRange | undefined) => {
    onFiltersChange({ ...filters, dateRange: range });
  };

  const handleStatusToggle = (status: SwapStatus) => {
    const currentStatuses = filters.statuses || [];
    const newStatuses = currentStatuses.includes(status)
      ? currentStatuses.filter((s) => s !== status)
      : [...currentStatuses, status];

    onFiltersChange({
      ...filters,
      statuses: newStatuses.length > 0 ? newStatuses : undefined,
    });
  };

  const handleSwapTypeToggle = (swapType: SwapType) => {
    const currentTypes = filters.swapTypes || [];
    const newTypes = currentTypes.includes(swapType)
      ? currentTypes.filter((t) => t !== swapType)
      : [...currentTypes, swapType];

    onFiltersChange({
      ...filters,
      swapTypes: newTypes.length > 0 ? newTypes : undefined,
    });
  };

  const handleSearchChange = (query: string) => {
    onFiltersChange({
      ...filters,
      searchQuery: query || undefined,
    });
  };

  const handleMyPostingsToggle = () => {
    onFiltersChange({
      ...filters,
      showMyPostingsOnly: !filters.showMyPostingsOnly,
    });
  };

  const handleCompatibleOnlyToggle = () => {
    onFiltersChange({
      ...filters,
      showCompatibleOnly: !filters.showCompatibleOnly,
    });
  };

  const handleReset = () => {
    onFiltersChange({});
    setIsExpanded(false);
  };

  const activeFilterCount = [
    filters.dateRange,
    filters.statuses?.length,
    filters.swapTypes?.length,
    filters.searchQuery,
    filters.showMyPostingsOnly,
    filters.showCompatibleOnly,
  ].filter(Boolean).length;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <Filter className="w-5 h-5 text-gray-500 flex-shrink-0" />
          <h3 className="text-base sm:text-lg font-semibold truncate">Filters</h3>
          {activeFilterCount > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs sm:text-sm font-medium rounded-full whitespace-nowrap">
              {activeFilterCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
          {hasActiveFilters && (
            <button
              onClick={handleReset}
              className="flex items-center gap-1 px-2 sm:px-3 py-1.5 text-xs sm:text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              disabled={isLoading}
              title="Reset all filters"
            >
              <RotateCcw className="w-3 h-3 sm:w-4 sm:h-4" />
              <span className="hidden sm:inline">Reset</span>
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 px-2 sm:px-3 py-1.5 text-xs sm:text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
            title={isExpanded ? 'Collapse filters' : 'Expand filters'}
          >
            <ChevronDown
              className={`w-3 h-3 sm:w-4 sm:h-4 transition-transform ${
                isExpanded ? 'rotate-180' : ''
              }`}
            />
            <span className="hidden sm:inline">{isExpanded ? 'Collapse' : 'Expand'}</span>
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by faculty name or reason..."
          value={filters.searchQuery || ''}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
      </div>

      {/* Quick toggles */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button
          onClick={handleMyPostingsToggle}
          className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
            filters.showMyPostingsOnly
              ? 'bg-blue-100 text-blue-700 border border-blue-300'
              : 'bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200'
          }`}
          disabled={isLoading}
        >
          My Postings Only
        </button>
        <button
          onClick={handleCompatibleOnlyToggle}
          className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
            filters.showCompatibleOnly
              ? 'bg-blue-100 text-blue-700 border border-blue-300'
              : 'bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200'
          }`}
          disabled={isLoading}
        >
          Compatible Only
        </button>
      </div>

      {/* Expanded Filters */}
      {isExpanded && (
        <div className="space-y-4 pt-4 border-t border-gray-200">
          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Calendar className="inline w-4 h-4 mr-1" />
              Date Range
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              {QUICK_DATE_RANGES.map((range) => (
                <button
                  key={range.label}
                  onClick={() => handleDateRangeChange(range.getValue())}
                  className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors"
                  disabled={isLoading}
                >
                  {range.label}
                </button>
              ))}
              {filters.dateRange && (
                <button
                  onClick={() => handleDateRangeChange(undefined)}
                  className="px-3 py-1.5 text-sm bg-red-50 text-red-700 border border-red-300 rounded-md hover:bg-red-100 transition-colors"
                  disabled={isLoading}
                >
                  <X className="inline w-3 h-3 mr-1" />
                  Clear
                </button>
              )}
            </div>
            {filters.dateRange && (
              <div className="text-sm text-gray-600">
                Selected: {filters.dateRange.start} to {filters.dateRange.end}
              </div>
            )}
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <div className="flex flex-wrap gap-2">
              {STATUS_OPTIONS.map((status) => (
                <button
                  key={status}
                  onClick={() => handleStatusToggle(status)}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    filters.statuses?.includes(status)
                      ? 'bg-blue-100 text-blue-700 border border-blue-300'
                      : 'bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200'
                  }`}
                  disabled={isLoading}
                >
                  {SWAP_STATUS_LABELS[status]}
                </button>
              ))}
            </div>
          </div>

          {/* Swap Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Swap Type
            </label>
            <div className="flex flex-wrap gap-2">
              {SWAP_TYPE_OPTIONS.map((swapType) => (
                <button
                  key={swapType}
                  onClick={() => handleSwapTypeToggle(swapType)}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    filters.swapTypes?.includes(swapType)
                      ? 'bg-blue-100 text-blue-700 border border-blue-300'
                      : 'bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200'
                  }`}
                  disabled={isLoading}
                >
                  {SWAP_TYPE_LABELS[swapType]}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
