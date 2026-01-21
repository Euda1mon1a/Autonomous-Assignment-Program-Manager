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
  BatchTemplateCreateRequest,
  BatchArchiveRequest,
  BatchRestoreRequest,
  ConflictCheckRequest,
  ConflictCheckResponse,
  TemplateExportRequest,
  TemplateExportResponse,
} from '@/types/admin-templates';

// ============================================================================
// Query Keys
// ============================================================================

export const adminTemplatesQueryKeys = {
  /** All templates */
  all: ['admin-templates'] as const,
  /** Templates list with filters */
  list: (filters?: { activityType?: string }) =>
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
 * Fetches all rotation templates with optional activityType filter.
 */
export function useAdminTemplates(
  activityType?: ActivityType | '',
  options?: Omit<
    UseQueryOptions<RotationTemplateListResponse, ApiError>,
    'queryKey' | 'queryFn'
  > & { includeArchived?: boolean }
) {
  const { includeArchived = false, ...queryOptions } = options || {};
  const filters = activityType ? { activityType: activityType } : undefined;

  return useQuery<RotationTemplateListResponse, ApiError>({
    queryKey: adminTemplatesQueryKeys.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (activityType) params.append('activity_type', activityType);
      if (includeArchived) params.append('include_archived', 'true');
      const queryString = params.toString();
      return get<RotationTemplateListResponse>(`/rotation-templates${queryString ? `?${queryString}` : ''}`);
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...queryOptions,
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
        templateIds: templateIds,
        dryRun: false,
      };
      // Use axios del with data - axios converts camelCase to snake_case automatically
      return del<BatchTemplateResponse>('/rotation-templates/batch', { data: request });
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
          templateId: id,
          updates,
        })),
        dryRun: false,
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

// ============================================================================
// Bulk Create Mutation
// ============================================================================

/**
 * Creates multiple rotation templates atomically using batch endpoint.
 * All succeed or all fail - no partial creates.
 */
export function useBulkCreateTemplates() {
  const queryClient = useQueryClient();

  return useMutation<BatchTemplateResponse, ApiError, TemplateCreateRequest[]>({
    mutationFn: async (templates) => {
      const request: BatchTemplateCreateRequest = {
        templates,
        dryRun: false,
      };
      return post<BatchTemplateResponse>('/rotation-templates/batch', request);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: adminTemplatesQueryKeys.all,
      });
    },
  });
}

// ============================================================================
// Conflict Check Hook
// ============================================================================

/**
 * Checks for conflicts before performing batch operations.
 */
export function useCheckConflicts() {
  return useMutation<ConflictCheckResponse, ApiError, ConflictCheckRequest>({
    mutationFn: async (request) => {
      return post<ConflictCheckResponse>('/rotation-templates/batch/conflicts', request);
    },
  });
}

// ============================================================================
// Export Templates Hook
// ============================================================================

/**
 * Exports selected templates with their patterns and preferences.
 */
export function useExportTemplates() {
  return useMutation<TemplateExportResponse, ApiError, TemplateExportRequest>({
    mutationFn: async (request) => {
      return post<TemplateExportResponse>('/rotation-templates/export', request);
    },
  });
}

// ============================================================================
// Archive/Restore Hooks
// ============================================================================

/**
 * Archives a single rotation template (soft delete).
 */
export function useArchiveTemplate() {
  const queryClient = useQueryClient();

  return useMutation<RotationTemplate, ApiError, string>({
    mutationFn: async (templateId) => {
      return put<RotationTemplate>(`/rotation-templates/${templateId}/archive`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: adminTemplatesQueryKeys.all,
      });
    },
  });
}

/**
 * Restores a single archived rotation template.
 */
export function useRestoreTemplate() {
  const queryClient = useQueryClient();

  return useMutation<RotationTemplate, ApiError, string>({
    mutationFn: async (templateId) => {
      return put<RotationTemplate>(`/rotation-templates/${templateId}/restore`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: adminTemplatesQueryKeys.all,
      });
    },
  });
}

/**
 * Archives multiple rotation templates atomically using batch endpoint.
 * All succeed or all fail - no partial archives.
 */
export function useBulkArchiveTemplates() {
  const queryClient = useQueryClient();

  return useMutation<BatchTemplateResponse, ApiError, string[]>({
    mutationFn: async (templateIds) => {
      const request: BatchArchiveRequest = {
        templateIds: templateIds,
        dryRun: false,
      };
      return put<BatchTemplateResponse>('/rotation-templates/batch/archive', request);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: adminTemplatesQueryKeys.all,
      });
    },
  });
}

/**
 * Restores multiple archived rotation templates atomically using batch endpoint.
 * All succeed or all fail - no partial restores.
 */
export function useBulkRestoreTemplates() {
  const queryClient = useQueryClient();

  return useMutation<BatchTemplateResponse, ApiError, string[]>({
    mutationFn: async (templateIds) => {
      const request: BatchRestoreRequest = {
        templateIds: templateIds,
        dryRun: false,
      };
      return put<BatchTemplateResponse>('/rotation-templates/batch/restore', request);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: adminTemplatesQueryKeys.all,
      });
    },
  });
}

// ============================================================================
// Inline Update Hook
// ============================================================================

/**
 * Updates a single field on a template (for inline editing).
 * Uses batch endpoint with single item for consistency.
 */
export function useInlineUpdateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<
    BatchTemplateResponse,
    ApiError,
    { templateId: string; field: string; value: unknown }
  >({
    mutationFn: async ({ templateId, field, value }) => {
      const request: BatchTemplateUpdateRequest = {
        templates: [
          {
            templateId: templateId,
            updates: { [field]: value } as TemplateUpdateRequest,
          },
        ],
        dryRun: false,
      };
      return put<BatchTemplateResponse>('/rotation-templates/batch', request);
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
