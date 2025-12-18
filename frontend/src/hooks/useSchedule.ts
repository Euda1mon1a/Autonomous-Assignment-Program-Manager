/**
 * Schedule Management Hooks
 *
 * Hooks for schedule generation, validation, rotation templates,
 * and assignment management with React Query caching.
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query'
import { get, post, put, del, ApiError } from '@/lib/api'
import type {
  RotationTemplate,
  RotationTemplateCreate,
  RotationTemplateUpdate,
  Assignment,
  AssignmentCreate,
  AssignmentUpdate,
  ValidationResult,
} from '@/types/api'

// ============================================================================
// Types
// ============================================================================

export interface ListResponse<T> {
  items: T[]
  total: number
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
  algorithm?: 'greedy' | 'cp_sat' | 'pulp' | 'hybrid'
  timeout_seconds?: number
}

export interface ScheduleGenerateResponse {
  status: 'success' | 'partial' | 'failed'
  message: string
  total_blocks_assigned: number
  total_blocks: number
  validation: ValidationResult
  run_id?: string
  solver_stats?: {
    total_residents?: number
    coverage_rate?: number
    solve_time?: number
    iterations?: number
    branches?: number
    conflicts?: number
    [key: string]: unknown
  }
}

// ============================================================================
// Query Keys
// ============================================================================

export const scheduleQueryKeys = {
  schedule: (startDate: string, endDate: string) => ['schedule', startDate, endDate] as const,
  rotationTemplates: (activityType?: string) => ['rotation-templates', activityType] as const,
  rotationTemplate: (id: string) => ['rotation-templates', id] as const,
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
    queryKey: scheduleQueryKeys.validation(startDate, endDate),
    queryFn: () => get<ValidationResult>(`/schedule/validate?start_date=${startDate}&end_date=${endDate}`),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
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
    queryKey: scheduleQueryKeys.rotationTemplate(id),
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
      queryClient.invalidateQueries({ queryKey: scheduleQueryKeys.rotationTemplate(id) })
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
    queryKey: scheduleQueryKeys.assignments(filters),
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
