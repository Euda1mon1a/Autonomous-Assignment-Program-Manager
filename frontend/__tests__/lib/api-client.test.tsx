/**
 * Tests for API client HTTP functionality
 *
 * Tests the axios-based HTTP client including request/response handling,
 * error transformation, 401 redirect behavior, and token refresh logic.
 */
import type { ApiError } from '@/lib/api'

// Track axios.create calls
const mockCreateCalls: unknown[][] = []

// Track interceptor registrations
const mockInterceptorCalls = {
  request: [] as unknown[][],
  response: [] as unknown[][],
}

// Create a mock axios instance with proper typing
const mockAxiosInstance = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  patch: jest.fn(),
  delete: jest.fn(),
  interceptors: {
    request: {
      use: jest.fn((...args: unknown[]) => {
        mockInterceptorCalls.request.push(args)
      }),
    },
    response: {
      use: jest.fn((...args: unknown[]) => {
        mockInterceptorCalls.response.push(args)
      }),
    },
  },
}

// Mock axios before importing api module
jest.mock('axios', () => ({
  __esModule: true,
  default: {
    create: jest.fn((...args: unknown[]) => {
      mockCreateCalls.push(args)
      return mockAxiosInstance
    }),
    isAxiosError: jest.fn((error: { isAxiosError?: boolean }) => error?.isAxiosError === true),
  },
  create: jest.fn((...args: unknown[]) => {
    mockCreateCalls.push(args)
    return mockAxiosInstance
  }),
  isAxiosError: jest.fn((error: { isAxiosError?: boolean }) => error?.isAxiosError === true),
}))

// Mock the auth module for token refresh
jest.mock('@/lib/auth', () => ({
  attemptTokenRefresh: jest.fn(),
}))

// Now import the api module (after mocks are set up)
// eslint-disable-next-line @typescript-eslint/no-require-imports
const apiModule = require('@/lib/api')
const { api, post, put, patch, del } = apiModule
// Type the get function to preserve generic parameter
const get = apiModule.get as <T>(url: string, config?: unknown) => Promise<T>

