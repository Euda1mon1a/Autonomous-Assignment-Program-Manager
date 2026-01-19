/**
 * Health Status Indicator Component
 *
 * Displays current system health status with color-coded indicators:
 * - GREEN: Healthy
 * - YELLOW: Warning
 * - ORANGE: Degraded
 * - RED: Critical
 * - BLACK: Emergency
 *
 * Integrates with useSystemHealth hook to fetch real-time resilience metrics.
 */

'use client';

import React from 'react';
import { useSystemHealth } from '@/hooks/useResilience';
import { OverallStatus } from '@/types/resilience';

export type HealthStatus = 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED' | 'BLACK';

export interface HealthStatusIndicatorProps {
  /** Override status (if not provided, fetches from API) */
  status?: HealthStatus;
  /** Show detailed metrics (N-1/N-2 status, utilization) */
  showDetails?: boolean;
  /** Show loading spinner during fetch */
  showLoading?: boolean;
  /** Custom CSS classes */
  className?: string;
  /** Compact mode - just the indicator dot */
  compact?: boolean;
}

/** Maps OverallStatus from API to display HealthStatus */
const mapOverallStatusToHealthStatus = (overall: OverallStatus): HealthStatus => {
  switch (overall) {
    case OverallStatus.HEALTHY:
      return 'GREEN';
    case OverallStatus.WARNING:
      return 'YELLOW';
    case OverallStatus.DEGRADED:
      return 'ORANGE';
    case OverallStatus.CRITICAL:
      return 'RED';
    case OverallStatus.EMERGENCY:
      return 'BLACK';
    default:
      return 'GREEN';
  }
};

// Status config uses uppercase keys to match HealthStatus type for type-safe indexing
/* eslint-disable @typescript-eslint/naming-convention */
const statusConfig: Record<HealthStatus, {
  color: string;
  bgColor: string;
  borderColor: string;
  textColor: string;
  label: string;
  description: string;
}> = {
  GREEN: {
    color: 'bg-green-500',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-700',
    label: 'Healthy',
    description: 'All systems operational',
  },
  YELLOW: {
    color: 'bg-yellow-500',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    textColor: 'text-yellow-700',
    label: 'Warning',
    description: 'Elevated monitoring recommended',
  },
  ORANGE: {
    color: 'bg-orange-500',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    textColor: 'text-orange-700',
    label: 'Degraded',
    description: 'Proactive intervention required',
  },
  RED: {
    color: 'bg-red-500',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-700',
    label: 'Critical',
    description: 'Immediate action required',
  },
  BLACK: {
    color: 'bg-gray-900',
    bgColor: 'bg-gray-100',
    borderColor: 'border-gray-400',
    textColor: 'text-gray-900',
    label: 'Emergency',
    description: 'Crisis management mode',
  },
};
/* eslint-enable @typescript-eslint/naming-convention */

/**
 * Health Status Indicator Component
 *
 * Displays system health with color-coded status. Can either:
 * 1. Accept a status prop directly (controlled mode)
 * 2. Fetch status from the resilience API (automatic mode)
 *
 * @example
 * ```tsx
 * // Automatic mode - fetches from API
 * <HealthStatusIndicator showDetails />
 *
 * // Controlled mode - status provided
 * <HealthStatusIndicator status="GREEN" compact />
 * ```
 */
export const HealthStatusIndicator: React.FC<HealthStatusIndicatorProps> = ({
  status: statusOverride,
  showDetails = false,
  showLoading = true,
  className = '',
  compact = false,
}) => {
  // Only fetch if no status override provided
  const { data, isLoading, isError, error } = useSystemHealth({
    enabled: !statusOverride,
  });

  // Determine the status to display
  const status: HealthStatus = statusOverride
    ?? (data ? mapOverallStatusToHealthStatus(data.overallStatus) : 'GREEN');

  const config = statusConfig[status];

  // Loading state
  if (!statusOverride && isLoading && showLoading) {
    return (
      <div
        className={`flex items-center gap-2 ${className}`}
        role="status"
        aria-label="Loading health status"
      >
        <span className="inline-block w-3 h-3 rounded-full bg-gray-300 animate-pulse" />
        {!compact && <span className="text-sm text-gray-500">Loading...</span>}
      </div>
    );
  }

  // Error state
  if (!statusOverride && isError) {
    return (
      <div
        className={`flex items-center gap-2 ${className}`}
        role="alert"
        aria-label="Health status unavailable"
      >
        <span className="inline-block w-3 h-3 rounded-full bg-gray-400" />
        {!compact && (
          <span className="text-sm text-gray-500" title={error?.message}>
            Unavailable
          </span>
        )}
      </div>
    );
  }

  // Compact mode - just the indicator dot
  if (compact) {
    return (
      <div
        className={`flex items-center gap-2 ${className}`}
        role="status"
        aria-label={`System health: ${config.label}`}
      >
        <span
          className={`inline-block w-3 h-3 rounded-full ${config.color}`}
          title={`${config.label}: ${config.description}`}
        />
        <span className={`text-sm font-medium ${config.textColor}`}>
          {status}
        </span>
      </div>
    );
  }

  // Full mode with optional details
  return (
    <div
      className={`rounded-lg border p-3 ${config.bgColor} ${config.borderColor} ${className}`}
      role="status"
      aria-label={`System health: ${config.label}`}
    >
      <div className="flex items-center gap-3">
        <span
          className={`inline-block w-4 h-4 rounded-full ${config.color} ring-2 ring-offset-1 ring-offset-white ${config.color.replace('bg-', 'ring-')}`}
          aria-hidden="true"
        />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={`font-semibold ${config.textColor}`}>
              {config.label}
            </span>
            <span className="text-xs text-gray-500">({status})</span>
          </div>
          <p className="text-sm text-gray-600">{config.description}</p>
        </div>
      </div>

      {/* Detailed metrics */}
      {showDetails && data && (
        <div className="mt-3 pt-3 border-t border-gray-200 grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-1">
            <span className={`w-2 h-2 rounded-full ${data.n1Pass ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-gray-600">N-1: {data.n1Pass ? 'Pass' : 'Fail'}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className={`w-2 h-2 rounded-full ${data.n2Pass ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-gray-600">N-2: {data.n2Pass ? 'Pass' : 'Fail'}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-gray-600">
              Utilization: {(data.utilization.utilizationRate * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-gray-600">
              Defense: {data.defenseLevel}
            </span>
          </div>
          {data.crisisMode && (
            <div className="col-span-2 flex items-center gap-1 text-red-600 font-medium">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              CRISIS MODE ACTIVE
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default HealthStatusIndicator;
