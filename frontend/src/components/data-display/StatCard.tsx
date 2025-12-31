'use client';

import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface StatCardProps {
  label: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  variant?: 'default' | 'success' | 'warning' | 'danger';
  loading?: boolean;
  className?: string;
}

const variantStyles = {
  default: 'bg-white border-gray-200',
  success: 'bg-green-50 border-green-200',
  warning: 'bg-amber-50 border-amber-200',
  danger: 'bg-red-50 border-red-200',
};

/**
 * StatCard component for displaying key metrics
 *
 * @example
 * ```tsx
 * <StatCard
 *   label="Total Residents"
 *   value={24}
 *   change={12}
 *   changeLabel="vs last month"
 *   trend="up"
 *   icon={<UserIcon />}
 * />
 * ```
 */
export function StatCard({
  label,
  value,
  change,
  changeLabel,
  icon,
  trend,
  variant = 'default',
  loading = false,
  className = '',
}: StatCardProps) {
  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4" />;
    return <Minus className="w-4 h-4" />;
  };

  const getTrendColor = () => {
    if (trend === 'up') return 'text-green-600';
    if (trend === 'down') return 'text-red-600';
    return 'text-gray-600';
  };

  if (loading) {
    return (
      <div className={`rounded-lg border p-6 ${variantStyles[variant]} ${className}`}>
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          <div className="h-3 bg-gray-200 rounded w-1/3"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-lg border p-6 ${variantStyles[variant]} ${className}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{label}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>

          {(change !== undefined || changeLabel) && (
            <div className={`mt-2 flex items-center gap-1 text-sm ${getTrendColor()}`}>
              {trend && getTrendIcon()}
              <span>
                {change !== undefined && (
                  <span className="font-medium">
                    {change > 0 ? '+' : ''}
                    {change}%
                  </span>
                )}
                {changeLabel && <span className="ml-1 text-gray-600">{changeLabel}</span>}
              </span>
            </div>
          )}
        </div>

        {icon && (
          <div className="p-3 bg-gray-100 rounded-lg">
            <div className="w-6 h-6 text-gray-600">{icon}</div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Compact stat display
 */
export function CompactStat({
  label,
  value,
  className = '',
}: Pick<StatCardProps, 'label' | 'value' | 'className'>) {
  return (
    <div className={className}>
      <dt className="text-sm font-medium text-gray-600">{label}</dt>
      <dd className="mt-1 text-2xl font-semibold text-gray-900">{value}</dd>
    </div>
  );
}

/**
 * Stat grid layout
 */
export function StatGrid({
  stats,
  columns = 3,
  className = '',
}: {
  stats: StatCardProps[];
  columns?: 2 | 3 | 4;
  className?: string;
}) {
  const gridCols = {
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  };

  return (
    <div className={`grid gap-6 ${gridCols[columns]} ${className}`}>
      {stats.map((stat, index) => (
        <StatCard key={index} {...stat} />
      ))}
    </div>
  );
}
