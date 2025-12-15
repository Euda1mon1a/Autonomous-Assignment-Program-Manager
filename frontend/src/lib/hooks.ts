/**
 * React Query Hooks for Residency Scheduler
 *
 * Provides data fetching hooks with caching, loading states,
 * and error handling for all API endpoints.
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query'
import { get, post, put, del, ApiError } from './api'
import type {
  Person,
  PersonCreate,
  PersonUpdate,
  Absence,
  AbsenceCreate,
  AbsenceUpdate,
  RotationTemplate,
  RotationTemplateCreate,
  RotationTemplateUpdate,
  Assignment,
  AssignmentCreate,
  AssignmentUpdate,
  ScheduleResponse,
  ValidationResult,
} from '@/types/api'

// ============================================================================
// API Response Types
// ============================================================================

export interface ListResponse<T> {
  items: T[]
  total: number
}

export interface PeopleFilters {
  role?: string
  pgy_level?: number
}

export interface AbsenceFilters {
  person_id?: string
  start_date?: string
  end_date?: string
  absence_type?: string
}

export interface AssignmentFilters {
  start_date?: string
  end_date?: string
  person_id?: string
  role?: string
}

export interface ScheduleGenerateRequest {
  start_date: string
  end_date: string
  pgy_levels?: number[]
  rotation_template_ids?: string[]
  algorithm?: 'greedy' | 'min_conflicts' | 'cp_sat'
}

export interface ScheduleGenerateResponse {
  status: 'success' | 'partial' | 'failed'
  message: string
  total_blocks_assigned: number
  total_blocks: number
  validation: ValidationResult
  run_id?: string
}



// ============================================================================
// Query Keys
// ============================================================================

export const queryKeys = {
  schedule: (startDate: string, endDate: string) => ['schedule', startDate, endDate] as const,
  people: (filters?: PeopleFilters) => ['people', filters] as const,
  person: (id: string) => ['people', id] as const,
  residents: (pgyLevel?: number) => ['residents', pgyLevel] as const,
  faculty: (specialty?: string) => ['faculty', specialty] as const,
  rotationTemplates: (activityType?: string) => ['rotation-templates', activityType] as const,
  rotationTemplate: (id: string) => ['rotation-templates', id] as const,
  absences: (filters?: AbsenceFilters) => ['absences', filters] as const,
  absence: (id: string) => ['absences', id] as const,
  validation: (startDate: string, endDate: string) => ['validation', startDate, endDate] as const,
  assignments: (filters?: AssignmentFilters) => ['assignments', filters] as const,
}

// ============================================================================
// Schedule Hooks
// ============================================================================

/**
 * Fetch schedule for a date range
 * Used by the main calendar view
 */
export function useSchedule(
  startDate: Date,
  endDate: Date,
  options?: Omit<UseQueryOptions<ListResponse<Assignment>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const startIso = startDate.toISOString()
  const endIso = endDate.toISOString()
  const startDateStr = startDate.toISOString().split('T')[0]
  const endDateStr = endDate.toISOString().split('T')[0]

  return useQuery<ListResponse<Assignment>, ApiError>({
    queryKey: ['schedule', startIso, endIso],
    queryFn: () => get<ListResponse<Assignment>>(`/assignments?start_date=${startDateStr}&end_date=${endDateStr}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    refetchOnWindowFocus: true,
    ...options,
  })
}

/**
 * Generate a new schedule
 */
export function useGenerateSchedule() {
  const queryClient = useQueryClient()

  return useMutation<ScheduleGenerateResponse, ApiError, ScheduleGenerateRequest>({
    mutationFn: (request) => post<ScheduleGenerateResponse>('/schedule/generate', request),
    onSuccess: (data, variables) => {
      // Invalidate schedule queries for the affected date range
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
      queryClient.invalidateQueries({ queryKey: ['validation'] })
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
    },
  })
}

/**
 * Validate schedule for ACGME compliance
 */
export function useValidateSchedule(
  startDate: string,
  endDate: string,
  options?: Omit<UseQueryOptions<ValidationResult, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ValidationResult, ApiError>({
    queryKey: queryKeys.validation(startDate, endDate),
    queryFn: () => get<ValidationResult>(`/schedule/validate?start_date=${startDate}&end_date=${endDate}`),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
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
    queryKey: queryKeys.person(id),
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
    queryKey: queryKeys.residents(pgyLevel),
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
    queryKey: queryKeys.faculty(specialty),
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
      queryClient.invalidateQueries({ queryKey: queryKeys.person(id) })
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
    queryKey: queryKeys.absence(id),
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
      queryClient.invalidateQueries({ queryKey: queryKeys.absence(id) })
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

// ============================================================================
// Rotation Template Hooks
// ============================================================================

/**
 * Fetch all rotation templates
 */
export function useRotationTemplates(
  options?: Omit<UseQueryOptions<ListResponse<RotationTemplate>, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ListResponse<RotationTemplate>, ApiError>({
    queryKey: ['rotation-templates'],
    queryFn: () => get<ListResponse<RotationTemplate>>('/rotation-templates'),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}

/**
 * Fetch a single rotation template by ID
 */
export function useRotationTemplate(
  id: string,
  options?: Omit<UseQueryOptions<RotationTemplate, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<RotationTemplate, ApiError>({
    queryKey: queryKeys.rotationTemplate(id),
    queryFn: () => get<RotationTemplate>(`/rotation-templates/${id}`),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!id,
    ...options,
  })
}

/**
 * Create a new rotation template
 */
export function useCreateTemplate() {
  const queryClient = useQueryClient()

  return useMutation<RotationTemplate, ApiError, RotationTemplateCreate>({
    mutationFn: (data) => post<RotationTemplate>('/rotation-templates', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rotation-templates'] })
    },
  })
}

/**
 * Update an existing rotation template
 */
export function useUpdateTemplate() {
  const queryClient = useQueryClient()

  return useMutation<RotationTemplate, ApiError, { id: string; data: RotationTemplateUpdate }>({
    mutationFn: ({ id, data }) => put<RotationTemplate>(`/rotation-templates/${id}`, data),
    onSuccess: (data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['rotation-templates'] })
      queryClient.invalidateQueries({ queryKey: queryKeys.rotationTemplate(id) })
    },
  })
}

/**
 * Delete a rotation template
 */
export function useDeleteTemplate() {
  const queryClient = useQueryClient()

  return useMutation<void, ApiError, string>({
    mutationFn: (id) => del(`/rotation-templates/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rotation-templates'] })
    },
  })
}

