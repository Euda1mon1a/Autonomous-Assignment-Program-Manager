/**
 * Weekly Pattern Management Hooks
 *
 * TanStack Query hooks for fetching and updating weekly rotation patterns.
 * These patterns define recurring weekly schedules for rotation templates.
 *
 * Uses real API endpoints:
 * - GET /api/rotation-templates/{templateId}/patterns
 * - PUT /api/rotation-templates/{templateId}/patterns
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { get, put } from '@/lib/api';
import type { ApiError } from '@/lib/api';
import type {
  WeeklyPatternResponse,
  WeeklyPatternUpdateRequest,
  RotationTemplateRef,
  WeeklyPatternGrid,
  DayOfWeek,
  WeeklyPatternTimeOfDay,
  BatchPatternUpdateRequest,
  BatchPatternUpdateResponse,
} from '@/types/weekly-pattern';
import { createEmptyPattern, ensureCompletePattern } from '@/types/weekly-pattern';

// ============================================================================
// Query Keys
// ============================================================================

export const weeklyPatternQueryKeys = {
  /** All weekly patterns */
  all: ['weekly-patterns'] as const,
  /** Single pattern by template ID */
  pattern: (templateId: string) => ['weekly-patterns', templateId] as const,
  /** Available rotation templates for selection */
  templates: () => ['weekly-patterns', 'templates'] as const,
};

// ============================================================================
// API Response Types (from backend)
// ============================================================================

/**
 * Backend weekly pattern response structure.
 * Matches backend/app/schemas/rotation_template_gui.py WeeklyPatternResponse
 */
