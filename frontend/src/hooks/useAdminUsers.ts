/**
 * Admin User Management Hooks
 *
 * Hooks for managing system users with React Query caching,
 * optimistic updates, and proper error handling.
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query'
import { get, post, del, patch, ApiError } from '@/lib/api'
import type {
  User,
  UserCreate,
  UserUpdate,
  UsersResponse,
  UserRole,
  UserStatus,
  BulkAction,
  BulkActionRequest,
} from '@/types/admin-users'

// ============================================================================
// Types
// ============================================================================

/**
 * Filters for querying admin users
 */
export interface AdminUserFilters {
  search?: string
  role?: UserRole | 'all'
  status?: UserStatus | 'all'
  page?: number
  pageSize?: number
}

/**
 * Response for lock/unlock action
 */
export interface LockUserResponse {
  success: boolean
  user: User
  message: string
}

/**
 * Response for resend invite action
 */
export interface ResendInviteResponse {
  success: boolean
  message: string
}

/**
 * Response for bulk actions
 */
export interface BulkActionResponse {
  success: boolean
  affected: number
  failures: string[]
  message: string
}

// ============================================================================
// Query Keys
// ============================================================================

export const adminUsersQueryKeys = {
  all: ['admin', 'users'] as const,
  list: (filters?: AdminUserFilters) => ['admin', 'users', 'list', filters] as const,
  detail: (id: string) => ['admin', 'users', 'detail', id] as const,
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Fetches admin users list from API
 */
async function fetchUsers(filters?: AdminUserFilters): Promise<UsersResponse> {
  const params = new URLSearchParams()

  if (filters?.search) {
    params.set('search', filters.search)
  }
  if (filters?.role && filters.role !== 'all') {
    params.set('role', filters.role)
  }
  if (filters?.status && filters.status !== 'all') {
    params.set('status', filters.status)
  }
  if (filters?.page !== undefined) {
    params.set('page', String(filters.page))
  }
  if (filters?.pageSize !== undefined) {
    params.set('page_size', String(filters.pageSize))
  }

  const queryString = params.toString()
  return get<UsersResponse>(`/admin/users${queryString ? `?${queryString}` : ''}`)
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetches a paginated list of admin users with optional filtering.
 *
 * This hook retrieves users from the admin API with support for
 * search, role filtering, status filtering, and pagination.
 *
 * @param filters - Optional filters for search, role, status, and pagination
 * @param options - Optional React Query configuration options
 * @returns Query result containing:
 *   - `data`: UsersResponse with users array, total count, page, and pageSize
 *   - `isLoading`: Whether the fetch is in progress
 *   - `error`: Any error that occurred
 *   - `refetch`: Function to manually refetch users
 *
 * @example
 * ```tsx
 * function AdminUsersTable() {
 *   const { data, isLoading, error } = useUsers({
 *     search: 'smith',
 *     role: 'faculty',
 *     status: 'active'
 *   });
 *
 *   if (isLoading) return <TableSkeleton />;
 *   if (error) return <ErrorMessage error={error} />;
 *
 *   return <UsersTable users={data.users} total={data.total} />;
 * }
 * ```
 */
export function useUsers(
  filters?: AdminUserFilters,
  options?: Omit<UseQueryOptions<UsersResponse, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<UsersResponse, ApiError>({
    queryKey: adminUsersQueryKeys.list(filters),
    queryFn: () => fetchUsers(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes - shorter for admin data
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  })
}

/**
 * Fetches a single user by ID.
 *
 * @param id - The user ID to fetch
 * @param options - Optional React Query configuration options
 * @returns Query result containing the user details
 */
export function useUser(
  id: string,
  options?: Omit<UseQueryOptions<User, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery<User, ApiError>({
    queryKey: adminUsersQueryKeys.detail(id),
    queryFn: () => get<User>(`/admin/users/${id}`),
    staleTime: 2 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    enabled: !!id,
    ...options,
  })
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Creates a new user in the system.
 *
 * This mutation hook adds a new user with the specified role and
 * optionally sends an invitation email. Automatically refreshes
 * the users list on success.
 *
 * @returns Mutation object containing:
 *   - `mutate`: Function to create a user
 *   - `mutateAsync`: Async version returning a Promise
 *   - `isPending`: Whether creation is in progress
 *   - `isSuccess`: Whether creation completed successfully
 *   - `isError`: Whether an error occurred
 *   - `error`: Any error that occurred (e.g., duplicate email)
 *   - `data`: The created user with generated ID
 *
 * @example
 * ```tsx
 * function CreateUserForm() {
 *   const { mutate, isPending, error } = useCreateUser();
 *
 *   const handleSubmit = (data: UserCreate) => {
 *     mutate(data, {
 *       onSuccess: (newUser) => {
 *         toast.success(`User ${newUser.email} created`);
 *         onClose();
 *       },
 *       onError: (error) => {
 *         toast.error(error.message);
 *       },
 *     });
 *   };
 *
 *   return <UserForm onSubmit={handleSubmit} loading={isPending} />;
 * }
 * ```
 */
export function useCreateUser() {
  const queryClient = useQueryClient()

  return useMutation<User, ApiError, UserCreate>({
    mutationFn: (data) => post<User>('/admin/users', data),
    onSuccess: () => {
      // Invalidate and refetch users list
      queryClient.invalidateQueries({ queryKey: adminUsersQueryKeys.all })
    },
  })
}

/**
 * Updates an existing user.
 *
 * @returns Mutation object for updating user details
 *
 * @example
 * ```tsx
 * function EditUserForm({ userId }: Props) {
 *   const { mutate, isPending } = useUpdateUser();
 *
 *   const handleUpdate = (updates: UserUpdate) => {
 *     mutate({ id: userId, data: updates }, {
 *       onSuccess: () => toast.success('User updated'),
 *     });
 *   };
 *
 *   return <UserForm onSubmit={handleUpdate} loading={isPending} />;
 * }
 * ```
 */
export function useUpdateUser() {
  const queryClient = useQueryClient()

  return useMutation<User, ApiError, { id: string; data: UserUpdate }>({
    mutationFn: ({ id, data }) => patch<User>(`/admin/users/${id}`, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: adminUsersQueryKeys.all })
      queryClient.invalidateQueries({ queryKey: adminUsersQueryKeys.detail(id) })
    },
  })
}

/**
 * Deletes a user from the system.
 *
 * This mutation permanently removes a user. The operation may fail
 * if the user has associated data that cannot be orphaned.
 *
 * @returns Mutation object for deleting users
 *
 * @example
 * ```tsx
 * function DeleteUserButton({ user }: Props) {
 *   const { mutate, isPending } = useDeleteUser();
 *
 *   const handleDelete = () => {
 *     if (confirm(`Delete ${user.email}? This cannot be undone.`)) {
 *       mutate(user.id, {
 *         onSuccess: () => toast.success('User deleted'),
 *         onError: (error) => toast.error(error.message),
 *       });
 *     }
 *   };
 *
 *   return (
 *     <Button onClick={handleDelete} loading={isPending} variant="danger">
 *       Delete
 *     </Button>
 *   );
 * }
 * ```
 */
export function useDeleteUser() {
  const queryClient = useQueryClient()

  return useMutation<void, ApiError, string>({
    mutationFn: (id) => del(`/admin/users/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminUsersQueryKeys.all })
    },
  })
}

/**
 * Toggles the lock status of a user account.
 *
 * Locks an active user or unlocks a locked user. Locked users
 * cannot log in until their account is unlocked.
 *
 * @returns Mutation object for lock/unlock operations
 *
 * @example
 * ```tsx
 * function LockUserButton({ user }: Props) {
 *   const { mutate, isPending } = useToggleUserLock();
 *   const isLocked = user.status === 'locked';
 *
 *   return (
 *     <Button
 *       onClick={() => mutate({ id: user.id, lock: !isLocked })}
 *       loading={isPending}
 *     >
 *       {isLocked ? 'Unlock' : 'Lock'} Account
 *     </Button>
 *   );
 * }
 * ```
 */
export function useToggleUserLock() {
  const queryClient = useQueryClient()

  return useMutation<LockUserResponse, ApiError, { id: string; lock: boolean }>({
    mutationFn: ({ id, lock }) =>
      post<LockUserResponse>(`/admin/users/${id}/lock`, { lock }),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: adminUsersQueryKeys.all })
      queryClient.invalidateQueries({ queryKey: adminUsersQueryKeys.detail(id) })
    },
  })
}

/**
 * Resends an invitation email to a pending user.
 *
 * This can only be used for users with 'pending' status who
 * haven't completed their account setup.
 *
 * @returns Mutation object for resending invitations
 *
 * @example
 * ```tsx
 * function ResendInviteButton({ user }: Props) {
 *   const { mutate, isPending } = useResendInvite();
 *
 *   return (
 *     <Button
 *       onClick={() => mutate(user.id, {
 *         onSuccess: () => toast.success('Invitation sent'),
 *       })}
 *       loading={isPending}
 *       disabled={user.status !== 'pending'}
 *     >
 *       Resend Invite
 *     </Button>
 *   );
 * }
 * ```
 */
export function useResendInvite() {
  const queryClient = useQueryClient()

  return useMutation<ResendInviteResponse, ApiError, string>({
    mutationFn: (id) => post<ResendInviteResponse>(`/admin/users/${id}/resend-invite`),
    onSuccess: (_, id) => {
      // Refresh the user to get updated invite timestamp
      queryClient.invalidateQueries({ queryKey: adminUsersQueryKeys.detail(id) })
    },
  })
}

/**
 * Performs a bulk action on multiple users.
 *
 * Supports actions like activate, deactivate, resetPassword,
 * resendInvite, and delete for multiple users at once.
 *
 * @returns Mutation object for bulk operations
 *
 * @example
 * ```tsx
 * function BulkActionsToolbar({ selectedIds }: Props) {
 *   const { mutate, isPending } = useBulkUserAction();
 *
 *   const handleActivate = () => {
 *     mutate({
 *       userIds: selectedIds,
 *       action: 'activate',
 *     }, {
 *       onSuccess: (result) => {
 *         toast.success(`${result.affected} users activated`);
 *       },
 *     });
 *   };
 *
 *   return (
 *     <Button onClick={handleActivate} loading={isPending}>
 *       Activate Selected
 *     </Button>
 *   );
 * }
 * ```
 */
export function useBulkUserAction() {
  const queryClient = useQueryClient()

  return useMutation<BulkActionResponse, ApiError, BulkActionRequest>({
    mutationFn: (request) => post<BulkActionResponse>('/admin/users/bulk', request),
    onSuccess: () => {
      // Refresh entire users list after bulk action
      queryClient.invalidateQueries({ queryKey: adminUsersQueryKeys.all })
    },
  })
}