// ============================================================================
// Assignment Hooks
// ============================================================================

/**
 * Fetch assignments with optional filters
 */
export function useAssignments(
  filters?: AssignmentFilters,
  options?: Omit<UseQueryOptions<ListResponse<Assignment>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams()
  if (filters?.start_date) params.set('start_date', filters.start_date)
  if (filters?.end_date) params.set('end_date', filters.end_date)
  if (filters?.person_id) params.set('person_id', filters.person_id)
  if (filters?.role) params.set('role', filters.role)
  const queryString = params.toString()

  return useQuery<ListResponse<Assignment>, ApiError>({
    queryKey: queryKeys.assignments(filters),
    queryFn: () => get<ListResponse<Assignment>>(`/assignments${queryString ? `?${queryString}` : ''}`),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}

/**
 * Create a new assignment
 */
export function useCreateAssignment() {
  const queryClient = useQueryClient()

  return useMutation<Assignment, ApiError, AssignmentCreate>({
    mutationFn: (data) => post<Assignment>('/assignments', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
      queryClient.invalidateQueries({ queryKey: ['validation'] })
    },
  })
}

/**
 * Update an existing assignment
 */
export function useUpdateAssignment() {
  const queryClient = useQueryClient()

  return useMutation<Assignment, ApiError, { id: string; data: AssignmentUpdate }>({
    mutationFn: ({ id, data }) => put<Assignment>(`/assignments/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
      queryClient.invalidateQueries({ queryKey: ['validation'] })
    },
  })
}

/**
 * Delete an assignment
 */
export function useDeleteAssignment() {
  const queryClient = useQueryClient()

  return useMutation<void, ApiError, string>({
    mutationFn: (id) => del(`/assignments/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
      queryClient.invalidateQueries({ queryKey: ['validation'] })
    },
  })
}

// ============================================================================
// Emergency Coverage Hooks
// ============================================================================

export interface EmergencyCoverageRequest {
  person_id: string
  start_date: string
  end_date: string
  reason: string
  is_deployment?: boolean
}

export interface EmergencyCoverageResponse {
  status: 'success' | 'partial' | 'failed'
  replacements_found: number
  coverage_gaps: number
  requires_manual_review: boolean
  details: Array<{
    date: string
    original_assignment: string
    replacement?: string
    status: string
  }>
}

/**
 * Handle emergency coverage request
 */
export function useEmergencyCoverage() {
  const queryClient = useQueryClient()

  return useMutation<EmergencyCoverageResponse, ApiError, EmergencyCoverageRequest>({
    mutationFn: (data) => post<EmergencyCoverageResponse>('/schedule/emergency-coverage', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
      queryClient.invalidateQueries({ queryKey: ['absences'] })
      queryClient.invalidateQueries({ queryKey: ['validation'] })
    },
  })
}
