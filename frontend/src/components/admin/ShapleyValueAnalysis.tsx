'use client';

/**
 * Shapley Value Analysis Component
 *
 * Displays comprehensive Shapley-based workload equity analysis including:
 * - Summary statistics cards
 * - Horizontal bar chart comparing actual vs fair workload
 * - Sortable faculty table with equity gaps
 *
 * Uses cooperative game theory's Shapley value to determine fair workload
 * allocation based on each faculty member's marginal contribution.
 */

import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import {
  RefreshCw,
  AlertTriangle,
  Info,
  TrendingUp,
  TrendingDown,
  Users,
  Scale,
  Target,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { DataTable, Column } from '@/components/ui/DataTable';
import {
  useShapleyWorkload,
  getEquityGapColorClass,
  getEquityStatusLabel,
  formatEquityGap,
  getEquityGapPercentage,
  type ShapleyFacultyResult,
} from '@/hooks/useShapleyWorkload';

// ============================================================================
// Types
// ============================================================================

interface ShapleyValueAnalysisProps {
  /** Faculty member IDs to analyze */
  facultyIds: string[] | null;
  /** Start date in YYYY-MM-DD format */
  startDate: string | null;
  /** End date in YYYY-MM-DD format */
  endDate: string | null;
  /** Optional Monte Carlo samples (default 1000) */
  numSamples?: number;
  /** Whether parent data is loading */
  isParentLoading?: boolean;
  /** Optional class name */
  className?: string;
}

interface ChartDataPoint {
  name: string;
  facultyId: string;
  currentWorkload: number;
  fairTarget: number;
  equityGap: number;
  shapleyValue: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name?: string;
    value?: number;
    color?: string;
    dataKey?: string;
    payload?: ChartDataPoint;
  }>;
  label?: string;
}

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * Summary stat card
 */
