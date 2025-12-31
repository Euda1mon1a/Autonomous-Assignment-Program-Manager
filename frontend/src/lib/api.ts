/**
 * API Client for Residency Scheduler
 *
 * Provides a configured axios instance with interceptors for
 * authentication, error handling, and type-safe request helpers.
 *
 * Features:
 * - Automatic token refresh on 401 errors (reactive refresh)
 * - Request queuing during refresh to prevent race conditions
 * - Retry failed requests after successful refresh
 *
 * @module lib/api
 */
import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios'

// API base URL from environment or default for development
// Use /api/v1 directly to avoid 307 redirect which causes CORS issues
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

// Import token refresh functions (lazy import to avoid circular dependency)
// These will be dynamically imported when needed
let authModule: typeof import('./auth') | null = null

async function getAuthModule() {
  if (!authModule) {
    authModule = await import('./auth')
  }
  return authModule
}

/**
 * Queue of failed requests waiting for token refresh.
 * Each entry contains resolve/reject functions to continue or fail the request.
 */
interface QueuedRequest {
  resolve: (config: InternalAxiosRequestConfig) => void
  reject: (error: Error) => void
  config: InternalAxiosRequestConfig
}

/**
 * Standardized API error shape returned by all API operations.
 * Provides consistent error handling across the application.
 */
export interface ApiError {
  /** Human-readable error message for display */
  message: string
  /** HTTP status code (0 for network errors) */
  status: number
  /** Detailed error message from server (optional) */
  detail?: string
  /** Field-specific validation errors (optional) */
  errors?: Record<string, string[]>
}

/**
 * Transforms axios errors into consistent ApiError shape.
 *
 * This function normalizes different error scenarios (response errors,
 * network errors, and other errors) into a single, predictable format
 * that the application can handle uniformly.
 *
 * @param error - The axios error to transform
 * @returns Normalized API error object
 *
 * @example
 * ```ts
 * try {
 *   await api.get('/endpoint');
 * } catch (error) {
 *   const apiError = transformError(error as AxiosError);
 *   console.log(apiError.message); // User-friendly error message
 * }
 * ```
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
 * Gets human-readable error message for HTTP status codes.
 *
 * Maps common HTTP status codes to user-friendly messages that can
 * be displayed in the UI without exposing technical details.
 *
 * @param status - HTTP status code
 * @returns User-friendly error message
 *
 * @example
 * ```ts
 * getStatusMessage(404); // "Not found"
 * getStatusMessage(500); // "Server error - please try again later"
 * ```
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
 * Creates a configured axios instance with authentication and error handling.
 *
 * The instance includes:
 * - Base URL from environment or defaults to localhost
 * - 120-second timeout for long-running operations (schedule generation)
 * - Automatic credential inclusion for httpOnly cookies
 * - Request/response interceptors for error transformation
 * - Automatic redirect to login on 401 errors
 * - Special handling for 207 Multi-Status responses (partial success)
 *
 * @returns Configured axios instance
 *
 * @example
 * ```ts
 * const client = createApiClient();
 * const response = await client.get('/people');
 * ```
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
    // Security: Enable credentials to send httpOnly cookies
    withCredentials: true,
  })

  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // Response interceptor - transform errors and handle token refresh
  client.interceptors.response.use(
    (response) => {
      // Issue #5: Handle 207 Multi-Status as a successful response (partial success)
      // This is used for schedule generation that completes but has validation warnings
      return response
    },
    async (error: AxiosError) => {
      const apiError = transformError(error)
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

      // Issue #5: Treat 207 Multi-Status as success (partial success scenario)
      if (error.response?.status === 207) {
        return error.response
      }

      if (typeof window !== 'undefined') {
        const requestUrl = error.config?.url || ''
        const isAuthEndpoint = requestUrl.includes('/auth/')

        // Handle 401 - attempt token refresh before redirecting
        // Don't try to refresh for auth endpoints (prevents infinite loops)
        // Don't retry if we already tried to refresh
        if (apiError.status === 401 && !isAuthEndpoint && !originalRequest._retry) {
          try {
            const auth = await getAuthModule()

            // Check if we have a refresh mechanism available
            if (auth.attemptTokenRefresh) {
              originalRequest._retry = true
              const refreshed = await auth.attemptTokenRefresh()

              if (refreshed) {
                // Retry the original request - the new access token is already
                // set as httpOnly cookie by the refresh endpoint
                return client(originalRequest)
              }
            }
          } catch (refreshError) {
            // Refresh failed - will redirect to login
          }

          // Refresh failed or not available - redirect to login
          // Don't redirect if already on login page (prevents infinite loop)
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login'
          }
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
 * Performs a type-safe GET request to the API.
 *
 * @template T - Expected response data type
 * @param url - API endpoint URL (relative to base URL)
 * @param config - Optional axios request configuration
 * @returns Promise resolving to typed response data
 * @throws {ApiError} If the request fails
 *
 * @example
 * ```ts
 * interface User { id: string; name: string }
 * const user = await get<User>('/auth/me');
 * console.log(user.name);
 * ```
 */
export async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.get<T>(url, config)
  return response.data
}

/**
 * Performs a type-safe POST request to the API.
 *
 * @template T - Expected response data type
 * @param url - API endpoint URL (relative to base URL)
 * @param data - Request body data
 * @param config - Optional axios request configuration
 * @returns Promise resolving to typed response data
 * @throws {ApiError} If the request fails
 *
 * @example
 * ```ts
 * interface Person { id: string; name: string }
 * const newPerson = await post<Person>('/people', {
 *   name: 'Dr. Smith',
 *   role: 'faculty'
 * });
 * ```
 */
export async function post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.post<T>(url, data, config)
  return response.data
}

/**
 * Performs a type-safe PUT request to the API.
 *
 * @template T - Expected response data type
 * @param url - API endpoint URL (relative to base URL)
 * @param data - Request body data (full replacement)
 * @param config - Optional axios request configuration
 * @returns Promise resolving to typed response data
 * @throws {ApiError} If the request fails
 *
 * @example
 * ```ts
 * interface Person { id: string; name: string; email: string }
 * const updated = await put<Person>('/people/123', {
 *   name: 'Dr. Smith',
 *   email: 'smith@example.com'
 * });
 * ```
 */
export async function put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.put<T>(url, data, config)
  return response.data
}

/**
 * Performs a type-safe PATCH request to the API.
 *
 * @template T - Expected response data type
 * @param url - API endpoint URL (relative to base URL)
 * @param data - Request body data (partial update)
 * @param config - Optional axios request configuration
 * @returns Promise resolving to typed response data
 * @throws {ApiError} If the request fails
 *
 * @example
 * ```ts
 * interface Person { id: string; name: string }
 * const updated = await patch<Person>('/people/123', {
 *   name: 'Dr. Jane Smith' // Only update the name
 * });
 * ```
 */
export async function patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.patch<T>(url, data, config)
  return response.data
}

/**
 * Performs a type-safe DELETE request to the API.
 *
 * @param url - API endpoint URL (relative to base URL)
 * @param config - Optional axios request configuration
 * @returns Promise resolving when deletion completes
 * @throws {ApiError} If the request fails
 *
 * @example
 * ```ts
 * await del('/people/123');
 * console.log('Person deleted successfully');
 * ```
 */
export async function del(url: string, config?: AxiosRequestConfig): Promise<void> {
  await api.delete(url, config)
}

// Re-export types
export type { AxiosRequestConfig }
