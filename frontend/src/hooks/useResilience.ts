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
 * Handles emergency coverage requests when a person becomes unavailable.
 *
 * This mutation hook initiates an automated coverage search when a resident
 * or faculty member needs emergency replacement due to illness, deployment,
 * or other urgent circumstances. The system attempts to find suitable
 * replacements while maintaining ACGME compliance and schedule integrity.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to trigger emergency coverage
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isLoading`: Whether the request is in progress
 *   - `error`: Any error that occurred during processing
 *   - `data`: Coverage response with replacement details
 *
 * @example
 * ```tsx
 * function EmergencyCoverageDialog({ personId }: Props) {
 *   const { mutate, isLoading } = useEmergencyCoverage();
 *
 *   const handleSubmit = (data: EmergencyCoverageRequest) => {
 *     mutate(data, {
 *       onSuccess: (result) => {
 *         if (result.status === 'success') {
 *           toast.success(`Found ${result.replacements_found} replacements`);
 *         } else if (result.requires_manual_review) {
 *           toast.warning('Manual review required for coverage gaps');
 *         }
 *       },
 *       onError: (error) => {
 *         toast.error(`Failed to process coverage: ${error.message}`);
 *       },
 *     });
 *   };
 *
 *   return <CoverageForm onSubmit={handleSubmit} loading={isLoading} />;
 * }
 * ```
 *
 * @see EmergencyCoverageRequest - Input parameters for coverage request
 * @see EmergencyCoverageResponse - Detailed response with replacement status
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
