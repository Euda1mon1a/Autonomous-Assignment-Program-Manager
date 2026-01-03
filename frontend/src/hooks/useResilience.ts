/**
 * Resilience Hooks
 *
 * React Query hooks for system resilience monitoring:
 * - System health status (utilization, defense level, N-1/N-2)
 * - Vulnerability analysis and contingency reporting
 * - Emergency coverage handling for deployments and absences
 * - Burnout risk assessment and epidemiology
 *
 * @module hooks/useResilience
 */
import {
  fetchSystemHealth,
  fetchVulnerabilityReport,
  requestEmergencyCoverage,
} from "@/api/resilience";
import { ApiError, post } from "@/lib/api";
import type {
  HealthCheckResponse,
  VulnerabilityReportResponse,
  EmergencyCoverageRequest,
  EmergencyCoverageResponse,
  BurnoutRtResponse,
  DefenseLevelResponse,
  UtilizationThresholdResponse,
} from "@/types/resilience";
import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryOptions,
  UseMutationResult,
} from "@tanstack/react-query";

// ============================================================================
// Query Keys
// ============================================================================

export const resilienceQueryKeys = {
  all: ["resilience"] as const,
  health: () => ["resilience", "health"] as const,
  vulnerability: (params?: {
    start_date?: string;
    end_date?: string;
    include_n2?: boolean;
  }) => ["resilience", "vulnerability", params] as const,
  defenseLevel: (coverageRate: number) =>
    ["resilience", "defense-level", coverageRate] as const,
  utilization: (params?: {
    available_faculty: number;
    required_blocks: number;
  }) => ["resilience", "utilization", params] as const,
  burnoutRt: (providerIds: string[]) =>
    ["resilience", "burnout-rt", providerIds] as const,
};

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetches overall system health status with real-time polling.
 *
 * This hook retrieves comprehensive resilience metrics including:
 * - Overall status (healthy/warning/degraded/critical/emergency)
 * - Utilization levels and buffer remaining
 * - Defense level (prevention -> emergency)
 * - N-1/N-2 compliance status
 * - Active fallbacks and crisis mode
 * - Recommended actions and watch items
 *
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: Health check response with all resilience metrics
 *   - `isLoading`: Whether the initial fetch is in progress
 *   - `isRefetching`: Whether a background refetch is in progress
 *   - `error`: Any error that occurred during fetch
 *   - `refetch`: Function to manually trigger a refetch
 *
 * @example
 * ```tsx
 * function ResilienceHeader() {
 *   const { data, isLoading, refetch, isRefetching } = useSystemHealth();
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return (
 *     <div className={data.crisis_mode ? 'bg-red-900' : 'bg-slate-900'}>
 *       <StatusBadge status={data.overall_status} />
 *       <DefenseLevel level={data.defense_level} />
 *       <button onClick={() => refetch()} disabled={isRefetching}>
 *         Refresh
 *       </button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useSystemHealth(
  options?: Omit<
    UseQueryOptions<HealthCheckResponse, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<HealthCheckResponse, ApiError>({
    queryKey: resilienceQueryKeys.health(),
    queryFn: () => fetchSystemHealth(),
    refetchInterval: 30000, // Poll every 30 seconds
    staleTime: 10000, // Consider data stale after 10 seconds
    ...options,
  });
}

/**
 * Fetches N-1/N-2 vulnerability analysis report.
 *
 * This hook retrieves detailed vulnerability analysis including:
 * - N-1 vulnerabilities (single-point failures)
 * - N-2 fatal pairs (dual faculty loss scenarios)
 * - Most critical faculty by centrality score
 * - Recommended mitigation actions
 *
 * Note: This is an expensive computation, so results are cached for 5 minutes.
 *
 * @param params - Optional date range and N-2 inclusion flag
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: Vulnerability report with N-1/N-2 analysis
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function VulnerabilityPanel() {
 *   const { data, isLoading, error } = useVulnerabilityReport({
 *     include_n2: true,
 *   });
 *
 *   if (isLoading) return <Skeleton />;
 *   if (error) return <ErrorMessage error={error} />;
 *
 *   return (
 *     <div>
 *       <N1StatusBadge pass={data.n1_pass} />
 *       <CriticalFacultyList faculty={data.most_critical_faculty} />
 *       <RecommendationsList actions={data.recommended_actions} />
 *     </div>
 *   );
 * }
 * ```
 */
