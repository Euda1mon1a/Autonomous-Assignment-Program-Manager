/**
 * Authentication Library for Residency Scheduler
 *
 * Provides authentication API functions with secure httpOnly cookie-based
 * JWT token management. This prevents XSS attacks by keeping tokens out of
 * JavaScript-accessible storage (no localStorage or sessionStorage).
 *
 * Security Features:
 * - httpOnly cookies for JWT tokens (XSS-resistant)
 * - Automatic token refresh via cookies
 * - Secure logout with server-side session invalidation
 *
 * @module lib/auth
 */
import { api, post, get, ApiError } from './api'

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
  is_active: boolean
  /** Timestamp when user was created */
  created_at: string
  /** Timestamp of last profile update (optional) */
  updated_at?: string
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
  access_token: string
  /** Token type (typically "bearer") */
  token_type: string
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
  console.log('[auth.ts] login() called with username:', credentials.username)
  console.log('[auth.ts] API base URL:', process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api (default)')

  // Create form data for OAuth2 password flow
  const formData = new URLSearchParams()
  formData.append('username', credentials.username)
  formData.append('password', credentials.password)

  console.log('[auth.ts] Sending POST to /auth/login...')

  // Step 1: Authenticate and get token (set as httpOnly cookie)
  let tokenResponse;
  try {
    tokenResponse = await api.post<{ access_token: string; token_type: string }>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      withCredentials: true, // Required for cookies
    })
    console.log('[auth.ts] Login response received:', { status: 'success', hasToken: !!tokenResponse?.data?.access_token })
  } catch (loginError) {
    console.error('[auth.ts] Login request FAILED:', loginError)
    throw loginError
  }

  // Step 2: Fetch user data using the newly set token
  try {
    const user = await getCurrentUser()

    return {
      access_token: tokenResponse.data.access_token,
      token_type: tokenResponse.data.token_type,
      user,
    }
  } catch (error) {
    // Login succeeded (token is set in cookie), but failed to fetch user data
    // This is a partial success - the user is authenticated but we can't get their details
    console.error('Failed to fetch user data after successful login:', error)

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
 * logged out client-side. The httpOnly cookie is cleared server-side.
 *
 * @returns Promise resolving when logout completes
 * @throws Does not throw - errors are logged and swallowed
 *
 * @example
 * ```ts
 * await logout();
 * console.log('User logged out');
 * navigate('/login');
 * ```
 *
 * @see login - For logging in
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
  console.log('[auth.ts] getCurrentUser() - fetching /auth/me...')
  try {
    const user = await get<User>('/auth/me')
    console.log('[auth.ts] getCurrentUser() - success:', { id: user?.id, username: user?.username })
    return user
  } catch (err) {
    console.error('[auth.ts] getCurrentUser() - FAILED:', err)
    throw err
  }
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
  } catch (error) {
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
  } catch (error) {
    // Token is invalid or missing
    return null
  }
}
