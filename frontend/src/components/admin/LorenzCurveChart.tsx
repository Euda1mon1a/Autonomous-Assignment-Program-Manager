'use client';

/**
 * Lorenz Curve Chart Component
 *
 * Visualizes workload inequality using the Lorenz curve - a graphical
 * representation of the cumulative distribution of workload across faculty.
 *
 * The area between the 45-degree equality line and the Lorenz curve
 * represents the Gini coefficient (larger area = more inequality).
 */

import { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { RefreshCw, AlertTriangle, Info, TrendingUp } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  useLorenzCurve,
  getGiniColorClass,
  getGiniLabel,
  getLorenzInterpretation,
  type LorenzDataPoint,
} from '@/hooks/useLorenzCurve';

// ============================================================================
// Types
// ============================================================================

interface LorenzCurveChartProps {
  /** Array of workload values (e.g., total scores per faculty) */
  values: number[] | null;
  /** Whether parent data is loading */
  isParentLoading?: boolean;
  /** Optional class name */
  className?: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name?: string;
    value?: number;
    color?: string;
    dataKey?: string;
  }>;
  label?: string;
}

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * Custom tooltip for the Lorenz curve chart
 */
function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const populationPct = parseFloat(label || '0');
  const lorenzEntry = payload.find((p) => p.dataKey === 'lorenz');
  const equalityEntry = payload.find((p) => p.dataKey === 'equality');

  return (
    <div className="bg-slate-800 border border-slate-600 rounded-lg shadow-lg p-3">
      <p className="text-sm font-semibold text-white mb-2">
        Bottom {populationPct.toFixed(0)}% of faculty
      </p>
      <div className="space-y-1 text-sm">
        <div className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span className="text-slate-300">Actual share</span>
          </span>
          <span className="font-semibold text-white">
            {lorenzEntry?.value?.toFixed(1)}%
          </span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-slate-400" />
            <span className="text-slate-300">If equal</span>
          </span>
          <span className="font-semibold text-white">
            {equalityEntry?.value?.toFixed(1)}%
          </span>
        </div>
      </div>
      {lorenzEntry?.value && equalityEntry?.value && (
        <div className="mt-2 pt-2 border-t border-slate-600 text-xs text-slate-400">
          Gap: {(equalityEntry.value - lorenzEntry.value).toFixed(1)}%
        </div>
      )}
    </div>
  );
}

/**
 * Gini interpretation panel
 */
