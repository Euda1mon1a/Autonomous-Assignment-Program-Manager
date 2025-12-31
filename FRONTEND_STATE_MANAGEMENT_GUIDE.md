# Frontend State Management Best Practices & Debugging Guide

**Created:** 2025-12-31
**Source:** SESSION_2_FRONTEND State Patterns Analysis
**Status:** Comprehensive Reference for State Management
**Target:** TanStack Query + Context API architecture

---

## Table of Contents

1. [TanStack Query Architecture](#tanstack-query-architecture)
2. [State Management Anti-Patterns & Fixes](#state-management-anti-patterns--fixes)
3. [TanStack Query Best Practices](#tanstack-query-best-practices)
4. [Cache Invalidation Patterns](#cache-invalidation-patterns)
5. [State Debugging Guide](#state-debugging-guide)
6. [Common Issues & Solutions](#common-issues--solutions)

---

## TanStack Query Architecture

### Current Implementation

**Configuration Location:** `/frontend/src/app/providers.tsx`

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,        // 1 minute default
      refetchOnWindowFocus: false,  // Don't auto-refetch on window focus
      gcTime: 5 * 60 * 1000,        // 5 minute garbage collection
    },
    mutations: {
      retry: false,  // Don't auto-retry mutations
    },
  },
});
```

### Query Structure

```typescript
// Standard pattern for all queries
export function useSchedule(filters: ScheduleFilters) {
  return useQuery<Schedule, ApiError>({
    queryKey: ['schedule', filters],  // Include filters in key
    queryFn: async () => {
      const response = await getSchedule(filters);
      return response.data;
    },
    staleTime: 5 * 60 * 1000,  // 5 minutes for schedule data
    gcTime: 30 * 60 * 1000,     // 30 minutes before garbage collected
    enabled: !!filters.startDate,  // Only fetch if filters are valid
  });
}
```

### Mutation Structure

```typescript
// Standard pattern for mutations
export function useCreateAssignment() {
  const queryClient = useQueryClient();

  return useMutation<Assignment, ApiError, CreateAssignmentInput>({
    mutationFn: (data) => createAssignmentApi(data),

    onSuccess: (newAssignment) => {
      // Update cache optimistically
      queryClient.setQueryData(['assignments'], (old?: Assignment[]) => [
        ...(old ?? []),
        newAssignment,
      ]);

      // Invalidate dependent queries
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      queryClient.invalidateQueries({ queryKey: ['validation'] });
    },

    onError: (error) => {
      console.error('Failed to create assignment:', error);
      // Toast notification handled by caller
    },
  });
}
```

---

## State Management Anti-Patterns & Fixes

### Anti-Pattern 1: Over-Fetching with Multiple Queries

**Problem:**
```typescript
// Bad: Fetches every time component mounts
const { data: people } = usePeople();
const { data: templates } = useRotationTemplates();
const { data: absences } = useAbsences();

// All queries fetch immediately regardless of whether data is needed
```

**Fix:**
```typescript
// Good: Conditional query enabling
const { data: people } = usePeople({
  enabled: !!shouldShowPeopleList,  // Only fetch if needed
});

const { data: templates } = useRotationTemplates({
  enabled: currentTab === 'templates',  // Only fetch when tab active
});

// Combine related queries
const { data: scheduleData } = useSchedule(filters, {
  // This single query fetches both schedule and related data
  select: (response) => ({
    schedule: response.schedule,
    assignments: response.assignments,
    validation: response.validation,
  }),
});
```

---

### Anti-Pattern 2: Broad Cache Invalidation

**Problem:**
```typescript
// Bad: Invalidates ALL assignments even if unrelated
export function useCreateAssignment() {
  return useMutation({
    mutationFn: createAssignmentApi,
    onSuccess: () => {
      // This invalidates ALL assignment queries regardless of filters
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
    },
  });
}

// If user has filters active, ALL cached queries refetch
// Even queries with different date ranges
```

**Fix:**
```typescript
// Good: Selective invalidation by predicate
export function useCreateAssignment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAssignmentInput) => createAssignmentApi(data),
    onSuccess: (newAssignment) => {
      // Invalidate only affected week's data
      queryClient.invalidateQueries({
        queryKey: ['assignments'],
        predicate: (query) => {
          // Only invalidate if date range includes new assignment
          const [, filters] = query.queryKey as [string, ScheduleFilters?];
          return isDateInRange(newAssignment.date, filters?.dateRange);
        },
      });

      // Invalidate validation for this specific week
      queryClient.invalidateQueries({
        queryKey: ['validation', getWeekOf(newAssignment.date)],
      });
    },
  });
}
```

---

### Anti-Pattern 3: Missing Optimistic Updates

**Problem:**
```typescript
// Bad: User waits for network round-trip
const { mutate: updateAssignment } = useUpdateAssignment();

