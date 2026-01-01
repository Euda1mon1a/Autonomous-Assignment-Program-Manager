/**
 * ViolationAlert Component
 *
 * Displays ACGME compliance violations with severity levels
 */

import React from 'react';
import { Badge } from '../ui/Badge';

export interface Violation {
  id: string;
  type: string;
  severity: 'critical' | 'warning';
  message: string;
  date: string;
  details?: {
    actual: number;
    limit: number;
    unit: string;
  };
  suggestions?: string[];
}

export interface ViolationAlertProps {
  violation: Violation;
  compact?: boolean;
  onDismiss?: (id: string) => void;
  onResolve?: (id: string) => void;
  className?: string;
}

const severityConfig = {
  critical: {
    color: 'bg-red-50 border-red-500 text-red-900',
    badgeVariant: 'destructive' as const,
    icon: '🚨',
    label: 'Critical',
  },
  warning: {
    color: 'bg-yellow-50 border-yellow-500 text-yellow-900',
    badgeVariant: 'warning' as const,
    icon: '⚠️',
    label: 'Warning',
  },
};

const typeLabels: Record<string, string> = {
  work_hours: '80-Hour Violation',
  days_off: '1-in-7 Violation',
  supervision: 'Supervision Ratio Violation',
  continuous_duty: 'Continuous Duty Violation',
  rest_period: 'Rest Period Violation',
};

export const ViolationAlert: React.FC<ViolationAlertProps> = ({
  violation,
  compact = false,
  onDismiss,
  onResolve,
  className = '',
}) => {
  const config = severityConfig[violation.severity];
  const typeLabel = typeLabels[violation.type] || violation.type;

  if (compact) {
    return (
      <div
        className={`violation-alert-compact border-l-4 rounded p-2 ${config.color} ${className}`}
        role="alert"
        aria-label={`${config.label}: ${violation.message}`}
      >
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span aria-hidden="true">{config.icon}</span>
            <span className="text-sm font-medium truncate">{violation.message}</span>
          </div>
          <Badge variant={config.badgeVariant} className="text-xs">
            {config.label}
          </Badge>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`violation-alert border-l-4 rounded-lg p-4 shadow-sm ${config.color} ${className}`}
      role="alert"
      aria-live="assertive"
      aria-label={`${config.label}: ${typeLabel}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl" aria-hidden="true">
            {config.icon}
          </span>
          <div>
            <h4 className="font-bold text-lg">{typeLabel}</h4>
            <Badge variant={config.badgeVariant} className="mt-1">
              {config.label}
            </Badge>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2" role="group" aria-label="Violation actions">
          {onResolve && (
            <button
              onClick={() => onResolve(violation.id)}
              className="px-3 py-1 bg-white border border-gray-300 rounded hover:bg-gray-50 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label={`Resolve ${typeLabel}`}
            >
              Resolve
            </button>
          )}
          {onDismiss && (
            <button
              onClick={() => onDismiss(violation.id)}
              className="p-1 hover:bg-white hover:bg-opacity-50 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label={`Dismiss ${typeLabel} alert`}
            >
              <span aria-hidden="true">✕</span>
            </button>
          )}
        </div>
      </div>

      {/* Message */}
      <p className="text-sm mb-3 font-medium">{violation.message}</p>

      {/* Details */}
      {violation.details && (
        <div className="bg-white bg-opacity-50 rounded p-3 mb-3">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Actual:</span>
              <span className="ml-2 font-semibold">
                {violation.details.actual} {violation.details.unit}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Limit:</span>
              <span className="ml-2 font-semibold">
                {violation.details.limit} {violation.details.unit}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Date */}
      <div className="text-xs text-gray-600 mb-3">
        Occurred on: {new Date(violation.date).toLocaleDateString('en-US', {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        })}
      </div>

      {/* Suggestions */}
      {violation.suggestions && violation.suggestions.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded p-3" role="region" aria-label="Suggested actions">
          <h5 className="text-sm font-semibold text-blue-900 mb-2">
            <span aria-hidden="true">💡</span> Suggested Actions:
          </h5>
          <ul className="list-disc list-inside text-sm text-blue-800 space-y-1">
            {violation.suggestions.map((suggestion, idx) => (
              <li key={idx}>{suggestion}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ViolationAlert;
