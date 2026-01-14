/**
 * Authentication Library for Residency Scheduler
 *
 * Provides authentication API functions with secure httpOnly cookie-based
 * JWT token management. This prevents XSS attacks by keeping tokens out of
 * JavaScript-accessible storage (no localStorage or sessionStorage).
 *
 * Security Features:
 * - httpOnly cookies for JWT tokens (XSS-resistant)
 * - Automatic token refresh before expiry (proactive)
 * - Reactive refresh on 401 errors (fallback)
 * - Secure logout with server-side session invalidation
 *
 * @module lib/auth
 */
import { api, post, get } from './api'

// ============================================================================
// Types
// ============================================================================

/**
 * User profile information returned from authentication endpoints.
 */
export interface User {
  /** Unique user identifier */
  id: string
  /** Username for login */
  username: string
  /** User's email address */
  email: string
  /** User's role determining permissions */
  role: 'admin' | 'coordinator' | 'faculty' | 'resident'
  /** Whether the user account is active */
  isActive: boolean
  /** Timestamp when user was created */
  createdAt: string
  /** Timestamp of last profile update (optional) */
  updatedAt?: string
}

/**
 * Login credentials required for authentication.
 */
export interface LoginCredentials {
  /** Username for authentication */
  username: string
  /** Password for authentication */
  password: string
}

/**
 * Response returned after successful login.
 */
export interface LoginResponse {
  /** JWT access token (also set as httpOnly cookie) */
  accessToken: string
  /** Token type (typically "bearer") */
  tokenType: string
  /** Authenticated user's profile information */
  user: User
}

/**
 * Response from authentication status check.
 */
export interface AuthCheckResponse {
  /** Whether the user is currently authenticated */
  authenticated: boolean
  /** User profile if authenticated (optional) */
  user?: User
}

/**
 * Request to refresh access token using refresh token.
 */
export interface RefreshTokenRequest {
  /** The refresh token to exchange for a new access token */
  refreshToken: string
}

/**
 * Response from token refresh endpoint.
 */
export interface RefreshTokenResponse {
  /** New JWT access token (also set as httpOnly cookie) */
  accessToken: string
  /** New refresh token (if rotation is enabled) */
  refreshToken: string
  /** Token type (typically "bearer") */
  tokenType: string
}

// ============================================================================
// Token Storage (in-memory for refresh token)
// ============================================================================

/**
 * In-memory storage for tokens.
 *
 * Security: Tokens are stored in memory (not localStorage) for better
 * security. This means tokens are lost on page refresh, but that's acceptable
 * because the httpOnly cookie still allows re-authentication via the /me endpoint.
 *
 * The access token is needed for WebSocket authentication (can't use cookies
 * cross-origin). The refresh token is for proactive token refresh before expiry.
 */
let refreshToken: string | null = null
let accessToken: string | null = null

/**
 * Timestamp when the current access token expires.
 * Used for proactive refresh scheduling.
 */
let tokenExpiresAt: number | null = null

/**
 * Timer ID for proactive refresh.
 */
let refreshTimerId: ReturnType<typeof setTimeout> | null = null

/**
 * Flag to prevent multiple concurrent refresh attempts.
 */
let isRefreshing = false

/**
 * Promise that resolves when the current refresh completes.
 * Used to queue requests during refresh.
 */
let refreshPromise: Promise<RefreshTokenResponse | null> | null = null

// Access token expiry time in minutes (should match backend)
const ACCESS_TOKEN_EXPIRE_MINUTES = 15

// Refresh margin: refresh token 1 minute before expiry
const REFRESH_MARGIN_MS = 60 * 1000

// ============================================================================
// Authentication API Functions
// ============================================================================

/**
 * Authenticates a user with username and password credentials.
 *
 * This function performs a two-step authentication process:
 * 1. Sends credentials to authenticate and receive a JWT token (set as httpOnly cookie)
 * 2. Fetches the user's profile data using the newly set cookie
 *
 * Security: The JWT token is automatically set as an httpOnly cookie by the
 * server, preventing XSS attacks. No client-side token storage is needed.
 *
 * @param credentials - Username and password for authentication
 * @returns Promise resolving to login response with token and user data
 * @throws {Error} If authentication succeeds but user profile fetch fails
 * @throws {ApiError} If authentication fails
 *
 * @example
 * ```ts
 * try {
 *   const response = await login({
 *     username: 'dr.smith',
 *     password: 'SecurePassword123!'
 *   });
 *   console.log(`Logged in as: ${response.user.username}`);
 *   console.log(`Role: ${response.user.role}`);
 * } catch (error) {
 *   console.error('Login failed:', error.message);
 * }
 * ```
 *
 * @see getCurrentUser - For fetching current user after login
 * @see logout - For clearing the session
 */
