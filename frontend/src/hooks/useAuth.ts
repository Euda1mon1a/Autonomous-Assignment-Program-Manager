/**
 * Authentication Hooks
 *
 * Hooks for user authentication, authorization, and session management
 * with React Query caching and httpOnly cookie-based authentication.
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query'
import { useCallback, useRef } from 'react'
import { ApiError } from '@/lib/api'
import {
  login as loginApi,
  logout as logoutApi,
  getCurrentUser,
  checkAuth,
  validateToken,
  performRefresh,
  isTokenExpired,
  getTimeUntilExpiry,
  type User,
  type LoginCredentials,
  type LoginResponse,
  type AuthCheckResponse,
} from '@/lib/auth'

// ============================================================================
// Types
// ============================================================================

/**
 * User roles in the residency scheduler system
 */
export type UserRole = 'admin' | 'coordinator' | 'faculty' | 'resident'

/**
 * Permissions available in the system
 */
export type Permission =
  | 'schedule:read'
  | 'schedule:write'
  | 'schedule:generate'
  | 'schedule:validate'
  | 'assignments:read'
  | 'assignments:write'
  | 'assignments:delete'
  | 'people:read'
  | 'people:write'
  | 'people:delete'
  | 'absences:read'
  | 'absences:write'
  | 'absences:approve'
  | 'absences:delete'
  | 'templates:read'
  | 'templates:write'
  | 'templates:delete'
  | 'resilience:read'
  | 'resilience:trigger'
  | 'admin:full'

/**
 * Role-based permission mapping
 */
const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  admin: [
    'schedule:read',
    'schedule:write',
    'schedule:generate',
    'schedule:validate',
    'assignments:read',
    'assignments:write',
    'assignments:delete',
    'people:read',
    'people:write',
    'people:delete',
    'absences:read',
    'absences:write',
    'absences:approve',
    'absences:delete',
    'templates:read',
    'templates:write',
    'templates:delete',
    'resilience:read',
    'resilience:trigger',
    'admin:full',
  ],
  coordinator: [
    'schedule:read',
    'schedule:write',
    'schedule:generate',
    'schedule:validate',
    'assignments:read',
    'assignments:write',
    'assignments:delete',
    'people:read',
    'people:write',
    'absences:read',
    'absences:write',
    'absences:approve',
    'templates:read',
    'templates:write',
    'resilience:read',
  ],
  faculty: [
    'schedule:read',
    'assignments:read',
    'people:read',
    'absences:read',
    'absences:write',
    'templates:read',
  ],
  resident: [
    'schedule:read',
    'assignments:read',
    'people:read',
    'absences:read',
    'absences:write',
  ],
}

// ============================================================================
// Query Keys
// ============================================================================

export const authQueryKeys = {
  user: () => ['auth', 'user'] as const,
  check: () => ['auth', 'check'] as const,
  validate: () => ['auth', 'validate'] as const,
  tokenStatus: () => ['auth', 'tokenStatus'] as const,
}

// ============================================================================
// Authentication Hooks
// ============================================================================

/**
 * Gets the current authenticated user from the session.
 *
 * This hook retrieves the user profile for the currently authenticated session
 * using httpOnly cookies. The hook automatically handles token validation and
 * provides loading, error, and success states for the UI.
 *
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: Current user object with profile information
 *   - `isLoading`: Whether the initial fetch is in progress
 *   - `isFetching`: Whether any fetch is in progress (including background)
 *   - `error`: Any error that occurred during fetch
 *   - `refetch`: Function to manually refetch the user
 *
 * @example
 * ```tsx
 * function UserProfile() {
 *   const { data: user, isLoading, error } = useUser();
 *
 *   if (isLoading) return <Spinner />;
 *   if (error) return <ErrorAlert error={error} />;
 *   if (!user) return <NotAuthenticated />;
 *
 *   return (
 *     <div>
 *       <h1>Welcome, {user.username}</h1>
 *       <p>Role: {user.role}</p>
 *       <p>Email: {user.email}</p>
 *     </div>
 *   );
 * }
 * ```
 *
 * @see useAuth - For complete authentication state including permissions
 * @see useRole - For checking the user's role
 */
export function useUser(
  options?: Omit<UseQueryOptions<User, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<User, ApiError>({
    queryKey: authQueryKeys.user(),
    queryFn: getCurrentUser,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    retry: (failureCount, error) => {
      // Don't retry on 401 (unauthorized) - user is not logged in
      if (error?.status === 401) return false
      return failureCount < 2
    },
    ...options,
  })
}

