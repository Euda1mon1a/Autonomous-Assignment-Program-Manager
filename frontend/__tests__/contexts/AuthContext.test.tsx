/**
 * Tests for AuthContext and AuthProvider
 *
 * Tests authentication state management, login/logout flows, and
 * session persistence behavior.
 */
import React from 'react'
import { render, screen, waitFor, act } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'

// Mock the auth library
const mockAuthLogin = jest.fn()
const mockAuthLogout = jest.fn()
const mockValidateToken = jest.fn()

jest.mock('@/lib/auth', () => ({
  login: (...args: unknown[]) => mockAuthLogin(...args),
  logout: (...args: unknown[]) => mockAuthLogout(...args),
  validateToken: (...args: unknown[]) => mockValidateToken(...args),
}))

// Test component that uses the auth context
function TestConsumer({ testId = 'test-consumer' }: { testId?: string }) {
  const { user, isLoading, isAuthenticated, login, logout, refreshUser } = useAuth()

  return (
    <div data-testid={testId}>
      <div data-testid="loading-state">{isLoading ? 'loading' : 'not-loading'}</div>
      <div data-testid="auth-state">{isAuthenticated ? 'authenticated' : 'not-authenticated'}</div>
      <div data-testid="user-state">{user ? JSON.stringify(user) : 'no-user'}</div>
      <button
        data-testid="login-btn"
        onClick={() => login({ username: 'test', password: 'pass' })}
      >
        Login
      </button>
      <button data-testid="logout-btn" onClick={() => logout()}>
        Logout
      </button>
      <button data-testid="refresh-btn" onClick={() => refreshUser()}>
        Refresh
      </button>
    </div>
  )
}

// Component that tests the useAuth hook outside of provider
function InvalidConsumer() {
  try {
    useAuth()
    return <div>No error thrown</div>
  } catch (error) {
    return <div data-testid="error-message">{(error as Error).message}</div>
  }
}

