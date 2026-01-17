'use client';

import React from 'react';
import { AlertCircle } from 'lucide-react';

export interface CoverageSlot {
  date: Date;
  period: 'AM' | 'PM';
  required: number;
  assigned: number;
  staff: string[];
}

export interface CoverageMatrixProps {
  slots: CoverageSlot[];
  dateRange: { start: Date; end: Date };
  showWarnings?: boolean;
  className?: string;
}

/**
 * CoverageMatrix component for visualizing staffing levels
 *
 * @example
 * ```tsx
 * <CoverageMatrix
 *   slots={coverageSlots}
 *   dateRange={{ start: new Date(), end: new Date() }}
 *   showWarnings
 * />
 * ```
 */
export function CoverageMatrix({
  slots,
  dateRange,
  showWarnings = true,
  className = '',
}: CoverageMatrixProps) {
  const getDates = () => {
    const dates: Date[] = [];
    const current = new Date(dateRange.start);
    while (current <= dateRange.end) {
      dates.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }
    return dates;
  };

  const dates = getDates();

  const getSlot = (date: Date, period: 'AM' | 'PM') => {
    return slots.find(
      (s) =>
        s.date.toDateString() === date.toDateString() && s.period === period
    );
  };

  const getCoverageColor = (slot?: CoverageSlot) => {
    if (!slot) return 'bg-gray-50';

    const coverage = slot.assigned / slot.required;

    if (coverage >= 1) return 'bg-green-100 text-green-900';
    if (coverage >= 0.75) return 'bg-amber-100 text-amber-900';
    return 'bg-red-100 text-red-900';
  };

  const _getCoverageStatus = (slot?: CoverageSlot) => {
    if (!slot) return 'empty';

    const coverage = slot.assigned / slot.required;

    if (coverage >= 1) return 'full';
    if (coverage >= 0.75) return 'partial';
    return 'critical';
  };

  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Date
            </th>
            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
              AM
            </th>
            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
              PM
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {dates.map((date, index) => {
            const amSlot = getSlot(date, 'AM');
            const pmSlot = getSlot(date, 'PM');

            return (
              <tr key={index} className="hover:bg-gray-50">
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                  {date.toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    weekday: 'short',
                  })}
                </td>
                <td className={`px-3 py-2 text-center ${getCoverageColor(amSlot)}`}>
                  <CoverageCell slot={amSlot} showWarnings={showWarnings} />
                </td>
                <td className={`px-3 py-2 text-center ${getCoverageColor(pmSlot)}`}>
                  <CoverageCell slot={pmSlot} showWarnings={showWarnings} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Individual coverage cell component
 */
function CoverageCell({
  slot,
  showWarnings,
}: {
  slot?: CoverageSlot;
  showWarnings: boolean;
}) {
  if (!slot) {
    return <span className="text-xs text-gray-400">-</span>;
  }

  const coverage = slot.assigned / slot.required;
  const isCritical = coverage < 0.75;

  return (
    <div className="inline-flex items-center gap-1">
      <span className="text-sm font-medium">
        {slot.assigned}/{slot.required}
      </span>
      {showWarnings && isCritical && (
        <AlertCircle className="w-4 h-4" />
      )}
    </div>
  );
}

/**
 * Coverage summary statistics
 */
export function CoverageSummary({
  slots,
  className = '',
}: {
  slots: CoverageSlot[];
  className?: string;
}) {
  const totalSlots = slots.length;
  const fullyStaffed = slots.filter((s) => s.assigned >= s.required).length;
  const partiallyStaffed = slots.filter(
    (s) => s.assigned > 0 && s.assigned < s.required && s.assigned / s.required >= 0.75
  ).length;
  const critical = slots.filter(
    (s) => s.assigned / s.required < 0.75
  ).length;

  const stats = [
    {
      label: 'Fully Staffed',
      value: fullyStaffed,
      color: 'text-green-600',
      bg: 'bg-green-100',
    },
    {
      label: 'Partial Coverage',
      value: partiallyStaffed,
      color: 'text-amber-600',
      bg: 'bg-amber-100',
    },
    {
      label: 'Critical',
      value: critical,
      color: 'text-red-600',
      bg: 'bg-red-100',
    },
  ];

  return (
    <div className={`grid grid-cols-3 gap-4 ${className}`}>
      {stats.map((stat) => (
        <div key={stat.label} className={`rounded-lg p-4 ${stat.bg}`}>
          <div className={`text-2xl font-bold ${stat.color}`}>
            {stat.value}
          </div>
          <div className="text-sm text-gray-600">{stat.label}</div>
          <div className="text-xs text-gray-500 mt-1">
            {((stat.value / totalSlots) * 100).toFixed(1)}%
          </div>
        </div>
      ))}
    </div>
  );
}
