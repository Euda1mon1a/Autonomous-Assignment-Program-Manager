'use client';

/**
 * AuditLogFilters Component
 *
 * Provides comprehensive filtering and search capabilities
 * for the audit log viewer including date range, entity types,
 * actions, users, and severity levels.
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { format, subDays, startOfMonth, endOfMonth, subMonths } from 'date-fns';
import {
  Search,
  Filter,
  X,
  Calendar,
  User,
  Activity,
  AlertTriangle,
  ChevronDown,
  RotateCcw,
} from 'lucide-react';
import type {
  AuditLogFilters as AuditFilters,
  AuditEntityType,
  AuditActionType,
  AuditSeverity,
  DateRange,
} from './types';
import {
  ENTITY_TYPE_LABELS,
  ACTION_TYPE_LABELS,
} from './types';

// ============================================================================
// Types
// ============================================================================

interface AuditLogFiltersProps {
  filters: AuditFilters;
  onFiltersChange: (filters: AuditFilters) => void;
  users?: Array<{ id: string; name: string }>;
  isLoading?: boolean;
}

interface QuickDateRange {
  label: string;
  getValue: () => DateRange;
}

// ============================================================================
// Constants
// ============================================================================

const ENTITY_TYPES: AuditEntityType[] = [
  'assignment',
  'person',
  'absence',
  'rotation_template',
  'schedule_run',
  'block',
  'system',
];

const ACTION_TYPES: AuditActionType[] = [
  'create',
  'update',
  'delete',
  'override',
  'restore',
  'bulk_import',
  'bulk_delete',
  'schedule_generate',
  'schedule_validate',
  'login',
  'logout',
  'export',
];

const SEVERITY_LEVELS: AuditSeverity[] = ['info', 'warning', 'critical'];

const QUICK_DATE_RANGES: QuickDateRange[] = [
  {
    label: 'Today',
    getValue: () => {
      const today = format(new Date(), 'yyyy-MM-dd');
      return { start: today, end: today };
    },
  },
  {
    label: 'Last 7 days',
    getValue: () => ({
      start: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd'),
    }),
  },
  {
    label: 'Last 30 days',
    getValue: () => ({
      start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd'),
    }),
  },
  {
    label: 'This month',
    getValue: () => ({
      start: format(startOfMonth(new Date()), 'yyyy-MM-dd'),
      end: format(endOfMonth(new Date()), 'yyyy-MM-dd'),
    }),
  },
  {
    label: 'Last month',
    getValue: () => {
      const lastMonth = subMonths(new Date(), 1);
      return {
        start: format(startOfMonth(lastMonth), 'yyyy-MM-dd'),
        end: format(endOfMonth(lastMonth), 'yyyy-MM-dd'),
      };
    },
  },
  {
    label: 'Last 90 days',
    getValue: () => ({
      start: format(subDays(new Date(), 90), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd'),
    }),
  },
];

// ============================================================================
// Helper Components
// ============================================================================

/**
 * Dropdown multi-select component
 */
