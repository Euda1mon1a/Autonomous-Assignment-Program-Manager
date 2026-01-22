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
  AdminUserApiResponse,
  AdminUserListApiResponse,
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
 * Transform a raw API user response to the frontend User type.
 * Handles snake_case to camelCase conversion and status derivation.
 */
function transformApiUser(apiUser: AdminUserApiResponse): User {
  // Derive status from isActive and isLocked flags (camelCase from axios interceptor)
  let status: UserStatus;
  if (apiUser.isLocked) {
    status = "locked";
  } else if (!apiUser.isActive) {
    status = "inactive";
  } else if (apiUser.inviteSentAt && !apiUser.inviteAcceptedAt) {
    status = "pending";
  } else {
    status = "active";
  }

  return {
    id: apiUser.id,
    email: apiUser.email,
    firstName: apiUser.firstName || "",
    lastName: apiUser.lastName || "",
    role: apiUser.role as UserRole,
    status,
    lastLogin: apiUser.lastLogin || undefined,
    createdAt: apiUser.createdAt || new Date().toISOString(),
    updatedAt: apiUser.updatedAt || new Date().toISOString(),
    mfaEnabled: false, // Not provided by API, default to false
    failedLoginAttempts: 0, // Not provided by API, default to 0
    lockedUntil: undefined,
  };
}

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
  const response = await get<AdminUserListApiResponse>(
    `/admin/users${queryString ? `?${queryString}` : ""}`
  );

  // Transform API response to frontend format
  return {
    users: response.items.map(transformApiUser),
    total: response.total,
    page: response.page,
    pageSize: response.pageSize,
    totalPages: response.totalPages,
  };
}

/**
 * Fetches activity logs from API
 */
async function fetchActivityLog(
  filters?: ActivityLogFilters
): Promise<ActivityLogResponse> {
  const params = new URLSearchParams();

  if (filters?.userId) params.set("user_id", filters.userId);
  if (filters?.action) params.set("action", filters.action);
  if (filters?.dateFrom) params.set("date_from", filters.dateFrom);
  if (filters?.dateTo) params.set("date_to", filters.dateTo);
  if (filters?.page !== undefined) params.set("page", String(filters.page));
  if (filters?.pageSize !== undefined)
    params.set("page_size", String(filters.pageSize));

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
    queryFn: async () => {
      const response = await get<AdminUserApiResponse>(`/admin/users/${id}`);
      return transformApiUser(response);
    },
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
    mutationFn: async (data) => {
      // Transform camelCase to snake_case for API
      const apiPayload = {
        email: data.email,
        firstName: data.firstName,
        lastName: data.lastName,
        role: data.role,
        send_invite: data.sendInvite,
      };
      const response = await post<AdminUserApiResponse>(
        "/admin/users",
        apiPayload
      );
      return transformApiUser(response);
    },
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
    mutationFn: async ({ id, data }) => {
      // Transform camelCase to snake_case for API
      const apiPayload: Record<string, unknown> = {};
      if (data.email !== undefined) apiPayload.email = data.email;
      if (data.firstName !== undefined) apiPayload.firstName = data.firstName;
      if (data.lastName !== undefined) apiPayload.lastName = data.lastName;
      if (data.role !== undefined) apiPayload.role = data.role;
      if (data.status !== undefined) {
        // Map status to isActive
        apiPayload.isActive = data.status === "active";
      }

      const response = await patch<AdminUserApiResponse>(
        `/admin/users/${id}`,
        apiPayload
      );
      return transformApiUser(response);
    },
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
      mutationFn: async ({ id, lock }) => {
        // Backend expects 'locked' field, not 'lock'
        const response = await post<{
          userId: string;
          isLocked: boolean;
          lockReason: string | null;
          lockedAt: string | null;
          lockedBy: string | null;
          message: string;
        }>(`/admin/users/${id}/lock`, { locked: lock });

        // Transform response to match expected format
        return {
          success: true,
          user: {
            id: response.userId,
          } as User,
          message: response.message,
        };
      },
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
    mutationFn: async (request) => {
      // Transform to snake_case for API
      const apiPayload = {
        userIds: request.userIds,
        action: request.action,
      };

      const response = await post<{
        action: string;
        affectedCount: number;
        successIds: string[];
        failedIds: string[];
        errors: string[];
        message: string;
      }>("/admin/users/bulk", apiPayload);

      return {
        success: response.failedIds.length === 0,
        affected: response.affectedCount,
        failures: response.errors,
        message: response.message,
      };
    },
    onSuccess: () => {
      // Refresh entire users list after bulk action
      queryClient.invalidateQueries({ queryKey: adminUsersQueryKeys.all });
    },
  });
}
