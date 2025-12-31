/**
 * Error handling utilities for the frontend.
 *
 * Centralized error handling with TypeScript types, error boundary,
 * toast notifications, and error messages.
 *
 * @example
 * ```tsx
 * import {
 *   ErrorBoundary,
 *   ErrorToastContainer,
 *   showErrorToast,
 *   useErrorHandler,
 * } from '@/lib/errors'
 *
 * // In your app root
 * <ErrorBoundary>
 *   <ErrorToastContainer />
 *   <YourApp />
 * </ErrorBoundary>
 *
 * // In a component
 * const { handleError, getUserMessage } = useErrorHandler()
 *
 * try {
 *   await someApiCall()
 * } catch (error) {
 *   handleError(error)
 *   showErrorToast(error)
 * }
 * ```
 */

// Error types
export * from './error-types'

// Error messages
export * from './error-messages'

// Error handler
export * from './error-handler'

// React components
export * from './error-boundary'
export * from './error-toast'
