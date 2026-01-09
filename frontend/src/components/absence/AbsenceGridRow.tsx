'use client';

/**
 * AbsenceGridRow Component
 *
 * A single row in the absence grid representing one person.
 * Shows their name (sticky) and absence bars for each date.
 */

import { useMemo } from 'react';
import { format, isWeekend as checkIsWeekend, isSameDay, parseISO } from 'date-fns';
import { AbsenceBar, EmptyAbsenceCell } from './AbsenceBar';
import type { Absence, Person } from '@/types/api';

export interface AbsenceGridRowProps {
  person: Person;
  dates: Date[];
  /** Absences for this person, indexed by date string */
  absencesByDate: Map<string, Absence[]>;
  /** All absences for this person (for spanning calculation) */
  allAbsences: Absence[];
  /** Today's date for highlighting */
  today: Date;
  /** Handler for clicking empty cell to add absence */
  onAddAbsence: (personId: string, date: Date) => void;
  /** Handler for clicking absence to edit */
  onEditAbsence: (absence: Absence) => void;
}

export function AbsenceGridRow({
  person,
  dates,
  absencesByDate: _absencesByDate,
  allAbsences,
  today,
  onAddAbsence,
  onEditAbsence,
}: AbsenceGridRowProps) {
  // Calculate which absences span which cells
  const absenceSpans = useMemo(() => {
    const spans: Map<string, { absence: Absence; isFirst: boolean; isLast: boolean }[]> = new Map();

    // Initialize all dates
    dates.forEach((date) => {
      spans.set(format(date, 'yyyy-MM-dd'), []);
    });

    // For each absence, determine which cells it spans
    allAbsences.forEach((absence) => {
      const startDate = parseISO(absence.startDate);
      const endDate = parseISO(absence.endDate);

      dates.forEach((date) => {
        const dateStr = format(date, 'yyyy-MM-dd');
        const isInRange = date >= startDate && date <= endDate;

        if (isInRange) {
          const existingSpans = spans.get(dateStr) || [];
          const isFirst = isSameDay(date, startDate) || isSameDay(date, dates[0]);
          const isLast = isSameDay(date, endDate) || isSameDay(date, dates[dates.length - 1]);

          existingSpans.push({ absence, isFirst, isLast });
          spans.set(dateStr, existingSpans);
        }
      });
    });

    return spans;
  }, [allAbsences, dates]);

  return (
    <tr className="group hover:bg-gray-50 transition-colors duration-150">
      {/* Person name cell (sticky) */}
      <td className="sticky left-0 z-10 bg-white group-hover:bg-gray-50 transition-colors duration-150 px-3 py-2 text-sm font-medium text-gray-900 whitespace-nowrap border-r border-b border-gray-200 min-w-[180px]">
        <div className="flex flex-col">
          <span className="truncate max-w-[160px]" title={person.name}>
            {person.name}
          </span>
          <span className="text-xs text-gray-500">
            {person.type === 'resident' ? `PGY-${person.pgyLevel}` : 'Faculty'}
          </span>
        </div>
      </td>

      {/* Date cells */}
      {dates.map((date) => {
        const dateStr = format(date, 'yyyy-MM-dd');
        const isWeekend = checkIsWeekend(date);
        const isToday = isSameDay(date, today);
        const cellAbsences = absenceSpans.get(dateStr) || [];

        return (
          <td
            key={dateStr}
            className={`
              p-0.5 min-w-[40px] max-w-[60px] border-r border-b border-gray-200
              ${isWeekend ? 'bg-gray-100 group-hover:bg-gray-150' : 'bg-white group-hover:bg-gray-50'}
              ${isToday ? 'ring-2 ring-inset ring-blue-400' : ''}
            `}
          >
            {cellAbsences.length > 0 ? (
              <div className="flex flex-col gap-0.5">
                {cellAbsences.slice(0, 2).map(({ absence, isFirst, isLast }) => (
                  <AbsenceBar
                    key={absence.id}
                    absence={absence}
                    isFirst={isFirst}
                    isLast={isLast}
                    onClick={() => onEditAbsence(absence)}
                  />
                ))}
                {cellAbsences.length > 2 && (
                  <span className="text-xs text-gray-500 text-center">
                    +{cellAbsences.length - 2}
                  </span>
                )}
              </div>
            ) : (
              <EmptyAbsenceCell
                onClick={() => onAddAbsence(person.id, date)}
                isWeekend={isWeekend}
                isToday={isToday}
              />
            )}
          </td>
        );
      })}
    </tr>
  );
}

/**
 * Separator row between person groups (e.g., between PGY levels)
 */
export interface AbsenceGridSeparatorRowProps {
  label: string;
  columnCount: number;
}

export function AbsenceGridSeparatorRow({ label, columnCount }: AbsenceGridSeparatorRowProps) {
  return (
    <tr className="bg-gray-100">
      <td
        colSpan={columnCount + 1}
        className="px-3 py-1.5 text-xs font-semibold text-gray-600 uppercase tracking-wide border-b border-gray-300"
      >
        {label}
      </td>
    </tr>
  );
}
