/**
 * Authentication Library for Residency Scheduler
 *
 * Provides token management and authentication API functions.
 */
import { api, get } from './api'

// Token storage key (consistent with api.ts interceptor)
const TOKEN_KEY = 'auth_token'

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

export interface TokenResponse {
  access_token: string
  token_type: string
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
// Token Management
// ============================================================================

/**
 * Get stored authentication token from localStorage
 */
export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * Store authentication token in localStorage
 */
export function setStoredToken(token: string): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(TOKEN_KEY, token)
}

/**
 * Remove authentication token from localStorage
 */
export function removeStoredToken(): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem(TOKEN_KEY)
}

/**
 * Check if user has a stored token
 */
export function hasStoredToken(): boolean {
  return !!getStoredToken()
}

// ============================================================================
// Authentication API Functions
// ============================================================================

/**
 * Login with username and password
 * POST /api/auth/login with form data, then fetch user
 */
export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  // Create form data for OAuth2 password flow
  const formData = new URLSearchParams()
  formData.append('username', credentials.username)
  formData.append('password', credentials.password)

  const response = await api.post<TokenResponse>('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })

  const tokenData = response.data

  // Store the token
  if (tokenData.access_token) {
    setStoredToken(tokenData.access_token)
  }

  // Fetch user info with the new token
  const user = await getCurrentUser()

  return {
    access_token: tokenData.access_token,
    token_type: tokenData.token_type,
    user,
  }
}

/**
 * Logout - remove stored token
 */
export function logout(): void {
  removeStoredToken()
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
 */
export async function validateToken(): Promise<User | null> {
  const token = getStoredToken()
  if (!token) return null

  try {
    const user = await getCurrentUser()
    return user
  } catch (error) {
    // Token is invalid, remove it
    removeStoredToken()
    return null
  }
}