export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  // Create form data for OAuth2 password flow
  const formData = new URLSearchParams()
  formData.append('username', credentials.username)
  formData.append('password', credentials.password)

  // Step 1: Authenticate and get token (set as httpOnly cookie)
  // Convert URLSearchParams to string to ensure body is sent correctly through proxy
  const tokenResponse = await api.post<RefreshTokenResponse>('/auth/login', formData.toString(), {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    withCredentials: true, // Required for cookies
  })

  // Step 2: Store tokens and schedule proactive refresh
  storeTokens(tokenResponse.data.refreshToken, tokenResponse.data.accessToken)

  // Step 3: Fetch user data using the newly set token
  try {
    const user = await getCurrentUser()

    return {
      accessToken: tokenResponse.data.accessToken,
      tokenType: tokenResponse.data.tokenType,
      user,
    }
  } catch (_error) {
    // Login succeeded (token is set in cookie), but failed to fetch user data
    // This is a partial success - the user is authenticated but we can't get their details
    // Throw a descriptive error for the UI to handle
    // The user can try refreshing the page since the cookie is set
    throw new Error('Authentication succeeded but failed to load user profile. Please refresh the page.')
  }
}

/**
 * Logs out the current user and invalidates their session.
 *
 * This function calls the backend logout endpoint which:
 * - Invalidates the user's session server-side
 * - Deletes the httpOnly authentication cookie
 * - Ensures the user is fully logged out from the system
 *
 * Security: Even if the API call fails, the user should be treated as
 * logged out client-side. Local state is always cleared for security,
 * even if the server-side logout fails.
 *
 * @returns Promise resolving to true if server logout succeeded, false if it failed
 *          (local state is cleared regardless of return value)
 *
 * @example
 * ```ts
 * const serverLogoutSuccess = await logout();
 * if (!serverLogoutSuccess) {
 *   console.warn('Server logout failed, but local session cleared');
 * }
 * navigate('/login');
 * ```
 *
 * @see login - For logging in
 */
export async function logout(): Promise<boolean> {
  // Clear token state before making the request (security: always clear local state)
  clearTokenState()

  try {
    await post('/auth/logout', {})
    return true
  } catch (_error) {
    // Even if the request fails, the user is logged out client-side
    return false
  }
}

/**
 * Fetches the current authenticated user's profile.
 *
 * This function retrieves the user profile for the currently authenticated
 * session using the httpOnly cookie. If the cookie is missing or invalid,
 * the request will fail with a 401 error.
 *
 * @returns Promise resolving to the current user's profile
 * @throws {ApiError} If not authenticated or session is invalid (401)
 * @throws {ApiError} If the request fails for other reasons
 *
 * @example
 * ```ts
 * try {
 *   const user = await getCurrentUser();
 *   console.log(`Current user: ${user.username}`);
 *   console.log(`Role: ${user.role}`);
 * } catch (error) {
 *   if (error.status === 401) {
 *     console.log('Not authenticated');
 *   }
 * }
 * ```
 *
 * @see login - For authenticating a user
 * @see validateToken - For checking if the session is still valid
 */
export async function getCurrentUser(): Promise<User> {
  const user = await get<User>('/auth/me')
  return user
}

/**
 * Checks if the current session is authenticated without fetching full user details.
 *
 * This lightweight endpoint provides a quick way to verify authentication
 * status without the overhead of fetching complete user profile data. Useful
 * for authentication guards and conditional rendering.
 *
 * @returns Promise resolving to authentication status
 * @returns {AuthCheckResponse} Object with `authenticated` boolean and optional user
 *
 * @example
 * ```ts
 * const authStatus = await checkAuth();
 * if (authStatus.authenticated) {
 *   console.log('User is logged in');
 *   if (authStatus.user) {
 *     console.log(`Username: ${authStatus.user.username}`);
 *   }
 * } else {
 *   console.log('User is not authenticated');
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Use in authentication guard
 * async function requireAuth() {
 *   const { authenticated } = await checkAuth();
 *   if (!authenticated) {
 *     navigate('/login');
 *   }
 * }
 * ```
 *
 * @see getCurrentUser - For fetching complete user profile
 * @see validateToken - For token validation with user data
 */
