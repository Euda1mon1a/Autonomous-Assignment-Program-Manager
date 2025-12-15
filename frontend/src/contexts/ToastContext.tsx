'use client'

import {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from 'react'
import { ToastContainer, ToastItem, ToastType } from '@/components/Toast'
import { getErrorMessage } from '@/lib/errors'

// ============================================================================
// Types
// ============================================================================

interface ToastOptions {
  duration?: number
}

interface ToastContextType {
  /**
   * Show a toast notification with specified type and message
   */
  showToast: (type: ToastType, message: string, options?: ToastOptions) => void

  /**
   * Show a success toast notification
   */
  showSuccess: (message: string, options?: ToastOptions) => void

  /**
   * Show an error toast notification
   * Accepts an error object, ApiError, or string message
   */
  showError: (error: unknown, options?: ToastOptions) => void

  /**
   * Show a warning toast notification
   */
  showWarning: (message: string, options?: ToastOptions) => void

  /**
   * Show an info toast notification
   */
  showInfo: (message: string, options?: ToastOptions) => void

  /**
   * Dismiss a specific toast by ID
   */
  dismissToast: (id: string) => void

  /**
   * Dismiss all toasts
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
 * @example
 * ```tsx
 * // In providers.tsx
 * <ToastProvider>
 *   <App />
 * </ToastProvider>
 *
 * // In a component
 * const { showSuccess, showError } = useToast()
 * try {
 *   await createPerson(data)
 *   showSuccess('Person created successfully')
 * } catch (error) {
 *   showError(error)
 * }
 * ```
 */
export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  // Generate unique ID for each toast
  const generateId = useCallback(() => {
    return `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }, [])

  // Add a new toast
  const showToast = useCallback(
    (type: ToastType, message: string, options?: ToastOptions) => {
      const id = generateId()
      const newToast: ToastItem = {
        id,
        type,
        message,
        duration: options?.duration,
      }

      setToasts((prev) => [...prev, newToast])
    },
    [generateId]
  )

  // Show success toast
  const showSuccess = useCallback(
    (message: string, options?: ToastOptions) => {
      showToast('success', message, options)
    },
    [showToast]
  )

  // Show error toast - handles various error types
  const showError = useCallback(
    (error: unknown, options?: ToastOptions) => {
      const message = getErrorMessage(error)
      showToast('error', message, { duration: 7000, ...options })
    },
    [showToast]
  )

  // Show warning toast
  const showWarning = useCallback(
    (message: string, options?: ToastOptions) => {
      showToast('warning', message, options)
    },
    [showToast]
  )

  // Show info toast
  const showInfo = useCallback(
    (message: string, options?: ToastOptions) => {
      showToast('info', message, options)
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

  const value: ToastContextType = {
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
 * const { showSuccess, showError } = useToast()
 *
 * const handleSubmit = async () => {
 *   try {
 *     await createPerson(data)
 *     showSuccess('Person created successfully')
 *   } catch (error) {
 *     showError(error)
 *   }
 * }
 * ```
 */
export function useToast(): ToastContextType {
  const context = useContext(ToastContext)
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}
