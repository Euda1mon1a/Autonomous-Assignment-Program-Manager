'use client';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
};

const textSizeClasses = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
};

/**
 * Reusable loading spinner component with optional text.
 */
export function LoadingSpinner({ size = 'md', text }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <div
        className={`${sizeClasses[size]} border-2 border-slate-700 border-t-violet-500 rounded-full animate-spin`}
        role="status"
        aria-label="Loading"
      />
      {text && (
        <p className={`${textSizeClasses[size]} text-slate-400`}>{text}</p>
      )}
    </div>
  );
}
