/**
 * Lorenz Curve Hook
 *
 * React Query hook for generating Lorenz curve data for workload inequality
 * visualization. Uses the MCP generate_lorenz_curve tool via backend proxy.
 *
 * The Lorenz curve plots cumulative share of population (x-axis) against
 * cumulative share of value (y-axis). Perfect equality is the 45-degree
 * diagonal line. The Gini coefficient equals twice the area between the
 * Lorenz curve and the equality line.
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { post } from '@/lib/api';
import type { ApiError } from '@/lib/api';

// ============================================================================
// Types
// ============================================================================

export interface LorenzCurveRequest {
  /** List of workload values to analyze */
  values: number[];
}

export interface LorenzCurveResponse {
  /** Cumulative population share (x-axis) */
  populationShares: number[];
  /** Cumulative value share (y-axis) - the Lorenz curve */
  valueShares: number[];
  /** 45-degree equality line for comparison */
  equalityLine: number[];
  /** Gini coefficient calculated from curve (0-1) */
  giniCoefficient: number;
}

/** Data point for Recharts visualization */
export interface LorenzDataPoint {
  /** Population percentage (0-100) */
  population: number;
  /** Value percentage on Lorenz curve */
  lorenz: number;
  /** Value percentage on equality line */
  equality: number;
}

// ============================================================================
// Query Keys
// ============================================================================

export const lorenzCurveQueryKeys = {
  all: ['lorenz-curve'] as const,
  generate: (values: number[]) =>
    ['lorenz-curve', 'generate', values.sort((a, b) => a - b).join(',')] as const,
};

// ============================================================================
// Hook
// ============================================================================

/**
 * Generate Lorenz curve data for workload inequality visualization.
 *
 * Uses the MCP generate_lorenz_curve tool to calculate the curve coordinates.
 * Returns data formatted for Recharts AreaChart visualization.
 *
 * @param values - Array of workload values (e.g., hours per faculty)
 * @param options - React Query options
 * @returns Query result with Lorenz curve data points
 *
 * @example
 * ```tsx
 * function WorkloadDistribution({ workloads }: Props) {
 *   const values = workloads.map(w => w.totalScore);
 *   const { data, isLoading } = useLorenzCurve(values);
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <AreaChart data={data.chartData}>
 *       <Area dataKey="lorenz" fill="blue" />
 *       <Line dataKey="equality" stroke="gray" strokeDasharray="5 5" />
 *     </AreaChart>
 *   );
 * }
 * ```
 */
export function useLorenzCurve(
  values: number[] | null,
  options?: Omit<
    UseQueryOptions<LorenzCurveResponse & { chartData: LorenzDataPoint[] }, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<LorenzCurveResponse & { chartData: LorenzDataPoint[] }, ApiError>({
    queryKey: lorenzCurveQueryKeys.generate(values || []),
    queryFn: async () => {
      if (!values || values.length === 0) {
        // Return default empty data
        return {
          populationShares: [0, 1],
          valueShares: [0, 1],
          equalityLine: [0, 1],
          giniCoefficient: 0,
          chartData: [
            { population: 0, lorenz: 0, equality: 0 },
            { population: 100, lorenz: 100, equality: 100 },
          ],
        };
      }

      const request: LorenzCurveRequest = { values };

      // Call MCP tool via backend proxy
      const response = await post<LorenzCurveResponse>(
        '/mcp/generate-lorenz-curve',
        request
      );

      // Transform to Recharts-friendly format
      const chartData: LorenzDataPoint[] = response.populationShares.map(
        (pop, index) => ({
          population: pop * 100,
          lorenz: response.valueShares[index] * 100,
          equality: response.equalityLine[index] * 100,
        })
      );

      return {
        ...response,
        chartData,
      };
    },
    enabled: !!values && values.length > 0,
    staleTime: 60 * 1000, // 1 minute - curve doesn't change frequently
    ...options,
  });
}

/**
 * Helper: Get Gini coefficient color class for visualization.
 *
 * @param gini - Gini coefficient value (0-1)
 * @returns Tailwind color class
 */
export function getGiniColorClass(gini: number): string {
  if (gini < 0.15) return 'text-green-500';
  if (gini < 0.25) return 'text-yellow-500';
  return 'text-red-500';
}

/**
 * Helper: Get Gini coefficient background color class.
 *
 * @param gini - Gini coefficient value (0-1)
 * @returns Tailwind background color class
 */
export function getGiniBgColorClass(gini: number): string {
  if (gini < 0.15) return 'bg-green-500';
  if (gini < 0.25) return 'bg-yellow-500';
  return 'bg-red-500';
}

/**
 * Helper: Get Gini coefficient interpretation label.
 *
 * @param gini - Gini coefficient value (0-1)
 * @returns Human-readable label
 */
export function getGiniLabel(gini: number): string {
  if (gini < 0.15) return 'Equitable';
  if (gini < 0.25) return 'Moderate Inequality';
  return 'High Inequality';
}

/**
 * Helper: Generate interpretation text for Lorenz curve.
 *
 * @param gini - Gini coefficient value (0-1)
 * @param bottomHalfShare - What share the bottom 50% of faculty have
 * @returns Human-readable interpretation
 */
export function getLorenzInterpretation(
  gini: number,
  bottomHalfShare?: number
): string {
  const shareText = bottomHalfShare
    ? `The bottom 50% of faculty account for ${(bottomHalfShare * 100).toFixed(1)}% of total workload.`
    : '';

  if (gini < 0.15) {
    return `Workload is distributed equitably across faculty. ${shareText} No rebalancing needed.`;
  }
  if (gini < 0.25) {
    return `Moderate inequality in workload distribution. ${shareText} Consider reviewing assignments for outliers.`;
  }
  return `High inequality detected - significant workload imbalance. ${shareText} Immediate rebalancing recommended to prevent burnout.`;
}
