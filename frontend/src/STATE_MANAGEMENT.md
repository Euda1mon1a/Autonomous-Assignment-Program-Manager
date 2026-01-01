# State Management Patterns - Residency Scheduler Frontend

> **Document Type:** Technical Reference
> **Last Updated:** 2025-12-31
> **Audience:** Frontend Developers, AI Agents

---

## Overview

The Residency Scheduler frontend uses a **layered state management architecture** combining:

1. **React Context** - For global UI state (auth, toasts, chat sessions)
2. **TanStack Query (React Query v5)** - For server state (API data fetching, caching, mutations)
3. **Component Local State** - For ephemeral UI state (form inputs, modals, selections)

**No Zustand or Redux** is used in this codebase. All state management relies on React's built-in primitives plus TanStack Query.

---

## Architecture Diagram

```
+------------------------------------------+
|              Providers Layer              |
|  (providers.tsx - wraps entire app)       |
+------------------------------------------+
|  QueryClientProvider (TanStack Query)     |
|    -> AuthProvider (React Context)        |
|      -> ToastProvider (React Context)     |
|        -> ClaudeChatProvider (optional)   |
+------------------------------------------+
                    |
                    v
+------------------------------------------+
|            Component Layer                |
+------------------------------------------+
|  useQuery / useMutation (server state)    |
|  useContext (global UI state)             |
|  useState / useReducer (local state)      |
+------------------------------------------+
```

---

## 1. React Context Providers

### Location: `/frontend/src/contexts/`

The codebase uses three React Context providers:

### 1.1 AuthContext

**File:** `contexts/AuthContext.tsx`

**Purpose:** Manages authentication state including current user, login/logout, and session validation.

**State Shape:**
```typescript
interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}
```

**Usage:**
```tsx
import { useAuth } from '@/contexts/AuthContext';

function ProfilePage() {
  const { user, isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) {
    return <Redirect to="/login" />;
  }

  return (
    <div>
      <h1>Welcome, {user?.name}</h1>
      <button onClick={logout}>Log Out</button>
    </div>
  );
}
```

**Key Features:**
- Automatic token validation on mount
- httpOnly cookie-based authentication (XSS-resistant)
- Memoized callback functions to prevent re-renders

---

### 1.2 ToastContext

**File:** `contexts/ToastContext.tsx`

**Purpose:** Global toast notification system with queue management.

**State Shape:**
```typescript
interface ToastMethods {
  success: (message: string, options?: ToastOptions) => string;
  error: (error: unknown, options?: ToastOptions) => string;
  warning: (message: string, options?: ToastOptions) => string;
  info: (message: string, options?: ToastOptions) => string;
  dismiss: (id: string) => void;
  dismissAll: () => void;
}

interface ToastContextType {
  toast: ToastMethods;
  // Legacy methods (deprecated but supported)
  showToast: (type: ToastType, message: string, options?: ToastOptions) => string;
  showSuccess: (message: string, options?: ToastOptions) => string;
  showError: (error: unknown, options?: ToastOptions) => string;
  showWarning: (message: string, options?: ToastOptions) => string;
  showInfo: (message: string, options?: ToastOptions) => string;
  dismissToast: (id: string) => void;
  dismissAll: () => void;
}
```

**Usage:**
```tsx
import { useToast } from '@/contexts/ToastContext';

function SaveButton() {
  const { toast } = useToast();

  const handleSave = async () => {
    try {
      await saveData();
      toast.success('Changes saved successfully');
    } catch (error) {
      toast.error(error);  // Automatically extracts error message
    }
  };

  return <button onClick={handleSave}>Save</button>;
}
```

**Key Features:**
- Queue management (max 3 visible toasts)
- Auto-dismiss with configurable duration
- Pause on hover
- Progress bar animation
- Action buttons support

---

### 1.3 ClaudeChatContext

**File:** `contexts/ClaudeChatContext.tsx`

**Purpose:** Manages Claude AI chat sessions for the admin Claude Code Chat interface.

**State Shape:**
```typescript
interface ClaudeChatContextType {
  session: ChatSession | null;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  initializeSession: (programId: string, adminId: string, title?: string) => ChatSession;
  sendMessage: (userInput: string, context?: Partial<ClaudeCodeContext>, onStreamUpdate?: (update: StreamUpdate) => void) => Promise<void>;
  cancelRequest: () => void;
  clearMessages: () => void;
  exportSession: () => ExportedSession | null;
  getSavedSessions: () => SavedSession[];
  loadSession: (sessionId: string) => boolean;
}
```

**Key Features:**
- Streaming response handling via Server-Sent Events
- Session persistence to localStorage
- Session history management (last 20 sessions)
- Request cancellation via AbortController

---

## 2. TanStack Query (Server State)

