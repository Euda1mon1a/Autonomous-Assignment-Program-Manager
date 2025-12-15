/**
 * Error handling utilities for the application
 *
 * Provides standardized error messages and utilities for
 * transforming various error types into user-friendly messages.
 */

import { ApiError } from './api'

// ============================================================================
// Error Message Constants
// ============================================================================

export const ERROR_MESSAGES = {
  // Network errors
  NETWORK_ERROR: 'Unable to connect to the server. Please check your internet connection.',
  TIMEOUT_ERROR: 'The request timed out. Please try again.',

  // Authentication errors
  UNAUTHORIZED: 'Your session has expired. Please log in again.',
  FORBIDDEN: 'You do not have permission to perform this action.',
  INVALID_CREDENTIALS: 'Invalid email or password.',

  // Validation errors
  VALIDATION_ERROR: 'Please check your input and try again.',
  REQUIRED_FIELD: 'This field is required.',
  INVALID_EMAIL: 'Please enter a valid email address.',
  INVALID_DATE: 'Please enter a valid date.',

  // Resource errors
  NOT_FOUND: 'The requested resource was not found.',
  CONFLICT: 'This resource already exists.',
  ALREADY_EXISTS: 'A record with this information already exists.',

  // Server errors
  SERVER_ERROR: 'A server error occurred. Please try again later.',
  SERVICE_UNAVAILABLE: 'The service is temporarily unavailable. Please try again later.',

  // Generic errors
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again.',
  OPERATION_FAILED: 'The operation could not be completed. Please try again.',

  // CRUD operations
  CREATE_FAILED: 'Failed to create the record. Please try again.',
  UPDATE_FAILED: 'Failed to update the record. Please try again.',
  DELETE_FAILED: 'Failed to delete the record. Please try again.',
  LOAD_FAILED: 'Failed to load data. Please try again.',

  // Specific entity errors
  PERSON_CREATE_FAILED: 'Failed to create person. Please try again.',
  PERSON_UPDATE_FAILED: 'Failed to update person. Please try again.',
  PERSON_DELETE_FAILED: 'Failed to delete person. Please try again.',
  ASSIGNMENT_CREATE_FAILED: 'Failed to create assignment. Please try again.',
  ASSIGNMENT_UPDATE_FAILED: 'Failed to update assignment. Please try again.',
  ASSIGNMENT_DELETE_FAILED: 'Failed to delete assignment. Please try again.',
  SCHEDULE_GENERATE_FAILED: 'Failed to generate schedule. Please try again.',
} as const

// Type for error message keys
export type ErrorMessageKey = keyof typeof ERROR_MESSAGES

// ============================================================================
// Error Type Guards
// ============================================================================

/**
 * Check if an error is an ApiError from our API client
 */
export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    'status' in error &&
    typeof (error as ApiError).message === 'string' &&
    typeof (error as ApiError).status === 'number'
  )
}

/**
 * Check if an error is a standard Error object
 */
export function isError(error: unknown): error is Error {
  return error instanceof Error
}

// ============================================================================
// Error Message Extraction
// ============================================================================

/**
 * Extract a user-friendly error message from various error types
 *
 * @param error - The error to extract a message from
 * @param fallback - Optional fallback message if extraction fails
 * @returns A user-friendly error message string
 *
 * @example
 * try {
 *   await createPerson(data)
 * } catch (error) {
 *   const message = getErrorMessage(error)
 *   showError(message)
 * }
 */
export function getErrorMessage(
  error: unknown,
  fallback: string = ERROR_MESSAGES.UNKNOWN_ERROR
): string {
  // Handle null/undefined
  if (error === null || error === undefined) {
    return fallback
  }

  // Handle ApiError from our API client
  if (isApiError(error)) {
    return getApiErrorMessage(error)
  }

  // Handle standard Error objects
  if (isError(error)) {
    // Check for specific error types by message content
    const message = error.message.toLowerCase()

    if (message.includes('network') || message.includes('fetch')) {
      return ERROR_MESSAGES.NETWORK_ERROR
    }

    if (message.includes('timeout')) {
      return ERROR_MESSAGES.TIMEOUT_ERROR
    }

    // Return the error message if it seems user-friendly
    if (error.message && !error.message.includes('Error:') && error.message.length < 200) {
      return error.message
    }

    return fallback
  }

  // Handle string errors
  if (typeof error === 'string') {
    return error.length > 0 && error.length < 200 ? error : fallback
  }

  // Handle objects with message property
  if (typeof error === 'object' && 'message' in error) {
    const message = (error as { message: unknown }).message
    if (typeof message === 'string' && message.length > 0 && message.length < 200) {
      return message
    }
  }

  return fallback
}

/**
 * Get a user-friendly message from an ApiError based on status code
 */
function getApiErrorMessage(error: ApiError): string {
  // If the API provided a specific message, use it (unless it's too technical)
  if (error.message && !error.message.includes('Error:') && error.message.length < 200) {
    return error.message
  }

  // Map status codes to user-friendly messages
  switch (error.status) {
    case 0:
      return ERROR_MESSAGES.NETWORK_ERROR
    case 400:
      return error.detail || ERROR_MESSAGES.VALIDATION_ERROR
    case 401:
      return ERROR_MESSAGES.UNAUTHORIZED
    case 403:
      return ERROR_MESSAGES.FORBIDDEN
    case 404:
      return ERROR_MESSAGES.NOT_FOUND
    case 409:
      return error.detail || ERROR_MESSAGES.CONFLICT
    case 422:
      return error.detail || ERROR_MESSAGES.VALIDATION_ERROR
    case 500:
    case 502:
    case 503:
      return ERROR_MESSAGES.SERVER_ERROR
    case 504:
      return ERROR_MESSAGES.TIMEOUT_ERROR
    default:
      return error.message || ERROR_MESSAGES.UNKNOWN_ERROR
  }
}

// ============================================================================
// Success Messages
// ============================================================================

export const SUCCESS_MESSAGES = {
  // Generic
  SAVED: 'Changes saved successfully.',
  DELETED: 'Item deleted successfully.',
  CREATED: 'Item created successfully.',
  UPDATED: 'Item updated successfully.',

  // Person
  PERSON_CREATED: 'Person created successfully.',
  PERSON_UPDATED: 'Person updated successfully.',
  PERSON_DELETED: 'Person deleted successfully.',

  // Assignment
  ASSIGNMENT_CREATED: 'Assignment created successfully.',
  ASSIGNMENT_UPDATED: 'Assignment updated successfully.',
  ASSIGNMENT_DELETED: 'Assignment deleted successfully.',

  // Schedule
  SCHEDULE_GENERATED: 'Schedule generated successfully.',
  SCHEDULE_SAVED: 'Schedule saved successfully.',

  // Auth
  LOGIN_SUCCESS: 'Welcome back!',
  LOGOUT_SUCCESS: 'You have been logged out.',
} as const

export type SuccessMessageKey = keyof typeof SUCCESS_MESSAGES
