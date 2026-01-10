'use client';

/**
 * AbsenceGrid Component
 *
 * Main grid view for viewing and editing absences across multiple people.
 * Layout: People (rows) × Dates (columns)
 *
 * Features:
 * - People grouped by PGY level
 * - Absence bars spanning date ranges
 * - Click empty cell to add, click bar to edit
 * - Weekend/today highlighting
 * - Person type filter (residents/faculty/all)
 */

import React, { useMemo } from 'react';
import { Users } from 'lucide-react';
import { format, eachDayOfInterval, isWeekend, isSameDay, parseISO } from 'date-fns';
import { useQuery } from '@tanstack/react-query';
import { get } from '@/lib/api';
import { usePeople, ListResponse } from '@/lib/hooks';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorAlert } from '@/components/ErrorAlert';
import { EmptyState } from '@/components/EmptyState';
import { AbsenceGridRow, AbsenceGridSeparatorRow } from './AbsenceGridRow';
import type { Absence, Person } from '@/types/api';

export type PersonTypeFilter = 'all' | 'residents' | 'faculty';

export interface AbsenceGridProps {
  startDate: Date;
  endDate: Date;
  /** Filter by person type */
  personTypeFilter?: PersonTypeFilter;
  /** Handler for adding absence (opens modal) */
  onAddAbsence: (personId: string, date: Date) => void;
  /** Handler for editing absence (opens modal) */
  onEditAbsence: (absence: Absence) => void;
}

interface PersonGroup {
  label: string;
  people: Person[];
}

/**
 * Custom hook to fetch absences for a date range
 */
