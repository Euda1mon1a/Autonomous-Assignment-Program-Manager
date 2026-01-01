'use client'

import { useState, useCallback, useEffect, useRef, useId } from 'react'
import { ArrowLeftRight, X, Loader2, Check, Calendar, Clock } from 'lucide-react'
import { format } from 'date-fns'
import { motion, AnimatePresence } from 'framer-motion'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { post } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'

interface SwapRequestData {
  assignment_id: string
  reason?: string
  preferred_dates?: string[]
}

interface QuickSwapButtonProps {
  /** Assignment ID to request swap for */
  assignmentId: string
  /** Date of the assignment */
  date: string
  /** Time of day (AM/PM) */
  timeOfDay: 'AM' | 'PM'
  /** Activity type for display */
  activity: string
  /** Callback when swap is requested successfully */
  onSuccess?: () => void
  /** Callback when modal is closed */
  onClose?: () => void
  /** Size variant */
  size?: 'sm' | 'md'
  /** Additional CSS classes */
  className?: string
}

/**
 * Quick Swap Request Button
 *
 * Allows residents to quickly request a swap for a specific assignment.
 * Opens a compact modal to add swap details and submit the request.
 */
export function QuickSwapButton({
  assignmentId,
  date,
  timeOfDay,
  activity,
  onSuccess,
  onClose,
  size = 'sm',
  className = '',
}: QuickSwapButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [reason, setReason] = useState('')
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const modalRef = useRef<HTMLDivElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const titleId = useId()
  const descId = useId()

  const swapMutation = useMutation({
    mutationFn: async (data: SwapRequestData) => {
      return post('/swaps/request', data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['swap-requests'] })
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
      setIsOpen(false)
      setReason('')
      onSuccess?.()
    },
  })

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      swapMutation.mutate({
        assignment_id: assignmentId,
        reason: reason || undefined,
      })
    },
    [assignmentId, reason, swapMutation]
  )

  const handleClose = useCallback(() => {
    setIsOpen(false)
    setReason('')
    onClose?.()
  }, [onClose])

  // Focus management and keyboard handling
  useEffect(() => {
    if (isOpen) {
      // Focus close button when modal opens
      closeButtonRef.current?.focus()

      // Prevent body scroll
      document.body.style.overflow = 'hidden'

      // Handle Escape key
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape' && !swapMutation.isPending) {
          handleClose()
        }
      }

      document.addEventListener('keydown', handleEscape)

      return () => {
        document.body.style.overflow = 'unset'
        document.removeEventListener('keydown', handleEscape)
      }
    }
  }, [isOpen, handleClose, swapMutation.isPending])

  const sizeClasses = {
    sm: 'p-1.5 text-xs',
    md: 'p-2 text-sm',
  }

  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'

  return (
    <>
      <button
        onClick={(e) => {
          e.stopPropagation()
          setIsOpen(true)
        }}
        className={`
          inline-flex items-center gap-1 rounded-md
          bg-blue-50 text-blue-700 border border-blue-200
          hover:bg-blue-100 hover:border-blue-300
          transition-colors
          ${sizeClasses[size]}
          ${className}
        `}
        aria-label="Request swap for this assignment"
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            e.stopPropagation()
            setIsOpen(true)
          }
        }}
      >
        <ArrowLeftRight className={iconSize} aria-hidden="true" />
        {size === 'md' && <span>Swap</span>}
      </button>

      {/* Swap Request Modal */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50"
              onClick={handleClose}
              aria-hidden="true"
            />

            {/* Modal */}
            <motion.div
              ref={modalRef}
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
              role="dialog"
              aria-modal="true"
              aria-labelledby={titleId}
              aria-describedby={descId}
            >
              <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-100">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg" aria-hidden="true">
                      <ArrowLeftRight className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h3 id={titleId} className="font-semibold text-gray-900">Request Swap</h3>
                      <p className="text-sm text-gray-500">Find someone to cover this shift</p>
                    </div>
                  </div>
                  <button
                    ref={closeButtonRef}
                    onClick={handleClose}
                    className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
                    aria-label="Close swap request dialog"
                  >
                    <X className="w-5 h-5 text-gray-500" aria-hidden="true" />
                  </button>
                </div>

                {/* Assignment Details */}
                <div id={descId} className="p-4 bg-gray-50 border-b border-gray-100">
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-2 text-gray-600">
                      <Calendar className="w-4 h-4" aria-hidden="true" />
                      <span className="font-medium">
                        {format(new Date(date), 'EEE, MMM d, yyyy')}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-600">
                      <Clock className="w-4 h-4" aria-hidden="true" />
                      <span>{timeOfDay}</span>
                    </div>
                    <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium capitalize">
                      {activity}
                    </span>
                  </div>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-4 space-y-4">
                  <div>
                    <label
                      htmlFor="swap-reason"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Reason (optional)
                    </label>
                    <textarea
                      id="swap-reason"
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      placeholder="e.g., Family commitment, conference attendance..."
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                        focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                        placeholder:text-gray-400"
                    />
                  </div>

                  {/* Error Message */}
                  {swapMutation.isError && (
                    <div
                      className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
                      role="alert"
                      aria-live="assertive"
                    >
                      Failed to submit swap request. Please try again.
                    </div>
                  )}

                  {/* Success Message */}
                  {swapMutation.isSuccess && (
                    <div
                      className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700 flex items-center gap-2"
                      role="status"
                      aria-live="polite"
                    >
                      <Check className="w-4 h-4" aria-hidden="true" />
                      Swap request submitted successfully!
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-3 pt-2">
                    <button
                      type="button"
                      onClick={handleClose}
                      className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg
                        hover:bg-gray-50 transition-colors text-sm font-medium"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={swapMutation.isPending || swapMutation.isSuccess}
                      className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg
                        hover:bg-blue-700 transition-colors text-sm font-medium
                        disabled:opacity-50 disabled:cursor-not-allowed
                        flex items-center justify-center gap-2"
                    >
                      {swapMutation.isPending ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Submitting...
                        </>
                      ) : swapMutation.isSuccess ? (
                        <>
                          <Check className="w-4 h-4" />
                          Submitted
                        </>
                      ) : (
                        <>
                          <ArrowLeftRight className="w-4 h-4" />
                          Submit Request
                        </>
                      )}
                    </button>
                  </div>
                </form>

                {/* Footer Note */}
                <div className="px-4 pb-4">
                  <p className="text-xs text-gray-500 text-center">
                    Your request will be posted to the swap marketplace for others to accept.
                  </p>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}

/**
 * Inline swap request link for use in lists
 */
export function QuickSwapLink({
  assignmentId,
  date,
  timeOfDay,
  activity,
  onSuccess,
}: Omit<QuickSwapButtonProps, 'size' | 'className'>) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <button
        onClick={(e) => {
          e.stopPropagation()
          setIsOpen(true)
        }}
        className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
      >
        <ArrowLeftRight className="w-3.5 h-3.5" />
        Request Swap
      </button>

      {isOpen && (
        <QuickSwapButton
          assignmentId={assignmentId}
          date={date}
          timeOfDay={timeOfDay}
          activity={activity}
          onSuccess={() => {
            setIsOpen(false)
            onSuccess?.()
          }}
          onClose={() => setIsOpen(false)}
        />
      )}
    </>
  )
}
