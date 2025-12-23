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

  // Validate token and load user on mount
  // Security: Checks httpOnly cookie automatically via validateToken
  useEffect(() => {
    async function initAuth() {
<<<<<<< HEAD
      console.log('[AuthContext] initAuth() - checking for existing session...')
      try {
        const validatedUser = await validateToken()
        console.log('[AuthContext] initAuth() - session found:', { userId: validatedUser?.id })
        setUser(validatedUser)
      } catch (error) {
        // Token validation failed, user remains null
        console.log('[AuthContext] initAuth() - no valid session (this is normal for login page)')
      }
      setIsLoading(false)
      console.log('[AuthContext] initAuth() - complete, isLoading=false')
=======
      try {
        const validatedUser = await validateToken()
        setUser(validatedUser)
      } catch (error) {
        // Token validation failed, user remains null
        console.error('Token validation failed:', error)
      }
      setIsLoading(false)
>>>>>>> origin/docs/session-14-summary
    }

    initAuth()
  }, [])

  // Login function
  const login = useCallback(async (credentials: LoginCredentials) => {
<<<<<<< HEAD
    console.log('[AuthContext] login() - starting login for:', credentials.username)
    setIsLoading(true)
    try {
      const response = await authLogin(credentials)
      console.log('[AuthContext] login() - SUCCESS, user:', response.user?.username)
      setUser(response.user)
    } catch (err) {
      console.error('[AuthContext] login() - FAILED:', err)
      throw err  // Re-throw so LoginForm can catch it
    } finally {
      setIsLoading(false)
      console.log('[AuthContext] login() - complete')
=======
    setIsLoading(true)
    try {
      const response = await authLogin(credentials)
      setUser(response.user)
    } finally {
      setIsLoading(false)
>>>>>>> origin/docs/session-14-summary
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
      console.error('Token refresh failed:', error)
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