function StatCard({
  title,
  value,
  icon: Icon,
  variant = 'default',
  subtitle,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  variant?: 'default' | 'success' | 'warning' | 'danger';
  subtitle?: string;
}) {
  const variantClasses = {
    default: 'text-slate-300',
    success: 'text-green-500',
    warning: 'text-yellow-500',
    danger: 'text-red-500',
  };

  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardContent className="pt-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-slate-400">{title}</p>
            <p className={`text-2xl font-bold mt-1 ${variantClasses[variant]}`}>
              {value}
            </p>
            {subtitle && (
              <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
            )}
          </div>
          <Icon className={`w-5 h-5 ${variantClasses[variant]}`} />
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Custom tooltip for the bar chart
 */
function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const data = payload[0]?.payload;
  if (!data) return null;

  return (
    <div className="bg-slate-800 border border-slate-600 rounded-lg shadow-lg p-3">
      <p className="text-sm font-semibold text-white mb-2">{data.name}</p>
      <div className="space-y-1 text-sm">
        <div className="flex items-center justify-between gap-4">
          <span className="text-slate-300">Current Workload:</span>
          <span className="font-semibold text-blue-400">
            {data.currentWorkload.toFixed(1)}h
          </span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-slate-300">Fair Target:</span>
          <span className="font-semibold text-green-400">
            {data.fairTarget.toFixed(1)}h
          </span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-slate-300">Equity Gap:</span>
          <span
            className={`font-semibold ${getEquityGapColorClass(data.equityGap)}`}
          >
            {formatEquityGap(data.equityGap)}
          </span>
        </div>
        <div className="flex items-center justify-between gap-4 pt-1 border-t border-slate-600">
          <span className="text-slate-300">Shapley Value:</span>
          <span className="font-semibold text-white">
            {(data.shapleyValue * 100).toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function ShapleyValueAnalysis({
  facultyIds,
  startDate,
  endDate,
  numSamples = 1000,
  isParentLoading = false,
  className = '',
}: ShapleyValueAnalysisProps) {
  const { data, isLoading, error } = useShapleyWorkload(
    facultyIds,
    startDate,
    endDate,
    numSamples
  );

  // Transform data for bar chart
  const chartData = useMemo<ChartDataPoint[]>(() => {
    if (!data?.facultyResults) return [];

    return data.facultyResults
      .map((r) => ({
        name: r.facultyName,
        facultyId: r.facultyId,
        currentWorkload: r.currentWorkload,
        fairTarget: r.fairWorkloadTarget,
        equityGap: r.equityGap,
        shapleyValue: r.shapleyValue,
      }))
      .sort((a, b) => b.equityGap - a.equityGap); // Sort by equity gap descending
  }, [data]);

  // Table columns
  const columns = useMemo<Column<ShapleyFacultyResult>[]>(
    () => [
      {
        key: 'facultyName',
        header: 'Faculty',
        accessor: (row) => row.facultyName,
        sortable: true,
      },
      {
        key: 'shapleyValue',
        header: 'Shapley %',
        accessor: (row) => row.shapleyValue,
        sortable: true,
        render: (value) => {
          const pct = ((value as number) * 100).toFixed(1);
          return <span className="font-medium">{pct}%</span>;
        },
      },
      {
        key: 'fairWorkloadTarget',
        header: 'Fair Target',
        accessor: (row) => row.fairWorkloadTarget,
        sortable: true,
        render: (value) => (
          <span className="text-green-400">{(value as number).toFixed(1)}h</span>
        ),
      },
      {
        key: 'currentWorkload',
        header: 'Actual',
        accessor: (row) => row.currentWorkload,
        sortable: true,
        render: (value) => (
          <span className="text-blue-400">{(value as number).toFixed(1)}h</span>
        ),
      },
      {
        key: 'equityGap',
        header: 'Equity Gap',
        accessor: (row) => row.equityGap,
        sortable: true,
        render: (value, row) => {
          const gap = value as number;
          const pct = getEquityGapPercentage(gap, row.fairWorkloadTarget);
          const status = getEquityStatusLabel(gap);

          return (
            <div className="flex items-center gap-2">
              <span className={`font-medium ${getEquityGapColorClass(gap)}`}>
                {formatEquityGap(gap)}
              </span>
              <Badge
                variant={
                  status === 'Fair'
                    ? 'success'
                    : status === 'Overworked'
                      ? 'danger'
                      : 'warning'
                }
                size="sm"
              >
                {Math.abs(pct).toFixed(0)}%
              </Badge>
            </div>
          );
        },
      },
    ],
    []
  );

  const loading = isLoading || isParentLoading;

  // Loading state
  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="bg-slate-800 border-slate-700">
              <CardContent className="flex items-center justify-center py-8">
                <RefreshCw className="w-5 h-5 animate-spin text-slate-300" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="flex items-center justify-center py-24">
            <div className="flex items-center gap-3 text-slate-300">
              <RefreshCw className="w-5 h-5 animate-spin" />
              <span>Calculating Shapley values (Monte Carlo simulation)...</span>
            </div>
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
            <span>Failed to calculate Shapley values: {error.message}</span>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Minimum faculty requirement
  if (!facultyIds || facultyIds.length < 2) {
    return (
      <div className={className}>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center text-slate-400">
              <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>Shapley value calculation requires at least 2 faculty members.</p>
              <p className="text-sm mt-1">
                Select a date range with faculty assignments.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // No data state
  if (!data || !data.facultyResults.length) {
    return (
      <div className={className}>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center text-slate-400">
              <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No Shapley data available for the selected period.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Equity Gap Std Dev"
          value={`${data.equityGapStdDev.toFixed(1)}h`}
          icon={Scale}
          variant={data.equityGapStdDev < 5 ? 'success' : data.equityGapStdDev < 10 ? 'warning' : 'danger'}
          subtitle="Lower is more equitable"
        />
        <StatCard
          title="Overworked Faculty"
          value={data.overworkedCount}
          icon={TrendingUp}
          variant={data.overworkedCount === 0 ? 'success' : data.overworkedCount <= 2 ? 'warning' : 'danger'}
          subtitle="Above fair share"
        />
        <StatCard
          title="Underworked Faculty"
          value={data.underworkedCount}
          icon={TrendingDown}
          variant={data.underworkedCount === 0 ? 'success' : data.underworkedCount <= 2 ? 'warning' : 'danger'}
          subtitle="Below fair share"
        />
        <StatCard
          title="Total Workload"
          value={`${data.totalWorkload.toFixed(0)}h`}
          icon={Target}
          subtitle={`${data.facultyResults.length} faculty`}
        />
      </div>

      {/* Bar Chart */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <span>Workload Distribution</span>
            <Badge variant="default" size="sm">
              Actual vs Fair Target
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 100, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis
                  type="number"
                  stroke="#94a3b8"
                  tickFormatter={(v) => `${v}h`}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="#94a3b8"
                  width={90}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <ReferenceLine x={0} stroke="#94a3b8" />
                <Bar
                  dataKey="fairTarget"
                  name="Fair Target"
                  fill="#22c55e"
                  opacity={0.6}
                  radius={[0, 4, 4, 0]}
                />
                <Bar dataKey="currentWorkload" name="Actual Workload" radius={[0, 4, 4, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        Math.abs(entry.equityGap) < 5
                          ? '#22c55e' // green for fair
                          : entry.equityGap > 0
                            ? '#ef4444' // red for overworked
                            : '#eab308' // yellow for underworked
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 flex items-center justify-center gap-6 text-sm text-slate-400">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500 opacity-60" />
              <span>Fair Target</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span>Fair (&lt;5h gap)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <span>Overworked</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <span>Underworked</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Faculty Table */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Faculty Shapley Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            data={data.facultyResults}
            columns={columns}
            rowKey={(row) => row.facultyId}
            pageSize={10}
            searchable
            className="[&_table]:bg-slate-800 [&_thead]:bg-slate-700 [&_th]:text-slate-300 [&_td]:text-slate-200 [&_input]:bg-slate-700 [&_input]:border-slate-600 [&_input]:text-white"
          />
        </CardContent>
      </Card>

      {/* Info Box */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-slate-400">
              <p className="font-medium text-slate-300 mb-1">About Shapley Values</p>
              <p>
                Shapley values use cooperative game theory to determine fair workload
                allocation based on each faculty member&apos;s marginal contribution to
                schedule coverage. A faculty with higher Shapley value provides more
                unique coverage and should receive a proportionally larger share of the
                total workload.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ShapleyValueAnalysis;