function useAbsencesForRange(startDate: string, endDate: string) {
  return useQuery<ListResponse<Absence>>({
    queryKey: ['absences', 'range', startDate, endDate],
    queryFn: () =>
      get<ListResponse<Absence>>(
        `/absences?startDate=${startDate}&endDate=${endDate}&pageSize=500`
      ),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function AbsenceGrid({
  startDate,
  endDate,
  personTypeFilter = 'all',
  onAddAbsence,
  onEditAbsence,
}: AbsenceGridProps) {
  const today = useMemo(() => new Date(), []);

  // Format dates for API
  const startDateStr = format(startDate, 'yyyy-MM-dd');
  const endDateStr = format(endDate, 'yyyy-MM-dd');

  // Fetch data
  const { data: absencesData, isLoading: absencesLoading, error: absencesError } = useAbsencesForRange(startDateStr, endDateStr);
  const { data: peopleData, isLoading: peopleLoading, error: peopleError } = usePeople();

  // Generate date array for columns
  const dates = useMemo(() => {
    return eachDayOfInterval({ start: startDate, end: endDate });
  }, [startDate, endDate]);

  // Filter and group people
  const personGroups = useMemo((): PersonGroup[] => {
    if (!peopleData?.items) return [];

    let filteredPeople = peopleData.items;

    // Apply person type filter
    if (personTypeFilter === 'residents') {
      filteredPeople = filteredPeople.filter((p) => p.type === 'resident');
    } else if (personTypeFilter === 'faculty') {
      filteredPeople = filteredPeople.filter((p) => p.type === 'faculty');
    }

    // Group by type and PGY level
    const residents = filteredPeople.filter((p) => p.type === 'resident');
    const faculty = filteredPeople.filter((p) => p.type === 'faculty');

    // Sort residents by PGY level
    const pgy1 = residents.filter((p) => p.pgyLevel === 1).sort((a, b) => a.name.localeCompare(b.name));
    const pgy2 = residents.filter((p) => p.pgyLevel === 2).sort((a, b) => a.name.localeCompare(b.name));
    const pgy3 = residents.filter((p) => p.pgyLevel === 3).sort((a, b) => a.name.localeCompare(b.name));

    // Sort faculty alphabetically
    const sortedFaculty = faculty.sort((a, b) => a.name.localeCompare(b.name));

    const groups: PersonGroup[] = [];

    if (pgy1.length > 0) groups.push({ label: 'PGY-1', people: pgy1 });
    if (pgy2.length > 0) groups.push({ label: 'PGY-2', people: pgy2 });
    if (pgy3.length > 0) groups.push({ label: 'PGY-3', people: pgy3 });
    if (sortedFaculty.length > 0 && personTypeFilter !== 'residents') {
      groups.push({ label: 'Faculty', people: sortedFaculty });
    }

    return groups;
  }, [peopleData?.items, personTypeFilter]);

  // Build absence lookup: personId -> Absence[]
  const absencesByPerson = useMemo(() => {
    const map = new Map<string, Absence[]>();

    absencesData?.items?.forEach((absence) => {
      const existing = map.get(absence.personId) || [];
      existing.push(absence);
      map.set(absence.personId, existing);
    });

    return map;
  }, [absencesData?.items]);

  // Build absence lookup by person and date: personId -> dateStr -> Absence[]
  const absenceLookup = useMemo(() => {
    const lookup = new Map<string, Map<string, Absence[]>>();

    absencesData?.items?.forEach((absence) => {
      const personMap = lookup.get(absence.personId) || new Map<string, Absence[]>();

      const absenceStart = parseISO(absence.startDate);
      const absenceEnd = parseISO(absence.endDate);

      dates.forEach((date) => {
        if (date >= absenceStart && date <= absenceEnd) {
          const dateStr = format(date, 'yyyy-MM-dd');
          const existing = personMap.get(dateStr) || [];
          existing.push(absence);
          personMap.set(dateStr, existing);
        }
      });

      lookup.set(absence.personId, personMap);
    });

    return lookup;
  }, [absencesData?.items, dates]);

  // Loading state
  if (absencesLoading || peopleLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  // Error state
  if (absencesError || peopleError) {
    return (
      <ErrorAlert
        message={absencesError || peopleError || 'Failed to load data'}
      />
    );
  }

  // Empty state
  if (personGroups.length === 0) {
    return (
      <EmptyState
        icon={Users}
        title="No people found"
        description="Add people to see them in the absence grid."
      />
    );
  }

  return (
    <div className="overflow-auto max-h-[calc(100vh-250px)] border border-gray-200 rounded-lg shadow-sm">
      <table className="min-w-full border-collapse">
        {/* Header row with dates */}
        <thead className="sticky top-0 z-20 bg-gray-50">
          <tr>
            {/* Person column header */}
            <th className="sticky left-0 z-30 bg-gray-50 px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide border-r border-b border-gray-300 min-w-[180px]">
              Person
            </th>
            {/* Date column headers */}
            {dates.map((date) => {
              const dateStr = format(date, 'yyyy-MM-dd');
              const dayOfWeek = format(date, 'EEE');
              const dayNum = format(date, 'd');
              const isWeekendDay = isWeekend(date);
              const isTodayDate = isSameDay(date, today);

              return (
                <th
                  key={dateStr}
                  className={`
                    px-1 py-2 text-center text-xs font-medium border-r border-b border-gray-300
                    min-w-[40px] max-w-[60px]
                    ${isWeekendDay ? 'bg-gray-200 text-gray-600' : 'bg-gray-50 text-gray-700'}
                    ${isTodayDate ? 'ring-2 ring-inset ring-blue-400' : ''}
                  `}
                >
                  <div className="flex flex-col items-center">
                    <span className={isWeekendDay ? 'text-gray-500' : ''}>{dayOfWeek}</span>
                    <span className="font-semibold">{dayNum}</span>
                  </div>
                </th>
              );
            })}
          </tr>
        </thead>

        {/* Body with person groups */}
        <tbody>
          {personGroups.map((group) => (
            <React.Fragment key={group.label}>
              {/* Group separator */}
              <AbsenceGridSeparatorRow label={group.label} columnCount={dates.length} />

              {/* Person rows */}
              {group.people.map((person) => (
                <AbsenceGridRow
                  key={person.id}
                  person={person}
                  dates={dates}
                  absencesByDate={absenceLookup.get(person.id) || new Map()}
                  allAbsences={absencesByPerson.get(person.id) || []}
                  today={today}
                  onAddAbsence={onAddAbsence}
                  onEditAbsence={onEditAbsence}
                />
              ))}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
