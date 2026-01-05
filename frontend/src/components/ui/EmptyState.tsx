'use client';

import { type LucideIcon, Inbox } from 'lucide-react';
import { ReactNode } from 'react';

export interface DarkEmptyStateProps {
  /** Icon to display (default: Inbox) */
  icon?: LucideIcon;
  /** Main title text */
  title: string;
  /** Optional description text */
  description?: string;
  /** Optional action button or element */
  action?: ReactNode;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Additional CSS classes */
  className?: string;
}

const sizeClasses = {
  sm: {
    container: 'py-6 px-4',
    icon: 'w-8 h-8',
    title: 'text-sm',
    description: 'text-xs',
  },
  md: {
    container: 'py-8 px-4',
    icon: 'w-12 h-12',
    title: 'text-base',
    description: 'text-sm',
  },
  lg: {
    container: 'py-12 px-6',
    icon: 'w-16 h-16',
    title: 'text-lg',
    description: 'text-base',
  },
};

/**
 * Reusable empty state component for dark theme admin pages.
 * Uses slate/violet palette for consistency with admin interface.
 *
 * @example
 * ```tsx
 * <DarkEmptyState
 *   icon={Users}
 *   title="No users found"
 *   description="Try adjusting your filters or add a new user."
 *   action={
 *     <Button onClick={() => setShowModal(true)}>
 *       Add User
 *     </Button>
 *   }
 * />
 * ```
 */
export function DarkEmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  size = 'md',
  className = '',
}: DarkEmptyStateProps) {
  const sizes = sizeClasses[size];

  return (
    <div
      className={`
        flex flex-col items-center justify-center text-center
        border border-dashed border-slate-700 rounded-lg
        ${sizes.container}
        ${className}
      `}
    >
      <div className="p-3 bg-slate-800/50 rounded-full mb-4">
        <Icon className={`${sizes.icon} text-slate-500`} />
      </div>
      <h3 className={`font-medium text-slate-200 mb-1 ${sizes.title}`}>
        {title}
      </h3>
      {description && (
        <p className={`text-slate-400 mb-4 max-w-sm ${sizes.description}`}>
          {description}
        </p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

/**
 * Simple inline empty state for compact spaces like table cells or lists.
 * Uses dark theme styling.
 */
export function InlineEmptyState({
  message,
  className = '',
}: {
  message: string;
  className?: string;
}) {
  return (
    <div className={`py-8 text-center text-slate-500 text-sm ${className}`}>
      {message}
    </div>
  );
}
