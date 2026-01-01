/**
 * EarlyWarningPanel Component
 *
 * Early warning system using SPC monitoring with Western Electric rules
 */

import React, { useState } from 'react';
import { Badge } from '../ui/Badge';

export interface EarlyWarning {
  id: string;
  type: 'utilization' | 'burnout' | 'coverage' | 'compliance';
  severity: 'critical' | 'warning' | 'info';
  message: string;
  detectedAt: string;
  rule?: string; // Which detection rule triggered
  trend?: Array<{ date: string; value: number }>;
}

export interface EarlyWarningPanelProps {
  warnings: EarlyWarning[];
  onDismiss?: (id: string) => void;
  onDrillDown?: () => void;
  className?: string;
}

const severityConfig = {
  critical: {
    color: 'bg-red-50 border-red-500',
    badgeVariant: 'destructive' as const,
    icon: '🚨',
    label: 'Critical',
  },
  warning: {
    color: 'bg-yellow-50 border-yellow-500',
    badgeVariant: 'warning' as const,
    icon: '⚠️',
    label: 'Warning',
  },
  info: {
    color: 'bg-blue-50 border-blue-500',
    badgeVariant: 'default' as const,
    icon: 'ℹ️',
    label: 'Info',
  },
};

const typeIcons = {
  utilization: '📊',
  burnout: '😰',
  coverage: '📅',
  compliance: '⚖️',
};

const typeLabels = {
  utilization: 'Utilization',
  burnout: 'Burnout',
  coverage: 'Coverage',
  compliance: 'Compliance',
};

