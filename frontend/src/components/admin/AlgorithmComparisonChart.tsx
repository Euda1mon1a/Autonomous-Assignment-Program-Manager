'use client';

/**
 * Algorithm Comparison Chart Component
 *
 * Displays a bar chart comparing performance metrics across different
 * scheduling algorithms. Uses pure CSS/SVG for visualization.
 */
import { useMemo, useState } from 'react';
import type { Algorithm } from '@/types/admin-scheduling';

// ============================================================================
// Types
// ============================================================================

export interface AlgorithmMetrics {
  algorithm: Algorithm;
  coverage: number;
  violations: number;
  fairness: number;
  runtime: number;
  stability: number;
  runCount: number;
}

export interface AlgorithmComparisonChartProps {
  data: AlgorithmMetrics[];
  metric?: 'coverage' | 'violations' | 'fairness' | 'runtime' | 'stability';
  height?: number;
}

// ============================================================================
// Mock Data (for development)
// ============================================================================

export const MOCK_ALGORITHM_DATA: AlgorithmMetrics[] = [
  { algorithm: 'greedy', coverage: 89.5, violations: 12, fairness: 72.3, runtime: 2.5, stability: 78.2, runCount: 45 },
  { algorithm: 'cp_sat', coverage: 96.2, violations: 2, fairness: 88.7, runtime: 45.3, stability: 92.1, runCount: 38 },
  { algorithm: 'pulp', coverage: 91.8, violations: 5, fairness: 81.2, runtime: 8.2, stability: 85.6, runCount: 22 },
  { algorithm: 'hybrid', coverage: 97.5, violations: 1, fairness: 91.5, runtime: 28.7, stability: 94.8, runCount: 67 },
];

// ============================================================================
// Constants
// ============================================================================

const ALGORITHM_LABELS: Record<Algorithm, string> = {
  greedy: 'Greedy',
  cp_sat: 'CP-SAT',
  pulp: 'PuLP',
  hybrid: 'Hybrid',
};

const ALGORITHM_COLORS: Record<Algorithm, string> = {
  greedy: 'bg-orange-500',
  cp_sat: 'bg-blue-500',
  pulp: 'bg-green-500',
  hybrid: 'bg-violet-500',
};

const METRIC_CONFIG: Record<string, { label: string; unit: string; higherIsBetter: boolean; format: (v: number) => string }> = {
  coverage: { label: 'Coverage', unit: '%', higherIsBetter: true, format: (v) => `${v.toFixed(1)}%` },
  violations: { label: 'ACGME Violations', unit: '', higherIsBetter: false, format: (v) => v.toString() },
  fairness: { label: 'Fairness Score', unit: '%', higherIsBetter: true, format: (v) => `${v.toFixed(1)}%` },
  runtime: { label: 'Runtime', unit: 's', higherIsBetter: false, format: (v) => `${v.toFixed(1)}s` },
  stability: { label: 'Stability', unit: '%', higherIsBetter: true, format: (v) => `${v.toFixed(1)}%` },
};

// ============================================================================
// Component
// ============================================================================

