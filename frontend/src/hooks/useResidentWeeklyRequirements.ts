/**
 * Resident Weekly Requirements Hooks
 *
 * TanStack Query hooks for managing weekly scheduling requirements
 * per rotation template. Handles CRUD operations with optimistic updates.
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
  ResidentWeeklyRequirement,
  ResidentWeeklyRequirementCreate,
  ResidentWeeklyRequirementUpdate,
} from '@/types/resident-weekly-requirement';

// ============================================================================
// Query Keys
// ============================================================================

export const weeklyRequirementsQueryKeys = {
  /** All weekly requirements */
  all: ['resident-weekly-requirements'] as const,
  /** Weekly requirement by template ID */
  byTemplate: (templateId: string) =>
    ['resident-weekly-requirements', 'by-template', templateId] as const,
  /** Single weekly requirement by ID */
  detail: (id: string) =>
    ['resident-weekly-requirements', 'detail', id] as const,
};

// ============================================================================
// Fetch Hooks
// ============================================================================

/**
 * Fetches weekly requirements for a specific rotation template.
 *
 * @param templateId - The rotation template ID
 * @param options - Additional query options
 * @returns Query result with weekly requirements data
 *
 * @example
 * ```ts
 * const { data, isLoading } = useResidentWeeklyRequirement(templateId);
 * if (data) {
 *   console.log(data.fm_clinic_min_per_week);
 * }
 * ```
 */
export function useResidentWeeklyRequirement(
  templateId: string,
  options?: Omit<
    UseQueryOptions<ResidentWeeklyRequirement | null, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<ResidentWeeklyRequirement | null, ApiError>({
    queryKey: weeklyRequirementsQueryKeys.byTemplate(templateId),
    queryFn: async () => {
      try {
        return await get<ResidentWeeklyRequirement>(
          `/resident-weekly-requirements/${templateId}`
        );
      } catch (error) {
        // Return null if not found (404) - template may not have requirements yet
        if ((error as ApiError).status === 404) {
          return null;
        }
        throw error;
      }
    },
    enabled: !!templateId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (garbage collection)
    ...options,
  });
}

/**
 * Fetches a weekly requirement by its ID.
 *
 * @param id - The weekly requirement ID
 * @param options - Additional query options
 * @returns Query result with weekly requirement data
 */
