/**
 * Call Roster Hooks
 *
 * React Query hooks for fetching on-call assignment data
 * and contact information.
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { get, ApiError } from '@/lib/api';
import { format, startOfMonth, endOfMonth } from 'date-fns';
import type {
  AssignmentsResponse,
  CallRosterFilters,
  CallAssignment,
  OnCallPerson,
  Assignment,
} from './types';
import {
  isOnCallAssignment,
  getRoleType,
  getPersonName,
  getShiftType,
} from './types';

// ============================================================================
// Query Keys
// ============================================================================

export const callRosterQueryKeys = {
  all: ['call-roster'] as const,
  byDate: (startDate: string, endDate: string) =>
    ['call-roster', startDate, endDate] as const,
  byMonth: (month: Date) => {
    const start = format(startOfMonth(month), 'yyyy-MM-dd');
    const end = format(endOfMonth(month), 'yyyy-MM-dd');
    return ['call-roster', 'month', start, end] as const;
  },
  today: () => {
    const today = format(new Date(), 'yyyy-MM-dd');
    return ['call-roster', 'today', today] as const;
  },
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Build query string from filters
 */
function buildAssignmentsQueryString(filters: {
  start_date?: string;
  end_date?: string;
  person_id?: string;
  role?: string;
}): string {
  const params = new URLSearchParams();

  if (filters.start_date) {
    params.set('start_date', filters.start_date);
  }
  if (filters.end_date) {
    params.set('end_date', filters.end_date);
  }
  if (filters.person_id) {
    params.set('person_id', filters.person_id);
  }
  if (filters.role) {
    params.set('role', filters.role);
  }

  return params.toString();
}

/**
 * Transform API assignment to CallAssignment
 */
function transformToCallAssignment(assignment: Assignment): CallAssignment | null {
  if (!isOnCallAssignment(assignment) || !assignment.person || !assignment.block) {
    return null;
  }

  const roleType = getRoleType(assignment.person.pgy_level, assignment.role);
  const shift = getShiftType(assignment.rotation_template?.name, assignment.notes);

  const person: OnCallPerson = {
    id: assignment.person.id,
    name: getPersonName(assignment.person),
    pgy_level: assignment.person.pgy_level,
    role: roleType,
    phone: assignment.person.phone,
    pager: assignment.person.pager,
    email: assignment.person.email,
  };

  return {
    id: assignment.id,
    date: assignment.block.start_date,
    shift,
    person,
    rotation_name: assignment.rotation_template?.name,
    notes: assignment.notes,
  };
}

/**
 * Filter and transform assignments to on-call assignments only
 */
function filterOnCallAssignments(response: AssignmentsResponse): CallAssignment[] {
  return response.items
    .map(transformToCallAssignment)
    .filter((assignment): assignment is CallAssignment => assignment !== null);
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetch on-call assignments for a date range
 */
export function useOnCallAssignments(
  startDate: string,
  endDate: string,
  options?: Omit<UseQueryOptions<CallAssignment[], ApiError>, 'queryKey' | 'queryFn'>
) {
  const queryString = buildAssignmentsQueryString({
    start_date: startDate,
    end_date: endDate,
  });

  return useQuery<CallAssignment[], ApiError>({
    queryKey: callRosterQueryKeys.byDate(startDate, endDate),
    queryFn: async () => {
      const response = await get<AssignmentsResponse>(
        `/assignments${queryString ? `?${queryString}` : ''}`
      );
      return filterOnCallAssignments(response);
    },
    staleTime: 60 * 1000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: !!startDate && !!endDate,
    ...options,
  });
}

/**
 * Fetch on-call assignments for a specific month
 */
export function useMonthlyOnCallRoster(
  month: Date,
  options?: Omit<UseQueryOptions<CallAssignment[], ApiError>, 'queryKey' | 'queryFn'>
) {
  const startDate = format(startOfMonth(month), 'yyyy-MM-dd');
  const endDate = format(endOfMonth(month), 'yyyy-MM-dd');

  return useOnCallAssignments(startDate, endDate, {
    ...options,
    // Override the query key to use the month-specific one
    queryKey: callRosterQueryKeys.byMonth(month) as any,
  });
}

/**
 * Fetch today's on-call assignments
 */
export function useTodayOnCall(
  options?: Omit<UseQueryOptions<CallAssignment[], ApiError>, 'queryKey' | 'queryFn'>
) {
  const today = format(new Date(), 'yyyy-MM-dd');

  return useQuery<CallAssignment[], ApiError>({
    queryKey: callRosterQueryKeys.today(),
    queryFn: async () => {
      const queryString = buildAssignmentsQueryString({
        start_date: today,
        end_date: today,
      });
      const response = await get<AssignmentsResponse>(
        `/assignments${queryString ? `?${queryString}` : ''}`
      );
      return filterOnCallAssignments(response);
    },
    staleTime: 30 * 1000, // 30 seconds - today's data should be fresh
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true, // Always refetch when user returns to window
    ...options,
  });
}

/**
 * Fetch on-call assignments for a specific person
 */
export function usePersonOnCallAssignments(
  personId: string,
  startDate: string,
  endDate: string,
  options?: Omit<UseQueryOptions<CallAssignment[], ApiError>, 'queryKey' | 'queryFn'>
) {
  const queryString = buildAssignmentsQueryString({
    start_date: startDate,
    end_date: endDate,
    person_id: personId,
  });

  return useQuery<CallAssignment[], ApiError>({
    queryKey: ['call-roster', 'person', personId, startDate, endDate] as const,
    queryFn: async () => {
      const response = await get<AssignmentsResponse>(
        `/assignments${queryString ? `?${queryString}` : ''}`
      );
      return filterOnCallAssignments(response);
    },
    staleTime: 60 * 1000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: !!personId && !!startDate && !!endDate,
    ...options,
  });
}

/**
 * Group assignments by date for calendar display
 */
export function useOnCallByDate(startDate: string, endDate: string) {
  const { data, ...rest } = useOnCallAssignments(startDate, endDate);

  const byDate = data?.reduce((acc, assignment) => {
    if (!acc[assignment.date]) {
      acc[assignment.date] = [];
    }
    acc[assignment.date].push(assignment);
    return acc;
  }, {} as Record<string, CallAssignment[]>);

  return {
    data: byDate || {},
    assignments: data || [],
    ...rest,
  };
}
