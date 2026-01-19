/**
 * Fragility Data Hook
 *
 * Fetches vulnerability data from the resilience API and maps it to
 * the DayData format used by the fragility triage visualization.
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { DayData } from '../types';

/**
 * API Response Types (camelCase - converted by axios interceptor)
 */

interface CentralityScore {
  facultyId: string;
  facultyName: string;
  centralityScore: number;
  servicesCovered: number;
  uniqueCoverageSlots: number;
  replacementDifficulty: number;
  riskLevel: string;
}

interface N1Vulnerability {
  facultyId: string;
  affectedBlocks: number;
  severity: string;
}

interface N2FatalPair {
  faculty1Id: string;
  faculty2Id: string;
}

interface VulnerabilityReportResponse {
  analyzedAt: string;
  periodStart: string;
  periodEnd: string;
  n1Pass: boolean;
  n2Pass: boolean;
  phaseTransitionRisk: string;
  n1Vulnerabilities: N1Vulnerability[];
  n2FatalPairs: N2FatalPair[];
  mostCriticalFaculty: CentralityScore[];
  recommendedActions: string[];
}

/**
 * Maps vulnerability API response to DayData format for visualization.
 *
 * The API provides N-1/N-2 vulnerability data which we transform into
 * per-day fragility metrics for the temporal grid visualization.
 */
function mapToFragilityDays(response: VulnerabilityReportResponse): DayData[] {
  const startDate = new Date(response.periodStart);
  const endDate = new Date(response.periodEnd);
  const dayCount = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)) + 1;

  // Determine overall fragility based on N-1/N-2 status
  const baseFragility = calculateBaseFragility(response);

  // Get the most critical faculty member as potential SPOF
  const topCriticalFaculty = response.mostCriticalFaculty[0];
  const spofName = topCriticalFaculty?.facultyName || null;

  // Build violations list from analysis results
  const violations = buildViolationsList(response);

  // Generate day-by-day data based on vulnerability analysis
  return Array.from({ length: dayCount }, (_, i) => {
    // Vary fragility slightly per day based on vulnerability distribution
    const dayVariance = calculateDayVariance(i, response.n1Vulnerabilities);
    const fragility = Math.min(1.0, Math.max(0.0, baseFragility + dayVariance));

    // Only show SPOF for high-fragility days
    const daySpof = fragility > 0.7 ? spofName : null;

    // Filter violations based on fragility level
    const dayViolations = violations.filter((_, idx) => {
      if (fragility > 0.8) return true;
      if (fragility > 0.6) return idx < 2;
      if (fragility > 0.4) return idx < 1;
      return false;
    });

    return {
      day: i + 1,
      fragility,
      spof: daySpof,
      violations: dayViolations,
      staffingLevel: 100 - fragility * 40, // Inverse correlation with fragility
    };
  });
}

/**
 * Calculates base fragility score from vulnerability report.
 */
function calculateBaseFragility(response: VulnerabilityReportResponse): number {
  let fragility = 0.1; // Base level

  // N-1 failure significantly increases fragility
  if (!response.n1Pass) {
    fragility += 0.4;
  }

  // N-2 failure adds additional risk
  if (!response.n2Pass) {
    fragility += 0.2;
  }

  // Phase transition risk assessment
  switch (response.phaseTransitionRisk) {
    case 'critical':
      fragility += 0.3;
      break;
    case 'high':
      fragility += 0.2;
      break;
    case 'medium':
      fragility += 0.1;
      break;
    default:
      break;
  }

  // Vulnerabilities contribute to fragility
  if (response.n1Vulnerabilities.length > 0) {
    fragility += Math.min(0.2, response.n1Vulnerabilities.length * 0.03);
  }

  return Math.min(1.0, fragility);
}

/**
 * Calculates variance for a specific day based on vulnerability distribution.
 */
function calculateDayVariance(dayIndex: number, vulnerabilities: N1Vulnerability[]): number {
  if (vulnerabilities.length === 0) return 0;

  // Use a deterministic pseudo-random pattern based on vulnerability data
  const seed = vulnerabilities.reduce((acc, v) => acc + v.affectedBlocks, 0);
  const variance = Math.sin(dayIndex * 0.5 + seed * 0.1) * 0.15;

  return variance;
}

/**
 * Builds a list of violations from the vulnerability report.
 */
function buildViolationsList(response: VulnerabilityReportResponse): string[] {
  const violations: string[] = [];

  if (!response.n1Pass) {
    violations.push('N-1 Contingency Failure');
  }

  if (!response.n2Pass) {
    violations.push('N-2 Contingency Failure');
  }

  if (response.phaseTransitionRisk === 'critical' || response.phaseTransitionRisk === 'high') {
    violations.push('Phase Transition Risk Elevated');
  }

  // Add violations based on fatal pairs
  if (response.n2FatalPairs.length > 3) {
    violations.push('Multiple Fatal Faculty Pairs');
  }

  // Add violations based on critical faculty concentration
  const catastrophicCount = response.mostCriticalFaculty.filter(
    f => f.riskLevel === 'critical' || f.riskLevel === 'catastrophic'
  ).length;

  if (catastrophicCount > 0) {
    violations.push(`${catastrophicCount} Catastrophic Hub${catastrophicCount > 1 ? 's' : ''} Identified`);
  }

  // Add any recommended actions as implicit violations (first 2)
  response.recommendedActions.slice(0, 2).forEach(action => {
    if (action.includes('ACGME')) {
      violations.push('ACGME Compliance Risk');
    } else if (action.includes('coverage') || action.includes('Coverage')) {
      violations.push('Coverage Gap Risk');
    }
  });

  return violations;
}

/**
 * Hook to fetch fragility/vulnerability data from the API.
 *
 * @param startDate - Start date for the analysis period (ISO string)
 * @param endDate - End date for the analysis period (ISO string)
 * @param enabled - Whether to enable the query (default: true)
 */
export function useFragilityData(
  startDate: string,
  endDate: string,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: ['resilience', 'vulnerability', startDate, endDate],
    queryFn: async () => {
      const response = await api.get<VulnerabilityReportResponse>('/resilience/vulnerability', {
        params: {
          start_date: startDate,
          end_date: endDate,
          include_n2: true,
        },
      });
      return mapToFragilityDays(response.data);
    },
    enabled: enabled && !!startDate && !!endDate,
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
    gcTime: 30 * 60 * 1000, // Keep in cache for 30 minutes
  });
}

/**
 * Hook to fetch raw vulnerability report (for metrics display).
 */
export function useVulnerabilityReport(
  startDate: string,
  endDate: string,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: ['resilience', 'vulnerability', 'raw', startDate, endDate],
    queryFn: async () => {
      const response = await api.get<VulnerabilityReportResponse>('/resilience/vulnerability', {
        params: {
          start_date: startDate,
          end_date: endDate,
          include_n2: true,
        },
      });
      return response.data;
    },
    enabled: enabled && !!startDate && !!endDate,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

export type { VulnerabilityReportResponse, CentralityScore, N1Vulnerability, N2FatalPair };
