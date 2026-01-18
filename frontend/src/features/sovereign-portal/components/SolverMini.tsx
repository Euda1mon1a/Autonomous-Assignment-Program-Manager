/**
 * Solver Mini Visualization
 *
 * Mini gauge for solver status.
 */

'use client';

import type { SolverMetrics } from '../types';

interface SolverMiniProps {
  metrics: SolverMetrics;
}

export function SolverMini({ metrics }: SolverMiniProps) {
  const satisfactionRate =
    (metrics.constraintsSatisfied / metrics.constraintsTotal) * 100;
  const unsatisfied = metrics.constraintsTotal - metrics.constraintsSatisfied;

  const qualityColor =
    metrics.solutionQuality === 'optimal'
      ? 'text-green-400'
      : metrics.solutionQuality === 'feasible'
        ? 'text-amber-400'
        : 'text-red-400';

  return (
    <div className="space-y-3">
      {/* Circular gauge */}
      <div className="relative flex items-center justify-center">
        <svg className="w-24 h-24 transform -rotate-90">
          {/* Background arc */}
          <circle
            cx="48"
            cy="48"
            r="40"
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            className="text-slate-700"
          />
          {/* Progress arc */}
          <circle
            cx="48"
            cy="48"
            r="40"
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            className="text-cyan-400"
            strokeDasharray={`${satisfactionRate * 2.51} 251`}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute text-center">
          <div className="text-xl font-bold text-white">
            {satisfactionRate.toFixed(0)}%
          </div>
          <div className="text-xs text-slate-500">SAT</div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-lg font-bold text-white">
            {metrics.constraintsSatisfied}
          </div>
          <div className="text-xs text-slate-500">Satisfied</div>
        </div>
        <div>
          <div className="text-lg font-bold text-red-400">{unsatisfied}</div>
          <div className="text-xs text-slate-500">Violated</div>
        </div>
        <div>
          <div className={`text-sm font-bold uppercase ${qualityColor}`}>
            {metrics.solutionQuality}
          </div>
          <div className="text-xs text-slate-500">Quality</div>
        </div>
      </div>
    </div>
  );
}

export default SolverMini;