interface BackendWeeklyPattern {
  id: string;
  rotation_template_id: string;
  day_of_week: number;
  time_of_day: 'AM' | 'PM';
  activity_type: string;
  linked_template_id: string | null;
  is_protected: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Convert backend patterns array to frontend WeeklyPatternGrid format.
 */
function convertBackendToGrid(
  templateId: string,
  backendPatterns: BackendWeeklyPattern[]
): WeeklyPatternResponse {
  const pattern = createEmptyPattern();

  // Map backend patterns to frontend slots
  for (const bp of backendPatterns) {
    // Find the slot index: day * 2 + (PM ? 1 : 0)
    const slotIndex = bp.day_of_week * 2 + (bp.time_of_day === 'PM' ? 1 : 0);
    if (slotIndex >= 0 && slotIndex < 14) {
      pattern.slots[slotIndex] = {
        dayOfWeek: bp.day_of_week as DayOfWeek,
        timeOfDay: bp.time_of_day as WeeklyPatternTimeOfDay,
        rotationTemplateId: bp.linked_template_id,
        // Preserve activity_type for slots without linked_template_id
        activityType: bp.activity_type,
        isProtected: bp.is_protected,
        notes: bp.notes,
      };
    }
  }

  // Find the latest updated_at
  const updatedAt = backendPatterns.length > 0
    ? backendPatterns.reduce((latest, p) =>
        p.updated_at > latest ? p.updated_at : latest,
        backendPatterns[0].updated_at
      )
    : new Date().toISOString();

  return {
    templateId,
    pattern: ensureCompletePattern(pattern),
    updatedAt,
  };
}

/**
 * Convert frontend grid to backend format for PUT request.
 */
function convertGridToBackend(
  grid: WeeklyPatternGrid
): { patterns: Array<{
  day_of_week: number;
  time_of_day: 'AM' | 'PM';
  activity_type: string;
  linked_template_id: string | null;
  is_protected: boolean;
  notes: string | null;
}> } {
  const patterns = grid.slots
    // Include slots that have either a linked template OR an activity type
    .filter(slot => slot.rotationTemplateId !== null || slot.activityType)
    .map(slot => ({
      day_of_week: slot.dayOfWeek,
      time_of_day: slot.timeOfDay,
      // Use existing activity_type or default to 'scheduled' for linked templates
      activity_type: slot.activityType || 'scheduled',
      linked_template_id: slot.rotationTemplateId,
      // Preserve existing is_protected and notes values from grid model
      is_protected: slot.isProtected ?? false,
      notes: slot.notes ?? null,
    }));

  return { patterns };
}

// ============================================================================
// Hooks
// ============================================================================

/**
 * Fetches the weekly pattern for a specific rotation template.
 *
 * Returns the current weekly schedule pattern showing which rotations
 * are assigned to each day/time slot. Used by the WeeklyGridEditor
 * component for display and editing.
 *
 * @param templateId - UUID of the rotation template
 * @param options - Optional React Query configuration
 * @returns Query result with weekly pattern data
 *
 * @example
 * ```tsx
 * function PatternEditor({ templateId }: Props) {
 *   const { data, isLoading, error } = useWeeklyPattern(templateId);
 *
 *   if (isLoading) return <Skeleton />;
 *   if (error) return <ErrorAlert error={error} />;
 *
 *   return (
 *     <WeeklyGridEditor
 *       templateId={templateId}
 *       pattern={data.pattern}
 *       onChange={handleChange}
 *     />
 *   );
 * }
 * ```
 */
export function useWeeklyPattern(
  templateId: string,
  options?: Omit<UseQueryOptions<WeeklyPatternResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<WeeklyPatternResponse, ApiError>({
    queryKey: weeklyPatternQueryKeys.pattern(templateId),
    queryFn: async () => {
      // Fetch patterns from API
      const backendPatterns = await get<BackendWeeklyPattern[]>(
        `/rotation-templates/${templateId}/patterns`
      );

      // Convert backend format to frontend grid format
      return convertBackendToGrid(templateId, backendPatterns);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!templateId,
    ...options,
  });
}

/**
 * Updates the weekly pattern for a rotation template.
 *
 * Persists changes made in the WeeklyGridEditor to the backend.
 * Automatically invalidates related queries on success.
 *
 * @returns Mutation object for updating patterns
 *
 * @example
 * ```tsx
 * function PatternEditor({ templateId }: Props) {
 *   const { mutate, isPending } = useUpdateWeeklyPattern();
 *
 *   const handleSave = (pattern: WeeklyPatternGrid) => {
 *     mutate(
 *       { templateId, pattern },
 *       {
 *         onSuccess: () => toast.success('Pattern saved'),
 *         onError: (error) => toast.error(`Failed: ${error.message}`),
 *       }
 *     );
 *   };
 *
 *   return <WeeklyGridEditor onSave={handleSave} saving={isPending} />;
 * }
 * ```
 */
export function useUpdateWeeklyPattern() {
  const queryClient = useQueryClient();

  return useMutation<WeeklyPatternResponse, ApiError, WeeklyPatternUpdateRequest>({
    mutationFn: async (request) => {
      // Convert frontend grid format to backend format
      const backendPayload = convertGridToBackend(request.pattern);

      // PUT to update patterns (atomic replace)
      const updatedPatterns = await put<BackendWeeklyPattern[]>(
        `/rotation-templates/${request.templateId}/patterns`,
        backendPayload
      );

      // Convert response back to frontend format
      return convertBackendToGrid(request.templateId, updatedPatterns);
    },
    onSuccess: (data, variables) => {
      // Invalidate the specific pattern query
      queryClient.invalidateQueries({
        queryKey: weeklyPatternQueryKeys.pattern(variables.templateId),
      });
      // Also invalidate rotation templates as pattern changes may affect them
      queryClient.invalidateQueries({
        queryKey: ['rotation-templates'],
      });
    },
  });
}

/**
 * Fetches available rotation templates for the pattern selector.
 *
 * Returns a list of rotation templates that can be assigned to slots
 * in the weekly pattern grid. Each template includes display information
 * like colors and abbreviations.
 *
 * @param options - Optional React Query configuration
 * @returns Query result with rotation template list
 *
 * @example
 * ```tsx
 * function TemplateSelector({ onSelect }: Props) {
 *   const { data, isLoading } = useAvailableTemplates();
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <select onChange={(e) => onSelect(e.target.value)}>
 *       <option value="">Select rotation...</option>
 *       {data?.map((template) => (
 *         <option key={template.id} value={template.id}>
 *           {template.name}
 *         </option>
 *       ))}
 *     </select>
 *   );
 * }
 * ```
 */
/**
 * Backend rotation template structure from API.
 */
interface BackendRotationTemplate {
  id: string;
  name: string;
  activity_type: string;
  abbreviation: string | null;
  display_abbreviation: string | null;
  font_color: string | null;
  background_color: string | null;
  // ... other fields not needed for pattern editor
}

/**
 * Response wrapper for template list.
 */
interface TemplateListResponse {
  items: BackendRotationTemplate[];
  total: number;
}

export function useAvailableTemplates(
  options?: Omit<UseQueryOptions<RotationTemplateRef[], ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<RotationTemplateRef[], ApiError>({
    queryKey: weeklyPatternQueryKeys.templates(),
    queryFn: async () => {
      // Fetch templates from API
      const response = await get<TemplateListResponse>('/rotation-templates');

      // Convert to frontend format
      return response.items.map((t) => ({
        id: t.id,
        name: t.name,
        displayAbbreviation: t.display_abbreviation || t.abbreviation,
        backgroundColor: t.background_color,
        fontColor: t.font_color,
      }));
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}

/**
 * Bulk update weekly patterns across multiple rotation templates.
 *
 * Supports two modes:
 * - **overlay**: Merges provided slots with existing patterns
 * - **replace**: Replaces entire patterns with provided slots
 *
 * Can target specific weeks (1-4) or apply to all weeks.
 *
 * @returns Mutation object for bulk updating patterns
 *
 * @example
 * ```tsx
 * function BulkPatternEditor({ selectedTemplates }: Props) {
 *   const { mutate, isPending } = useBulkUpdateWeeklyPatterns();
 *
 *   const handleApply = (slots: BatchPatternSlot[]) => {
 *     mutate(
 *       {
 *         template_ids: selectedTemplates.map(t => t.id),
 *         mode: 'overlay',
 *         slots,
 *         week_numbers: [1, 2, 3], // Apply to weeks 1-3
 *       },
 *       {
 *         onSuccess: (result) => {
 *           toast.success(`Updated ${result.successful} templates`);
 *         },
 *         onError: (error) => toast.error(`Failed: ${error.message}`),
 *       }
 *     );
 *   };
 *
 *   return <PatternGrid onApply={handleApply} saving={isPending} />;
 * }
 * ```
 */
export function useBulkUpdateWeeklyPatterns() {
  const queryClient = useQueryClient();

  return useMutation<BatchPatternUpdateResponse, ApiError, BatchPatternUpdateRequest>({
    mutationFn: async (request) => {
      const response = await put<BatchPatternUpdateResponse>(
        '/rotation-templates/batch/patterns',
        request
      );
      return response;
    },
    onSuccess: (data, variables) => {
      // Invalidate patterns for all affected templates
      for (const templateId of variables.template_ids) {
        queryClient.invalidateQueries({
          queryKey: weeklyPatternQueryKeys.pattern(templateId),
        });
      }
      // Also invalidate the templates list as patterns affect template display
      queryClient.invalidateQueries({
        queryKey: ['rotation-templates'],
      });
    },
  });
}
