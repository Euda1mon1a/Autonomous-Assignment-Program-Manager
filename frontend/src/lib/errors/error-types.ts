/**
 * TypeScript types for error handling in the frontend.
 *
 * These types match the backend error response schemas (RFC 7807 Problem Details).
 */

/**
 * Error codes from backend (matches backend ErrorCode enum)
 */
export enum ErrorCode {
  // Resource errors
  NOT_FOUND = 'NOT_FOUND',
  ALREADY_EXISTS = 'ALREADY_EXISTS',
  RECORD_NOT_FOUND = 'RECORD_NOT_FOUND',
  DUPLICATE_RECORD = 'DUPLICATE_RECORD',

  // Validation errors
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  INVALID_STATE = 'INVALID_STATE',
  INPUT_VALIDATION_ERROR = 'INPUT_VALIDATION_ERROR',
  SCHEMA_VALIDATION_ERROR = 'SCHEMA_VALIDATION_ERROR',
  REQUIRED_FIELD = 'REQUIRED_FIELD',
  INVALID_FORMAT = 'INVALID_FORMAT',
  VALUE_OUT_OF_RANGE = 'VALUE_OUT_OF_RANGE',

  // Date validation errors
  DATE_VALIDATION_ERROR = 'DATE_VALIDATION_ERROR',
  DATE_OUT_OF_RANGE = 'DATE_OUT_OF_RANGE',
  FUTURE_DATE_NOT_ALLOWED = 'FUTURE_DATE_NOT_ALLOWED',
  PAST_DATE_NOT_ALLOWED = 'PAST_DATE_NOT_ALLOWED',

  // Concurrency errors
  CONFLICT = 'CONFLICT',
  CONCURRENT_MODIFICATION = 'CONCURRENT_MODIFICATION',

  // Authorization errors
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  INVALID_CREDENTIALS = 'INVALID_CREDENTIALS',
  TOKEN_EXPIRED = 'TOKEN_EXPIRED',
  INVALID_TOKEN = 'INVALID_TOKEN',
  TOKEN_REVOKED = 'TOKEN_REVOKED',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  INSUFFICIENT_ROLE = 'INSUFFICIENT_ROLE',
  ACCOUNT_DISABLED = 'ACCOUNT_DISABLED',
  MFA_REQUIRED = 'MFA_REQUIRED',
  MFA_INVALID = 'MFA_INVALID',

  // Business logic errors
  BUSINESS_RULE_VIOLATION = 'BUSINESS_RULE_VIOLATION',
  CONSTRAINT_VIOLATION = 'CONSTRAINT_VIOLATION',
  INVALID_STATE_TRANSITION = 'INVALID_STATE_TRANSITION',

  // Scheduling errors
  SCHEDULING_ERROR = 'SCHEDULING_ERROR',
  SCHEDULE_CONFLICT = 'SCHEDULE_CONFLICT',
  SCHEDULE_GENERATION_FAILED = 'SCHEDULE_GENERATION_FAILED',
  SOLVER_TIMEOUT = 'SOLVER_TIMEOUT',
  CONSTRAINT_VIOLATION_SCHEDULING = 'CONSTRAINT_VIOLATION_SCHEDULING',
  INFEASIBLE_SCHEDULE = 'INFEASIBLE_SCHEDULE',
  ROTATION_TEMPLATE_ERROR = 'ROTATION_TEMPLATE_ERROR',
  BLOCK_ASSIGNMENT_ERROR = 'BLOCK_ASSIGNMENT_ERROR',

  // ACGME compliance errors
  ACGME_COMPLIANCE_ERROR = 'ACGME_COMPLIANCE_ERROR',
  WORK_HOUR_VIOLATION = 'WORK_HOUR_VIOLATION',
  REST_REQUIREMENT_VIOLATION = 'REST_REQUIREMENT_VIOLATION',
  SUPERVISION_VIOLATION = 'SUPERVISION_VIOLATION',
  SHIFT_LENGTH_VIOLATION = 'SHIFT_LENGTH_VIOLATION',
  CALL_FREQUENCY_VIOLATION = 'CALL_FREQUENCY_VIOLATION',

  // Database errors
  DATABASE_ERROR = 'DATABASE_ERROR',
  DATABASE_CONNECTION_ERROR = 'DATABASE_CONNECTION_ERROR',
  DATABASE_TIMEOUT = 'DATABASE_TIMEOUT',
  INTEGRITY_CONSTRAINT_ERROR = 'INTEGRITY_CONSTRAINT_ERROR',
  FOREIGN_KEY_VIOLATION = 'FOREIGN_KEY_VIOLATION',
  TRANSACTION_ERROR = 'TRANSACTION_ERROR',

  // External service errors
  EXTERNAL_SERVICE_ERROR = 'EXTERNAL_SERVICE_ERROR',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  SERVICE_TIMEOUT = 'SERVICE_TIMEOUT',
  EXTERNAL_API_ERROR = 'EXTERNAL_API_ERROR',
  EMAIL_SERVICE_ERROR = 'EMAIL_SERVICE_ERROR',
  SMS_SERVICE_ERROR = 'SMS_SERVICE_ERROR',
  NOTIFICATION_SERVICE_ERROR = 'NOTIFICATION_SERVICE_ERROR',
  CLOUD_STORAGE_ERROR = 'CLOUD_STORAGE_ERROR',
  PAYMENT_SERVICE_ERROR = 'PAYMENT_SERVICE_ERROR',
  WEBHOOK_DELIVERY_ERROR = 'WEBHOOK_DELIVERY_ERROR',

