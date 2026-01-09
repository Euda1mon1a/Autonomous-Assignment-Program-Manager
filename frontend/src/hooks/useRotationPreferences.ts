/**
 * Rotation Preferences Management Hooks
 *
 * TanStack Query hooks for fetching and updating rotation preferences.
 * Preferences are soft scheduling constraints that guide the optimizer.
 *
 * Uses real API endpoints:
 * - GET /api/rotation-templates/{templateId}/preferences
 * - PUT /api/rotation-templates/{templateId}/preferences
 */
import type { ApiError } from "@/lib/api";
import { get, put } from "@/lib/api";
import type { UUID } from "@/types/api";
import {
  useMutation,
  useQuery,
  useQueryClient,
  UseQueryOptions,
} from "@tanstack/react-query";

// ============================================================================
// Types
// ============================================================================

/**
 * Valid preference weight levels.
 */
export type PreferenceWeight = "low" | "medium" | "high" | "required";

/**
 * Valid preference types.
 */
export type PreferenceType =
  | "full_day_grouping"
  | "consecutive_specialty"
  | "avoid_isolated"
  | "preferred_days"
  | "avoid_friday_pm"
  | "balance_weekly";

/**
 * Rotation preference as returned from backend.
 */
export interface RotationPreference {
  id: UUID;
  rotation_template_id: UUID;
  preference_type: PreferenceType;
  weight: PreferenceWeight;
  config_json: Record<string, unknown>;
  is_active: boolean;
  description: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Request to create a preference.
 */
export interface RotationPreferenceCreate {
  preference_type: PreferenceType;
  weight?: PreferenceWeight;
  config_json?: Record<string, unknown>;
  is_active?: boolean;
  description?: string | null;
}

/**
 * Request to update preferences (atomic replace).
 */
export interface PreferencesUpdateRequest {
  templateId: UUID;
  preferences: RotationPreferenceCreate[];
}

// ============================================================================
// Query Keys
// ============================================================================

export const preferencesQueryKeys = {
  /** All preferences */
  all: ["rotation-preferences"] as const,
  /** Preferences for a specific template */
  byTemplate: (templateId: string) =>
    ["rotation-preferences", templateId] as const,
};

// ============================================================================
// Preference Type Metadata
// ============================================================================

/**
 * Human-readable metadata for each preference type.
 */
export const PREFERENCE_METADATA: Record<
  PreferenceType,
  {
    label: string;
    description: string;
    defaultWeight: PreferenceWeight;
    configSchema?: string[];
  }
> = {
  full_day_grouping: {
    label: "Full Day Grouping",
    description: "Prefer full days when possible (AM+PM same activity)",
    defaultWeight: "medium",
  },
  consecutive_specialty: {
    label: "Consecutive Specialty",
    description: "Group specialty sessions consecutively",
    defaultWeight: "high",
    configSchema: ["min_consecutive"],
  },
  avoid_isolated: {
    label: "Avoid Isolated Sessions",
    description: "Avoid single isolated half-day sessions",
    defaultWeight: "low",
  },
  preferred_days: {
    label: "Preferred Days",
    description: "Prefer specific activities on specific days",
    defaultWeight: "medium",
    configSchema: ["activity", "days"],
  },
  avoid_friday_pm: {
    label: "Avoid Friday PM",
    description: "Keep Friday PM open as travel buffer",
    defaultWeight: "low",
  },
  balance_weekly: {
    label: "Balance Weekly",
    description: "Distribute activities evenly across the week",
    defaultWeight: "medium",
    configSchema: ["max_same_per_day"],
  },
};

/**
 * Weight multipliers for optimization scoring.
 */
export const WEIGHT_MULTIPLIERS: Record<PreferenceWeight, number> = {
  low: 1.0,
  medium: 2.0,
  high: 4.0,
  required: 8.0,
};

// ============================================================================
// Hooks
// ============================================================================

/**
 * Fetches rotation preferences for a template.
 *
 * @param templateId - UUID of the rotation template
 * @param options - Optional React Query configuration
 * @returns Query result with preferences list
 *
 * @example
 * ```tsx
 * function PreferencesEditor({ templateId }: Props) {
 *   const { data: preferences, isLoading } = useRotationPreferences(templateId);
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <PreferencesList
 *       preferences={preferences}
 *       onToggle={handleToggle}
 *       onWeightChange={handleWeightChange}
 *     />
 *   );
 * }
 * ```
 */
export function useRotationPreferences(
  templateId: string,
  options?: Omit<
    UseQueryOptions<RotationPreference[], ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<RotationPreference[], ApiError>({
    queryKey: preferencesQueryKeys.byTemplate(templateId),
    queryFn: async () => {
      return get<RotationPreference[]>(
        `/rotation-templates/${templateId}/preferences`
      );
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!templateId,
    ...options,
  });
}

/**
 * Updates rotation preferences for a template (atomic replace).
 *
 * Replaces all existing preferences with the new list.
 *
 * @returns Mutation object for updating preferences
 *
 * @example
 * ```tsx
 * function PreferencesEditor({ templateId }: Props) {
 *   const { mutate, isPending } = useUpdateRotationPreferences();
 *
 *   const handleSave = (preferences: RotationPreferenceCreate[]) => {
 *     mutate(
 *       { templateId, preferences },
 *       {
 *         onSuccess: () => toast.success('Preferences saved'),
 *         onError: (error) => toast.error(`Failed: ${error.message}`),
 *       }
 *     );
 *   };
 *
 *   return <PreferencesList onSave={handleSave} saving={isPending} />;
 * }
 * ```
 */
export function useUpdateRotationPreferences() {
  const queryClient = useQueryClient();

  return useMutation<RotationPreference[], ApiError, PreferencesUpdateRequest>({
    mutationFn: async (request) => {
      return put<RotationPreference[]>(
        `/rotation-templates/${request.templateId}/preferences`,
        request.preferences
      );
    },
    onSuccess: (_data, variables) => {
      // Invalidate the specific preferences query
      queryClient.invalidateQueries({
        queryKey: preferencesQueryKeys.byTemplate(variables.templateId),
      });
      // Also invalidate rotation templates list
      queryClient.invalidateQueries({
        queryKey: ["rotation-templates"],
      });
    },
  });
}

/**
 * Toggle a specific preference's active status.
 *
 * Convenience hook that modifies a single preference and saves all.
 *
 * @param templateId - UUID of the rotation template
 * @returns Mutation for toggling a preference
 */
export function useTogglePreference(templateId: string) {
  const queryClient = useQueryClient();

  return useMutation<
    RotationPreference[],
    ApiError,
    { preferenceType: PreferenceType }
  >({
    mutationFn: async ({ preferenceType }) => {
      // Get current preferences
      const currentPreferences = queryClient.getQueryData<RotationPreference[]>(
        preferencesQueryKeys.byTemplate(templateId)
      );

      if (!currentPreferences) {
        throw new Error("Preferences not loaded");
      }

      // Toggle the specified preference
      const updatedPreferences = currentPreferences.map((p) =>
        p.preferenceType === preferenceType
          ? { ...p, is_active: !p.isActive }
          : p
      );

      // Convert to create format and save
      const createPayload = updatedPreferences.map((p) => ({
        preference_type: p.preferenceType,
        weight: p.weight,
        config_json: p.configJson,
        is_active: p.isActive,
        description: p.description,
      }));

      return put<RotationPreference[]>(
        `/rotation-templates/${templateId}/preferences`,
        createPayload
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: preferencesQueryKeys.byTemplate(templateId),
      });
    },
  });
}

/**
 * Update a preference's weight.
 *
 * @param templateId - UUID of the rotation template
 * @returns Mutation for updating preference weight
 */
export function useUpdatePreferenceWeight(templateId: string) {
  const queryClient = useQueryClient();

  return useMutation<
    RotationPreference[],
    ApiError,
    { preferenceType: PreferenceType; weight: PreferenceWeight }
  >({
    mutationFn: async ({ preferenceType, weight }) => {
      // Get current preferences
      const currentPreferences = queryClient.getQueryData<RotationPreference[]>(
        preferencesQueryKeys.byTemplate(templateId)
      );

      if (!currentPreferences) {
        throw new Error("Preferences not loaded");
      }

      // Update the specified preference's weight
      const updatedPreferences = currentPreferences.map((p) =>
        p.preferenceType === preferenceType ? { ...p, weight } : p
      );

      // Convert to create format and save
      const createPayload = updatedPreferences.map((p) => ({
        preference_type: p.preferenceType,
        weight: p.weight,
        config_json: p.configJson,
        is_active: p.isActive,
        description: p.description,
      }));

      return put<RotationPreference[]>(
        `/rotation-templates/${templateId}/preferences`,
        createPayload
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: preferencesQueryKeys.byTemplate(templateId),
      });
    },
  });
}
