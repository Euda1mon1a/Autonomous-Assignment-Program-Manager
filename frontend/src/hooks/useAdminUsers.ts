/**
 * Admin User Management Hooks
 *
 * Hooks for managing system users with React Query caching,
 * optimistic updates, and proper error handling.
 */
import { ApiError, del, get, patch, post } from "@/lib/api";
import type {
  ActivityAction,
  ActivityLogResponse,
  BulkActionRequest,
  User,
  UserCreate,
  UserRole,
  UsersResponse,
  UserStatus,
  UserUpdate,
} from "@/types/admin-users";
import {
  useMutation,
  useQuery,
  useQueryClient,
  UseQueryOptions,
} from "@tanstack/react-query";

// ============================================================================
// Types
// ============================================================================

/**
 * Filters for querying admin users
 */
export interface AdminUserFilters {
  search?: string;
  role?: UserRole | "all";
  status?: UserStatus | "all";
  page?: number;
  pageSize?: number;
}

/**
 * Filters for querying activity logs
 */
export interface ActivityLogFilters {
  userId?: string;
  action?: ActivityAction;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  pageSize?: number;
}

/**
 * Response for lock/unlock action
 */
export interface LockUserResponse {
  success: boolean;
  user: User;
  message: string;
}

/**
 * Response for resend invite action
 */
export interface ResendInviteResponse {
  success: boolean;
  message: string;
}

/**
 * Response for bulk actions
 */
export interface BulkActionResponse {
  success: boolean;
  affected: number;
  failures: string[];
  message: string;
}

// ============================================================================
// Query Keys
// ============================================================================

export const adminUsersQueryKeys = {
  all: ["admin", "users"] as const,
  list: (filters?: AdminUserFilters) =>
    ["admin", "users", "list", filters] as const,
  detail: (id: string) => ["admin", "users", "detail", id] as const,
  activity: (filters?: ActivityLogFilters) =>
    ["admin", "activity", filters] as const,
};

// ============================================================================
// API Functions
// ============================================================================

/**
 * Fetches admin users list from API
 */
async function fetchUsers(filters?: AdminUserFilters): Promise<UsersResponse> {
  const params = new URLSearchParams();

  if (filters?.search) {
    params.set("search", filters.search);
  }
  if (filters?.role && filters.role !== "all") {
    params.set("role", filters.role);
  }
  if (filters?.status && filters.status !== "all") {
    params.set("status", filters.status);
  }
  if (filters?.page !== undefined) {
    params.set("page", String(filters.page));
  }
  if (filters?.pageSize !== undefined) {
    params.set("page_size", String(filters.pageSize));
  }

  const queryString = params.toString();
  return get<UsersResponse>(
    `/admin/users${queryString ? `?${queryString}` : ""}`
  );
}

/**
 * Fetches activity logs from API
 */
async function fetchActivityLog(
  filters?: ActivityLogFilters
): Promise<ActivityLogResponse> {
  const params = new URLSearchParams();

  if (filters?.userId) params.set("userId", filters.userId);
  if (filters?.action) params.set("action", filters.action);
  if (filters?.dateFrom) params.set("dateFrom", filters.dateFrom);
  if (filters?.dateTo) params.set("dateTo", filters.dateTo);
  if (filters?.page !== undefined) params.set("page", String(filters.page));
  if (filters?.pageSize !== undefined)
    params.set("pageSize", String(filters.pageSize));

  const queryString = params.toString();
  return get<ActivityLogResponse>(
    `/admin/users/activity-log${queryString ? `?${queryString}` : ""}`
  );
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetches a paginated list of admin users with optional filtering.
 */
export function useUsers(
  filters?: AdminUserFilters,
  options?: Omit<
    UseQueryOptions<UsersResponse, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<UsersResponse, ApiError>({
    queryKey: adminUsersQueryKeys.list(filters),
    queryFn: () => fetchUsers(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes - shorter for admin data
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  });
}

/**
 * Fetches activity logs.
 */
export function useActivityLog(
  filters?: ActivityLogFilters,
  options?: Omit<
    UseQueryOptions<ActivityLogResponse, ApiError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery<ActivityLogResponse, ApiError>({
    queryKey: adminUsersQueryKeys.activity(filters),
    queryFn: () => fetchActivityLog(filters),
    staleTime: 30 * 1000, // 30 seconds
    placeholderData: (previousData) => previousData,
    ...options,
  });
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
  options?: Omit<UseQueryOptions<User, ApiError>, "queryKey" | "queryFn">
) {
  return useQuery<User, ApiError>({
    queryKey: adminUsersQueryKeys.detail(id),
    queryFn: () => get<User>(`/admin/users/${id}`),
    staleTime: 2 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    enabled: !!id,
    ...options,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Creates a new user in the system.
 */
export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation<User, ApiError, UserCreate>({
    mutationFn: (data) => post<User>("/admin/users", data),
    onSuccess: () => {
      // Invalidate and refetch users list
      queryClient.invalidateQueries({ queryKey: adminUsersQueryKeys.all });
    },
  });
}

/**
 * Updates an existing user.
 */
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation<User, ApiError, { id: string; data: UserUpdate }>({
    mutationFn: ({ id, data }) => patch<User>(`/admin/users/${id}`, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: adminUsersQueryKeys.all });
      queryClient.invalidateQueries({
        queryKey: adminUsersQueryKeys.detail(id),
      });
    },
  });
}

/**
 * Deletes a user from the system.
 */
export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: (id) => del(`/admin/users/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminUsersQueryKeys.all });
    },
  });
}

/**
 * Toggles the lock status of a user account.
 */
export function useToggleUserLock() {
  const queryClient = useQueryClient();

  return useMutation<LockUserResponse, ApiError, { id: string; lock: boolean }>(
    {
      mutationFn: ({ id, lock }) =>
        post<LockUserResponse>(`/admin/users/${id}/lock`, { lock }),
      onSuccess: (_, { id }) => {
        queryClient.invalidateQueries({ queryKey: adminUsersQueryKeys.all });
        queryClient.invalidateQueries({
          queryKey: adminUsersQueryKeys.detail(id),
        });
      },
    }
  );
}

/**
 * Resends an invitation email to a pending user.
 */
export function useResendInvite() {
  const queryClient = useQueryClient();

  return useMutation<ResendInviteResponse, ApiError, string>({
    mutationFn: (id) =>
      post<ResendInviteResponse>(`/admin/users/${id}/resend-invite`),
    onSuccess: (_, id) => {
      // Refresh the user to get updated invite timestamp
      queryClient.invalidateQueries({
        queryKey: adminUsersQueryKeys.detail(id),
      });
    },
  });
}

/**
 * Performs a bulk action on multiple users.
 */
export function useBulkUserAction() {
  const queryClient = useQueryClient();

  return useMutation<BulkActionResponse, ApiError, BulkActionRequest>({
    mutationFn: (request) =>
      post<BulkActionResponse>("/admin/users/bulk", request),
    onSuccess: () => {
      // Refresh entire users list after bulk action
      queryClient.invalidateQueries({ queryKey: adminUsersQueryKeys.all });
    },
  });
}
