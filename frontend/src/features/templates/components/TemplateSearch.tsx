'use client';

import { useState, useEffect, useCallback } from 'react';
import { Search, X, SlidersHorizontal } from 'lucide-react';
import type { TemplateFilters, TemplateCategory, TemplateVisibility, TemplateStatus } from '../types';
import { TEMPLATE_CATEGORIES, VISIBILITY_OPTIONS, STATUS_COLORS } from '../constants';

interface TemplateSearchProps {
  filters: TemplateFilters;
  onFiltersChange: (filters: TemplateFilters) => void;
  totalResults?: number;
  showAdvanced?: boolean;
}

export function TemplateSearch({
  filters,
  onFiltersChange,
  totalResults,
  showAdvanced = true,
}: TemplateSearchProps) {
  const [localQuery, setLocalQuery] = useState(filters.searchQuery || '');
  const [showFilters, setShowFilters] = useState(false);

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localQuery !== filters.searchQuery) {
        onFiltersChange({ ...filters, searchQuery: localQuery || undefined });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [localQuery, filters, onFiltersChange]);

  const handleClearSearch = () => {
    setLocalQuery('');
    onFiltersChange({ ...filters, searchQuery: undefined });
  };

  const handleCategoryChange = (category: TemplateCategory | '') => {
    onFiltersChange({ ...filters, category: category || undefined });
  };

  const handleVisibilityChange = (visibility: TemplateVisibility | '') => {
    onFiltersChange({ ...filters, visibility: visibility || undefined });
  };

  const handleStatusChange = (status: TemplateStatus | '') => {
    onFiltersChange({ ...filters, status: status || undefined });
  };

  const handleSortChange = (sortBy: TemplateFilters['sortBy']) => {
    onFiltersChange({ ...filters, sortBy });
  };

  const handleSortOrderChange = () => {
    onFiltersChange({
      ...filters,
      sortOrder: filters.sortOrder === 'asc' ? 'desc' : 'asc',
    });
  };

  const handleClearFilters = () => {
    setLocalQuery('');
    onFiltersChange({});
    setShowFilters(false);
  };

  const hasActiveFilters =
    filters.category ||
    filters.visibility ||
    filters.status ||
    filters.searchQuery ||
    (filters.tags && filters.tags.length > 0);

  return (
    <div className="space-y-3">
      {/* Search bar */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={localQuery}
            onChange={(e) => setLocalQuery(e.target.value)}
            placeholder="Search templates..."
            className="w-full pl-10 pr-10 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {localQuery && (
            <button
              onClick={handleClearSearch}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          )}
        </div>

        {showAdvanced && (
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-3 py-2 border rounded-lg flex items-center gap-2 ${
              showFilters || hasActiveFilters
                ? 'bg-blue-50 border-blue-200 text-blue-700'
                : 'hover:bg-gray-50'
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" />
            <span className="hidden sm:inline">Filters</span>
            {hasActiveFilters && (
              <span className="bg-blue-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {[filters.category, filters.visibility, filters.status, filters.searchQuery].filter(
                  Boolean
                ).length}
              </span>
            )}
          </button>
        )}
      </div>

      {/* Results count */}
      {totalResults !== undefined && (
        <div className="text-sm text-gray-600">
          {totalResults} template{totalResults !== 1 ? 's' : ''} found
          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="ml-2 text-blue-600 hover:underline"
            >
              Clear filters
            </button>
          )}
        </div>
      )}

      {/* Advanced filters */}
      {showFilters && (
        <div className="p-4 bg-gray-50 rounded-lg border space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Category filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                value={filters.category || ''}
                onChange={(e) => handleCategoryChange(e.target.value as TemplateCategory | '')}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All categories</option>
                {TEMPLATE_CATEGORIES.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Visibility filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Visibility
              </label>
              <select
                value={filters.visibility || ''}
                onChange={(e) => handleVisibilityChange(e.target.value as TemplateVisibility | '')}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All visibility</option>
                {VISIBILITY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Status filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={filters.status || ''}
                onChange={(e) => handleStatusChange(e.target.value as TemplateStatus | '')}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All statuses</option>
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="archived">Archived</option>
              </select>
            </div>

            {/* Sort options */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sort by
              </label>
              <div className="flex gap-1">
                <select
                  value={filters.sortBy || 'createdAt'}
                  onChange={(e) => handleSortChange(e.target.value as TemplateFilters['sortBy'])}
                  className="flex-1 px-3 py-2 border rounded-l-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="createdAt">Created date</option>
                  <option value="updatedAt">Updated date</option>
                  <option value="name">Name</option>
                  <option value="usageCount">Usage</option>
                </select>
                <button
                  onClick={handleSortOrderChange}
                  className="px-3 py-2 border border-l-0 rounded-r-lg hover:bg-gray-100"
                  title={filters.sortOrder === 'asc' ? 'Ascending' : 'Descending'}
                >
                  {filters.sortOrder === 'asc' ? '↑' : '↓'}
                </button>
              </div>
            </div>
          </div>

          {/* Active filter chips */}
          {hasActiveFilters && (
            <div className="flex flex-wrap gap-2 pt-2 border-t">
              {filters.category && (
                <FilterChip
                  label={`Category: ${filters.category}`}
                  onRemove={() => handleCategoryChange('')}
                />
              )}
              {filters.visibility && (
                <FilterChip
                  label={`Visibility: ${filters.visibility}`}
                  onRemove={() => handleVisibilityChange('')}
                />
              )}
              {filters.status && (
                <FilterChip
                  label={`Status: ${filters.status}`}
                  onRemove={() => handleStatusChange('')}
                />
              )}
              {filters.searchQuery && (
                <FilterChip
                  label={`Search: "${filters.searchQuery}"`}
                  onRemove={handleClearSearch}
                />
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function FilterChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
      {label}
      <button onClick={onRemove} className="p-0.5 hover:bg-blue-200 rounded-full">
        <X className="w-3 h-3" />
      </button>
    </span>
  );
}
