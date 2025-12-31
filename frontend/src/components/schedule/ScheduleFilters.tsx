/**
 * ScheduleFilters Component
 *
 * Comprehensive filtering controls for schedule views
 */

import React, { useState } from 'react';
import { Badge } from '../ui/Badge';

export interface ScheduleFilterOptions {
  persons?: string[];
  rotations?: string[];
  shifts?: Array<'AM' | 'PM' | 'Night'>;
  dateRange?: {
    start: string;
    end: string;
  };
  showConflicts?: boolean;
  showACGMEViolations?: boolean;
  pgyLevels?: string[];
}

export interface ScheduleFiltersProps {
  availablePersons: Array<{ id: string; name: string; role: string }>;
  availableRotations: string[];
  availablePGYLevels: string[];
  currentFilters: ScheduleFilterOptions;
  onFilterChange: (filters: ScheduleFilterOptions) => void;
  onReset?: () => void;
  className?: string;
}

export const ScheduleFilters: React.FC<ScheduleFiltersProps> = ({
  availablePersons,
  availableRotations,
  availablePGYLevels,
  currentFilters,
  onFilterChange,
  onReset,
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handlePersonToggle = (personId: string) => {
    const current = currentFilters.persons || [];
    const updated = current.includes(personId)
      ? current.filter(id => id !== personId)
      : [...current, personId];
    onFilterChange({ ...currentFilters, persons: updated });
  };

  const handleRotationToggle = (rotation: string) => {
    const current = currentFilters.rotations || [];
    const updated = current.includes(rotation)
      ? current.filter(r => r !== rotation)
      : [...current, rotation];
    onFilterChange({ ...currentFilters, rotations: updated });
  };

  const handleShiftToggle = (shift: 'AM' | 'PM' | 'Night') => {
    const current = currentFilters.shifts || [];
    const updated = current.includes(shift)
      ? current.filter(s => s !== shift)
      : [...current, shift];
    onFilterChange({ ...currentFilters, shifts: updated });
  };

  const handlePGYToggle = (level: string) => {
    const current = currentFilters.pgyLevels || [];
    const updated = current.includes(level)
      ? current.filter(l => l !== level)
      : [...current, level];
    onFilterChange({ ...currentFilters, pgyLevels: updated });
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (currentFilters.persons?.length) count += currentFilters.persons.length;
    if (currentFilters.rotations?.length) count += currentFilters.rotations.length;
    if (currentFilters.shifts?.length) count += currentFilters.shifts.length;
    if (currentFilters.pgyLevels?.length) count += currentFilters.pgyLevels.length;
    if (currentFilters.showConflicts) count++;
    if (currentFilters.showACGMEViolations) count++;
    return count;
  };

  const activeCount = getActiveFilterCount();

  return (
    <div className={`schedule-filters bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold">Filters</h3>
          {activeCount > 0 && (
            <Badge variant="default">{activeCount} active</Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {onReset && activeCount > 0 && (
            <button
              onClick={onReset}
              className="text-sm text-blue-600 hover:text-blue-800 focus:outline-none focus:underline"
            >
              Clear All
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label={isExpanded ? 'Collapse filters' : 'Expand filters'}
            aria-expanded={isExpanded}
          >
            {isExpanded ? '▲' : '▼'}
          </button>
        </div>
      </div>

      {/* Filter Controls */}
      {isExpanded && (
        <div className="p-4 space-y-4">
          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date Range
            </label>
            <div className="grid grid-cols-2 gap-2">
              <input
                type="date"
                value={currentFilters.dateRange?.start || ''}
                onChange={(e) => onFilterChange({
                  ...currentFilters,
                  dateRange: {
                    start: e.target.value,
                    end: currentFilters.dateRange?.end || '',
                  },
                })}
                className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="date"
                value={currentFilters.dateRange?.end || ''}
                onChange={(e) => onFilterChange({
                  ...currentFilters,
                  dateRange: {
                    start: currentFilters.dateRange?.start || '',
                    end: e.target.value,
                  },
                })}
                className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Persons */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Persons ({currentFilters.persons?.length || 0} selected)
            </label>
            <div className="max-h-48 overflow-y-auto border border-gray-300 rounded p-2">
              {availablePersons.map(person => (
                <label key={person.id} className="flex items-center gap-2 p-1 hover:bg-gray-50 rounded cursor-pointer">
                  <input
                    type="checkbox"
                    checked={currentFilters.persons?.includes(person.id) || false}
                    onChange={() => handlePersonToggle(person.id)}
                    className="rounded focus:ring-blue-500"
                  />
                  <span className="text-sm">{person.name}</span>
                  <span className="text-xs text-gray-500">({person.role})</span>
                </label>
              ))}
            </div>
          </div>

          {/* Rotations */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Rotations
            </label>
            <div className="flex flex-wrap gap-2">
              {availableRotations.map(rotation => (
                <button
                  key={rotation}
                  onClick={() => handleRotationToggle(rotation)}
                  className={`
                    px-3 py-1 rounded-full text-sm font-medium transition-colors
                    ${currentFilters.rotations?.includes(rotation)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }
                    focus:outline-none focus:ring-2 focus:ring-blue-500
                  `}
                >
                  {rotation}
                </button>
              ))}
            </div>
          </div>

          {/* Shifts */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Shifts
            </label>
            <div className="flex gap-2">
              {(['AM', 'PM', 'Night'] as const).map(shift => (
                <button
                  key={shift}
                  onClick={() => handleShiftToggle(shift)}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium transition-colors
                    ${currentFilters.shifts?.includes(shift)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }
                    focus:outline-none focus:ring-2 focus:ring-blue-500
                  `}
                >
                  {shift}
                </button>
              ))}
            </div>
          </div>

          {/* PGY Levels */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              PGY Levels
            </label>
            <div className="flex gap-2">
              {availablePGYLevels.map(level => (
                <button
                  key={level}
                  onClick={() => handlePGYToggle(level)}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium transition-colors
                    ${currentFilters.pgyLevels?.includes(level)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }
                    focus:outline-none focus:ring-2 focus:ring-blue-500
                  `}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>

          {/* Special Filters */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Special Filters
            </label>
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={currentFilters.showConflicts || false}
                  onChange={(e) => onFilterChange({
                    ...currentFilters,
                    showConflicts: e.target.checked,
                  })}
                  className="rounded focus:ring-blue-500"
                />
                <span className="text-sm">Show only conflicts</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={currentFilters.showACGMEViolations || false}
                  onChange={(e) => onFilterChange({
                    ...currentFilters,
                    showACGMEViolations: e.target.checked,
                  })}
                  className="rounded focus:ring-blue-500"
                />
                <span className="text-sm">Show only ACGME violations</span>
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScheduleFilters;
