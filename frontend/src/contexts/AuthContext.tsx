'use client'

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react'
import {
  User,
  LoginCredentials,
  login as authLogin,
  logout as authLogout,
  validateToken,
  restoreSession,
} from '@/lib/auth'

// ============================================================================
// Types
// ============================================================================

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

// ============================================================================
// Context
// ============================================================================

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// ============================================================================
// Provider
// ============================================================================

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user

  // Restore session on mount
  // First tries to restore from sessionStorage (for page refresh),
  // then validates the token to get user data.
  useEffect(() => {
    // Timeout for auth check to prevent infinite loading on network issues
    const AUTH_TIMEOUT_MS = 5000

    async function initAuth() {
      try {
        // Try to restore session from sessionStorage first
        // This handles page refresh where in-memory tokens are lost
        const restored = await restoreSession()
        console.log('[AuthContext] restoreSession result:', restored)

        // Now validate the token to get user data
        // If session was restored, we have a fresh access token
        // If not, this will fail and user will need to log in
        const validatedUser = await validateToken()
        setUser(validatedUser)
      } catch {
        // Token validation failed, user remains null (needs to log in)
        console.log('[AuthContext] Session validation failed, user needs to log in')
      }
      setIsLoading(false)
    }

    // Race auth init against timeout to prevent infinite loading
    // If auth takes longer than timeout, assume not authenticated
    const timeoutPromise = new Promise<void>((resolve) => {
      setTimeout(() => {
        console.log('[AuthContext] Auth check timed out, proceeding as unauthenticated')
        resolve()
      }, AUTH_TIMEOUT_MS)
    })

    Promise.race([initAuth(), timeoutPromise]).then(() => {
      // Ensure loading is set to false regardless of which promise resolved
      setIsLoading(false)
    })
  }, [])

  // Login function
  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true)
    try {
      const response = await authLogin(credentials)
      setUser(response.user)
    } catch (err) {
      throw err  // Re-throw so LoginForm can catch it
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Logout function
  // Security: Calls backend to invalidate session and clear httpOnly cookie
  const logout = useCallback(async () => {
    await authLogout()
    setUser(null)
  }, [])

  // Refresh user data
  // Security: Checks httpOnly cookie automatically via validateToken
  const refreshUser = useCallback(async () => {
    try {
      const validatedUser = await validateToken()
      setUser(validatedUser)
    } catch (error) {
      // Token no longer valid
      if (process.env.NODE_ENV === 'development') {
        console.error('Token refresh failed:', error)
      }
      logout()
    }
  }, [logout])

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Hook to access authentication context
 * Must be used within an AuthProvider
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
