/**
 * CallCard Component
 *
 * Individual call entry card displaying on-call person details,
 * contact information, and shift details.
 */

'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Moon, Sun, Clock } from 'lucide-react';
import type { CallAssignment } from './types';
import { ROLE_COLORS, SHIFT_LABELS } from './types';
import { ContactInfo } from './ContactInfo';

interface CallCardProps {
  assignment: CallAssignment;
  showDate?: boolean;
  defaultExpanded?: boolean;
}

export function CallCard({
  assignment,
  showDate = false,
  defaultExpanded = false,
}: CallCardProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const getShiftIcon = () => {
    switch (assignment.shift) {
      case 'night':
        return <Moon className="h-4 w-4" />;
      case '24hr':
        return <Clock className="h-4 w-4" />;
      default:
        return <Sun className="h-4 w-4" />;
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
      {/* Header - Always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3 flex-1">
          {/* Role Badge */}
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium border ${
              ROLE_COLORS[assignment.person.role]
            }`}
          >
            {assignment.person.role.charAt(0).toUpperCase() +
              assignment.person.role.slice(1)}
          </span>

          {/* Person Info */}
          <div className="flex flex-col items-start">
            <span className="font-semibold text-gray-900">
              {assignment.person.name}
            </span>
            {assignment.person.pgyLevel && (
              <span className="text-xs text-gray-500">
                PGY-{assignment.person.pgyLevel}
              </span>
            )}
          </div>

          {/* Shift Badge */}
          <div className="flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm">
            {getShiftIcon()}
            <span>{SHIFT_LABELS[assignment.shift]}</span>
          </div>
        </div>

        {/* Expand/Collapse Icon */}
        {expanded ? (
          <ChevronUp className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronDown className="h-5 w-5 text-gray-400" />
        )}
      </button>

      {/* Expanded Content */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-100 space-y-3 pt-3">
          {/* Date (if shown) */}
          {showDate && (
            <div className="text-sm text-gray-600">
              <span className="font-medium">Date:</span>{' '}
              {new Date(assignment.date).toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })}
            </div>
          )}

          {/* Rotation Name */}
          {assignment.rotationName && (
            <div className="text-sm">
              <span className="font-medium text-gray-700">Rotation:</span>{' '}
              <span className="text-gray-600">{assignment.rotationName}</span>
            </div>
          )}

          {/* Contact Information */}
          <ContactInfo person={assignment.person} showLabel={true} />

          {/* Notes */}
          {assignment.notes && (
            <div className="text-sm">
              <span className="font-medium text-gray-700">Notes:</span>{' '}
              <span className="text-gray-600">{assignment.notes}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Compact version for calendar day cells
 */
export function CallCardCompact({ assignment }: { assignment: CallAssignment }) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div
      className="relative"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div
        className={`px-2 py-1 rounded text-xs border cursor-pointer ${
          ROLE_COLORS[assignment.person.role]
        }`}
      >
        <div className="font-medium truncate">{assignment.person.name}</div>
        {assignment.person.pgyLevel && (
          <div className="text-xs opacity-75">PGY-{assignment.person.pgyLevel}</div>
        )}
      </div>

      {/* Tooltip on hover */}
      {showTooltip && (
        <div className="absolute z-50 left-0 top-full mt-1 w-64 bg-white border border-gray-300 rounded-lg shadow-lg p-3 space-y-2">
          <div className="font-semibold">{assignment.person.name}</div>
          {assignment.person.pgyLevel && (
            <div className="text-sm text-gray-600">
              PGY-{assignment.person.pgyLevel} • {assignment.person.role}
            </div>
          )}
          {assignment.rotationName && (
            <div className="text-sm text-gray-600">{assignment.rotationName}</div>
          )}
          <div className="pt-2 border-t border-gray-200">
            <ContactInfo person={assignment.person} showLabel={false} compact={true} />
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * List item version for list view
 */
export function CallListItem({ assignment, showDate }: { assignment: CallAssignment; showDate?: boolean }) {
  return (
    <div className="flex items-center gap-4 py-3 px-4 hover:bg-gray-50 border-b border-gray-100">
      {showDate && (
        <div className="text-sm font-medium text-gray-700 w-32">
          {new Date(assignment.date).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
          })}
        </div>
      )}

      <span
        className={`px-3 py-1 rounded-full text-xs font-medium border ${
          ROLE_COLORS[assignment.person.role]
        }`}
      >
        {assignment.person.role.charAt(0).toUpperCase() + assignment.person.role.slice(1)}
      </span>

      <div className="flex-1">
        <div className="font-medium text-gray-900">{assignment.person.name}</div>
        {assignment.person.pgyLevel && (
          <div className="text-sm text-gray-500">PGY-{assignment.person.pgyLevel}</div>
        )}
      </div>

      <div className="flex items-center gap-2 text-sm text-gray-600">
        {assignment.shift === 'night' && <Moon className="h-4 w-4" />}
        {assignment.shift === '24hr' && <Clock className="h-4 w-4" />}
        {assignment.shift === 'day' && <Sun className="h-4 w-4" />}
        <span>{SHIFT_LABELS[assignment.shift]}</span>
      </div>

      <ContactInfo person={assignment.person} showLabel={false} compact={true} />
    </div>
  );
}
