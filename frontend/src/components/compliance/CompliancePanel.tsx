/**
 * CompliancePanel Component
 *
 * Main ACGME compliance dashboard showing work hours, days off, and violations
 */

import React from 'react';
import { WorkHourGauge } from './WorkHourGauge';
import { DayOffIndicator } from './DayOffIndicator';
import { SupervisionRatio } from './SupervisionRatio';
import { ViolationAlert } from './ViolationAlert';
import { Badge } from '../ui/Badge';

export interface ComplianceData {
  personId: string;
  personName: string;
  pgyLevel: string;
  currentWeekHours: number;
  rolling4WeekAverage: number;
  consecutiveDaysWorked: number;
  lastDayOff: string;
  supervisionRatio: {
    current: number;
    required: number;
  };
  violations: Array<{
    id: string;
    type: string;
    severity: 'critical' | 'warning';
    message: string;
    date: string;
  }>;
}

export interface CompliancePanelProps {
  data: ComplianceData;
  dateRange: {
    start: string;
    end: string;
  };
  onViewDetails?: () => void;
  className?: string;
}

export const CompliancePanel: React.FC<CompliancePanelProps> = ({
  data,
  dateRange,
  onViewDetails,
  className = '',
}) => {
  const hasViolations = data.violations.length > 0;
  const criticalViolations = data.violations.filter(v => v.severity === 'critical');
  const warningViolations = data.violations.filter(v => v.severity === 'warning');

  const getComplianceStatus = (): 'compliant' | 'warning' | 'violation' => {
    if (criticalViolations.length > 0) return 'violation';
    if (warningViolations.length > 0) return 'warning';
    return 'compliant';
  };

  const status = getComplianceStatus();

  const statusConfig = {
    compliant: {
      color: 'bg-green-100 border-green-500 text-green-900',
      badge: 'bg-green-500 text-white',
      icon: '✅',
      label: 'Compliant',
    },
    warning: {
      color: 'bg-yellow-100 border-yellow-500 text-yellow-900',
      badge: 'bg-yellow-500 text-white',
      icon: '⚠️',
      label: 'Warning',
    },
    violation: {
      color: 'bg-red-100 border-red-500 text-red-900',
      badge: 'bg-red-500 text-white',
      icon: '🚨',
      label: 'Violation',
    },
  };

  const config = statusConfig[status];

  return (
    <div
      className={`compliance-panel bg-white rounded-lg shadow-lg border-l-4 ${config.color} ${className}`}
      role="region"
      aria-label="ACGME Compliance Dashboard"
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <span className="text-2xl" role="img" aria-label={config.label}>
              {config.icon}
            </span>
            <div>
              <h2 className="text-xl font-bold">{data.personName}</h2>
              <p className="text-sm text-gray-600">{data.pgyLevel}</p>
            </div>
          </div>
          <Badge className={config.badge}>{config.label}</Badge>
        </div>

        <div className="text-sm text-gray-600">
          Compliance Period: {new Date(dateRange.start).toLocaleDateString()} -{' '}
          {new Date(dateRange.end).toLocaleDateString()}
        </div>
      </div>

      {/* Violations Summary (if any) */}
      {hasViolations && (
        <div className="p-4 bg-red-50 border-b border-red-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-red-900">Active Violations</h3>
            <div className="flex gap-2">
              {criticalViolations.length > 0 && (
                <Badge variant="destructive">
                  {criticalViolations.length} Critical
                </Badge>
              )}
              {warningViolations.length > 0 && (
                <Badge variant="warning">
                  {warningViolations.length} Warnings
                </Badge>
              )}
            </div>
          </div>

          <div className="space-y-2">
            {data.violations.slice(0, 3).map(violation => (
              <ViolationAlert
                key={violation.id}
                violation={violation}
                compact
              />
            ))}
          </div>

          {data.violations.length > 3 && (
            <button
              onClick={onViewDetails}
              className="mt-2 text-sm text-red-700 hover:text-red-900 font-medium focus:outline-none focus:underline"
            >
              View all {data.violations.length} violations →
            </button>
          )}
        </div>
      )}

      {/* Compliance Metrics */}
      <div className="p-4 space-y-4">
        {/* Work Hours */}
        <div>
          <h3 className="font-semibold mb-3">Work Hour Compliance</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <WorkHourGauge
              label="Current Week"
              hours={data.currentWeekHours}
              maxHours={80}
              showThreshold
            />
            <WorkHourGauge
              label="4-Week Rolling Avg"
              hours={data.rolling4WeekAverage}
              maxHours={80}
              showThreshold
            />
          </div>
        </div>

        {/* Days Off */}
        <div>
          <h3 className="font-semibold mb-3">1-in-7 Days Off</h3>
          <DayOffIndicator
            consecutiveDaysWorked={data.consecutiveDaysWorked}
            lastDayOff={data.lastDayOff}
          />
        </div>

        {/* Supervision Ratio */}
        <div>
          <h3 className="font-semibold mb-3">Supervision Ratio</h3>
          <SupervisionRatio
            current={data.supervisionRatio.current}
            required={data.supervisionRatio.required}
            pgyLevel={data.pgyLevel}
          />
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="text-xs text-gray-600">
            Last updated: {new Date().toLocaleString()}
          </div>
          {onViewDetails && (
            <button
              onClick={onViewDetails}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            >
              View Full Report
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default CompliancePanel;