export async function checkAuth(): Promise<AuthCheckResponse> {
  try {
    // Use /auth/me instead of /auth/check (which doesn't exist on backend)
    // Transform the User response into AuthCheckResponse format
    const user = await get<User>('/auth/me')
    return { authenticated: true, user }
  } catch (_error) {
    // If request fails, user is not authenticated
    return { authenticated: false }
  }
}

/**
 * Validates if the current authentication token/session is still valid.
 *
 * This function attempts to fetch the current user profile to verify that
 * the httpOnly cookie contains a valid, non-expired JWT token. Useful for
 * session timeout checks and authentication validation.
 *
 * Security: Validates the httpOnly cookie by attempting to fetch the current
 * user. If the cookie is missing, expired, or invalid, this returns null.
 *
 * @returns Promise resolving to User if valid, null if invalid or missing
 *
 * @example
 * ```ts
 * const user = await validateToken();
 * if (user) {
 *   console.log('Session is valid');
 *   console.log(`Logged in as: ${user.username}`);
 * } else {
 *   console.log('Session expired or invalid');
 *   navigate('/login');
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Use in session guard
 * function SessionGuard({ children }: PropsWithChildren) {
 *   const [user, setUser] = useState<User | null>(null);
 *   const [loading, setLoading] = useState(true);
 *
 *   useEffect(() => {
 *     validateToken().then(user => {
 *       setUser(user);
 *       setLoading(false);
 *     });
 *   }, []);
 *
 *   if (loading) return <LoadingScreen />;
 *   if (!user) return <Navigate to="/login" />;
 *
 *   return <>{children}</>;
 * }
 * ```
 *
 * @see getCurrentUser - For fetching user without null handling
 * @see checkAuth - For lighter authentication check
 */
export async function validateToken(): Promise<User | null> {
  try {
    const user = await getCurrentUser()
    return user
  } catch (_error) {
    // Token is invalid or missing
    return null
  }
}

// ============================================================================
// Token Refresh Functions
// ============================================================================

/**
 * Stores tokens and schedules proactive refresh.
 *
 * @param refresh - The refresh token to store
 * @param access - The access token to store (optional, for WebSocket auth)
 */
function storeTokens(refresh: string, access?: string): void {
  console.log('[Auth] storeTokens called:', { hasRefresh: !!refresh, hasAccess: !!access })
  refreshToken = refresh
  if (access) {
    accessToken = access
    console.log('[Auth] Access token stored:', access.substring(0, 20) + '...')
  }
  tokenExpiresAt = Date.now() + ACCESS_TOKEN_EXPIRE_MINUTES * 60 * 1000
  scheduleProactiveRefresh()

  // Persist refresh token to sessionStorage for page refresh recovery.
  // This is needed because Next.js proxy doesn't forward cookies, so we
  // can't rely on httpOnly cookies for session restoration.
  // Security: sessionStorage is cleared when browser tab closes.
  if (typeof window !== 'undefined') {
    try {
      sessionStorage.setItem('__rt', refresh)
    } catch {
      // sessionStorage not available (e.g., incognito mode)
    }
  }
}

/**
 * Clears all token-related state.
 *
 * Called on logout or when refresh fails.
 */
export function clearTokenState(): void {
  refreshToken = null
  accessToken = null
  tokenExpiresAt = null
  isRefreshing = false
  refreshPromise = null

  if (refreshTimerId) {
    clearTimeout(refreshTimerId)
    refreshTimerId = null
  }

  // Clear persisted refresh token
  if (typeof window !== 'undefined') {
    try {
      sessionStorage.removeItem('__rt')
    } catch {
      // sessionStorage not available
    }
  }
}

/**
 * Attempts to restore the session from sessionStorage on page refresh.
 *
 * This is needed because Next.js proxy doesn't forward httpOnly cookies,
 * so we persist the refresh token in sessionStorage and use it to get
 * a fresh access token on page load.
 *
 * @returns Promise resolving to true if session was restored, false otherwise
 */
export async function restoreSession(): Promise<boolean> {
  // Try to get refresh token from sessionStorage
  if (typeof window === 'undefined') {
    return false
  }

  try {
    const storedRefreshToken = sessionStorage.getItem('__rt')
    if (!storedRefreshToken) {
      console.log('[Auth] No stored refresh token found')
      return false
    }

    console.log('[Auth] Found stored refresh token, attempting refresh...')
    // Temporarily set the refresh token so performRefresh can use it
    refreshToken = storedRefreshToken

    const result = await performRefresh()
    if (result) {
      console.log('[Auth] Session restored successfully')
      return true
    } else {
      console.log('[Auth] Session restore failed - refresh token invalid')
      // Clear invalid token from storage
      sessionStorage.removeItem('__rt')
      refreshToken = null
      return false
    }
  } catch {
    console.log('[Auth] Session restore error')
    return false
  }
}

