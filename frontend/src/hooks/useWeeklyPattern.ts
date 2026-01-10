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
 * Matches backend/app/schemas/rotationTemplate_gui.py WeeklyPatternResponse
 */
interface BackendWeeklyPattern {
  id: string;
  rotationTemplateId: string;
  dayOfWeek: number;
  timeOfDay: 'AM' | 'PM';
  activityType: string;
  linkedTemplateId: string | null;
  isProtected: boolean;
  notes: string | null;
  createdAt: string;
  updatedAt: string;
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
    const slotIndex = bp.dayOfWeek * 2 + (bp.timeOfDay === 'PM' ? 1 : 0);
    if (slotIndex >= 0 && slotIndex < 14) {
      pattern.slots[slotIndex] = {
        dayOfWeek: bp.dayOfWeek as DayOfWeek,
        timeOfDay: bp.timeOfDay as WeeklyPatternTimeOfDay,
        rotationTemplateId: bp.linkedTemplateId,
        // Preserve activityType for slots without linkedTemplateId
        activityType: bp.activityType,
        isProtected: bp.isProtected,
        notes: bp.notes,
      };
    }
  }

  // Find the latest updatedAt
  const updatedAt = backendPatterns.length > 0
    ? backendPatterns.reduce((latest, p) =>
        p.updatedAt > latest ? p.updatedAt : latest,
        backendPatterns[0].updatedAt
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
  dayOfWeek: number;
  timeOfDay: 'AM' | 'PM';
  activityType: string;
  linkedTemplateId: string | null;
  isProtected: boolean;
  notes: string | null;
}> } {
  const patterns = grid.slots
    // Include slots that have either a linked template OR an activity type
    .filter(slot => slot.rotationTemplateId !== null || slot.activityType)
    .map(slot => ({
      dayOfWeek: slot.dayOfWeek,
      timeOfDay: slot.timeOfDay,
      // Use existing activityType or default to 'scheduled' for linked templates
      activityType: slot.activityType || 'scheduled',
      linkedTemplateId: slot.rotationTemplateId,
      // Preserve existing isProtected and notes values from grid model
      isProtected: slot.isProtected ?? false,
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
  activityType: string;
  abbreviation: string | null;
  displayAbbreviation: string | null;
  fontColor: string | null;
  backgroundColor: string | null;
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
        displayAbbreviation: t.displayAbbreviation || t.abbreviation,
        backgroundColor: t.backgroundColor,
        fontColor: t.fontColor,
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
 *         templateIds: selectedTemplates.map(t => t.id),
 *         mode: 'overlay',
 *         slots,
 *         weekNumbers: [1, 2, 3], // Apply to weeks 1-3
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
      for (const templateId of variables.templateIds) {
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
