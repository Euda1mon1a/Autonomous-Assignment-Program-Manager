/**
 * Half-Day Requirements Management Hooks
 *
 * TanStack Query hooks for fetching and updating rotation half-day requirements.
 * Half-day requirements define activity distribution per rotation template block.
 *
 * API endpoints:
 * - GET /api/rotation-templates/{templateId}/halfday-requirements
 * - PUT /api/rotation-templates/{templateId}/halfday-requirements
 */
import type { ApiError } from "@/lib/api";
import { get, put } from "@/lib/api";
import type {
  HalfDayRequirement,
  HalfDayRequirementCreate,
} from "@/types/admin-templates";
import {
  useMutation,
  useQuery,
  useQueryClient,
  UseQueryOptions,
} from "@tanstack/react-query";

// ============================================================================
// Query Keys
// ============================================================================

export const halfDayRequirementsQueryKeys = {
  /** All half-day requirements */
  all: ["halfday-requirements"] as const,
  /** Requirements for a specific template */
  byTemplate: (templateId: string) =>
    ["halfday-requirements", templateId] as const,
};

// ============================================================================
// Default Values
// ============================================================================

/**
 * Default half-day requirement values.
 * Standard block has 10 half-days: 4 FM clinic + 5 specialty + 1 academics.
 */
export const DEFAULT_HALFDAY_REQUIREMENTS: HalfDayRequirementCreate = {
  fmClinicHalfdays: 4,
  specialtyHalfdays: 5,
  specialtyName: null,
  academicsHalfdays: 1,
  electiveHalfdays: 0,
  minConsecutiveSpecialty: 1,
  preferCombinedClinicDays: true,
};

// ============================================================================
// Hooks
// ============================================================================

/**
 * Fetches half-day requirements for a rotation template.
 *
 * @param templateId - UUID of the rotation template
 * @param options - Optional React Query configuration
 * @returns Query result with requirements or null if not configured
 *
 * @example
 * ```tsx
 * function RequirementsEditor({ templateId }: Props) {
 *   const { data: requirements, isLoading } = useHalfDayRequirements(templateId);
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <RequirementsForm
 *       requirements={requirements ?? DEFAULT_HALFDAY_REQUIREMENTS}
 *       onSave={handleSave}
 *     />
 *   );
 * }
 * ```
 */
export function useHalfDayRequirements(
  templateId: string,
  options?: Omit<
    UseQueryOptions<HalfDayRequirement | null, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<HalfDayRequirement | null, ApiError>({
    queryKey: halfDayRequirementsQueryKeys.byTemplate(templateId),
    queryFn: async () => {
      return get<HalfDayRequirement | null>(
        `/rotation-templates/${templateId}/halfday-requirements`
      );
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!templateId,
    ...options,
  });
}

/**
 * Request type for updating half-day requirements.
 */
export interface HalfDayRequirementsUpdateRequest {
  templateId: string;
  requirements: HalfDayRequirementCreate;
}

/**
 * Creates or updates half-day requirements for a rotation template.
 *
 * @returns Mutation object for updating requirements
 *
 * @example
 * ```tsx
 * function RequirementsEditor({ templateId }: Props) {
 *   const { mutate, isPending } = useUpdateHalfDayRequirements();
 *
 *   const handleSave = (requirements: HalfDayRequirementCreate) => {
 *     mutate(
 *       { templateId, requirements },
 *       {
 *         onSuccess: () => toast.success('Requirements saved'),
 *         onError: (err) => toast.error(err.message),
 *       }
 *     );
 *   };
 *
 *   return <RequirementsForm onSave={handleSave} isLoading={isPending} />;
 * }
 * ```
 */
export function useUpdateHalfDayRequirements() {
  const queryClient = useQueryClient();

  return useMutation<
    HalfDayRequirement,
    ApiError,
    HalfDayRequirementsUpdateRequest
  >({
    mutationFn: async ({ templateId, requirements }) => {
      return put<HalfDayRequirement>(
        `/rotation-templates/${templateId}/halfday-requirements`,
        requirements
      );
    },
    onSuccess: (data, variables) => {
      // Update cache with new requirements
      queryClient.setQueryData(
        halfDayRequirementsQueryKeys.byTemplate(variables.templateId),
        data
      );
      // Invalidate related queries
      queryClient.invalidateQueries({
        queryKey: halfDayRequirementsQueryKeys.all,
      });
    },
  });
}

/**
 * Calculate total half-days from requirement values.
 */
export function calculateTotalHalfdays(
  requirements: HalfDayRequirementCreate
): number {
  return (
    (requirements.fmClinicHalfdays ?? 4) +
    (requirements.specialtyHalfdays ?? 5) +
    (requirements.academicsHalfdays ?? 1) +
    (requirements.electiveHalfdays ?? 0)
  );
}

/**
 * Check if requirements are balanced (total = 10).
 */
export function isRequirementsBalanced(
  requirements: HalfDayRequirementCreate
): boolean {
  return calculateTotalHalfdays(requirements) === 10;
}
