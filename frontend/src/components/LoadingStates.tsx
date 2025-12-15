'use client';

import React from 'react';

// ============================================================================
// Types and Shared Props
// ============================================================================

type Size = 'sm' | 'md' | 'lg';
type Variant = 'primary' | 'secondary' | 'white';

interface BaseProps {
  size?: Size;
  variant?: Variant;
  className?: string;
}

// ============================================================================
// Size Mappings
// ============================================================================

const spinnerSizes = {
  sm: 'w-4 h-4 border-2',
  md: 'w-8 h-8 border-2',
  lg: 'w-12 h-12 border-3',
};

const textSizes = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
};

// ============================================================================
// Spinner Variants
// ============================================================================

interface SpinnerProps extends BaseProps {
  label?: string;
}

/**
 * Circular spinning loader
 */
export function Spinner({
  size = 'md',
  variant = 'primary',
  className = '',
  label = 'Loading'
}: SpinnerProps) {
  const variantClasses = {
    primary: 'border-gray-200 border-t-blue-600',
    secondary: 'border-gray-300 border-t-gray-600',
    white: 'border-white/30 border-t-white',
  };

  return (
    <div
      className={`${spinnerSizes[size]} ${variantClasses[variant]} rounded-full animate-spin ${className}`}
      role="status"
      aria-busy="true"
      aria-label={label}
    />
  );
}

/**
 * Small inline spinner for buttons
 */
export function ButtonSpinner({
  variant = 'white',
  className = ''
}: Omit<SpinnerProps, 'size'>) {
  return (
    <Spinner
      size="sm"
      variant={variant}
      className={className}
      label="Processing"
    />
  );
}

interface PageSpinnerProps extends SpinnerProps {
  message?: string;
}

/**
 * Full-page centered spinner with optional message
 */
export function PageSpinner({
  size = 'lg',
  variant = 'primary',
  message,
  className = ''
}: PageSpinnerProps) {
  return (
    <div className={`flex flex-col items-center justify-center min-h-[400px] gap-4 ${className}`}>
      <Spinner size={size} variant={variant} />
      {message && (
        <p className={`${textSizes[size]} text-gray-600`}>
          {message}
        </p>
      )}
    </div>
  );
}

// ============================================================================
// Skeleton Variants
// ============================================================================

interface SkeletonTextProps extends BaseProps {
  lines?: number;
  widths?: string[];
}

/**
 * Animated text placeholder with configurable lines
 */
export function SkeletonText({
  lines = 3,
  widths,
  size = 'md',
  className = ''
}: SkeletonTextProps) {
  const heights = {
    sm: 'h-3',
    md: 'h-4',
    lg: 'h-5',
  };

  const defaultWidths = ['w-full', 'w-5/6', 'w-4/6'];
  const lineWidths = widths || defaultWidths;

  return (
    <div
      className={`space-y-2 ${className}`}
      role="status"
      aria-busy="true"
      aria-label="Loading content"
    >
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={`${heights[size]} bg-gray-200 rounded animate-pulse ${
            lineWidths[i % lineWidths.length]
          }`}
        />
      ))}
    </div>
  );
}

/**
 * Circular avatar placeholder
 */
export function SkeletonAvatar({
  size = 'md',
  className = ''
}: BaseProps) {
  const sizes = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  };

  return (
    <div
      className={`${sizes[size]} bg-gray-200 rounded-full animate-pulse ${className}`}
      role="status"
      aria-busy="true"
      aria-label="Loading avatar"
    />
  );
}

/**
 * Button-shaped placeholder
 */
export function SkeletonButton({
  size = 'md',
  className = ''
}: BaseProps) {
  const sizes = {
    sm: 'h-8 w-20',
    md: 'h-10 w-24',
    lg: 'h-12 w-32',
  };

  return (
    <div
      className={`${sizes[size]} bg-gray-200 rounded animate-pulse ${className}`}
      role="status"
      aria-busy="true"
      aria-label="Loading button"
    />
  );
}

/**
 * Card-shaped placeholder
 */
export function SkeletonCard({
  size = 'md',
  className = ''
}: BaseProps) {
  const padding = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  return (
    <div
      className={`bg-white rounded-lg shadow ${padding[size]} ${className}`}
      role="status"
      aria-busy="true"
      aria-label="Loading card"
    >
      <div className="animate-pulse space-y-3">
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        <div className="h-3 bg-gray-200 rounded w-1/2"></div>
        <div className="h-8 bg-gray-200 rounded w-full"></div>
      </div>
    </div>
  );
}

// ============================================================================
// Progress Variants
// ============================================================================

interface ProgressBarProps extends BaseProps {
  percentage: number;
  showLabel?: boolean;
}

/**
 * Horizontal progress bar with percentage
 */
