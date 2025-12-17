/**
 * CallCalendarDay Component
 *
 * Calendar day cell showing on-call assignments for a specific day.
 * Highlights today and displays color-coded badges for each on-call person.
 */

'use client';

import { useState } from 'react';
import { format, isSameDay } from 'date-fns';
import type { CallAssignment } from './types';
import { ROLE_COLORS } from './types';
import { ContactInfo } from './ContactInfo';

interface CallCalendarDayProps {
  date: Date;
  assignments: CallAssignment[];
  isCurrentMonth: boolean;
  isToday: boolean;
  onClick?: (date: Date, assignments: CallAssignment[]) => void;
}

export function CallCalendarDay({
  date,
  assignments,
  isCurrentMonth,
  isToday,
  onClick,
}: CallCalendarDayProps) {
  const [showPopover, setShowPopover] = useState(false);

  const handleClick = () => {
    if (onClick) {
      onClick(date, assignments);
    }
  };

  return (
    <div
      className={`
        min-h-[120px] border border-gray-200 p-2 relative cursor-pointer
        ${!isCurrentMonth ? 'bg-gray-50 opacity-50' : 'bg-white hover:bg-gray-50'}
        ${isToday ? 'ring-2 ring-blue-500 ring-inset' : ''}
      `}
      onClick={handleClick}
      onMouseEnter={() => setShowPopover(assignments.length > 0)}
      onMouseLeave={() => setShowPopover(false)}
    >
      {/* Day Number */}
      <div className="flex justify-between items-start mb-2">
        <span
          className={`
            text-sm font-semibold
            ${isToday ? 'text-blue-600' : isCurrentMonth ? 'text-gray-900' : 'text-gray-400'}
          `}
        >
          {format(date, 'd')}
        </span>

        {isToday && (
          <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full">
            Today
          </span>
        )}
      </div>

      {/* Assignments */}
      <div className="space-y-1">
        {assignments.slice(0, 3).map((assignment) => (
          <div
            key={assignment.id}
            className={`text-xs px-2 py-1 rounded border truncate ${
              ROLE_COLORS[assignment.person.role]
            }`}
            title={`${assignment.person.name} - ${assignment.person.role}`}
          >
            <div className="font-medium truncate">{assignment.person.name}</div>
            <div className="text-xs opacity-75">
              {assignment.person.pgy_level ? `PGY-${assignment.person.pgy_level}` : assignment.person.role}
            </div>
          </div>
        ))}

        {/* Show count if more than 3 */}
        {assignments.length > 3 && (
          <div className="text-xs text-gray-500 text-center py-1">
            +{assignments.length - 3} more
          </div>
        )}

        {/* Empty state */}
        {assignments.length === 0 && isCurrentMonth && (
          <div className="text-xs text-gray-400 text-center py-2">
            No call
          </div>
        )}
      </div>

      {/* Popover with full details */}
      {showPopover && assignments.length > 0 && (
        <div className="absolute z-50 left-0 top-full mt-1 w-80 bg-white border border-gray-300 rounded-lg shadow-xl p-4 space-y-3">
          <div className="font-semibold border-b pb-2">
            {format(date, 'EEEE, MMMM d, yyyy')}
            {isToday && <span className="ml-2 text-blue-600">(Today)</span>}
          </div>

          {assignments.map((assignment, index) => (
            <div
              key={assignment.id}
              className={`space-y-2 ${index > 0 ? 'pt-3 border-t border-gray-200' : ''}`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-1 rounded text-xs font-medium border ${
                    ROLE_COLORS[assignment.person.role]
                  }`}
                >
                  {assignment.person.role.charAt(0).toUpperCase() + assignment.person.role.slice(1)}
                </span>
                <span className="font-medium">{assignment.person.name}</span>
                {assignment.person.pgy_level && (
                  <span className="text-sm text-gray-500">
                    PGY-{assignment.person.pgy_level}
                  </span>
                )}
              </div>

              {assignment.rotation_name && (
                <div className="text-sm text-gray-600">
                  {assignment.rotation_name}
                </div>
              )}

              <ContactInfo person={assignment.person} showLabel={false} compact={true} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Simple day header for calendar
 */
export function CalendarDayHeader({ day }: { day: string }) {
  return (
    <div className="bg-gray-100 border border-gray-200 p-2 text-center font-semibold text-sm text-gray-700">
      {day}
    </div>
  );
}

/**
 * Empty calendar day (for padding)
 */
export function EmptyCalendarDay() {
  return <div className="min-h-[120px] bg-gray-50 border border-gray-200" />;
}
