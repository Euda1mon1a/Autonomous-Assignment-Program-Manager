/**
 * Activities Hooks
 *
 * TanStack Query hooks for activity management including:
 * - CRUD operations on activities
 * - Activity requirements for rotation templates
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
  Activity,
  ActivityCategory,
  ActivityListResponse,
  ActivityCreateRequest,
  ActivityUpdateRequest,
  ActivityRequirement,
  ActivityRequirementCreateRequest,
  ActivityRequirementBulkUpdateRequest,
} from '@/types/activity';

// ============================================================================
// Query Keys
// ============================================================================

export const activityQueryKeys = {
  /** All activities */
  all: ['activities'] as const,
  /** Activities list with filters */
  list: (filters?: { category?: ActivityCategory; includeArchived?: boolean }) =>
    ['activities', 'list', filters] as const,
  /** Single activity by ID */
  detail: (id: string) => ['activities', 'detail', id] as const,
  /** Activity requirements for a rotation template */
  requirements: (templateId: string) =>
    ['activities', 'requirements', templateId] as const,
};

// ============================================================================
// Activities List Hook
// ============================================================================

/**
 * Fetches all activities with optional filtering.
 *
 * @param category - Filter by activity category
 * @param options - Additional query options including includeArchived
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useActivities('clinical');
 * const clinicalActivities = data?.activities ?? [];
 * ```
 */
export function useActivities(
  category?: ActivityCategory | '',
  options?: Omit<
    UseQueryOptions<ActivityListResponse, ApiError>,
    'queryKey' | 'queryFn'
  > & { includeArchived?: boolean }
) {
  const { includeArchived = false, ...queryOptions } = options || {};
  const filters = {
    category: category || undefined,
    includeArchived,
  };

  return useQuery<ActivityListResponse, ApiError>({
    queryKey: activityQueryKeys.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (category) params.append('category', category);
      if (includeArchived) params.append('include_archived', 'true');
      const queryString = params.toString();
      return get<ActivityListResponse>(`/activities${queryString ? `?${queryString}` : ''}`);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes - activities change rarely
    gcTime: 15 * 60 * 1000, // 15 minutes
    ...queryOptions,
  });
}

// ============================================================================
// Single Activity Hook
// ============================================================================

/**
 * Fetches a single activity by ID.
 */
