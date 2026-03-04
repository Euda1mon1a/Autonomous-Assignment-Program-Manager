/**
 * Enum Fetching Hooks
 *
 * TanStack Query hooks for fetching enum/dropdown values from
 * the backend /api/v1/enums/* endpoints. Replaces hardcoded
 * dropdown options with dynamic API-driven values.
 */
import { useQuery } from '@tanstack/react-query';
import { get, ApiError } from '@/lib/api';

// ============================================================================
// Types
// ============================================================================

export interface EnumOption {
  value: string;
  label: string;
}

// ============================================================================
// Query Keys
// ============================================================================

export const enumKeys = {
  schedulingAlgorithms: ['enums', 'scheduling-algorithms'] as const,
  activityCategories: ['enums', 'activity-categories'] as const,
  rotationTypes: ['enums', 'rotation-types'] as const,
  pgyLevels: ['enums', 'pgy-levels'] as const,
  constraintCategories: ['enums', 'constraint-categories'] as const,
  personTypes: ['enums', 'person-types'] as const,
  freezeScopes: ['enums', 'freeze-scopes'] as const,
};

// ============================================================================
// Hooks
// ============================================================================

const ENUM_STALE_TIME = 10 * 60 * 1000; // 10 minutes
const ENUM_GC_TIME = 30 * 60 * 1000; // 30 minutes

export function useSchedulingAlgorithms() {
  return useQuery<EnumOption[], ApiError>({
    queryKey: enumKeys.schedulingAlgorithms,
    queryFn: () => get<EnumOption[]>('/enums/scheduling-algorithms'),
    staleTime: ENUM_STALE_TIME,
    gcTime: ENUM_GC_TIME,
  });
}

export function useActivityCategories() {
  return useQuery<EnumOption[], ApiError>({
    queryKey: enumKeys.activityCategories,
    queryFn: () => get<EnumOption[]>('/enums/activity-categories'),
    staleTime: ENUM_STALE_TIME,
    gcTime: ENUM_GC_TIME,
  });
}

export function useRotationTypes() {
  return useQuery<EnumOption[], ApiError>({
    queryKey: enumKeys.rotationTypes,
    queryFn: () => get<EnumOption[]>('/enums/rotation-types'),
    staleTime: ENUM_STALE_TIME,
    gcTime: ENUM_GC_TIME,
  });
}

export function usePgyLevels() {
  return useQuery<EnumOption[], ApiError>({
    queryKey: enumKeys.pgyLevels,
    queryFn: () => get<EnumOption[]>('/enums/pgy-levels'),
    staleTime: ENUM_STALE_TIME,
    gcTime: ENUM_GC_TIME,
  });
}

export function useConstraintCategories() {
  return useQuery<EnumOption[], ApiError>({
    queryKey: enumKeys.constraintCategories,
    queryFn: () => get<EnumOption[]>('/enums/constraint-categories'),
    staleTime: ENUM_STALE_TIME,
    gcTime: ENUM_GC_TIME,
  });
}

export function usePersonTypes() {
  return useQuery<EnumOption[], ApiError>({
    queryKey: enumKeys.personTypes,
    queryFn: () => get<EnumOption[]>('/enums/person-types'),
    staleTime: ENUM_STALE_TIME,
    gcTime: ENUM_GC_TIME,
  });
}

export function useFreezeScopes() {
  return useQuery<EnumOption[], ApiError>({
    queryKey: enumKeys.freezeScopes,
    queryFn: () => get<EnumOption[]>('/enums/freeze-scopes'),
    staleTime: ENUM_STALE_TIME,
    gcTime: ENUM_GC_TIME,
  });
}