export const EarlyWarningPanel: React.FC<EarlyWarningPanelProps> = ({
  warnings,
  onDismiss,
  onDrillDown,
  className = '',
}) => {
  const [expandedWarningId, setExpandedWarningId] = useState<string | null>(null);

  const criticalWarnings = warnings.filter(w => w.severity === 'critical');
  const warningCount = warnings.filter(w => w.severity === 'warning').length;

  // Group warnings by type
  const groupedWarnings = warnings.reduce((acc, warning) => {
    if (!acc[warning.type]) {
      acc[warning.type] = [];
    }
    acc[warning.type].push(warning);
    return acc;
  }, {} as Record<string, EarlyWarning[]>);

  if (warnings.length === 0) {
    return (
      <div
        className={`early-warning-panel bg-green-50 rounded-lg p-6 text-center ${className}`}
        role="status"
        aria-live="polite"
      >
        <div className="text-4xl mb-3" aria-hidden="true">✅</div>
        <h3 className="text-lg font-semibold text-green-900 mb-2">All Clear</h3>
        <p className="text-sm text-green-700">
          No early warning indicators detected. System operating normally.
        </p>
      </div>
    );
  }

  return (
    <div className={`early-warning-panel ${className}`}>
      {/* Summary */}
      <div
        className="bg-white rounded-lg border border-gray-200 p-4 mb-4"
        role="status"
        aria-live="polite"
        aria-label="Early warning summary"
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold">Active Warnings</h3>
          <div className="flex gap-2">
            {criticalWarnings.length > 0 && (
              <Badge variant="destructive">{criticalWarnings.length} Critical</Badge>
            )}
            {warningCount > 0 && (
              <Badge variant="warning">{warningCount} Warnings</Badge>
            )}
          </div>
        </div>

        {/* Type Breakdown */}
        <div className="grid grid-cols-4 gap-2">
          {Object.entries(groupedWarnings).map(([type, typeWarnings]) => (
            <div key={type} className="bg-gray-50 rounded p-2 text-center">
              <div className="text-xl mb-1" aria-hidden="true">{typeIcons[type as keyof typeof typeIcons]}</div>
              <div className="text-xs font-medium text-gray-700">
                {typeLabels[type as keyof typeof typeLabels]}
              </div>
              <div className="text-lg font-bold text-gray-900">{typeWarnings.length}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Warning List */}
      <div className="space-y-3">
        {warnings
          .sort((a, b) => {
            // Sort by severity (critical > warning > info), then by date
            const severityOrder = { critical: 0, warning: 1, info: 2 };
            const severityDiff = severityOrder[a.severity] - severityOrder[b.severity];
            if (severityDiff !== 0) return severityDiff;
            return new Date(b.detectedAt).getTime() - new Date(a.detectedAt).getTime();
          })
          .map((warning) => {
            const config = severityConfig[warning.severity];
            const isExpanded = expandedWarningId === warning.id;

            return (
              <div
                key={warning.id}
                className={`border-l-4 rounded-lg bg-white shadow-sm ${config.color}`}
              >
                <div className="p-4">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-3 flex-1">
                      <span className="text-2xl" aria-hidden="true">
                        {config.icon}
                      </span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant={config.badgeVariant}>{config.label}</Badge>
                          <span className="text-xs text-gray-600">
                            <span aria-hidden="true">{typeIcons[warning.type]} </span>
                            {typeLabels[warning.type]}
                          </span>
                        </div>
                        <p className="text-sm font-medium">{warning.message}</p>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                      {warning.trend && (
                        <button
                          onClick={() => setExpandedWarningId(isExpanded ? null : warning.id)}
                          className="text-sm text-blue-600 hover:text-blue-800 focus:outline-none focus:underline"
                          aria-label={`${isExpanded ? 'Hide' : 'View'} trend chart for ${warning.message}`}
                          aria-expanded={isExpanded}
                        >
                          {isExpanded ? 'Hide' : 'View'} Trend
                        </button>
                      )}
                      {onDismiss && (
                        <button
                          onClick={() => onDismiss(warning.id)}
                          className="text-sm text-gray-500 hover:text-gray-700 focus:outline-none"
                          aria-label={`Dismiss warning: ${warning.message}`}
                        >
                          <span aria-hidden="true">✕</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="flex items-center gap-4 text-xs text-gray-600">
                    <span>
                      Detected: {new Date(warning.detectedAt).toLocaleString()}
                    </span>
                    {warning.rule && (
                      <span className="px-2 py-0.5 bg-gray-100 rounded">
                        Rule: {warning.rule}
                      </span>
                    )}
                  </div>

                  {/* Trend Chart (if expanded) */}
                  {isExpanded && warning.trend && (
                    <div
                      className="mt-4 p-3 bg-gray-50 rounded border border-gray-200"
                      role="img"
                      aria-label={`Trend chart showing ${warning.trend.length} data points`}
                    >
                      <h4 className="text-sm font-semibold mb-2">Trend Data</h4>
                      <div className="flex items-end justify-around h-24 gap-1">
                        {warning.trend.map((point, idx) => {
                          const maxValue = Math.max(...warning.trend!.map(p => p.value));
                          const height = (point.value / maxValue) * 100;

                          return (
                            <div key={idx} className="flex-1 flex flex-col items-center">
                              <div
                                className={`w-full rounded-t transition-all ${
                                  idx === warning.trend!.length - 1
                                    ? 'bg-red-500'
                                    : 'bg-blue-400'
                                }`}
                                style={{ height: `${height}%` }}
                                title={`${point.date}: ${point.value}`}
                                aria-hidden="true"
                              />
                              <div className="text-xs text-gray-500 mt-1">
                                {new Date(point.date).toLocaleDateString('en-US', {
                                  month: 'short',
                                  day: 'numeric',
                                })}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
      </div>

      {/* Drill Down Button */}
      {onDrillDown && (
        <button
          onClick={onDrillDown}
          className="w-full mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          aria-label="View full early warning analysis with detailed metrics"
        >
          View Full Early Warning Analysis
        </button>
      )}

      {/* Framework Info */}
      <div className="mt-4 text-xs text-gray-600 bg-blue-50 rounded p-3">
        <strong>SPC Early Warning System:</strong> Uses Statistical Process Control (SPC) monitoring
        with Western Electric rules from semiconductor manufacturing. Detects abnormal patterns including:
        single points outside control limits, runs, trends, and cycles. Provides advance warning before
        hard threshold violations occur.
      </div>
    </div>
  );
};

export default EarlyWarningPanel;
