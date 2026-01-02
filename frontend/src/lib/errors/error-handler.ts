/**
 * Global error handler for the application.
 *
 * Provides centralized error handling, logging, and reporting functionality.
 */

import {
  ErrorCode,
  ErrorResponse,
  ErrorSeverity,
  getErrorSeverity,
  isRFC7807Error,
  isValidationError,
  isACGMEComplianceError,
  isScheduleConflictError,
  isRateLimitError,
} from './error-types'
import { getErrorMessage } from './error-messages'

/**
 * Error handling configuration
 */
interface ErrorHandlerConfig {
  enableLogging: boolean
  enableReporting: boolean
  onError?: (error: ErrorResponse | Error) => void
}

/**
 * Global error handler class
 */
class GlobalErrorHandler {
  private config: ErrorHandlerConfig = {
    enableLogging: true,
    enableReporting: false,
  }

  /**
   * Configure the error handler
   */
  configure(config: Partial<ErrorHandlerConfig>): void {
    this.config = { ...this.config, ...config }
  }

  /**
   * Handle an error
   */
  handle(error: unknown, context?: Record<string, unknown>): ErrorResponse | Error {
    // Convert unknown error to structured format
    const structuredError = this.normalizeError(error)

    // Log error if enabled
    if (this.config.enableLogging) {
      this.logError(structuredError, context)
    }

    // Report error if enabled
    if (this.config.enableReporting) {
      this.reportError(structuredError, context)
    }

    // Call custom error handler if configured
    if (this.config.onError) {
      this.config.onError(structuredError)
    }

    return structuredError
  }

  /**
   * Normalize error to structured format
   */
  private normalizeError(error: unknown): ErrorResponse | Error {
    // Already an RFC 7807 error
    if (isRFC7807Error(error)) {
      return error
    }

    // Standard Error object
    if (error instanceof Error) {
      return error
    }

    // Unknown error type
    return new Error(String(error))
  }

  /**
   * Log error to console
   */
  private logError(error: ErrorResponse | Error, context?: Record<string, unknown>): void {
    const severity = this.getErrorSeverityForLogging(error)

    const logData = {
      error: error instanceof Error ? error.message : error.detail,
      errorCode: isRFC7807Error(error) ? error.error_code : 'UNKNOWN',
      status: isRFC7807Error(error) ? error.status : undefined,
      context,
      timestamp: new Date().toISOString(),
    }

    switch (severity) {
      case ErrorSeverity.CRITICAL:
        // console.error('[CRITICAL]', logData, error)
        break
      case ErrorSeverity.ERROR:
        // console.error('[ERROR]', logData, error)
        break
      case ErrorSeverity.WARNING:
        // console.warn('[WARNING]', logData, error)
        break
      case ErrorSeverity.INFO:
        console.info('[INFO]', logData, error)
        break
    }
  }

  /**
   * Get severity for logging
   */
  private getErrorSeverityForLogging(error: ErrorResponse | Error): ErrorSeverity {
    if (isRFC7807Error(error)) {
      return getErrorSeverity(error.status)
    }
    return ErrorSeverity.ERROR
  }

  /**
   * Report error to external service (e.g., Sentry)
   */
  private reportError(
    error: ErrorResponse | Error,
    context?: Record<string, unknown>
  ): void {
    // Only report critical and error severity
    const severity = this.getErrorSeverityForLogging(error)
    if (severity !== ErrorSeverity.CRITICAL && severity !== ErrorSeverity.ERROR) {
      return
    }

    // TODO: Integrate with error reporting service (e.g., Sentry)
    // For now, just log that we would report
    if (process.env.NODE_ENV === 'development') {
      console.debug('[ERROR REPORTING]', 'Would report error to external service', {
        error,
        context,
      })
    }
  }

  /**
   * Get user-friendly error message
   */
  getUserMessage(error: unknown): string {
    return getErrorMessage(error)
  }

