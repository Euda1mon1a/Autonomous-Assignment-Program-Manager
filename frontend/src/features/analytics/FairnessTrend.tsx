'use client';

/**
 * FairnessTrend Component
 *
 * Displays fairness metrics trend over time with line charts,
 * including Gini coefficient, workload variance, and PGY equity.
 */

import { useState } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, TrendingDown, Info, BarChart3, Activity } from 'lucide-react';
import { useFairnessTrend, usePgyEquity } from './hooks';
import type { TimePeriod, TrendDirection } from './types';
import { TIME_PERIOD_LABELS } from './types';

// ============================================================================
// Types
// ============================================================================

interface FairnessTrendProps {
  months?: number;
  showPgyComparison?: boolean;
  className?: string;
}

type ChartType = 'line' | 'bar';
type MetricType = 'gini' | 'variance' | 'equity' | 'all';

// Recharts tooltip payload type
interface TooltipPayloadEntry {
  name?: string;
  value?: number | string;
  color?: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadEntry[];
  label?: string;
}

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * Custom tooltip for charts
 */
function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
      <p className="text-sm font-semibold text-gray-900 mb-2">{label}</p>
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center justify-between gap-4 text-sm">
          <span className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-gray-700">{entry.name}</span>
          </span>
          <span className="font-semibold text-gray-900">
            {typeof entry.value === 'number' ? entry.value.toFixed(3) : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}

/**
 * Period selector buttons
 */
function PeriodSelector({
  selectedPeriod,
  onPeriodChange,
}: {
  selectedPeriod: TimePeriod;
  onPeriodChange: (period: TimePeriod) => void;
}) {
  const periods: TimePeriod[] = ['7d', '30d', '90d', '180d', '1y'];

  return (
    <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1" role="group" aria-label="Time period selection">
      {periods.map((period) => (
        <button
          key={period}
          type="button"
          onClick={() => onPeriodChange(period)}
          aria-pressed={selectedPeriod === period}
          aria-label={`Select ${TIME_PERIOD_LABELS[period]} period`}
          className={`
            px-3 py-1.5 rounded-md text-xs font-medium transition-colors
            ${
              selectedPeriod === period
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }
          `}
        >
          {TIME_PERIOD_LABELS[period]}
        </button>
      ))}
    </div>
  );
}

/**
 * Metric selector
 */
function MetricSelector({
  selectedMetric,
  onMetricChange,
}: {
  selectedMetric: MetricType;
  onMetricChange: (metric: MetricType) => void;
}) {
  const metrics: Array<{ value: MetricType; label: string }> = [
    { value: 'all', label: 'All Metrics' },
    { value: 'gini', label: 'Gini Coefficient' },
    { value: 'variance', label: 'Workload Variance' },
    { value: 'equity', label: 'PGY Equity' },
  ];

  return (
    <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1" role="group" aria-label="Metric filter selection">
      {metrics.map((metric) => (
        <button
          key={metric.value}
          type="button"
          onClick={() => onMetricChange(metric.value)}
          aria-pressed={selectedMetric === metric.value}
          aria-label={`Filter by ${metric.label}`}
          className={`
            px-3 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap
            ${
              selectedMetric === metric.value
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }
          `}
        >
          {metric.label}
        </button>
      ))}
    </div>
  );
}

/**
 * Trend indicator
 */
function TrendIndicator({
  direction,
  value,
}: {
  direction: TrendDirection;
  value: number;
}) {
  const isPositive = direction === 'up';
  const Icon = direction === 'up' ? TrendingUp : direction === 'down' ? TrendingDown : Activity;

  return (
    <div className={`flex items-center gap-1 ${
      direction === 'stable' ? 'text-gray-600' : isPositive ? 'text-green-600' : 'text-red-600'
    }`}>
      <Icon className="w-4 h-4" />
      <span className="text-sm font-medium">
        {isPositive && '+'}
        {value.toFixed(1)}%
      </span>
    </div>
  );
}

/**
 * Statistics summary card
 */
function StatisticsSummary({
  avgGini,
  avgVariance,
  avgPgyEquity,
  trend,
  improvementRate,
}: {
  avgGini: number;
  avgVariance: number;
  avgPgyEquity: number;
  trend: TrendDirection;
  improvementRate: number;
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 bg-blue-50 border border-blue-200 rounded-lg" role="region" aria-label="Fairness statistics summary">
      <div role="group" aria-label={`Average Gini Coefficient: ${avgGini.toFixed(3)}`}>
        <p className="text-xs text-gray-600 mb-1">Avg Gini Coefficient</p>
        <p className="text-lg font-bold text-gray-900">{avgGini.toFixed(3)}</p>
      </div>
      <div role="group" aria-label={`Average Workload Variance: ${avgVariance.toFixed(2)}`}>
        <p className="text-xs text-gray-600 mb-1">Avg Workload Variance</p>
        <p className="text-lg font-bold text-gray-900">{avgVariance.toFixed(2)}</p>
      </div>
      <div role="group" aria-label={`Average PGY Equity: ${avgPgyEquity.toFixed(2)}`}>
        <p className="text-xs text-gray-600 mb-1">Avg PGY Equity</p>
        <p className="text-lg font-bold text-gray-900">{avgPgyEquity.toFixed(2)}</p>
      </div>
      <div className="sm:col-span-3 pt-3 border-t border-blue-300">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-700">Overall Trend</span>
          <TrendIndicator direction={trend} value={improvementRate} />
        </div>
      </div>
    </div>
  );
}

