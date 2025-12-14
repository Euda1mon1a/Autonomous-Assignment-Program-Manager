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
  hasStoredToken,
} from '@/lib/auth'

// ============================================================================
// Types
// ============================================================================

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
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
  useEffect(() => {
    async function initAuth() {
      if (hasStoredToken()) {
        try {
          const validatedUser = await validateToken()
          setUser(validatedUser)
        } catch {
          // Token validation failed, user remains null
        }
      }
      setIsLoading(false)
    }

    initAuth()
  }, [])

  // Login function
  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true)
    try {
      const response = await authLogin(credentials)
      setUser(response.user)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Logout function
  const logout = useCallback(() => {
    authLogout()
    setUser(null)
  }, [])

  // Refresh user data
  const refreshUser = useCallback(async () => {
    if (hasStoredToken()) {
      try {
        const validatedUser = await validateToken()
        setUser(validatedUser)
      } catch {
        // Token no longer valid
        logout()
      }
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
