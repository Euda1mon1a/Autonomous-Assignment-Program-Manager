'use client';

import React from 'react';
import { Clock } from 'lucide-react';

export type TimeSlotPeriod = 'AM' | 'PM';

export interface TimeSlotProps {
  date: Date;
  period: TimeSlotPeriod;
  rotation?: string;
  person?: string;
  isSelected?: boolean;
  isHighlighted?: boolean;
  isDisabled?: boolean;
  onClick?: () => void;
  className?: string;
}

/**
 * TimeSlot component for displaying AM/PM schedule blocks
 *
 * @example
 * ```tsx
 * <TimeSlot
 *   date={new Date()}
 *   period="AM"
 *   rotation="Clinic"
 *   person="Dr. Smith"
 *   onClick={() => // console.log('clicked')}
 * />
 * ```
 */
export function TimeSlot({
  date: _date,
  period,
  rotation,
  person,
  isSelected = false,
  isHighlighted = false,
  isDisabled = false,
  onClick,
  className = '',
}: TimeSlotProps) {
  const baseStyles = 'relative p-2 rounded border transition-all min-h-[60px]';

  const stateStyles = isDisabled
    ? 'bg-gray-50 border-gray-200 opacity-50 cursor-not-allowed'
    : isSelected
    ? 'bg-blue-100 border-blue-400 ring-2 ring-blue-500'
    : isHighlighted
    ? 'bg-amber-50 border-amber-300'
    : rotation
    ? 'bg-white border-gray-300 hover:border-blue-400 hover:shadow-sm cursor-pointer'
    : 'bg-gray-50 border-gray-200 hover:bg-gray-100 cursor-pointer';

  return (
    <div
      className={`${baseStyles} ${stateStyles} ${className}`}
      onClick={!isDisabled ? onClick : undefined}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick && !isDisabled ? 0 : undefined}
    >
      {/* Period Badge */}
      <div className="absolute top-1 right-1">
        <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
          period === 'AM' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
        }`}>
          {period}
        </span>
      </div>

      {/* Content */}
      <div className="space-y-1">
        {rotation ? (
          <>
            <div className="text-sm font-medium text-gray-900 pr-8">
              {rotation}
            </div>
            {person && (
              <div className="text-xs text-gray-600 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {person}
              </div>
            )}
          </>
        ) : (
          <div className="text-xs text-gray-400 text-center py-2">
            Unassigned
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * TimeSlot grid for displaying a week or month view
 */
export function TimeSlotGrid({
  slots,
  className = '',
}: {
  slots: TimeSlotProps[];
  className?: string;
}) {
  return (
    <div className={`grid grid-cols-7 gap-1 ${className}`}>
      {slots.map((slot, index) => (
        <TimeSlot key={index} {...slot} />
      ))}
    </div>
  );
}
