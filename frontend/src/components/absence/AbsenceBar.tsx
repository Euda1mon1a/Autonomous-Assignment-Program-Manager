'use client';

/**
 * AbsenceBar Component
 *
 * Visual representation of an absence spanning one or more days in the grid.
 * Displays as a colored bar with the absence type abbreviation.
 */

import { useMemo } from 'react';
import type { Absence } from '@/types/api';

export interface AbsenceBarProps {
  absence: Absence;
  /** Whether this is the first visible cell of the absence */
  isFirst: boolean;
  /** Whether this is the last visible cell of the absence */
  isLast: boolean;
  /** Click handler for editing */
  onClick: () => void;
}

// Color mapping for absence types (matching AbsenceList.tsx)
export const absenceTypeColors: Record<string, { bg: string; text: string; border: string }> = {
  // Planned leave
  vacation: { bg: 'bg-green-200', text: 'text-green-800', border: 'border-green-400' },
  conference: { bg: 'bg-blue-200', text: 'text-blue-800', border: 'border-blue-400' },
  // Medical
  sick: { bg: 'bg-red-200', text: 'text-red-800', border: 'border-red-400' },
  medical: { bg: 'bg-red-200', text: 'text-red-800', border: 'border-red-400' },
  convalescent: { bg: 'bg-red-300', text: 'text-red-900', border: 'border-red-500' },
  maternity_paternity: { bg: 'bg-pink-200', text: 'text-pink-800', border: 'border-pink-400' },
  // Emergency (blocking - Hawaii reality)
  family_emergency: { bg: 'bg-purple-200', text: 'text-purple-800', border: 'border-purple-400' },
  emergency_leave: { bg: 'bg-purple-300', text: 'text-purple-900', border: 'border-purple-500' },
  bereavement: { bg: 'bg-gray-300', text: 'text-gray-800', border: 'border-gray-500' },
  // Military
  deployment: { bg: 'bg-orange-200', text: 'text-orange-800', border: 'border-orange-400' },
  tdy: { bg: 'bg-yellow-200', text: 'text-yellow-800', border: 'border-yellow-400' },
  // Fallback
  personal: { bg: 'bg-purple-200', text: 'text-purple-800', border: 'border-purple-400' },
};

// Abbreviations for absence types
const absenceTypeAbbreviations: Record<string, string> = {
  vacation: 'VAC',
  conference: 'CONF',
  sick: 'SICK',
  medical: 'MED',
  convalescent: 'CONV',
  maternity_paternity: 'PAR',
  family_emergency: 'FAM',
  emergency_leave: 'EMER',
  bereavement: 'BER',
  deployment: 'DEP',
  tdy: 'TDY',
  personal: 'PER',
};

export function AbsenceBar({ absence, isFirst, isLast, onClick }: AbsenceBarProps) {
  const colors = absenceTypeColors[absence.absence_type] || absenceTypeColors.personal;
  const abbreviation = absenceTypeAbbreviations[absence.absence_type] || absence.absence_type.substring(0, 3).toUpperCase();

  // Build tooltip text
  const tooltipText = useMemo(() => {
    const type = absence.absence_type.replace('_', ' ');
    const start = new Date(absence.start_date).toLocaleDateString();
    const end = new Date(absence.end_date).toLocaleDateString();
    const notes = absence.notes ? `\n${absence.notes}` : '';
    return `${type}\n${start} - ${end}${notes}`;
  }, [absence]);

  return (
    <button
      onClick={onClick}
      title={tooltipText}
      className={`
        h-6 w-full flex items-center overflow-hidden
        ${colors.bg} ${colors.text} border ${colors.border}
        hover:opacity-80 transition-opacity cursor-pointer
        ${isFirst ? 'rounded-l-md pl-1' : 'border-l-0'}
        ${isLast ? 'rounded-r-md pr-1' : 'border-r-0'}
        ${!isFirst && !isLast ? 'border-l-0 border-r-0' : ''}
      `}
    >
      {isFirst && (
        <span className="text-xs font-medium truncate">
          {abbreviation}
        </span>
      )}
    </button>
  );
}

/**
 * Empty cell component for cells without absences
 */
export interface EmptyAbsenceCellProps {
  onClick: () => void;
  isWeekend: boolean;
  isToday: boolean;
}

export function EmptyAbsenceCell({ onClick, isWeekend, isToday }: EmptyAbsenceCellProps) {
  return (
    <button
      onClick={onClick}
      className={`
        h-8 w-full
        ${isWeekend ? 'bg-gray-100' : 'bg-white'}
        ${isToday ? 'ring-2 ring-inset ring-blue-400' : ''}
        hover:bg-blue-50 transition-colors cursor-pointer
        border-r border-b border-gray-200
      `}
      aria-label="Add absence"
    />
  );
}