const handleDragDrop = (source, target) => {
  updateAssignment({ ...data }); // Network request

  // UI doesn't update until response returns
  // On slow networks (3G), user sees 1-2 second delay
};
```

**Fix:**
```typescript
// Good: Optimistic update with rollback
export function useUpdateAssignment() {
  const queryClient = useQueryClient();

  return useMutation<Assignment, ApiError, UpdateAssignmentInput>({
    mutationFn: updateAssignmentApi,

    onMutate: async (newData) => {
      // 1. Cancel ongoing queries
      await queryClient.cancelQueries({ queryKey: ['assignments'] });

      // 2. Snapshot old data
      const previousData = queryClient.getQueryData(['assignments']);

      // 3. Update cache optimistically
      queryClient.setQueryData(['assignments'], (old?: Assignment[]) => {
        return old?.map((a) => a.id === newData.id ? newData : a);
      });

      // 4. Return context for rollback
      return { previousData };
    },

    onError: (error, variables, context) => {
      // Rollback on error
      if (context?.previousData) {
        queryClient.setQueryData(['assignments'], context.previousData);
      }
    },

    onSuccess: (data) => {
      // Update with server response
      queryClient.setQueryData(['assignments'], (old?: Assignment[]) => {
        return old?.map((a) => a.id === data.id ? data : a);
      });
    },
  });
}

// Usage
const handleDragDrop = (source, target) => {
  updateAssignment({ ...newData });
  // UI updates immediately, server catches up
};
```

---

### Anti-Pattern 4: Context Overload

**Problem:**
```typescript
// Bad: Too much state in context
const MyContext = createContext<{
  assignments: Assignment[];
  selectedAssignment: Assignment | null;
  filters: Filters;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
  updateAssignment: (a: Assignment) => void;
  deleteAssignment: (id: string) => void;
  // ... 10 more properties
}>(null!);

