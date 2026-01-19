/**
 * useSynapseData Hook
 *
 * Fetches resilience health data from the backend API and maps it to
 * personnel-like metrics for the SynapseMonitor visualization.
 *
 * Since there's no direct wellness endpoint, this hook derives cognitive
 * load and burnout metrics from the resilience health API.
 */

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Personnel, AcuityLevel, RiskLevel } from "./types";

/**
 * API Response types (camelCase - converted by axios interceptor)
 */
interface UtilizationMetrics {
  utilizationRate: number;
  level: string;
  bufferRemaining: number;
  waitTimeMultiplier: number;
  safeCapacity: number;
  currentDemand: number;
  theoreticalCapacity: number;
}

interface RedundancyStatus {
  service: string;
  status: string;
  available: number;
  minimumRequired: number;
  buffer: number;
}

interface HealthCheckResponse {
  timestamp: string;
  overallStatus: string;
  utilization: UtilizationMetrics;
  defenseLevel: string;
  redundancyStatus: RedundancyStatus[];
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
 * Maps utilization level to acuity
 */
function mapUtilizationToAcuity(level: string): AcuityLevel {
  switch (level.toUpperCase()) {
    case "BLACK":
      return "Critical";
    case "RED":
      return "High";
    case "ORANGE":
      return "Med";
    case "YELLOW":
      return "Med";
    case "GREEN":
    default:
      return "Low";
  }
}

/**
 * Maps phase transition risk to risk level
 */
function mapPhaseTransitionToRisk(risk: string): RiskLevel {
  switch (risk.toLowerCase()) {
    case "critical":
      return "Critical";
    case "high":
      return "High";
    case "medium":
      return "Med";
    case "low":
    default:
      return "Low";
  }
}

/**
 * Maps defense level to a rank prefix for the synthetic personnel name
 */
function getDefenseLevelRank(defenseLevel: string): string {
  switch (defenseLevel.toUpperCase()) {
    case "EMERGENCY":
      return "GEN"; // General - highest alert
    case "CONTAINMENT":
      return "COL"; // Colonel
    case "SAFETY_SYSTEMS":
      return "LTC"; // Lieutenant Colonel
    case "CONTROL":
      return "MAJ"; // Major
    case "PREVENTION":
    default:
      return "CPT"; // Captain - nominal state
  }
}

/**
 * Generates synthetic personnel entries from health data
 * Each redundancy status becomes a "personnel" entry representing system subsystem health
 */
function mapHealthToPersonnel(health: HealthCheckResponse): Personnel[] {
  const personnel: Personnel[] = [];

  // Create a system-wide personnel entry based on overall health
  const systemUtilization = health.utilization.utilizationRate;
  const systemReserve = Math.round((1 - systemUtilization) * 100);
  const systemDebt = Math.round(systemUtilization * 48); // Max 48h sleep debt at 100% utilization

  personnel.push({
    name: `${getDefenseLevelRank(health.defenseLevel)} System`,
    debt: systemDebt,
    reserve: systemReserve,
    acuity: mapUtilizationToAcuity(health.utilization.level),
    risk: mapPhaseTransitionToRisk(health.phaseTransitionRisk),
    unit: `Defense: ${health.defenseLevel}`,
  });

  // Create personnel entries from redundancy status (each service as a "unit")
  health.redundancyStatus.forEach((status, index) => {
    // Calculate synthetic metrics based on redundancy buffer
    const bufferRatio = status.minimumRequired > 0
      ? status.buffer / status.minimumRequired
      : 1;
    const reserve = Math.max(0, Math.min(100, Math.round(bufferRatio * 100)));
    const debt = Math.round((1 - bufferRatio) * 40);

    // Determine acuity based on status
    let acuity: AcuityLevel;
    switch (status.status) {
      case "BELOW":
        acuity = "Critical";
        break;
      case "N+0":
        acuity = "High";
        break;
      case "N+1":
        acuity = "Med";
        break;
      case "N+2":
      default:
        acuity = "Low";
    }

    // Risk based on availability vs minimum
    let risk: RiskLevel;
    if (status.available < status.minimumRequired) {
      risk = "Critical";
    } else if (status.buffer === 0) {
      risk = "High";
    } else if (status.buffer === 1) {
      risk = "Med";
    } else {
      risk = "Low";
    }

    // Generate rank based on service priority (lower index = higher priority assumed)
    const ranks = ["LTC", "MAJ", "MAJ", "CPT", "CPT", "1LT", "2LT", "WO1"];
    const rank = ranks[Math.min(index, ranks.length - 1)];

    personnel.push({
      name: `${rank} ${formatServiceName(status.service)}`,
      debt: Math.max(0, debt),
      reserve: reserve,
      acuity: acuity,
      risk: risk,
      unit: `${status.available}/${status.minimumRequired} available`,
    });
  });

  // If crisis mode is active, add a crisis indicator personnel
  if (health.crisisMode) {
    personnel.unshift({
      name: "GEN Crisis",
      debt: 48,
      reserve: 5,
      acuity: "Critical",
      risk: "Critical",
      unit: "CRISIS MODE ACTIVE",
    });
  }

  // If we have no redundancy data, create synthetic entries from utilization
  if (personnel.length === 1) {
    // Add synthetic entries based on utilization bands
    const bands = [
      { name: "Alpha Sector", factor: 1.0 },
      { name: "Bravo Sector", factor: 0.9 },
      { name: "Charlie Sector", factor: 0.8 },
      { name: "Delta Sector", factor: 1.1 },
    ];

    bands.forEach((band, index) => {
      const adjustedUtil = Math.min(1, systemUtilization * band.factor);
      const reserve = Math.round((1 - adjustedUtil) * 100);
      const debt = Math.round(adjustedUtil * 40);

      const ranks = ["MAJ", "CPT", "CPT", "1LT"];

      personnel.push({
        name: `${ranks[index]} ${band.name}`,
        debt: debt,
        reserve: reserve,
        acuity: reserve < 30 ? "Critical" : reserve < 50 ? "High" : reserve < 70 ? "Med" : "Low",
        risk: debt > 30 ? "Critical" : debt > 20 ? "High" : debt > 10 ? "Med" : "Low",
        unit: `Util: ${Math.round(adjustedUtil * 100)}%`,
      });
    });
  }

  return personnel;
}

/**
 * Formats a service name for display
 */
function formatServiceName(service: string): string {
  // Convert snake_case or SCREAMING_CASE to Title Case
  return service
    .toLowerCase()
    .split(/[_\s]+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 15); // Keep names short
}

/**
 * Hook to fetch and transform resilience health data for SynapseMonitor
 */
export function useSynapseData() {
  const healthQuery = useQuery<HealthCheckResponse>({
    queryKey: ["resilience", "health"],
    queryFn: async () => {
      const response = await api.get<HealthCheckResponse>("/resilience/health");
      return response.data;
    },
    // Refresh every 30 seconds for real-time monitoring feel
    refetchInterval: 30000,
    // Keep stale data while refetching
    staleTime: 10000,
    // Retry on failure with backoff
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  // Map health data to personnel structure
  const personnel = useMemo<Personnel[]>(() => {
    if (!healthQuery.data) {
      return [];
    }
    return mapHealthToPersonnel(healthQuery.data);
  }, [healthQuery.data]);

  // Extract additional metrics for potential use
  const systemMetrics = useMemo(() => {
    if (!healthQuery.data) {
      return null;
    }
    return {
      overallStatus: healthQuery.data.overallStatus,
      defenseLevel: healthQuery.data.defenseLevel,
      crisisMode: healthQuery.data.crisisMode,
      n1Pass: healthQuery.data.n1Pass,
      n2Pass: healthQuery.data.n2Pass,
      utilizationRate: healthQuery.data.utilization.utilizationRate,
      loadSheddingLevel: healthQuery.data.loadSheddingLevel,
      immediateActions: healthQuery.data.immediateActions,
      watchItems: healthQuery.data.watchItems,
    };
  }, [healthQuery.data]);

  return {
    personnel,
    systemMetrics,
    isLoading: healthQuery.isLoading,
    isError: healthQuery.isError,
    error: healthQuery.error,
    refetch: healthQuery.refetch,
  };
}
