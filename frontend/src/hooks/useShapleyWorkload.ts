/**
 * Shapley Workload Hook
 *
 * React Query hook for calculating Shapley values for fair workload distribution.
 * Uses cooperative game theory to determine each faculty member's fair share
 * of workload based on their marginal contribution to schedule coverage.
 *
 * The Shapley value is the unique fair division satisfying:
 * - Efficiency: Sum of all values = total value
 * - Symmetry: Identical players get identical payoffs
 * - Null player: Zero contribution = zero payoff
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { post } from '@/lib/api';
import type { ApiError } from '@/lib/api';

// ============================================================================
// Types
// ============================================================================

export interface ShapleyWorkloadRequest {
  /** Faculty member IDs to analyze (minimum 2) */
  facultyIds: string[];
  /** Start date in YYYY-MM-DD format */
  startDate: string;
  /** End date in YYYY-MM-DD format */
  endDate: string;
  /** Monte Carlo samples (100-10000, default 1000) */
  numSamples?: number;
}

export interface ShapleyFacultyResult {
  /** Faculty member ID */
  facultyId: string;
  /** Faculty member name */
  facultyName: string;
  /** Normalized Shapley value (0-1, proportion of total contribution) */
  shapleyValue: number;
  /** Marginal contribution to coverage (blocks) */
  marginalContribution: number;
  /** Fair workload in hours based on Shapley proportion */
  fairWorkloadTarget: number;
  /** Actual workload in hours */
  currentWorkload: number;
  /** Hours above (+) or below (-) fair target */
  equityGap: number;
}

export interface ShapleyMetricsResponse {
  /** Per-faculty Shapley analysis results */
  facultyResults: ShapleyFacultyResult[];
  /** Total hours worked by all faculty */
  totalWorkload: number;
  /** Sum of all fair workload targets */
  totalFairTarget: number;
  /** Standard deviation of equity gaps (lower = more equitable) */
  equityGapStdDev: number;
  /** Number of faculty working above fair share */
  overworkedCount: number;
  /** Number of faculty working below fair share */
  underworkedCount: number;
  /** Faculty ID with largest positive equity gap */
  mostOverworkedFacultyId: string | null;
  /** Faculty ID with largest negative equity gap */
  mostUnderworkedFacultyId: string | null;
}

// ============================================================================
// Query Keys
// ============================================================================

export const shapleyQueryKeys = {
  all: ['shapley-workload'] as const,
  calculate: (facultyIds: string[], startDate: string, endDate: string) =>
    ['shapley-workload', 'calculate', facultyIds.sort().join(','), startDate, endDate] as const,
};

// ============================================================================
// Hook
// ============================================================================

/**
 * Calculate Shapley values for fair workload distribution.
 *
 * Uses cooperative game theory via the backend Shapley service to determine
 * fair workload allocation based on marginal contributions.
 *
 * @param facultyIds - Array of faculty member IDs (minimum 2)
 * @param startDate - Start date in YYYY-MM-DD format
 * @param endDate - End date in YYYY-MM-DD format
 * @param numSamples - Monte Carlo samples (default 1000)
 * @param options - React Query options
 * @returns Query result with Shapley metrics
 *
 * @example
 * ```tsx
 * function ShapleyAnalysis({ facultyIds, dateRange }: Props) {
 *   const { data, isLoading } = useShapleyWorkload(
 *     facultyIds,
 *     dateRange.start,
 *     dateRange.end
 *   );
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <div>
 *       <p>Overworked: {data.overworkedCount}</p>
 *       <p>Underworked: {data.underworkedCount}</p>
 *       {data.facultyResults.map(f => (
 *         <div key={f.facultyId}>
 *           {f.facultyName}: Gap {f.equityGap.toFixed(1)}h
 *         </div>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useShapleyWorkload(
  facultyIds: string[] | null,
  startDate: string | null,
  endDate: string | null,
  numSamples: number = 1000,
  options?: Omit<
    UseQueryOptions<ShapleyMetricsResponse, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<ShapleyMetricsResponse, ApiError>({
    queryKey: shapleyQueryKeys.calculate(facultyIds || [], startDate || '', endDate || ''),
    queryFn: async () => {
      if (!facultyIds || facultyIds.length < 2 || !startDate || !endDate) {
        // Return empty default
        return {
          facultyResults: [],
          totalWorkload: 0,
          totalFairTarget: 0,
          equityGapStdDev: 0,
          overworkedCount: 0,
          underworkedCount: 0,
          mostOverworkedFacultyId: null,
          mostUnderworkedFacultyId: null,
        };
      }

      const request: ShapleyWorkloadRequest = {
        facultyIds,
        startDate,
        endDate,
        numSamples,
      };

      // Call backend Shapley endpoint
      const response = await post<ShapleyMetricsResponse>(
        '/mcp/calculate-shapley-workload',
        request
      );

      return response;
    },
    enabled: !!facultyIds && facultyIds.length >= 2 && !!startDate && !!endDate,
    staleTime: 5 * 60 * 1000, // 5 minutes - Shapley calculation is expensive
    ...options,
  });
}

/**
 * Helper: Get equity gap color class.
 *
 * @param gap - Equity gap in hours (positive = overworked)
 * @param threshold - Threshold for warning (default 10 hours)
 * @returns Tailwind color class
 */
export function getEquityGapColorClass(gap: number, threshold: number = 10): string {
  const absGap = Math.abs(gap);
  if (absGap < threshold * 0.5) return 'text-green-500';
  if (absGap < threshold) return 'text-yellow-500';
  return 'text-red-500';
}

/**
 * Helper: Get equity gap background color class.
 *
 * @param gap - Equity gap in hours
 * @param threshold - Threshold for warning (default 10 hours)
 * @returns Tailwind background color class
 */
export function getEquityGapBgColorClass(gap: number, threshold: number = 10): string {
  const absGap = Math.abs(gap);
  if (absGap < threshold * 0.5) return 'bg-green-500';
  if (absGap < threshold) return 'bg-yellow-500';
  return 'bg-red-500';
}

/**
 * Helper: Get equity status label.
 *
 * @param gap - Equity gap in hours
 * @param threshold - Threshold for warning (default 10 hours)
 * @returns Human-readable status
 */
export function getEquityStatusLabel(gap: number, threshold: number = 10): string {
  const absGap = Math.abs(gap);
  if (absGap < threshold * 0.5) return 'Fair';
  if (gap > 0) return 'Overworked';
  return 'Underworked';
}

/**
 * Helper: Format equity gap for display.
 *
 * @param gap - Equity gap in hours
 * @returns Formatted string with sign
 */
export function formatEquityGap(gap: number): string {
  const sign = gap >= 0 ? '+' : '';
  return `${sign}${gap.toFixed(1)}h`;
}

/**
 * Helper: Calculate equity gap percentage.
 *
 * @param gap - Equity gap in hours
 * @param fairTarget - Fair workload target in hours
 * @returns Percentage deviation from fair target
 */
export function getEquityGapPercentage(gap: number, fairTarget: number): number {
  if (fairTarget === 0) return 0;
  return (gap / fairTarget) * 100;
}
