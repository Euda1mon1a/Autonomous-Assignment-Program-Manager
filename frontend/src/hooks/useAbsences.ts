/**
 * Absence Management Hooks
 *
 * Hooks for managing resident and faculty absences (vacation,
 * conferences, illness, etc.) with React Query caching.
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query'
import { get, post, put, del, ApiError } from '@/lib/api'
import type {
  Absence,
  AbsenceCreate,
  AbsenceUpdate,
} from '@/types/api'

// ============================================================================
// Types
// ============================================================================

export interface ListResponse<T> {
  items: T[]
  total: number
}

export interface AbsenceFilters {
  person_id?: string
  start_date?: string
  end_date?: string
  absence_type?: string
}

// ============================================================================
// Query Keys
// ============================================================================

export const absenceQueryKeys = {
  absences: (filters?: AbsenceFilters) => ['absences', filters] as const,
  absence: (id: string) => ['absences', id] as const,
}

// ============================================================================
// Absence Hooks
// ============================================================================

/**
 * Fetch absences with optional person filter
 */
export function useAbsences(
  personId?: number,
  options?: Omit<UseQueryOptions<ListResponse<Absence>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = personId !== undefined ? `?person_id=${personId}` : ''

  return useQuery<ListResponse<Absence>, ApiError>({
    queryKey: ['absences', personId],
    queryFn: () => get<ListResponse<Absence>>(`/absences${params}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}

/**
 * Fetch a single absence by ID
 */
export function useAbsence(
  id: string,
  options?: Omit<UseQueryOptions<Absence, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Absence, ApiError>({
    queryKey: absenceQueryKeys.absence(id),
    queryFn: () => get<Absence>(`/absences/${id}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!id,
    ...options,
  })
}

/**
 * Create a new absence
 */
export function useCreateAbsence() {
  const queryClient = useQueryClient()

  return useMutation<Absence, ApiError, AbsenceCreate>({
    mutationFn: (data) => post<Absence>('/absences', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['absences'] })
      // Absences affect schedule availability
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
    },
  })
}

/**
 * Update an existing absence
 */
export function useUpdateAbsence() {
  const queryClient = useQueryClient()

  return useMutation<Absence, ApiError, { id: string; data: AbsenceUpdate }>({
    mutationFn: ({ id, data }) => put<Absence>(`/absences/${id}`, data),
    onSuccess: (data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['absences'] })
      queryClient.invalidateQueries({ queryKey: absenceQueryKeys.absence(id) })
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
    },
  })
}

/**
 * Delete an absence
 */
export function useDeleteAbsence() {
  const queryClient = useQueryClient()

  return useMutation<void, ApiError, string>({
    mutationFn: (id) => del(`/absences/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['absences'] })
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
    },
  })
}
