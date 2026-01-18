'use client';

/**
 * Analysis Panel Component
 *
 * Displays detailed analysis for a selected day including:
 * - Risk status and fragility metrics
 * - Single Point of Failure detection
 * - Cascading failure predictions
 * - AI analysis section (placeholder)
 */

import {
  ShieldAlert,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Brain,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { DayData, AnalysisResponse } from '../types';

interface AnalysisPanelProps {
  /** Selected day data */
  day: DayData;
  /** AI analysis data (if available) */
  aiData: AnalysisResponse | null;
  /** Whether AI is currently loading */
  isLoadingAi: boolean;
  /** Callback to trigger AI analysis */
  onRunAi: () => void;
}

export function AnalysisPanel({
  day,
  aiData,
  isLoadingAi,
  onRunAi,
}: AnalysisPanelProps) {
  const riskLevel =
    day.fragility > 0.7 ? 'CRITICAL' : day.fragility > 0.4 ? 'WARNING' : 'STABLE';
  const riskVariant =
    day.fragility > 0.7 ? 'danger' : day.fragility > 0.4 ? 'warning' : 'success';
  const riskColorClass =
    day.fragility > 0.7
      ? 'text-red-500'
      : day.fragility > 0.4
        ? 'text-amber-500'
        : 'text-emerald-500';

  return (
    <Card className="bg-slate-800 border-slate-700 relative overflow-hidden">
      {/* Background watermark */}
      <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none">
        <Activity size={120} />
      </div>

      <CardHeader className="relative z-10">
        <CardTitle className="text-white flex items-center gap-3">
          <ShieldAlert className={`w-5 h-5 ${riskColorClass}`} />
          <span>Day {day.day} Analysis</span>
          <Badge variant={riskVariant} size="sm">
            {riskLevel}
          </Badge>
        </CardTitle>
      </CardHeader>

      <CardContent className="relative z-10 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Metrics Column */}
          <div className="space-y-4">
            {/* Fragility Score */}
            <div className="bg-slate-900/50 p-4 border border-slate-700 rounded">
              <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                Fragility Score
              </div>
              <div className="flex items-end gap-2">
                <span className={`text-3xl font-bold ${riskColorClass}`}>
                  {(day.fragility * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-slate-700 h-1.5 mt-3 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 rounded-full ${
                    day.fragility > 0.7 ? 'bg-red-500' : day.fragility > 0.4 ? 'bg-amber-500' : 'bg-emerald-500'
                  }`}
                  style={{ width: `${day.fragility * 100}%` }}
                />
              </div>
            </div>

            {/* SPOF */}
            <div className="bg-slate-900/50 p-4 border border-slate-700 rounded">
              <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                Single Point of Failure
              </div>
              <div className="text-lg font-bold">
                {day.spof ? (
                  <span className="text-red-400">{day.spof}</span>
                ) : (
                  <span className="text-slate-500">None Detected</span>
                )}
              </div>
            </div>

            {/* Staffing Level */}
            <div className="bg-slate-900/50 p-4 border border-slate-700 rounded">
              <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                Staffing Level
              </div>
              <div className="text-2xl font-bold text-white">
                {day.staffingLevel.toFixed(0)}%
              </div>
            </div>
          </div>

          {/* Cascading Failures Column */}
          <div className="space-y-3">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider border-b border-slate-700 pb-2">
              Cascading Failures
            </div>
            {day.violations.length > 0 ? (
              <ul className="space-y-2">
                {day.violations.map((v, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-3 text-sm bg-amber-500/10 border border-amber-500/20 p-3 rounded"
                  >
                    <AlertTriangle
                      size={16}
                      className="text-amber-500 shrink-0 mt-0.5"
                    />
                    <span className="text-amber-200">{v}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="flex items-center gap-2 text-sm text-emerald-400/70 p-4 border border-emerald-500/20 bg-emerald-500/5 rounded">
                <CheckCircle2 size={16} />
                No secondary failures predicted.
              </div>
            )}
          </div>
        </div>

        {/* AI Analysis Section */}
        <div className="border-t border-slate-700 pt-6">
          {!aiData ? (
            <button
              onClick={onRunAi}
              disabled={isLoadingAi}
              className="group flex items-center justify-between w-full bg-cyan-500/10 border border-cyan-500/30 p-4 hover:bg-cyan-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed rounded"
            >
              <span className="flex items-center gap-3 text-cyan-400 font-semibold tracking-wide text-sm">
                <Brain size={18} className={isLoadingAi ? 'animate-spin' : ''} />
                {isLoadingAi ? 'Analyzing...' : 'Request AI Analysis'}
              </span>
              <span className="text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity">
                {'>'}
              </span>
            </button>
          ) : (
            <div className="space-y-4">
              <div className="flex justify-between items-center text-cyan-400">
                <h3 className="text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                  <Brain size={14} /> AI Assessment
                </h3>
                <button
                  onClick={onRunAi}
                  className="text-[10px] hover:text-white transition-colors uppercase"
                >
                  [Re-Analyze]
                </button>
              </div>

              <div className="bg-slate-900/50 border-l-2 border-cyan-500 p-4 rounded-r">
                <p className="text-sm text-cyan-300 leading-relaxed">
                  &ldquo;{aiData.analysis}&rdquo;
                </p>
              </div>

              <div className="space-y-2">
                <div className="text-[9px] text-slate-500 uppercase tracking-widest">
                  Suggested Mitigations
                </div>
                <ul className="space-y-2">
                  {aiData.mitigations.map((m, i) => (
                    <li
                      key={i}
                      className="flex items-center gap-3 text-sm text-slate-300 bg-slate-700/50 p-3 rounded border border-slate-600"
                    >
                      <span className="text-cyan-400 font-mono text-[10px]">
                        0{i + 1}
                      </span>
                      {m}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default AnalysisPanel;
