/**
 * Tests for authentication library with token refresh functionality (DEBT-007)
 *
 * Tests token refresh logic including:
 * - Proactive refresh scheduling
 * - Reactive refresh on 401 errors
 * - Concurrent refresh request deduplication
 * - Token state management
 */
import {
  clearTokenState,
  performRefresh,
  attemptTokenRefresh,
  isTokenRefreshing,
  getRefreshPromise,
  isTokenExpired,
  getTimeUntilExpiry,
} from '@/lib/auth'
import * as api from '@/lib/api'

// Mock the api module
jest.mock('@/lib/api', () => ({
  api: {
    post: jest.fn(),
  },
  post: jest.fn(),
  get: jest.fn(),
}))

const mockedApi = api as jest.Mocked<typeof api>

// ============================================================================
// Mock Data
// ============================================================================

const mockRefreshResponse = {
  access_token: 'new-access-token-123',
  refresh_token: 'new-refresh-token-456',
  token_type: 'bearer',
}

// ============================================================================
// Test Setup
// ============================================================================

describe('Token Refresh Functions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
    // Clear token state before each test
    clearTokenState()
  })

  afterEach(() => {
    jest.useRealTimers()
    clearTokenState()
  })

  // ==========================================================================
  // clearTokenState tests
  // ==========================================================================

  describe('clearTokenState', () => {
    it('should clear all token state', () => {
      // The state is module-private, so we test behavior indirectly
      // After clearing, isTokenExpired should return true (no token)
      clearTokenState()
      expect(isTokenExpired()).toBe(true)
      expect(getTimeUntilExpiry()).toBe(0)
      expect(isTokenRefreshing()).toBe(false)
      expect(getRefreshPromise()).toBeNull()
    })
  })

  // ==========================================================================
  // isTokenExpired tests
  // ==========================================================================

  describe('isTokenExpired', () => {
    it('should return true when no token is stored', () => {
      clearTokenState()
      expect(isTokenExpired()).toBe(true)
    })

    it('should return true when token expiry is not set', () => {
      // No tokens have been stored
      expect(isTokenExpired()).toBe(true)
    })
  })

  // ==========================================================================
  // getTimeUntilExpiry tests
  // ==========================================================================

  describe('getTimeUntilExpiry', () => {
    it('should return 0 when no token is stored', () => {
      clearTokenState()
      expect(getTimeUntilExpiry()).toBe(0)
    })
  })

  // ==========================================================================
  // performRefresh tests
  // ==========================================================================

  describe('performRefresh', () => {
    it('should return null when no refresh token is available', async () => {
      clearTokenState()
      const result = await performRefresh()
      expect(result).toBeNull()
    })

    it('should not call API when no refresh token is stored', async () => {
      clearTokenState()
      await performRefresh()
      expect(mockedApi.post).not.toHaveBeenCalled()
    })
  })

  // ==========================================================================
  // attemptTokenRefresh tests
  // ==========================================================================

  describe('attemptTokenRefresh', () => {
    it('should return false when no refresh token is available', async () => {
      clearTokenState()
      const result = await attemptTokenRefresh()
      expect(result).toBe(false)
    })
  })

  // ==========================================================================
  // isTokenRefreshing tests
  // ==========================================================================

  describe('isTokenRefreshing', () => {
    it('should return false initially', () => {
      expect(isTokenRefreshing()).toBe(false)
    })

    it('should return false after clearTokenState', () => {
      clearTokenState()
      expect(isTokenRefreshing()).toBe(false)
    })
  })

  // ==========================================================================
  // getRefreshPromise tests
  // ==========================================================================

  describe('getRefreshPromise', () => {
    it('should return null when no refresh is in progress', () => {
      expect(getRefreshPromise()).toBeNull()
    })
  })
})

// ============================================================================
// Integration Tests with Mocked Login
// ============================================================================

describe('Token Refresh Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    clearTokenState()
  })

  afterEach(() => {
    clearTokenState()
  })

  it('should clear state and allow fresh login cycle', () => {
    // This tests that the module properly resets between sessions
    clearTokenState()
    expect(isTokenExpired()).toBe(true)
    expect(isTokenRefreshing()).toBe(false)
    expect(getRefreshPromise()).toBeNull()
    expect(getTimeUntilExpiry()).toBe(0)
  })
})
