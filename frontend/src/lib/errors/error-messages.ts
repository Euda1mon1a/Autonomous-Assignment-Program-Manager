/**
 * User-friendly error messages for different error codes.
 *
 * Provides consistent, helpful error messages across the application.
 */

import {
  ErrorCode,
  isRFC7807Error,
  isValidationError,
} from './error-types'

/**
 * Map of error codes to user-friendly messages
 */
export const ERROR_MESSAGES: Record<ErrorCode, string> = {
  // Resource errors
  [ErrorCode.NOT_FOUND]: 'The requested resource was not found.',
  [ErrorCode.ALREADY_EXISTS]: 'A resource with this information already exists.',
  [ErrorCode.RECORD_NOT_FOUND]: 'The requested record was not found.',
  [ErrorCode.DUPLICATE_RECORD]: 'A record with this information already exists.',

  // Validation errors
  [ErrorCode.VALIDATION_ERROR]: 'Please check your input and try again.',
  [ErrorCode.INVALID_STATE]:
    'The resource is in an invalid state for this operation.',
  [ErrorCode.INPUT_VALIDATION_ERROR]: 'The input data is invalid.',
  [ErrorCode.SCHEMA_VALIDATION_ERROR]: 'The data does not match the required format.',
  [ErrorCode.REQUIRED_FIELD]: 'A required field is missing.',
  [ErrorCode.INVALID_FORMAT]: 'The data format is invalid.',
  [ErrorCode.VALUE_OUT_OF_RANGE]: 'The value is outside the allowed range.',

  // Date validation errors
  [ErrorCode.DATE_VALIDATION_ERROR]: 'The provided date is invalid.',
  [ErrorCode.DATE_OUT_OF_RANGE]: 'The date is outside the allowed range.',
  [ErrorCode.FUTURE_DATE_NOT_ALLOWED]: 'Future dates are not allowed for this field.',
  [ErrorCode.PAST_DATE_NOT_ALLOWED]: 'Past dates are not allowed for this field.',

  // Concurrency errors
  [ErrorCode.CONFLICT]: 'The request conflicts with existing data.',
  [ErrorCode.CONCURRENT_MODIFICATION]:
    'This record was modified by another user. Please refresh and try again.',

  // Authorization errors
  [ErrorCode.UNAUTHORIZED]: 'Your session has expired. Please log in again.',
  [ErrorCode.FORBIDDEN]: 'You do not have permission to perform this action.',
  [ErrorCode.INVALID_CREDENTIALS]: 'Invalid email or password.',
  [ErrorCode.TOKEN_EXPIRED]: 'Your session has expired. Please log in again.',
  [ErrorCode.INVALID_TOKEN]: 'Your session is invalid. Please log in again.',
  [ErrorCode.TOKEN_REVOKED]: 'Your session has been revoked. Please log in again.',
  [ErrorCode.PERMISSION_DENIED]: 'You do not have permission to perform this action.',
  [ErrorCode.INSUFFICIENT_ROLE]: 'Your role does not allow this action.',
  [ErrorCode.ACCOUNT_DISABLED]:
    'This account has been disabled. Please contact support.',
  [ErrorCode.MFA_REQUIRED]: 'Multi-factor authentication is required.',
  [ErrorCode.MFA_INVALID]: 'The multi-factor authentication code is invalid.',

  // Business logic errors
  [ErrorCode.BUSINESS_RULE_VIOLATION]: 'A business rule was violated.',
  [ErrorCode.CONSTRAINT_VIOLATION]: 'A constraint was violated.',
  [ErrorCode.INVALID_STATE_TRANSITION]: 'The requested state transition is not allowed.',

  // Scheduling errors
  [ErrorCode.SCHEDULING_ERROR]: 'A scheduling error occurred. Please try again.',
  [ErrorCode.SCHEDULE_CONFLICT]:
    'The assignment conflicts with existing schedules. Please choose a different time.',
  [ErrorCode.SCHEDULE_GENERATION_FAILED]:
    'Schedule generation failed. Please adjust your requirements and try again.',
  [ErrorCode.SOLVER_TIMEOUT]:
    'Schedule generation is taking longer than expected. Please simplify your requirements or try again later.',
  [ErrorCode.CONSTRAINT_VIOLATION_SCHEDULING]: 'A scheduling constraint was violated.',
  [ErrorCode.INFEASIBLE_SCHEDULE]:
    'The schedule requirements cannot be satisfied. Please adjust your constraints.',
  [ErrorCode.ROTATION_TEMPLATE_ERROR]: 'The rotation template is invalid.',
  [ErrorCode.BLOCK_ASSIGNMENT_ERROR]: 'The block assignment is invalid.',

  // ACGME compliance errors
  [ErrorCode.ACGME_COMPLIANCE_ERROR]:
    'ACGME compliance requirements were violated. Please review the details.',
  [ErrorCode.WORK_HOUR_VIOLATION]:
    'This assignment would violate the 80-hour work week limit.',
  [ErrorCode.REST_REQUIREMENT_VIOLATION]:
    'This assignment would violate the 1-in-7 rest day requirement.',
  [ErrorCode.SUPERVISION_VIOLATION]:
    'This assignment would violate supervision ratio requirements.',
  [ErrorCode.SHIFT_LENGTH_VIOLATION]:
    'This assignment would exceed the maximum shift length.',
  [ErrorCode.CALL_FREQUENCY_VIOLATION]:
    'This assignment would violate call frequency limits.',

  // Database errors
  [ErrorCode.DATABASE_ERROR]:
    'A database error occurred. Please try again later or contact support.',
  [ErrorCode.DATABASE_CONNECTION_ERROR]:
    'Unable to connect to the database. Please check your connection and try again.',
  [ErrorCode.DATABASE_TIMEOUT]:
    'The database operation timed out. Please try again.',
  [ErrorCode.INTEGRITY_CONSTRAINT_ERROR]:
    'A database constraint was violated. Please check your data.',
  [ErrorCode.FOREIGN_KEY_VIOLATION]: 'The referenced record does not exist.',
  [ErrorCode.TRANSACTION_ERROR]:
    'The database transaction failed. Please try again.',

  // External service errors
  [ErrorCode.EXTERNAL_SERVICE_ERROR]:
    'An external service error occurred. Please try again later.',
  [ErrorCode.SERVICE_UNAVAILABLE]:
    'The service is temporarily unavailable. Please try again later.',
  [ErrorCode.SERVICE_TIMEOUT]:
    'The service request timed out. Please try again.',
  [ErrorCode.EXTERNAL_API_ERROR]:
    'An error occurred while communicating with an external service.',
  [ErrorCode.EMAIL_SERVICE_ERROR]:
    'Failed to send email. Please try again or contact support.',
  [ErrorCode.SMS_SERVICE_ERROR]:
    'Failed to send SMS. Please try again or contact support.',
  [ErrorCode.NOTIFICATION_SERVICE_ERROR]:
    'Failed to send notification. Please try again or contact support.',
  [ErrorCode.CLOUD_STORAGE_ERROR]:
    'Cloud storage operation failed. Please try again.',
  [ErrorCode.PAYMENT_SERVICE_ERROR]:
    'Payment processing failed. Please try again or contact support.',
  [ErrorCode.WEBHOOK_DELIVERY_ERROR]:
    'Webhook delivery failed. Please check your webhook configuration.',

  // Rate limiting errors
  [ErrorCode.RATE_LIMIT_EXCEEDED]:
    'You have made too many requests. Please wait a moment and try again.',
  [ErrorCode.QUOTA_EXCEEDED]:
    'Your usage quota has been exceeded. Please upgrade your plan or wait for the quota to reset.',
  [ErrorCode.CONCURRENCY_LIMIT_EXCEEDED]:
    'Too many concurrent operations. Please wait and try again.',
  [ErrorCode.BANDWIDTH_LIMIT_EXCEEDED]:
    'Bandwidth limit exceeded. Please wait for the limit to reset.',
  [ErrorCode.STORAGE_QUOTA_EXCEEDED]:
    'Storage quota exceeded. Please free up space or upgrade your plan.',

  // Generic error
  [ErrorCode.INTERNAL_ERROR]:
    'An internal server error occurred. Please try again later or contact support.',
}

