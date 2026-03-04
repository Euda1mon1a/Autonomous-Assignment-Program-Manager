/**
 * Impersonation Hooks for Admin "View As User" Feature
 *
 * TanStack Query hooks for managing user impersonation with proper
 * cache management, token storage, and state synchronization.
 *
 * Security: Impersonation requires admin privileges and is audit logged.
 *
 * @module hooks/useImpersonation
 */
import { ApiError, get, post } from "@/lib/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// ============================================================================
// Types
// ============================================================================

/**
 * User information for impersonation display
 */
export interface ImpersonatedUser {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
}

/**
 * Response from impersonation status endpoint
 */
export interface ImpersonationStatusResponse {
  isImpersonating: boolean;
  targetUser: ImpersonatedUser | null;
  originalUser: ImpersonatedUser | null;
  sessionExpiresAt: string | null;
}

/**
 * Response from start impersonation endpoint
 */
export interface StartImpersonationResponse {
  success: boolean;
  impersonationToken: string;
  targetUser: ImpersonatedUser;
  originalUser: ImpersonatedUser;
  sessionExpiresAt: string;
  message: string;
}

/**
 * Response from end impersonation endpoint
 */
export interface EndImpersonationResponse {
  success: boolean;
  message: string;
  restoredUser: ImpersonatedUser;
}

/**
 * API response from status endpoint (after axios interceptor camelCase conversion)
 */
interface ImpersonationStatusApiResponse {
  isImpersonating: boolean;
  targetUser: {
    id: string;
    username: string;
    email: string;
    firstName: string;
    lastName: string;
    role: string;
  } | null;
  originalUser: {
    id: string;
    username: string;
    email: string;
    firstName: string;
    lastName: string;
    role: string;
  } | null;
  sessionExpiresAt: string | null;
}

/**
 * API response from start impersonation (after axios interceptor camelCase conversion)
 */
interface StartImpersonationApiResponse {
  success: boolean;
  impersonationToken: string;
  targetUser: {
    id: string;
    username: string;
    email: string;
    firstName: string;
    lastName: string;
    role: string;
  };
  originalUser: {
    id: string;
    username: string;
    email: string;
    firstName: string;
    lastName: string;
    role: string;
  };
  sessionExpiresAt: string;
  message: string;
}

/**
 * API response from end impersonation (after axios interceptor camelCase conversion)
 */
interface EndImpersonationApiResponse {
  success: boolean;
  message: string;
  restoredUser: {
    id: string;
    username: string;
    email: string;
    firstName: string;
    lastName: string;
    role: string;
  };
}

// ============================================================================
// Constants
// ============================================================================

const IMPERSONATION_TOKEN_KEY = "impersonation_token";

// ============================================================================
// Query Keys
// ============================================================================

export const impersonationQueryKeys = {
  all: ["impersonation"] as const,
  status: () => ["impersonation", "status"] as const,
};

// ============================================================================
// Token Storage Helpers
// ============================================================================

/**
 * Store impersonation token in localStorage
 */
function storeImpersonationToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(IMPERSONATION_TOKEN_KEY, token);
  }
}

/**
 * Get impersonation token from localStorage
 */
export function getImpersonationToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem(IMPERSONATION_TOKEN_KEY);
  }
  return null;
}

/**
 * Clear impersonation token from localStorage
 */
function clearImpersonationToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(IMPERSONATION_TOKEN_KEY);
  }
}

// ============================================================================
// API Transform Functions
// ============================================================================

/**
 * Transform API user response to frontend format
 */
