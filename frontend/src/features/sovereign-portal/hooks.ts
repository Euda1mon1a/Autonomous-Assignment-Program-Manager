/**
 * Sovereign Portal Hooks
 *
 * React Query hooks for fetching real data to populate the command dashboard.
 * Aggregates data from multiple backend APIs:
 * - /api/v1/resilience/health - System fragility and resilience metrics
 * - /api/v1/visualization/coverage - Spatial coverage metrics
 *
 * Note: Fairness metrics require POST with provider data. For the dashboard,
 * we derive basic fairness from the health/coverage responses or use defaults.
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { get, ApiError } from '@/lib/api';
import type {
  DashboardState,
  SpatialMetrics,
  FairnessMetrics,
  SolverMetrics,
  FragilityMetrics,
  SystemAlert,
  SystemStatus,
} from './types';

// ============================================================================
// API Response Types (camelCase - axios converts from snake_case)
// ============================================================================

/**
 * Response from /resilience/health endpoint
 */
interface HealthCheckResponse {
  timestamp: string;
  overallStatus: 'GREEN' | 'YELLOW' | 'RED';
  utilization: {
    utilizationRate: number;
    level: string;
    bufferRemaining: number;
  };
  defenseLevel: string;
  redundancyStatus: Array<{
    service: string;
    status: string; // N+2, N+1, N+0, BELOW
    available: number;
    minimumRequired: number;
    buffer: number;
  }>;
  loadSheddingLevel: string;
  activeFallbacks: string[];
  crisisMode: boolean;
  n1Pass: boolean;
  n2Pass: boolean;
  phaseTransitionRisk: string;
  immediateActions: string[];
  watchItems: string[];
}

/**
 * Response from /visualization/coverage endpoint
 */
interface CoverageHeatmapResponse {
  data: {
    xLabels: string[];
    yLabels: string[];
    zValues: number[][];
    colorScale: string;
    annotations: unknown;
  };
  coveragePercentage: number;
  gaps: Array<{
    date: string;
    timeOfDay: string;
    rotation: string;
    severity: string;
  }>;
  title: string;
  generatedAt: string;
}

// ============================================================================
// Query Keys
// ============================================================================

export const sovereignQueryKeys = {
  all: ['sovereign'] as const,
  health: () => ['sovereign', 'health'] as const,
  coverage: (startDate: string, endDate: string) =>
    ['sovereign', 'coverage', startDate, endDate] as const,
  dashboard: (startDate: string, endDate: string) =>
    ['sovereign', 'dashboard', startDate, endDate] as const,
};

// ============================================================================
// Individual Query Hooks
// ============================================================================

/**
 * Fetch system health and fragility metrics
 */
