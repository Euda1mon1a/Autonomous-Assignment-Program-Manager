"use client";

/**
 * Impersonation Context Provider
 *
 * React context that provides impersonation state and actions throughout
 * the application. Wraps the useImpersonation hook to share state without
 * prop drilling.
 *
 * Security: Only admins can impersonate. All actions are audit logged.
 *
 * @module contexts/ImpersonationContext
 */
import {
  createContext,
  useContext,
  useCallback,
  ReactNode,
} from "react";
import {
  useImpersonation,
  type ImpersonatedUser,
  type ImpersonationStatusResponse,
} from "@/hooks/useImpersonation";
import { useRouter } from "next/navigation";

// ============================================================================
// Types
// ============================================================================

interface ImpersonationContextType {
  /** Whether currently impersonating another user */
  isImpersonating: boolean;
  /** The user being impersonated (if any) */
  targetUser: ImpersonatedUser | null;
  /** The original admin user (if impersonating) */
  originalUser: ImpersonatedUser | null;
  /** When the impersonation session expires */
  sessionExpiresAt: string | null;
  /** Full status response */
  status: ImpersonationStatusResponse | undefined;
  /** Whether status is loading */
  isLoading: boolean;
  /** Whether start impersonation is in progress */
  isStarting: boolean;
  /** Whether end impersonation is in progress */
  isEnding: boolean;
  /** Start impersonating a user by ID */
  startImpersonation: (userId: string) => Promise<void>;
  /** End the current impersonation session */
  endImpersonation: () => Promise<void>;
  /** Refresh impersonation status */
  refreshStatus: () => void;
}

// ============================================================================
// Context
// ============================================================================

const ImpersonationContext = createContext<ImpersonationContextType | undefined>(
  undefined
);

// ============================================================================
// Provider
// ============================================================================

interface ImpersonationProviderProps {
  children: ReactNode;
}

/**
 * Impersonation Provider Component
 *
 * Provides impersonation state and actions to all child components.
 * Should be wrapped around the application inside QueryClientProvider.
 *
 * @example
 * ```tsx
 * <QueryClientProvider client={queryClient}>
 *   <ImpersonationProvider>
 *     <App />
 *   </ImpersonationProvider>
 * </QueryClientProvider>
 * ```
 */
export function ImpersonationProvider({ children }: ImpersonationProviderProps) {
  const router = useRouter();
  const {
    isImpersonating,
    targetUser,
    originalUser,
    sessionExpiresAt,
    status,
    isLoading,
    isStarting,
    isEnding,
    startImpersonation: startMutation,
    endImpersonation: endMutation,
    refetch,
  } = useImpersonation();

  /**
   * Start impersonating a user
   * Automatically redirects to home page on success
   */
  const startImpersonation = useCallback(
    async (userId: string): Promise<void> => {
      return new Promise((resolve, reject) => {
        startMutation.mutate(userId, {
          onSuccess: () => {
            // Redirect to home page to view as the impersonated user
            router.push("/");
            resolve();
          },
          onError: (error) => {
            reject(error);
          },
        });
      });
    },
    [startMutation, router]
  );

  /**
   * End the current impersonation session
   * Automatically redirects to admin users page on success
   */
  const endImpersonation = useCallback(async (): Promise<void> => {
    return new Promise((resolve, reject) => {
      endMutation.mutate(undefined, {
        onSuccess: () => {
          // Redirect to admin users page after ending
          router.push("/admin/users");
          resolve();
        },
        onError: (error) => {
          // Still redirect even on error to avoid stuck state
          router.push("/admin/users");
          reject(error);
        },
      });
    });
  }, [endMutation, router]);

  /**
   * Refresh impersonation status
   */
  const refreshStatus = useCallback(() => {
    refetch();
  }, [refetch]);

  const value: ImpersonationContextType = {
    isImpersonating,
    targetUser,
    originalUser,
    sessionExpiresAt,
    status,
    isLoading,
    isStarting,
    isEnding,
    startImpersonation,
    endImpersonation,
    refreshStatus,
  };

  return (
    <ImpersonationContext.Provider value={value}>
      {children}
    </ImpersonationContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Hook to access impersonation context
 *
 * Must be used within an ImpersonationProvider.
 *
 * @returns Impersonation context value
 * @throws Error if used outside of ImpersonationProvider
 *
 * @example
 * ```tsx
 * function UserActions({ user }) {
 *   const { startImpersonation, isStarting, isImpersonating } = useImpersonationContext();
 *
 *   const handleViewAs = async () => {
 *     try {
 *       await startImpersonation(user.id);
 *     } catch (error) {
 *       console.error('Failed to start impersonation:', error);
 *     }
 *   };
 *
 *   return (
 *     <button onClick={handleViewAs} disabled={isStarting || isImpersonating}>
 *       View As {user.name}
 *     </button>
 *   );
 * }
 * ```
 */
export function useImpersonationContext(): ImpersonationContextType {
  const context = useContext(ImpersonationContext);
  if (context === undefined) {
    throw new Error(
      "useImpersonationContext must be used within an ImpersonationProvider"
    );
  }
  return context;
}
