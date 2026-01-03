/**
 * Resilience API Client
 */
import { get } from "@/lib/api";
import type {
  HealthCheckResponse,
  VulnerabilityReportResponse,
} from "@/types/resilience";

const BASE_URL = "/resilience";

export async function fetchSystemHealth(): Promise<HealthCheckResponse> {
  // Pass include_contingency=false by default for faster polling
  return get<HealthCheckResponse>(
    `${BASE_URL}/health?include_contingency=false`
  );
}

export async function fetchVulnerabilityReport(params?: {
  start_date?: string;
  end_date?: string;
  include_n2?: boolean;
}): Promise<VulnerabilityReportResponse> {
  const queryParams = new URLSearchParams();
  if (params?.start_date) queryParams.set("start_date", params.start_date);
  if (params?.end_date) queryParams.set("end_date", params.end_date);
  if (params?.include_n2 !== undefined)
    queryParams.set("include_n2", String(params.include_n2));

  // Note: This endpoint is expensive to call
  return get<VulnerabilityReportResponse>(
    `${BASE_URL}/vulnerability?${queryParams.toString()}`
  );
}