export function ProgressBar({
  percentage,
  showLabel = true,
  size = 'md',
  variant = 'primary',
  className = ''
}: ProgressBarProps) {
  const heights = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  const colors = {
    primary: 'bg-blue-600',
    secondary: 'bg-gray-600',
    white: 'bg-white',
  };

  const clampedPercentage = Math.min(Math.max(percentage, 0), 100);

  return (
    <div className={className}>
      <div
        className={`w-full bg-gray-200 rounded-full overflow-hidden ${heights[size]}`}
        role="progressbar"
        aria-valuenow={clampedPercentage}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Progress: ${clampedPercentage}%`}
      >
        <div
          className={`${heights[size]} ${colors[variant]} transition-all duration-300 ease-in-out`}
          style={{ width: `${clampedPercentage}%` }}
        />
      </div>
      {showLabel && (
        <p className={`${textSizes[size]} text-gray-600 mt-1 text-right`}>
          {clampedPercentage}%
        </p>
      )}
    </div>
  );
}

interface ProgressCircleProps extends BaseProps {
  percentage: number;
  showLabel?: boolean;
}

/**
 * Circular progress indicator
 */
export function ProgressCircle({
  percentage,
  showLabel = true,
  size = 'md',
  variant = 'primary',
  className = ''
}: ProgressCircleProps) {
  const sizes = {
    sm: { size: 40, stroke: 3 },
    md: { size: 60, stroke: 4 },
    lg: { size: 80, stroke: 5 },
  };

  const colors = {
    primary: 'text-blue-600',
    secondary: 'text-gray-600',
    white: 'text-white',
  };

  const { size: circleSize, stroke } = sizes[size];
  const radius = (circleSize - stroke) / 2;
  const circumference = radius * 2 * Math.PI;
  const clampedPercentage = Math.min(Math.max(percentage, 0), 100);
  const offset = circumference - (clampedPercentage / 100) * circumference;

  return (
    <div
      className={`relative inline-flex items-center justify-center ${className}`}
      role="progressbar"
      aria-valuenow={clampedPercentage}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Progress: ${clampedPercentage}%`}
    >
      <svg
        width={circleSize}
        height={circleSize}
        className="transform -rotate-90"
      >
        {/* Background circle */}
        <circle
          cx={circleSize / 2}
          cy={circleSize / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={stroke}
          fill="none"
          className="text-gray-200"
        />
        {/* Progress circle */}
        <circle
          cx={circleSize / 2}
          cy={circleSize / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={stroke}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={`${colors[variant]} transition-all duration-300 ease-in-out`}
        />
      </svg>
      {showLabel && (
        <span
          className={`absolute ${textSizes[size]} font-semibold ${colors[variant]}`}
        >
          {clampedPercentage}%
        </span>
      )}
    </div>
  );
}

// ============================================================================
// Composite Loaders
// ============================================================================

interface PageLoaderProps extends BaseProps {
  message?: string;
}

/**
 * Full page loading state
 */
export function PageLoader({
  size = 'lg',
  variant = 'primary',
  message = 'Loading...',
  className = ''
}: PageLoaderProps) {
  return (
    <div className={`flex items-center justify-center min-h-screen ${className}`}>
      <PageSpinner size={size} variant={variant} message={message} />
    </div>
  );
}

interface CardLoaderProps extends BaseProps {
  count?: number;
}

/**
 * Loading state for cards
 */
export function CardLoader({
  size = 'md',
  count = 1,
  className = ''
}: CardLoaderProps) {
  return (
    <div className={`grid gap-4 ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} size={size} />
      ))}
    </div>
  );
}

interface TableLoaderProps extends BaseProps {
  rows?: number;
  columns?: number;
}

/**
 * Loading state for tables (multiple skeleton rows)
 */
export function TableLoader({
  rows = 5,
  columns = 4,
  className = ''
}: TableLoaderProps) {
  return (
    <div
      className={className}
      role="status"
      aria-busy="true"
      aria-label="Loading table"
    >
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="grid gap-4 py-3 border-b border-gray-100" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {Array.from({ length: columns }).map((_, colIndex) => (
            <div key={colIndex} className="h-4 bg-gray-200 rounded animate-pulse" />
          ))}
        </div>
      ))}
    </div>
  );
}

interface InlineLoaderProps extends BaseProps {
  text?: string;
}

/**
 * Small inline loading indicator
 */
export function InlineLoader({
  size = 'sm',
  variant = 'primary',
  text,
  className = ''
}: InlineLoaderProps) {
  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <Spinner size={size} variant={variant} />
      {text && (
        <span className={`${textSizes[size]} text-gray-600`}>
          {text}
        </span>
      )}
    </div>
  );
}

// ============================================================================
// Exports
// ============================================================================

export default {
  // Spinners
  Spinner,
  ButtonSpinner,
  PageSpinner,

  // Skeletons
  SkeletonText,
  SkeletonAvatar,
  SkeletonButton,
  SkeletonCard,

  // Progress
  ProgressBar,
  ProgressCircle,

  // Composite
  PageLoader,
  CardLoader,
  TableLoader,
  InlineLoader,
};
