'use client'

import { useEffect, useState } from 'react'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'

// ============================================================================
// Types
// ============================================================================

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface ToastProps {
  id: string
  type: ToastType
  message: string
  duration?: number
  onDismiss: (id: string) => void
}

// ============================================================================
// Toast Icons
// ============================================================================

const toastIcons: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle className="w-5 h-5" />,
  error: <AlertCircle className="w-5 h-5" />,
  warning: <AlertTriangle className="w-5 h-5" />,
  info: <Info className="w-5 h-5" />,
}

// ============================================================================
// Toast Styles
// ============================================================================

const toastStyles: Record<ToastType, { container: string; icon: string }> = {
  success: {
    container: 'bg-green-50 border-green-200 text-green-800',
    icon: 'text-green-500',
  },
  error: {
    container: 'bg-red-50 border-red-200 text-red-800',
    icon: 'text-red-500',
  },
  warning: {
    container: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    icon: 'text-yellow-500',
  },
  info: {
    container: 'bg-blue-50 border-blue-200 text-blue-800',
    icon: 'text-blue-500',
  },
}

// ============================================================================
// Toast Component
// ============================================================================

/**
 * Individual toast notification with auto-dismiss and manual dismiss.
 * Features slide-in animation from top-right.
 */
export function Toast({
  id,
  type,
  message,
  duration = 5000,
  onDismiss,
}: ToastProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [isLeaving, setIsLeaving] = useState(false)

  const styles = toastStyles[type]
  const icon = toastIcons[type]

  // Handle entrance animation
  useEffect(() => {
    // Trigger slide-in animation after mount
    const enterTimer = requestAnimationFrame(() => {
      setIsVisible(true)
    })

    return () => cancelAnimationFrame(enterTimer)
  }, [])

  // Handle auto-dismiss
  useEffect(() => {
    if (duration <= 0) return

    const dismissTimer = setTimeout(() => {
      handleDismiss()
    }, duration)

    return () => clearTimeout(dismissTimer)
  }, [duration])

  // Handle dismiss with exit animation
  const handleDismiss = () => {
    setIsLeaving(true)
    // Wait for animation to complete before removing
    setTimeout(() => {
      onDismiss(id)
    }, 300)
  }

  return (
    <div
      role="alert"
      aria-live="polite"
      className={`
        flex items-start gap-3 p-4 border rounded-lg shadow-lg
        transform transition-all duration-300 ease-out
        ${styles.container}
        ${isVisible && !isLeaving
          ? 'translate-x-0 opacity-100'
          : 'translate-x-full opacity-0'}
      `}
      style={{ minWidth: '320px', maxWidth: '420px' }}
    >
      {/* Icon */}
      <div className={`flex-shrink-0 ${styles.icon}`}>
        {icon}
      </div>

      {/* Message */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium break-words">{message}</p>
      </div>

      {/* Dismiss button */}
      <button
        onClick={handleDismiss}
        className={`
          flex-shrink-0 p-1 rounded
          hover:bg-black/5 transition-colors
          focus:outline-none focus:ring-2 focus:ring-offset-1
          ${type === 'success' ? 'focus:ring-green-500' : ''}
          ${type === 'error' ? 'focus:ring-red-500' : ''}
          ${type === 'warning' ? 'focus:ring-yellow-500' : ''}
          ${type === 'info' ? 'focus:ring-blue-500' : ''}
        `}
        aria-label="Dismiss notification"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

// ============================================================================
// Toast Container
// ============================================================================

export interface ToastItem {
  id: string
  type: ToastType
  message: string
  duration?: number
}

interface ToastContainerProps {
  toasts: ToastItem[]
  onDismiss: (id: string) => void
}

/**
 * Container for displaying toast notifications.
 * Positioned in the top-right corner of the viewport.
 */
export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  if (toasts.length === 0) return null

  return (
    <div
      className="fixed top-4 right-4 z-50 flex flex-col gap-2"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          id={toast.id}
          type={toast.type}
          message={toast.message}
          duration={toast.duration}
          onDismiss={onDismiss}
        />
      ))}
    </div>
  )
}
