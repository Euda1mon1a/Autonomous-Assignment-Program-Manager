/**
 * Faculty Activities Hooks
 *
 * TanStack Query hooks for faculty weekly activity management including:
 * - Template CRUD (default weekly patterns)
 * - Override CRUD (week-specific exceptions)
 * - Effective week view (merged template + overrides)
 * - Permitted activities by role
 * - Faculty matrix view
 */
import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryOptions,
} from '@tanstack/react-query';
import { get, post, put, del } from '@/lib/api';
import type { ApiError } from '@/lib/api';
import type {
  FacultyRole,
  FacultyTemplateResponse,
  FacultyTemplateUpdateRequest,
  FacultyTemplateSlotRequest,
  FacultyTemplateSlot,
  FacultyOverridesResponse,
  FacultyOverrideRequest,
  FacultyOverride,
  EffectiveWeekResponse,
  PermittedActivitiesResponse,
  FacultyMatrixResponse,
} from '@/types/faculty-activity';

// ============================================================================
// Query Keys
// ============================================================================

export const facultyActivityQueryKeys = {
  /** All faculty activity queries */
  all: ['facultyActivities'] as const,

  /** Template queries */
  templates: () => [...facultyActivityQueryKeys.all, 'templates'] as const,
  template: (personId: string, weekNumber?: number) =>
    [...facultyActivityQueryKeys.templates(), personId, weekNumber] as const,

  /** Override queries */
  overrides: () => [...facultyActivityQueryKeys.all, 'overrides'] as const,
  overridesByWeek: (personId: string, weekStart: string) =>
    [...facultyActivityQueryKeys.overrides(), personId, weekStart] as const,

  /** Effective week queries */
  effective: () => [...facultyActivityQueryKeys.all, 'effective'] as const,
  effectiveWeek: (personId: string, weekStart: string, weekNumber?: number) =>
    [...facultyActivityQueryKeys.effective(), personId, weekStart, weekNumber] as const,

  /** Permission queries */
  permissions: () => [...facultyActivityQueryKeys.all, 'permissions'] as const,
  permittedActivities: (role: FacultyRole) =>
    [...facultyActivityQueryKeys.permissions(), role] as const,

  /** Matrix queries */
  matrix: () => [...facultyActivityQueryKeys.all, 'matrix'] as const,
  matrixRange: (startDate: string, endDate: string, includeAdjunct?: boolean) =>
    [...facultyActivityQueryKeys.matrix(), startDate, endDate, includeAdjunct] as const,
};

// ============================================================================
// Template Hooks
// ============================================================================

/**
 * Fetches the weekly template for a faculty member.
 *
 * @param personId - Faculty member's UUID
 * @param weekNumber - Optional week filter (1-4)
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useFacultyTemplate(facultyId);
 * const slots = data?.slots ?? [];
 * ```
 */
export function useFacultyTemplate(
  personId: string,
  weekNumber?: number,
  options?: Omit<UseQueryOptions<FacultyTemplateResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<FacultyTemplateResponse, ApiError>({
    queryKey: facultyActivityQueryKeys.template(personId, weekNumber),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (weekNumber) params.append('week_number', weekNumber.toString());
      const queryString = params.toString();
      return get<FacultyTemplateResponse>(
        `/faculty/${personId}/weekly-template${queryString ? `?${queryString}` : ''}`
      );
    },
    enabled: !!personId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  });
}

/**
 * Updates the weekly template for a faculty member (bulk).
 *
 * @example
 * ```tsx
 * const mutation = useUpdateFacultyTemplate();
 *
 * mutation.mutate({
 *   personId: facultyId,
 *   slots: [{ dayOfWeek: 1, timeOfDay: 'AM', activityId: activityUUID }],
 *   clearExisting: false,
 * });
 * ```
 */
export function useUpdateFacultyTemplate() {
  const queryClient = useQueryClient();

  return useMutation<
    FacultyTemplateResponse,
    ApiError,
    { personId: string } & FacultyTemplateUpdateRequest
  >({
    mutationFn: async ({ personId, ...request }) => {
      return put<FacultyTemplateResponse>(
        `/faculty/${personId}/weekly-template`,
        {
          slots: request.slots,
          clear_existing: request.clearExisting ?? false,
        }
      );
    },
    onSuccess: (data, variables) => {
      // Invalidate template queries
      queryClient.invalidateQueries({
        queryKey: facultyActivityQueryKeys.templates(),
      });
      // Invalidate effective week queries for this person
      queryClient.invalidateQueries({
        queryKey: [...facultyActivityQueryKeys.effective(), variables.personId],
      });
    },
  });
}