/**
 * PGY Equity Comparison Chart
 */
function PgyEquityChart({ className = '' }: { className?: string }) {
  const { data: pgyData, isLoading, error } = usePgyEquity();

  if (isLoading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-300 rounded w-48 mb-4" />
          <div className="h-64 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (error || !pgyData) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <p className="text-sm text-red-600">Failed to load PGY equity data</p>
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`} role="region" aria-label="PGY Level Equity Comparison">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">PGY Level Equity Comparison</h3>
        <BarChart3 className="w-5 h-5 text-gray-400" aria-hidden="true" />
      </div>

      <div role="img" aria-label="Bar chart comparing shift distributions across PGY levels, showing average shifts, night shifts, weekend shifts, and holiday shifts">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={pgyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="pgyLevel"
              tickFormatter={(value) => `PGY-${value}`}
              tick={{ fontSize: 12 }}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            <Bar dataKey="averageShifts" name="Avg Shifts" fill="#3b82f6" />
            <Bar dataKey="nightShifts" name="Night Shifts" fill="#8b5cf6" />
            <Bar dataKey="weekendShifts" name="Weekend Shifts" fill="#ec4899" />
            <Bar dataKey="holidayShifts" name="Holiday Shifts" fill="#f59e0b" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function FairnessTrend({
  months = 3,
  showPgyComparison = true,
  className = '',
}: FairnessTrendProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<TimePeriod>('30d');
  const [selectedMetric, setSelectedMetric] = useState<MetricType>('all');
  const [chartType, setChartType] = useState<ChartType>('line');

  const { data, isLoading, error } = useFairnessTrend(months);

  if (isLoading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-300 rounded w-64 mb-4" />
          <div className="h-96 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={`bg-white border border-red-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center gap-2 text-red-600">
          <Info className="w-5 h-5" />
          <p className="text-sm font-medium">Failed to load fairness trend data</p>
        </div>
      </div>
    );
  }

  // Format data for charts
  const chartData = data.dataPoints.map((point) => ({
    date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    'Gini Coefficient': point.giniCoefficient,
    'Workload Variance': point.workloadVariance,
    'PGY Equity Score': point.pgyEquityScore,
    'Fairness Score': point.fairnessScore,
  }));

  // Filter lines based on selected metric
  const getVisibleLines = () => {
    if (selectedMetric === 'all') {
      return ['Gini Coefficient', 'Workload Variance', 'PGY Equity Score', 'Fairness Score'];
    }
    if (selectedMetric === 'gini') return ['Gini Coefficient'];
    if (selectedMetric === 'variance') return ['Workload Variance'];
    if (selectedMetric === 'equity') return ['PGY Equity Score'];
    return [];
  };

  const visibleLines = getVisibleLines();

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Main Trend Chart */}
      <div className="bg-white border border-gray-200 rounded-lg p-6" role="region" aria-label="Fairness Metrics Trend">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Fairness Metrics Trend</h3>
            <p className="text-sm text-gray-600">Track fairness metrics over time</p>
          </div>
          <div className="flex items-center gap-2">
            <MetricSelector selectedMetric={selectedMetric} onMetricChange={setSelectedMetric} />
          </div>
        </div>

        {/* Statistics Summary */}
        <StatisticsSummary
          avgGini={data.statistics.avgGini}
          avgVariance={data.statistics.avgVariance}
          avgPgyEquity={data.statistics.avgPgyEquity}
          trend={data.statistics.trend}
          improvementRate={data.statistics.improvementRate}
        />

        {/* Chart */}
        <div className="mt-6" role="img" aria-label={`Line chart showing fairness metrics trends over time. Displaying ${visibleLines.join(', ')}`}>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                tickMargin={10}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }} />
              {visibleLines.includes('Gini Coefficient') && (
                <Line
                  type="monotone"
                  dataKey="Gini Coefficient"
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              )}
              {visibleLines.includes('Workload Variance') && (
                <Line
                  type="monotone"
                  dataKey="Workload Variance"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              )}
              {visibleLines.includes('PGY Equity Score') && (
                <Line
                  type="monotone"
                  dataKey="PGY Equity Score"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              )}
              {visibleLines.includes('Fairness Score') && (
                <Line
                  type="monotone"
                  dataKey="Fairness Score"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Info Note */}
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg" role="note" aria-label="Chart interpretation guide">
          <div className="flex gap-2">
            <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <p className="text-xs text-blue-900">
              Lower Gini coefficient and workload variance indicate better fairness.
              Higher PGY equity and fairness scores are better.
            </p>
          </div>
        </div>
      </div>

      {/* PGY Equity Comparison */}
      {showPgyComparison && <PgyEquityChart />}
    </div>
  );
}