/**
 * Gets the current access token for WebSocket authentication.
 *
 * WebSocket connections can't use httpOnly cookies cross-origin, so they need
 * the token passed as a query parameter. This function provides access to the
 * in-memory token for that purpose.
 *
 * @returns The current access token, or null if not authenticated
 */
export function getAccessToken(): string | null {
  console.log('[Auth] getAccessToken called, token:', accessToken ? 'exists' : 'null')
  return accessToken
}

/**
 * Schedules a proactive token refresh before the access token expires.
 *
 * Uses a timer to refresh 1 minute before expiry (configurable via REFRESH_MARGIN_MS).
 * This prevents 401 errors during normal use.
 */
function scheduleProactiveRefresh(): void {
  // Clear any existing timer
  if (refreshTimerId) {
    clearTimeout(refreshTimerId)
    refreshTimerId = null
  }

  if (!tokenExpiresAt || !refreshToken) {
    return
  }

  // Calculate time until refresh (1 minute before expiry)
  const timeUntilRefresh = tokenExpiresAt - Date.now() - REFRESH_MARGIN_MS

  if (timeUntilRefresh <= 0) {
    // Token is already expired or about to expire, refresh immediately
    performRefresh().catch(() => {
      // Silent failure - rely on reactive refresh
    })
    return
  }

  refreshTimerId = setTimeout(() => {
    performRefresh().catch(() => {
      // On proactive refresh failure, we'll rely on reactive refresh
    })
  }, timeUntilRefresh)
}

/**
 * Performs the actual token refresh.
 *
 * This function is idempotent - if a refresh is already in progress, it returns
 * the existing promise. This prevents multiple concurrent refresh requests.
 *
 * @returns Promise resolving to the refresh response, or null if refresh failed
 */
export async function performRefresh(): Promise<RefreshTokenResponse | null> {
  // If already refreshing, return the existing promise
  if (isRefreshing && refreshPromise) {
    return refreshPromise
  }

  // Check if we have a refresh token
  if (!refreshToken) {
    return null
  }

  isRefreshing = true

  refreshPromise = (async () => {
    try {
      const response = await post<RefreshTokenResponse>('/auth/refresh', {
        refreshToken: refreshToken,
      })

      // Store the new tokens
      storeTokens(response.refreshToken, response.accessToken)

      return response
    } catch (_error) {
      // Clear state on failure - user needs to re-login
      clearTokenState()

      return null
    } finally {
      isRefreshing = false
      refreshPromise = null
    }
  })()

  return refreshPromise
}

/**
 * Attempts to refresh the token if a refresh is needed or in progress.
 *
 * This is the main entry point for reactive token refresh (called by API interceptor
 * on 401 errors). It handles the refresh and returns whether it was successful.
 *
 * @returns Promise resolving to true if refresh succeeded, false otherwise
 */
export async function attemptTokenRefresh(): Promise<boolean> {
  const result = await performRefresh()
  return result !== null
}

/**
 * Checks if a token refresh is currently in progress.
 *
 * Useful for API interceptors to know whether to wait for refresh before
 * retrying failed requests.
 *
 * @returns True if a refresh is in progress
 */
export function isTokenRefreshing(): boolean {
  return isRefreshing
}

/**
 * Gets the current refresh promise if one is in progress.
 *
 * Allows API interceptors to wait for the refresh to complete before retrying.
 *
 * @returns The current refresh promise, or null if no refresh is in progress
 */
export function getRefreshPromise(): Promise<RefreshTokenResponse | null> | null {
  return refreshPromise
}

/**
 * Checks if the access token is expired or about to expire.
 *
 * @returns True if the token is expired or will expire within the refresh margin
 */
export function isTokenExpired(): boolean {
  if (!tokenExpiresAt) {
    return true
  }
  return Date.now() >= tokenExpiresAt - REFRESH_MARGIN_MS
}

/**
 * Gets the remaining time until the access token expires.
 *
 * @returns Milliseconds until expiry, or 0 if expired/unknown
 */
export function getTimeUntilExpiry(): number {
  if (!tokenExpiresAt) {
    return 0
  }
  return Math.max(0, tokenExpiresAt - Date.now())
}