  // Rate limiting errors
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  QUOTA_EXCEEDED = 'QUOTA_EXCEEDED',
  CONCURRENCY_LIMIT_EXCEEDED = 'CONCURRENCY_LIMIT_EXCEEDED',
  BANDWIDTH_LIMIT_EXCEEDED = 'BANDWIDTH_LIMIT_EXCEEDED',
  STORAGE_QUOTA_EXCEEDED = 'STORAGE_QUOTA_EXCEEDED',

  // Generic error
  INTERNAL_ERROR = 'INTERNAL_ERROR',
}

/**
 * Detailed error information for a specific field
 */
export interface ErrorDetail {
  field: string
  message: string
  type?: string
  location?: 'body' | 'query' | 'path' | 'header'
}

/**
 * RFC 7807 Problem Details error response
 */
export interface ErrorResponse {
  type: string
  title: string
  status: number
  detail: string
  instance: string
  error_code: ErrorCode
  error_id: string
  timestamp: string
  request_id?: string
  fingerprint?: string
}

/**
 * Validation error response with detailed field errors
 */
export interface ValidationErrorResponse extends ErrorResponse {
  errors: ErrorDetail[]
}

/**
 * ACGME compliance violation details
 */
export interface ACGMEViolationDetail {
  resident_id?: string
  violation_date?: string
  period_start?: string
  period_end?: string
  actual_hours?: number
  limit_hours?: number
  rule_violated?: string
}

/**
 * ACGME compliance error response
 */
export interface ACGMEComplianceErrorResponse extends ErrorResponse {
  violation: ACGMEViolationDetail
}

/**
 * Schedule conflict details
 */
export interface ScheduleConflictDetail {
  conflicting_assignment_id?: string
  requested_date?: string
  person_id?: string
  conflict_type?: 'time' | 'location' | 'resource'
}

/**
 * Schedule conflict error response
 */
export interface ScheduleConflictErrorResponse extends ErrorResponse {
  conflict: ScheduleConflictDetail
}

/**
 * Rate limit error response
 */
export interface RateLimitErrorResponse extends ErrorResponse {
  limit: number
  window_seconds: number
  retry_after: number
}

/**
 * Error response with suggested solutions
 */
export interface ErrorResponseWithSuggestions extends ErrorResponse {
  suggestions: string[]
}

/**
 * Multi-error response (for batch operations)
 */
export interface MultiErrorResponse {
  errors: ErrorResponse[]
  total_errors: number
  timestamp: string
}

/**
 * Legacy simple error response
 */
export interface SimpleErrorResponse {
  detail: string
  status_code: number
  error_code?: string
}

/**
 * Type guard to check if error is RFC 7807 format
 */
export function isRFC7807Error(error: unknown): error is ErrorResponse {
  return (
    typeof error === 'object' &&
    error !== null &&
    'type' in error &&
    'title' in error &&
    'status' in error &&
    'detail' in error &&
    'error_code' in error
  )
}

/**
 * Type guard to check if error is validation error
 */
export function isValidationError(
  error: unknown
): error is ValidationErrorResponse {
  return isRFC7807Error(error) && 'errors' in error && Array.isArray(error.errors)
}

/**
 * Type guard to check if error is ACGME compliance error
 */
export function isACGMEComplianceError(
  error: unknown
): error is ACGMEComplianceErrorResponse {
  return (
    isRFC7807Error(error) &&
    'violation' in error &&
    typeof error.violation === 'object'
  )
}

/**
 * Type guard to check if error is schedule conflict error
 */
export function isScheduleConflictError(
  error: unknown
): error is ScheduleConflictErrorResponse {
  return (
    isRFC7807Error(error) &&
    'conflict' in error &&
    typeof error.conflict === 'object'
  )
}

/**
 * Type guard to check if error is rate limit error
 */
export function isRateLimitError(
  error: unknown
): error is RateLimitErrorResponse {
  return (
    isRFC7807Error(error) &&
    'limit' in error &&
    'retry_after' in error &&
    typeof error.limit === 'number' &&
    typeof error.retry_after === 'number'
  )
}

/**
 * Type guard to check if error has suggestions
 */
export function hasErrorSuggestions(
  error: unknown
): error is ErrorResponseWithSuggestions {
  return (
    isRFC7807Error(error) &&
    'suggestions' in error &&
    Array.isArray(error.suggestions)
  )
}

/**
 * Error severity levels
 */
export enum ErrorSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical',
}

/**
 * Get error severity from status code
 */
export function getErrorSeverity(statusCode: number): ErrorSeverity {
  if (statusCode === 404 || statusCode === 422) {
    return ErrorSeverity.INFO
  }
  if (statusCode === 401 || statusCode === 403) {
    return ErrorSeverity.WARNING
  }
  if (statusCode >= 500) {
    return ErrorSeverity.CRITICAL
  }
  return ErrorSeverity.ERROR
}
