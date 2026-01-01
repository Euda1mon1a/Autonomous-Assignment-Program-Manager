/**
 * DatePicker Component
 *
 * Calendar-based date selection with range support
 */

import React, { useState, useMemo } from 'react';

export interface DatePickerProps {
  value?: string; // ISO date string
  onChange: (date: string) => void;
  min?: string;
  max?: string;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export const DatePicker: React.FC<DatePickerProps> = ({
  value,
  onChange,
  min,
  max,
  disabled = false,
  placeholder = 'Select date',
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [viewDate, setViewDate] = useState(() => {
    return value ? new Date(value) : new Date();
  });

  const selectedDate = value ? new Date(value) : null;

  // Get days in month
  const daysInMonth = useMemo(() => {
    const year = viewDate.getFullYear();
    const month = viewDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysCount = lastDay.getDate();
    const startDayOfWeek = firstDay.getDay();

    const days: Array<{ date: Date; isCurrentMonth: boolean }> = [];

    // Previous month days
    const prevMonthLastDay = new Date(year, month, 0).getDate();
    for (let i = startDayOfWeek - 1; i >= 0; i--) {
      days.push({
        date: new Date(year, month - 1, prevMonthLastDay - i),
        isCurrentMonth: false,
      });
    }

    // Current month days
    for (let i = 1; i <= daysCount; i++) {
      days.push({
        date: new Date(year, month, i),
        isCurrentMonth: true,
      });
    }

    // Next month days
    const remainingDays = 42 - days.length; // 6 weeks * 7 days
    for (let i = 1; i <= remainingDays; i++) {
      days.push({
        date: new Date(year, month + 1, i),
        isCurrentMonth: false,
      });
    }

    return days;
  }, [viewDate]);

  const handleDateClick = (date: Date) => {
    const isoDate = date.toISOString().split('T')[0];

    // Check min/max constraints
    if (min && isoDate < min) return;
    if (max && isoDate > max) return;

    onChange(isoDate);
    setIsOpen(false);
  };

  const handlePrevMonth = () => {
    setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() - 1));
  };

  const handleNextMonth = () => {
    setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() + 1));
  };

  const handleToday = () => {
    const today = new Date();
    setViewDate(today);
    handleDateClick(today);
  };

  const isDateDisabled = (date: Date): boolean => {
    const isoDate = date.toISOString().split('T')[0];
    if (min && isoDate < min) return true;
    if (max && isoDate > max) return true;
    return false;
  };

  const isDateSelected = (date: Date): boolean => {
    if (!selectedDate) return false;
    return date.toISOString().split('T')[0] === selectedDate.toISOString().split('T')[0];
  };

  const isToday = (date: Date): boolean => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  return (
    <div className={`date-picker relative ${className}`}>
      {/* Input */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        aria-label={value ? `Selected date: ${new Date(value).toLocaleDateString('en-US', {
          weekday: 'short',
          year: 'numeric',
          month: 'short',
          day: 'numeric',
        })}` : placeholder}
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-white text-left focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
      >
        <div className="flex items-center justify-between">
          <span className={value ? 'text-gray-900' : 'text-gray-500'}>
            {value
              ? new Date(value).toLocaleDateString('en-US', {
                  weekday: 'short',
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })
              : placeholder}
          </span>
          <span className="text-gray-400" aria-hidden="true">📅</span>
        </div>
      </button>

      {/* Calendar Popup */}
      {isOpen && !disabled && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Calendar */}
          <div className="absolute z-20 mt-2 bg-white rounded-lg shadow-lg border border-gray-200 p-4 min-w-[320px]" role="dialog" aria-label="Choose date">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <button
                type="button"
                onClick={handlePrevMonth}
                className="p-1 hover:bg-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Previous month"
              >
                <span aria-hidden="true">←</span>
              </button>

              <div className="font-semibold text-gray-900" aria-live="polite">
                {viewDate.toLocaleDateString('en-US', {
                  month: 'long',
                  year: 'numeric',
                })}
              </div>

              <button
                type="button"
                onClick={handleNextMonth}
                className="p-1 hover:bg-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Next month"
              >
                <span aria-hidden="true">→</span>
              </button>
            </div>

            {/* Weekday Headers */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map((day) => (
                <div
                  key={day}
                  className="text-center text-xs font-semibold text-gray-600 py-1"
                >
                  {day}
                </div>
              ))}
            </div>

            {/* Days Grid */}
            <div className="grid grid-cols-7 gap-1" role="grid" aria-label="Calendar days">
              {daysInMonth.map((day, idx) => {
                const disabled = isDateDisabled(day.date);
                const selected = isDateSelected(day.date);
                const today = isToday(day.date);

                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => !disabled && handleDateClick(day.date)}
                    disabled={disabled}
                    aria-label={`${day.date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}${today ? ' (today)' : ''}${selected ? ' (selected)' : ''}`}
                    aria-selected={selected}
                    aria-disabled={disabled}
                    className={`
                      aspect-square p-1 text-sm rounded transition-colors
                      ${!day.isCurrentMonth ? 'text-gray-400' : 'text-gray-900'}
                      ${selected ? 'bg-blue-600 text-white font-semibold' : ''}
                      ${today && !selected ? 'border-2 border-blue-600' : ''}
                      ${disabled ? 'cursor-not-allowed opacity-30' : 'hover:bg-gray-100'}
                      ${selected ? 'hover:bg-blue-700' : ''}
                      focus:outline-none focus:ring-2 focus:ring-blue-500
                    `}
                  >
                    {day.date.getDate()}
                  </button>
                );
              })}
            </div>

            {/* Footer */}
            <div className="mt-4 pt-4 border-t border-gray-200 flex justify-between">
              <button
                type="button"
                onClick={handleToday}
                className="text-sm text-blue-600 hover:text-blue-800 focus:outline-none focus:underline"
                aria-label="Select today's date"
              >
                Today
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="text-sm text-gray-600 hover:text-gray-800 focus:outline-none focus:underline"
                aria-label="Close calendar"
              >
                Close
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default DatePicker;
