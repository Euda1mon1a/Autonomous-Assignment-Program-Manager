'use client';

import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import {
  Search,
  Filter,
  SortAsc,
  SortDesc,
  RefreshCw,
  CheckSquare,
  Square,
  ChevronDown,
  X,
  AlertTriangle,
} from 'lucide-react';
import { ConflictCard } from './ConflictCard';
import { useConflicts, useDetectConflicts } from './hooks';
import type {
  Conflict,
  ConflictFilters,
  ConflictSortOptions,
  ConflictSortField,
  ConflictSeverity,
  ConflictType,
  ConflictStatus,
} from './types';

// ============================================================================
// Props
// ============================================================================

interface ConflictListProps {
  initialFilters?: ConflictFilters;
  onConflictSelect?: (conflict: Conflict) => void;
  onResolve?: (conflict: Conflict) => void;
  onViewSuggestions?: (conflict: Conflict) => void;
  onViewHistory?: (conflict: Conflict) => void;
  onOverride?: (conflict: Conflict) => void;
  onIgnore?: (conflict: Conflict) => void;
  onBatchSelect?: (conflicts: Conflict[]) => void;
  selectable?: boolean;
  compact?: boolean;
}

// ============================================================================
// Filter Options
// ============================================================================

const SEVERITY_OPTIONS: { value: ConflictSeverity; label: string }[] = [
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

const TYPE_OPTIONS: { value: ConflictType; label: string }[] = [
  { value: 'scheduling_overlap', label: 'Scheduling Overlap' },
  { value: 'acgmeViolation', label: 'ACGME Violation' },
  { value: 'supervision_missing', label: 'Missing Supervision' },
  { value: 'capacity_exceeded', label: 'Capacity Exceeded' },
  { value: 'absence_conflict', label: 'Absence Conflict' },
  { value: 'qualification_mismatch', label: 'Qualification Mismatch' },
  { value: 'consecutive_duty', label: 'Consecutive Duty' },
  { value: 'rest_period', label: 'Rest Period Violation' },
  { value: 'coverage_gap', label: 'Coverage Gap' },
];

const STATUS_OPTIONS: { value: ConflictStatus; label: string }[] = [
  { value: 'unresolved', label: 'Unresolved' },
  { value: 'pending_review', label: 'Pending Review' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'ignored', label: 'Ignored' },
];

const SORT_OPTIONS: { value: ConflictSortField; label: string }[] = [
  { value: 'severity', label: 'Severity' },
  { value: 'date', label: 'Conflict Date' },
  { value: 'detectedAt', label: 'Detection Date' },
  { value: 'type', label: 'Type' },
  { value: 'status', label: 'Status' },
];

// ============================================================================
// Component
// ============================================================================

export function ConflictList({
  initialFilters = {},
  onConflictSelect,
  onResolve,
  onViewSuggestions,
  onViewHistory,
  onOverride,
  onIgnore,
  onBatchSelect,
  selectable = false,
  compact = false,
}: ConflictListProps) {
  // State
  const [filters, setFilters] = useState<ConflictFilters>(initialFilters);
  const [sort, setSort] = useState<ConflictSortOptions>({
    field: 'severity',
    direction: 'desc',
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [focusedIndex, setFocusedIndex] = useState<number>(-1);
  const conflictRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  // Queries
  const {
    data: conflictsData,
    isLoading,
    error,
    refetch,
  } = useConflicts({ ...filters, search: searchQuery }, sort);

  const detectConflicts = useDetectConflicts();

  // Computed values
  const conflicts = useMemo(() => conflictsData?.items || [], [conflictsData]);
  const totalCount = conflictsData?.total || 0;

  // Handlers
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  }, []);

  const handleSortChange = useCallback((field: ConflictSortField) => {
    setSort((prev) => ({
      field,
      direction: prev.field === field && prev.direction === 'desc' ? 'asc' : 'desc',
    }));
  }, []);

  const handleFilterChange = useCallback(
    <K extends keyof ConflictFilters>(key: K, value: ConflictFilters[K]) => {
      setFilters((prev) => ({ ...prev, [key]: value }));
    },
    []
  );

  const handleClearFilters = useCallback(() => {
    setFilters({});
    setSearchQuery('');
  }, []);

  const handleToggleSelect = useCallback((conflict: Conflict) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(conflict.id)) {
        next.delete(conflict.id);
      } else {
        next.add(conflict.id);
      }
      return next;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    if (selectedIds.size === conflicts.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(conflicts.map((c) => c.id)));
    }
  }, [conflicts, selectedIds.size]);

  const handleBatchAction = useCallback(() => {
    if (onBatchSelect) {
      const selected = conflicts.filter((c) => selectedIds.has(c.id));
      onBatchSelect(selected);
    }
  }, [conflicts, selectedIds, onBatchSelect]);

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  const handleDetectNew = useCallback(() => {
    const today = new Date();
    const monthAgo = new Date(today);
    monthAgo.setMonth(monthAgo.getMonth() - 1);

    detectConflicts.mutate({
      startDate: monthAgo.toISOString().split('T')[0],
      endDate: today.toISOString().split('T')[0],
    });
  }, [detectConflicts]);

  // Keyboard navigation for conflict list
  useEffect(() => {
    if (!conflicts.length) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if user is typing in an input field
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return;

      switch (e.key) {
        case 'ArrowDown':
        case 'j':
          e.preventDefault();
          setFocusedIndex(prev => {
            const next = prev < conflicts.length - 1 ? prev + 1 : prev;
            conflictRefs.current.get(next)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return next;
          });
          break;
        case 'ArrowUp':
        case 'k':
          e.preventDefault();
          setFocusedIndex(prev => {
            const next = prev > 0 ? prev - 1 : 0;
            conflictRefs.current.get(next)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return next;
          });
          break;
        case 'Enter':
          e.preventDefault();
          if (focusedIndex >= 0 && focusedIndex < conflicts.length) {
            const conflict = conflicts[focusedIndex];
            onConflictSelect?.(conflict);
          }
          break;
        case 'Escape':
          e.preventDefault();
          setFocusedIndex(-1);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [conflicts, focusedIndex, onConflictSelect]);

  // Reset focus when conflicts change
  useEffect(() => {
    setFocusedIndex(-1);
  }, [filters, searchQuery, sort]);

  // Active filter count
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.types?.length) count++;
    if (filters.severities?.length) count++;
    if (filters.statuses?.length) count++;
    if (filters.dateRange) count++;
    if (searchQuery) count++;
    return count;
  }, [filters, searchQuery]);

  // Render
  return (
    <div className="flex flex-col h-full">
      {/* Header with search and filters */}
      <div className="p-4 border-b bg-white">
        {/* Search and action bar */}
        <div className="flex items-center gap-3 mb-3">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
            <input
              type="text"
              placeholder="Search conflicts..."
              value={searchQuery}
              onChange={handleSearchChange}
              aria-label="Search conflicts by title or description"
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Filter toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            aria-label={showFilters ? 'Hide filters' : 'Show filters'}
            aria-expanded={showFilters}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors
              ${showFilters || activeFilterCount > 0
                ? 'bg-blue-50 border-blue-200 text-blue-700'
                : 'border-gray-300 hover:bg-gray-50'
              }
            `}
          >
            <Filter className="w-4 h-4" aria-hidden="true" />
            <span>Filters</span>
            {activeFilterCount > 0 && (
              <span className="px-1.5 py-0.5 bg-blue-500 text-white text-xs rounded-full">
                {activeFilterCount}
              </span>
            )}
          </button>

          {/* Refresh */}
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50"
            aria-label={isLoading ? 'Refreshing conflicts' : 'Refresh conflict list'}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} aria-hidden="true" />
          </button>

          {/* Detect new conflicts */}
          <button
            onClick={handleDetectNew}
            disabled={detectConflicts.isPending}
            aria-label={detectConflicts.isPending ? 'Detecting conflicts' : 'Detect new conflicts'}
            className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:opacity-50 transition-all duration-200 hover:shadow-lg active:scale-95"
          >
            <AlertTriangle className={`w-4 h-4 ${detectConflicts.isPending ? 'animate-spin' : ''}`} aria-hidden="true" />
            <span>{detectConflicts.isPending ? 'Detecting...' : 'Detect'}</span>
          </button>
        </div>

        {/* Filter panel */}
        {showFilters && (
          <div className="p-4 bg-gray-50 rounded-lg space-y-4" role="region" aria-label="Conflict filters">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Severity filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Severity
                </label>
                <MultiSelect
                  options={SEVERITY_OPTIONS}
                  value={filters.severities || []}
                  onChange={(value) => handleFilterChange('severities', value as ConflictSeverity[])}
                  placeholder="All severities"
                />
              </div>

              {/* Type filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type
                </label>
                <MultiSelect
                  options={TYPE_OPTIONS}
                  value={filters.types || []}
                  onChange={(value) => handleFilterChange('types', value as ConflictType[])}
                  placeholder="All types"
                />
              </div>

              {/* Status filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <MultiSelect
                  options={STATUS_OPTIONS}
                  value={filters.statuses || []}
                  onChange={(value) => handleFilterChange('statuses', value as ConflictStatus[])}
                  placeholder="All statuses"
                />
              </div>
            </div>

            {/* Date range */}
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date Range
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="date"
                    value={filters.dateRange?.start || ''}
                    onChange={(e) =>
                      handleFilterChange('dateRange', {
                        start: e.target.value,
                        end: filters.dateRange?.end || '',
                      })
                    }
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-gray-500">to</span>
                  <input
                    type="date"
                    value={filters.dateRange?.end || ''}
                    onChange={(e) =>
                      handleFilterChange('dateRange', {
                        start: filters.dateRange?.start || '',
                        end: e.target.value,
                      })
                    }
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <button
                onClick={handleClearFilters}
                className="self-end px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Clear All
              </button>
            </div>
          </div>
        )}

        {/* Sort and selection bar */}
        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center gap-2">
            {selectable && (
              <>
                <button
                  onClick={handleSelectAll}
                  className="p-1 rounded hover:bg-gray-100"
                  aria-label={
                    selectedIds.size === conflicts.length ? 'Deselect all' : 'Select all'
                  }
                >
                  {selectedIds.size === conflicts.length && conflicts.length > 0 ? (
                    <CheckSquare className="w-5 h-5 text-blue-500" />
                  ) : (
                    <Square className="w-5 h-5 text-gray-400" />
                  )}
                </button>
                {selectedIds.size > 0 && (
                  <span className="text-sm text-gray-600">
                    {selectedIds.size} selected
                  </span>
                )}
                {selectedIds.size > 0 && onBatchSelect && (
                  <button
                    onClick={handleBatchAction}
                    className="ml-2 px-3 py-1 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Batch Actions
                  </button>
                )}
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">
              {totalCount} conflict{totalCount !== 1 ? 's' : ''}
            </span>
            <div className="flex items-center gap-1 ml-4">
              <span className="text-sm text-gray-500">Sort:</span>
              {SORT_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleSortChange(option.value)}
                  className={`
                    flex items-center gap-1 px-2 py-1 text-sm rounded transition-colors
                    ${sort.field === option.value
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100'
                    }
                  `}
                >
                  {option.label}
                  {sort.field === option.value &&
                    (sort.direction === 'desc' ? (
                      <SortDesc className="w-3 h-3" />
                    ) : (
                      <SortAsc className="w-3 h-3" />
                    ))}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Conflict list */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading && conflicts.length === 0 ? (
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="p-4 bg-gray-100 rounded-lg border border-gray-200">
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 bg-gray-200 rounded"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-5 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                      <div className="flex gap-2 mt-2">
                        <div className="h-3 bg-gray-200 rounded w-20"></div>
                        <div className="h-3 bg-gray-200 rounded w-20"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-64 text-red-500">
            <AlertTriangle className="w-12 h-12 mb-4" />
            <p className="text-lg font-medium">Error loading conflicts</p>
            <p className="text-sm">{error.message}</p>
            <button
              onClick={handleRefresh}
              className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
            >
              Try Again
            </button>
          </div>
        ) : conflicts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <CheckSquare className="w-12 h-12 mb-4 text-green-500" />
            <p className="text-lg font-medium">No conflicts found</p>
            <p className="text-sm">
              {activeFilterCount > 0
                ? 'Try adjusting your filters'
                : 'All scheduling conflicts have been resolved'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {conflicts.map((conflict, index) => (
              <div
                key={conflict.id}
                ref={(el) => {
                  if (el) {
                    conflictRefs.current.set(index, el);
                  } else {
                    conflictRefs.current.delete(index);
                  }
                }}
                tabIndex={0}
                className={`
                  flex items-start gap-3 animate-fadeInUp transition-all rounded-lg
                  ${focusedIndex === index ? 'ring-2 ring-blue-500 ring-offset-2' : ''}
                `}
                style={{ animationDelay: `${index * 50}ms` }}
                onFocus={() => setFocusedIndex(index)}
                onClick={() => setFocusedIndex(index)}
                role="button"
                aria-label={`Conflict: ${conflict.description}`}
              >
                {selectable && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleSelect(conflict);
                    }}
                    className="flex-shrink-0 mt-4 p-1 rounded hover:bg-gray-100"
                    aria-label={
                      selectedIds.has(conflict.id) ? 'Deselect' : 'Select'
                    }
                  >
                    {selectedIds.has(conflict.id) ? (
                      <CheckSquare className="w-5 h-5 text-blue-500" />
                    ) : (
                      <Square className="w-5 h-5 text-gray-400" />
                    )}
                  </button>
                )}
                <div className="flex-1">
                  <ConflictCard
                    conflict={conflict}
                    isSelected={selectedIds.has(conflict.id)}
                    onSelect={onConflictSelect}
                    onResolve={onResolve}
                    onViewSuggestions={onViewSuggestions}
                    onViewHistory={onViewHistory}
                    onOverride={onOverride}
                    onIgnore={onIgnore}
                    compact={compact}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// MultiSelect Component
// ============================================================================

interface MultiSelectProps<T extends string> {
  options: { value: T; label: string }[];
  value: T[];
  onChange: (value: T[]) => void;
  placeholder?: string;
}

function MultiSelect<T extends string>({
  options,
  value,
  onChange,
  placeholder = 'Select...',
}: MultiSelectProps<T>) {
  const [isOpen, setIsOpen] = useState(false);

  const handleToggle = (optionValue: T) => {
    if (value.includes(optionValue)) {
      onChange(value.filter((v) => v !== optionValue));
    } else {
      onChange([...value, optionValue]);
    }
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange([]);
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <span className="truncate text-gray-700">
          {value.length === 0
            ? placeholder
            : value.length === 1
            ? options.find((o) => o.value === value[0])?.label
            : `${value.length} selected`}
        </span>
        <div className="flex items-center gap-1">
          {value.length > 0 && (
            <button
              onClick={handleClear}
              className="p-0.5 hover:bg-gray-100 rounded"
            >
              <X className="w-3 h-3 text-gray-400" />
            </button>
          )}
          <ChevronDown
            className={`w-4 h-4 text-gray-400 transition-transform ${
              isOpen ? 'rotate-180' : ''
            }`}
          />
        </div>
      </button>

      {isOpen && (
        <div
          className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto"
          onMouseLeave={() => setIsOpen(false)}
        >
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => handleToggle(option.value)}
              className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-50 text-left"
            >
              {value.includes(option.value) ? (
                <CheckSquare className="w-4 h-4 text-blue-500 flex-shrink-0" />
              ) : (
                <Square className="w-4 h-4 text-gray-400 flex-shrink-0" />
              )}
              <span className="text-sm">{option.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
