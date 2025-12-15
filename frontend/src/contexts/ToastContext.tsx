'use client'

import {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from 'react'
import {
  ToastContainer,
  ToastItem,
  ToastType,
  ToastPosition,
  ToastAction,
} from '@/components/Toast'
import { getErrorMessage } from '@/lib/errors'

// ============================================================================
// Types
// ============================================================================

interface ToastOptions {
  duration?: number
  persistent?: boolean
  action?: ToastAction
}

// Max number of toasts visible at once
const MAX_TOASTS = 3

interface ToastMethods {
  /**
   * Show a success toast notification
   * @returns The toast ID for manual dismissal
   */
  success: (message: string, options?: ToastOptions) => string

  /**
   * Show an error toast notification
   * Accepts an error object, ApiError, or string message
   * @returns The toast ID for manual dismissal
   */
  error: (error: unknown, options?: ToastOptions) => string

  /**
   * Show a warning toast notification
   * @returns The toast ID for manual dismissal
   */
  warning: (message: string, options?: ToastOptions) => string

  /**
   * Show an info toast notification
   * @returns The toast ID for manual dismissal
   */
  info: (message: string, options?: ToastOptions) => string

  /**
   * Dismiss a specific toast by ID
   */
  dismiss: (id: string) => void

  /**
   * Dismiss all toasts
   */
  dismissAll: () => void
}

interface ToastContextType {
  /**
   * Toast methods for showing and dismissing toasts
   */
  toast: ToastMethods

  /**
   * Legacy: Show a toast notification with specified type and message
   * @deprecated Use toast.success(), toast.error(), etc. instead
   * @returns The toast ID for manual dismissal
   */
  showToast: (type: ToastType, message: string, options?: ToastOptions) => string

  /**
   * Legacy: Show a success toast notification
   * @deprecated Use toast.success() instead
   * @returns The toast ID for manual dismissal
   */
  showSuccess: (message: string, options?: ToastOptions) => string

  /**
   * Legacy: Show an error toast notification
   * @deprecated Use toast.error() instead
   * @returns The toast ID for manual dismissal
   */
  showError: (error: unknown, options?: ToastOptions) => string

  /**
   * Legacy: Show a warning toast notification
   * @deprecated Use toast.warning() instead
   * @returns The toast ID for manual dismissal
   */
  showWarning: (message: string, options?: ToastOptions) => string

  /**
   * Legacy: Show an info toast notification
   * @deprecated Use toast.info() instead
   * @returns The toast ID for manual dismissal
   */
  showInfo: (message: string, options?: ToastOptions) => string

  /**
   * Legacy: Dismiss a specific toast by ID
   * @deprecated Use toast.dismiss() instead
   */
  dismissToast: (id: string) => void

  /**
   * Legacy: Dismiss all toasts
   * @deprecated Use toast.dismissAll() instead
   */
  dismissAll: () => void
}

// ============================================================================
// Context
// ============================================================================

const ToastContext = createContext<ToastContextType | undefined>(undefined)

// ============================================================================
// Provider
// ============================================================================

interface ToastProviderProps {
  children: ReactNode
}

/**
 * Toast provider that manages toast notifications throughout the app.
 * Wrap your app with this provider to enable toast functionality.
 *
 * Features:
 * - Queue management (max 3 toasts visible at once)
 * - Auto-dismiss with configurable duration
 * - Pause on hover
 * - Progress bar showing time until dismiss
 *
 * @example
 * ```tsx
 * // In providers.tsx
 * <ToastProvider>
 *   <App />
 * </ToastProvider>
 *
 * // In a component (new syntax)
 * const { toast } = useToast()
 * try {
 *   await createPerson(data)
 *   toast.success('Person created successfully')
 * } catch (error) {
 *   toast.error(error)
 * }
 *
 * // With options
 * toast.success('Saved!', {
 *   duration: 3000,
 *   action: { label: 'Undo', onClick: handleUndo }
 * })
 *
 * // Persistent toast (no auto-dismiss)
 * toast.warning('Important notice', { persistent: true })
 * ```
 */
export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  // Generate unique ID for each toast
  const generateId = useCallback(() => {
    return `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }, [])

  // Add a new toast with queue management
  const showToast = useCallback(
    (type: ToastType, message: string, options?: ToastOptions): string => {
      const id = generateId()
      const newToast: ToastItem = {
        id,
        type,
        message,
        duration: options?.duration,
        persistent: options?.persistent,
        action: options?.action,
      }

      setToasts((prev) => {
        // If we're at max capacity, remove the oldest toast
        const updatedToasts = prev.length >= MAX_TOASTS ? prev.slice(1) : prev
        return [...updatedToasts, newToast]
      })

      return id
    },
    [generateId]
  )

  // Show success toast
  const showSuccess = useCallback(
    (message: string, options?: ToastOptions): string => {
      return showToast('success', message, options)
    },
    [showToast]
  )

  // Show error toast - handles various error types
  const showError = useCallback(
    (error: unknown, options?: ToastOptions): string => {
      const message = getErrorMessage(error)
      return showToast('error', message, { duration: 7000, ...options })
    },
    [showToast]
  )

  // Show warning toast
  const showWarning = useCallback(
    (message: string, options?: ToastOptions): string => {
      return showToast('warning', message, options)
    },
    [showToast]
  )

  // Show info toast
  const showInfo = useCallback(
    (message: string, options?: ToastOptions): string => {
      return showToast('info', message, options)
    },
    [showToast]
  )

  // Dismiss a specific toast
  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  // Dismiss all toasts
  const dismissAll = useCallback(() => {
    setToasts([])
  }, [])

  // Create the toast methods object
  const toastMethods: ToastMethods = {
    success: showSuccess,
    error: showError,
    warning: showWarning,
    info: showInfo,
    dismiss: dismissToast,
    dismissAll,
  }

  const value: ToastContextType = {
    toast: toastMethods,
    // Legacy methods (deprecated but still available)
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    dismissToast,
    dismissAll,
  }

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </ToastContext.Provider>
  )
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Hook to access toast notification functions.
 * Must be used within a ToastProvider.
 *
 * @example
 * ```tsx
 * // New syntax (recommended)
 * const { toast } = useToast()
 *
 * // Basic usage
 * toast.success('Operation successful!')
 * toast.error('Something went wrong')
 * toast.warning('Please check your input')
 * toast.info('New features available')
 *
 * // With options
 * toast.success('Changes saved', {
 *   duration: 3000,
 *   action: { label: 'Undo', onClick: handleUndo }
 * })
 *
 * // Persistent toast (no auto-dismiss)
 * toast.warning('Server maintenance scheduled', { persistent: true })
 *
 * // Dismiss specific or all toasts
 * const id = toast.info('Processing...')
 * toast.dismiss(id)
 * toast.dismissAll()
 *
 * // Legacy syntax (still supported)
 * const { showSuccess, showError } = useToast()
 * showSuccess('Person created successfully')
 * showError(error)
 * ```
 */
export function useToast(): ToastContextType {
  const context = useContext(ToastContext)
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}
