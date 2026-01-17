'use client';

import React from 'react';
import { Calendar } from 'lucide-react';

export interface DateRange {
  start: Date | null;
  end: Date | null;
}

export interface DateRangePickerProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
  label?: string;
  minDate?: Date;
  maxDate?: Date;
  className?: string;
}

/**
 * DateRangePicker component for selecting date ranges
 *
 * @example
 * ```tsx
 * <DateRangePicker
 *   value={{ start: new Date(), end: new Date() }}
 *   onChange={(range) => setDateRange(range)}
 *   label="Select Date Range"
 * />
 * ```
 */
export function DateRangePicker({
  value,
  onChange,
  label,
  minDate,
  maxDate,
  className = '',
}: DateRangePickerProps) {
  const formatDate = (date: Date | null) => {
    if (!date) return '';
    return date.toISOString().split('T')[0];
  };

  const handleStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = e.target.value ? new Date(e.target.value) : null;
    onChange({ ...value, start: newDate });
  };

  const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = e.target.value ? new Date(e.target.value) : null;
    onChange({ ...value, end: newDate });
  };

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
        </label>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div className="relative">
          <label htmlFor="start-date" className="block text-xs text-gray-600 mb-1">
            Start Date
          </label>
          <div className="relative">
            <input
              id="start-date"
              type="date"
              value={formatDate(value.start)}
              onChange={handleStartChange}
              min={minDate ? formatDate(minDate) : undefined}
              max={maxDate ? formatDate(maxDate) : undefined}
              className="block w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>

        <div className="relative">
          <label htmlFor="end-date" className="block text-xs text-gray-600 mb-1">
            End Date
          </label>
          <div className="relative">
            <input
              id="end-date"
              type="date"
              value={formatDate(value.end)}
              onChange={handleEndChange}
              min={value.start ? formatDate(value.start) : minDate ? formatDate(minDate) : undefined}
              max={maxDate ? formatDate(maxDate) : undefined}
              className="block w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Quick date range presets
 */
export function DateRangePresets({
  onSelect,
  className = '',
}: {
  onSelect: (range: DateRange) => void;
  className?: string;
}) {
  const presets = [
    {
      label: 'Today',
      getValue: () => {
        const today = new Date();
        return { start: today, end: today };
      },
    },
    {
      label: 'This Week',
      getValue: () => {
        const today = new Date();
        const start = new Date(today);
        start.setDate(today.getDate() - today.getDay());
        const end = new Date(start);
        end.setDate(start.getDate() + 6);
        return { start, end };
      },
    },
    {
      label: 'This Month',
      getValue: () => {
        const today = new Date();
        const start = new Date(today.getFullYear(), today.getMonth(), 1);
        const end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        return { start, end };
      },
    },
    {
      label: 'This Year',
      getValue: () => {
        const today = new Date();
        const start = new Date(today.getFullYear(), 0, 1);
        const end = new Date(today.getFullYear(), 11, 31);
        return { start, end };
      },
    },
  ];

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {presets.map((preset) => (
        <button
          key={preset.label}
          onClick={() => onSelect(preset.getValue())}
          className="px-3 py-1 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
        >
          {preset.label}
        </button>
      ))}
    </div>
  );
}
