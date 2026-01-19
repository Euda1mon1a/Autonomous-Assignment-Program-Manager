/**
 * Resilience API Client
 *
 * API functions for the resilience framework:
 * - System health monitoring
 * - Vulnerability analysis (N-1/N-2)
 * - Emergency coverage handling
 * - Defense level and utilization thresholds
 *
 * @module api/resilience
 */
import { get, post } from "@/lib/api";
import type {
  HealthCheckResponse,
  VulnerabilityReportResponse,
  EmergencyCoverageRequest,
  EmergencyCoverageResponse,
} from "@/types/resilience";

const BASE_URL = "/resilience";

/**
 * Fetches the current system health status.
 *
 * @param includeContingency - Whether to include expensive contingency analysis
 * @returns Health check response with all resilience metrics
 */
export async function fetchSystemHealth(
  includeContingency: boolean = false
): Promise<HealthCheckResponse> {
  return get<HealthCheckResponse>(
    `${BASE_URL}/health?include_contingency=${includeContingency}`
  );
}

/**
 * Fetches detailed vulnerability report with N-1/N-2 analysis.
 *
 * Note: This is an expensive computation call.
 *
 * @param params - Optional date range and N-2 inclusion flag
 * @returns Vulnerability report with critical faculty and recommendations
 */
export async function fetchVulnerabilityReport(params?: {
  startDate?: string;
  endDate?: string;
  include_n2?: boolean;
}): Promise<VulnerabilityReportResponse> {
  const queryParams = new URLSearchParams();
  // URL query params MUST use snake_case (backend expects snake_case)
  if (params?.startDate) queryParams.set("start_date", params.startDate);
  if (params?.endDate) queryParams.set("end_date", params.endDate);
  if (params?.include_n2 !== undefined)
    queryParams.set("include_n2", String(params.include_n2));

  return get<VulnerabilityReportResponse>(
    `${BASE_URL}/vulnerability?${queryParams.toString()}`
  );
}

/**
 * Requests emergency coverage for a faculty absence.
 *
 * Triggers automatic replacement finding for schedule gaps caused by
 * military deployments, TDY, or medical emergencies.
 *
 * @param request - Emergency coverage request with person ID and date range
 * @returns Coverage response with replacements found and any gaps
 */
export async function requestEmergencyCoverage(
  request: EmergencyCoverageRequest
): Promise<EmergencyCoverageResponse> {
  return post<EmergencyCoverageResponse>(
    "/schedule/emergency-coverage",
    request
  );
}
