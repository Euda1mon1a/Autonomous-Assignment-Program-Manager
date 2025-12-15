/**
 * Tests for API client and error handling utilities
 *
 * Tests the error transformation logic in api.ts and errors.ts
 */
import {
  ERROR_MESSAGES,
  isApiError,
  isError,
  getErrorMessage,
} from '@/lib/errors'
import type { ApiError } from '@/lib/api'

describe('Error Type Guards', () => {
  describe('isApiError', () => {
    it('should return true for valid ApiError objects', () => {
      const apiError: ApiError = {
        message: 'Not found',
        status: 404,
      }
      expect(isApiError(apiError)).toBe(true)
    })

    it('should return true for ApiError with optional fields', () => {
      const apiError: ApiError = {
        message: 'Validation failed',
        status: 422,
        detail: 'Name is required',
        errors: {
          name: ['Name is required'],
        },
      }
      expect(isApiError(apiError)).toBe(true)
    })

    it('should return false for null', () => {
      expect(isApiError(null)).toBe(false)
    })

    it('should return false for undefined', () => {
      expect(isApiError(undefined)).toBe(false)
    })

    it('should return false for plain strings', () => {
      expect(isApiError('error message')).toBe(false)
    })

    it('should return false for objects without message', () => {
      expect(isApiError({ status: 404 })).toBe(false)
    })

    it('should return false for objects without status', () => {
      expect(isApiError({ message: 'error' })).toBe(false)
    })

    it('should return false for objects with wrong types', () => {
      expect(isApiError({ message: 123, status: '404' })).toBe(false)
    })

    it('should return false for Error instances', () => {
      expect(isApiError(new Error('something went wrong'))).toBe(false)
    })
  })

  describe('isError', () => {
    it('should return true for Error instances', () => {
      expect(isError(new Error('test'))).toBe(true)
    })

    it('should return true for TypeError', () => {
      expect(isError(new TypeError('type error'))).toBe(true)
    })

    it('should return true for SyntaxError', () => {
      expect(isError(new SyntaxError('syntax error'))).toBe(true)
    })

    it('should return false for plain objects', () => {
      expect(isError({ message: 'error' })).toBe(false)
    })

    it('should return false for null', () => {
      expect(isError(null)).toBe(false)
    })

    it('should return false for undefined', () => {
      expect(isError(undefined)).toBe(false)
    })

    it('should return false for strings', () => {
      expect(isError('error string')).toBe(false)
    })
  })
})

