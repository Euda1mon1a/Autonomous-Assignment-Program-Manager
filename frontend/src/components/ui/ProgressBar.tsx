/**
 * ProgressBar Component
 *
 * Visual progress indicator with percentage display
 */

import React from 'react';

export interface ProgressBarProps {
  value: number; // 0-100
  max?: number;
  showLabel?: boolean;
  label?: string;
  variant?: 'default' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  showLabel = true,
  label,
  variant = 'default',
  size = 'md',
  animated = false,
  className = '',
}) => {
  const percentage = Math.min((value / max) * 100, 100);

  const variantColors = {
    default: 'bg-blue-600',
    success: 'bg-green-600',
    warning: 'bg-yellow-600',
    danger: 'bg-red-600',
  };

  const sizeConfig = {
    sm: 'h-2',
    md: 'h-4',
    lg: 'h-6',
  };

  const textSizeConfig = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <div className={`progress-bar ${className}`}>
      {/* Label */}
      {(label || showLabel) && (
        <div className={`flex items-center justify-between mb-2 ${textSizeConfig[size]}`}>
          {label && <span className="font-medium text-gray-700">{label}</span>}
          {showLabel && (
            <span className="font-semibold text-gray-900">
              {percentage.toFixed(0)}%
            </span>
          )}
        </div>
      )}

      {/* Progress Track */}
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${sizeConfig[size]}`}>
        <div
          className={`
            h-full transition-all duration-500 ease-out
            ${variantColors[variant]}
            ${animated ? 'animate-pulse' : ''}
          `}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
          aria-label={label || `Progress: ${percentage.toFixed(0)}%`}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