### Configuration

**File:** `app/providers.tsx`

```typescript
const [queryClient] = useState(
  () =>
    new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 60 * 1000,      // 1 minute
          refetchOnWindowFocus: false,
        },
      },
    })
);
```

### Query Key Factory Pattern

All hooks use a consistent query key factory pattern for cache management:

```typescript
// Example from usePeople.ts
export const peopleQueryKeys = {
  people: (filters?: PeopleFilters) => ['people', filters] as const,
  person: (id: string) => ['people', id] as const,
  residents: (pgyLevel?: number) => ['residents', pgyLevel] as const,
  faculty: (specialty?: string) => ['faculty', specialty] as const,
  certifications: (personId: string) => ['certifications', 'person', personId] as const,
}
```

### Hook Organization

**Location:** `/frontend/src/hooks/`

| Hook File | Domain | Query Keys |
|-----------|--------|------------|
| `useAuth.ts` | Authentication | `authQueryKeys` |
| `useSchedule.ts` | Schedules, assignments, templates | `scheduleQueryKeys` |
| `usePeople.ts` | People, residents, faculty, certifications | `peopleQueryKeys` |
| `useAbsences.ts` | Absence management | `absenceQueryKeys` |
| `useSwaps.ts` | Swap requests | `swapQueryKeys` |
| `useHealth.ts` | Health checks | `healthQueryKeys` |
| `useAdminScheduling.ts` | Admin scheduling operations | `adminSchedulingKeys` |
| `useAdminUsers.ts` | User management | `adminUsersQueryKeys` |
| `useProcedures.ts` | Procedure credentialing | `procedureKeys`, `credentialKeys` |
| `useRAG.ts` | RAG search | `ragQueryKeys` |
| `useResilience.ts` | Emergency coverage | - |
| `useGameTheory.ts` | Game theory analysis | - |
| `useClaudeChat.ts` | Claude AI chat (local state) | - |
| `useWebSocket.ts` | Real-time updates | - |

### Query Hook Pattern

```typescript
export function usePeople(
  filters?: PeopleFilters,
  options?: Omit<UseQueryOptions<ListResponse<Person>, ApiError>, 'queryKey' | 'queryFn'>
) {
  const params = new URLSearchParams()
  if (filters?.role) params.set('role', filters.role)
  if (filters?.pgy_level !== undefined) params.set('pgy_level', String(filters.pgy_level))
  const queryString = params.toString()

  return useQuery<ListResponse<Person>, ApiError>({
    queryKey: ['people', filters],
    queryFn: () => get<ListResponse<Person>>(`/people${queryString ? `?${queryString}` : ''}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}
```

### Mutation Hook Pattern

```typescript
export function useCreatePerson() {
  const queryClient = useQueryClient()

  return useMutation<Person, ApiError, PersonCreate>({
    mutationFn: (data) => post<Person>('/people', data),
    onSuccess: () => {
      // Invalidate related queries to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['people'] })
      queryClient.invalidateQueries({ queryKey: ['residents'] })
      queryClient.invalidateQueries({ queryKey: ['faculty'] })
    },
  })
}
```

---

## 3. Optimistic Updates

**File:** `hooks/useOptimisticUpdate.ts`

### Basic Optimistic Update

```typescript
import { useOptimisticUpdate } from '@/hooks/useOptimisticUpdate';

const mutation = useOptimisticUpdate<Person[], PersonUpdate>({
  queryKey: ['people'],
  mutationFn: (data) => updatePerson(data),
  optimisticUpdate: (currentData, variables) => {
    return currentData?.map(person =>
      person.id === variables.id ? { ...person, ...variables } : person
    ) ?? [];
  },
  onError: (error, variables, context) => {
    toast.error(`Failed to update: ${error.message}`);
  },
});
```

### Optimistic List Operations

```typescript
import { useOptimisticList } from '@/hooks/useOptimisticUpdate';

const { addItem, updateItem, deleteItem, replaceItem } = useOptimisticList<Person>({
  queryKey: ['people'],
  getId: (person) => person.id,
});

// Add new person to cache immediately
addItem(newPerson);

// Update person in cache
updateItem(personId, { name: 'Updated Name' });

// Remove person from cache
deleteItem(personId);
```

### Conflict Resolution

```typescript
import { useOptimisticUpdateWithConflictResolution } from '@/hooks/useOptimisticUpdate';