// Every component subscribes to entire context
// Any change causes full re-render of all consumers
```

**Fix:**
```typescript
// Good: Split contexts by domain
const AssignmentDataContext = createContext<{
  assignments: Assignment[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}>(null!);

const AssignmentActionContext = createContext<{
  updateAssignment: (a: Assignment) => void;
  deleteAssignment: (id: string) => void;
}>(null!);

const AssignmentUIContext = createContext<{
  selectedAssignment: Assignment | null;
  setSelectedAssignment: (a: Assignment | null) => void;
  filters: Filters;
  setFilters: (f: Filters) => void;
}>(null!);

// Components only subscribe to what they need
const ListComponent = () => {
  const { assignments, isLoading } = useContext(AssignmentDataContext);
  // Only re-renders if assignments or isLoading changes
};

const DetailComponent = () => {
  const { selectedAssignment } = useContext(AssignmentUIContext);
  // Only re-renders if selection changes
};
```

---

### Anti-Pattern 5: No Error Handling Strategy

**Problem:**
```typescript
// Bad: Errors not handled consistently
const { data, error } = useSchedule();

if (error) {
  return <div>Error</div>;  // Generic, no retry option
}

// No error reporting, no logging
```

**Fix:**
```typescript
// Good: Consistent error handling
export function useSchedule(filters: ScheduleFilters) {
  return useQuery({
    queryKey: ['schedule', filters],
    queryFn: async () => {
      try {
        return await getScheduleApi(filters);
      } catch (error) {
        // Log for debugging
        console.error('[Schedule Query]', {
          filters,
          error: error.message,
          timestamp: new Date().toISOString(),
        });

        // Throw for TanStack Query to handle
        throw error;
      }
    },

    retry: (failureCount, error: ApiError) => {
      // Don't retry on client errors
      if (error.status >= 400 && error.status < 500) {
        return false;
      }

      // Retry server errors up to 2 times
      return failureCount < 2;
    },
  });
}

// In component
const { data, error, isLoading } = useSchedule(filters);

if (isLoading) {
  return <ScheduleSkeleton />;
}

if (error) {
  return (
    <ErrorAlert
      title="Failed to load schedule"
      message={error.message}
      onRetry={() => refetch()}
    />
  );
}

return <ScheduleView data={data} />;
```

---

## TanStack Query Best Practices

### 1. Query Key Factory Pattern

**Use centralized query keys:**

```typescript
// lib/query-keys.ts
export const scheduleQueryKeys = {
  all: ['schedule'] as const,
  lists: () => [...scheduleQueryKeys.all, 'list'] as const,
  list: (filters: ScheduleFilters) =>
    [...scheduleQueryKeys.lists(), filters] as const,
  details: () => [...scheduleQueryKeys.all, 'detail'] as const,
  detail: (id: string) =>
    [...scheduleQueryKeys.details(), id] as const,
  validation: (startDate: string, endDate: string) =>
    [...scheduleQueryKeys.all, 'validation', startDate, endDate] as const,
} as const;

// Usage
export function useSchedules(filters: ScheduleFilters) {
  return useQuery({
    queryKey: scheduleQueryKeys.list(filters),  // Type-safe key
    queryFn: () => getSchedules(filters),
  });
}

// Invalidation
queryClient.invalidateQueries({
  queryKey: scheduleQueryKeys.all,  // Invalidates all schedule queries
});

queryClient.invalidateQueries({
  queryKey: scheduleQueryKeys.lists(),  // Invalidates only lists
});
```

---

### 2. Cache Time Strategy by Data Type

| Data Type | Example | Stale Time | GC Time | Refetch |
|-----------|---------|-----------|---------|---------|
| **Real-time** | Live health status | 10-30s | N/A | Poll |
| **User actions** | Current assignments | 1-2 min | 10 min | Immediate |
| **Business data** | Templates, rotations | 5-10 min | 30 min | On demand |
| **Reference** | People list, config | 30 min | 60 min | Manual |

```typescript
// Real-time: Active polling
useHealthStatus({
  staleTime: 15 * 1000,  // 15 seconds
  refetchInterval: 30 * 1000,  // Poll every 30 seconds
});

// User actions: Fresh but cached
useAssignments({
  staleTime: 1 * 60 * 1000,  // 1 minute
  gcTime: 10 * 60 * 1000,    // 10 minutes
});

// Reference data: Long-lived cache
usePeople({
  staleTime: 30 * 60 * 1000,  // 30 minutes
  gcTime: 60 * 60 * 1000,     // 1 hour
  refetchOnWindowFocus: false,
});
```

---

### 3. Async Error Handling

```typescript
// Global error handler
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: ApiError) => {
        // Never retry 4xx errors
        if (error?.status >= 400 && error?.status < 500) {
          return false;
        }

        // Retry 5xx errors up to 3 times
        return failureCount < 3;
      },

      retryDelay: (attemptIndex) => {
        // Exponential backoff: 100ms, 200ms, 400ms, 800ms...
        return Math.min(1000 * 2 ** attemptIndex, 30000);
      },
    },
  },
});
```

---

### 4. Dependent Queries

```typescript
// Only fetch person details after person ID is known
export function usePersonDetails(personId: string | null) {
  return useQuery({
    queryKey: ['people', personId, 'details'],
    queryFn: () => getPersonDetails(personId!),
    enabled: !!personId,  // Wait until ID exists
  });
}

// Usage
const [selectedPersonId, setSelectedPersonId] = useState<string | null>(null);
const { data: personDetails } = usePersonDetails(selectedPersonId);

// Query only runs when selectedPersonId is set
```

---

## Cache Invalidation Patterns

### Pattern 1: After Mutations

```typescript
// When creating: invalidate list
useMutation({
  mutationFn: createAssignmentApi,
  onSuccess: (newAssignment) => {
    // Invalidate the list to refetch
    queryClient.invalidateQueries({
      queryKey: ['assignments'],
    });

    // Cache new item
    queryClient.setQueryData(
      ['assignments', newAssignment.id],
      newAssignment
    );
  },
});

// When updating: update existing cache
useMutation({
  mutationFn: updateAssignmentApi,
  onSuccess: (updated) => {
    queryClient.setQueryData(
      ['assignments', updated.id],
      updated
    );
  },
});

