'use client';

import React from 'react';
import { CheckCircle, AlertTriangle, XCircle, Clock } from 'lucide-react';
import { Tooltip } from '../ui/Tooltip';

export type ComplianceStatus = 'compliant' | 'warning' | 'violation' | 'pending';

export interface ComplianceIndicatorProps {
  status: ComplianceStatus;
  rule?: string;
  message?: string;
  details?: string;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const statusConfig = {
  compliant: {
    icon: CheckCircle,
    color: 'text-green-600',
    bg: 'bg-green-100',
    label: 'Compliant',
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-amber-600',
    bg: 'bg-amber-100',
    label: 'Warning',
  },
  violation: {
    icon: XCircle,
    color: 'text-red-600',
    bg: 'bg-red-100',
    label: 'Violation',
  },
  pending: {
    icon: Clock,
    color: 'text-gray-600',
    bg: 'bg-gray-100',
    label: 'Pending',
  },
};

const iconSizes = {
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
};

/**
 * ComplianceIndicator component for ACGME compliance status
 *
 * @example
 * ```tsx
 * <ComplianceIndicator
 *   status="compliant"
 *   rule="80-Hour Rule"
 *   message="65/80 hours this week"
 * />
 *
 * <ComplianceIndicator
 *   status="violation"
 *   rule="1-in-7 Rule"
 *   message="No day off in 8 days"
 *   showLabel
 * />
 * ```
 */
export function ComplianceIndicator({
  status,
  rule,
  message,
  details,
  showLabel = false,
  size = 'md',
  className = '',
}: ComplianceIndicatorProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  const tooltipContent = (
    <div className="text-left">
      {rule && <div className="font-semibold">{rule}</div>}
      {message && <div className="mt-1">{message}</div>}
      {details && <div className="mt-1 text-xs opacity-90">{details}</div>}
    </div>
  );

  const indicator = (
    <div className={`inline-flex items-center gap-1.5 ${className}`}>
      <Icon className={`${iconSizes[size]} ${config.color}`} />
      {showLabel && (
        <span className={`text-sm font-medium ${config.color}`}>
          {config.label}
        </span>
      )}
    </div>
  );

  if (message || rule || details) {
    return (
      <Tooltip content={tooltipContent}>
        {indicator}
      </Tooltip>
    );
  }

  return indicator;
}

/**
 * Compliance status card with detailed information
 */
export function ComplianceCard({
  status,
  rule,
  message,
  details,
  actions,
  className = '',
}: ComplianceIndicatorProps & {
  actions?: React.ReactNode;
}) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div
      className={`rounded-lg border p-4 ${
        status === 'compliant' ? 'border-green-200 bg-green-50' :
        status === 'warning' ? 'border-amber-200 bg-amber-50' :
        status === 'violation' ? 'border-red-200 bg-red-50' :
        'border-gray-200 bg-gray-50'
      } ${className}`}
    >
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg ${config.bg}`}>
          <Icon className={`w-5 h-5 ${config.color}`} />
        </div>

        <div className="flex-1 min-w-0">
          {rule && (
            <h4 className="text-sm font-semibold text-gray-900 mb-1">
              {rule}
            </h4>
          )}
          {message && (
            <p className="text-sm text-gray-700">{message}</p>
          )}
          {details && (
            <p className="text-xs text-gray-600 mt-1">{details}</p>
          )}

          {actions && (
            <div className="mt-3">
              {actions}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Compliance summary component showing multiple rules
 */
export function ComplianceSummary({
  items,
  className = '',
}: {
  items: Array<ComplianceIndicatorProps>;
  className?: string;
}) {
  const violationCount = items.filter((i) => i.status === 'violation').length;
  const warningCount = items.filter((i) => i.status === 'warning').length;

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-900">
          ACGME Compliance
        </h3>
        <div className="flex items-center gap-2">
          {violationCount > 0 && (
            <span className="text-xs font-medium text-red-600">
              {violationCount} violation{violationCount !== 1 ? 's' : ''}
            </span>
          )}
          {warningCount > 0 && (
            <span className="text-xs font-medium text-amber-600">
              {warningCount} warning{warningCount !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>

      <div className="space-y-2">
        {items.map((item, index) => (
          <ComplianceCard key={index} {...item} />
        ))}
      </div>
    </div>
  );
}
