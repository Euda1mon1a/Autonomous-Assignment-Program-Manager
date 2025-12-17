/**
 * CallRoster Component
 *
 * Main component for the Call Roster feature.
 * Displays who is on call in a month view calendar with contact information.
 * Critical for nurses to know who to page right now.
 */

'use client';

import { useState, useMemo } from 'react';
import {
  format,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  addMonths,
  subMonths,
  eachDayOfInterval,
  isSameMonth,
  isToday as isTodayFn,
} from 'date-fns';
import { ChevronLeft, ChevronRight, Calendar, List, AlertCircle, Loader2 } from 'lucide-react';
import { useMonthlyOnCallRoster, useTodayOnCall } from './hooks';
import { CallCalendarDay, CalendarDayHeader } from './CallCalendarDay';
import { CallCard, CallListItem } from './CallCard';
import { ROLE_COLORS, ROLE_LABELS, type RoleType, type CallAssignment } from './types';

const DAYS_OF_WEEK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export function CallRoster() {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [viewMode, setViewMode] = useState<'calendar' | 'list'>('calendar');
  const [selectedRole, setSelectedRole] = useState<RoleType | 'all'>('all');

  // Fetch monthly data
  const {
    data: monthlyAssignments,
    isLoading: isLoadingMonthly,
    error: monthlyError,
  } = useMonthlyOnCallRoster(currentMonth);

  // Fetch today's data separately for the highlight section
  const { data: todayAssignments } = useTodayOnCall();

  // Generate calendar days
  const calendarDays = useMemo(() => {
    const monthStart = startOfMonth(currentMonth);
    const monthEnd = endOfMonth(currentMonth);
    const calendarStart = startOfWeek(monthStart);
    const calendarEnd = endOfWeek(monthEnd);

    return eachDayOfInterval({ start: calendarStart, end: calendarEnd });
  }, [currentMonth]);

  // Group assignments by date
  const assignmentsByDate = useMemo(() => {
    if (!monthlyAssignments) return {};

    return monthlyAssignments.reduce((acc, assignment) => {
      const dateKey = assignment.date;
      if (!acc[dateKey]) {
        acc[dateKey] = [];
      }
      acc[dateKey].push(assignment);
      return acc;
    }, {} as Record<string, CallAssignment[]>);
  }, [monthlyAssignments]);

  // Filter assignments by role
  const filteredAssignments = useMemo(() => {
    if (!monthlyAssignments) return [];

    if (selectedRole === 'all') {
      return monthlyAssignments;
    }

    return monthlyAssignments.filter((a) => a.person.role === selectedRole);
  }, [monthlyAssignments, selectedRole]);

  // Navigation
  const goToPreviousMonth = () => setCurrentMonth((prev) => subMonths(prev, 1));
  const goToNextMonth = () => setCurrentMonth((prev) => addMonths(prev, 1));
  const goToToday = () => setCurrentMonth(new Date());

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Call Roster</h1>
          <p className="text-gray-600 mt-1">Who to page right now</p>
        </div>

        <div className="flex gap-2">
          {/* View Toggle */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('calendar')}
              className={`px-3 py-1.5 rounded flex items-center gap-2 text-sm font-medium transition-colors ${
                viewMode === 'calendar'
                  ? 'bg-white text-gray-900 shadow'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Calendar className="h-4 w-4" />
              Calendar
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 rounded flex items-center gap-2 text-sm font-medium transition-colors ${
                viewMode === 'list'
                  ? 'bg-white text-gray-900 shadow'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <List className="h-4 w-4" />
              List
            </button>
          </div>
        </div>
      </header>

      {/* Today's On-Call Highlight */}
      {todayAssignments && todayAssignments.length > 0 && (
        <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="h-5 w-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-blue-900">On Call RIGHT NOW</h2>
          </div>
          <div className="space-y-2">
            {todayAssignments.map((assignment) => (
              <CallCard key={assignment.id} assignment={assignment} defaultExpanded={false} />
            ))}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-4 flex-wrap">
        <span className="text-sm font-medium text-gray-700">Role Legend:</span>
        <button
          onClick={() => setSelectedRole('all')}
          className={`px-3 py-1.5 rounded border-2 text-sm font-medium transition-colors ${
            selectedRole === 'all'
              ? 'bg-gray-800 text-white border-gray-800'
              : 'bg-white text-gray-600 border-gray-300 hover:border-gray-400'
          }`}
        >
          All
        </button>
        {(Object.keys(ROLE_COLORS) as RoleType[]).map((role) => (
          <button
            key={role}
            onClick={() => setSelectedRole(role)}
            className={`px-3 py-1.5 rounded border-2 text-sm font-medium transition-colors ${
              selectedRole === role
                ? ROLE_COLORS[role]
                : `bg-white ${ROLE_COLORS[role].split(' ')[1]} border-gray-300 hover:border-${role === 'attending' ? 'red' : role === 'senior' ? 'blue' : 'green'}-400`
            }`}
          >
            {ROLE_LABELS[role]}
          </button>
        ))}
      </div>

      {/* Month Navigation */}
      <div className="flex items-center justify-between bg-white border border-gray-200 rounded-lg p-4">
        <button
          onClick={goToPreviousMonth}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="Previous month"
        >
          <ChevronLeft className="h-5 w-5 text-gray-600" />
        </button>

        <div className="flex items-center gap-4">
          <h2 className="text-xl font-semibold text-gray-900">
            {format(currentMonth, 'MMMM yyyy')}
          </h2>
          <button
            onClick={goToToday}
            className="px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium"
          >
            Today
          </button>
        </div>

        <button
          onClick={goToNextMonth}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="Next month"
        >
          <ChevronRight className="h-5 w-5 text-gray-600" />
        </button>
      </div>

      {/* Loading State */}
      {isLoadingMonthly && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-3 text-gray-600">Loading call roster...</span>
        </div>
      )}

      {/* Error State */}
      {monthlyError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900">Error loading call roster</h3>
            <p className="text-red-700 text-sm mt-1">{monthlyError.message}</p>
          </div>
        </div>
      )}

      {/* Calendar View */}
      {!isLoadingMonthly && !monthlyError && viewMode === 'calendar' && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          {/* Day Headers */}
          <div className="grid grid-cols-7">
            {DAYS_OF_WEEK.map((day) => (
              <CalendarDayHeader key={day} day={day} />
            ))}
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7">
            {calendarDays.map((day) => {
              const dateKey = format(day, 'yyyy-MM-dd');
              const dayAssignments = assignmentsByDate[dateKey] || [];
              const filteredDayAssignments =
                selectedRole === 'all'
                  ? dayAssignments
                  : dayAssignments.filter((a) => a.person.role === selectedRole);

              return (
                <CallCalendarDay
                  key={dateKey}
                  date={day}
                  assignments={filteredDayAssignments}
                  isCurrentMonth={isSameMonth(day, currentMonth)}
                  isToday={isTodayFn(day)}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* List View */}
      {!isLoadingMonthly && !monthlyError && viewMode === 'list' && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          {filteredAssignments.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No on-call assignments found for this month
            </div>
          ) : (
            <div>
              {filteredAssignments.map((assignment) => (
                <CallListItem
                  key={assignment.id}
                  assignment={assignment}
                  showDate={true}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Stats */}
      {!isLoadingMonthly && monthlyAssignments && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="grid grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {monthlyAssignments.length}
              </div>
              <div className="text-sm text-gray-600">Total Call Shifts</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-700">
                {monthlyAssignments.filter((a) => a.person.role === 'attending').length}
              </div>
              <div className="text-sm text-gray-600">Attending</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-700">
                {monthlyAssignments.filter((a) => a.person.role === 'senior').length}
              </div>
              <div className="text-sm text-gray-600">Senior</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-700">
                {monthlyAssignments.filter((a) => a.person.role === 'intern').length}
              </div>
              <div className="text-sm text-gray-600">Intern</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
