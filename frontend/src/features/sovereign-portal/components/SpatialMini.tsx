/**
 * Spatial Mini Visualization
 *
 * Mini heatmap for the spatial coverage panel.
 */

'use client';

import { useMemo } from 'react';
import type { SpatialMetrics } from '../types';

interface SpatialMiniProps {
  metrics: SpatialMetrics;
}

export function SpatialMini({ metrics }: SpatialMiniProps) {
  // Generate mini heatmap grid (7 days x 4 time slots)
  const grid = useMemo(() => {
    const cells: { filled: boolean; intensity: number }[] = [];
    const fillRate = metrics.coveragePercent / 100;

    for (let i = 0; i < 28; i++) {
      const filled = Math.random() < fillRate;
      const intensity = filled ? 0.5 + Math.random() * 0.5 : 0.1;
      cells.push({ filled, intensity });
    }
    return cells;
  }, [metrics.coveragePercent]);

  return (
    <div className="space-y-3">
      {/* Mini heatmap */}
      <div className="grid grid-cols-7 gap-1">
        {grid.map((cell, i) => (
          <div
            key={i}
            className="aspect-square rounded-sm"
            style={{
              backgroundColor: cell.filled
                ? `rgba(34, 197, 94, ${cell.intensity})`
                : `rgba(100, 116, 139, ${cell.intensity})`,
            }}
          />
        ))}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-lg font-bold text-white">
            {metrics.coveragePercent.toFixed(1)}%
          </div>
          <div className="text-xs text-slate-500">Coverage</div>
        </div>
        <div>
          <div className="text-lg font-bold text-amber-400">
            {metrics.gapCount}
          </div>
          <div className="text-xs text-slate-500">Gaps</div>
        </div>
        <div>
          <div className="text-lg font-bold text-cyan-400">
            {(metrics.distributionScore * 100).toFixed(0)}%
          </div>
          <div className="text-xs text-slate-500">Distribution</div>
        </div>
      </div>
    </div>
  );
}

export default SpatialMini;