/**
 * Checks the current authentication status without fetching full user details.
 *
 * This hook provides a lightweight way to check if a user is authenticated
 * without fetching the complete user profile. Useful for conditional rendering
 * of authenticated vs. unauthenticated UI elements.
 *
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: Authentication check response with status and optional user
 *   - `isLoading`: Whether the check is in progress
 *   - `error`: Any error that occurred during check
 *
 * @example
 * ```tsx
 * function LoginPrompt() {
 *   const { data: authStatus } = useAuthCheck();
 *
 *   if (authStatus?.authenticated) {
 *     return <Navigate to="/dashboard" />;
 *   }
 *
 *   return <LoginForm />;
 * }
 * ```
 *
 * @see useAuth - For full authentication state with user details
 * @see useUser - For fetching complete user profile
 */
export function useAuthCheck(
  options?: Omit<UseQueryOptions<AuthCheckResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AuthCheckResponse, ApiError>({
    queryKey: authQueryKeys.check(),
    queryFn: checkAuth,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    retry: false,
    ...options,
  })
}

/**
 * Gets complete authentication state including user profile and permissions.
 *
 * This hook combines user data with permission checking functionality to provide
 * a complete authentication context. It's the primary hook for components that
 * need to check both authentication status and user permissions.
 *
 * @param options - Optional React Query configuration options
 * @returns Authentication state object containing:
 *   - `user`: Current user object (or undefined if not authenticated)
 *   - `isAuthenticated`: Boolean indicating authentication status
 *   - `isLoading`: Whether authentication check is in progress
 *   - `error`: Any error that occurred
 *   - `hasPermission`: Function to check if user has a specific permission
 *   - `hasRole`: Function to check if user has a specific role
 *   - `refetch`: Function to manually refresh authentication state
 *
 * @example
 * ```tsx
 * function ScheduleGenerator() {
 *   const { user, isAuthenticated, hasPermission, isLoading } = useAuth();
 *
 *   if (isLoading) return <LoadingScreen />;
 *   if (!isAuthenticated) return <Navigate to="/login" />;
 *
 *   const canGenerate = hasPermission('schedule:generate');
 *
 *   return (
 *     <div>
 *       <h1>Schedule Generator</h1>
 *       <p>Logged in as: {user?.username}</p>
 *       {canGenerate ? (
 *         <GenerateButton />
 *       ) : (
 *         <PermissionDenied requiredPermission="schedule:generate" />
 *       )}
 *     </div>
 *   );
 * }
 * ```
 *
 * @see useUser - For just fetching user data
 * @see usePermissions - For permission checking only
 * @see useRole - For role checking only
 */
export function useAuth(
  options?: Omit<UseQueryOptions<User, ApiError>, 'queryKey' | 'queryFn'>
) {
  const queryClient = useQueryClient()
  const userQuery = useUser(options)

  // Track if we're refreshing
  const isRefreshingRef = useRef(false)

  /**
   * Manually triggers a token refresh.
   *
   * This is useful when you want to proactively refresh the token
   * before making a critical operation, ensuring the token is fresh.
   *
   * @returns Promise resolving to true if refresh succeeded
   */
  const refreshToken = useCallback(async (): Promise<boolean> => {
    if (isRefreshingRef.current) {
      return false
    }

    isRefreshingRef.current = true
    try {
      const result = await performRefresh()
      if (result) {
        // Refresh user data after successful token refresh
        await queryClient.invalidateQueries({ queryKey: authQueryKeys.user() })
        return true
      }
      return false
    } finally {
      isRefreshingRef.current = false
    }
  }, [queryClient])

  /**
   * Gets the remaining time until the access token expires.
   *
   * @returns Milliseconds until expiry, or 0 if expired/unknown
   */
  const getTokenExpiry = useCallback((): number => {
    return getTimeUntilExpiry()
  }, [])

  /**
   * Checks if the access token is expired or about to expire.
   *
   * @returns True if the token needs refresh
   */
  const needsRefresh = useCallback((): boolean => {
    return isTokenExpired()
  }, [])

  const hasPermission = (permission: Permission): boolean => {
    if (!userQuery.data?.role) return false
    const rolePermissions = ROLE_PERMISSIONS[userQuery.data.role as UserRole]
    return rolePermissions.includes(permission)
  }

  const hasRole = (role: UserRole | UserRole[]): boolean => {
    if (!userQuery.data?.role) return false
    const roles = Array.isArray(role) ? role : [role]
    return roles.includes(userQuery.data.role as UserRole)
  }

  return {
    user: userQuery.data,
    isAuthenticated: !!userQuery.data && !userQuery.error,
    isLoading: userQuery.isLoading,
    isFetching: userQuery.isFetching,
    error: userQuery.error,
    hasPermission,
    hasRole,
    refetch: userQuery.refetch,
    // New token refresh methods
    refreshToken,
    getTokenExpiry,
    needsRefresh,
  }
}