function GiniInterpretation({
  gini,
  chartData,
}: {
  gini: number;
  chartData: LorenzDataPoint[];
}) {
  // Calculate what share the bottom 50% has
  const bottomHalfPoint = chartData.find((p) => p.population >= 50);
  const bottomHalfShare = bottomHalfPoint ? bottomHalfPoint.lorenz / 100 : undefined;

  const colorClass = getGiniColorClass(gini);
  const label = getGiniLabel(gini);
  const interpretation = getLorenzInterpretation(gini, bottomHalfShare);

  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardHeader className="pb-2">
        <CardTitle className="text-white text-base flex items-center gap-2">
          <TrendingUp className="w-4 h-4" />
          Gini Coefficient
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between mb-4">
          <span className={`text-3xl font-bold ${colorClass}`}>
            {gini.toFixed(3)}
          </span>
          <Badge
            variant={
              gini < 0.15 ? 'success' : gini < 0.25 ? 'warning' : 'danger'
            }
          >
            {label}
          </Badge>
        </div>

        <div className="space-y-3 text-sm">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
            <p className="text-slate-300">{interpretation}</p>
          </div>

          {bottomHalfShare !== undefined && (
            <div className="p-3 bg-slate-700/50 rounded-lg">
              <div className="text-slate-400 text-xs mb-1">
                Bottom 50% of faculty have:
              </div>
              <div className="text-white font-semibold">
                {(bottomHalfShare * 100).toFixed(1)}% of total workload
              </div>
              <div className="text-slate-400 text-xs mt-1">
                (In a perfectly equal system, they would have 50%)
              </div>
            </div>
          )}

          <div className="pt-2 border-t border-slate-700">
            <div className="text-slate-400 text-xs mb-2">Reference:</div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="text-center">
                <div className="text-green-500 font-semibold">&lt; 0.15</div>
                <div className="text-slate-400">Equitable</div>
              </div>
              <div className="text-center">
                <div className="text-yellow-500 font-semibold">0.15 - 0.25</div>
                <div className="text-slate-400">Moderate</div>
              </div>
              <div className="text-center">
                <div className="text-red-500 font-semibold">&gt; 0.25</div>
                <div className="text-slate-400">High</div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function LorenzCurveChart({
  values,
  isParentLoading = false,
  className = '',
}: LorenzCurveChartProps) {
  const { data, isLoading, error } = useLorenzCurve(values);

  // Determine the gradient color based on Gini
  const gradientColor = useMemo(() => {
    if (!data) return '#3b82f6'; // blue-500 default
    if (data.giniCoefficient < 0.15) return '#22c55e'; // green-500
    if (data.giniCoefficient < 0.25) return '#eab308'; // yellow-500
    return '#ef4444'; // red-500
  }, [data]);

  const loading = isLoading || isParentLoading;

  // Loading state
  if (loading) {
    return (
      <div className={`grid grid-cols-1 lg:grid-cols-3 gap-6 ${className}`}>
        <Card className="lg:col-span-2 bg-slate-800 border-slate-700">
          <CardContent className="flex items-center justify-center py-24">
            <div className="flex items-center gap-3 text-slate-300">
              <RefreshCw className="w-5 h-5 animate-spin" />
              <span>Generating Lorenz curve...</span>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="flex items-center justify-center py-24">
            <RefreshCw className="w-5 h-5 animate-spin text-slate-300" />
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={className}>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="flex items-center gap-3 py-8 text-red-400">
            <AlertTriangle className="w-5 h-5" />
            <span>Failed to generate Lorenz curve: {error.message}</span>
          </CardContent>
        </Card>
      </div>
    );
  }

  // No data state
  if (!data || !data.chartData.length) {
    return (
      <div className={className}>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center text-slate-400">
              <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No workload data available to generate Lorenz curve.</p>
              <p className="text-sm mt-1">
                Select a date range with faculty assignments.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-3 gap-6 ${className}`}>
      {/* Lorenz Curve Chart */}
      <Card className="lg:col-span-2 bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <span>Lorenz Curve</span>
            <Badge variant="default" size="sm">
              {values?.length || 0} faculty
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={data.chartData}
                margin={{ top: 10, right: 30, left: 0, bottom: 10 }}
              >
                <defs>
                  <linearGradient id="lorenzGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={gradientColor} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={gradientColor} stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis
                  dataKey="population"
                  stroke="#94a3b8"
                  tickFormatter={(v) => `${v}%`}
                  label={{
                    value: 'Cumulative % of Faculty',
                    position: 'insideBottom',
                    offset: -5,
                    fill: '#94a3b8',
                    fontSize: 12,
                  }}
                />
                <YAxis
                  stroke="#94a3b8"
                  tickFormatter={(v) => `${v}%`}
                  label={{
                    value: 'Cumulative % of Workload',
                    angle: -90,
                    position: 'insideLeft',
                    fill: '#94a3b8',
                    fontSize: 12,
                  }}
                />
                <Tooltip content={<CustomTooltip />} />
                {/* Equality line (45-degree diagonal) */}
                <ReferenceLine
                  segment={[
                    { x: 0, y: 0 },
                    { x: 100, y: 100 },
                  ]}
                  stroke="#94a3b8"
                  strokeDasharray="5 5"
                  strokeWidth={2}
                />
                {/* Lorenz curve with shaded area */}
                <Area
                  type="monotone"
                  dataKey="lorenz"
                  stroke={gradientColor}
                  strokeWidth={2}
                  fill="url(#lorenzGradient)"
                  name="Actual Distribution"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 flex items-center justify-center gap-6 text-sm text-slate-400">
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-0.5"
                style={{ backgroundColor: gradientColor }}
              />
              <span>Lorenz Curve (Actual)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-0.5 bg-slate-400 border-dashed" />
              <span>Perfect Equality</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Gini Interpretation Panel */}
      <GiniInterpretation gini={data.giniCoefficient} chartData={data.chartData} />
    </div>
  );
}

export default LorenzCurveChart;
