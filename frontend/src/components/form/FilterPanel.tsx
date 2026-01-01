'use client';

import React, { useState } from 'react';
import { Filter, X, ChevronDown } from 'lucide-react';
import { Button } from '../ui/Button';

export type FilterValue = string | string[] | boolean | { start: string; end: string } | null | undefined;

export interface FilterOption {
  key: string;
  label: string;
  type: 'select' | 'multiselect' | 'daterange' | 'checkbox';
  options?: Array<{ label: string; value: string }>;
  value?: FilterValue;
}

export interface FilterPanelProps {
  filters: FilterOption[];
  onFilterChange: (key: string, value: FilterValue) => void;
  onClearAll: () => void;
  activeFiltersCount?: number;
  collapsible?: boolean;
  className?: string;
}

/**
 * FilterPanel component for advanced filtering
 *
 * @example
 * ```tsx
 * <FilterPanel
 *   filters={[
 *     {
 *       key: 'role',
 *       label: 'Role',
 *       type: 'select',
 *       options: [
 *         { label: 'Resident', value: 'resident' },
 *         { label: 'Faculty', value: 'faculty' },
 *       ],
 *     },
 *   ]}
 *   onFilterChange={(key, value) => updateFilter(key, value)}
 *   onClearAll={() => clearFilters()}
 * />
 * ```
 */
export function FilterPanel({
  filters,
  onFilterChange,
  onClearAll,
  activeFiltersCount = 0,
  collapsible = true,
  className = '',
}: FilterPanelProps) {
  const [isExpanded, setIsExpanded] = useState(!collapsible);

  return (
    <div
      role="search"
      aria-label="Filter options"
      className={`bg-white border border-gray-200 rounded-lg ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-gray-600" />
          <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
          {activeFiltersCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
              {activeFiltersCount}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {activeFiltersCount > 0 && (
            <button
              onClick={onClearAll}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Clear all
            </button>
          )}

          {collapsible && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <ChevronDown
                className={`w-5 h-5 text-gray-400 transition-transform ${
                  isExpanded ? 'rotate-180' : ''
                }`}
              />
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      {isExpanded && (
        <div className="p-4 space-y-4">
          {filters.map((filter) => (
            <div key={filter.key}>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {filter.label}
              </label>

              {filter.type === 'select' && filter.options && (
                <select
                  value={typeof filter.value === 'string' ? filter.value : ''}
                  onChange={(e) => onFilterChange(filter.key, e.target.value)}
                  aria-label={filter.label}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All</option>
                  {filter.options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              )}

              {filter.type === 'checkbox' && (
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filter.value || false}
                    onChange={(e) => onFilterChange(filter.key, e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">{filter.label}</span>
                </label>
              )}

              {/* Add more filter type implementations as needed */}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Compact filter chips display
 */
export function ActiveFilters({
  filters,
  onRemove,
  className = '',
}: {
  filters: Array<{ key: string; label: string; value: string }>;
  onRemove: (key: string) => void;
  className?: string;
}) {
  if (filters.length === 0) return null;

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {filters.map((filter) => (
        <div
          key={filter.key}
          className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
        >
          <span className="font-medium">{filter.label}:</span>
          <span>{filter.value}</span>
          <button
            onClick={() => onRemove(filter.key)}
            className="ml-1 hover:bg-blue-200 rounded-full p-0.5"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      ))}
    </div>
  );
}
