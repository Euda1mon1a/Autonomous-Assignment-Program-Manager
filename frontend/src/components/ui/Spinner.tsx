/**
 * Spinner Component
 *
 * Loading spinner with various sizes and variants
 */

import React from 'react';

export interface SpinnerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'primary' | 'white';
  label?: string;
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  variant = 'default',
  label,
  className = '',
}) => {
  const sizeClasses = {
    xs: 'w-4 h-4',
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  };

  const variantClasses = {
    default: 'border-gray-300 border-t-gray-600',
    primary: 'border-blue-200 border-t-blue-600',
    white: 'border-white border-opacity-25 border-t-white',
  };

  return (
    <div className={`spinner inline-flex flex-col items-center gap-2 ${className}`}>
      <div
        className={`
          animate-spin rounded-full border-2
          ${sizeClasses[size]}
          ${variantClasses[variant]}
        `}
        role="status"
        aria-label={label || 'Loading'}
      />
      {label && (
        <span className="text-sm text-gray-600">{label}</span>
      )}
    </div>
  );
};

export default Spinner;
