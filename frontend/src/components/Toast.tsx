'use client'

import { useEffect, useState, useRef } from 'react'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'

// ============================================================================
// Types
// ============================================================================

export type ToastType = 'success' | 'error' | 'warning' | 'info'
export type ToastPosition = 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'

export interface ToastAction {
  label: string
  onClick: () => void
}

export interface ToastProps {
  id: string
  type: ToastType
  message: string
  duration?: number
  persistent?: boolean
  action?: ToastAction
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
 * Features slide-in animation from top-right, progress bar, and pause on hover.
 */
export function Toast({
  id,
  type,
  message,
  duration = 5000,
  persistent = false,
  action,
  onDismiss,
}: ToastProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [isLeaving, setIsLeaving] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [progress, setProgress] = useState(100)
  const dismissTimerRef = useRef<NodeJS.Timeout>()
  const progressIntervalRef = useRef<NodeJS.Timeout>()
  const startTimeRef = useRef<number>(Date.now())
  const remainingTimeRef = useRef<number>(duration)

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

  // Handle auto-dismiss with pause functionality
  useEffect(() => {
    if (persistent || duration <= 0) return

    const startDismissTimer = () => {
      startTimeRef.current = Date.now()

      // Update progress bar
      progressIntervalRef.current = setInterval(() => {
        const elapsed = Date.now() - startTimeRef.current
        const remaining = Math.max(0, remainingTimeRef.current - elapsed)
        const newProgress = (remaining / duration) * 100
        setProgress(newProgress)

        if (remaining <= 0) {
          clearInterval(progressIntervalRef.current)
        }
      }, 16) // ~60fps

      // Auto-dismiss timer
      dismissTimerRef.current = setTimeout(() => {
        handleDismiss()
      }, remainingTimeRef.current)
    }

    if (!isPaused) {
      startDismissTimer()
    }

    return () => {
      if (dismissTimerRef.current) {
        clearTimeout(dismissTimerRef.current)
      }
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
      }
    }
  }, [duration, isPaused, persistent])

  // Handle pause
  const handleMouseEnter = () => {
    if (persistent || duration <= 0) return

    setIsPaused(true)

    // Calculate remaining time
    const elapsed = Date.now() - startTimeRef.current
    remainingTimeRef.current = Math.max(0, remainingTimeRef.current - elapsed)

    // Clear timers
    if (dismissTimerRef.current) {
      clearTimeout(dismissTimerRef.current)
    }
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current)
    }
  }

  const handleMouseLeave = () => {
    if (persistent || duration <= 0) return
    setIsPaused(false)
  }

  // Handle dismiss with exit animation
  const handleDismiss = () => {
    setIsLeaving(true)
    // Wait for animation to complete before removing
    setTimeout(() => {
      onDismiss(id)
    }, 300)
  }

  // Handle action button click
  const handleActionClick = () => {
    if (action?.onClick) {
      action.onClick()
      handleDismiss()
    }
  }

  return (
    <div
      role="alert"
      aria-live="polite"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`
        relative overflow-hidden
        flex flex-col gap-2 p-4 border rounded-lg shadow-lg
        transform transition-all duration-300 ease-out
        ${styles.container}
        ${isVisible && !isLeaving
          ? 'translate-x-0 opacity-100'
          : 'translate-x-full opacity-0'}
      `}
      style={{ minWidth: '320px', maxWidth: '420px' }}
    >
      {/* Progress bar */}
      {!persistent && duration > 0 && (
        <div
          className={`
            absolute bottom-0 left-0 h-1 transition-all duration-100 ease-linear
            ${type === 'success' ? 'bg-green-500' : ''}
            ${type === 'error' ? 'bg-red-500' : ''}
            ${type === 'warning' ? 'bg-yellow-500' : ''}
            ${type === 'info' ? 'bg-blue-500' : ''}
          `}
          style={{ width: `${progress}%` }}
        />
      )}

      {/* Main content */}
      <div className="flex items-start gap-3">
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

      {/* Action button */}
      {action && (
        <div className="flex justify-end pl-8">
          <button
            onClick={handleActionClick}
            className={`
              px-3 py-1.5 text-sm font-medium rounded
              transition-colors
              focus:outline-none focus:ring-2 focus:ring-offset-1
              ${type === 'success' ? 'text-green-700 hover:bg-green-100 focus:ring-green-500' : ''}
              ${type === 'error' ? 'text-red-700 hover:bg-red-100 focus:ring-red-500' : ''}
              ${type === 'warning' ? 'text-yellow-700 hover:bg-yellow-100 focus:ring-yellow-500' : ''}
              ${type === 'info' ? 'text-blue-700 hover:bg-blue-100 focus:ring-blue-500' : ''}
            `}
          >
            {action.label}
          </button>
        </div>
      )}
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
  persistent?: boolean
  action?: ToastAction
}

interface ToastContainerProps {
  toasts: ToastItem[]
  position?: ToastPosition
  onDismiss: (id: string) => void
}

const positionClasses: Record<ToastPosition, string> = {
  'top-right': 'top-4 right-4',
  'top-left': 'top-4 left-4',
  'bottom-right': 'bottom-4 right-4',
  'bottom-left': 'bottom-4 left-4',
}

/**
 * Container for displaying toast notifications.
 * Positioned based on the position prop (default: top-right).
 */
export function ToastContainer({
  toasts,
  position = 'top-right',
  onDismiss
}: ToastContainerProps) {
  if (toasts.length === 0) return null

  return (
    <div
      className={`fixed ${positionClasses[position]} z-50 flex flex-col gap-3`}
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          id={toast.id}
          type={toast.type}
          message={toast.message}
          duration={toast.duration}
          persistent={toast.persistent}
          action={toast.action}
          onDismiss={onDismiss}
        />
      ))}
    </div>
  )
}
