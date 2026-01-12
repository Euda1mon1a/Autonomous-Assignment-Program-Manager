/**
 * Fairness Audit Hooks
 *
 * React Query hooks for faculty workload fairness analysis.
 * Integrates with the FairnessAuditService backend API.
 */
import { useQuery } from '@tanstack/react-query';
import { get } from '@/lib/api';
import type { ApiError } from '@/lib/api';

// ============================================================================
// Types
// ============================================================================

export interface CategoryStats {
  min: number;
  max: number;
  mean: number;
  spread: number;
}

export interface FacultyWorkload {
  personId: string;
  personName: string;
  callCount: number;
  fmitWeeks: number;
  clinicHalfdays: number;
  adminHalfdays: number;
  academicHalfdays: number;
  totalScore: number;
}

export interface FairnessAuditResponse {
  period: {
    start: string;
    end: string;
  };
  facultyCount: number;
  categoryStats: {
    call: CategoryStats;
    fmit: CategoryStats;
    clinic: CategoryStats;
    admin: CategoryStats;
    academic: CategoryStats;
  };
  workloadStats: CategoryStats;
  fairnessIndex: number;
  outliers: {
    high: string[];
    low: string[];
  };
  workloads: FacultyWorkload[];
  weights: {
    call: number;
    fmit: number;
    clinic: number;
    admin: number;
    academic: number;
  };
}

export interface FairnessSummaryResponse {
  period: {
    start: string;
    end: string;
  };
  facultyCount: number;
  fairnessIndex: number;
  workloadSpread: number;
  outlierCount: {
    high: number;
    low: number;
  };
}

// ============================================================================
// Query Keys
// ============================================================================

export const fairnessQueryKeys = {
  all: ['fairness'] as const,
  audit: (startDate: string, endDate: string, includeTitled?: boolean) =>
    ['fairness', 'audit', startDate, endDate, includeTitled ?? false] as const,
  summary: (startDate: string, endDate: string) =>
    ['fairness', 'summary', startDate, endDate] as const,
  facultyWorkload: (facultyId: string, startDate: string, endDate: string) =>
    ['fairness', 'faculty', facultyId, startDate, endDate] as const,
};

// ============================================================================
// Hooks
// ============================================================================

/**
 * Get full fairness audit report for date range.
 *
 * Returns comprehensive workload breakdown across 5 categories:
 * - Call (overnight shifts)
 * - FMIT (weeks)
 * - Clinic (half-days)
 * - Admin (GME, DFM half-days)
 * - Academic (LEC, ADV half-days)
 *
 * @param startDate - Start date (YYYY-MM-DD)
 * @param endDate - End date (YYYY-MM-DD)
 * @param includeTitledFaculty - Include PD, APD, OIC, Dept Chief (default: false)
 */
export function useFairnessAudit(
  startDate: string | null,
  endDate: string | null,
  includeTitledFaculty = false
) {
  return useQuery<FairnessAuditResponse, ApiError>({
    queryKey: fairnessQueryKeys.audit(
      startDate || '',
      endDate || '',
      includeTitledFaculty
    ),
    queryFn: async () => {
      const params = new URLSearchParams({
        start_date: startDate!,
        end_date: endDate!,
        include_titled_faculty: String(includeTitledFaculty),
      });
      return get<FairnessAuditResponse>(`/fairness/audit?${params}`);
    },
    enabled: !!startDate && !!endDate,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Get compact fairness summary (lighter than full audit).
 *
 * Returns key metrics without per-faculty breakdown.
 */
export function useFairnessSummary(
  startDate: string | null,
  endDate: string | null
) {
  return useQuery<FairnessSummaryResponse, ApiError>({
    queryKey: fairnessQueryKeys.summary(startDate || '', endDate || ''),
    queryFn: async () => {
      const params = new URLSearchParams({
        start_date: startDate!,
        end_date: endDate!,
      });
      return get<FairnessSummaryResponse>(`/fairness/summary?${params}`);
    },
    enabled: !!startDate && !!endDate,
    staleTime: 60 * 1000,
  });
}

/**
 * Get workload breakdown for a specific faculty member.
 */
export function useFacultyWorkload(
  facultyId: string | null,
  startDate: string | null,
  endDate: string | null
) {
  return useQuery<FacultyWorkload, ApiError>({
    queryKey: fairnessQueryKeys.facultyWorkload(
      facultyId || '',
      startDate || '',
      endDate || ''
    ),
    queryFn: async () => {
      const params = new URLSearchParams({
        start_date: startDate!,
        end_date: endDate!,
      });
      return get<FacultyWorkload>(
        `/fairness/faculty/${facultyId}/workload?${params}`
      );
    },
    enabled: !!facultyId && !!startDate && !!endDate,
    staleTime: 60 * 1000,
  });
}

// ============================================================================
// Helpers
// ============================================================================

/**
 * Get color class for fairness index.
 * Uses Jain's fairness index (0-1, where 1 is perfectly fair).
 */
export function getFairnessColorClass(fairnessIndex: number): string {
  if (fairnessIndex >= 0.95) return 'text-green-500';
  if (fairnessIndex >= 0.85) return 'text-emerald-500';
  if (fairnessIndex >= 0.75) return 'text-yellow-500';
  return 'text-red-500';
}

/**
 * Get status label for fairness index.
 */
export function getFairnessLabel(fairnessIndex: number): string {
  if (fairnessIndex >= 0.95) return 'Excellent';
  if (fairnessIndex >= 0.85) return 'Good';
  if (fairnessIndex >= 0.75) return 'Fair';
  return 'Poor';
}

/**
 * Get status variant for fairness index (for badges/cards).
 */
export function getFairnessStatus(
  fairnessIndex: number
): 'excellent' | 'good' | 'warning' | 'critical' {
  if (fairnessIndex >= 0.95) return 'excellent';
  if (fairnessIndex >= 0.85) return 'good';
  if (fairnessIndex >= 0.75) return 'warning';
  return 'critical';
}

/**
 * Calculate workload deviation from mean.
 */
export function getWorkloadDeviation(
  workload: FacultyWorkload,
  meanScore: number
): number {
  if (meanScore === 0) return 0;
  return ((workload.totalScore - meanScore) / meanScore) * 100;
}

/**
 * Get color class for workload deviation.
 */
export function getDeviationColorClass(deviationPercent: number): string {
  const absDeviation = Math.abs(deviationPercent);
  if (absDeviation <= 10) return 'text-green-500';
  if (absDeviation <= 25) return 'text-yellow-500';
  return 'text-red-500';
}
