/**
 * React Context Providers
 *
 * Centralized exports for all React Context providers and their hooks.
 * These contexts manage global application state that doesn't belong
 * in React Query (UI state, authentication, notifications).
 */

// ============================================================================
// Auth Context
// ============================================================================
export { AuthProvider, useAuth } from './AuthContext';

// ============================================================================
// Toast Context
// ============================================================================
export { ToastProvider, useToast } from './ToastContext';

// ============================================================================
// Claude Chat Context
// ============================================================================
export { ClaudeChatProvider, useClaudeChatContext } from './ClaudeChatContext';

// ============================================================================
// Impersonation Context
// ============================================================================
export { ImpersonationProvider, useImpersonationContext } from './ImpersonationContext';

// ============================================================================
// Type Re-exports
// ============================================================================
// Types are available from @/types/state
// Import like: import type { AuthContextType, ToastContextType } from '@/types';
