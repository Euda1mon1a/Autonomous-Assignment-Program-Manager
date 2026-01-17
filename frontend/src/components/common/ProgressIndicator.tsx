'use client'

import { useState, useEffect, useMemo } from 'react'
import { Loader2, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react'
import { motion } from 'framer-motion'

type ProgressStatus = 'idle' | 'pending' | 'running' | 'success' | 'error' | 'warning'

interface ProgressStep {
  id: string
  label: string
  status: ProgressStatus
  detail?: string
}

interface ProgressIndicatorProps {
  /** Current progress percentage (0-100) */
  progress?: number
  /** Current status of the operation */
  status: ProgressStatus
  /** Main message to display */
  message: string
  /** Detailed description or current step */
  detail?: string
  /** Show estimated time remaining */
  estimatedTimeRemaining?: number // in seconds
  /** Show elapsed time */
  showElapsedTime?: boolean
  /** Start time for elapsed calculation */
  startTime?: Date
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Show as inline or card */
  variant?: 'inline' | 'card' | 'fullscreen'
  /** Additional CSS classes */
  className?: string
}

/**
 * Progress Indicator Component
 *
 * Shows progress for long-running operations with status, progress bar,
 * time estimates, and step details.
 */
export function ProgressIndicator({
  progress,
  status,
  message,
  detail,
  estimatedTimeRemaining,
  showElapsedTime = false,
  startTime,
  size = 'md',
  variant = 'card',
  className = '',
}: ProgressIndicatorProps) {
  const [elapsed, setElapsed] = useState(0)

  // Update elapsed time
  useEffect(() => {
    if (!showElapsedTime || !startTime || status !== 'running') return

    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime.getTime()) / 1000))
    }, 1000)

    return () => clearInterval(interval)
  }, [showElapsedTime, startTime, status])

  const statusConfig = {
    idle: { icon: Clock, color: 'text-gray-400', bgColor: 'bg-gray-100' },
    pending: { icon: Clock, color: 'text-blue-500', bgColor: 'bg-blue-50' },
    running: { icon: Loader2, color: 'text-blue-600', bgColor: 'bg-blue-50', animate: true },
    success: { icon: CheckCircle, color: 'text-green-600', bgColor: 'bg-green-50' },
    error: { icon: XCircle, color: 'text-red-600', bgColor: 'bg-red-50' },
    warning: { icon: AlertTriangle, color: 'text-amber-600', bgColor: 'bg-amber-50' },
  }

  const config = statusConfig[status]
  const Icon = config.icon

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    if (mins < 60) return `${mins}m ${secs}s`
    const hours = Math.floor(mins / 60)
    const remainingMins = mins % 60
    return `${hours}h ${remainingMins}m`
  }

  const sizeClasses = {
    sm: 'p-3 text-sm',
    md: 'p-4 text-base',
    lg: 'p-6 text-lg',
  }

  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  }

  if (variant === 'inline') {
    return (
      <div className={`flex items-center gap-3 ${className}`}>
        <Icon
          className={`${iconSizes[size]} ${config.color} ${'animate' in config && config.animate ? 'animate-spin' : ''}`}
        />
        <span className="text-gray-700">{message}</span>
        {progress !== undefined && (
          <span className="text-gray-500 tabular-nums">{Math.round(progress)}%</span>
        )}
      </div>
    )
  }

  if (variant === 'fullscreen') {
    return (
      <div className="fixed inset-0 bg-white/80 backdrop-blur-sm z-50 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-2xl shadow-2xl border border-gray-200 p-8 max-w-md w-full mx-4 text-center"
        >
          <div
            className={`w-16 h-16 rounded-full ${config.bgColor} flex items-center justify-center mx-auto mb-6`}
          >
            <Icon
              className={`w-8 h-8 ${config.color} ${'animate' in config && config.animate ? 'animate-spin' : ''}`}
            />
          </div>

          <h3 className="text-xl font-semibold text-gray-900 mb-2">{message}</h3>
          {detail && <p className="text-gray-500 mb-6">{detail}</p>}

          {progress !== undefined && (
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-500 mb-1">
                <span>Progress</span>
                <span className="tabular-nums">{Math.round(progress)}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.3 }}
                  className={`h-full ${
                    status === 'error'
                      ? 'bg-red-500'
                      : status === 'success'
                        ? 'bg-green-500'
                        : 'bg-blue-600'
                  }`}
                />
              </div>
            </div>
          )}

          <div className="flex justify-center gap-6 text-sm text-gray-500">
            {showElapsedTime && elapsed > 0 && (
              <div>
                <span className="text-gray-400">Elapsed:</span>{' '}
                <span className="font-medium tabular-nums">{formatTime(elapsed)}</span>
              </div>
            )}
            {estimatedTimeRemaining !== undefined && estimatedTimeRemaining > 0 && (
              <div>
                <span className="text-gray-400">Remaining:</span>{' '}
                <span className="font-medium tabular-nums">
                  ~{formatTime(estimatedTimeRemaining)}
                </span>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    )
  }

  // Card variant (default)
  return (
    <div
      className={`rounded-lg border ${config.bgColor} border-opacity-50 ${sizeClasses[size]} ${className}`}
    >
      <div className="flex items-start gap-3">
        <Icon
          className={`${iconSizes[size]} ${config.color} flex-shrink-0 mt-0.5 ${'animate' in config && config.animate ? 'animate-spin' : ''}`}
        />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900">{message}</p>
          {detail && <p className="text-gray-500 text-sm mt-0.5">{detail}</p>}

          {progress !== undefined && (
            <div className="mt-3">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Progress</span>
                <span className="tabular-nums">{Math.round(progress)}%</span>
              </div>
              <div className="h-1.5 bg-white/50 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.3 }}
                  className={`h-full ${
                    status === 'error'
                      ? 'bg-red-500'
                      : status === 'success'
                        ? 'bg-green-500'
                        : 'bg-blue-600'
                  }`}
                />
              </div>
            </div>
          )}

          {(showElapsedTime || estimatedTimeRemaining !== undefined) && (
            <div className="flex gap-4 mt-2 text-xs text-gray-500">
              {showElapsedTime && elapsed > 0 && (
                <span>
                  Elapsed: <span className="tabular-nums">{formatTime(elapsed)}</span>
                </span>
              )}
              {estimatedTimeRemaining !== undefined && estimatedTimeRemaining > 0 && (
                <span>
                  ~<span className="tabular-nums">{formatTime(estimatedTimeRemaining)}</span>{' '}
                  remaining
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * Multi-step Progress Indicator
 *
 * Shows progress through multiple steps of an operation.
 */
export function StepProgressIndicator({
  steps,
  currentStepIndex,
  className = '',
}: {
  steps: ProgressStep[]
  currentStepIndex: number
  className?: string
}) {
  return (
    <div className={`space-y-3 ${className}`}>
      {steps.map((step, index) => {
        const isActive = index === currentStepIndex
        const isComplete = index < currentStepIndex || step.status === 'success'
        const isError = step.status === 'error'

        return (
          <div key={step.id} className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium transition-colors ${
                  isComplete
                    ? 'bg-green-500 text-white'
                    : isError
                      ? 'bg-red-500 text-white'
                      : isActive
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-500'
                }`}
              >
                {isComplete ? (
                  <CheckCircle className="w-4 h-4" />
                ) : isError ? (
                  <XCircle className="w-4 h-4" />
                ) : isActive ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  index + 1
                )}
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`w-0.5 h-8 ${
                    isComplete ? 'bg-green-500' : 'bg-gray-200'
                  } transition-colors`}
                />
              )}
            </div>
            <div className="flex-1 pt-0.5">
              <p
                className={`text-sm font-medium ${
                  isComplete
                    ? 'text-green-700'
                    : isError
                      ? 'text-red-700'
                      : isActive
                        ? 'text-gray-900'
                        : 'text-gray-500'
                }`}
              >
                {step.label}
              </p>
              {step.detail && (
                <p className="text-xs text-gray-500 mt-0.5">{step.detail}</p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

/**
 * Hook for managing operation progress
 */
export function useProgress(totalSteps?: number) {
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState<ProgressStatus>('idle')
  const [message, setMessage] = useState('')
  const [detail, setDetail] = useState<string>()
  const [startTime, setStartTime] = useState<Date>()
  const [currentStep, setCurrentStep] = useState(0)

  const start = (initialMessage: string) => {
    setProgress(0)
    setStatus('running')
    setMessage(initialMessage)
    setStartTime(new Date())
    setCurrentStep(0)
  }

  const updateProgress = (value: number, newMessage?: string, newDetail?: string) => {
    setProgress(Math.min(100, Math.max(0, value)))
    if (newMessage) setMessage(newMessage)
    if (newDetail !== undefined) setDetail(newDetail)
  }

  const nextStep = (stepMessage?: string) => {
    if (totalSteps) {
      const newStep = currentStep + 1
      setCurrentStep(newStep)
      setProgress((newStep / totalSteps) * 100)
      if (stepMessage) setMessage(stepMessage)
    }
  }

  const complete = (finalMessage?: string) => {
    setProgress(100)
    setStatus('success')
    if (finalMessage) setMessage(finalMessage)
  }

  const error = (errorMessage: string, errorDetail?: string) => {
    setStatus('error')
    setMessage(errorMessage)
    if (errorDetail) setDetail(errorDetail)
  }

  const reset = () => {
    setProgress(0)
    setStatus('idle')
    setMessage('')
    setDetail(undefined)
    setStartTime(undefined)
    setCurrentStep(0)
  }

  const estimatedTimeRemaining = useMemo(() => {
    if (!startTime || progress <= 0 || status !== 'running') return undefined

    const elapsed = (Date.now() - startTime.getTime()) / 1000
    const estimatedTotal = elapsed / (progress / 100)
    const remaining = estimatedTotal - elapsed

    return Math.max(0, Math.round(remaining))
  }, [startTime, progress, status])

  return {
    progress,
    status,
    message,
    detail,
    startTime,
    currentStep,
    estimatedTimeRemaining,
    start,
    updateProgress,
    nextStep,
    complete,
    error,
    reset,
  }
}