// When deleting: remove from cache
useMutation({
  mutationFn: deleteAssignmentApi,
  onSuccess: (deletedId) => {
    queryClient.setQueryData(
      ['assignments'],
      (old?: Assignment[]) => old?.filter((a) => a.id !== deletedId)
    );
  },
});
```

---

### Pattern 2: Cascade Invalidation

```typescript
// When person deleted: invalidate assignments involving that person
useMutation({
  mutationFn: deletePersonApi,
  onSuccess: (deletedPersonId) => {
    // Direct invalidation
    queryClient.invalidateQueries({
      queryKey: ['people', deletedPersonId],
    });

    // Cascade: Invalidate assignments for this person
    queryClient.invalidateQueries({
      queryKey: ['assignments'],
      predicate: (query) => {
        const [, id] = query.queryKey as [string, string?];
        return id === deletedPersonId;
      },
    });

    // Cascade: Invalidate related schedules
    queryClient.invalidateQueries({
      queryKey: ['schedule'],
    });
  },
});
```

---

### Pattern 3: Logout Cache Clearing

```typescript
// Only invalidate auth-dependent data on logout
export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: logoutApi,
    onSuccess: () => {
      // Clear auth state
      queryClient.setQueryData(['auth', 'user'], null);
      queryClient.setQueryData(['auth', 'check'], { authenticated: false });

      // Invalidate all user-dependent data
      queryClient.invalidateQueries();

      // OR: Be selective if needed
      // queryClient.invalidateQueries({ queryKey: ['schedule'] });
      // queryClient.invalidateQueries({ queryKey: ['assignments'] });
    },
  });
}
```

---

## State Debugging Guide

### Debug Strategy 1: React DevTools

**Setup:**
```bash
npm install react-query-devtools
```

**Usage:**
```typescript
// In development
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

