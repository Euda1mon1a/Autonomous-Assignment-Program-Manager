'use client';

import { X, RefreshCw } from 'lucide-react';
import { getErrorMessage } from '@/lib/errors';

interface ErrorAlertProps {
  /**
   * Error message to display. Can be a string or any error type.
   * If an error object is passed, getErrorMessage will extract a user-friendly message.
   */
  message: string | unknown;
  onRetry?: () => void;
  onDismiss?: () => void;
}

/**
 * Reusable error display component with optional retry and dismiss actions.
 * Automatically converts error objects to user-friendly messages.
 */
export function ErrorAlert({ message, onRetry, onDismiss }: ErrorAlertProps) {
  // Convert error objects to user-friendly messages
  const displayMessage = typeof message === 'string' ? message : getErrorMessage(message);
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4" role="alert">
      <div className="flex items-start gap-3">
        {/* Error icon */}
        <div className="flex-shrink-0">
          <svg
            className="w-5 h-5 text-red-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>

        {/* Message content */}
        <div className="flex-1 min-w-0">
          <p className="text-sm text-red-800">{displayMessage}</p>
        </div>

        {/* Action buttons */}
        <div className="flex-shrink-0 flex items-center gap-2">
          {onRetry && (
            <button
              onClick={onRetry}
              className="p-1 text-red-600 hover:text-red-800 hover:bg-red-100 rounded transition-colors"
              title="Retry"
              aria-label="Retry"
            >
              <RefreshCw className="w-4 h-4" aria-hidden="true" />
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="p-1 text-red-600 hover:text-red-800 hover:bg-red-100 rounded transition-colors"
              title="Dismiss"
              aria-label="Dismiss error"
            >
              <X className="w-4 h-4" aria-hidden="true" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