function transformApiUser(
  apiUser: {
    id: string;
    username: string;
    email: string;
    firstName: string;
    lastName: string;
    role: string;
  } | null
): ImpersonatedUser | null {
  if (!apiUser) return null;
  return {
    id: apiUser.id,
    username: apiUser.username,
    email: apiUser.email,
    firstName: apiUser.firstName,
    lastName: apiUser.lastName,
    role: apiUser.role,
  };
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Fetch current impersonation status
 */
async function fetchImpersonationStatus(): Promise<ImpersonationStatusResponse> {
  const token = getImpersonationToken();
  const headers: Record<string, string> = {};

  if (token) {
    headers["X-Impersonation-Token"] = token;
  }

  const response = await get<ImpersonationStatusApiResponse>(
    "/auth/impersonation-status",
    { headers }
  );

  return {
    isImpersonating: response.isImpersonating,
    targetUser: transformApiUser(response.targetUser),
    originalUser: transformApiUser(response.originalUser),
    sessionExpiresAt: response.sessionExpiresAt,
  };
}

/**
 * Start impersonating a user
 */
async function startImpersonation(
  targetUserId: string
): Promise<StartImpersonationResponse> {
  const response = await post<StartImpersonationApiResponse>(
    "/auth/impersonate",
    {
      targetUserId: targetUserId,
    }
  );

  // Store the impersonation token
  storeImpersonationToken(response.impersonationToken);

  return {
    success: response.success,
    impersonationToken: response.impersonationToken,
    targetUser: transformApiUser(response.targetUser)!,
    originalUser: transformApiUser(response.originalUser)!,
    sessionExpiresAt: response.sessionExpiresAt,
    message: response.message,
  };
}

/**
 * End current impersonation session
 */
async function endImpersonation(): Promise<EndImpersonationResponse> {
  const token = getImpersonationToken();

  if (!token) {
    throw new Error("No impersonation token found");
  }

  const response = await post<EndImpersonationApiResponse>(
    "/auth/end-impersonation",
    {},
    {
      headers: {
        "X-Impersonation-Token": token,
      },
    }
  );

  // Clear the impersonation token
  clearImpersonationToken();

  return {
    success: response.success,
    message: response.message,
    restoredUser: transformApiUser(response.restoredUser)!,
  };
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Hook to fetch current impersonation status
 *
 * @returns Query result with impersonation status
 */
export function useImpersonationStatus() {
  return useQuery<ImpersonationStatusResponse, ApiError>({
    queryKey: impersonationQueryKeys.status(),
    queryFn: fetchImpersonationStatus,
    staleTime: 30 * 1000, // 30 seconds
    refetchOnWindowFocus: true, // Important for impersonation state sync
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Hook to start impersonating a user
 *
 * @returns Mutation for starting impersonation
 */
export function useStartImpersonation() {
  const queryClient = useQueryClient();

  return useMutation<StartImpersonationResponse, ApiError, string>({
    mutationFn: startImpersonation,
    onSuccess: () => {
      // Invalidate impersonation status to refetch
      queryClient.invalidateQueries({
        queryKey: impersonationQueryKeys.status(),
      });
      // Invalidate auth queries to update current user
      queryClient.invalidateQueries({ queryKey: ["auth"] });
    },
  });
}

/**
 * Hook to end current impersonation session
 *
 * @returns Mutation for ending impersonation
 */
export function useEndImpersonation() {
  const queryClient = useQueryClient();

  return useMutation<EndImpersonationResponse, ApiError, void>({
    mutationFn: endImpersonation,
    onSuccess: () => {
      // Invalidate impersonation status to refetch
      queryClient.invalidateQueries({
        queryKey: impersonationQueryKeys.status(),
      });
      // Invalidate auth queries to restore original user
      queryClient.invalidateQueries({ queryKey: ["auth"] });
      // Invalidate all queries to refetch data as original user
      queryClient.invalidateQueries();
    },
  });
}

// ============================================================================
// Combined Hook
// ============================================================================

/**
 * Main impersonation hook combining status query and mutations
 *
 * Provides a unified interface for impersonation functionality:
 * - Current impersonation status
 * - Start/end impersonation mutations
 * - Derived state helpers
 *
 * @returns Combined impersonation state and actions
 *
 * @example
 * ```tsx
 * function AdminUserRow({ user }) {
 *   const { startImpersonation, isStarting, isImpersonating } = useImpersonation();
 *
 *   const handleViewAs = () => {
 *     startImpersonation.mutate(user.id, {
 *       onSuccess: () => {
 *         router.push('/');
 *       }
 *     });
 *   };
 *
 *   return (
 *     <button onClick={handleViewAs} disabled={isStarting || isImpersonating}>
 *       View As
 *     </button>
 *   );
 * }
 * ```
 */
export function useImpersonation() {
  const statusQuery = useImpersonationStatus();
  const startMutation = useStartImpersonation();
  const endMutation = useEndImpersonation();

  return {
    // Status query
    status: statusQuery.data,
    isLoading: statusQuery.isLoading,
    isError: statusQuery.isError,
    error: statusQuery.error,
    refetch: statusQuery.refetch,

    // Derived state
    isImpersonating: statusQuery.data?.isImpersonating ?? false,
    targetUser: statusQuery.data?.targetUser ?? null,
    originalUser: statusQuery.data?.originalUser ?? null,
    sessionExpiresAt: statusQuery.data?.sessionExpiresAt ?? null,

    // Mutations
    startImpersonation: startMutation,
    endImpersonation: endMutation,

    // Mutation states
    isStarting: startMutation.isPending,
    isEnding: endMutation.isPending,
  };
}