export function AlgorithmComparisonChart({
  data,
  metric = 'coverage',
  height = 250,
}: AlgorithmComparisonChartProps) {
  const [selectedMetric, setSelectedMetric] = useState<keyof typeof METRIC_CONFIG>(metric);
  const [hoveredBar, setHoveredBar] = useState<Algorithm | null>(null);

  const chartData = useMemo(() => {
    if (data.length === 0) return null;

    const config = METRIC_CONFIG[selectedMetric];
    const values = data.map((d) => d[selectedMetric] as number);
    const maxValue = Math.max(...values);
    const minValue = Math.min(...values);

    // Determine best performer
    const sortedByMetric = [...data].sort((a, b) => {
      const aVal = a[selectedMetric] as number;
      const bVal = b[selectedMetric] as number;
      return config.higherIsBetter ? bVal - aVal : aVal - bVal;
    });
    const best = sortedByMetric[0]?.algorithm;

    return {
      config,
      maxValue,
      minValue,
      best,
      bars: data.map((d) => ({
        ...d,
        value: d[selectedMetric] as number,
        percentage: maxValue > 0 ? ((d[selectedMetric] as number) / maxValue) * 100 : 0,
        isBest: d.algorithm === best,
      })),
    };
  }, [data, selectedMetric]);

  if (!chartData || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-slate-800/50 rounded-lg border border-slate-700/50"
        style={{ height }}
      >
        <div className="text-center text-slate-400">
          <p className="text-sm">No algorithm data available</p>
          <p className="text-xs mt-1">Run experiments to compare algorithms</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-medium text-slate-300">Algorithm Comparison</h3>
          <p className="text-xs text-slate-500">Based on {data.reduce((sum, d) => sum + d.runCount, 0)} runs</p>
        </div>
        <select
          value={selectedMetric}
          onChange={(e) => setSelectedMetric(e.target.value as keyof typeof METRIC_CONFIG)}
          className="px-3 py-1.5 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
        >
          {Object.entries(METRIC_CONFIG).map(([key, config]) => (
            <option key={key} value={key}>{config.label}</option>
          ))}
        </select>
      </div>

      {/* Chart */}
      <div className="relative" style={{ height: height - 80 }}>
        <div className="absolute inset-0 flex items-end gap-4 px-4">
          {chartData.bars.map((bar) => (
            <div
              key={bar.algorithm}
              className="flex-1 flex flex-col items-center"
              onMouseEnter={() => setHoveredBar(bar.algorithm)}
              onMouseLeave={() => setHoveredBar(null)}
            >
              {/* Value label */}
              <div
                className={`text-sm font-medium mb-2 transition-opacity ${
                  hoveredBar === bar.algorithm || hoveredBar === null ? 'opacity-100' : 'opacity-50'
                } ${bar.isBest ? 'text-green-400' : 'text-white'}`}
              >
                {chartData.config.format(bar.value)}
                {bar.isBest && <span className="ml-1 text-xs">★</span>}
              </div>

              {/* Bar */}
              <div
                className={`w-full rounded-t-lg transition-all duration-300 ${ALGORITHM_COLORS[bar.algorithm]} ${
                  hoveredBar === bar.algorithm ? 'opacity-100 scale-x-110' : hoveredBar === null ? 'opacity-90' : 'opacity-50'
                }`}
                style={{
                  height: `${bar.percentage}%`,
                  minHeight: '4px',
                }}
              />

              {/* Label */}
              <div className="mt-2 text-xs text-slate-400">{ALGORITHM_LABELS[bar.algorithm]}</div>
              <div className="text-xs text-slate-500">{bar.runCount} runs</div>
            </div>
          ))}
        </div>

        {/* Y-axis grid lines */}
        <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
          {[100, 75, 50, 25, 0].map((pct) => (
            <div key={pct} className="flex items-center">
              <div className="w-full border-t border-slate-700/30" />
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-700/50">
        <div className="flex items-center gap-4 text-xs">
          {data.map((d) => (
            <div key={d.algorithm} className="flex items-center gap-1.5">
              <div className={`w-3 h-3 rounded ${ALGORITHM_COLORS[d.algorithm]}`} />
              <span className="text-slate-400">{ALGORITHM_LABELS[d.algorithm]}</span>
            </div>
          ))}
        </div>
        <div className="text-xs text-slate-500">
          {chartData.config.higherIsBetter ? 'Higher is better' : 'Lower is better'}
        </div>
      </div>

      {/* Tooltip */}
      {hoveredBar && (
        <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 bg-slate-900 border border-slate-700 rounded-lg p-3 shadow-xl z-10">
          <div className="text-sm font-medium text-white mb-2">{ALGORITHM_LABELS[hoveredBar]}</div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            {Object.entries(METRIC_CONFIG).map(([key, config]) => {
              const value = chartData.bars.find((b) => b.algorithm === hoveredBar)?.[key as keyof AlgorithmMetrics] as number;
              return (
                <div key={key} className="flex justify-between gap-2">
                  <span className="text-slate-400">{config.label}:</span>
                  <span className="text-white">{config.format(value)}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default AlgorithmComparisonChart;