const mutation = useOptimisticUpdateWithConflictResolution<Schedule, ScheduleUpdate>({
  queryKey: ['schedule'],
  mutationFn: updateSchedule,
  optimisticUpdate: (current, variables) => ({ ...current, ...variables }),
  conflictResolution: {
    hasConflict: (local, server) => local.version !== server.version,
    resolve: (local, server) => ({
      ...server,
      // Merge specific fields from local if needed
      notes: local.notes,
    }),
  },
  onConflict: (local, server, resolved) => {
    toast.warning('Schedule was modified by another user. Changes merged.');
  },
});
```

---

## 4. Type Definitions

### Location: `/frontend/src/types/`

| File | Contents |
|------|----------|
| `api.ts` | Core API types, enums, request/response shapes |
| `index.ts` | Re-exports + view-specific types |
| `chat.ts` | Claude AI chat types |
| `admin-scheduling.ts` | Admin scheduling types |
| `admin-health.ts` | Health check types |
| `admin-users.ts` | User management types |
| `admin-audit.ts` | Audit log types |
| `game-theory.ts` | Game theory analysis types |

### Key Type Patterns

**UUID/Date branded types:**
```typescript
export type UUID = string;
export type DateString = string;  // YYYY-MM-DD
export type DateTimeString = string;  // ISO 8601
```

**List response wrapper:**
```typescript
export interface ListResponse<T> {
  items: T[];
  total: number;
}
```

**API error type:**
```typescript
export interface ApiError extends Error {
  status: number;
  code?: string;
  detail?: string;
}
```

---

## 5. Hook Exports

**File:** `hooks/index.ts`

All hooks and types are centrally exported:

```typescript
// Import hooks
import {
  usePeople,
  usePerson,
  useCreatePerson,
  useUpdatePerson,
  useDeletePerson,
  peopleQueryKeys,
  type PeopleFilters,
  type PersonType,
} from '@/hooks';

// Import types
import type { Person, PersonCreate, PersonUpdate } from '@/types';
```

---

## 6. WebSocket Real-Time Updates

**File:** `hooks/useWebSocket.ts`

The application uses WebSockets for real-time schedule updates:

```typescript
import { useScheduleWebSocket } from '@/hooks';

function ScheduleView() {
  const { connectionState, lastEvent, subscribe, unsubscribe } = useScheduleWebSocket({
    onScheduleUpdated: (event) => {
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
    },
    onAssignmentChanged: (event) => {
      toast.info(`Assignment updated for ${event.personName}`);
    },
    onConflictDetected: (event) => {
      toast.warning(`Conflict detected: ${event.message}`);
    },
  });

  // Subscribe to specific schedule updates
  useEffect(() => {
    subscribe('schedule-updates');
    return () => unsubscribe('schedule-updates');
  }, []);
}
```

---

## 7. Best Practices

### Do

1. **Use query key factories** - Always use the domain-specific `*QueryKeys` objects
2. **Invalidate related queries** - On mutation success, invalidate all affected queries
3. **Use optimistic updates** - For better UX on slow networks
4. **Handle loading and error states** - Every component using queries should handle all states
5. **Type your hooks** - Use generic type parameters for type safety

### Don't

1. **Don't store server state in Context** - Use TanStack Query for API data
2. **Don't create global state for ephemeral UI** - Use local component state
3. **Don't manually manage cache** - Let TanStack Query handle invalidation
4. **Don't use `queryClient.setQueryData` without rollback** - Use optimistic update pattern

---

## 8. Migration Notes

### From Legacy `queryKeys` Object

The centralized `queryKeys` object in `hooks/index.ts` is deprecated. Migrate to domain-specific factories:

```typescript
// Old (deprecated)
import { queryKeys } from '@/hooks';
queryClient.invalidateQueries({ queryKey: queryKeys.people() });

// New (recommended)
import { peopleQueryKeys } from '@/hooks';
queryClient.invalidateQueries({ queryKey: peopleQueryKeys.people() });
```

### From Legacy Toast Methods

The `showSuccess`, `showError` methods are deprecated. Use the new `toast` object:

```typescript
// Old (deprecated)
const { showSuccess, showError } = useToast();
showSuccess('Saved!');

// New (recommended)
const { toast } = useToast();
toast.success('Saved!');
```

---

## 9. Files Reference

| Path | Purpose |
|------|---------|
| `app/providers.tsx` | Root provider composition |
| `contexts/AuthContext.tsx` | Authentication state |
| `contexts/ToastContext.tsx` | Toast notification state |
| `contexts/ClaudeChatContext.tsx` | Claude AI chat state |
| `hooks/index.ts` | Central hook exports |
| `hooks/use*.ts` | Domain-specific data hooks |
| `hooks/useOptimisticUpdate.ts` | Optimistic update utilities |
| `hooks/useWebSocket.ts` | Real-time WebSocket connection |
| `types/index.ts` | Type re-exports |
| `types/api.ts` | Core API types |
| `types/chat.ts` | Chat feature types |
| `lib/api.ts` | Axios-based API client |
| `lib/auth.ts` | Authentication utilities |
| `lib/errors.ts` | Error handling utilities |