describe('AuthContext', () => {
  const mockUser = {
    id: 'user-1',
    username: 'testuser',
    email: 'test@example.com',
    role: 'admin' as const,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
  }

  beforeEach(() => {
    jest.clearAllMocks()
    // Default: no existing session
    mockValidateToken.mockResolvedValue(null)
    mockAuthLogin.mockResolvedValue({
      access_token: 'mock-token',
      token_type: 'bearer',
      user: mockUser,
    })
    mockAuthLogout.mockResolvedValue(true)
  })

  describe('Provider Setup', () => {
    it('should render children within AuthProvider', () => {
      render(
        <AuthProvider>
          <div data-testid="child-content">Child Content</div>
        </AuthProvider>
      )

      expect(screen.getByTestId('child-content')).toBeInTheDocument()
      expect(screen.getByText('Child Content')).toBeInTheDocument()
    })

    it('should throw error when useAuth is used outside AuthProvider', () => {
      // Suppress console.error for this test since we expect an error
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

      render(<InvalidConsumer />)

      expect(screen.getByTestId('error-message')).toHaveTextContent(
        'useAuth must be used within an AuthProvider'
      )

      consoleSpy.mockRestore()
    })

    it('should provide auth context to nested components', () => {
      render(
        <AuthProvider>
          <div>
            <div>
              <TestConsumer />
            </div>
          </div>
        </AuthProvider>
      )

      expect(screen.getByTestId('test-consumer')).toBeInTheDocument()
    })
  })

  describe('Initial State', () => {
    it('should start in loading state', () => {
      // Make validateToken hang to keep loading state
      mockValidateToken.mockImplementation(() => new Promise(() => {}))

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      expect(screen.getByTestId('loading-state')).toHaveTextContent('loading')
    })

    it('should start not authenticated', async () => {
      mockValidateToken.mockResolvedValue(null)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toHaveTextContent('not-loading')
      })

      expect(screen.getByTestId('auth-state')).toHaveTextContent('not-authenticated')
    })

    it('should start with no user', async () => {
      mockValidateToken.mockResolvedValue(null)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toHaveTextContent('not-loading')
      })

      expect(screen.getByTestId('user-state')).toHaveTextContent('no-user')
    })
  })

  describe('Session Validation on Mount', () => {
    it('should call validateToken on mount to check existing session', async () => {
      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(mockValidateToken).toHaveBeenCalledTimes(1)
      })
    })

    it('should set user from valid session', async () => {
      mockValidateToken.mockResolvedValue(mockUser)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      const userState = JSON.parse(screen.getByTestId('user-state').textContent || '{}')
      expect(userState.username).toBe('testuser')
    })

    it('should remain unauthenticated when no valid session exists', async () => {
      mockValidateToken.mockResolvedValue(null)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toHaveTextContent('not-loading')
      })

      expect(screen.getByTestId('auth-state')).toHaveTextContent('not-authenticated')
    })

    it('should handle validation error gracefully', async () => {
      mockValidateToken.mockRejectedValue(new Error('Validation failed'))

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toHaveTextContent('not-loading')
      })

      // Should remain unauthenticated on error
      expect(screen.getByTestId('auth-state')).toHaveTextContent('not-authenticated')
      expect(screen.getByTestId('user-state')).toHaveTextContent('no-user')
    })

    it('should set isLoading to false after validation completes', async () => {
      mockValidateToken.mockResolvedValue(mockUser)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      // Should start loading
      expect(screen.getByTestId('loading-state')).toHaveTextContent('loading')

      // Should stop loading after validation
      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toHaveTextContent('not-loading')
      })
    })
  })

  describe('Login Flow', () => {
    it('should update user state on successful login', async () => {
      const user = userEvent.setup()
      mockValidateToken.mockResolvedValue(null)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toHaveTextContent('not-loading')
      })

      // Perform login
      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      const userState = JSON.parse(screen.getByTestId('user-state').textContent || '{}')
      expect(userState.username).toBe('testuser')
    })

    it('should call auth login with correct credentials', async () => {
      const user = userEvent.setup()
      mockValidateToken.mockResolvedValue(null)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toHaveTextContent('not-loading')
      })

      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        expect(mockAuthLogin).toHaveBeenCalledWith({
          username: 'test',
          password: 'pass',
        })
      })
    })

    it('should set isAuthenticated to true after login', async () => {
      const user = userEvent.setup()
      mockValidateToken.mockResolvedValue(null)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toHaveTextContent('not-loading')
      })

      expect(screen.getByTestId('auth-state')).toHaveTextContent('not-authenticated')

      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })
    })

    it('should propagate login errors', async () => {
      const user = userEvent.setup()
      mockValidateToken.mockResolvedValue(null)
      mockAuthLogin.mockRejectedValue(new Error('Invalid credentials'))

      // Create a test component that catches login errors
      function TestLoginWithError() {
        const { login, isLoading } = useAuth()
        const [error, setError] = React.useState<string | null>(null)

        return (
          <div>
            <div data-testid="loading">{isLoading ? 'loading' : 'not-loading'}</div>
            <div data-testid="error">{error || 'no-error'}</div>
            <button
              onClick={async () => {
                try {
                  await login({ username: 'test', password: 'wrong' })
                } catch (e) {
                  setError((e as Error).message)
                }
              }}
            >
              Login
            </button>
          </div>
        )
      }

      render(
        <AuthProvider>
          <TestLoginWithError />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
      })

      await user.click(screen.getByRole('button', { name: /login/i }))

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Invalid credentials')
      })
    })

    it('should set isLoading during login process', async () => {
      const user = userEvent.setup()
      mockValidateToken.mockResolvedValue(null)

      // Make login slow so we can observe loading state
      let resolveLogin: (value: unknown) => void
      mockAuthLogin.mockImplementation(
        () =>
          new Promise((resolve) => {
            resolveLogin = resolve
          })
      )

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toHaveTextContent('not-loading')
      })

      // Start login
      await user.click(screen.getByTestId('login-btn'))

      // Should be loading during login
      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toHaveTextContent('loading')
      })

      // Complete login
      await act(async () => {
        resolveLogin!({
          access_token: 'mock-token',
          token_type: 'bearer',
          user: mockUser,
        })
      })

      // Should stop loading
      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toHaveTextContent('not-loading')
      })
    })
  })

  describe('Logout Flow', () => {
    it('should clear user state on logout', async () => {
      const user = userEvent.setup()
      mockValidateToken.mockResolvedValue(mockUser)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      // Wait for authenticated state
      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      // Perform logout
      await user.click(screen.getByTestId('logout-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('not-authenticated')
      })

      expect(screen.getByTestId('user-state')).toHaveTextContent('no-user')
    })

    it('should call auth logout function', async () => {
      const user = userEvent.setup()
      mockValidateToken.mockResolvedValue(mockUser)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      await user.click(screen.getByTestId('logout-btn'))

      await waitFor(() => {
        expect(mockAuthLogout).toHaveBeenCalledTimes(1)
      })
    })

    it('should set isAuthenticated to false after logout', async () => {
      const user = userEvent.setup()
      mockValidateToken.mockResolvedValue(mockUser)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      await user.click(screen.getByTestId('logout-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('not-authenticated')
      })
    })
  })

  describe('Refresh User Flow', () => {
    it('should update user state on successful refresh', async () => {
      const user = userEvent.setup()
      mockValidateToken.mockResolvedValue(mockUser)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      // Update the mock to return different user data
      const updatedUser = { ...mockUser, username: 'updateduser' }
      mockValidateToken.mockResolvedValue(updatedUser)

      await user.click(screen.getByTestId('refresh-btn'))

      await waitFor(() => {
        const userState = JSON.parse(screen.getByTestId('user-state').textContent || '{}')
        expect(userState.username).toBe('updateduser')
      })
    })

    it('should call logout if refresh fails', async () => {
      const user = userEvent.setup()
      mockValidateToken.mockResolvedValueOnce(mockUser)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      // Make next validateToken call fail
      mockValidateToken.mockRejectedValueOnce(new Error('Token expired'))

      await user.click(screen.getByTestId('refresh-btn'))

      // Should trigger logout
      await waitFor(() => {
        expect(mockAuthLogout).toHaveBeenCalled()
      })
    })
  })

  describe('Context Value Stability', () => {
    it('should provide stable function references', async () => {
      mockValidateToken.mockResolvedValue(null)

      // Track function references
      const loginRefs: unknown[] = []
      const logoutRefs: unknown[] = []
      let rerender: ((element: React.ReactElement) => void) | null = null

      function ReferenceTracker() {
        const { login, logout } = useAuth()

        // Track references immediately on render
        React.useLayoutEffect(() => {
          loginRefs.push(login)
          logoutRefs.push(logout)
        })

        return null
      }

      const { rerender: rerenderFn } = render(
        <AuthProvider>
          <ReferenceTracker />
        </AuthProvider>
      )
      rerender = rerenderFn

      // Wait for initial render
      await waitFor(() => {
        expect(loginRefs.length).toBeGreaterThan(0)
      })

      const initialLoginRef = loginRefs[0]

      // Force rerender of entire tree
      if (rerender) {
        await act(async () => {
          rerender(
            <AuthProvider>
              <ReferenceTracker />
            </AuthProvider>
          )
        })
      }

      await waitFor(() => {
        expect(loginRefs.length).toBeGreaterThan(1)
      })

      // useCallback should ensure stable references across rerenders
      expect(loginRefs[0]).toBe(loginRefs[1])
      expect(logoutRefs[0]).toBe(logoutRefs[1])
      expect(loginRefs[0]).toBe(initialLoginRef)
    })
  })

  describe('Multiple Consumers', () => {
    it('should provide same state to multiple consumers', async () => {
      mockValidateToken.mockResolvedValue(mockUser)

      render(
        <AuthProvider>
          <TestConsumer testId="consumer-1" />
          <TestConsumer testId="consumer-2" />
        </AuthProvider>
      )

      await waitFor(() => {
        const consumer1 = screen.getByTestId('consumer-1')
        const consumer2 = screen.getByTestId('consumer-2')

        // Both consumers should see authenticated state
        expect(consumer1.querySelector('[data-testid="auth-state"]')).toHaveTextContent(
          'authenticated'
        )
        expect(consumer2.querySelector('[data-testid="auth-state"]')).toHaveTextContent(
          'authenticated'
        )
      })
    })

    it('should update all consumers when state changes', async () => {
      const user = userEvent.setup()
      mockValidateToken.mockResolvedValue(mockUser)

      render(
        <AuthProvider>
          <TestConsumer testId="consumer-1" />
          <TestConsumer testId="consumer-2" />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(
          screen.getByTestId('consumer-1').querySelector('[data-testid="auth-state"]')
        ).toHaveTextContent('authenticated')
      })

      // Logout from first consumer
      const logoutBtn = screen.getByTestId('consumer-1').querySelector('[data-testid="logout-btn"]')
      await user.click(logoutBtn!)

      // Both consumers should update
      await waitFor(() => {
        expect(
          screen.getByTestId('consumer-1').querySelector('[data-testid="auth-state"]')
        ).toHaveTextContent('not-authenticated')
        expect(
          screen.getByTestId('consumer-2').querySelector('[data-testid="auth-state"]')
        ).toHaveTextContent('not-authenticated')
      })
    })
  })

  describe('Edge Cases', () => {
    it('should handle rapid login/logout cycles', async () => {
      const user = userEvent.setup()
      mockValidateToken.mockResolvedValue(null)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toHaveTextContent('not-loading')
      })

      // Rapid login/logout
      await user.click(screen.getByTestId('login-btn'))
      await user.click(screen.getByTestId('logout-btn'))
      await user.click(screen.getByTestId('login-btn'))

      // Should eventually settle in authenticated state
      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })
    })

    it('should handle login during existing session', async () => {
      const user = userEvent.setup()
      mockValidateToken.mockResolvedValue(mockUser)

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
      })

      // Login again with different user
      const newUser = { ...mockUser, username: 'newuser' }
      mockAuthLogin.mockResolvedValue({
        access_token: 'new-token',
        token_type: 'bearer',
        user: newUser,
      })

      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        const userState = JSON.parse(screen.getByTestId('user-state').textContent || '{}')
        expect(userState.username).toBe('newuser')
      })
    })
  })
})
