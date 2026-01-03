/**
 * Resilience Hooks
 */
import { fetchSystemHealth, fetchVulnerabilityReport } from "@/api/resilience";
import { ApiError } from "@/lib/api";
import type {
  HealthCheckResponse,
  VulnerabilityReportResponse,
} from "@/types/resilience";
import { useQuery, UseQueryOptions } from "@tanstack/react-query";

export const resilienceQueryKeys = {
  all: ["resilience"] as const,
  health: () => ["resilience", "health"] as const,
  vulnerability: (params?: any) =>
    ["resilience", "vulnerability", params] as const,
};

export function useSystemHealth(
  options?: Omit<
    UseQueryOptions<HealthCheckResponse, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<HealthCheckResponse, ApiError>({
    queryKey: resilienceQueryKeys.health(),
    queryFn: fetchSystemHealth,
    refetchInterval: 30000, // Poll every 30 seconds
    staleTime: 10000, // Consider data stale after 10 seconds
    ...options,
  });
}

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
