/**
 * Cascade Metrics Component
 *
 * Displays the impact metrics from absence simulation.
 */

'use client';

import {
  Activity,
  AlertTriangle,
  Clock,
  Layers,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { STATUS_COLORS, STATUS_BG_COLORS } from '../constants';
import type { CascadeMetricsProps } from '../types';

function MetricCard({
  icon: Icon,
  label,
  value,
  unit,
  status,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  unit?: string;
  status?: 'good' | 'warning' | 'danger';
}) {
  const statusColors = {
    good: 'text-green-400',
    warning: 'text-amber-400',
    danger: 'text-red-400',
  };

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 text-slate-400" />
        <span className="text-xs text-slate-400 uppercase tracking-wide">
          {label}
        </span>
      </div>
      <div
        className={`text-2xl font-bold ${status ? statusColors[status] : 'text-white'}`}
      >
        {value}
        {unit && <span className="text-sm text-slate-500 ml-1">{unit}</span>}
      </div>
    </div>
  );
}

export function CascadeMetrics({ metrics, mode }: CascadeMetricsProps) {
  const getGapStatus = (gap: number): 'good' | 'warning' | 'danger' => {
    if (gap < 10) return 'good';
    if (gap < 25) return 'warning';
    return 'danger';
  };

  const getLoadStatus = (load: number): 'good' | 'warning' | 'danger' => {
    if (load < 15) return 'good';
    if (load < 30) return 'warning';
    return 'danger';
  };

  const getDepthStatus = (depth: number): 'good' | 'warning' | 'danger' => {
    if (depth < 3) return 'good';
    if (depth < 6) return 'warning';
    return 'danger';
  };

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide">
          Cascade Analysis
        </h3>
        <span className="text-xs bg-slate-700 px-2 py-1 rounded text-slate-300">
          {mode} MODE
        </span>
      </div>

      {/* System Status Banner */}
      <div
        className={`mb-4 p-3 rounded-lg border ${STATUS_BG_COLORS[metrics.systemStatus]}`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle
              className={`w-5 h-5 ${STATUS_COLORS[metrics.systemStatus]}`}
            />
            <span
              className={`font-semibold uppercase ${STATUS_COLORS[metrics.systemStatus]}`}
            >
              System {metrics.systemStatus}
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Clock className="w-3 h-3" />
            <span>Recovery: {metrics.recoveryTime}</span>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-3">
        <MetricCard
          icon={Activity}
          label="Coverage Gap"
          value={metrics.coverageGap}
          unit="%"
          status={getGapStatus(metrics.coverageGap)}
        />
        <MetricCard
          icon={Zap}
          label="Affected Slots"
          value={metrics.affectedSlots}
          status={metrics.affectedSlots > 20 ? 'danger' : metrics.affectedSlots > 10 ? 'warning' : 'good'}
        />
        <MetricCard
          icon={Layers}
          label="Cascade Depth"
          value={metrics.cascadeDepth}
          status={getDepthStatus(metrics.cascadeDepth)}
        />
        <MetricCard
          icon={TrendingUp}
          label="Redistribution Load"
          value={metrics.redistributionLoad}
          unit="%"
          status={getLoadStatus(metrics.redistributionLoad)}
        />
      </div>

      {/* Interpretation */}
      <div className="mt-4 pt-4 border-t border-slate-700">
        <p className="text-xs text-slate-400 leading-relaxed">
          {metrics.systemStatus === 'stable' && (
            <>No absences simulated. System operating at full capacity.</>
          )}
          {metrics.systemStatus === 'strained' && (
            <>
              System absorbing absence within {mode} tolerance. Monitor for
              additional stress.
            </>
          )}
          {metrics.systemStatus === 'critical' && (
            <>
              Warning: Approaching {mode} failure threshold. Coverage gaps may
              cascade.
            </>
          )}
          {metrics.systemStatus === 'failed' && (
            <>
              ALERT: {mode} resilience exceeded. Immediate intervention required
              to prevent cascading failure.
            </>
          )}
        </p>
      </div>
    </div>
  );
}

export default CascadeMetrics;
