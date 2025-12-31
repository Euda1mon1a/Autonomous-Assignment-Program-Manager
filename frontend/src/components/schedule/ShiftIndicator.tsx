/**
 * ShiftIndicator Component
 *
 * Visual indicator for AM/PM/Night shifts with color coding
 */

import React from 'react';

export type ShiftType = 'AM' | 'PM' | 'Night' | 'All-Day';

export interface ShiftIndicatorProps {
  shift: ShiftType;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'badge' | 'icon' | 'full';
  className?: string;
}

const shiftConfig: Record<ShiftType, {
  icon: string;
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
}> = {
  AM: {
    icon: '☀️',
    label: 'AM',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-300',
  },
  PM: {
    icon: '🌤️',
    label: 'PM',
    color: 'text-orange-800',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-300',
  },
  Night: {
    icon: '🌙',
    label: 'Night',
    color: 'text-indigo-800',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-300',
  },
  'All-Day': {
    icon: '⏰',
    label: 'All Day',
    color: 'text-purple-800',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-300',
  },
};

const sizeClasses = {
  sm: 'text-xs px-1.5 py-0.5',
  md: 'text-sm px-2 py-1',
  lg: 'text-base px-3 py-1.5',
};

const iconSizeClasses = {
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-xl',
};

export const ShiftIndicator: React.FC<ShiftIndicatorProps> = ({
  shift,
  size = 'md',
  variant = 'badge',
  className = '',
}) => {
  const config = shiftConfig[shift];

  if (variant === 'icon') {
    return (
      <span
        className={`inline-flex items-center ${iconSizeClasses[size]} ${className}`}
        role="img"
        aria-label={`${config.label} shift`}
      >
        {config.icon}
      </span>
    );
  }

  if (variant === 'badge') {
    return (
      <span
        className={`
          inline-flex items-center gap-1 rounded-full font-semibold
          ${config.bgColor} ${config.color}
          ${sizeClasses[size]}
          ${className}
        `}
        role="status"
        aria-label={`${config.label} shift`}
      >
        <span role="img" aria-hidden="true">{config.icon}</span>
        <span>{config.label}</span>
      </span>
    );
  }

  // Full variant with border
  return (
    <div
      className={`
        inline-flex items-center gap-2 rounded-lg border-2 font-medium
        ${config.bgColor} ${config.color} ${config.borderColor}
        ${sizeClasses[size]}
        ${className}
      `}
      role="status"
      aria-label={`${config.label} shift`}
    >
      <span className="text-lg" role="img" aria-hidden="true">
        {config.icon}
      </span>
      <span className="font-semibold">{config.label} Shift</span>
    </div>
  );
};

export default ShiftIndicator;
