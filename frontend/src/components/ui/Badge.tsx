'use client';

import React from 'react';

export type BadgeVariant = 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'destructive' | 'info';
export type BadgeSize = 'sm' | 'md' | 'lg';

export interface BadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  rounded?: boolean;
  dot?: boolean;
  children: React.ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-gray-100 text-gray-800',
  primary: 'bg-blue-100 text-blue-800',
  success: 'bg-green-100 text-green-800',
  warning: 'bg-amber-100 text-amber-800',
  danger: 'bg-red-100 text-red-800',
  destructive: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  info: 'bg-cyan-100 text-cyan-800',
};

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-base',
};

/**
 * Badge component for labels, tags, and status indicators
 *
 * @example
 * ```tsx
 * <Badge variant="success">Active</Badge>
 * <Badge variant="warning" dot>Pending</Badge>
 * <Badge variant="danger" rounded>Error</Badge>
 * ```
 */
export function Badge({
  variant = 'default',
  size = 'md',
  rounded = false,
  dot = false,
  children,
  className = '',
}: BadgeProps) {
  const baseStyles = 'inline-flex items-center gap-1.5 font-medium';
  const roundedStyles = rounded ? 'rounded-full' : 'rounded';

  return (
    <span className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${roundedStyles} ${className}`}>
      {dot && (
        <span className={`w-1.5 h-1.5 rounded-full ${variant === 'default' ? 'bg-gray-600' :
          variant === 'primary' ? 'bg-blue-600' :
          variant === 'success' ? 'bg-green-600' :
          variant === 'warning' ? 'bg-amber-600' :
          variant === 'danger' ? 'bg-red-600' :
          variant === 'destructive' ? 'bg-red-600' :
          'bg-cyan-600'
        }`} />
      )}
      {children}
    </span>
  );
}

/**
 * Numeric badge variant (e.g., notification count)
 */
export function NumericBadge({
  count,
  max = 99,
  variant = 'danger',
  className = '',
}: {
  count: number;
  max?: number;
  variant?: BadgeVariant;
  className?: string;
}) {
  const displayCount = count > max ? `${max}+` : count;

  return (
    <Badge variant={variant} size="sm" rounded className={className}>
      {displayCount}
    </Badge>
  );
}