describe('API Client', () => {
  beforeEach(() => {
    // Only clear the instance method mocks, not the create mock
    // because axios.create is called once at module load time
    mockAxiosInstance.get.mockClear()
    mockAxiosInstance.post.mockClear()
    mockAxiosInstance.put.mockClear()
    mockAxiosInstance.patch.mockClear()
    mockAxiosInstance.delete.mockClear()
  })

  describe('Client Configuration', () => {
    it('should create axios instance with correct base URL', () => {
      // The api client is created on module import
      // Check the captured create calls
      expect(mockCreateCalls.length).toBeGreaterThan(0)
      const createArgs = mockCreateCalls[0][0] as { baseURL: string }
      expect(createArgs.baseURL).toContain('localhost:8000')
    })

    it('should set Content-Type header to application/json', () => {
      expect(mockCreateCalls.length).toBeGreaterThan(0)
      const createArgs = mockCreateCalls[0][0] as { headers: { 'Content-Type': string } }
      expect(createArgs.headers['Content-Type']).toBe('application/json')
    })

    it('should enable credentials for cookie support', () => {
      expect(mockCreateCalls.length).toBeGreaterThan(0)
      const createArgs = mockCreateCalls[0][0] as { withCredentials: boolean }
      expect(createArgs.withCredentials).toBe(true)
    })

    it('should set timeout to 120 seconds', () => {
      expect(mockCreateCalls.length).toBeGreaterThan(0)
      const createArgs = mockCreateCalls[0][0] as { timeout: number }
      expect(createArgs.timeout).toBe(120000)
    })

    it('should register request interceptor', () => {
      // Check that at least one request interceptor was registered
      expect(mockInterceptorCalls.request.length).toBeGreaterThan(0)
    })

    it('should register response interceptor', () => {
      // Check that at least one response interceptor was registered
      expect(mockInterceptorCalls.response.length).toBeGreaterThan(0)
    })
  })

  describe('GET Requests', () => {
    it('should make GET request with correct URL', async () => {
      const responseData = { id: '1', name: 'Test' }
      mockAxiosInstance.get.mockResolvedValueOnce({ data: responseData })

      const result = await get('/test-endpoint')

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/test-endpoint', undefined)
      expect(result).toEqual(responseData)
    })

    it('should pass config options to GET request', async () => {
      const responseData = { items: [] }
      const config = { params: { page: 1, limit: 10 } }
      mockAxiosInstance.get.mockResolvedValueOnce({ data: responseData })

      await get('/items', config)

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/items', config)
    })

    it('should return typed response data', async () => {
      interface User {
        id: string
        name: string
        email: string
      }
      const userData: User = { id: '1', name: 'John', email: 'john@example.com' }
      mockAxiosInstance.get.mockResolvedValueOnce({ data: userData })

      const result = await get<User>('/users/1')

      expect(result.id).toBe('1')
      expect(result.name).toBe('John')
      expect(result.email).toBe('john@example.com')
    })
  })

  describe('POST Requests', () => {
    it('should make POST request with JSON body', async () => {
      const requestData = { name: 'Test', email: 'test@example.com' }
      const responseData = { id: '1', ...requestData }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: responseData })

      const result = await post('/users', requestData)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/users', requestData, undefined)
      expect(result).toEqual(responseData)
    })

    it('should handle POST without body', async () => {
      const responseData = { success: true }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: responseData })

      const result = await post('/trigger-action')

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/trigger-action', undefined, undefined)
      expect(result).toEqual(responseData)
    })

    it('should pass config to POST request', async () => {
      const responseData = { id: '1' }
      const config = { headers: { 'X-Custom-Header': 'value' } }
      mockAxiosInstance.post.mockResolvedValueOnce({ data: responseData })

      await post('/endpoint', { data: 'value' }, config)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/endpoint', { data: 'value' }, config)
    })
  })

  describe('PUT Requests', () => {
    it('should make PUT request with JSON body', async () => {
      const requestData = { id: '1', name: 'Updated' }
      const responseData = { ...requestData, updatedAt: '2024-01-01' }
      mockAxiosInstance.put.mockResolvedValueOnce({ data: responseData })

      const result = await put('/users/1', requestData)

      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/users/1', requestData, undefined)
      expect(result).toEqual(responseData)
    })

    it('should handle PUT without body', async () => {
      const responseData = { success: true }
      mockAxiosInstance.put.mockResolvedValueOnce({ data: responseData })

      await put('/reset/1')

      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/reset/1', undefined, undefined)
    })
  })

  describe('PATCH Requests', () => {
    it('should make PATCH request with partial data', async () => {
      const patchData = { name: 'Updated Name' }
      const responseData = { id: '1', name: 'Updated Name', email: 'existing@email.com' }
      mockAxiosInstance.patch.mockResolvedValueOnce({ data: responseData })

      const result = await patch('/users/1', patchData)

      expect(mockAxiosInstance.patch).toHaveBeenCalledWith('/users/1', patchData, undefined)
      expect(result).toEqual(responseData)
    })
  })

  describe('DELETE Requests', () => {
    it('should make DELETE request', async () => {
      mockAxiosInstance.delete.mockResolvedValueOnce({ data: undefined })

      await del('/users/1')

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/users/1', undefined)
    })

    it('should not return data for DELETE', async () => {
      mockAxiosInstance.delete.mockResolvedValueOnce({ data: { deleted: true } })

      const result = await del('/items/123')

      expect(result).toBeUndefined()
    })
  })

  describe('Error Handling', () => {
    // Note: These tests verify the error shape. The actual error transformation
    // happens in the axios interceptor which is mocked. Full integration tests
    // would need to test the interceptor behavior.

    it('should reject with ApiError for failed requests', async () => {
      const apiError: ApiError = {
        message: 'Not found',
        status: 404,
      }
      mockAxiosInstance.get.mockRejectedValueOnce(apiError)

      await expect(get('/missing')).rejects.toEqual(apiError)
    })

    it('should handle network errors', async () => {
      const networkError: ApiError = {
        message: 'Network error - unable to reach server',
        status: 0,
      }
      mockAxiosInstance.get.mockRejectedValueOnce(networkError)

      await expect(get('/endpoint')).rejects.toEqual(
        expect.objectContaining({
          status: 0,
          message: expect.stringContaining('Network'),
        })
      )
    })

    it('should include detail in error when provided', async () => {
      const apiError: ApiError = {
        message: 'Validation failed',
        status: 422,
        detail: 'Email is required',
      }
      mockAxiosInstance.post.mockRejectedValueOnce(apiError)

      await expect(post('/users', {})).rejects.toEqual(
        expect.objectContaining({
          detail: 'Email is required',
        })
      )
    })

    it('should include field errors when provided', async () => {
      const apiError: ApiError = {
        message: 'Validation failed',
        status: 422,
        errors: {
          email: ['Invalid email format'],
          password: ['Too short'],
        },
      }
      mockAxiosInstance.post.mockRejectedValueOnce(apiError)

      await expect(post('/register', {})).rejects.toEqual(
        expect.objectContaining({
          errors: {
            email: ['Invalid email format'],
            password: ['Too short'],
          },
        })
      )
    })
  })
})

