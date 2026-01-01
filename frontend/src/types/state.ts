/**
 * State Management Types
 *
 * Centralized type definitions for React Context providers and state management.
 * These types are used by AuthContext, ToastContext, ClaudeChatContext, and
 * the optimistic update hooks.
 */

// Re-export auth types from lib/auth
export type {
  User,
  LoginCredentials,
  LoginResponse,
  AuthCheckResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
} from '@/lib/auth';

// Re-export chat types from types/chat
export type {
  ChatMessage,
  ChatSession,
  CodeBlock,
  ChatArtifact,
  StreamUpdate,
  ClaudeCodeRequest,
  ClaudeCodeResponse,
  ClaudeCodeExecutionContext,
  ScheduleContext,
  RotationContext,
  ConstraintContext,
  ResidentContext,
} from './chat';

// ============================================================================
// Auth Context Types
// ============================================================================

/**
 * Authentication context state and methods.
 *
 * Provides user authentication state and functions for login/logout.
 * Uses httpOnly cookie-based JWT for XSS-resistant authentication.
 */
export interface AuthContextType {
  /** Current authenticated user, or null if not logged in */
  user: import('@/lib/auth').User | null;
  /** Whether authentication state is being loaded/validated */
  isLoading: boolean;
  /** Convenience boolean for checking if user is authenticated */
  isAuthenticated: boolean;
  /** Login with username/password credentials */
  login: (credentials: import('@/lib/auth').LoginCredentials) => Promise<void>;
  /** Logout and clear session */
  logout: () => Promise<void>;
  /** Refresh user data from server */
  refreshUser: () => Promise<void>;
}

// ============================================================================
// Toast Context Types
// ============================================================================

/**
 * Toast notification types.
 */
export type ToastType = 'success' | 'error' | 'warning' | 'info';

/**
 * Position options for toast notifications.
 */
export type ToastPosition = 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';

/**
 * Action button for toast notifications.
 */
export interface ToastAction {
  /** Button label text */
  label: string;
  /** Click handler */
  onClick: () => void;
}

/**
 * Options when showing a toast notification.
 */
export interface ToastOptions {
  /** Duration in milliseconds before auto-dismiss (default: 5000) */
  duration?: number;
  /** If true, toast will not auto-dismiss */
  persistent?: boolean;
  /** Optional action button */
  action?: ToastAction;
}

/**
 * Internal toast item structure.
 */
export interface ToastItem {
  /** Unique identifier for the toast */
  id: string;
  /** Type determines the icon and color */
  type: ToastType;
  /** Message to display */
  message: string;
  /** Optional duration override */
  duration?: number;
  /** Whether to persist until manually dismissed */
  persistent?: boolean;
  /** Optional action button */
  action?: ToastAction;
}

/**
 * Modern toast methods object.
 */
export interface ToastMethods {
  /** Show a success toast */
  success: (message: string, options?: ToastOptions) => string;
  /** Show an error toast (accepts Error object or string) */
  error: (error: unknown, options?: ToastOptions) => string;
  /** Show a warning toast */
  warning: (message: string, options?: ToastOptions) => string;
  /** Show an info toast */
  info: (message: string, options?: ToastOptions) => string;
  /** Dismiss a specific toast by ID */
  dismiss: (id: string) => void;
  /** Dismiss all active toasts */
  dismissAll: () => void;
}

/**
 * Toast context state and methods.
 *
 * Provides global toast notification system with queue management.
 */
export interface ToastContextType {
  /** Modern toast methods (recommended) */
  toast: ToastMethods;

  // Legacy methods (deprecated but supported for backward compatibility)
  /** @deprecated Use toast.success() instead */
  showToast: (type: ToastType, message: string, options?: ToastOptions) => string;
  /** @deprecated Use toast.success() instead */
  showSuccess: (message: string, options?: ToastOptions) => string;
  /** @deprecated Use toast.error() instead */
  showError: (error: unknown, options?: ToastOptions) => string;
  /** @deprecated Use toast.warning() instead */
  showWarning: (message: string, options?: ToastOptions) => string;
  /** @deprecated Use toast.info() instead */
  showInfo: (message: string, options?: ToastOptions) => string;
  /** @deprecated Use toast.dismiss() instead */
  dismissToast: (id: string) => void;
  /** @deprecated Use toast.dismissAll() instead */
  dismissAll: () => void;
}

// ============================================================================
// Claude Chat Context Types
// ============================================================================

/**
 * Saved session metadata for session history.
 */
export interface SavedSession {
  /** Session ID */
  id: string;
  /** Session title */
  title: string;
  /** When session was created */
  createdAt: Date;
  /** When session was last updated */
  updatedAt: Date;
  /** Number of messages in the session */
  messageCount: number;
  /** Program ID for context */
  programId: string;
}

