'use client';

/**
 * MetricsCard Component
 *
 * Reusable card component for displaying a metric with status indicator,
 * trend arrow, and threshold visualization.
 */

import { TrendingUp, TrendingDown, Minus, AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react';
import type { Metric, MetricStatus, TrendDirection } from './types';
import { METRIC_STATUS_COLORS } from './types';

// ============================================================================
// Types
// ============================================================================

interface MetricsCardProps {
  metric: Metric;
  onClick?: () => void;
  className?: string;
  compact?: boolean;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get status icon based on metric status
 */
function getStatusIcon(status: MetricStatus): React.ReactNode {
  const className = 'w-5 h-5';

  switch (status) {
    case 'excellent':
      return <CheckCircle className={`${className} text-green-600`} />;
    case 'good':
      return <CheckCircle className={`${className} text-blue-600`} />;
    case 'warning':
      return <AlertTriangle className={`${className} text-yellow-600`} />;
    case 'critical':
      return <AlertCircle className={`${className} text-red-600`} />;
  }
}

/**
 * Get trend icon based on direction
 */
function getTrendIcon(direction: TrendDirection, trendValue: number): React.ReactNode {
  const className = 'w-4 h-4';

  switch (direction) {
    case 'up':
      return <TrendingUp className={`${className} text-green-600`} />;
    case 'down':
      return <TrendingDown className={`${className} text-red-600`} />;
    case 'stable':
      return <Minus className={`${className} text-gray-600`} />;
  }
}

/**
 * Get background color classes based on status
 */
function getStatusBgColor(status: MetricStatus): string {
  const color = METRIC_STATUS_COLORS[status];

  switch (color) {
    case 'green':
      return 'bg-green-50 border-green-200';
    case 'blue':
      return 'bg-blue-50 border-blue-200';
    case 'yellow':
      return 'bg-yellow-50 border-yellow-200';
    case 'red':
      return 'bg-red-50 border-red-200';
    default:
      return 'bg-gray-50 border-gray-200';
  }
}

/**
 * Format metric value with proper precision
 */
function formatValue(value: number, unit: string): string {
  if (unit === '%') {
    return `${value.toFixed(1)}%`;
  }
  if (unit === 'score') {
    return value.toFixed(2);
  }
  return value.toFixed(0);
}

// ============================================================================
// Component
// ============================================================================

export function MetricsCard({ metric, onClick, className = '', compact = false }: MetricsCardProps) {
  const bgColor = getStatusBgColor(metric.status);
  const isClickable = !!onClick;

  if (compact) {
    return (
      <button
        type="button"
        onClick={onClick}
        disabled={!isClickable}
        className={`
          w-full text-left p-3 rounded-lg border-2 transition-all
          ${bgColor}
          ${isClickable ? 'hover:shadow-md cursor-pointer' : 'cursor-default'}
          ${className}
        `}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-700 truncate">{metric.name}</p>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold text-gray-900">
                {formatValue(metric.value, metric.unit)}
              </span>
              <span className="text-sm text-gray-600">{metric.unit !== '%' && metric.unit !== 'score' && metric.unit}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 ml-2">
            <div className="flex items-center gap-1">
              {getTrendIcon(metric.trend, metric.trendValue)}
              <span className={`text-xs font-medium ${
                metric.trend === 'up' ? 'text-green-600' :
                metric.trend === 'down' ? 'text-red-600' :
                'text-gray-600'
              }`}>
                {Math.abs(metric.trendValue).toFixed(1)}%
              </span>
            </div>
            {getStatusIcon(metric.status)}
          </div>
        </div>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!isClickable}
      className={`
        w-full text-left p-6 rounded-xl border-2 transition-all
        ${bgColor}
        ${isClickable ? 'hover:shadow-lg cursor-pointer' : 'cursor-default'}
        ${className}
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-gray-700 mb-1">{metric.name}</h3>
          <p className="text-xs text-gray-500 line-clamp-2">{metric.description}</p>
        </div>
        <div className="ml-3">
          {getStatusIcon(metric.status)}
        </div>
      </div>

      {/* Value */}
      <div className="flex items-baseline gap-2 mb-3">
        <span className="text-4xl font-bold text-gray-900">
          {formatValue(metric.value, metric.unit)}
        </span>
        {metric.unit !== '%' && metric.unit !== 'score' && (
          <span className="text-lg text-gray-600">{metric.unit}</span>
        )}
      </div>

      {/* Trend */}
      <div className="flex items-center gap-2">
        {getTrendIcon(metric.trend, metric.trendValue)}
        <span className={`text-sm font-medium ${
          metric.trend === 'up' ? 'text-green-600' :
          metric.trend === 'down' ? 'text-red-600' :
          'text-gray-600'
        }`}>
          {metric.trend === 'up' && '+'}
          {metric.trend === 'down' && '-'}
          {Math.abs(metric.trendValue).toFixed(1)}% from last period
        </span>
      </div>

      {/* Threshold indicator (if available) */}
      {metric.threshold && (
        <div className="mt-4 pt-4 border-t border-gray-300">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <span>Threshold</span>
            <div className="flex gap-3">
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-yellow-500" />
                {metric.threshold.warning}
              </span>
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-red-500" />
                {metric.threshold.critical}
              </span>
            </div>
          </div>
          {/* Progress bar */}
          <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${
                metric.status === 'excellent' ? 'bg-green-500' :
                metric.status === 'good' ? 'bg-blue-500' :
                metric.status === 'warning' ? 'bg-yellow-500' :
                'bg-red-500'
              }`}
              style={{
                width: `${Math.min(100, (metric.value / (metric.threshold.critical || 100)) * 100)}%`,
              }}
            />
          </div>
        </div>
      )}
    </button>
  );
}

/**
 * MetricsCardSkeleton - Loading skeleton
 */
export function MetricsCardSkeleton({ compact = false }: { compact?: boolean }) {
  if (compact) {
    return (
      <div className="w-full p-3 rounded-lg border-2 border-gray-200 bg-gray-50 animate-pulse">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="h-4 bg-gray-300 rounded w-24 mb-2" />
            <div className="h-8 bg-gray-300 rounded w-20" />
          </div>
          <div className="flex items-center gap-2 ml-2">
            <div className="h-4 w-12 bg-gray-300 rounded" />
            <div className="h-5 w-5 bg-gray-300 rounded-full" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full p-6 rounded-xl border-2 border-gray-200 bg-gray-50 animate-pulse">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="h-4 bg-gray-300 rounded w-32 mb-2" />
          <div className="h-3 bg-gray-300 rounded w-48" />
        </div>
        <div className="h-5 w-5 bg-gray-300 rounded-full" />
      </div>
      <div className="h-10 bg-gray-300 rounded w-28 mb-3" />
      <div className="h-4 bg-gray-300 rounded w-40" />
    </div>
  );
}
