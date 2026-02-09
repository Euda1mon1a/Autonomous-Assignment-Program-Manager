/**
 * Error reporting interface and implementations
 *
 * Provides a pluggable error reporting system that can be swapped with
 * external services like Sentry when needed.
 */

import { ErrorResponse, ErrorSeverity, getErrorSeverity } from '../errors/error-types'

/**
 * Error reporter interface
 */
export interface ErrorReporter {
  report(error: ErrorResponse | Error, context?: Record<string, unknown>): void
  flush?(): void
}

/**
 * No-op reporter for development/testing
 */
export class NullErrorReporter implements ErrorReporter {
  report(_error: ErrorResponse | Error, _context?: Record<string, unknown>): void {
    // Do nothing
  }
}

/**
 * Console reporter for development
 */
export class ConsoleErrorReporter implements ErrorReporter {
  report(error: ErrorResponse | Error, context?: Record<string, unknown>): void {
    const severity = this.getErrorSeverity(error)
    const logData = {
      error: error instanceof Error ? error.message : (error as ErrorResponse).detail,
      errorCode: (error as ErrorResponse).errorCode || 'UNKNOWN',
      status: (error as ErrorResponse).status,
      severity,
      context,
      timestamp: new Date().toISOString(),
    }

    switch (severity) {
      case ErrorSeverity.CRITICAL:
        console.error('[CRITICAL ERROR REPORT]', logData)
        break
      case ErrorSeverity.ERROR:
        console.error('[ERROR REPORT]', logData)
        break
      case ErrorSeverity.WARNING:
        console.warn('[WARNING REPORT]', logData)
        break
      default:
        console.info('[INFO REPORT]', logData)
    }
  }

  private getErrorSeverity(error: ErrorResponse | Error): ErrorSeverity {
    if (error instanceof Error) {
      return ErrorSeverity.ERROR
    }
    return getErrorSeverity(error.status)
  }
}

/**
 * Factory function to get error reporter based on environment
 */
export function createErrorReporter(): ErrorReporter {
  if (process.env.NODE_ENV === 'production' && process.env.SENTRY_DSN) {
    // TODO: Integrate with Sentry when DSN is configured
    // return new SentryErrorReporter(process.env.SENTRY_DSN)
  }

  // Default to console reporter for development
  return new ConsoleErrorReporter()
}