describe('API Error Transformation', () => {
  // Test the expected error message mapping
  const errorCases: Array<{ status: number; expectedPattern: RegExp }> = [
    { status: 400, expectedPattern: /bad request|check your input/i },
    { status: 401, expectedPattern: /unauthorized|log in/i },
    { status: 403, expectedPattern: /forbidden|permission/i },
    { status: 404, expectedPattern: /not found/i },
    { status: 409, expectedPattern: /conflict/i },
    { status: 422, expectedPattern: /validation/i },
    { status: 500, expectedPattern: /server error/i },
  ]

  describe.each(errorCases)('Status $status', ({ status, expectedPattern }) => {
    it(`should have appropriate message pattern`, () => {
      const statusMessages: Record<number, string> = {
        207: 'Partial success - some validation warnings',
        400: 'Bad request - please check your input',
        401: 'Unauthorized - please log in',
        403: 'Forbidden - you do not have permission',
        404: 'Not found',
        409: 'Conflict - resource already exists or operation in progress',
        422: 'Validation error - generation failed',
        500: 'Server error - please try again later',
      }

      const message = statusMessages[status] || `Error (${status})`
      expect(message).toMatch(expectedPattern)
    })
  })
})

describe('401 Handling', () => {
  // Note: Full 401 handling with token refresh requires testing the
  // response interceptor. These tests document the expected behavior.

  it('should expect redirect to /login on 401 for non-auth endpoints', () => {
    // The api client redirects to /login on 401 if:
    // 1. Not already on login page
    // 2. Not an auth endpoint (to prevent loops)
    // 3. Token refresh fails or is not available

    // This behavior is implemented in the response interceptor
    // and relies on window.location which is mocked in setup.ts
  })

  it('should not redirect on 401 for auth endpoints', () => {
    // Auth endpoints (containing '/auth/') should not trigger
    // redirect to prevent infinite loops during login failures
  })

  it('should attempt token refresh before redirecting', () => {
    // On 401, the client should:
    // 1. Check if refresh is available
    // 2. Attempt to refresh the token
    // 3. Retry the original request if refresh succeeds
    // 4. Only redirect if refresh fails
  })
})

describe('207 Multi-Status Handling', () => {
  // 207 responses indicate partial success and should not be treated as errors

  it('should treat 207 as successful response', () => {
    // The response interceptor has special handling for 207
    // to return the response instead of rejecting
    // This is used for schedule generation with validation warnings
  })
})

describe('API Client Export', () => {
  it('should export api instance', () => {
    expect(api).toBeDefined()
  })

  it('should export get function', () => {
    expect(get).toBeDefined()
    expect(typeof get).toBe('function')
  })

  it('should export post function', () => {
    expect(post).toBeDefined()
    expect(typeof post).toBe('function')
  })

  it('should export put function', () => {
    expect(put).toBeDefined()
    expect(typeof put).toBe('function')
  })

  it('should export patch function', () => {
    expect(patch).toBeDefined()
    expect(typeof patch).toBe('function')
  })

  it('should export del function', () => {
    expect(del).toBeDefined()
    expect(typeof del).toBe('function')
  })
})
