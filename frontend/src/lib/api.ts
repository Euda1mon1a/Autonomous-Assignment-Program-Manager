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
    400: 'Bad request - please check your input',
    401: 'Unauthorized - please log in',
    403: 'Forbidden - you do not have permission',
    404: 'Not found',
    409: 'Conflict - resource already exists',
    422: 'Validation error',
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
    timeout: 30000, // 30 second timeout
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
    (response) => response,
    (error: AxiosError) => {
      const apiError = transformError(error)

      // Handle 401 - redirect to login if unauthorized
      if (apiError.status === 401 && typeof window !== 'undefined') {
        // Could dispatch to auth context or redirect
        // window.location.href = '/login'
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