export function useSystemHealth(
  options?: Omit<UseQueryOptions<HealthCheckResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<HealthCheckResponse, ApiError>({
    queryKey: sovereignQueryKeys.health(),
    queryFn: () => get<HealthCheckResponse>('/resilience/health'),
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Fetch coverage heatmap and gap analysis
 */
export function useCoverageMetrics(
  startDate: string,
  endDate: string,
  options?: Omit<UseQueryOptions<CoverageHeatmapResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<CoverageHeatmapResponse, ApiError>({
    queryKey: sovereignQueryKeys.coverage(startDate, endDate),
    queryFn: () =>
      get<CoverageHeatmapResponse>(
        `/visualization/coverage?start_date=${startDate}&end_date=${endDate}`
      ),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!startDate && !!endDate,
    ...options,
  });
}

// ============================================================================
// Data Transformation Utilities
// ============================================================================

/**
 * Check if redundancy status is adequate
 * Derives adequacy from status string: N+2/N+1 are adequate, N+0/BELOW are not
 */
function isAdequate(item: { status: string }): boolean {
  return item.status !== 'N+0' && item.status !== 'BELOW';
}

/**
 * Map overall status to SystemStatus type
 */
function mapOverallStatus(status: string): SystemStatus {
  switch (status) {
    case 'GREEN':
      return 'OPERATIONAL';
    case 'YELLOW':
      return 'DEGRADED';
    case 'RED':
      return 'CRITICAL';
    default:
      return 'OFFLINE';
  }
}

/**
 * Extract fragility metrics from health check response
 */
function extractFragilityMetrics(health: HealthCheckResponse): FragilityMetrics {
  // Calculate system fragility based on various factors
  const utilizationFactor = health.utilization.utilizationRate / 100;
  const redundancyFactor = health.redundancyStatus.filter((r) => !isAdequate(r)).length /
    Math.max(health.redundancyStatus.length, 1);
  const criticalityFactor = health.crisisMode ? 0.5 : 0;

  // Weighted fragility score (0-1)
  const systemFragility = Math.min(
    1,
    utilizationFactor * 0.3 + redundancyFactor * 0.4 + criticalityFactor * 0.3
  );

  // Count critical paths (services with inadequate redundancy)
  const criticalPaths = health.redundancyStatus.filter((r) => !isAdequate(r)).length;

  // Calculate redundancy level as percentage
  const totalRedundancy = health.redundancyStatus.reduce(
    (sum, r) => sum + (r.available - r.minimumRequired),
    0
  );
  const totalRequired = health.redundancyStatus.reduce((sum, r) => sum + r.minimumRequired, 0);
  const redundancyLevel = totalRequired > 0
    ? Math.max(0, Math.min(100, ((totalRequired + totalRedundancy) / totalRequired) * 50))
    : 100;

  return {
    systemFragility: Math.round(systemFragility * 100) / 100,
    criticalPaths,
    redundancyLevel: Math.round(redundancyLevel),
  };
}

/**
 * Extract spatial metrics from coverage response
 */
function extractSpatialMetrics(coverage: CoverageHeatmapResponse): SpatialMetrics {
  // Calculate distribution score from z-values variance
  const allValues = coverage.data.zValues.flat();
  const mean = allValues.reduce((a, b) => a + b, 0) / Math.max(allValues.length, 1);
  const variance = allValues.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) /
    Math.max(allValues.length, 1);
  const stdDev = Math.sqrt(variance);

  // Distribution score: 1 = uniform, 0 = highly variable
  // Normalize by mean to get coefficient of variation, then invert
  const cv = mean > 0 ? stdDev / mean : 0;
  const distributionScore = Math.max(0, Math.min(1, 1 - cv));

  return {
    coveragePercent: Math.round(coverage.coveragePercentage * 10) / 10,
    gapCount: coverage.gaps.length,
    distributionScore: Math.round(distributionScore * 100) / 100,
  };
}

/**
 * Generate solver metrics placeholder
 * Note: Real solver metrics would come from schedule generation status
 */
function generateSolverMetrics(health: HealthCheckResponse): SolverMetrics {
  // Derive from health status as proxy
  const isFeasible = health.overallStatus !== 'RED';
  const satisfactionRate = health.overallStatus === 'GREEN' ? 0.98 :
    health.overallStatus === 'YELLOW' ? 0.85 : 0.65;

  return {
    objectiveValue: Math.round(1000 + satisfactionRate * 500),
    constraintsSatisfied: Math.round(satisfactionRate * 150),
    constraintsTotal: 150,
    solutionQuality: isFeasible ? 'feasible' : 'infeasible',
  };
}

/**
 * Generate fairness metrics placeholder
 * Note: Real fairness requires provider workload data via POST
 */
function generateFairnessMetrics(health: HealthCheckResponse): FairnessMetrics {
  // Use health status as proxy for workload balance
  const baseGini = health.overallStatus === 'GREEN' ? 0.08 :
    health.overallStatus === 'YELLOW' ? 0.15 : 0.25;

  // Add some variation based on utilization
  const utilizationFactor = (health.utilization.utilizationRate - 50) / 500;
  const giniCoefficient = Math.max(0, Math.min(1, baseGini + utilizationFactor));

  // Jain's Index: higher is better (1 = perfect fairness)
  const jainsIndex = Math.max(0, Math.min(1, 1 - giniCoefficient * 1.2));

  // Max deviation percentage
  const maxDeviation = Math.round(giniCoefficient * 100);

  return {
    giniCoefficient: Math.round(giniCoefficient * 100) / 100,
    jainsIndex: Math.round(jainsIndex * 100) / 100,
    maxDeviation,
  };
}

/**
 * Generate alerts from health and coverage data
 */
function generateAlerts(
  health: HealthCheckResponse | null,
  coverage: CoverageHeatmapResponse | null
): SystemAlert[] {
  const alerts: SystemAlert[] = [];

  // Alerts from immediate actions
  if (health?.immediateActions) {
    health.immediateActions.forEach((action, idx) => {
      alerts.push({
        id: `health-action-${idx}`,
        panel: 'fragility',
        severity: 'warning',
        message: action,
        timestamp: new Date(health.timestamp),
      });
    });
  }

  // Alerts from watch items
  if (health?.watchItems) {
    health.watchItems.slice(0, 2).forEach((item, idx) => {
      alerts.push({
        id: `health-watch-${idx}`,
        panel: 'fragility',
        severity: 'info',
        message: item,
        timestamp: new Date(health.timestamp),
      });
    });
  }

  // Alerts from coverage gaps
  if (coverage?.gaps) {
    const criticalGaps = coverage.gaps.filter((g) => g.severity === 'high');
    if (criticalGaps.length > 0) {
      alerts.push({
        id: 'coverage-gaps',
        panel: 'spatial',
        severity: 'warning',
        message: `${criticalGaps.length} critical coverage gap${criticalGaps.length > 1 ? 's' : ''} detected`,
        timestamp: new Date(),
      });
    }

    if (coverage.coveragePercentage < 90) {
      alerts.push({
        id: 'coverage-low',
        panel: 'spatial',
        severity: coverage.coveragePercentage < 80 ? 'critical' : 'warning',
        message: `Overall coverage at ${coverage.coveragePercentage.toFixed(1)}%`,
        timestamp: new Date(),
      });
    }
  }

  // Sort by timestamp descending
  return alerts.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
}

// ============================================================================
// Aggregate Dashboard Hook
// ============================================================================

/**
 * Get date range for dashboard queries
 * Default: current week
 */
function getDefaultDateRange(): { startDate: string; endDate: string } {
  const now = new Date();
  const startOfWeek = new Date(now);
  startOfWeek.setDate(now.getDate() - now.getDay());

  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(startOfWeek.getDate() + 6);

  return {
    startDate: startOfWeek.toISOString().split('T')[0],
    endDate: endOfWeek.toISOString().split('T')[0],
  };
}

/**
 * Aggregate hook for the Sovereign Dashboard
 *
 * Fetches and aggregates data from multiple endpoints into the DashboardState shape.
 * Handles partial data gracefully by providing sensible defaults.
 */
export function useSovereignDashboard(options?: {
  startDate?: string;
  endDate?: string;
  refetchInterval?: number;
}) {
  const { startDate, endDate } = options?.startDate && options?.endDate
    ? { startDate: options.startDate, endDate: options.endDate }
    : getDefaultDateRange();

  const refetchInterval = options?.refetchInterval ?? 30000; // 30 seconds default

  // Fetch health data
  const healthQuery = useQuery<HealthCheckResponse, ApiError>({
    queryKey: sovereignQueryKeys.health(),
    queryFn: () => get<HealthCheckResponse>('/resilience/health'),
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
    refetchInterval,
  });

  // Fetch coverage data
  const coverageQuery = useQuery<CoverageHeatmapResponse, ApiError>({
    queryKey: sovereignQueryKeys.coverage(startDate, endDate),
    queryFn: () =>
      get<CoverageHeatmapResponse>(
        `/visualization/coverage?start_date=${startDate}&end_date=${endDate}`
      ),
    staleTime: 60 * 1000,
    gcTime: 5 * 60 * 1000,
    refetchInterval,
  });

  // Aggregate data into DashboardState
  const data: DashboardState | null = (() => {
    // Need at least health data to show anything meaningful
    if (!healthQuery.data) {
      return null;
    }

    const health = healthQuery.data;
    const coverage = coverageQuery.data ?? null;

    // Extract metrics from responses
    const fragility = extractFragilityMetrics(health);
    const spatial = coverage
      ? extractSpatialMetrics(coverage)
      : { coveragePercent: 0, gapCount: 0, distributionScore: 0 };
    const solver = generateSolverMetrics(health);
    const fairness = generateFairnessMetrics(health);
    const alerts = generateAlerts(health, coverage);

    return {
      status: mapOverallStatus(health.overallStatus),
      spatial,
      fairness,
      solver,
      fragility,
      alerts,
      lastUpdate: new Date(health.timestamp),
    };
  })();

  return {
    data,
    isLoading: healthQuery.isLoading,
    isError: healthQuery.isError || coverageQuery.isError,
    error: healthQuery.error || coverageQuery.error,
    isFetching: healthQuery.isFetching || coverageQuery.isFetching,
    refetch: async () => {
      await Promise.all([healthQuery.refetch(), coverageQuery.refetch()]);
    },
    // Expose individual query states for fine-grained loading UI
    queries: {
      health: healthQuery,
      coverage: coverageQuery,
    },
  };
}

// ============================================================================
// Export types for consumers
// ============================================================================

export type { HealthCheckResponse, CoverageHeatmapResponse };