  /**
   * Check if error should trigger re-authentication
   */
  shouldReauthenticate(error: unknown): boolean {
    if (!isRFC7807Error(error)) {
      return false
    }

    return (
      error.error_code === ErrorCode.TOKEN_EXPIRED ||
      error.error_code === ErrorCode.INVALID_TOKEN ||
      error.error_code === ErrorCode.TOKEN_REVOKED ||
      error.error_code === ErrorCode.UNAUTHORIZED
    )
  }

  /**
   * Check if error is retryable
   */
  isRetryable(error: unknown): boolean {
    if (!isRFC7807Error(error)) {
      return false
    }

    // Retryable error codes
    const retryableErrors = [
      ErrorCode.DATABASE_TIMEOUT,
      ErrorCode.SERVICE_TIMEOUT,
      ErrorCode.SERVICE_UNAVAILABLE,
      ErrorCode.DATABASE_CONNECTION_ERROR,
    ]

    return retryableErrors.includes(error.error_code)
  }

  /**
   * Get retry delay for rate limit errors
   */
  getRetryDelay(error: unknown): number | null {
    if (!isRateLimitError(error)) {
      return null
    }

    return error.retry_after * 1000 // Convert to milliseconds
  }

  /**
   * Extract validation errors
   */
  getValidationErrors(error: unknown): Array<{ field: string; message: string }> {
    if (!isValidationError(error)) {
      return []
    }

    return error.errors.map((err) => ({
      field: err.field,
      message: err.message,
    }))
  }

  /**
   * Extract ACGME violation details
   */
  getACGMEViolationDetails(error: unknown) {
    if (!isACGMEComplianceError(error)) {
      return null
    }

    return error.violation
  }

  /**
   * Extract schedule conflict details
   */
  getScheduleConflictDetails(error: unknown) {
    if (!isScheduleConflictError(error)) {
      return null
    }

    return error.conflict
  }
}

// Export singleton instance
export const errorHandler = new GlobalErrorHandler()

/**
 * Hook-style error handler for React components
 */
export function useErrorHandler(): {
  handleError: (error: unknown, context?: Record<string, unknown>) => void;
  getUserMessage: (error: unknown) => string;
  shouldReauthenticate: (error: unknown) => boolean;
  isRetryable: (error: unknown) => boolean;
  getRetryDelay: (error: unknown) => number | null;
  getValidationErrors: (error: unknown) => Array<{ field: string; message: string }>;
  getACGMEViolationDetails: (error: unknown) => unknown | null;
  getScheduleConflictDetails: (error: unknown) => unknown | null;
} {
  const handleError = (error: unknown, context?: Record<string, unknown>): void => {
    errorHandler.handle(error, context)
  }

  return {
    handleError,
    getUserMessage: errorHandler.getUserMessage.bind(errorHandler),
    shouldReauthenticate: errorHandler.shouldReauthenticate.bind(errorHandler),
    isRetryable: errorHandler.isRetryable.bind(errorHandler),
    getRetryDelay: errorHandler.getRetryDelay.bind(errorHandler),
    getValidationErrors: errorHandler.getValidationErrors.bind(errorHandler),
    getACGMEViolationDetails: errorHandler.getACGMEViolationDetails.bind(errorHandler),
    getScheduleConflictDetails:
      errorHandler.getScheduleConflictDetails.bind(errorHandler),
  }
}

/**
 * Initialize error handler
 */
export function initializeErrorHandler(config?: Partial<ErrorHandlerConfig>): void {
  if (config) {
    errorHandler.configure(config)
  }

  // Set up global error handlers
  if (typeof window !== 'undefined') {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      errorHandler.handle(event.reason, {
        type: 'unhandledRejection',
        promise: event.promise,
      })
    })

    // Handle uncaught errors
    window.addEventListener('error', (event) => {
      errorHandler.handle(event.error, {
        type: 'uncaughtError',
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
      })
    })
  }
}
