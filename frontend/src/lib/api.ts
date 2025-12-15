/**
 * API Client for Residency Scheduler
 *
 * Provides a configured axios instance with interceptors for
 * authentication, error handling, and type-safe request helpers.
 */
import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'

// API base URL from environment or default for development
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

/**
 * Standardized API error shape
 */
export interface ApiError {
  message: string
  status: number
  detail?: string
  errors?: Record<string, string[]>
}

/**
 * Transform axios errors into consistent ApiError shape
 */
function transformError(error: AxiosError): ApiError {
  if (error.response) {
    const { status, data } = error.response
    const responseData = data as { detail?: string; message?: string } | undefined
    return {
      message: responseData?.detail || responseData?.message || getStatusMessage(status),
      status,
      detail: responseData?.detail,
    }
  }

  if (error.request) {
    return {
      message: 'Network error - unable to reach server',
      status: 0,
    }
  }

  return {
    message: error.message || 'An unexpected error occurred',
    status: 0,
  }
}

/**
 * Get human-readable message for HTTP status codes
 */
function getStatusMessage(status: number): string {
  const messages: Record<number, string> = {
    207: 'Partial success - some validation warnings',
    400: 'Bad request - please check your input',
    401: 'Unauthorized - please log in',
    403: 'Forbidden - you do not have permission',
    404: 'Not found',
    409: 'Conflict - resource already exists or operation in progress',
    422: 'Validation error - generation failed',
    500: 'Server error - please try again later',
  }
  return messages[status] || `Error (${status})`
}

/**
 * Create configured axios instance
 */
function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
    // Issue #4: Timeout mismatch - increased from 30s to 120s to match backend
    // Schedule generation can take longer with constraint solving algorithms
    timeout: 120000, // 120 second timeout (2 minutes)
  })

  // Request interceptor - attach auth token if available
  client.interceptors.request.use(
    (config) => {
      // Get token from localStorage if available
      if (typeof window !== 'undefined') {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  // Response interceptor - transform errors
  client.interceptors.response.use(
    (response) => {
      // Issue #5: Handle 207 Multi-Status as a successful response (partial success)
      // This is used for schedule generation that completes but has validation warnings
      return response
    },
    (error: AxiosError) => {
      const apiError = transformError(error)

      // Issue #5: Treat 207 Multi-Status as success (partial success scenario)
      if (error.response?.status === 207) {
        return error.response
      }

      if (typeof window !== 'undefined') {
        // Handle 401 - clear auth and redirect to login
        if (apiError.status === 401) {
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user')
          window.location.href = '/login'
        }

        // Handle 403 - forbidden access
        if (apiError.status === 403) {
          apiError.message = 'You do not have permission to perform this action'
        }

        // Handle 409 - conflict (e.g., generation already in progress)
        if (apiError.status === 409) {
          apiError.message = apiError.detail || 'Operation already in progress'
        }

        // Handle 422 - validation error
        if (apiError.status === 422) {
          apiError.message = apiError.detail || 'Validation failed'
        }

        // Handle 500 - server error
        if (apiError.status >= 500) {
          apiError.message = 'A server error occurred. Please try again later.'
        }
      }

      return Promise.reject(apiError)
    }
  )

  return client
}

// Export configured axios instance
export const api = createApiClient()

/**
 * Type-safe GET request
 */
export async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.get<T>(url, config)
  return response.data
}

/**
 * Type-safe POST request
 */
export async function post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.post<T>(url, data, config)
  return response.data
}

/**
 * Type-safe PUT request
 */
export async function put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.put<T>(url, data, config)
  return response.data
}

/**
 * Type-safe PATCH request
 */
export async function patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.patch<T>(url, data, config)
  return response.data
}

/**
 * Type-safe DELETE request
 */
export async function del(url: string, config?: AxiosRequestConfig): Promise<void> {
  await api.delete(url, config)
}

// Re-export types
export type { AxiosRequestConfig }
