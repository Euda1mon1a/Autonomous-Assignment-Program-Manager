'use client';

/**
 * Coverage Trend Chart Component
 *
 * Displays a trend line chart showing coverage percentage over time
 * for schedule generation runs. Uses pure CSS/SVG for visualization.
 */
import { useMemo } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

export interface CoverageDataPoint {
  timestamp: string;
  coverage: number;
  algorithm?: string;
  runId?: string;
}

export interface CoverageTrendChartProps {
  data: CoverageDataPoint[];
  height?: number;
  showLegend?: boolean;
  targetCoverage?: number;
}

// ============================================================================
// Mock Data (for development)
// ============================================================================

export const MOCK_COVERAGE_DATA: CoverageDataPoint[] = [
  { timestamp: '2024-12-01', coverage: 92.5, algorithm: 'greedy' },
  { timestamp: '2024-12-05', coverage: 94.2, algorithm: 'hybrid' },
  { timestamp: '2024-12-08', coverage: 93.8, algorithm: 'cp_sat' },
  { timestamp: '2024-12-12', coverage: 95.1, algorithm: 'hybrid' },
  { timestamp: '2024-12-15', coverage: 96.3, algorithm: 'hybrid' },
  { timestamp: '2024-12-18', coverage: 95.8, algorithm: 'cp_sat' },
  { timestamp: '2024-12-20', coverage: 97.2, algorithm: 'hybrid' },
  { timestamp: '2024-12-22', coverage: 96.8, algorithm: 'hybrid' },
];

// ============================================================================
// Component
// ============================================================================

export function CoverageTrendChart({
  data,
  height = 200,
  showLegend = true,
  targetCoverage = 95,
}: CoverageTrendChartProps) {
  const chartData = useMemo(() => {
    if (data.length === 0) return null;

    const minCoverage = Math.min(...data.map((d) => d.coverage), targetCoverage - 5);
    const maxCoverage = Math.max(...data.map((d) => d.coverage), targetCoverage + 5);
    const range = maxCoverage - minCoverage || 1;

    const points = data.map((d, i) => {
      const x = (i / (data.length - 1 || 1)) * 100;
      const y = 100 - ((d.coverage - minCoverage) / range) * 100;
      return { x, y, ...d };
    });

    const pathD = points
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
      .join(' ');

    const areaD = `${pathD} L ${points[points.length - 1].x} 100 L ${points[0].x} 100 Z`;

    const targetY = 100 - ((targetCoverage - minCoverage) / range) * 100;

    const current = data[data.length - 1]?.coverage || 0;
    const previous = data[data.length - 2]?.coverage || current;
    const trend = current > previous ? 'up' : current < previous ? 'down' : 'stable';
    const change = current - previous;

    const average = data.reduce((sum, d) => sum + d.coverage, 0) / data.length;

    return {
      points,
      pathD,
      areaD,
      targetY,
      minCoverage,
      maxCoverage,
      trend,
      change,
      current,
      average,
    };
  }, [data, targetCoverage]);

  if (!chartData || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-slate-800/50 rounded-lg border border-slate-700/50"
        style={{ height }}
      >
        <div className="text-center text-slate-400">
          <p className="text-sm">No coverage data available</p>
          <p className="text-xs mt-1">Run schedule generation to see trends</p>
        </div>
      </div>
    );
  }

  const TrendIcon = chartData.trend === 'up' ? TrendingUp : chartData.trend === 'down' ? TrendingDown : Minus;
  const trendColor = chartData.trend === 'up' ? 'text-green-400' : chartData.trend === 'down' ? 'text-red-400' : 'text-gray-400';

  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-medium text-slate-300">Coverage Trend</h3>
          <p className="text-xs text-slate-500">Last {data.length} runs</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-right">
            <div className="text-2xl font-bold text-white">{chartData.current.toFixed(1)}%</div>
            <div className={`flex items-center gap-1 text-xs ${trendColor}`}>
              <TrendIcon className="w-3 h-3" />
              {chartData.change >= 0 ? '+' : ''}{chartData.change.toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="relative" style={{ height }}>
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          className="w-full h-full"
        >
          {/* Grid lines */}
          <defs>
            <pattern id="grid" width="25" height="25" patternUnits="userSpaceOnUse">
              <path
                d="M 25 0 L 0 0 0 25"
                fill="none"
                stroke="currentColor"
                strokeWidth="0.2"
                className="text-slate-700"
              />
            </pattern>
          </defs>
          <rect width="100" height="100" fill="url(#grid)" />

          {/* Target line */}
          <line
            x1="0"
            y1={chartData.targetY}
            x2="100"
            y2={chartData.targetY}
            stroke="currentColor"
            strokeWidth="0.5"
            strokeDasharray="2 2"
            className="text-green-500"
          />

          {/* Gradient fill */}
          <defs>
            <linearGradient id="coverageGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgb(139, 92, 246)" stopOpacity="0.3" />
              <stop offset="100%" stopColor="rgb(139, 92, 246)" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path
            d={chartData.areaD}
            fill="url(#coverageGradient)"
          />

          {/* Line */}
          <path
            d={chartData.pathD}
            fill="none"
            stroke="rgb(139, 92, 246)"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data points */}
          {chartData.points.map((point, i) => (
            <g key={i}>
              <circle
                cx={point.x}
                cy={point.y}
                r="2"
                fill="rgb(139, 92, 246)"
                className="transition-all duration-200 hover:r-3"
              />
              <circle
                cx={point.x}
                cy={point.y}
                r="1"
                fill="white"
              />
            </g>
          ))}
        </svg>

        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-xs text-slate-500 -ml-1 py-1">
          <span>{chartData.maxCoverage.toFixed(0)}%</span>
          <span>{chartData.minCoverage.toFixed(0)}%</span>
        </div>

        {/* Target label */}
        <div
          className="absolute right-0 text-xs text-green-400 -mr-1"
          style={{ top: `${chartData.targetY}%`, transform: 'translateY(-50%)' }}
        >
          Target
        </div>
      </div>

      {/* Legend */}
      {showLegend && (
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-700/50">
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 bg-violet-500 rounded" />
              <span className="text-slate-400">Coverage</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 bg-green-500 rounded border-dashed" style={{ borderTopWidth: 1, borderTopStyle: 'dashed' }} />
              <span className="text-slate-400">Target ({targetCoverage}%)</span>
            </div>
          </div>
          <div className="text-xs text-slate-500">
            Avg: {chartData.average.toFixed(1)}%
          </div>
        </div>
      )}
    </div>
  );
}

export default CoverageTrendChart;
