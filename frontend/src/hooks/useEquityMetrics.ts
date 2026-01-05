/**
 * Equity Metrics Hook
 *
 * React Query hook for calculating Gini coefficient and workload equity analysis
 * using the MCP equity metrics tool via the backend API proxy.
 *
 * Provides real-time equity impact preview for bulk template operations.
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { post } from '@/lib/api';
import type { ApiError } from '@/lib/api';

// ============================================================================
// Types
// ============================================================================

export interface EquityMetricsRequest {
  /** Mapping of provider ID to total hours worked */
  provider_hours: Record<string, number>;
  /** Optional intensity weights (e.g., night shift = 1.5x) */
  intensity_weights?: Record<string, number> | null;
}

export interface EquityMetricsResponse {
  /** Gini coefficient (0 = perfect equality, 1 = perfect inequality) */
  gini_coefficient: number;
  /** Whether workload distribution is equitable (Gini < 0.15) */
  is_equitable: boolean;
  /** Mean workload across all providers */
  mean_workload: number;
  /** Standard deviation of workload */
  std_workload: number;
  /** Provider ID with highest workload */
  most_overloaded_provider: string | null;
  /** Provider ID with lowest workload */
  most_underloaded_provider: string | null;
  /** Maximum workload value */
  max_workload: number;
  /** Minimum workload value */
  min_workload: number;
  /** Recommended rebalancing actions */
  recommendations: string[];
  /** Human-readable interpretation */
  interpretation: string;
}

// ============================================================================
// Query Keys
// ============================================================================

export const equityMetricsQueryKeys = {
  all: ['equity-metrics'] as const,
  calculate: (providerHours: Record<string, number>) =>
    ['equity-metrics', 'calculate', providerHours] as const,
};

// ============================================================================
// Hook
// ============================================================================

/**
 * Calculate workload equity metrics using Gini coefficient.
 *
 * Uses the MCP calculate_equity_metrics tool to quantify workload inequality.
 * Gini coefficient < 0.15 indicates equitable distribution.
 *
 * @param providerHours - Mapping of provider ID to hours worked
 * @param intensityWeights - Optional intensity multipliers per provider
 * @param options - React Query options
 * @returns Query result with Gini coefficient and recommendations
 *
 * @example
 * ```tsx
 * function EquityPreview({ selectedTemplates }: Props) {
 *   const providerHours = calculateProviderHours(selectedTemplates);
 *   const { data, isLoading } = useEquityMetrics(providerHours);
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <div className={data.is_equitable ? 'text-green-500' : 'text-red-500'}>
 *       <span>Gini: {data.gini_coefficient.toFixed(3)}</span>
 *       <p>{data.interpretation}</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function useEquityMetrics(
  providerHours: Record<string, number> | null,
  intensityWeights?: Record<string, number> | null,
  options?: Omit<
    UseQueryOptions<EquityMetricsResponse, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<EquityMetricsResponse, ApiError>({
    queryKey: equityMetricsQueryKeys.calculate(providerHours || {}),
    queryFn: async () => {
      if (!providerHours || Object.keys(providerHours).length === 0) {
        // Return default values for empty input
        return {
          gini_coefficient: 0.0,
          is_equitable: true,
          mean_workload: 0,
          std_workload: 0,
          most_overloaded_provider: null,
          most_underloaded_provider: null,
          max_workload: 0,
          min_workload: 0,
          recommendations: [],
          interpretation: 'No workload data to analyze',
        };
      }

      const request: EquityMetricsRequest = {
        provider_hours: providerHours,
        intensity_weights: intensityWeights || null,
      };

      // Call MCP tool via backend proxy
      // Note: The MCP tool name is calculate_equity_metrics_tool
      // The backend should expose this at /mcp/calculate-equity-metrics or similar
      const response = await post<EquityMetricsResponse>(
        '/mcp/calculate-equity-metrics',
        request
      );

      return response;
    },
    enabled: !!providerHours && Object.keys(providerHours).length > 0,
    staleTime: 30 * 1000, // 30 seconds - equity changes as selection changes
    ...options,
  });
}

/**
 * Helper: Calculate Gini coefficient color coding.
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
