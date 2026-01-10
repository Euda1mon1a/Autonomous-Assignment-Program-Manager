'use client';

/**
 * PhaseTransitionBanner Component
 *
 * Warning banner that appears when system is approaching a phase transition
 * based on critical phenomena theory early warning signals.
 *
 * Displays at top of admin pages when risk level is elevated or higher.
 */
import React, { useState } from 'react';
import { AlertTriangle, X, ChevronDown, ChevronUp, Clock } from 'lucide-react';
import {
  usePhaseTransitionRisk,
  getSeverityColorClass,
  getSeverityBgClass,
  requiresAction,
} from '@/hooks/usePhaseTransitionRisk';

// ============================================================================
// Types
// ============================================================================

export interface PhaseTransitionBannerProps {
  /** Optional schedule ID to analyze */
  scheduleId?: string | null;
  /** Days of history to analyze */
  lookbackDays?: number;
  /** Hide if severity is normal */
  hideIfNormal?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export function PhaseTransitionBanner({
  scheduleId,
  lookbackDays = 30,
  hideIfNormal = true,
}: PhaseTransitionBannerProps) {
  const [expanded, setExpanded] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const { data, isLoading, error } = usePhaseTransitionRisk(
    scheduleId,
    lookbackDays
  );

  // Don't show if loading or error
  if (isLoading || error || !data) {
    return null;
  }

  // Don't show if normal and hideIfNormal is true
  if (hideIfNormal && data.overallSeverity === 'normal') {
    return null;
  }

  // Don't show if dismissed
  if (dismissed) {
    return null;
  }

  const severityClass = getSeverityColorClass(data.overallSeverity);
  const bgClass = getSeverityBgClass(data.overallSeverity);
  const actionRequired = requiresAction(data.overallSeverity);

  return (
    <div
      className={`border-l-4 ${bgClass} ${
        data.overallSeverity === 'normal'
          ? 'border-green-500'
          : data.overallSeverity === 'elevated'
          ? 'border-yellow-500'
          : data.overallSeverity === 'high'
          ? 'border-orange-500'
          : 'border-red-500'
      } rounded-lg overflow-hidden`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${bgClass}`}>
            <AlertTriangle className={`w-5 h-5 ${severityClass}`} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className={`text-sm font-semibold ${severityClass}`}>
                {data.overallSeverity === 'normal' && 'System Stable'}
                {data.overallSeverity === 'elevated' && 'Elevated Risk'}
                {data.overallSeverity === 'high' && 'High Risk - Phase Transition Warning'}
                {data.overallSeverity === 'critical' && 'CRITICAL - Phase Transition Imminent'}
                {data.overallSeverity === 'imminent' && '🚨 EMERGENCY - Phase Transition Detected'}
              </h3>
              <span className="text-xs text-slate-400">
                Confidence: {(data.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {data.signals.length} early warning signal{data.signals.length !== 1 ? 's' : ''} detected
              {data.time_to_transition && (
                <span className="ml-2 flex items-center gap-1 inline-flex">
                  <Clock className="w-3 h-3" />
                  ~{Math.round(data.time_to_transition)}h until transition
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {data.signals.length > 0 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1 text-slate-400 hover:text-white transition-colors"
              title={expanded ? 'Collapse details' : 'Expand details'}
            >
              {expanded ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
          )}
          {!actionRequired && (
            <button
              onClick={() => setDismissed(true)}
              className="p-1 text-slate-400 hover:text-white transition-colors"
              title="Dismiss"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="px-4 pb-3 space-y-3 border-t border-slate-700/50">
          {/* Early warning signals */}
          {data.signals.length > 0 && (
            <div>
              <div className="text-xs font-medium text-slate-400 mb-2 mt-3">
                Detected Signals:
              </div>
              <div className="space-y-1.5">
                {data.signals.map((signal, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-2 text-xs bg-slate-800/50 px-3 py-2 rounded"
                  >
                    <span
                      className={`font-medium ${
                        signal.severity === 'critical'
                          ? 'text-red-400'
                          : signal.severity === 'high'
                          ? 'text-orange-400'
                          : 'text-yellow-400'
                      }`}
                    >
                      {signal.signal_type}:
                    </span>
                    <span className="text-slate-300 flex-1">
                      {signal.description}
                    </span>
                    <span className="text-slate-500 text-xs">
                      {signal.value.toFixed(2)} / {signal.threshold.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {data.recommendations.length > 0 && (
            <div>
              <div className="text-xs font-medium text-slate-400 mb-2">
                Recommended Actions:
              </div>
              <ul className="space-y-1">
                {data.recommendations.map((rec, idx) => (
                  <li
                    key={idx}
                    className="text-xs text-slate-300 flex items-start gap-2"
                  >
                    <span className="text-slate-600">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Action required notice */}
          {actionRequired && (
            <div className="px-3 py-2 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-400">
              ⚠ Immediate action required to prevent system failure
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default PhaseTransitionBanner;
