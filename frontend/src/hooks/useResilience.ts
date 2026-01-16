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
import { ApiError, get, post } from "@/lib/api";
import type {
  HealthCheckResponse,
  VulnerabilityReportResponse,
  EmergencyCoverageRequest,
  EmergencyCoverageResponse,
  BurnoutRtResponse,
  DefenseLevelResponse,
  UtilizationThresholdResponse,
  AllBreakersStatusResponse,
  BreakerHealthResponse,
  MTFComplianceResponse,
  UnifiedCriticalIndexResponse,
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
    startDate?: string;
    endDate?: string;
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
  circuitBreakers: () => ["resilience", "circuit-breakers"] as const,
  breakerHealth: () => ["resilience", "breaker-health"] as const,
  mtfCompliance: (checkCircuitBreaker?: boolean) =>
    ["resilience", "mtf-compliance", checkCircuitBreaker] as const,
  unifiedCriticalIndex: (topN?: number) =>
    ["resilience", "unified-critical-index", topN] as const,
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
 *     <div className={data.crisisMode ? 'bg-red-900' : 'bg-slate-900'}>
 *       <StatusBadge status={data.overall_status} />
 *       <DefenseLevel level={data.defenseLevel} />
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
 *       <N1StatusBadge pass={data.n1Pass} />
 *       <CriticalFacultyList faculty={data.mostCriticalFaculty} />
 *       <RecommendationsList actions={data.recommendedActions} />
 *     </div>
 *   );
 * }
 * ```
 */
export function useVulnerabilityReport(
  params?: {
    startDate?: string;
    endDate?: string;
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
        { coverageRate: coverageRate }
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
 *       value={data.utilizationRate * 100}
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
 *           toast.success(`Coverage found: ${result.replacementsFound} replacements`);
 *         } else if (result.status === 'partial') {
 *           toast.warning(`Partial coverage: ${result.coverageGaps} gaps need review`);
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
 *       <Checkbox name="isDeployment" label="Military deployment" />
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

// ============================================================================
// Circuit Breaker Hooks (Netflix Hystrix Pattern)
// ============================================================================

/**
 * Fetches status of all circuit breakers.
 *
 * Circuit breakers provide failure isolation based on the Netflix Hystrix pattern:
 * - CLOSED: Normal operation, requests pass through
 * - OPEN: Circuit tripped due to failures, requests fail fast
 * - HALF_OPEN: Testing recovery, limited requests allowed
 *
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: All breakers status with health assessment
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function CircuitBreakerPanel() {
 *   const { data, isLoading } = useCircuitBreakers();
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <div>
 *       <StatusBadge status={data.overallHealth} />
 *       <span>Open: {data.openBreakers} / {data.totalBreakers}</span>
 *       {data.breakers.map(b => (
 *         <BreakerCard key={b.name} breaker={b} />
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useCircuitBreakers(
  options?: Omit<
    UseQueryOptions<AllBreakersStatusResponse, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<AllBreakersStatusResponse, ApiError>({
    queryKey: resilienceQueryKeys.circuitBreakers(),
    queryFn: async () => {
      const response = await get<AllBreakersStatusResponse>(
        "/resilience/circuit-breakers"
      );
      return response;
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 30 * 1000, // Auto-refresh every 30 seconds
    ...options,
  });
}

/**
 * Fetches aggregated health metrics for all circuit breakers.
 *
 * Provides a high-level health assessment across all circuit breakers:
 * - Aggregated metrics (failure rates, rejections)
 * - Trend analysis (improving, stable, degrading)
 * - Severity assessment (healthy, warning, critical, emergency)
 * - Breakers needing immediate attention
 *
 * @param options - Optional React Query configuration options
 * @returns Query result containing aggregated health metrics
 *
 * @example
 * ```tsx
 * function BreakerHealthSummary() {
 *   const { data, isLoading } = useBreakerHealth();
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <div className={`severity-${data.severity}`}>
 *       <span>Failure Rate: {(data.metrics.overallFailureRate * 100).toFixed(1)}%</span>
 *       <span>Trend: {data.trendAnalysis}</span>
 *       {data.breakersNeedingAttention.length > 0 && (
 *         <Alert>Attention needed: {data.breakersNeedingAttention.join(', ')}</Alert>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */
export function useBreakerHealth(
  options?: Omit<
    UseQueryOptions<BreakerHealthResponse, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<BreakerHealthResponse, ApiError>({
    queryKey: resilienceQueryKeys.breakerHealth(),
    queryFn: async () => {
      const response = await get<BreakerHealthResponse>(
        "/resilience/circuit-breakers/health"
      );
      return response;
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 30 * 1000, // Auto-refresh every 30 seconds
    ...options,
  });
}

// ============================================================================
// MTF Compliance Hooks (Military Multi-Tier Functionality)
// ============================================================================

/**
 * Fetches MTF compliance status with military readiness ratings.
 *
 * Translates scheduling metrics into military reporting format:
 * - DRRS C-ratings (C1-C5): Overall readiness category
 * - P-ratings (P1-P4): Personnel status
 * - S-ratings (S1-S4): Capability status
 * - Iron Dome status: Regulatory protection level
 *
 * @param checkCircuitBreaker - Whether to include circuit breaker status (default: true)
 * @param options - Optional React Query configuration options
 * @returns Query result containing military compliance metrics
 *
 * @example
 * ```tsx
 * function CompliancePanel() {
 *   const { data, isLoading } = useMTFCompliance(true);
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <div>
 *       <DRRSBadge category={data.drrsCategory} />
 *       <span>Mission: {data.missionCapability}</span>
 *       <IronDomeIndicator status={data.ironDomeStatus} />
 *       {data.deficiencies.length > 0 && (
 *         <DeficiencyList items={data.deficiencies} />
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */
export function useMTFCompliance(
  checkCircuitBreaker: boolean = true,
  options?: Omit<
    UseQueryOptions<MTFComplianceResponse, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<MTFComplianceResponse, ApiError>({
    queryKey: resilienceQueryKeys.mtfCompliance(checkCircuitBreaker),
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set("check_circuit_breaker", String(checkCircuitBreaker));
      const response = await get<MTFComplianceResponse>(
        `/resilience/mtf-compliance?${params.toString()}`
      );
      return response;
    },
    staleTime: 60 * 1000, // 1 minute
    ...options,
  });
}

// ============================================================================
// Unified Critical Index Hooks (Multi-Factor Risk Aggregation)
// ============================================================================

/**
 * Fetches unified critical index aggregating all resilience signals.
 *
 * Combines signals from three domains into a single actionable risk score:
 * 1. Contingency (N-1/N-2 Vulnerability) - Weight: 40%
 * 2. Epidemiology (Burnout Super-Spreader) - Weight: 25%
 * 3. Hub Analysis (Network Centrality) - Weight: 35%
 *
 * Risk Patterns:
 * - UNIVERSAL_CRITICAL: All domains high - maximum risk
 * - STRUCTURAL_BURNOUT: Contingency + Epidemiology high
 * - INFLUENTIAL_HUB: Contingency + Hub high
 * - SOCIAL_CONNECTOR: Epidemiology + Hub high
 * - LOW_RISK: No domains elevated
 *
 * @param topN - Number of top-risk faculty to return (default: 5)
 * @param options - Optional React Query configuration options
 * @returns Query result containing unified risk assessment
 *
 * @example
 * ```tsx
 * function CriticalFacultyPanel() {
 *   const { data, isLoading } = useUnifiedCriticalIndex(5);
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <div>
 *       <RiskGauge value={data.overallIndex} level={data.riskLevel} />
 *       <span>Critical: {data.criticalCount} / {data.totalFaculty}</span>
 *       {data.topCriticalFaculty.map(f => (
 *         <FacultyRiskCard key={f.facultyId} faculty={f} />
 *       ))}
 *       <RecommendationsList items={data.recommendations} />
 *     </div>
 *   );
 * }
 * ```
 */
export function useUnifiedCriticalIndex(
  topN: number = 5,
  options?: Omit<
    UseQueryOptions<UnifiedCriticalIndexResponse, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<UnifiedCriticalIndexResponse, ApiError>({
    queryKey: resilienceQueryKeys.unifiedCriticalIndex(topN),
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set("top_n", String(topN));
      params.set("include_details", "true");
      const response = await post<UnifiedCriticalIndexResponse>(
        "/resilience/unified-critical-index",
        { topN, includeDetails: true }
      );
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes (expensive computation)
    ...options,
  });
}