describe('getErrorMessage', () => {
  describe('with null/undefined errors', () => {
    it('should return fallback for null', () => {
      expect(getErrorMessage(null)).toBe(ERROR_MESSAGES.UNKNOWN_ERROR)
    })

    it('should return fallback for undefined', () => {
      expect(getErrorMessage(undefined)).toBe(ERROR_MESSAGES.UNKNOWN_ERROR)
    })

    it('should return custom fallback when provided', () => {
      expect(getErrorMessage(null, 'Custom fallback')).toBe('Custom fallback')
    })
  })

  describe('with ApiError objects', () => {
    it('should return message for network error (status 0)', () => {
      const error: ApiError = { message: '', status: 0 }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.NETWORK_ERROR)
    })

    it('should return validation message for 400 errors', () => {
      const error: ApiError = { message: '', status: 400 }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.VALIDATION_ERROR)
    })

    it('should return detail for 400 errors when provided', () => {
      const error: ApiError = {
        message: '',
        status: 400,
        detail: 'Name is required',
      }
      expect(getErrorMessage(error)).toBe('Name is required')
    })

    it('should return unauthorized message for 401 errors', () => {
      const error: ApiError = { message: '', status: 401 }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.UNAUTHORIZED)
    })

    it('should return forbidden message for 403 errors', () => {
      const error: ApiError = { message: '', status: 403 }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.FORBIDDEN)
    })

    it('should return not found message for 404 errors', () => {
      const error: ApiError = { message: '', status: 404 }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.NOT_FOUND)
    })

    it('should return conflict message for 409 errors', () => {
      const error: ApiError = { message: '', status: 409 }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.CONFLICT)
    })

    it('should return detail for 409 errors when provided', () => {
      const error: ApiError = {
        message: '',
        status: 409,
        detail: 'Email already exists',
      }
      expect(getErrorMessage(error)).toBe('Email already exists')
    })

    it('should return validation message for 422 errors', () => {
      const error: ApiError = { message: '', status: 422 }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.VALIDATION_ERROR)
    })

    it('should return server error for 500 errors', () => {
      const error: ApiError = { message: '', status: 500 }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.SERVER_ERROR)
    })

    it('should return server error for 502 errors', () => {
      const error: ApiError = { message: '', status: 502 }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.SERVER_ERROR)
    })

    it('should return server error for 503 errors', () => {
      const error: ApiError = { message: '', status: 503 }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.SERVER_ERROR)
    })

    it('should return timeout error for 504 errors', () => {
      const error: ApiError = { message: '', status: 504 }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.TIMEOUT_ERROR)
    })

    it('should return API-provided message when it is user-friendly', () => {
      const error: ApiError = {
        message: 'Please provide a valid date range',
        status: 400,
      }
      expect(getErrorMessage(error)).toBe('Please provide a valid date range')
    })

    it('should not return technical error messages', () => {
      const error: ApiError = {
        message: 'Error: ECONNREFUSED',
        status: 500,
      }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.SERVER_ERROR)
    })

    it('should not return very long messages', () => {
      const error: ApiError = {
        message: 'A'.repeat(300),
        status: 500,
      }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.SERVER_ERROR)
    })
  })

  describe('with Error objects', () => {
    it('should return network error message for network-related errors', () => {
      const error = new Error('Network request failed')
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.NETWORK_ERROR)
    })

    it('should return network error for fetch errors', () => {
      const error = new Error('Failed to fetch')
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.NETWORK_ERROR)
    })

    it('should return timeout message for timeout errors', () => {
      const error = new Error('Request timeout exceeded')
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.TIMEOUT_ERROR)
    })

    it('should return the error message for user-friendly errors', () => {
      const error = new Error('Invalid configuration')
      expect(getErrorMessage(error)).toBe('Invalid configuration')
    })

    it('should return fallback for technical error messages', () => {
      const error = new Error('Error: Something went wrong')
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.UNKNOWN_ERROR)
    })

    it('should return fallback for very long error messages', () => {
      const error = new Error('A'.repeat(300))
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.UNKNOWN_ERROR)
    })
  })

  describe('with string errors', () => {
    it('should return the string for short strings', () => {
      expect(getErrorMessage('Something went wrong')).toBe('Something went wrong')
    })

    it('should return fallback for empty strings', () => {
      expect(getErrorMessage('')).toBe(ERROR_MESSAGES.UNKNOWN_ERROR)
    })

    it('should return fallback for very long strings', () => {
      expect(getErrorMessage('A'.repeat(300))).toBe(ERROR_MESSAGES.UNKNOWN_ERROR)
    })
  })

  describe('with objects that have message property', () => {
    it('should extract message from objects with message property', () => {
      const error = { message: 'Custom error message' }
      expect(getErrorMessage(error)).toBe('Custom error message')
    })

    it('should return fallback for objects with non-string message', () => {
      const error = { message: 123 }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.UNKNOWN_ERROR)
    })

    it('should return fallback for objects with empty message', () => {
      const error = { message: '' }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.UNKNOWN_ERROR)
    })

    it('should return fallback for objects with long message', () => {
      const error = { message: 'A'.repeat(300) }
      expect(getErrorMessage(error)).toBe(ERROR_MESSAGES.UNKNOWN_ERROR)
    })
  })
})

describe('ERROR_MESSAGES constants', () => {
  it('should have all expected error messages defined', () => {
    expect(ERROR_MESSAGES.NETWORK_ERROR).toBeDefined()
    expect(ERROR_MESSAGES.TIMEOUT_ERROR).toBeDefined()
    expect(ERROR_MESSAGES.UNAUTHORIZED).toBeDefined()
    expect(ERROR_MESSAGES.FORBIDDEN).toBeDefined()
    expect(ERROR_MESSAGES.NOT_FOUND).toBeDefined()
    expect(ERROR_MESSAGES.VALIDATION_ERROR).toBeDefined()
    expect(ERROR_MESSAGES.CONFLICT).toBeDefined()
    expect(ERROR_MESSAGES.SERVER_ERROR).toBeDefined()
    expect(ERROR_MESSAGES.UNKNOWN_ERROR).toBeDefined()
  })

  it('should have user-friendly message strings', () => {
    // Messages should not contain technical jargon
    Object.values(ERROR_MESSAGES).forEach((message) => {
      expect(message).not.toContain('Error:')
      expect(message).not.toContain('Exception')
      expect(message.length).toBeLessThan(200)
    })
  })
})