export function useActivity(
  activityId: string,
  options?: Omit<UseQueryOptions<Activity, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Activity, ApiError>({
    queryKey: activityQueryKeys.detail(activityId),
    queryFn: async () => {
      return get<Activity>(`/activities/${activityId}`);
    },
    enabled: !!activityId,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

// ============================================================================
// Create Activity Mutation
// ============================================================================

/**
 * Creates a new activity.
 */
export function useCreateActivity() {
  const queryClient = useQueryClient();

  return useMutation<Activity, ApiError, ActivityCreateRequest>({
    mutationFn: async (data) => {
      // Convert camelCase to snake_case for API
      const payload = {
        name: data.name,
        code: data.code,
        displayAbbreviation: data.displayAbbreviation,
        activity_category: data.activityCategory,
        fontColor: data.fontColor,
        backgroundColor: data.backgroundColor,
        requires_supervision: data.requiresSupervision,
        isProtected: data.isProtected,
        counts_toward_clinical_hours: data.countsTowardClinicalHours,
        display_order: data.displayOrder,
      };
      return post<Activity>('/activities', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: activityQueryKeys.all,
      });
    },
  });
}

// ============================================================================
// Update Activity Mutation
// ============================================================================

/**
 * Updates an existing activity.
 */
export function useUpdateActivity() {
  const queryClient = useQueryClient();

  return useMutation<
    Activity,
    ApiError,
    { activityId: string; data: ActivityUpdateRequest }
  >({
    mutationFn: async ({ activityId, data }) => {
      // Convert camelCase to snake_case for API (only include non-undefined fields)
      const payload: Record<string, unknown> = {};
      if (data.name !== undefined) payload.name = data.name;
      if (data.code !== undefined) payload.code = data.code;
      if (data.displayAbbreviation !== undefined) payload.displayAbbreviation = data.displayAbbreviation;
      if (data.activityCategory !== undefined) payload.activity_category = data.activityCategory;
      if (data.fontColor !== undefined) payload.fontColor = data.fontColor;
      if (data.backgroundColor !== undefined) payload.backgroundColor = data.backgroundColor;
      if (data.requiresSupervision !== undefined) payload.requires_supervision = data.requiresSupervision;
      if (data.isProtected !== undefined) payload.isProtected = data.isProtected;
      if (data.countsTowardClinicalHours !== undefined) payload.counts_toward_clinical_hours = data.countsTowardClinicalHours;
      if (data.displayOrder !== undefined) payload.display_order = data.displayOrder;
      return put<Activity>(`/activities/${activityId}`, payload);
    },
    onSuccess: (_, { activityId }) => {
      queryClient.invalidateQueries({
        queryKey: activityQueryKeys.all,
      });
      queryClient.invalidateQueries({
        queryKey: activityQueryKeys.detail(activityId),
      });
    },
  });
}

// ============================================================================
// Delete Activity Mutation
// ============================================================================

/**
 * Hard deletes an activity.
 * Will fail if the activity is in use by weekly patterns or requirements.
 */
export function useDeleteActivity() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: async (activityId) => {
      await del(`/activities/${activityId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: activityQueryKeys.all,
      });
    },
  });
}

// ============================================================================
// Archive Activity Mutation
// ============================================================================

/**
 * Archives (soft deletes) an activity.
 * Archived activities are hidden from default lists but still referenced by data.
 */
export function useArchiveActivity() {
  const queryClient = useQueryClient();

  return useMutation<Activity, ApiError, string>({
    mutationFn: async (activityId) => {
      return put<Activity>(`/activities/${activityId}/archive`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: activityQueryKeys.all,
      });
    },
  });
}

// ============================================================================
// Activity Requirements Hooks
// ============================================================================

/**
 * Fetches activity requirements for a rotation template.
 */
export function useActivityRequirements(
  templateId: string,
  options?: Omit<
    UseQueryOptions<ActivityRequirement[], ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<ActivityRequirement[], ApiError>({
    queryKey: activityQueryKeys.requirements(templateId),
    queryFn: async () => {
      return get<ActivityRequirement[]>(
        `/rotation-templates/${templateId}/activity-requirements`
      );
    },
    enabled: !!templateId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  });
}

/**
 * Replaces all activity requirements for a rotation template.
 */
export function useReplaceActivityRequirements() {
  const queryClient = useQueryClient();

  return useMutation<
    ActivityRequirement[],
    ApiError,
    { templateId: string; requirements: ActivityRequirementCreateRequest[] }
  >({
    mutationFn: async ({ templateId, requirements }) => {
      // Convert camelCase to snake_case
      const payload = requirements.map((req) => ({
        activity_id: req.activityId,
        min_halfdays: req.minHalfdays ?? 0,
        max_halfdays: req.maxHalfdays ?? 14,
        target_halfdays: req.targetHalfdays,
        applicable_weeks: req.applicableWeeks,
        prefer_full_days: req.preferFullDays ?? true,
        preferred_days: req.preferredDays,
        avoid_days: req.avoidDays,
        priority: req.priority ?? 50,
      }));
      return put<ActivityRequirement[]>(
        `/rotation-templates/${templateId}/activity-requirements`,
        payload
      );
    },
    onSuccess: (_, { templateId }) => {
      queryClient.invalidateQueries({
        queryKey: activityQueryKeys.requirements(templateId),
      });
    },
  });
}

/**
 * Adds a single activity requirement to a rotation template.
 */
export function useAddActivityRequirement() {
  const queryClient = useQueryClient();

  return useMutation<
    ActivityRequirement,
    ApiError,
    { templateId: string; requirement: ActivityRequirementCreateRequest }
  >({
    mutationFn: async ({ templateId, requirement }) => {
      // Convert camelCase to snake_case
      const payload = {
        activity_id: requirement.activityId,
        min_halfdays: requirement.minHalfdays ?? 0,
        max_halfdays: requirement.maxHalfdays ?? 14,
        target_halfdays: requirement.targetHalfdays,
        applicable_weeks: requirement.applicableWeeks,
        prefer_full_days: requirement.preferFullDays ?? true,
        preferred_days: requirement.preferredDays,
        avoid_days: requirement.avoidDays,
        priority: requirement.priority ?? 50,
      };
      return post<ActivityRequirement>(
        `/rotation-templates/${templateId}/activity-requirements`,
        payload
      );
    },
    onSuccess: (_, { templateId }) => {
      queryClient.invalidateQueries({
        queryKey: activityQueryKeys.requirements(templateId),
      });
    },
  });
}

/**
 * Deletes a single activity requirement from a rotation template.
 */
export function useDeleteActivityRequirement() {
  const queryClient = useQueryClient();

  return useMutation<
    void,
    ApiError,
    { templateId: string; requirementId: string }
  >({
    mutationFn: async ({ templateId, requirementId }) => {
      await del(
        `/rotation-templates/${templateId}/activity-requirements/${requirementId}`
      );
    },
    onSuccess: (_, { templateId }) => {
      queryClient.invalidateQueries({
        queryKey: activityQueryKeys.requirements(templateId),
      });
    },
  });
}

// ============================================================================
// Utility Hooks
// ============================================================================

/**
 * Returns a map of activity IDs to activity objects for quick lookups.
 */
export function useActivitiesMap(category?: ActivityCategory | '') {
  const { data } = useActivities(category);

  return data?.activities.reduce(
    (acc, activity) => {
      acc[activity.id] = activity;
      return acc;
    },
    {} as Record<string, Activity>
  );
}

/**
 * Returns activities grouped by category.
 */
export function useActivitiesByCategory() {
  const { data, ...rest } = useActivities();

  const grouped = data?.activities.reduce(
    (acc, activity) => {
      const category = activity.activityCategory;
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(activity);
      return acc;
    },
    {} as Record<ActivityCategory, Activity[]>
  );

  return { data: grouped, ...rest };
}

/**
 * Returns only clinical activities (most common for scheduling).
 */
export function useClinicalActivities() {
  return useActivities('clinical');
}

/**
 * Returns only protected activities (like LEC).
 */
export function useProtectedActivities() {
  const { data, ...rest } = useActivities();

  const protectedActivities = data?.activities.filter((a) => a.isProtected) ?? [];

  return { data: protectedActivities, ...rest };
}