function MultiSelect<T extends string>({
  label,
  options,
  selected,
  onChange,
  getLabel,
  icon: Icon,
}: {
  label: string;
  options: T[];
  selected: T[];
  onChange: (selected: T[]) => void;
  getLabel: (value: T) => string;
  icon?: React.ComponentType<{ className?: string }>;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleOption = (option: T) => {
    if (selected.includes(option)) {
      onChange(selected.filter((s) => s !== option));
    } else {
      onChange([...selected, option]);
    }
  };

  const selectAll = () => onChange([...options]);
  const clearAll = () => onChange([]);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center gap-2 px-3 py-2 border rounded-lg text-sm
          hover:bg-gray-50 transition-colors
          ${selected.length > 0 ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
        `}
      >
        {Icon && <Icon className="w-4 h-4 text-gray-500" />}
        <span className="text-gray-700">{label}</span>
        {selected.length > 0 && (
          <span className="bg-blue-600 text-white text-xs px-1.5 py-0.5 rounded-full">
            {selected.length}
          </span>
        )}
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-20 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg">
          <div className="p-2 border-b border-gray-100 flex justify-between">
            <button
              type="button"
              onClick={selectAll}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              Select all
            </button>
            <button
              type="button"
              onClick={clearAll}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              Clear all
            </button>
          </div>
          <div className="max-h-60 overflow-y-auto p-2 space-y-1">
            {options.map((option) => (
              <label
                key={option}
                className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-50 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selected.includes(option)}
                  onChange={() => toggleOption(option)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">{getLabel(option)}</span>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Date range picker component
 */
function DateRangePicker({
  dateRange,
  onChange,
}: {
  dateRange?: DateRange;
  onChange: (range?: DateRange) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleQuickSelect = (range: QuickDateRange) => {
    onChange(range.getValue());
    setIsOpen(false);
  };

  const displayValue = dateRange
    ? `${format(new Date(dateRange.start), 'MMM d, yyyy')} - ${format(new Date(dateRange.end), 'MMM d, yyyy')}`
    : 'All time';

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center gap-2 px-3 py-2 border rounded-lg text-sm
          hover:bg-gray-50 transition-colors
          ${dateRange ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
        `}
      >
        <Calendar className="w-4 h-4 text-gray-500" />
        <span className="text-gray-700">{displayValue}</span>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-20 mt-1 w-80 bg-white border border-gray-200 rounded-lg shadow-lg p-4">
          <div className="space-y-3">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Quick Select
            </div>
            <div className="grid grid-cols-2 gap-2">
              {QUICK_DATE_RANGES.map((range) => (
                <button
                  key={range.label}
                  type="button"
                  onClick={() => handleQuickSelect(range)}
                  className="px-3 py-1.5 text-sm text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
                >
                  {range.label}
                </button>
              ))}
            </div>

            <div className="border-t border-gray-200 pt-3">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Custom Range
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Start</label>
                  <input
                    type="date"
                    value={dateRange?.start || ''}
                    onChange={(e) =>
                      onChange({
                        start: e.target.value,
                        end: dateRange?.end || e.target.value,
                      })
                    }
                    className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">End</label>
                  <input
                    type="date"
                    value={dateRange?.end || ''}
                    onChange={(e) =>
                      onChange({
                        start: dateRange?.start || e.target.value,
                        end: e.target.value,
                      })
                    }
                    className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            {dateRange && (
              <button
                type="button"
                onClick={() => {
                  onChange(undefined);
                  setIsOpen(false);
                }}
                className="w-full mt-2 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded transition-colors"
              >
                Clear date range
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Filter tag component
 */
function FilterTag({
  label,
  onRemove,
}: {
  label: string;
  onRemove: () => void;
}) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
      {label}
      <button
        type="button"
        onClick={onRemove}
        className="hover:bg-blue-200 rounded-full p-0.5"
        aria-label={`Remove ${label} filter`}
      >
        <X className="w-3 h-3" />
      </button>
    </span>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function AuditLogFilters({
  filters,
  onFiltersChange,
  users = [],
  isLoading = false,
}: AuditLogFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.searchQuery || '');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Debounced search
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (searchInput !== filters.searchQuery) {
        onFiltersChange({ ...filters, searchQuery: searchInput || undefined });
      }
    }, 300);
    return () => clearTimeout(timeout);
  }, [searchInput, filters, onFiltersChange]);

  const updateFilters = useCallback(
    (updates: Partial<AuditFilters>) => {
      onFiltersChange({ ...filters, ...updates });
    },
    [filters, onFiltersChange]
  );

  const clearAllFilters = useCallback(() => {
    setSearchInput('');
    onFiltersChange({});
  }, [onFiltersChange]);

  // Count active filters
  const activeFilterCount =
    (filters.dateRange ? 1 : 0) +
    (filters.entityTypes?.length || 0) +
    (filters.actions?.length || 0) +
    (filters.userIds?.length || 0) +
    (filters.severity?.length || 0) +
    (filters.searchQuery ? 1 : 0) +
    (filters.acgmeOverridesOnly ? 1 : 0);

  // Build active filter tags
  const filterTags: Array<{ label: string; onRemove: () => void }> = [];

  if (filters.dateRange) {
    filterTags.push({
      label: `Date: ${format(new Date(filters.dateRange.start), 'MMM d')} - ${format(new Date(filters.dateRange.end), 'MMM d')}`,
      onRemove: () => updateFilters({ dateRange: undefined }),
    });
  }

  filters.entityTypes?.forEach((type) => {
    filterTags.push({
      label: ENTITY_TYPE_LABELS[type],
      onRemove: () =>
        updateFilters({
          entityTypes: filters.entityTypes?.filter((t) => t !== type),
        }),
    });
  });

  filters.actions?.forEach((action) => {
    filterTags.push({
      label: ACTION_TYPE_LABELS[action],
      onRemove: () =>
        updateFilters({
          actions: filters.actions?.filter((a) => a !== action),
        }),
    });
  });

  filters.severity?.forEach((sev) => {
    filterTags.push({
      label: `Severity: ${sev}`,
      onRemove: () =>
        updateFilters({
          severity: filters.severity?.filter((s) => s !== sev),
        }),
    });
  });

  if (filters.acgmeOverridesOnly) {
    filterTags.push({
      label: 'ACGME Overrides Only',
      onRemove: () => updateFilters({ acgmeOverridesOnly: false }),
    });
  }

  return (
    <div className="bg-white rounded-lg shadow p-4 space-y-4">
      {/* Search bar */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search audit logs by entity name, reason, or user..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {searchInput && (
            <button
              type="button"
              onClick={() => setSearchInput('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className={`
            flex items-center gap-2 px-4 py-2 border rounded-lg text-sm transition-colors
            ${showAdvanced ? 'bg-gray-100 border-gray-400' : 'border-gray-300 hover:bg-gray-50'}
          `}
        >
          <Filter className="w-4 h-4" />
          Filters
          {activeFilterCount > 0 && (
            <span className="bg-blue-600 text-white text-xs px-1.5 py-0.5 rounded-full">
              {activeFilterCount}
            </span>
          )}
        </button>

        {activeFilterCount > 0 && (
          <button
            type="button"
            onClick={clearAllFilters}
            className="flex items-center gap-1 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Clear all
          </button>
        )}
      </div>

      {/* Advanced filters */}
      {showAdvanced && (
        <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-gray-200">
          <DateRangePicker
            dateRange={filters.dateRange}
            onChange={(range) => updateFilters({ dateRange: range })}
          />

          <MultiSelect
            label="Entity Type"
            options={ENTITY_TYPES}
            selected={filters.entityTypes || []}
            onChange={(types) => updateFilters({ entityTypes: types.length ? types : undefined })}
            getLabel={(type) => ENTITY_TYPE_LABELS[type]}
            icon={Activity}
          />

          <MultiSelect
            label="Action"
            options={ACTION_TYPES}
            selected={filters.actions || []}
            onChange={(actions) => updateFilters({ actions: actions.length ? actions : undefined })}
            getLabel={(action) => ACTION_TYPE_LABELS[action]}
            icon={Activity}
          />

          {users.length > 0 && (
            <MultiSelect
              label="User"
              options={users.map((u) => u.id)}
              selected={filters.userIds || []}
              onChange={(ids) => updateFilters({ userIds: ids.length ? ids : undefined })}
              getLabel={(id) => users.find((u) => u.id === id)?.name || id}
              icon={User}
            />
          )}

          <MultiSelect
            label="Severity"
            options={SEVERITY_LEVELS}
            selected={filters.severity || []}
            onChange={(levels) => updateFilters({ severity: levels.length ? levels : undefined })}
            getLabel={(level) => level.charAt(0).toUpperCase() + level.slice(1)}
            icon={AlertTriangle}
          />

          <label className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
            <input
              type="checkbox"
              checked={filters.acgmeOverridesOnly || false}
              onChange={(e) => updateFilters({ acgmeOverridesOnly: e.target.checked || undefined })}
              className="w-4 h-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500"
            />
            <span className="text-sm text-gray-700">ACGME Overrides Only</span>
          </label>
        </div>
      )}

      {/* Active filter tags */}
      {filterTags.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 pt-2">
          <span className="text-xs text-gray-500">Active filters:</span>
          {filterTags.map((tag, idx) => (
            <FilterTag key={idx} label={tag.label} onRemove={tag.onRemove} />
          ))}
        </div>
      )}

      {/* Loading indicator */}
      {isLoading && (
        <div className="flex items-center justify-center py-2">
          <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span className="ml-2 text-sm text-gray-600">Loading...</span>
        </div>
      )}
    </div>
  );
}
