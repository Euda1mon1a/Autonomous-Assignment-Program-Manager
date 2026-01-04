/**
 * Weekly Pattern Management Hooks
 *
 * TanStack Query hooks for fetching and updating weekly rotation patterns.
 * These patterns define recurring weekly schedules for rotation templates.
 *
 * NOTE: API endpoints do not exist yet. These hooks use mock data for
 * frontend development. Update to real API calls when backend is ready.
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import type { ApiError } from '@/lib/api';
import type {
  WeeklyPatternResponse,
  WeeklyPatternUpdateRequest,
  RotationTemplateRef,
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
// Mock Data (Remove when API is ready)
// ============================================================================

/**
 * Mock rotation templates for development.
 * Replace with actual API call when backend endpoint exists.
 */
const MOCK_TEMPLATES: RotationTemplateRef[] = [
  {
    id: 'clinic-001',
    name: 'Clinic',
    displayAbbreviation: 'C',
    backgroundColor: 'bg-clinic-light',
    fontColor: 'text-clinic-dark',
  },
  {
    id: 'inpatient-001',
    name: 'Inpatient Service',
    displayAbbreviation: 'IP',
    backgroundColor: 'bg-inpatient-light',
    fontColor: 'text-inpatient-dark',
  },
  {
    id: 'call-001',
    name: 'Call',
    displayAbbreviation: 'Call',
    backgroundColor: 'bg-call-light',
    fontColor: 'text-call-dark',
  },
  {
    id: 'fmit-001',
    name: 'FMIT',
    displayAbbreviation: 'FMIT',
    backgroundColor: 'bg-purple-100',
    fontColor: 'text-purple-800',
  },
  {
    id: 'procedure-001',
    name: 'Procedure Clinic',
    displayAbbreviation: 'Proc',
    backgroundColor: 'bg-amber-100',
    fontColor: 'text-amber-800',
  },
  {
    id: 'conference-001',
    name: 'Conference',
    displayAbbreviation: 'Conf',
    backgroundColor: 'bg-cyan-100',
    fontColor: 'text-cyan-800',
  },
];

/**
 * Mock pattern data for development.
 * Replace with actual API call when backend endpoint exists.
 *
 * Day numbering matches backend: 0=Sunday, 1=Monday, ..., 6=Saturday
 * Slots are ordered: [Sun AM, Sun PM, Mon AM, Mon PM, ..., Sat AM, Sat PM]
 */
function getMockPattern(templateId: string): WeeklyPatternResponse {
  const pattern = createEmptyPattern();

  // Add some sample assignments for visual testing
  // Pattern array: [0]=Sun AM, [1]=Sun PM, [2]=Mon AM, [3]=Mon PM, etc.
  if (templateId) {
    // Sunday: Off (null) - slots[0], slots[1]
    // Monday AM/PM: Clinic - slots[2], slots[3]
    pattern.slots[2].rotationTemplateId = 'clinic-001';
    pattern.slots[3].rotationTemplateId = 'clinic-001';
    // Tuesday AM: Inpatient, PM: Conference - slots[4], slots[5]
    pattern.slots[4].rotationTemplateId = 'inpatient-001';
    pattern.slots[5].rotationTemplateId = 'conference-001';
    // Wednesday AM/PM: FMIT - slots[6], slots[7]
    pattern.slots[6].rotationTemplateId = 'fmit-001';
    pattern.slots[7].rotationTemplateId = 'fmit-001';
    // Thursday AM: Procedure, PM: Clinic - slots[8], slots[9]
    pattern.slots[8].rotationTemplateId = 'procedure-001';
    pattern.slots[9].rotationTemplateId = 'clinic-001';
    // Friday AM/PM: Clinic - slots[10], slots[11]
    pattern.slots[10].rotationTemplateId = 'clinic-001';
    pattern.slots[11].rotationTemplateId = 'clinic-001';
    // Saturday: Off (null) - slots[12], slots[13]
  }

  return {
    templateId,
    pattern: ensureCompletePattern(pattern), // Ensure all 14 slots present
    updatedAt: new Date().toISOString(),
  };
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
      // TODO: Replace with actual API call when backend endpoint exists
      // return get<WeeklyPatternResponse>(`/rotation-templates/${templateId}/weekly-pattern`);

      // Mock implementation for frontend development
      await new Promise((resolve) => setTimeout(resolve, 300)); // Simulate network delay
      return getMockPattern(templateId);
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
      // TODO: Replace with actual API call when backend endpoint exists
      // return put<WeeklyPatternResponse>(
      //   `/rotation-templates/${request.templateId}/weekly-pattern`,
      //   request.pattern
      // );

      // Mock implementation for frontend development
      await new Promise((resolve) => setTimeout(resolve, 500)); // Simulate network delay
      return {
        templateId: request.templateId,
        pattern: request.pattern,
        updatedAt: new Date().toISOString(),
      };
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
export function useAvailableTemplates(
  options?: Omit<UseQueryOptions<RotationTemplateRef[], ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<RotationTemplateRef[], ApiError>({
    queryKey: weeklyPatternQueryKeys.templates(),
    queryFn: async () => {
      // TODO: Replace with actual API call when backend endpoint exists
      // const response = await get<ListResponse<RotationTemplate>>('/rotation-templates');
      // return response.items.map((t) => ({
      //   id: t.id,
      //   name: t.name,
      //   displayAbbreviation: t.display_abbreviation,
      //   backgroundColor: t.background_color,
      //   fontColor: t.font_color,
      // }));

      // Mock implementation for frontend development
      await new Promise((resolve) => setTimeout(resolve, 200)); // Simulate network delay
      return MOCK_TEMPLATES;
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
}