export function useResidentWeeklyRequirementById(
  id: string,
  options?: Omit<
    UseQueryOptions<ResidentWeeklyRequirement, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<ResidentWeeklyRequirement, ApiError>({
    queryKey: weeklyRequirementsQueryKeys.detail(id),
    queryFn: async () => {
      return get<ResidentWeeklyRequirement>(
        `/resident-weekly-requirements/by-id/${id}`
      );
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Creates a new weekly requirement for a rotation template.
 *
 * @example
 * ```ts
 * const createMutation = useCreateResidentWeeklyRequirement();
 *
 * createMutation.mutate({
 *   rotation_template_id: templateId,
 *   fm_clinic_min_per_week: 2,
 *   fm_clinic_max_per_week: 4,
 *   specialty_min_per_week: 1,
 *   specialty_max_per_week: 3,
 * });
 * ```
 */
export function useCreateResidentWeeklyRequirement() {
  const queryClient = useQueryClient();

  return useMutation<
    ResidentWeeklyRequirement,
    ApiError,
    ResidentWeeklyRequirementCreate
  >({
    mutationFn: async (data) => {
      return post<ResidentWeeklyRequirement>(
        '/resident-weekly-requirements',
        data
      );
    },
    onSuccess: (data) => {
      // Invalidate and refetch related queries
      queryClient.invalidateQueries({
        queryKey: weeklyRequirementsQueryKeys.all,
      });
      queryClient.invalidateQueries({
        queryKey: weeklyRequirementsQueryKeys.byTemplate(data.rotation_template_id),
      });
      // Set the data directly in cache
      queryClient.setQueryData(
        weeklyRequirementsQueryKeys.byTemplate(data.rotation_template_id),
        data
      );
    },
  });
}

/**
 * Updates an existing weekly requirement.
 *
 * @example
 * ```ts
 * const updateMutation = useUpdateResidentWeeklyRequirement();
 *
 * updateMutation.mutate({
 *   id: requirementId,
 *   templateId: templateId,
 *   data: {
 *     fm_clinic_min_per_week: 3,
 *     fm_clinic_max_per_week: 5,
 *   },
 * });
 * ```
 */
export function useUpdateResidentWeeklyRequirement() {
  const queryClient = useQueryClient();

  return useMutation<
    ResidentWeeklyRequirement,
    ApiError,
    { id: string; templateId: string; data: ResidentWeeklyRequirementUpdate }
  >({
    mutationFn: async ({ id, data }) => {
      return put<ResidentWeeklyRequirement>(
        `/resident-weekly-requirements/${id}`,
        data
      );
    },
    onSuccess: (data, { templateId }) => {
      // Invalidate and refetch related queries
      queryClient.invalidateQueries({
        queryKey: weeklyRequirementsQueryKeys.all,
      });
      queryClient.invalidateQueries({
        queryKey: weeklyRequirementsQueryKeys.byTemplate(templateId),
      });
      queryClient.invalidateQueries({
        queryKey: weeklyRequirementsQueryKeys.detail(data.id),
      });
      // Update cache directly
      queryClient.setQueryData(
        weeklyRequirementsQueryKeys.byTemplate(templateId),
        data
      );
    },
  });
}

/**
 * Deletes a weekly requirement.
 *
 * @example
 * ```ts
 * const deleteMutation = useDeleteResidentWeeklyRequirement();
 *
 * deleteMutation.mutate({
 *   id: requirementId,
 *   templateId: templateId,
 * });
 * ```
 */
export function useDeleteResidentWeeklyRequirement() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, { id: string; templateId: string }>({
    mutationFn: async ({ id }) => {
      await del(`/resident-weekly-requirements/${id}`);
    },
    onSuccess: (_, { templateId }) => {
      // Invalidate and refetch related queries
      queryClient.invalidateQueries({
        queryKey: weeklyRequirementsQueryKeys.all,
      });
      queryClient.invalidateQueries({
        queryKey: weeklyRequirementsQueryKeys.byTemplate(templateId),
      });
      // Set to null in cache (requirement deleted)
      queryClient.setQueryData(
        weeklyRequirementsQueryKeys.byTemplate(templateId),
        null
      );
    },
  });
}

/**
 * Creates or updates a weekly requirement (upsert operation).
 * If the requirement exists, it updates it; otherwise, it creates a new one.
 *
 * This is the recommended hook for the form component as it handles
 * both create and update scenarios seamlessly.
 *
 * @example
 * ```ts
 * const upsertMutation = useUpsertResidentWeeklyRequirement();
 *
 * upsertMutation.mutate({
 *   templateId: templateId,
 *   existingId: requirement?.id, // undefined if creating new
 *   data: formData,
 * });
 * ```
 */
export function useUpsertResidentWeeklyRequirement() {
  const queryClient = useQueryClient();
  const createMutation = useCreateResidentWeeklyRequirement();
  const updateMutation = useUpdateResidentWeeklyRequirement();

  return useMutation<
    ResidentWeeklyRequirement,
    ApiError,
    {
      templateId: string;
      existingId?: string;
      data: Omit<ResidentWeeklyRequirementCreate, 'rotation_template_id'>;
    }
  >({
    mutationFn: async ({ templateId, existingId, data }) => {
      if (existingId) {
        // Update existing
        return updateMutation.mutateAsync({
          id: existingId,
          templateId,
          data,
        });
      } else {
        // Create new
        return createMutation.mutateAsync({
          ...data,
          rotation_template_id: templateId,
        });
      }
    },
    onSuccess: (data) => {
      // Invalidate queries
      queryClient.invalidateQueries({
        queryKey: weeklyRequirementsQueryKeys.all,
      });
      queryClient.invalidateQueries({
        queryKey: weeklyRequirementsQueryKeys.byTemplate(data.rotation_template_id),
      });
    },
  });
}
