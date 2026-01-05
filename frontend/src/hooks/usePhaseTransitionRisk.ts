/**
 * Phase Transition Risk Hook
 *
 * React Query hook for detecting approaching phase transitions
 * using critical phenomena theory and early warning signals.
 *
 * Monitors universal early warning signals that appear BEFORE
 * system transitions regardless of mechanism.
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { post } from '@/lib/api';
import type { ApiError } from '@/lib/api';

// ============================================================================
// Types
// ============================================================================

export interface CriticalSignal {
  signal_type: string;
  metric_name: string;
  severity: string;
  value: number;
  threshold: number;
  description: string;
  detected_at: string;
}

export interface PhaseTransitionRequest {
  /** Schedule ID to analyze (optional) */
  schedule_id?: string | null;
  /** Days of history to analyze */
  lookback_days?: number;
  /** Detection sensitivity multiplier */
  sensitivity?: number;
}

export interface PhaseTransitionResponse {
  /** Overall risk level: normal, elevated, high, critical, imminent */
  overall_severity: string;
  /** Detected early warning signals */
  signals: CriticalSignal[];
  /** Estimated time until transition (hours) */
  time_to_transition: number | null;
  /** Prediction confidence (0-1) */
  confidence: number;
  /** Suggested interventions */
  recommendations: string[];
  /** Data source */
  source: string;
}

// ============================================================================
// Query Keys
// ============================================================================

export const phaseTransitionQueryKeys = {
  all: ['phase-transition'] as const,
  risk: (scheduleId?: string | null, lookbackDays?: number) =>
    ['phase-transition', 'risk', scheduleId, lookbackDays] as const,
};

// ============================================================================
// Hook
// ============================================================================

/**
 * Detect approaching phase transitions using critical phenomena theory.
 *
 * Monitors universal early warning signals:
 * - Variance increase (fluctuations diverge)
 * - Critical slowing down (recovery time increases)
 * - Flickering (rapid state switching)
 * - Skewness changes (distribution asymmetry)
 *
 * These signals appear 2-4 weeks before transition, providing early warning.
 *
 * @param scheduleId - Optional schedule ID to analyze
 * @param lookbackDays - Days of history to analyze (default: 30)
 * @param sensitivity - Detection sensitivity (default: 1.0)
 * @param options - React Query options
 * @returns Query result with severity and recommendations
 *
 * @example
 * ```tsx
 * function PhaseTransitionWarning() {
 *   const { data, isLoading } = usePhaseTransitionRisk();
 *
 *   if (isLoading) return null;
 *   if (data.overall_severity === 'normal') return null;
 *
 *   return (
 *     <Alert severity={data.overall_severity}>
 *       <AlertTitle>Phase Transition Warning</AlertTitle>
 *       <p>System approaching critical point</p>
 *       <p>Confidence: {(data.confidence * 100).toFixed(0)}%</p>
 *       {data.time_to_transition && (
 *         <p>Estimated time: {data.time_to_transition} hours</p>
 *       )}
 *       <ul>
 *         {data.recommendations.map((rec, i) => (
 *           <li key={i}>{rec}</li>
 *         ))}
 *       </ul>
 *     </Alert>
 *   );
 * }
 * ```
 */
export function usePhaseTransitionRisk(
  scheduleId?: string | null,
  lookbackDays: number = 30,
  sensitivity: number = 1.0,
  options?: Omit<
    UseQueryOptions<PhaseTransitionResponse, ApiError>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<PhaseTransitionResponse, ApiError>({
    queryKey: phaseTransitionQueryKeys.risk(scheduleId, lookbackDays),
    queryFn: async () => {
      const request: PhaseTransitionRequest = {
        schedule_id: scheduleId || null,
        lookback_days: lookbackDays,
        sensitivity: sensitivity,
      };

      // Call exotic resilience API endpoint
      const response = await post<PhaseTransitionResponse>(
        '/exotic-resilience/thermodynamics/phase-transition',
        request
      );

      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes - expensive calculation
    refetchInterval: 10 * 60 * 1000, // Refetch every 10 minutes for early warnings
    ...options,
  });
}

/**
 * Helper: Get severity color class.
 *
 * @param severity - Severity level
 * @returns Tailwind color class
 */
export function getSeverityColorClass(severity: string): string {
  switch (severity) {
    case 'normal':
      return 'text-green-500';
    case 'elevated':
      return 'text-yellow-500';
    case 'high':
      return 'text-orange-500';
    case 'critical':
      return 'text-red-500';
    case 'imminent':
      return 'text-red-700';
    default:
      return 'text-slate-500';
  }
}

/**
 * Helper: Get severity background color class.
 *
 * @param severity - Severity level
 * @returns Tailwind background color class
 */
export function getSeverityBgClass(severity: string): string {
  switch (severity) {
    case 'normal':
      return 'bg-green-500/20';
    case 'elevated':
      return 'bg-yellow-500/20';
    case 'high':
      return 'bg-orange-500/20';
    case 'critical':
      return 'bg-red-500/20';
    case 'imminent':
      return 'bg-red-700/20';
    default:
      return 'bg-slate-500/20';
  }
}

/**
 * Helper: Get severity icon.
 *
 * @param severity - Severity level
 * @returns Icon name or emoji
 */
export function getSeverityIcon(severity: string): string {
  switch (severity) {
    case 'normal':
      return '✓';
    case 'elevated':
      return '⚠';
    case 'high':
      return '⚠⚠';
    case 'critical':
      return '🔥';
    case 'imminent':
      return '🚨';
    default:
      return '?';
  }
}

/**
 * Helper: Check if severity requires action.
 *
 * @param severity - Severity level
 * @returns True if action required
 */
export function requiresAction(severity: string): boolean {
  return ['high', 'critical', 'imminent'].includes(severity);
}