/**
 * Authenticates a user with username and password credentials.
 *
 * This mutation hook handles the login process, setting the httpOnly authentication
 * cookie and fetching the user profile. On success, it automatically updates the
 * authentication cache so the app immediately reflects the logged-in state.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to trigger login
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether login is in progress (shows loading spinner)
 *   - `isSuccess`: Whether login completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred during login
 *   - `data`: Login response with access token and user data
 *
 * @example
 * ```tsx
 * function LoginForm() {
 *   const { mutate: login, isPending, error } = useLogin();
 *   const [username, setUsername] = useState('');
 *   const [password, setPassword] = useState('');
 *
 *   const handleSubmit = (e: FormEvent) => {
 *     e.preventDefault();
 *     login(
 *       { username, password },
 *       {
 *         onSuccess: (response) => {
 *           toast.success(`Welcome back, ${response.user.username}!`);
 *           navigate('/dashboard');
 *         },
 *         onError: (error) => {
 *           toast.error(`Login failed: ${error.message}`);
 *         },
 *       }
 *     );
 *   };
 *
 *   return (
 *     <form onSubmit={handleSubmit}>
 *       <input
 *         type="text"
 *         value={username}
 *         onChange={(e) => setUsername(e.target.value)}
 *         placeholder="Username"
 *       />
 *       <input
 *         type="password"
 *         value={password}
 *         onChange={(e) => setPassword(e.target.value)}
 *         placeholder="Password"
 *       />
 *       <button type="submit" disabled={isPending}>
 *         {isPending ? 'Logging in...' : 'Login'}
 *       </button>
 *       {error && <ErrorMessage>{error.message}</ErrorMessage>}
 *     </form>
 *   );
 * }
 * ```
 *
 * @see useLogout - For logging out
 * @see useAuth - Authentication state is auto-updated after login
 */
export function useLogin() {
  const queryClient = useQueryClient()

  return useMutation<LoginResponse, ApiError, LoginCredentials>({
    mutationFn: loginApi,
    onSuccess: (data) => {
      // Update the user query cache with the logged-in user
      queryClient.setQueryData(authQueryKeys.user(), data.user)
      // Mark auth check as authenticated
      queryClient.setQueryData(authQueryKeys.check(), {
        authenticated: true,
        user: data.user,
      })
      // Invalidate other queries to refetch with new authentication
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
      queryClient.invalidateQueries({ queryKey: ['people'] })
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
    },
  })
}

/**
 * Logs out the current user and clears the authentication session.
 *
 * This mutation hook handles the logout process, clearing the httpOnly cookie
 * server-side and removing all cached authentication data client-side. The user
 * is effectively logged out from both the backend session and frontend state.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to trigger logout
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether logout is in progress
 *   - `isSuccess`: Whether logout completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred during logout
 *
 * @example
 * ```tsx
 * function LogoutButton() {
 *   const { mutate: logout, isPending } = useLogout();
 *
 *   const handleLogout = () => {
 *     logout(undefined, {
 *       onSuccess: () => {
 *         toast.info('You have been logged out');
 *         navigate('/login');
 *       },
 *       onError: () => {
 *         // Even if server logout fails, client is logged out
 *         toast.warning('Logged out locally (server error)');
 *         navigate('/login');
 *       },
 *     });
 *   };
 *
 *   return (
 *     <button onClick={handleLogout} disabled={isPending}>
 *       {isPending ? 'Logging out...' : 'Logout'}
 *     </button>
 *   );
 * }
 * ```
 *
 * @see useLogin - For logging in
 * @see useAuth - Authentication state is auto-cleared after logout
 */
export function useLogout() {
  const queryClient = useQueryClient()

  return useMutation<boolean, ApiError, void>({
    mutationFn: logoutApi,
    onSuccess: (serverLogoutSuccess) => {
      // Clear all authentication-related cache
      queryClient.setQueryData(authQueryKeys.user(), null)
      queryClient.setQueryData(authQueryKeys.check(), { authenticated: false })
      // Clear all other cached queries (user no longer has access)
      queryClient.clear()

      // Log if server logout failed (local state was still cleared)
      if (!serverLogoutSuccess && process.env.NODE_ENV === 'development') {
        console.warn('Server logout failed, but local session was cleared')
      }
    },
    onError: () => {
      // Even if logout request fails, clear client-side auth state
      queryClient.setQueryData(authQueryKeys.user(), null)
      queryClient.setQueryData(authQueryKeys.check(), { authenticated: false })
      queryClient.clear()
    },
  })
}