/**
 * Creates or updates a single template slot.
 */
export function useUpsertTemplateSlot() {
  const queryClient = useQueryClient();

  return useMutation<
    FacultyTemplateSlot,
    ApiError,
    { personId: string; slot: FacultyTemplateSlotRequest }
  >({
    mutationFn: async ({ personId, slot }) => {
      return post<FacultyTemplateSlot>(
        `/faculty/${personId}/weekly-template/slots`,
        {
          day_of_week: slot.dayOfWeek,
          time_of_day: slot.timeOfDay,
          week_number: slot.weekNumber,
          activity_id: slot.activityId,
          is_locked: slot.isLocked ?? false,
          priority: slot.priority ?? 50,
          notes: slot.notes,
        }
      );
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: facultyActivityQueryKeys.templates(),
      });
      queryClient.invalidateQueries({
        queryKey: [...facultyActivityQueryKeys.effective(), variables.personId],
      });
    },
  });
}

/**
 * Deletes a specific template slot.
 */
export function useDeleteTemplateSlot() {
  const queryClient = useQueryClient();

  return useMutation<
    void,
    ApiError,
    {
      personId: string;
      dayOfWeek: number;
      timeOfDay: string;
      weekNumber?: number | null;
    }
  >({
    mutationFn: async ({ personId, dayOfWeek, timeOfDay, weekNumber }) => {
      const params = new URLSearchParams();
      params.append('day_of_week', dayOfWeek.toString());
      params.append('time_of_day', timeOfDay);
      if (weekNumber) params.append('week_number', weekNumber.toString());
      await del(`/faculty/${personId}/weekly-template/slots?${params.toString()}`);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: facultyActivityQueryKeys.templates(),
      });
      queryClient.invalidateQueries({
        queryKey: [...facultyActivityQueryKeys.effective(), variables.personId],
      });
    },
  });
}

// ============================================================================
// Override Hooks
// ============================================================================

/**
 * Fetches overrides for a faculty member for a specific week.
 *
 * @param personId - Faculty member's UUID
 * @param weekStart - Monday of the week (YYYY-MM-DD)
 */
export function useFacultyOverrides(
  personId: string,
  weekStart: string,
  options?: Omit<UseQueryOptions<FacultyOverridesResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<FacultyOverridesResponse, ApiError>({
    queryKey: facultyActivityQueryKeys.overridesByWeek(personId, weekStart),
    queryFn: async () => {
      return get<FacultyOverridesResponse>(
        `/faculty/${personId}/weekly-overrides?week_start=${weekStart}`
      );
    },
    enabled: !!personId && !!weekStart,
    staleTime: 1 * 60 * 1000, // 1 minute - overrides change more often
    ...options,
  });
}

/**
 * Creates or replaces an override for a specific slot and week.
 */
export function useCreateFacultyOverride() {
  const queryClient = useQueryClient();

  return useMutation<
    FacultyOverride,
    ApiError,
    { personId: string; override: FacultyOverrideRequest }
  >({
    mutationFn: async ({ personId, override }) => {
      return post<FacultyOverride>(
        `/faculty/${personId}/weekly-overrides`,
        {
          effective_date: override.effectiveDate,
          day_of_week: override.dayOfWeek,
          time_of_day: override.timeOfDay,
          activity_id: override.activityId,
          is_locked: override.isLocked ?? false,
          override_reason: override.overrideReason,
        }
      );
    },
    onSuccess: (data, variables) => {
      // Invalidate override queries for this person/week
      queryClient.invalidateQueries({
        queryKey: facultyActivityQueryKeys.overridesByWeek(
          variables.personId,
          variables.override.effectiveDate
        ),
      });
      // Invalidate effective week queries
      queryClient.invalidateQueries({
        queryKey: [...facultyActivityQueryKeys.effective(), variables.personId],
      });
      // Invalidate matrix queries
      queryClient.invalidateQueries({
        queryKey: facultyActivityQueryKeys.matrix(),
      });
    },
  });
}

