/**
 * Rigidity Score Hook
 *
 * React Query hook for calculating time crystal rigidity score
 * using the exotic resilience API endpoint.
 *
 * Rigidity measures schedule stability: how much a schedule changes
 * between versions. High rigidity (close to 1.0) means minimal churn.
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { post } from '@/lib/api';
import type { ApiError } from '@/lib/api';

// ============================================================================
// Types
// ============================================================================

export interface RigidityRequest {
  /** Current schedule ID */
  currentScheduleId?: string | null;
  /** Proposed schedule ID to compare */
  proposedScheduleId?: string | null;
  /** Alternative: provide assignment lists directly */
  currentAssignments?: Array<Record<string, string>> | null;
  /** Alternative: provide assignment lists directly */
  proposedAssignments?: Array<Record<string, string>> | null;
}

export interface RigidityResponse {
  /** Rigidity score (1.0 = no changes, 0.0 = complete overhaul) */
  rigidityScore: number;
  /** Number of assignments changed */
  changedAssignments: number;
  /** Total assignments compared */
  totalAssignments: number;
  /** Fraction of assignments changed (0.0 - 1.0) */
  changeRate: number;
  /** Faculty with changed assignments */
  affectedFaculty: string[];
  /** Detailed churn breakdown */
  churnAnalysis: Record<string, unknown>;
  /** Stability rating: excellent, good, fair, poor, unstable */
  stabilityGrade: string;
  /** Data source */
  source: string;
}

// ============================================================================
// Query Keys
// ============================================================================

export const rigidityScoreQueryKeys = {
  all: ['rigidity-score'] as const,
  calculate: (
    currentAssignments: Array<Record<string, string>> | null,
    proposedAssignments: Array<Record<string, string>> | null
  ) => ['rigidity-score', 'calculate', currentAssignments, proposedAssignments] as const,
};

// ============================================================================
// Hook
// ============================================================================

/**
 * Calculate schedule rigidity score using time crystal analysis.
 *
 * Measures how much a schedule changes between current and proposed versions.
 * Higher rigidity = more stable (less churn). Based on time-crystal-inspired
 * anti-churn optimization.
 *
 * @param currentAssignments - Current schedule assignments
 * @param proposedAssignments - Proposed schedule assignments
 * @param options - React Query options
 * @returns Query result with rigidity score and stability grade
 *
 * @example
 * ```tsx
 * function RigidityPreview({ currentTemplates, proposedChanges }: Props) {
 *   const current = convertToAssignments(currentTemplates);
 *   const proposed = applyChanges(current, proposedChanges);
 *   const { data, isLoading } = useRigidityScore(current, proposed);
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <div className={getRigidityColor(data.rigidityScore)}>
 *       <span>Rigidity: {data.rigidityScore.toFixed(2)}</span>
 *       <p>{data.stabilityGrade}</p>
 *       <p>{data.changedAssignments} assignments changed</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function useRigidityScore(
  currentAssignments: Array<Record<string, string>> | null,
  proposedAssignments: Array<Record<string, string>> | null,
  options?: Omit<UseQueryOptions<RigidityResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<RigidityResponse, ApiError>({
    queryKey: rigidityScoreQueryKeys.calculate(currentAssignments, proposedAssignments),
    queryFn: async () => {
      if (
        !currentAssignments ||
        !proposedAssignments ||
        currentAssignments.length === 0 ||
        proposedAssignments.length === 0
      ) {
        // Return default values for empty input
        return {
          rigidityScore: 1.0,
          changedAssignments: 0,
          totalAssignments: 0,
          changeRate: 0.0,
          affectedFaculty: [],
          churnAnalysis: {},
          stabilityGrade: 'excellent',
          source: 'frontend',
        };
      }

      const request: RigidityRequest = {
        currentAssignments: currentAssignments,
        proposedAssignments: proposedAssignments,
      };

      // Call exotic resilience API endpoint
      const response = await post<RigidityResponse>(
        '/resilience/exotic/time-crystal/rigidity',
        request
      );

      return response;
    },
    enabled:
      !!currentAssignments &&
      !!proposedAssignments &&
      currentAssignments.length > 0 &&
      proposedAssignments.length > 0,
    staleTime: 30 * 1000, // 30 seconds
    ...options,
  });
}

/**
 * Helper: Get rigidity score color class.
 *
 * @param rigidity - Rigidity score (0-1)
 * @returns Tailwind color class
 */
export function getRigidityColorClass(rigidity: number): string {
  if (rigidity >= 0.95) return 'text-green-500';
  if (rigidity >= 0.85) return 'text-blue-500';
  if (rigidity >= 0.70) return 'text-yellow-500';
  if (rigidity >= 0.50) return 'text-orange-500';
  return 'text-red-500';
}

/**
 * Helper: Get stability grade icon.
 *
 * @param grade - Stability grade (excellent, good, fair, poor, unstable)
 * @returns Icon name or emoji
 */
export function getStabilityIcon(grade: string): string {
  switch (grade) {
    case 'excellent':
      return '🔒';
    case 'good':
      return '✓';
    case 'fair':
      return '⚠';
    case 'poor':
      return '⚠⚠';
    case 'unstable':
      return '🔥';
    default:
      return '?';
  }
}
