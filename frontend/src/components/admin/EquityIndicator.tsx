'use client';

/**
 * EquityIndicator Component
 *
 * Displays Gini coefficient and workload equity analysis for bulk operations.
 * Shows current equity, projected equity after changes, and color-coded warnings.
 */
import React from 'react';
import { TrendingUp, TrendingDown, Minus, Loader2 } from 'lucide-react';
import {
  useEquityMetrics,
  getGiniColorClass,
  getGiniLabel,
} from '@/hooks/useEquityMetrics';

// ============================================================================
// Types
// ============================================================================

export interface EquityIndicatorProps {
  /** Current provider hours mapping */
  currentProviderHours: Record<string, number> | null;
  /** Projected provider hours after proposed changes */
  projectedProviderHours?: Record<string, number> | null;
  /** Compact mode (shows only summary) */
  compact?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export function EquityIndicator({
  currentProviderHours,
  projectedProviderHours,
  compact = false,
}: EquityIndicatorProps) {
  // Fetch current equity metrics
  const {
    data: currentEquity,
    isLoading: currentLoading,
    error: currentError,
  } = useEquityMetrics(currentProviderHours);

  // Fetch projected equity metrics if changes are proposed
  const {
    data: projectedEquity,
    isLoading: projectedLoading,
  } = useEquityMetrics(
    projectedProviderHours || null,
    null,
    { enabled: !!projectedProviderHours }
  );

  // Loading state
  if (currentLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Calculating equity...</span>
      </div>
    );
  }

  // Error state
  if (currentError || !currentEquity) {
    return (
      <div className="text-sm text-slate-500">
        Equity data unavailable
      </div>
    );
  }

  // Calculate trend if projection available
  const hasTrend = !!projectedEquity && !projectedLoading;
  const giniChange = hasTrend
    ? projectedEquity.gini_coefficient - currentEquity.gini_coefficient
    : 0;
  const improving = giniChange < 0; // Lower Gini = more equitable
  const worsening = giniChange > 0;

  // Determine trend icon
  const TrendIcon = improving
    ? TrendingDown
    : worsening
    ? TrendingUp
    : Minus;
  const trendColor = improving
    ? 'text-green-500'
    : worsening
    ? 'text-red-500'
    : 'text-slate-500';

  // Compact mode
  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-800 rounded-lg">
          <span className="text-xs font-medium text-slate-400">Gini:</span>
          <span
            className={`text-sm font-semibold ${getGiniColorClass(currentEquity.gini_coefficient)}`}
          >
            {currentEquity.gini_coefficient.toFixed(3)}
          </span>
        </div>
        {hasTrend && Math.abs(giniChange) > 0.001 && (
          <div className={`flex items-center gap-1 ${trendColor}`}>
            <TrendIcon className="w-3.5 h-3.5" />
            <span className="text-xs font-medium">
              {Math.abs(giniChange).toFixed(3)}
            </span>
          </div>
        )}
      </div>
    );
  }

  // Full mode
  return (
    <div className="space-y-2">
      {/* Current equity */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-300">
          Current Equity:
        </span>
        <div className="flex items-center gap-2">
          <span
            className={`text-sm font-semibold ${getGiniColorClass(currentEquity.gini_coefficient)}`}
          >
            Gini: {currentEquity.gini_coefficient.toFixed(3)}
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded ${
              currentEquity.is_equitable
                ? 'bg-green-500/20 text-green-400'
                : 'bg-yellow-500/20 text-yellow-400'
            }`}
          >
            {getGiniLabel(currentEquity.gini_coefficient)}
          </span>
        </div>
      </div>

      {/* Projected equity (if available) */}
      {hasTrend && (
        <>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-300">
              After Changes:
            </span>
            <div className="flex items-center gap-2">
              <span
                className={`text-sm font-semibold ${getGiniColorClass(projectedEquity.gini_coefficient)}`}
              >
                Gini: {projectedEquity.gini_coefficient.toFixed(3)}
              </span>
              <div className={`flex items-center gap-1 ${trendColor}`}>
                <TrendIcon className="w-3.5 h-3.5" />
                <span className="text-xs font-medium">
                  {giniChange > 0 ? '+' : ''}
                  {giniChange.toFixed(3)}
                </span>
              </div>
            </div>
          </div>

          {/* Impact summary */}
          {Math.abs(giniChange) > 0.01 && (
            <div
              className={`px-3 py-2 rounded-lg text-xs ${
                improving
                  ? 'bg-green-500/10 text-green-400'
                  : 'bg-red-500/10 text-red-400'
              }`}
            >
              {improving
                ? '✓ Equity improves with this change'
                : '⚠ Equity worsens with this change'}
            </div>
          )}
        </>
      )}

      {/* Recommendations (if any) */}
      {currentEquity.recommendations.length > 0 && (
        <div className="pt-2 border-t border-slate-700">
          <div className="text-xs font-medium text-slate-400 mb-1">
            Recommendations:
          </div>
          <ul className="text-xs text-slate-500 space-y-0.5">
            {currentEquity.recommendations.slice(0, 2).map((rec, idx) => (
              <li key={idx} className="flex items-start gap-1">
                <span className="text-slate-600">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default EquityIndicator;
