/**
 * Error toast notification component.
 *
 * Displays error messages as toast notifications.
 */

import React from 'react'
import { getErrorTitle, getDetailedErrorMessage } from './error-messages'
import { ErrorSeverity, getErrorSeverity, isRFC7807Error } from './error-types'

interface ErrorToastProps {
  error: unknown
  onClose: () => void
  autoClose?: boolean
  autoCloseDelay?: number
}

/**
 * Error Toast Component
 */
export function ErrorToast({
  error,
  onClose,
  autoClose = true,
  autoCloseDelay = 5000,
}: ErrorToastProps) {
  const title = getErrorTitle(error)
  const { message, details, suggestions } = getDetailedErrorMessage(error)

  // Get severity for styling
  const severity = isRFC7807Error(error)
    ? getErrorSeverity(error.status)
    : ErrorSeverity.ERROR

  // Auto close toast after delay
  React.useEffect(() => {
    if (autoClose) {
      const timer = setTimeout(() => {
        onClose()
      }, autoCloseDelay)

      return () => clearTimeout(timer)
    }
  }, [autoClose, autoCloseDelay, onClose])

  // Severity-based styling
  const severityStyles = {
    [ErrorSeverity.INFO]: {
      container: 'bg-blue-50 border-blue-200',
      icon: 'text-blue-600',
      title: 'text-blue-900',
      message: 'text-blue-700',
      iconPath: (
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      ),
    },
    [ErrorSeverity.WARNING]: {
      container: 'bg-yellow-50 border-yellow-200',
      icon: 'text-yellow-600',
      title: 'text-yellow-900',
      message: 'text-yellow-700',
      iconPath: (
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      ),
    },
    [ErrorSeverity.ERROR]: {
      container: 'bg-red-50 border-red-200',
      icon: 'text-red-600',
      title: 'text-red-900',
      message: 'text-red-700',
      iconPath: (
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      ),
    },
    [ErrorSeverity.CRITICAL]: {
      container: 'bg-red-100 border-red-300',
      icon: 'text-red-700',
      title: 'text-red-900',
      message: 'text-red-800',
      iconPath: (
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      ),
    },
  }

  const styles = severityStyles[severity]

  return (
    <div
      className={`max-w-md w-full ${styles.container} border rounded-lg shadow-lg p-4 transition-all duration-300 ease-in-out`}
      role="alert"
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg
            className={`h-6 w-6 ${styles.icon}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            {styles.iconPath}
          </svg>
        </div>

        <div className="ml-3 flex-1">
          <h3 className={`text-sm font-medium ${styles.title}`}>{title}</h3>
          <div className={`mt-1 text-sm ${styles.message}`}>
            <p>{message}</p>

            {/* Show detailed errors if available */}
            {details && details.length > 0 && (
              <ul className="mt-2 list-disc list-inside space-y-1">
                {details.map((detail, index) => (
                  <li key={index} className="text-xs">
                    {detail}
                  </li>
                ))}
              </ul>
            )}

            {/* Show suggestions if available */}
            {suggestions && suggestions.length > 0 && (
              <div className="mt-2">
                <p className="font-medium text-xs">Suggestions:</p>
                <ul className="mt-1 list-disc list-inside space-y-1">
                  {suggestions.map((suggestion, index) => (
                    <li key={index} className="text-xs">
                      {suggestion}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        <div className="ml-3 flex-shrink-0">
          <button
            onClick={onClose}
            className={`inline-flex rounded-md p-1.5 ${styles.message} hover:bg-opacity-20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent`}
          >
            <span className="sr-only">Dismiss</span>
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

/**
 * Error Toast Container for managing multiple toasts
 */
interface Toast {
  id: string
  error: unknown
}

interface ErrorToastContainerProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center'
}

export function ErrorToastContainer({
  position = 'top-right',
}: ErrorToastContainerProps) {
  const [toasts, setToasts] = React.useState<Toast[]>([])

  // Expose add toast function via context or custom event
  React.useEffect(() => {
    const handleAddToast = (event: CustomEvent<{ error: unknown }>) => {
      const toast: Toast = {
        id: Date.now().toString(),
        error: event.detail.error,
      }
      setToasts((prev) => [...prev, toast])
    }

    window.addEventListener('error-toast', handleAddToast as EventListener)
    return () => window.removeEventListener('error-toast', handleAddToast as EventListener)
  }, [])

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }

  const positionStyles = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-center': 'top-4 left-1/2 transform -translate-x-1/2',
  }

  return (
    <div
      className={`fixed ${positionStyles[position]} z-50 space-y-4 pointer-events-none`}
    >
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <ErrorToast error={toast.error} onClose={() => removeToast(toast.id)} />
        </div>
      ))}
    </div>
  )
}

/**
 * Function to show error toast
 */
export function showErrorToast(error: unknown): void {
  const event = new CustomEvent('error-toast', {
    detail: { error },
  })
  window.dispatchEvent(event)
}
