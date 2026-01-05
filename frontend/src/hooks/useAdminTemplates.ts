/**
 * Admin Templates Hooks
 *
 * TanStack Query hooks for admin rotation template management including
 * CRUD operations, bulk actions, and preference management.
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
  RotationTemplate,
  RotationTemplateListResponse,
  RotationPreference,
  RotationPreferenceCreate,
  TemplateCreateRequest,
  TemplateUpdateRequest,
  ActivityType,
  BatchTemplateDeleteRequest,
  BatchTemplateUpdateRequest,
  BatchTemplateResponse,
} from '@/types/admin-templates';

// ============================================================================
// Query Keys
// ============================================================================

export const adminTemplatesQueryKeys = {
  /** All templates */
  all: ['admin-templates'] as const,
  /** Templates list with filters */
  list: (filters?: { activity_type?: string }) =>
    ['admin-templates', 'list', filters] as const,
  /** Single template by ID */
  detail: (id: string) => ['admin-templates', 'detail', id] as const,
  /** Template preferences */
  preferences: (templateId: string) =>
    ['admin-templates', 'preferences', templateId] as const,
  /** Template patterns */
  patterns: (templateId: string) =>
    ['admin-templates', 'patterns', templateId] as const,
};

// ============================================================================
// Template List Hook
// ============================================================================

/**
 * Fetches all rotation templates with optional activity_type filter.
 */
export function useAdminTemplates(
  activityType?: ActivityType | '',
  options?: Omit<
    UseQueryOptions<RotationTemplateListResponse, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  const filters = activityType ? { activity_type: activityType } : undefined;

  return useQuery<RotationTemplateListResponse, ApiError>({
    queryKey: adminTemplatesQueryKeys.list(filters),
    queryFn: async () => {
      const params = activityType ? `?activity_type=${activityType}` : '';
      return get<RotationTemplateListResponse>(`/rotation-templates${params}`);
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  });
}

// ============================================================================
// Single Template Hook
// ============================================================================

/**
 * Fetches a single rotation template by ID.
 */
export function useAdminTemplate(
  templateId: string,
  options?: Omit<
    UseQueryOptions<RotationTemplate, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<RotationTemplate, ApiError>({
    queryKey: adminTemplatesQueryKeys.detail(templateId),
    queryFn: async () => {
      return get<RotationTemplate>(`/rotation-templates/${templateId}`);
    },
    enabled: !!templateId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

// ============================================================================
// Create Template Mutation
// ============================================================================

/**
 * Creates a new rotation template.
 */
export function useCreateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<RotationTemplate, ApiError, TemplateCreateRequest>({
    mutationFn: async (data) => {
      return post<RotationTemplate>('/rotation-templates', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: adminTemplatesQueryKeys.all,
      });
    },
  });
}

// ============================================================================
// Update Template Mutation
// ============================================================================

/**
 * Updates an existing rotation template.
 */
export function useUpdateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<
    RotationTemplate,
    ApiError,
    { templateId: string; data: TemplateUpdateRequest }
  >({
    mutationFn: async ({ templateId, data }) => {
      return put<RotationTemplate>(`/rotation-templates/${templateId}`, data);
    },
    onSuccess: (_, { templateId }) => {
      queryClient.invalidateQueries({
        queryKey: adminTemplatesQueryKeys.all,
      });
      queryClient.invalidateQueries({
        queryKey: adminTemplatesQueryKeys.detail(templateId),
      });
    },
  });
}

// ============================================================================
// Delete Template Mutation
// ============================================================================

/**
 * Deletes a single rotation template.
 */
export function useDeleteTemplate() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: async (templateId) => {
      await del(`/rotation-templates/${templateId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: adminTemplatesQueryKeys.all,
      });
    },
  });
}

// ============================================================================
// Bulk Delete Mutation
// ============================================================================

/**
 * Deletes multiple rotation templates atomically using batch endpoint.
 * All succeed or all fail - no partial deletions.
 */
export function useBulkDeleteTemplates() {
  const queryClient = useQueryClient();

  return useMutation<BatchTemplateResponse, ApiError, string[]>({
    mutationFn: async (templateIds) => {
      const request: BatchTemplateDeleteRequest = {
        template_ids: templateIds,
        dry_run: false,
      };
      // Use fetch with DELETE + body (axios del doesn't support body)
      // Use the same API base URL as other endpoints
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const response = await fetch(`${apiBaseUrl}/rotation-templates/batch`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(request),
      });
      if (!response.ok) {
        const error = await response.json();
        throw { status: response.status, message: error.detail?.message || 'Batch delete failed', ...error };
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: adminTemplatesQueryKeys.all,
      });
    },
  });
}

// ============================================================================
// Bulk Update Mutation
// ============================================================================

/**
 * Updates multiple rotation templates atomically using batch endpoint.
 * All succeed or all fail - no partial updates.
 * All templates receive the same update values.
 */
export function useBulkUpdateTemplates() {
  const queryClient = useQueryClient();

  return useMutation<
    BatchTemplateResponse,
    ApiError,
    { templateIds: string[]; updates: TemplateUpdateRequest }
  >({
    mutationFn: async ({ templateIds, updates }) => {
      const request: BatchTemplateUpdateRequest = {
        templates: templateIds.map((id) => ({
          template_id: id,
          updates,
        })),
        dry_run: false,
      };
      return put<BatchTemplateResponse>('/rotation-templates/batch', request);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: adminTemplatesQueryKeys.all,
      });
    },
  });
}

// ============================================================================
// Preferences Hooks
// ============================================================================

/**
 * Fetches preferences for a rotation template.
 */
export function useTemplatePreferences(
  templateId: string,
  options?: Omit<
    UseQueryOptions<RotationPreference[], ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<RotationPreference[], ApiError>({
    queryKey: adminTemplatesQueryKeys.preferences(templateId),
    queryFn: async () => {
      return get<RotationPreference[]>(
        `/rotation-templates/${templateId}/preferences`
      );
    },
    enabled: !!templateId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Replaces all preferences for a rotation template.
 */
export function useReplaceTemplatePreferences() {
  const queryClient = useQueryClient();

  return useMutation<
    RotationPreference[],
    ApiError,
    { templateId: string; preferences: RotationPreferenceCreate[] }
  >({
    mutationFn: async ({ templateId, preferences }) => {
      return put<RotationPreference[]>(
        `/rotation-templates/${templateId}/preferences`,
        preferences
      );
    },
    onSuccess: (_, { templateId }) => {
      queryClient.invalidateQueries({
        queryKey: adminTemplatesQueryKeys.preferences(templateId),
      });
    },
  });
}

// ============================================================================
// Utility Hooks
// ============================================================================

/**
 * Returns a map of template IDs to template objects for quick lookups.
 */
export function useTemplatesMap(activityType?: ActivityType | '') {
  const { data } = useAdminTemplates(activityType);

  return data?.items.reduce(
    (acc, template) => {
      acc[template.id] = template;
      return acc;
    },
    {} as Record<string, RotationTemplate>
  );
}
