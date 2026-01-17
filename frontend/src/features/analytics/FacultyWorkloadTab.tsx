'use client';

/**
 * FacultyWorkloadTab Component
 *
 * Lighter workload fairness view for the Analytics Dashboard.
 * Shows summary metrics and category distribution without full per-faculty breakdown.
 */

import { useState } from 'react';
import { Scale, TrendingUp, TrendingDown, Minus, Users } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { getFirstOfMonthLocal, getLastOfMonthLocal } from '@/lib/date-utils';
import {
  useFairnessSummary,
  getFairnessStatus,
  getFairnessLabel,
} from '@/hooks/useFairness';

// ============================================================================
// Sub-Components
// ============================================================================

function MetricCard({
  title,
  value,
  subtitle,
  status,
  icon,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  status?: 'excellent' | 'good' | 'warning' | 'critical';
  icon?: React.ReactNode;
}) {
  const statusColors = {
    excellent: 'border-green-500 bg-green-50',
    good: 'border-emerald-500 bg-emerald-50',
    warning: 'border-amber-500 bg-amber-50',
    critical: 'border-red-500 bg-red-50',
  };

  const textColors = {
    excellent: 'text-green-700',
    good: 'text-emerald-700',
    warning: 'text-amber-700',
    critical: 'text-red-700',
  };

  return (
    <div
      className={`p-4 rounded-lg border-2 ${
        status ? statusColors[status] : 'border-gray-200 bg-white'
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p
            className={`text-2xl font-bold ${
              status ? textColors[status] : 'text-gray-900'
            }`}
          >
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        {icon && (
          <div className={`${status ? textColors[status] : 'text-gray-400'}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

function _TrendIndicator({ value }: { value: number }) {
  if (value > 0) {
    return (
      <div className="flex items-center gap-1 text-red-600">
        <TrendingUp className="w-4 h-4" />
        <span className="text-sm">+{value}</span>
      </div>
    );
  }
  if (value < 0) {
    return (
      <div className="flex items-center gap-1 text-green-600">
        <TrendingDown className="w-4 h-4" />
        <span className="text-sm">{value}</span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-1 text-gray-500">
      <Minus className="w-4 h-4" />
      <span className="text-sm">No change</span>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function FacultyWorkloadTab() {
  // Default to current month (using local timezone)
  const [startDate] = useState<string>(getFirstOfMonthLocal);
  const [endDate] = useState<string>(getLastOfMonthLocal);

  const { data, isLoading, error } = useFairnessSummary(startDate, endDate);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-48 mb-4" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-sm text-red-600">
          Failed to load workload data: {error.message}
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Scale className="w-12 h-12 mx-auto mb-3 text-gray-400" />
        <p>No workload data available for this period</p>
      </div>
    );
  }

  const status = getFairnessStatus(data.fairnessIndex);
  const label = getFairnessLabel(data.fairnessIndex);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Scale className="w-5 h-5" />
            Faculty Workload Fairness
          </h2>
          <p className="text-sm text-gray-600">
            {data.period.start} to {data.period.end}
          </p>
        </div>
        <Badge
          variant={
            status === 'excellent'
              ? 'success'
              : status === 'good'
              ? 'primary'
              : status === 'warning'
              ? 'warning'
              : 'danger'
          }
        >
          {label}
        </Badge>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Fairness Index"
          value={`${(data.fairnessIndex * 100).toFixed(1)}%`}
          subtitle="Jain's fairness (0-100%)"
          status={status}
          icon={<Scale className="w-5 h-5" />}
        />
        <MetricCard
          title="Faculty Count"
          value={data.facultyCount}
          subtitle="Active faculty in period"
          icon={<Users className="w-5 h-5" />}
        />
        <MetricCard
          title="Workload Spread"
          value={data.workloadSpread.toFixed(1)}
          subtitle="Max - Min score"
          status={data.workloadSpread > 10 ? 'warning' : 'good'}
        />
        <MetricCard
          title="Outliers"
          value={data.outlierCount.high + data.outlierCount.low}
          subtitle={`${data.outlierCount.high} high, ${data.outlierCount.low} low`}
          status={
            data.outlierCount.high + data.outlierCount.low > 2
              ? 'warning'
              : 'excellent'
          }
        />
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-800 mb-2">
          About Workload Scoring
        </h3>
        <p className="text-sm text-blue-700">
          Workload scores combine 5 categories with weighted values: Call
          (1.0), FMIT weeks (3.0), Clinic half-days (0.5), Admin (0.25), and
          Academic (0.25). Higher fairness index means more equitable
          distribution.
        </p>
        <p className="text-sm text-blue-600 mt-2">
          For detailed per-faculty breakdown, visit{' '}
          <a href="/admin/fairness" className="underline font-medium">
            Admin &rarr; Fairness Audit
          </a>
        </p>
      </div>
    </div>
  );
}

export default FacultyWorkloadTab;
