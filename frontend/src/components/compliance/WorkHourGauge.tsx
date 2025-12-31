/**
 * WorkHourGauge Component
 *
 * Visual gauge for work hour tracking (80-hour ACGME limit)
 */

import React from 'react';

export interface WorkHourGaugeProps {
  label: string;
  hours: number;
  maxHours: number;
  showThreshold?: boolean;
  warningThreshold?: number; // Default 70 (87.5% of 80)
  className?: string;
}

export const WorkHourGauge: React.FC<WorkHourGaugeProps> = ({
  label,
  hours,
  maxHours,
  showThreshold = true,
  warningThreshold = 70,
  className = '',
}) => {
  const percentage = Math.min((hours / maxHours) * 100, 100);
  const isWarning = hours >= warningThreshold && hours < maxHours;
  const isViolation = hours >= maxHours;

  const getColor = () => {
    if (isViolation) return 'bg-red-500';
    if (isWarning) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getTextColor = () => {
    if (isViolation) return 'text-red-700';
    if (isWarning) return 'text-yellow-700';
    return 'text-green-700';
  };

  return (
    <div className={`work-hour-gauge ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className={`text-lg font-bold ${getTextColor()}`}>
          {hours.toFixed(1)}h / {maxHours}h
        </span>
      </div>

      {/* Progress Bar */}
      <div className="relative w-full h-8 bg-gray-200 rounded-full overflow-hidden">
        {/* Threshold Marker */}
        {showThreshold && (
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-gray-400 z-10"
            style={{ left: `${(warningThreshold / maxHours) * 100}%` }}
            aria-hidden="true"
          />
        )}

        {/* Progress Fill */}
        <div
          className={`h-full transition-all duration-500 ${getColor()}`}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={hours}
          aria-valuemin={0}
          aria-valuemax={maxHours}
          aria-label={`${label}: ${hours} hours out of ${maxHours} hours`}
        />

        {/* Percentage Text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-semibold text-gray-900 drop-shadow">
            {percentage.toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Status Indicator */}
      <div className="mt-2 flex items-center gap-2">
        {isViolation && (
          <div className="flex items-center gap-1 text-xs text-red-700">
            <span role="img" aria-label="Violation">🚨</span>
            <span className="font-medium">ACGME Violation</span>
          </div>
        )}
        {isWarning && !isViolation && (
          <div className="flex items-center gap-1 text-xs text-yellow-700">
            <span role="img" aria-label="Warning">⚠️</span>
            <span className="font-medium">Approaching Limit</span>
          </div>
        )}
        {!isWarning && !isViolation && (
          <div className="flex items-center gap-1 text-xs text-green-700">
            <span role="img" aria-label="Compliant">✅</span>
            <span className="font-medium">Within Limits</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkHourGauge;
