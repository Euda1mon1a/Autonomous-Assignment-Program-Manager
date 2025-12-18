/**
 * People Management Hooks
 *
 * Hooks for managing people (residents, faculty, staff) with
 * React Query caching and optimistic updates.
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query'
import { get, post, put, del, ApiError } from '@/lib/api'
import type {
  Person,
  PersonCreate,
  PersonUpdate,
} from '@/types/api'

// ============================================================================
// Types
// ============================================================================

export interface ListResponse<T> {
  items: T[]
  total: number
}

export interface PeopleFilters {
  role?: string
  pgy_level?: number
}

// ============================================================================
// Query Keys
// ============================================================================

export const peopleQueryKeys = {
  people: (filters?: PeopleFilters) => ['people', filters] as const,
  person: (id: string) => ['people', id] as const,
  residents: (pgyLevel?: number) => ['residents', pgyLevel] as const,
  faculty: (specialty?: string) => ['faculty', specialty] as const,
}

// ============================================================================
// People Hooks
// ============================================================================

/**
 * Fetch list of people with optional filters
 */
export function usePeople(
  filters?: PeopleFilters,
  options?: Omit<UseQueryOptions<ListResponse<Person>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams()
  if (filters?.role) params.set('role', filters.role)
  if (filters?.pgy_level !== undefined) params.set('pgy_level', String(filters.pgy_level))
  const queryString = params.toString()

  return useQuery<ListResponse<Person>, ApiError>({
    queryKey: ['people', filters],
    queryFn: () => get<ListResponse<Person>>(`/people${queryString ? `?${queryString}` : ''}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}

/**
 * Fetch a single person by ID
 */
export function usePerson(
  id: string,
  options?: Omit<UseQueryOptions<Person, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Person, ApiError>({
    queryKey: peopleQueryKeys.person(id),
    queryFn: () => get<Person>(`/people/${id}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!id,
    ...options,
  })
}

/**
 * Fetch residents with optional PGY level filter
 */
export function useResidents(
  pgyLevel?: number,
  options?: Omit<UseQueryOptions<ListResponse<Person>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = pgyLevel !== undefined ? `?pgy_level=${pgyLevel}` : ''

  return useQuery<ListResponse<Person>, ApiError>({
    queryKey: peopleQueryKeys.residents(pgyLevel),
    queryFn: () => get<ListResponse<Person>>(`/people/residents${params}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}

/**
 * Fetch faculty with optional specialty filter
 */
export function useFaculty(
  specialty?: string,
  options?: Omit<UseQueryOptions<ListResponse<Person>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = specialty ? `?specialty=${encodeURIComponent(specialty)}` : ''

  return useQuery<ListResponse<Person>, ApiError>({
    queryKey: peopleQueryKeys.faculty(specialty),
    queryFn: () => get<ListResponse<Person>>(`/people/faculty${params}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}

/**
 * Create a new person
 */
export function useCreatePerson() {
  const queryClient = useQueryClient()

  return useMutation<Person, ApiError, PersonCreate>({
    mutationFn: (data) => post<Person>('/people', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
      queryClient.invalidateQueries({ queryKey: ['residents'] })
      queryClient.invalidateQueries({ queryKey: ['faculty'] })
    },
  })
}

/**
 * Update an existing person
 */
export function useUpdatePerson() {
  const queryClient = useQueryClient()

  return useMutation<Person, ApiError, { id: string; data: PersonUpdate }>({
    mutationFn: ({ id, data }) => put<Person>(`/people/${id}`, data),
    onSuccess: (data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
      queryClient.invalidateQueries({ queryKey: peopleQueryKeys.person(id) })
      queryClient.invalidateQueries({ queryKey: ['residents'] })
      queryClient.invalidateQueries({ queryKey: ['faculty'] })
    },
  })
}

/**
 * Delete a person
 */
export function useDeletePerson() {
  const queryClient = useQueryClient()

  return useMutation<void, ApiError, string>({
    mutationFn: (id) => del(`/people/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
      queryClient.invalidateQueries({ queryKey: ['residents'] })
      queryClient.invalidateQueries({ queryKey: ['faculty'] })
    },
  })
}
