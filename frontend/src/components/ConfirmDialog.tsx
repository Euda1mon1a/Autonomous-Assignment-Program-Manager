'use client'

import { useEffect, useRef, useId } from 'react'
import { AlertTriangle, Trash2, X } from 'lucide-react'

interface ConfirmDialogProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'warning' | 'default'
  isLoading?: boolean
}

/**
 * A user-friendly confirmation dialog to replace browser confirm().
 *
 * Usage:
 * ```tsx
 * const [showConfirm, setShowConfirm] = useState(false)
 * const [itemToDelete, setItemToDelete] = useState<string | null>(null)
 *
 * const handleDeleteClick = (id: string) => {
 *   setItemToDelete(id)
 *   setShowConfirm(true)
 * }
 *
 * const handleConfirmDelete = () => {
 *   if (itemToDelete) {
 *     deleteItem(itemToDelete)
 *   }
 *   setShowConfirm(false)
 *   setItemToDelete(null)
 * }
 *
 * <ConfirmDialog
 *   isOpen={showConfirm}
 *   onClose={() => setShowConfirm(false)}
 *   onConfirm={handleConfirmDelete}
 *   title="Delete Item"
 *   message="Are you sure you want to delete this item? This cannot be undone."
 *   variant="danger"
 * />
 * ```
 */
export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  isLoading = false,
}: ConfirmDialogProps) {
  const modalRef = useRef<HTMLDivElement>(null)
  const cancelButtonRef = useRef<HTMLButtonElement>(null)
  const titleId = useId()
  const descId = useId()

  // Focus cancel button when dialog opens (safer default)
  useEffect(() => {
    if (isOpen && cancelButtonRef.current) {
      cancelButtonRef.current.focus()
    }
  }, [isOpen])

  // Handle escape key and body scroll
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isLoading) {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose, isLoading])

  if (!isOpen) return null

  const iconColors = {
    danger: 'text-red-600 bg-red-100',
    warning: 'text-amber-600 bg-amber-100',
    default: 'text-blue-600 bg-blue-100',
  }

  const buttonColors = {
    danger: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',
    warning: 'bg-amber-600 hover:bg-amber-700 focus:ring-amber-500',
    default: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
  }

  const Icon = variant === 'danger' ? Trash2 : AlertTriangle

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={isLoading ? undefined : onClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        ref={modalRef}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descId}
        className="relative bg-white rounded-lg shadow-xl w-full max-w-sm mx-auto"
      >
        {/* Close button */}
        <button
          onClick={onClose}
          disabled={isLoading}
          className="absolute top-3 right-3 p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="p-6">
          {/* Icon */}
          <div className="flex justify-center mb-4">
            <div className={`p-3 rounded-full ${iconColors[variant]}`}>
              <Icon className="w-6 h-6" />
            </div>
          </div>

          {/* Title */}
          <h2
            id={titleId}
            className="text-lg font-semibold text-gray-900 text-center mb-2"
          >
            {title}
          </h2>

          {/* Message */}
          <p
            id={descId}
            className="text-sm text-gray-600 text-center mb-6"
          >
            {message}
          </p>

          {/* Buttons */}
          <div className="flex gap-3">
            <button
              ref={cancelButtonRef}
              onClick={onClose}
              disabled={isLoading}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors disabled:opacity-50"
            >
              {cancelLabel}
            </button>
            <button
              onClick={onConfirm}
              disabled={isLoading}
              className={`flex-1 px-4 py-2 text-sm font-medium text-white rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 ${buttonColors[variant]}`}
            >
              {isLoading ? 'Please wait...' : confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
