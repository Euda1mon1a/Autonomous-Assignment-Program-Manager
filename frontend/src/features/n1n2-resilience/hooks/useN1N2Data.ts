/**
 * N-1/N-2 Resilience Data Hook
 *
 * Fetches real zone/blast radius data from the backend API and transforms
 * it into the Faculty format used by the visualizer components.
 *
 * @module features/n1n2-resilience/hooks/useN1N2Data
 */

import { useMemo } from 'react';
import { useBlastRadiusReport } from '@/hooks/useResilience';
import { useVulnerabilityReport } from '@/hooks/useResilience';
import type { Faculty } from '../types';
import type { ZoneHealthReport, ZoneStatus } from '@/types/resilience';

/**
 * Maps zone status to criticality level for the visualizer
 */
function mapZoneStatusToCriticality(
  status: ZoneStatus,
  capacityRatio: number
): Faculty['criticality'] {
  // Primary: Use status from the zone
  if (status === 'black' || status === 'red') {
    return 'critical';
  }
  if (status === 'orange') {
    return 'high';
  }
  if (status === 'yellow') {
    return 'medium';
  }

  // Secondary: Consider capacity ratio for more nuance
  if (capacityRatio < 0.5) {
    return 'critical';
  }
  if (capacityRatio < 0.7) {
    return 'high';
  }
  if (capacityRatio < 0.9) {
    return 'medium';
  }

  return 'low';
}

/**
 * Determines role based on zone type
 */
function mapZoneTypeToRole(
  zoneType: string
): 'attending' | 'senior' | 'junior' {
  // Map zone types to faculty roles for visualization
  if (
    zoneType === 'inpatient' ||
    zoneType === 'on_call' ||
    zoneType === 'outpatient'
  ) {
    return 'attending';
  }
  if (zoneType === 'education' || zoneType === 'research') {
    return 'senior';
  }
  return 'junior';
}

/**
 * Transforms a zone health report into a Faculty entry for the visualizer
 */
function transformZoneToFaculty(zone: ZoneHealthReport): Faculty {
  // Calculate coverage percentage from capacity ratio
  const coverage = Math.round(zone.capacityRatio * 100);

  return {
    id: zone.zoneId,
    name: zone.zoneName,
    role: mapZoneTypeToRole(zone.zoneType),
    specialty: zone.zoneType.charAt(0).toUpperCase() + zone.zoneType.slice(1),
    coverage: Math.min(coverage, 100), // Cap at 100%
    isAbsent: false,
    criticality: mapZoneStatusToCriticality(zone.status, zone.capacityRatio),
  };
}

/**
 * Hook return type for N1N2 data
 */
export interface UseN1N2DataResult {
  /** Transformed faculty data for visualization */
  faculty: Faculty[];
  /** Whether data is loading */
  isLoading: boolean;
  /** Error if fetch failed */
  error: Error | null;
  /** Whether N-1 resilience check passes */
  n1Pass: boolean;
  /** Whether N-2 resilience check passes */
  n2Pass: boolean;
  /** Total number of zones */
  totalZones: number;
  /** Number of healthy zones */
  zonesHealthy: number;
  /** Number of degraded zones */
  zonesDegraded: number;
  /** Number of critical zones */
  zonesCritical: number;
  /** Current containment level */
  containmentLevel: string;
  /** Whether containment is active */
  containmentActive: boolean;
  /** Recommendations from the backend */
  recommendations: string[];
  /** Refetch function */
  refetch: () => void;
}

/**
 * Fetches N-1/N-2 resilience data from the backend API.
 *
 * This hook combines data from two sources:
 * 1. Blast radius report (zones/faculty availability)
 * 2. Vulnerability report (N-1/N-2 pass/fail status)
 *
 * The data is transformed into the Faculty format expected by the
 * N1N2Visualizer components.
 *
 * @returns Object containing faculty data, loading state, and resilience metrics
 *
 * @example
 * ```tsx
 * function N1N2Visualizer() {
 *   const {
 *     faculty,
 *     isLoading,
 *     n1Pass,
 *     n2Pass,
 *     recommendations
 *   } = useN1N2Data();
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return (
 *     <div>
 *       <StatusBadge n1Pass={n1Pass} n2Pass={n2Pass} />
 *       <FacultyGrid faculty={faculty} />
 *     </div>
 *   );
 * }
 * ```
 */
export function useN1N2Data(): UseN1N2DataResult {
  // Fetch blast radius (zone) report
  const {
    data: blastRadiusData,
    isLoading: isLoadingBlastRadius,
    error: blastRadiusError,
    refetch: refetchBlastRadius,
  } = useBlastRadiusReport();

  // Fetch vulnerability report for N-1/N-2 status
  const {
    data: vulnerabilityData,
    isLoading: isLoadingVulnerability,
    error: vulnerabilityError,
    // eslint-disable-next-line @typescript-eslint/naming-convention -- API param is snake_case
  } = useVulnerabilityReport({ include_n2: true });

  // Transform zone data into faculty format for visualizer
  const faculty = useMemo<Faculty[]>(() => {
    if (!blastRadiusData?.zoneReports) {
      return [];
    }

    return blastRadiusData.zoneReports.map(transformZoneToFaculty);
  }, [blastRadiusData]);

  // Combined loading state
  const isLoading = isLoadingBlastRadius || isLoadingVulnerability;

  // Combined error (prefer blast radius error as it's the primary data)
  const error = blastRadiusError || vulnerabilityError || null;

  return {
    faculty,
    isLoading,
    error: error as Error | null,
    n1Pass: vulnerabilityData?.n1Pass ?? true,
    n2Pass: vulnerabilityData?.n2Pass ?? true,
    totalZones: blastRadiusData?.totalZones ?? 0,
    zonesHealthy: blastRadiusData?.zonesHealthy ?? 0,
    zonesDegraded: blastRadiusData?.zonesDegraded ?? 0,
    zonesCritical: blastRadiusData?.zonesCritical ?? 0,
    containmentLevel: blastRadiusData?.containmentLevel ?? 'none',
    containmentActive: blastRadiusData?.containmentActive ?? false,
    recommendations: blastRadiusData?.recommendations ?? [],
    refetch: refetchBlastRadius,
  };
}

export default useN1N2Data;