/**
 * Validates the current authentication token/session.
 *
 * This hook checks if the current httpOnly cookie token is still valid by
 * attempting to fetch the user profile. Returns the user if valid, null otherwise.
 * Useful for session timeout checks and authentication guards.
 *
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: User object if token is valid, null otherwise
 *   - `isLoading`: Whether validation is in progress
 *   - `error`: Any error that occurred
 *
 * @example
 * ```tsx
 * function SessionGuard({ children }: PropsWithChildren) {
 *   const { data: user, isLoading } = useValidateSession();
 *
 *   if (isLoading) return <LoadingScreen />;
 *   if (!user) return <Navigate to="/login" />;
 *
 *   return <>{children}</>;
 * }
 * ```
 *
 * @see useAuth - For full authentication state
 * @see useUser - For fetching current user
 */
export function useValidateSession(
  options?: Omit<UseQueryOptions<User | null, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<User | null, ApiError>({
    queryKey: authQueryKeys.validate(),
    queryFn: validateToken,
    staleTime: 1 * 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
    ...options,
  })
}

// ============================================================================
// Permission & Role Hooks
// ============================================================================

/**
 * Gets the current user's permissions based on their role.
 *
 * This hook provides a convenient way to check user permissions without
 * needing to access the full authentication state. Returns a function
 * to check if the user has a specific permission.
 *
 * @returns Object containing:
 *   - `hasPermission`: Function to check if user has a specific permission
 *   - `permissions`: Array of all permissions the user has
 *   - `isLoading`: Whether permission data is still loading
 *
 * @example
 * ```tsx
 * function ScheduleActions() {
 *   const { hasPermission, permissions, isLoading } = usePermissions();
 *
 *   if (isLoading) return <Skeleton />;
 *
 *   return (
 *     <div>
 *       {hasPermission('schedule:generate') && (
 *         <GenerateScheduleButton />
 *       )}
 *       {hasPermission('schedule:write') && (
 *         <EditScheduleButton />
 *       )}
 *       {hasPermission('schedule:read') && (
 *         <ViewScheduleButton />
 *       )}
 *     </div>
 *   );
 * }
 * ```
 *
 * @see useAuth - For complete authentication state with permissions
 * @see useRole - For checking user's role
 */
export function usePermissions() {
  const { data: user, isLoading } = useUser()

  const permissions = user?.role
    ? ROLE_PERMISSIONS[user.role as UserRole] || []
    : []

  const hasPermission = (permission: Permission): boolean => {
    return permissions.includes(permission)
  }

  return {
    hasPermission,
    permissions,
    isLoading,
  }
}

/**
 * Gets the current user's role.
 *
 * This hook provides a simple way to access and check the user's role
 * without needing the full authentication state. Returns the role string
 * and a function to check if the user has a specific role.
 *
 * @returns Object containing:
 *   - `role`: The user's role (or undefined if not authenticated)
 *   - `hasRole`: Function to check if user has a specific role or roles
 *   - `isLoading`: Whether role data is still loading
 *   - `isAdmin`: Convenience boolean for checking admin role
 *   - `isCoordinator`: Convenience boolean for checking coordinator role
 *   - `isFaculty`: Convenience boolean for checking faculty role
 *   - `isResident`: Convenience boolean for checking resident role
 *
 * @example
 * ```tsx
 * function AdminPanel() {
 *   const { role, isAdmin, hasRole, isLoading } = useRole();
 *
 *   if (isLoading) return <Spinner />;
 *   if (!isAdmin) return <Forbidden />;
 *
 *   return (
 *     <div>
 *       <h1>Admin Panel</h1>
 *       <p>Current role: {role}</p>
 *       {hasRole(['admin', 'coordinator']) && (
 *         <UserManagementSection />
 *       )}
 *     </div>
 *   );
 * }
 * ```
 *
 * @see useAuth - For complete authentication state
 * @see usePermissions - For checking specific permissions
 */
export function useRole() {
  const { data: user, isLoading } = useUser()

  const role = user?.role as UserRole | undefined

  const hasRole = (checkRole: UserRole | UserRole[]): boolean => {
    if (!role) return false
    const roles = Array.isArray(checkRole) ? checkRole : [checkRole]
    return roles.includes(role)
  }

  return {
    role,
    hasRole,
    isLoading,
    isAdmin: role === 'admin',
    isCoordinator: role === 'coordinator',
    isFaculty: role === 'faculty',
    isResident: role === 'resident',
  }
}