export function Providers({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

**How to Use:**
1. Open DevTools in browser
2. Click "React Query" tab
3. Observe cache state in real-time
4. Trigger mutations and see cache updates
5. Check query timing (stale vs fresh)

---

### Debug Strategy 2: Logging

```typescript
// Enable query logging
const queryClient = new QueryClient({
  logger: {
    log: (message) => console.log('🔵 Query:', message),
    warn: (message) => console.warn('⚠️  Query:', message),
    error: (message) => console.error('❌ Query:', message),
  },
});

// Or use custom logger for specific queries
export function useSchedule(filters: ScheduleFilters) {
  return useQuery({
    queryKey: ['schedule', filters],
    queryFn: async () => {
      console.log('📥 Fetching schedule:', filters);
      const start = performance.now();

      try {
        const data = await getScheduleApi(filters);
        const elapsed = performance.now() - start;
        console.log(`📦 Schedule loaded in ${elapsed.toFixed(0)}ms:`, data);
        return data;
      } catch (error) {
        console.error('❌ Schedule fetch failed:', error);
        throw error;
      }
    },
  });
}
```

---

### Debug Strategy 3: Cache State Inspection

```typescript
// Inspect current cache state
const cacheState = queryClient.getQueryCache().findAll();
console.log('Cache state:', cacheState);

// Check specific query
const scheduleQuery = queryClient.getQueryData(['schedule', filters]);
console.log('Schedule cache:', scheduleQuery);

// Inspect mutation observer
const observers = queryClient.getMutationCache().getAll();
console.log('Active mutations:', observers);

// Check garbage collection
console.log('Cache stats:', {
  total: cacheState.length,
  stale: cacheState.filter((q) => q.isStale()).length,
  fresh: cacheState.filter((q) => !q.isStale()).length,
});
```

---

### Debug Strategy 4: Performance Profiling

```typescript
// Track query performance
export function usePerformanceMetrics() {
  useEffect(() => {
    const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
      if (event.type === 'added') {
        const query = event.query;
        const start = performance.now();

        const observer = query.subscribe((state) => {
          if (state.status === 'success' || state.status === 'error') {
            const duration = performance.now() - start;
            console.log('📊 Query Performance:', {
              key: query.queryKey,
              status: state.status,
              duration: `${duration.toFixed(0)}ms`,
            });
            observer();
          }
        });
      }
    });

    return unsubscribe;
  }, []);
}

// Usage in root layout
export default function RootLayout({ children }) {
  usePerformanceMetrics();
  return <>{children}</>;
}
```

---

## Common Issues & Solutions

### Issue 1: Stale Data Being Displayed

**Symptom:** User sees outdated data after making changes.

**Diagnosis:**
```typescript
// Check cache timing
const query = queryClient.getQueryState(['schedule']);
console.log({
  stale: query?.isStale(),
  dataUpdatedAt: new Date(query?.dataUpdatedAt),
  now: new Date(),
});

// Expected: After mutation, should be invalidated immediately
```

**Solution:**
```typescript
// Ensure mutation invalidates the right queries
onSuccess: () => {
  // Wait for active queries to complete
  await queryClient.refetchQueries({ queryKey: ['schedule'] });

  // Or explicitly set new data
  queryClient.setQueryData(['schedule'], (old) => updateData(old));
};
```

---

### Issue 2: Repeated Network Requests

**Symptom:** Network tab shows same request multiple times.

**Diagnosis:**
```typescript
// Check query key includes all filters
queryKey: ['schedule', filters]  // Good
queryKey: ['schedule']  // Bad - loses filter context

// Check enabled condition
enabled: !!filters.startDate  // Should prevent extra requests
```

**Solution:**
```typescript
// Include all variables in query key
export function useSchedule(filters: ScheduleFilters) {
  return useQuery({
    queryKey: ['schedule', JSON.stringify(filters)],  // Serialize complex filters
    queryFn: () => getScheduleApi(filters),
  });
}

// Or use query key factory
queryKey: scheduleQueryKeys.list(filters),
```

---

### Issue 3: Memory Leaks from Queries

**Symptom:** Memory usage grows over time, performance degrades.

**Diagnosis:**
```typescript
// Check garbage collection settings
// Default gcTime: 5 minutes (should be adequate)

// Check for accumulating queries
const allQueries = queryClient.getQueryCache().findAll();
console.log(`${allQueries.length} cached queries`);
```

**Solution:**
```typescript
// Set appropriate gcTime based on data type
queries: {
  short_lived: { gcTime: 1 * 60 * 1000 },   // 1 minute
  normal: { gcTime: 5 * 60 * 1000 },         // 5 minutes (default)
  long_lived: { gcTime: 30 * 60 * 1000 },    // 30 minutes
}
```

---

### Issue 4: Race Conditions in Mutations

**Symptom:** Mutations finish out of order, final state is incorrect.

**Diagnosis:**
```typescript
// Check mutation order
const mutations = queryClient.getMutationCache().getAll();
mutations.forEach((m) => {
  console.log(`Mutation ${m.mutationId}: ${m.state.status}`);
});
```

**Solution:**
```typescript
// Use onMutate for optimistic updates with proper rollback
onMutate: async (newData) => {
  const previous = queryClient.getQueryData(['assignments']);

  queryClient.setQueryData(['assignments'], newData);

  return { previous };  // Saved for rollback
},

onError: (error, variables, context) => {
  if (context?.previous) {
    queryClient.setQueryData(['assignments'], context.previous);
  }
},
```

---

## Monitoring & Observability

### Health Check Metrics

```typescript
export function getQueryClientHealth() {
  const cache = queryClient.getQueryCache();
  const allQueries = cache.findAll();

  return {
    totalCached: allQueries.length,
    staleQueries: allQueries.filter((q) => q.isStale()).length,
    activeQueries: allQueries.filter((q) => q.isStale() === false).length,
    memory: {
      cached: allQueries.reduce((sum, q) => {
        const size = JSON.stringify(q.state.data).length;
        return sum + size;
      }, 0),
      cacheAge: allQueries.map((q) => ({
        key: q.queryKey,
        ageMs: Date.now() - (q.state.dataUpdatedAt ?? 0),
      })),
    },
  };
}
```

---

## Summary: Decision Tree

```
State management question?
├─ Is it from server API?
│  └─ Use TanStack Query ✓
│     ├─ Need to cache?  → staleTime + gcTime
│     ├─ Data changes?  → Invalidate on mutation
│     └─ Network error?  → Retry strategy
│
├─ Is it UI state (selection, modal open)?
│  └─ Use useState + Context if shared ✓
│     └─ Prop drill if only 2-3 levels
│
├─ Is it theme/auth/preferences?
│  └─ Use Context Provider ✓
│     └─ Keep minimal (< 5 values per context)
│
└─ Need global state machine?
   └─ Consider Zustand/Jotai (future)
```

---

**Document Version:** 1.0
**Last Updated:** 2025-12-31
**Reference:** React Query v5.17.0 docs