/**
 * Deletes an override by ID.
 */
export function useDeleteFacultyOverride() {
  const queryClient = useQueryClient();

  return useMutation<
    void,
    ApiError,
    { personId: string; overrideId: string; weekStart: string }
  >({
    mutationFn: async ({ personId, overrideId }) => {
      await del(`/faculty/${personId}/weekly-overrides/${overrideId}`);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: facultyActivityQueryKeys.overridesByWeek(
          variables.personId,
          variables.weekStart
        ),
      });
      queryClient.invalidateQueries({
        queryKey: [...facultyActivityQueryKeys.effective(), variables.personId],
      });
      queryClient.invalidateQueries({
        queryKey: facultyActivityQueryKeys.matrix(),
      });
    },
  });
}

// ============================================================================
// Effective Week Hook
// ============================================================================

/**
 * Fetches the effective schedule for a faculty member for a specific week.
 * Merges template slots with overrides (overrides take precedence).
 *
 * @param personId - Faculty member's UUID
 * @param weekStart - Monday of the week (YYYY-MM-DD)
 * @param weekNumber - Week number within block (1-4)
 */
export function useEffectiveFacultyWeek(
  personId: string,
  weekStart: string,
  weekNumber: number = 1,
  options?: Omit<UseQueryOptions<EffectiveWeekResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<EffectiveWeekResponse, ApiError>({
    queryKey: facultyActivityQueryKeys.effectiveWeek(personId, weekStart, weekNumber),
    queryFn: async () => {
      return get<EffectiveWeekResponse>(
        `/faculty/${personId}/weekly-template/effective?week_start=${weekStart}&week_number=${weekNumber}`
      );
    },
    enabled: !!personId && !!weekStart,
    staleTime: 1 * 60 * 1000, // 1 minute
    ...options,
  });
}

// ============================================================================
// Permission Hook
// ============================================================================

/**
 * Fetches activities permitted for a faculty role.
 *
 * @param role - Faculty role (pd, apd, oic, etc.)
 *
 * @example
 * ```tsx
 * const { data } = usePermittedActivities('apd');
 * const activities = data?.activities ?? [];
 * const defaults = data?.defaultActivities ?? [];
 * ```
 */
export function usePermittedActivities(
  role: FacultyRole,
  options?: Omit<UseQueryOptions<PermittedActivitiesResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<PermittedActivitiesResponse, ApiError>({
    queryKey: facultyActivityQueryKeys.permittedActivities(role),
    queryFn: async () => {
      return get<PermittedActivitiesResponse>(
        `/faculty/activities/permitted?role=${role}`
      );
    },
    enabled: !!role,
    staleTime: 10 * 60 * 1000, // 10 minutes - permissions change rarely
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

// ============================================================================
// Matrix Hook
// ============================================================================

/**
 * Fetches the faculty activity matrix for a date range.
 * Shows all faculty and their effective schedules for each week.
 *
 * @param startDate - Start date (YYYY-MM-DD)
 * @param endDate - End date (YYYY-MM-DD)
 * @param includeAdjunct - Include adjunct faculty (default: false)
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useFacultyMatrix('2026-01-06', '2026-02-02');
 * const matrix = data?.faculty ?? [];
 * ```
 */
export function useFacultyMatrix(
  startDate: string,
  endDate: string,
  includeAdjunct: boolean = false,
  options?: Omit<UseQueryOptions<FacultyMatrixResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<FacultyMatrixResponse, ApiError>({
    queryKey: facultyActivityQueryKeys.matrixRange(startDate, endDate, includeAdjunct),
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append('start_date', startDate);
      params.append('end_date', endDate);
      if (includeAdjunct) params.append('include_adjunct', 'true');
      return get<FacultyMatrixResponse>(`/faculty/activities/matrix?${params.toString()}`);
    },
    enabled: !!startDate && !!endDate,
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  });
}

// ============================================================================
// Utility Hooks
// ============================================================================

/**
 * Invalidates all faculty activity queries.
 * Useful after bulk operations.
 */
export function useInvalidateFacultyActivities() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({
      queryKey: facultyActivityQueryKeys.all,
    });
  };
}
