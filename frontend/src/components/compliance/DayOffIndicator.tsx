/**
 * DayOffIndicator Component
 *
 * Tracks 1-in-7 day off ACGME requirement
 */

import React from 'react';

export interface DayOffIndicatorProps {
  consecutiveDaysWorked: number;
  lastDayOff: string;
  maxConsecutiveDays?: number; // Default 6
  className?: string;
}

export const DayOffIndicator: React.FC<DayOffIndicatorProps> = ({
  consecutiveDaysWorked,
  lastDayOff,
  maxConsecutiveDays = 6,
  className = '',
}) => {
  const isViolation = consecutiveDaysWorked > maxConsecutiveDays;
  const isWarning = consecutiveDaysWorked === maxConsecutiveDays;
  const daysUntilRequired = Math.max(0, maxConsecutiveDays - consecutiveDaysWorked);

  const getStatus = () => {
    if (isViolation) return {
      color: 'bg-red-100 border-red-500 text-red-900',
      icon: '🚨',
      label: 'Violation',
      message: `Worked ${consecutiveDaysWorked} consecutive days (max ${maxConsecutiveDays})`,
    };
    if (isWarning) return {
      color: 'bg-yellow-100 border-yellow-500 text-yellow-900',
      icon: '⚠️',
      label: 'Warning',
      message: 'Day off required tomorrow',
    };
    return {
      color: 'bg-green-100 border-green-500 text-green-900',
      icon: '✅',
      label: 'Compliant',
      message: `${daysUntilRequired} day${daysUntilRequired !== 1 ? 's' : ''} until required day off`,
    };
  };

  const status = getStatus();
  const daysSinceLastOff = Math.floor(
    (new Date().getTime() - new Date(lastDayOff).getTime()) / (1000 * 60 * 60 * 24)
  );

  return (
    <div
      className={`day-off-indicator border-l-4 rounded-lg p-4 ${status.color} ${className}`}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl" role="img" aria-label={status.label}>
          {status.icon}
        </span>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold">{status.label}</h4>
            <span className="text-sm font-medium">
              {consecutiveDaysWorked} / {maxConsecutiveDays} days
            </span>
          </div>

          <p className="text-sm mb-3">{status.message}</p>

          {/* Visual Timeline */}
          <div className="flex gap-1 mb-3">
            {Array.from({ length: maxConsecutiveDays + 1 }).map((_, idx) => (
              <div
                key={idx}
                className={`
                  flex-1 h-8 rounded
                  ${idx < consecutiveDaysWorked
                    ? isViolation || (isWarning && idx === maxConsecutiveDays)
                      ? 'bg-red-500'
                      : 'bg-green-500'
                    : 'bg-gray-200'
                  }
                `}
                title={`Day ${idx + 1}`}
                aria-label={`Day ${idx + 1}${idx < consecutiveDaysWorked ? ' worked' : ' available'}`}
              />
            ))}
          </div>

          {/* Last Day Off Info */}
          <div className="text-xs text-gray-600">
            Last day off: {new Date(lastDayOff).toLocaleDateString()} ({daysSinceLastOff} day{daysSinceLastOff !== 1 ? 's' : ''} ago)
          </div>
        </div>
      </div>
    </div>
  );
};

export default DayOffIndicator;
