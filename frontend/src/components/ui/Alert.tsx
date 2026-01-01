'use client';

import React from 'react';
import { AlertCircle, CheckCircle, Info, XCircle, X } from 'lucide-react';

export type AlertVariant = 'info' | 'success' | 'warning' | 'error';

export interface AlertProps {
  variant?: AlertVariant;
  title?: string;
  children: React.ReactNode;
  dismissible?: boolean;
  onDismiss?: () => void;
  className?: string;
}

const variantConfig = {
  info: {
    container: 'bg-blue-50 border-blue-200 text-blue-900',
    icon: Info,
    iconColor: 'text-blue-600',
  },
  success: {
    container: 'bg-green-50 border-green-200 text-green-900',
    icon: CheckCircle,
    iconColor: 'text-green-600',
  },
  warning: {
    container: 'bg-amber-50 border-amber-200 text-amber-900',
    icon: AlertCircle,
    iconColor: 'text-amber-600',
  },
  error: {
    container: 'bg-red-50 border-red-200 text-red-900',
    icon: XCircle,
    iconColor: 'text-red-600',
  },
};

/**
 * Alert component for displaying important messages
 *
 * @example
 * ```tsx
 * <Alert variant="success" title="Success">
 *   Your changes have been saved.
 * </Alert>
 *
 * <Alert variant="error" dismissible onDismiss={() => // console.log('dismissed')}>
 *   An error occurred.
 * </Alert>
 * ```
 */
export function Alert({
  variant = 'info',
  title,
  children,
  dismissible = false,
  onDismiss,
  className = '',
}: AlertProps) {
  const config = variantConfig[variant];
  const Icon = config.icon;

  return (
    <div
      className={`rounded-lg border p-4 ${config.container} ${className}`}
      role="alert"
    >
      <div className="flex gap-3">
        <Icon className={`w-5 h-5 flex-shrink-0 ${config.iconColor}`} />

        <div className="flex-1 min-w-0">
          {title && (
            <h3 className="text-sm font-semibold mb-1">{title}</h3>
          )}
          <div className="text-sm">{children}</div>
        </div>

        {dismissible && onDismiss && (
          <button
            onClick={onDismiss}
            className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Dismiss"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  );
}
