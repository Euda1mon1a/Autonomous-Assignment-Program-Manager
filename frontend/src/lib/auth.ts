/**
 * Authentication Library for Residency Scheduler
 *
 * Provides authentication API functions.
 *
 * Security: Uses httpOnly cookies for JWT tokens to prevent XSS attacks.
 * Tokens are no longer stored in localStorage.
 */
import { api, post, get, ApiError } from './api'

// ============================================================================
// Types
// ============================================================================

export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'coordinator' | 'faculty' | 'resident'
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface AuthCheckResponse {
  authenticated: boolean
  user?: User
}

// ============================================================================
// Authentication API Functions
// ============================================================================

/**
 * Login with username and password
 * POST /api/auth/login with form data
 *
 * Security: Token is set as httpOnly cookie by the server.
 * No client-side token storage needed.
 */
export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  // Create form data for OAuth2 password flow
  const formData = new URLSearchParams()
  formData.append('username', credentials.username)
  formData.append('password', credentials.password)

  const response = await api.post<LoginResponse>('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    withCredentials: true, // Required for cookies
  })

  return response.data
}

/**
 * Logout - call backend to invalidate session and delete cookie
 *
 * Security: Clears the httpOnly cookie server-side.
 */
export async function logout(): Promise<void> {
  try {
    await post('/auth/logout', {})
  } catch (error) {
    // Even if the request fails, the user should be logged out client-side
    console.error('Logout error:', error)
  }
}

/**
 * Get current authenticated user
 * GET /api/auth/me
 */
export async function getCurrentUser(): Promise<User> {
  return get<User>('/auth/me')
}

/**
 * Check authentication status
 * GET /api/auth/check
 */
export async function checkAuth(): Promise<AuthCheckResponse> {
  try {
    const response = await get<AuthCheckResponse>('/auth/check')
    return response
  } catch (error) {
    // If request fails, user is not authenticated
    return { authenticated: false }
  }
}

/**
 * Validate if current token is still valid
 * Returns user if valid, null otherwise
 *
 * Security: Checks httpOnly cookie by attempting to fetch current user.
 */
export async function validateToken(): Promise<User | null> {
  try {
    const user = await getCurrentUser()
    return user
  } catch (error) {
    // Token is invalid or missing
    return null
  }
}
