/**
 * Fragility Mini Visualization
 *
 * Mini network diagram for fragility.
 */

'use client';

import { useMemo } from 'react';
import type { FragilityMetrics } from '../types';

interface FragilityMiniProps {
  metrics: FragilityMetrics;
}

export function FragilityMini({ metrics }: FragilityMiniProps) {
  // Generate node positions
  const nodes = useMemo(() => {
    const count = 7;
    const centerX = 60;
    const centerY = 40;
    const radius = 30;

    return Array.from({ length: count }, (_, i) => {
      const angle = (i / count) * Math.PI * 2 - Math.PI / 2;
      return {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        critical: i < metrics.criticalPaths,
      };
    });
  }, [metrics.criticalPaths]);

  const fragilityColor =
    metrics.systemFragility > 0.5
      ? 'text-red-400'
      : metrics.systemFragility > 0.3
        ? 'text-amber-400'
        : 'text-green-400';

  const redundancyColor =
    metrics.redundancyLevel > 70
      ? 'text-green-400'
      : metrics.redundancyLevel > 50
        ? 'text-amber-400'
        : 'text-red-400';

  return (
    <div className="space-y-3">
      {/* Mini network */}
      <div className="relative h-20">
        <svg className="w-full h-full" viewBox="0 0 120 80">
          {/* Edges */}
          {nodes.map((node, i) =>
            nodes.slice(i + 1).map((target, j) => (
              <line
                key={`${i}-${j}`}
                x1={node.x}
                y1={node.y}
                x2={target.x}
                y2={target.y}
                stroke={
                  node.critical || target.critical ? '#ef4444' : '#475569'
                }
                strokeWidth={node.critical && target.critical ? 2 : 1}
                opacity={0.5}
              />
            ))
          )}

          {/* Nodes */}
          {nodes.map((node, i) => (
            <circle
              key={i}
              cx={node.x}
              cy={node.y}
              r={node.critical ? 6 : 4}
              fill={node.critical ? '#ef4444' : '#22c55e'}
              className={node.critical ? 'animate-pulse' : ''}
            />
          ))}

          {/* Center node */}
          <circle cx={60} cy={40} r={8} fill="#06b6d4" />
        </svg>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <div className={`text-lg font-bold ${fragilityColor}`}>
            {metrics.systemFragility.toFixed(2)}
          </div>
          <div className="text-xs text-slate-500">Fragility</div>
        </div>
        <div>
          <div className="text-lg font-bold text-red-400">
            {metrics.criticalPaths}
          </div>
          <div className="text-xs text-slate-500">Critical</div>
        </div>
        <div>
          <div className={`text-lg font-bold ${redundancyColor}`}>
            {metrics.redundancyLevel}%
          </div>
          <div className="text-xs text-slate-500">Redundancy</div>
        </div>
      </div>
    </div>
  );
}

export default FragilityMini;
