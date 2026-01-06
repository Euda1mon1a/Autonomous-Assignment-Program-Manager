/**
 * Call Roster Hooks
 *
 * React Query hooks for fetching on-call assignment data
 * and contact information.
 *
 * ARCHITECTURE NOTE:
 * The backend API returns assignments with only IDs (block_id, person_id,
 * rotation_template_id), not nested objects. This hook performs client-side
 * joins by fetching blocks, people, and rotation templates separately,
 * then joining them in memory. This matches the pattern used by the
 * schedule page for consistent data access.
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { get, ApiError } from '@/lib/api';
import { format, startOfMonth, endOfMonth } from 'date-fns';
import type {
  CallAssignment,
  OnCallPerson,
  RawAssignment,
  RawAssignmentsResponse,
  RawBlock,
  RawBlocksResponse,
  RawPerson,
  RawPeopleResponse,
  RawRotationTemplate,
  RawRotationTemplatesResponse,
} from './types';
import {
  getRoleType,
  getShiftType,
  isOnCallTemplate,
  getPersonName,
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
// Data Fetching Functions
// ============================================================================

/**
 * Fetch assignments for a date range with activity_type filter for on_call
 */
async function fetchAssignments(startDate: string, endDate: string): Promise<RawAssignment[]> {
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
    activity_type: 'on_call',
    page_size: '1000', // Ensure we get all on-call assignments
  });
  const response = await get<RawAssignmentsResponse>(`/assignments?${params}`);
  return response.items;
}

/**
 * Fetch blocks for a date range
 */
async function fetchBlocks(startDate: string, endDate: string): Promise<Map<string, RawBlock>> {
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
  });
  const response = await get<RawBlocksResponse>(`/blocks?${params}`);

  const blockMap = new Map<string, RawBlock>();
  response.items.forEach(block => blockMap.set(block.id, block));
  return blockMap;
}

/**
 * Fetch all people (cached separately for efficiency)
 */
async function fetchPeople(): Promise<Map<string, RawPerson>> {
  const response = await get<RawPeopleResponse>('/people');

  const personMap = new Map<string, RawPerson>();
  response.items.forEach(person => personMap.set(person.id, person));
  return personMap;
}

/**
 * Fetch all rotation templates (cached separately for efficiency)
 */
async function fetchRotationTemplates(): Promise<Map<string, RawRotationTemplate>> {
  const response = await get<RawRotationTemplatesResponse>('/rotation-templates');

  const templateMap = new Map<string, RawRotationTemplate>();
  response.items.forEach(template => templateMap.set(template.id, template));
  return templateMap;
}

// ============================================================================
// Transform Functions
// ============================================================================

/**
 * Transform raw assignment to CallAssignment by joining with related data
 */
function transformToCallAssignment(
  assignment: RawAssignment,
  blockMap: Map<string, RawBlock>,
  personMap: Map<string, RawPerson>,
  templateMap: Map<string, RawRotationTemplate>
): CallAssignment | null {
  const block = blockMap.get(assignment.block_id);
  const person = personMap.get(assignment.person_id);
  const template = assignment.rotation_template_id
    ? templateMap.get(assignment.rotation_template_id)
    : null;

  // Skip if we can't find the block or person
  if (!block || !person) {
    return null;
  }

  // Skip if not an on-call template (double-check)
  if (template && !isOnCallTemplate(template)) {
    return null;
  }

  const roleType = getRoleType(person.pgy_level ?? undefined, assignment.role);
  const shift = getShiftType(template?.name, assignment.notes);

  const onCallPerson: OnCallPerson = {
    id: person.id,
    name: getPersonName(person),
    pgy_level: person.pgy_level ?? undefined,
    role: roleType,
    email: person.email ?? undefined,
    // Note: phone and pager are not in the current Person schema
    // but we include the fields for future compatibility
    phone: undefined,
    pager: undefined,
  };

  return {
    id: assignment.id,
    date: block.date,
    shift,
    person: onCallPerson,
    rotation_name: template?.name,
    notes: assignment.notes ?? undefined,
  };
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetch on-call assignments for a date range with client-side joins
 */
export function useOnCallAssignments(
  startDate: string,
  endDate: string,
  options?: Omit<UseQueryOptions<CallAssignment[], ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<CallAssignment[], ApiError>({
    queryKey: callRosterQueryKeys.byDate(startDate, endDate),
    queryFn: async () => {
      // Fetch all required data in parallel
      const [assignments, blockMap, personMap, templateMap] = await Promise.all([
        fetchAssignments(startDate, endDate),
        fetchBlocks(startDate, endDate),
        fetchPeople(),
        fetchRotationTemplates(),
      ]);

      // Transform and filter assignments
      return assignments
        .map(assignment => transformToCallAssignment(assignment, blockMap, personMap, templateMap))
        .filter((assignment): assignment is CallAssignment => assignment !== null)
        .sort((a, b) => a.date.localeCompare(b.date)); // Sort by date
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

  return useOnCallAssignments(startDate, endDate, options);
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
      // Fetch all required data in parallel
      const [assignments, blockMap, personMap, templateMap] = await Promise.all([
        fetchAssignments(today, today),
        fetchBlocks(today, today),
        fetchPeople(),
        fetchRotationTemplates(),
      ]);

      // Transform and filter assignments
      return assignments
        .map(assignment => transformToCallAssignment(assignment, blockMap, personMap, templateMap))
        .filter((assignment): assignment is CallAssignment => assignment !== null);
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
  return useQuery<CallAssignment[], ApiError>({
    queryKey: ['call-roster', 'person', personId, startDate, endDate] as const,
    queryFn: async () => {
      // Fetch all required data in parallel
      const [assignments, blockMap, personMap, templateMap] = await Promise.all([
        fetchAssignments(startDate, endDate),
        fetchBlocks(startDate, endDate),
        fetchPeople(),
        fetchRotationTemplates(),
      ]);

      // Transform, filter by person, and return
      return assignments
        .filter(a => a.person_id === personId)
        .map(assignment => transformToCallAssignment(assignment, blockMap, personMap, templateMap))
        .filter((assignment): assignment is CallAssignment => assignment !== null)
        .sort((a, b) => a.date.localeCompare(b.date));
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