/**
 * Exported session data structure.
 */
export interface ExportedSession {
  /** Session ID */
  id: string;
  /** Session title */
  title: string;
  /** All messages in the session */
  messages: import('./chat').ChatMessage[];
  /** When session was created */
  createdAt: Date;
  /** When session was last updated */
  updatedAt: Date;
  /** Program ID for context */
  programId: string;
  /** Admin ID who owns the session */
  adminId: string;
}

/**
 * Context data for Claude Code requests.
 */
export interface ClaudeCodeContext {
  /** Program ID for context */
  programId: string;
  /** Admin ID making the request */
  adminId: string;
  /** Current session ID */
  sessionId: string;
  /** Additional context properties */
  [key: string]: unknown;
}

/**
 * Claude Chat context state and methods.
 *
 * Provides AI chat functionality with streaming responses and session management.
 */
export interface ClaudeChatContextType {
  /** Current chat session */
  session: import('./chat').ChatSession | null;
  /** Messages in the current session */
  messages: import('./chat').ChatMessage[];
  /** Whether a request is in progress */
  isLoading: boolean;
  /** Current error message, if any */
  error: string | null;
  /** Initialize a new chat session */
  initializeSession: (programId: string, adminId: string, title?: string) => import('./chat').ChatSession;
  /** Send a message and get streaming response */
  sendMessage: (
    userInput: string,
    context?: Partial<ClaudeCodeContext>,
    onStreamUpdate?: (update: import('./chat').StreamUpdate) => void
  ) => Promise<void>;
  /** Cancel the current request */
  cancelRequest: () => void;
  /** Clear all messages in the session */
  clearMessages: () => void;
  /** Export the current session */
  exportSession: () => ExportedSession | null;
  /** Get list of saved sessions */
  getSavedSessions: () => SavedSession[];
  /** Load a previously saved session */
  loadSession: (sessionId: string) => boolean;
}

// ============================================================================
// Optimistic Update Types
// ============================================================================

/**
 * Context returned from onMutate handler containing rollback data.
 */
export interface MutationContext<T> {
  /** Previous data for rollback on error */
  previousData?: T;
}

/**
 * Options for useOptimisticUpdate hook.
 */
export interface OptimisticUpdateOptions<T, V> {
  /** Query key to update */
  queryKey: string[];
  /** Mutation function that performs the API call */
  mutationFn: (variables: V) => Promise<T>;
  /** Function to compute optimistic state */
  optimisticUpdate: (currentData: T | undefined, variables: V) => T;
  /** Optional error callback */
  onError?: (error: Error, variables: V, context: MutationContext<T> | undefined) => void;
  /** Optional success callback */
  onSuccess?: (data: T, variables: V) => void;
}

/**
 * Options for useOptimisticList hook.
 */
export interface OptimisticListOptions<T> {
  /** Query key for the list */
  queryKey: string[];
  /** Function to extract ID from an item */
  getId: (item: T) => string | number;
}

/**
 * Conflict resolution strategy for optimistic updates.
 */
export interface ConflictResolutionStrategy<T> {
  /** Check if server data conflicts with local changes */
  hasConflict: (local: T, server: T) => boolean;
  /** Resolve conflict between local and server data */
  resolve: (local: T, server: T) => T;
}

/**
 * Recorded conflict for debugging and analytics.
 */
export interface RecordedConflict<T> {
  /** Local data before resolution */
  local: T;
  /** Server data that conflicted */
  server: T;
  /** Resolved data */
  resolved: T;
  /** When the conflict occurred */
  timestamp: number;
}

/**
 * Performance statistics for optimistic updates.
 */
export interface OptimisticUpdateStats {
  /** Total number of updates attempted */
  totalUpdates: number;
  /** Number of successful updates */
  successfulUpdates: number;
  /** Number of failed updates */
  failedUpdates: number;
  /** Number of rollbacks performed */
  rollbacks: number;
  /** Average round-trip time in milliseconds */
  averageRoundTripTime: number;
  /** Success rate as percentage */
  successRate: number;
  /** Rollback rate as percentage */
  rollbackRate: number;
}

// ============================================================================
// WebSocket Types (for real-time updates)
// ============================================================================

/**
 * WebSocket connection states.
 */
export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error' | 'reconnecting';

/**
 * Event types received from WebSocket.
 */
export type EventType =
  | 'schedule.updated'
  | 'assignment.changed'
  | 'swap.requested'
  | 'swap.approved'
  | 'swap.rejected'
  | 'conflict.detected'
  | 'resilience.alert'
  | 'connection.ack';

/**
 * Base WebSocket event structure.
 */
export interface WebSocketEvent<T = unknown> {
  /** Event type identifier */
  type: EventType;
  /** Event payload */
  data: T;
  /** When the event was created */
  timestamp: string;
}