/**
 * Get user-friendly error message
 */
export function getErrorMessage(
  error: unknown,
  fallback: string = 'An unexpected error occurred. Please try again.'
): string {
  // Handle null/undefined
  if (error === null || error === undefined) {
    return fallback
  }

  // Handle RFC 7807 errors
  if (isRFC7807Error(error)) {
    // For validation errors, provide more specific message
    if (isValidationError(error) && error.errors.length > 0) {
      const fieldErrors = error.errors.map((e) => e.message).join(', ')
      return `Validation failed: ${fieldErrors}`
    }

    // Use mapped message if available
    const mappedMessage = ERROR_MESSAGES[error.error_code]
    if (mappedMessage) {
      return mappedMessage
    }

    // Fall back to detail from API
    return error.detail
  }

  // Handle standard Error objects
  if (error instanceof Error) {
    return error.message
  }

  // Handle string errors
  if (typeof error === 'string') {
    return error
  }

  // Handle objects with message property
  if (typeof error === 'object' && 'message' in error) {
    const message = (error as { message: unknown }).message
    if (typeof message === 'string') {
      return message
    }
  }

  return fallback
}

/**
 * Get contextual error message with additional details
 */
export function getDetailedErrorMessage(error: unknown): {
  message: string
  details?: string[]
  suggestions?: string[]
} {
  const message = getErrorMessage(error)

  if (!isRFC7807Error(error)) {
    return { message }
  }

  const result: {
    message: string
    details?: string[]
    suggestions?: string[]
  } = { message }

  // Add validation details
  if (isValidationError(error)) {
    result.details = error.errors.map((e) => `${e.field}: ${e.message}`)
  }

  // Add suggestions if available
  if ('suggestions' in error && Array.isArray(error.suggestions)) {
    result.suggestions = error.suggestions
  }

  return result
}

/**
 * Get short error title
 */
export function getErrorTitle(error: unknown): string {
  if (isRFC7807Error(error)) {
    return error.title
  }

  if (error instanceof Error) {
    return error.name
  }

  return 'Error'
}
