/**
 * Call Roster Hooks
 *
 * React Query hooks for fetching faculty call assignment data.
 * Uses the /call-assignments endpoint which returns pre-joined data.
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { get, ApiError } from '@/lib/api';
import { format, startOfMonth, endOfMonth } from 'date-fns';
import type { CallAssignment, OnCallPerson } from './types';

// ============================================================================
// API Response Types
// ============================================================================

interface ApiCallAssignment {
  id: string;
  date: string;
  person_id: string;
  call_type: 'sunday' | 'weekday' | 'holiday' | 'backup';
  is_weekend: boolean;
  is_holiday: boolean;
  person: {
    id: string;
    name: string;
    faculty_role: string | null;
  };
}

interface ApiCallAssignmentsResponse {
  items: ApiCallAssignment[];
  total: number;
}

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
// Data Fetching Functions
// ============================================================================

/**
 * Fetch call assignments for a date range from the /call-assignments endpoint
 */
async function fetchCallAssignments(startDate: string, endDate: string): Promise<ApiCallAssignment[]> {
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
  });
  const response = await get<ApiCallAssignmentsResponse>(`/call-assignments?${params}`);
  return response.items;
}

// ============================================================================
// Transform Functions
// ============================================================================

/**
 * Transform API call assignment to frontend CallAssignment type
 */
function transformToCallAssignment(apiAssignment: ApiCallAssignment): CallAssignment {
  const person: OnCallPerson = {
    id: apiAssignment.person.id,
    name: apiAssignment.person.name,
    role: 'attending', // Faculty are always attending
    pgy_level: undefined,
    email: undefined,
    phone: undefined,
    pager: undefined,
  };

  // Map call_type to shift - faculty call is typically day shifts
  const shift: 'day' | 'night' | '24hr' = apiAssignment.call_type === 'backup' ? 'day' : 'day';

  return {
    id: apiAssignment.id,
    date: apiAssignment.date,
    shift,
    person,
    rotation_name: apiAssignment.call_type, // Show call type as rotation name
    notes: apiAssignment.is_holiday ? 'Holiday' : undefined,
  };
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetch call assignments for a date range
 */
export function useOnCallAssignments(
  startDate: string,
  endDate: string,
  options?: Omit<UseQueryOptions<CallAssignment[], ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<CallAssignment[], ApiError>({
    queryKey: callRosterQueryKeys.byDate(startDate, endDate),
    queryFn: async () => {
      const assignments = await fetchCallAssignments(startDate, endDate);
      return assignments
        .map(transformToCallAssignment)
        .sort((a, b) => a.date.localeCompare(b.date));
    },
    staleTime: 60 * 1000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: !!startDate && !!endDate,
    ...options,
  });
}

/**
 * Fetch call assignments for a specific month
 */
export function useMonthlyOnCallRoster(
  month: Date,
  options?: Omit<UseQueryOptions<CallAssignment[], ApiError>, 'queryKey' | 'queryFn'>
) {
  const startDate = format(startOfMonth(month), 'yyyy-MM-dd');
  const endDate = format(endOfMonth(month), 'yyyy-MM-dd');

  return useOnCallAssignments(startDate, endDate, options);
}

/**
 * Fetch today's call assignments
 */
export function useTodayOnCall(
  options?: Omit<UseQueryOptions<CallAssignment[], ApiError>, 'queryKey' | 'queryFn'>
) {
  const today = format(new Date(), 'yyyy-MM-dd');

  return useQuery<CallAssignment[], ApiError>({
    queryKey: callRosterQueryKeys.today(),
    queryFn: async () => {
      const assignments = await fetchCallAssignments(today, today);
      return assignments.map(transformToCallAssignment);
    },
    staleTime: 30 * 1000, // 30 seconds - today's data should be fresh
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
    ...options,
  });
}

/**
 * Fetch call assignments for a specific person
 */
export function usePersonOnCallAssignments(
  personId: string,
  startDate: string,
  endDate: string,
  options?: Omit<UseQueryOptions<CallAssignment[], ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<CallAssignment[], ApiError>({
    queryKey: ['call-roster', 'person', personId, startDate, endDate] as const,
    queryFn: async () => {
      const assignments = await fetchCallAssignments(startDate, endDate);
      return assignments
        .filter(a => a.person_id === personId)
        .map(transformToCallAssignment)
        .sort((a, b) => a.date.localeCompare(b.date));
    },
    staleTime: 60 * 1000,
    gcTime: 10 * 60 * 1000,
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
