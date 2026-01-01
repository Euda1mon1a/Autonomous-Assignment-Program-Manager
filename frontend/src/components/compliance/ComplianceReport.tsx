/**
 * ComplianceReport Component
 *
 * Comprehensive, exportable ACGME compliance report
 */

import React, { useRef } from 'react';
import { Badge } from '../ui/Badge';

export interface ComplianceReportData {
  personName: string;
  pgyLevel: string;
  reportPeriod: {
    start: string;
    end: string;
  };
  workHours: {
    weeklyHours: number[];
    rollingAverage: number;
    maxWeekHours: number;
    violations: number;
  };
  daysOff: {
    totalDaysOff: number;
    longestStretch: number;
    violations: number;
  };
  supervision: {
    averageRatio: number;
    requiredRatio: number;
    violations: number;
  };
  overallCompliance: {
    status: 'compliant' | 'warning' | 'violation';
    score: number; // 0-100
  };
  violations: Array<{
    date: string;
    type: string;
    severity: 'critical' | 'warning';
    message: string;
  }>;
}

export interface ComplianceReportProps {
  data: ComplianceReportData;
  onExport?: (format: 'pdf' | 'excel') => void;
  className?: string;
}

export const ComplianceReport: React.FC<ComplianceReportProps> = ({
  data,
  onExport,
  className = '',
}) => {
  const reportRef = useRef<HTMLDivElement>(null);

  const statusConfig = {
    compliant: {
      color: 'text-green-700 bg-green-100',
      icon: '✅',
      label: 'Fully Compliant',
    },
    warning: {
      color: 'text-yellow-700 bg-yellow-100',
      icon: '⚠️',
      label: 'Warnings Detected',
    },
    violation: {
      color: 'text-red-700 bg-red-100',
      icon: '🚨',
      label: 'Violations Detected',
    },
  };

  const config = statusConfig[data.overallCompliance.status];

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className={`compliance-report bg-white ${className}`}>
      {/* Action Bar (non-printable) */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 print:hidden">
        <h2 className="text-2xl font-bold">ACGME Compliance Report</h2>
        <div className="flex gap-2">
          <button
            onClick={handlePrint}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Print compliance report"
          >
            <span aria-hidden="true">🖨️</span> Print
          </button>
          {onExport && (
            <>
              <button
                onClick={() => onExport('pdf')}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Export compliance report as PDF"
              >
                <span aria-hidden="true">📄</span> Export PDF
              </button>
              <button
                onClick={() => onExport('excel')}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
                aria-label="Export compliance report as Excel"
              >
                <span aria-hidden="true">📊</span> Export Excel
              </button>
            </>
          )}
        </div>
      </div>

      {/* Report Content */}
      <div ref={reportRef} className="p-8 max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">ACGME Compliance Report</h1>
          <p className="text-gray-600">
            {new Date(data.reportPeriod.start).toLocaleDateString()} -{' '}
            {new Date(data.reportPeriod.end).toLocaleDateString()}
          </p>
        </div>

        {/* Resident Info */}
        <div className="bg-gray-50 rounded-lg p-6 mb-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-sm text-gray-600">Resident:</span>
              <div className="text-lg font-semibold">{data.personName}</div>
            </div>
            <div>
              <span className="text-sm text-gray-600">PGY Level:</span>
              <div className="text-lg font-semibold">{data.pgyLevel}</div>
            </div>
          </div>
        </div>

        {/* Overall Compliance Status */}
        <div className={`rounded-lg p-6 mb-6 ${config.color}`} role="status" aria-label="Overall compliance status">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl" aria-hidden="true">{config.icon}</span>
              <div>
                <h3 className="text-xl font-bold">{config.label}</h3>
                <p className="text-sm">Compliance Score: {data.overallCompliance.score}/100</p>
              </div>
            </div>
            <div className="text-right">
              <div
                className="text-4xl font-bold"
                role="meter"
                aria-valuenow={data.overallCompliance.score}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Compliance score ${data.overallCompliance.score} out of 100`}
              >
                {data.overallCompliance.score}%
              </div>
            </div>
          </div>
        </div>

        {/* Work Hours Section */}
        <section className="mb-8" aria-labelledby="work-hours-heading">
          <h3 id="work-hours-heading" className="text-xl font-bold mb-4 border-b-2 border-gray-300 pb-2">
            <span aria-hidden="true">📊</span> Work Hour Compliance
          </h3>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-600">Rolling 4-Week Avg</div>
              <div className="text-2xl font-bold">
                {data.workHours.rollingAverage.toFixed(1)}h
              </div>
              <div className="text-xs text-gray-500">Limit: 80h</div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-600">Max Week Hours</div>
              <div className="text-2xl font-bold">
                {data.workHours.maxWeekHours}h
              </div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-600">Violations</div>
              <div className={`text-2xl font-bold ${data.workHours.violations > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {data.workHours.violations}
              </div>
            </div>
          </div>
        </section>

        {/* Days Off Section */}
        <section className="mb-8" aria-labelledby="days-off-heading">
          <h3 id="days-off-heading" className="text-xl font-bold mb-4 border-b-2 border-gray-300 pb-2">
            <span aria-hidden="true">📅</span> 1-in-7 Days Off Compliance
          </h3>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-600">Total Days Off</div>
              <div className="text-2xl font-bold">
                {data.daysOff.totalDaysOff}
              </div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-600">Longest Stretch</div>
              <div className="text-2xl font-bold">
                {data.daysOff.longestStretch} days
              </div>
              <div className="text-xs text-gray-500">Max: 6 days</div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-600">Violations</div>
              <div className={`text-2xl font-bold ${data.daysOff.violations > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {data.daysOff.violations}
              </div>
            </div>
          </div>
        </section>

        {/* Supervision Section */}
        <section className="mb-8" aria-labelledby="supervision-heading">
          <h3 id="supervision-heading" className="text-xl font-bold mb-4 border-b-2 border-gray-300 pb-2">
            <span aria-hidden="true">👨‍⚕️</span> Supervision Ratio
          </h3>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-600">Average Ratio</div>
              <div className="text-2xl font-bold">
                1:{data.supervision.averageRatio.toFixed(1)}
              </div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-600">Required Ratio</div>
              <div className="text-2xl font-bold">
                1:{data.supervision.requiredRatio}
              </div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-600">Violations</div>
              <div className={`text-2xl font-bold ${data.supervision.violations > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {data.supervision.violations}
              </div>
            </div>
          </div>
        </section>

        {/* Violations Detail */}
        {data.violations.length > 0 && (
          <section className="mb-8" aria-labelledby="violations-heading">
            <h3 id="violations-heading" className="text-xl font-bold mb-4 border-b-2 border-red-300 pb-2 text-red-700">
              <span aria-hidden="true">🚨</span> Violation Details
            </h3>
            <div className="space-y-2">
              {data.violations.map((violation, idx) => (
                <div
                  key={idx}
                  className={`border-l-4 rounded p-3 ${
                    violation.severity === 'critical'
                      ? 'bg-red-50 border-red-500'
                      : 'bg-yellow-50 border-yellow-500'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-semibold">{violation.type}</div>
                      <div className="text-sm text-gray-700">{violation.message}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-600">
                        {new Date(violation.date).toLocaleDateString()}
                      </div>
                      <Badge
                        variant={violation.severity === 'critical' ? 'destructive' : 'warning'}
                        className="mt-1"
                      >
                        {violation.severity}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Footer */}
        <div className="mt-12 pt-6 border-t border-gray-300 text-center text-sm text-gray-600">
          <p>This report was generated on {new Date().toLocaleString()}</p>
          <p className="mt-2">
            ACGME Compliance standards enforced in accordance with{' '}
            <a
              href="https://www.acgme.org/what-we-do/accreditation/common-program-requirements/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              ACGME Common Program Requirements
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default ComplianceReport;
