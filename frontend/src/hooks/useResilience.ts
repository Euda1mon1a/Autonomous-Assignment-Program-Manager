/**
 * Resilience Framework Hooks
 *
 * Hooks for emergency coverage, deployment handling, and
 * schedule resilience features with React Query caching.
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { post, ApiError } from '@/lib/api'

// ============================================================================
// Types
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

// ============================================================================
// Emergency Coverage Hooks
// ============================================================================

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
