'use client';

import React from 'react';

export type RotationType =
  | 'clinic'
  | 'inpatient'
  | 'call'
  | 'leave'
  | 'procedure'
  | 'conference'
  | 'admin'
  | 'research'
  | 'vacation'
  | 'sick';

export interface RotationBadgeProps {
  type: RotationType;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  showDot?: boolean;
  className?: string;
}

const rotationStyles: Record<RotationType, { bg: string; text: string; dot: string }> = {
  clinic: {
    bg: 'bg-clinic-light',
    text: 'text-clinic-dark',
    dot: 'bg-clinic',
  },
  inpatient: {
    bg: 'bg-inpatient-light',
    text: 'text-inpatient-dark',
    dot: 'bg-inpatient',
  },
  call: {
    bg: 'bg-call-light',
    text: 'text-call-dark',
    dot: 'bg-call',
  },
  leave: {
    bg: 'bg-leave-light',
    text: 'text-leave-dark',
    dot: 'bg-leave',
  },
  procedure: {
    bg: 'bg-purple-100',
    text: 'text-purple-800',
    dot: 'bg-purple-600',
  },
  conference: {
    bg: 'bg-cyan-100',
    text: 'text-cyan-800',
    dot: 'bg-cyan-600',
  },
  admin: {
    bg: 'bg-gray-100',
    text: 'text-gray-800',
    dot: 'bg-gray-600',
  },
  research: {
    bg: 'bg-indigo-100',
    text: 'text-indigo-800',
    dot: 'bg-indigo-600',
  },
  vacation: {
    bg: 'bg-emerald-100',
    text: 'text-emerald-800',
    dot: 'bg-emerald-600',
  },
  sick: {
    bg: 'bg-orange-100',
    text: 'text-orange-800',
    dot: 'bg-orange-600',
  },
};

const sizeStyles = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-base',
};

/**
 * RotationBadge component for displaying rotation types with consistent styling
 *
 * @example
 * ```tsx
 * <RotationBadge type="clinic" label="Clinic" />
 * <RotationBadge type="call" showDot />
 * <RotationBadge type="inpatient" size="lg" label="Inpatient Service" />
 * ```
 */
export function RotationBadge({
  type,
  label,
  size = 'md',
  showDot = false,
  className = '',
}: RotationBadgeProps) {
  const styles = rotationStyles[type];
  const displayLabel = label || type.charAt(0).toUpperCase() + type.slice(1);

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded ${styles.bg} ${styles.text} ${sizeStyles[size]} ${className}`}
    >
      {showDot && (
        <span className={`w-1.5 h-1.5 rounded-full ${styles.dot}`} />
      )}
      {displayLabel}
    </span>
  );
}

/**
 * RotationLegend component for displaying all rotation types
 */
export function RotationLegend({
  types,
  className = '',
}: {
  types?: RotationType[];
  className?: string;
}) {
  const displayTypes: RotationType[] = types || [
    'clinic',
    'inpatient',
    'call',
    'leave',
    'procedure',
    'conference',
  ];

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {displayTypes.map((type) => (
        <RotationBadge key={type} type={type} size="sm" showDot />
      ))}
    </div>
  );
}
