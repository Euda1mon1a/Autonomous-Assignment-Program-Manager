/**
 * RotationBadge Component
 *
 * Displays a color-coded badge for rotation types with icons
 */

import React from 'react';

export interface RotationBadgeProps {
  rotationType: string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

const rotationConfig: Record<string, { color: string; bgColor: string; icon: string; label: string }> = {
  clinic: {
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    icon: '🏥',
    label: 'Clinic',
  },
  inpatient: {
    color: 'text-purple-800',
    bgColor: 'bg-purple-100',
    icon: '🛏️',
    label: 'Inpatient',
  },
  procedures: {
    color: 'text-green-800',
    bgColor: 'bg-green-100',
    icon: '💉',
    label: 'Procedures',
  },
  conference: {
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    icon: '📚',
    label: 'Conference',
  },
  call: {
    color: 'text-red-800',
    bgColor: 'bg-red-100',
    icon: '📞',
    label: 'Call',
  },
  fmit: {
    color: 'text-indigo-800',
    bgColor: 'bg-indigo-100',
    icon: '🎖️',
    label: 'FMIT',
  },
  tdy: {
    color: 'text-gray-800',
    bgColor: 'bg-gray-100',
    icon: '✈️',
    label: 'TDY',
  },
  deployment: {
    color: 'text-orange-800',
    bgColor: 'bg-orange-100',
    icon: '🌍',
    label: 'Deployment',
  },
  leave: {
    color: 'text-teal-800',
    bgColor: 'bg-teal-100',
    icon: '🏖️',
    label: 'Leave',
  },
  admin: {
    color: 'text-pink-800',
    bgColor: 'bg-pink-100',
    icon: '📋',
    label: 'Admin',
  },
};

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-3 py-1 text-sm',
  lg: 'px-4 py-1.5 text-base',
};

export const RotationBadge: React.FC<RotationBadgeProps> = ({
  rotationType,
  size = 'md',
  showIcon = true,
  className = '',
}) => {
  const key = rotationType.toLowerCase().replace(/\s+/g, '_');
  const config = rotationConfig[key] || {
    color: 'text-slate-800',
    bgColor: 'bg-slate-100',
    icon: '📌',
    label: rotationType,
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1 rounded-full font-semibold
        ${config.bgColor} ${config.color}
        ${sizeClasses[size]}
        ${className}
      `}
      role="status"
      aria-label={`Rotation type: ${config.label}`}
    >
      {showIcon && (
        <span role="img" aria-hidden="true">
          {config.icon}
        </span>
      )}
      <span>{config.label}</span>
    </span>
  );
};

export default RotationBadge;
