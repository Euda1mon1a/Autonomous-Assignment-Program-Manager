/**
 * Fairness Mini Visualization
 *
 * Mini bar chart for workload distribution.
 */

'use client';

import { useMemo } from 'react';
import type { FairnessMetrics } from '../types';

interface FairnessMiniProps {
  metrics: FairnessMetrics;
}

export function FairnessMini({ metrics }: FairnessMiniProps) {
  // Generate bar heights based on Jains index
  const bars = useMemo(() => {
    const numBars = 8;
    const variance = 1 - metrics.jainsIndex;
    const heights: number[] = [];

    for (let i = 0; i < numBars; i++) {
      // More equal when Jains is higher
      const base = 0.7;
      const variation = (Math.random() - 0.5) * variance * 0.6;
      heights.push(Math.max(0.3, Math.min(1, base + variation)));
    }
    return heights;
  }, [metrics.jainsIndex]);

  const maxDevColor =
    metrics.maxDeviation > 20
      ? 'text-red-400'
      : metrics.maxDeviation > 10
        ? 'text-amber-400'
        : 'text-green-400';

  return (
    <div className="space-y-3">
      {/* Mini bar chart */}
      <div className="flex items-end justify-between h-16 gap-1">
        {bars.map((height, i) => (
          <div
            key={i}
            className="flex-1 bg-gradient-to-t from-purple-600 to-purple-400 rounded-t-sm transition-all"
            style={{ height: `${height * 100}%` }}
          />
        ))}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-lg font-bold text-white">
            {metrics.jainsIndex.toFixed(2)}
          </div>
          <div className="text-xs text-slate-500">Jain&apos;s</div>
        </div>
        <div>
          <div className="text-lg font-bold text-purple-400">
            {metrics.giniCoefficient.toFixed(2)}
          </div>
          <div className="text-xs text-slate-500">Gini</div>
        </div>
        <div>
          <div className={`text-lg font-bold ${maxDevColor}`}>
            ±{metrics.maxDeviation}%
          </div>
          <div className="text-xs text-slate-500">Max Dev</div>
        </div>
      </div>
    </div>
  );
}

export default FairnessMini;
