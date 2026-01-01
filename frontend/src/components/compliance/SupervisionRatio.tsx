/**
 * SupervisionRatio Component
 *
 * Displays faculty-to-resident supervision ratio compliance
 */

import React from 'react';

export interface SupervisionRatioProps {
  current: number; // Current ratio (e.g., 3.5 means 3.5 residents per faculty)
  required: number; // Required max ratio
  pgyLevel: string;
  className?: string;
}

const pgyRequirements: Record<string, { maxRatio: number; description: string }> = {
  'PGY-1': {
    maxRatio: 2,
    description: 'Interns require higher supervision (max 1:2 faculty:resident ratio)',
  },
  'PGY-2': {
    maxRatio: 4,
    description: 'Advanced residents (max 1:4 faculty:resident ratio)',
  },
  'PGY-3': {
    maxRatio: 4,
    description: 'Senior residents (max 1:4 faculty:resident ratio)',
  },
};

export const SupervisionRatio: React.FC<SupervisionRatioProps> = ({
  current,
  required,
  pgyLevel,
  className = '',
}) => {
  const isViolation = current > required;
  const isWarning = current > required * 0.9;
  const utilizationPercent = (current / required) * 100;

  const getStatus = () => {
    if (isViolation) return {
      color: 'bg-red-100 border-red-500 text-red-900',
      progressColor: 'bg-red-500',
      icon: '🚨',
      label: 'Insufficient Supervision',
    };
    if (isWarning) return {
      color: 'bg-yellow-100 border-yellow-500 text-yellow-900',
      progressColor: 'bg-yellow-500',
      icon: '⚠️',
      label: 'Approaching Limit',
    };
    return {
      color: 'bg-green-100 border-green-500 text-green-900',
      progressColor: 'bg-green-500',
      icon: '✅',
      label: 'Adequate Supervision',
    };
  };

  const status = getStatus();
  const requirement = pgyRequirements[pgyLevel] || pgyRequirements['PGY-2'];

  return (
    <div
      className={`supervision-ratio border-l-4 rounded-lg p-4 ${status.color} ${className}`}
      role="status"
      aria-live="polite"
      aria-label={`Supervision ratio compliance: ${status.label}`}
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl" aria-hidden="true">
          {status.icon}
        </span>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold">{status.label}</h4>
            <span className="text-sm font-medium">
              1:{current.toFixed(1)} (max 1:{required})
            </span>
          </div>

          {/* Progress Bar */}
          <div className="relative w-full h-6 bg-gray-200 rounded-full overflow-hidden mb-3">
            <div
              className={`h-full transition-all duration-500 ${status.progressColor}`}
              style={{ width: `${Math.min(utilizationPercent, 100)}%` }}
              role="progressbar"
              aria-valuenow={current}
              aria-valuemin={0}
              aria-valuemax={required}
              aria-label={`Supervision ratio: ${current.toFixed(1)} residents per faculty`}
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-xs font-semibold text-gray-900">
                {utilizationPercent.toFixed(0)}%
              </span>
            </div>
          </div>

          {/* PGY Level Info */}
          <div className="text-xs bg-white bg-opacity-50 rounded p-2">
            <div className="font-medium mb-1">{pgyLevel} Requirements:</div>
            <div className="text-gray-700">{requirement.description}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SupervisionRatio;