export function useVulnerabilityReport(
  params?: {
    start_date?: string;
    end_date?: string;
    include_n2?: boolean;
  },
  options?: Omit<
    UseQueryOptions<VulnerabilityReportResponse, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<VulnerabilityReportResponse, ApiError>({
    queryKey: resilienceQueryKeys.vulnerability(params),
    queryFn: () => fetchVulnerabilityReport(params),
    staleTime: 5 * 60 * 1000, // 5 minutes (expensive call)
    ...options,
  });
}

/**
 * Fetches defense level based on current coverage rate.
 *
 * Implements the 5-level defense-in-depth strategy from nuclear reactor safety:
 * - Level 1: PREVENTION - Normal operations
 * - Level 2: CONTROL - Minor degradation
 * - Level 3: SAFETY_SYSTEMS - Active mitigation
 * - Level 4: CONTAINMENT - Crisis containment
 * - Level 5: EMERGENCY - Full emergency response
 *
 * @param coverageRate - Current coverage rate (0.0 to 1.0)
 * @param options - Optional React Query configuration options
 * @returns Query result containing defense level and recommended actions
 *
 * @example
 * ```tsx
 * function DefenseLevelIndicator({ coverageRate }: Props) {
 *   const { data, isLoading } = useDefenseLevel(coverageRate);
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <div className={`defense-level-${data.level}`}>
 *       <span>Defense Level: {data.level}</span>
 *       <p>{data.description}</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function useDefenseLevel(
  coverageRate: number,
  options?: Omit<
    UseQueryOptions<DefenseLevelResponse, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<DefenseLevelResponse, ApiError>({
    queryKey: resilienceQueryKeys.defenseLevel(coverageRate),
    queryFn: async () => {
      const response = await post<DefenseLevelResponse>(
        "/resilience/defense-level",
        { coverage_rate: coverageRate }
      );
      return response;
    },
    staleTime: 60 * 1000, // 1 minute
    enabled: coverageRate >= 0 && coverageRate <= 1,
    ...options,
  });
}

/**
 * Fetches utilization threshold analysis based on queuing theory.
 *
 * Calculates system utilization and compares to the critical 80% threshold.
 * Above 80% utilization, wait times increase exponentially and cascade
 * failures become likely (M/M/c queuing theory).
 *
 * @param params - Available faculty and required blocks
 * @param options - Optional React Query configuration options
 * @returns Query result containing utilization status and recommendations
 *
 * @example
 * ```tsx
 * function UtilizationGauge({ facultyCount, blockCount }: Props) {
 *   const { data, isLoading } = useUtilizationThreshold({
 *     available_faculty: facultyCount,
 *     required_blocks: blockCount,
 *   });
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <Gauge
 *       value={data.utilization_rate * 100}
 *       max={100}
 *       warning={80}
 *       danger={90}
 *       label={`${data.level} - ${data.message}`}
 *     />
 *   );
 * }
 * ```
 */
export function useUtilizationThreshold(
  params: {
    available_faculty: number;
    required_blocks: number;
    blocks_per_faculty_per_day?: number;
    days_in_period?: number;
  },
  options?: Omit<
    UseQueryOptions<UtilizationThresholdResponse, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<UtilizationThresholdResponse, ApiError>({
    queryKey: resilienceQueryKeys.utilization(params),
    queryFn: async () => {
      const queryParams = new URLSearchParams();
      queryParams.set("available_faculty", String(params.available_faculty));
      queryParams.set("required_blocks", String(params.required_blocks));
      if (params.blocks_per_faculty_per_day !== undefined) {
        queryParams.set(
          "blocks_per_faculty_per_day",
          String(params.blocks_per_faculty_per_day)
        );
      }
      if (params.days_in_period !== undefined) {
        queryParams.set("days_in_period", String(params.days_in_period));
      }

      const response = await post<UtilizationThresholdResponse>(
        "/resilience/utilization-threshold",
        params
      );
      return response;
    },
    staleTime: 60 * 1000, // 1 minute
    enabled:
      params.available_faculty > 0 && params.required_blocks >= 0,
    ...options,
  });
}

/**
 * Fetches burnout reproduction number (Rt) for epidemiological analysis.
 *
 * Applies SIR epidemiological modeling to understand burnout transmission
 * dynamics through social networks:
 * - Rt < 1: Epidemic declining
 * - Rt = 1: Endemic state
 * - Rt > 1: Epidemic growing
 * - Rt > 2: Aggressive intervention needed
 * - Rt > 3: Crisis level
 *
 * @param providerIds - List of provider IDs currently experiencing burnout
 * @param timeWindowDays - Time window for tracing (default: 28 days)
 * @param options - Optional React Query configuration options
 * @returns Query result containing Rt value and intervention recommendations
 *
 * @example
 * ```tsx
 * function BurnoutSpreadIndicator({ burnedOutIds }: Props) {
 *   const { data, isLoading } = useBurnoutRt(burnedOutIds);
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   const color = data.rt > 1 ? 'red' : data.rt > 0.8 ? 'yellow' : 'green';
 *
 *   return (
 *     <div className={`text-${color}-500`}>
 *       <span>Rt: {data.rt.toFixed(2)}</span>
 *       <p>{data.status}</p>
 *       {data.interventions.map(i => <li key={i}>{i}</li>)}
 *     </div>
 *   );
 * }
 * ```
 */
export function useBurnoutRt(
  providerIds: string[],
  timeWindowDays: number = 28,
  options?: Omit<
    UseQueryOptions<BurnoutRtResponse, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<BurnoutRtResponse, ApiError>({
    queryKey: resilienceQueryKeys.burnoutRt(providerIds),
    queryFn: async () => {
      const response = await post<BurnoutRtResponse>(
        "/resilience/burnout/rt",
        {
          burned_out_provider_ids: providerIds,
          time_window_days: timeWindowDays,
        }
      );
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: providerIds.length > 0,
    ...options,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Requests emergency coverage for deployments or absences.
 *
 * This mutation hook triggers automatic replacement finding for schedule gaps
 * caused by military deployments, TDY, or medical emergencies. It:
 * - Finds compatible replacement faculty
 * - Validates ACGME compliance for all substitutions
 * - Reports coverage gaps requiring manual review
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to request emergency coverage
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether the request is in progress
 *   - `isSuccess`: Whether coverage was found
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred
 *   - `data`: Coverage response with replacements and gaps
 *
 * @example
 * ```tsx
 * function EmergencyCoverageForm({ personId }: Props) {
 *   const { mutate, isPending, data } = useEmergencyCoverage();
 *
 *   const handleSubmit = (formData: EmergencyCoverageRequest) => {
 *     mutate(formData, {
 *       onSuccess: (result) => {
 *         if (result.status === 'success') {
 *           toast.success(`Coverage found: ${result.replacements_found} replacements`);
 *         } else if (result.status === 'partial') {
 *           toast.warning(`Partial coverage: ${result.coverage_gaps} gaps need review`);
 *         } else {
 *           toast.error('Unable to find coverage - manual review required');
 *         }
 *       },
 *       onError: (error) => {
 *         toast.error(`Coverage request failed: ${error.message}`);
 *       },
 *     });
 *   };
 *
 *   return (
 *     <form onSubmit={handleSubmit}>
 *       <DateRangePicker name="dates" />
 *       <TextArea name="reason" placeholder="Reason for absence" />
 *       <Checkbox name="is_deployment" label="Military deployment" />
 *       <Button type="submit" loading={isPending}>
 *         Find Coverage
 *       </Button>
 *     </form>
 *   );
 * }
 * ```
 */
export function useEmergencyCoverage(): UseMutationResult<
  EmergencyCoverageResponse,
  ApiError,
  EmergencyCoverageRequest
> {
  const queryClient = useQueryClient();

  return useMutation<
    EmergencyCoverageResponse,
    ApiError,
    EmergencyCoverageRequest
  >({
    mutationFn: requestEmergencyCoverage,
    onSuccess: () => {
      // Invalidate related queries to refresh data
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      queryClient.invalidateQueries({ queryKey: ["absences"] });
      queryClient.invalidateQueries({ queryKey: ["validation"] });
    },
  });
}
