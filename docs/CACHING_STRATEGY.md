# React Query Caching Strategy

## Document Purpose

This document defines the caching strategy for the Residency Scheduler frontend, ensuring optimal performance while maintaining data consistency for schedule-critical operations.

**Author:** Opus 4.5 (Strategic Architect)
**Status:** APPROVED FOR IMPLEMENTATION
**Last Updated:** 2024-12-13

---

## Table of Contents

1. [Overview](#overview)
2. [Cache Time Configuration](#cache-time-configuration)
3. [Entity-Specific Strategies](#entity-specific-strategies)
4. [Cache Invalidation Rules](#cache-invalidation-rules)
5. [Optimistic Updates](#optimistic-updates)
6. [Background Refetching](#background-refetching)
7. [Implementation Patterns](#implementation-patterns)

---

## Overview

### Why Caching Matters

The Residency Scheduler displays complex schedule data that:
- Is viewed frequently but changes infrequently
- Requires real-time accuracy for emergency coverage
- Must be consistent across multiple users editing simultaneously
- Contains interconnected data (changes to one entity affect others)

### React Query Concepts

| Term | Definition |
|------|------------|
| `staleTime` | How long data is considered "fresh" - no refetch during this period |
| `gcTime` | How long inactive data stays in cache before garbage collection |
| `refetchInterval` | Automatic polling interval for real-time data |
| `refetchOnWindowFocus` | Refetch when user returns to the browser tab |

---

## Cache Time Configuration

### Entity Cache Times Summary

| Entity | staleTime | gcTime | refetchInterval | Rationale |
|--------|-----------|--------|-----------------|-----------|
| **Schedule** | 1 min | 10 min | 5 min | Core view, needs freshness but is expensive to fetch |
| **Assignments** | 1 min | 10 min | - | Tied to schedule, changes frequently during edits |
| **Validation** | 2 min | 10 min | - | Derived from assignments, computationally expensive |
| **People** | 5 min | 30 min | - | Rarely changes, static reference data |
| **Residents** | 5 min | 30 min | - | Subset of people, same rationale |
| **Faculty** | 5 min | 30 min | - | Subset of people, same rationale |
| **Absences** | 2 min | 10 min | - | Affects availability, moderate change frequency |
| **Rotation Templates** | 10 min | 60 min | - | Configuration data, very rarely changes |
| **Schedule Runs** | 5 min | 30 min | - | Historical/audit data, immutable after creation |

---

## Entity-Specific Strategies

### Schedule Data

**Priority: CRITICAL**

The schedule is the primary view and must balance freshness with performance.

```typescript
// Configuration
{
  staleTime: 60 * 1000,          // 1 minute
  gcTime: 10 * 60 * 1000,        // 10 minutes
  refetchOnWindowFocus: true,
  refetchInterval: 5 * 60 * 1000, // Poll every 5 minutes
}
```

**Rationale:**
- Schedule changes are collaborative - multiple coordinators may edit
- 5-minute polling catches external changes without overwhelming the server
- Window focus refetch ensures data is fresh when user returns
- Short staleTime ensures quick refreshes after mutations

### People (Residents, Faculty)

**Priority: LOW**

People data is relatively static and acts as reference data.

```typescript
// Configuration
{
  staleTime: 5 * 60 * 1000,       // 5 minutes
  gcTime: 30 * 60 * 1000,         // 30 minutes
  refetchOnWindowFocus: false,
}
```

**Rationale:**
- New residents/faculty are added rarely (start of academic year)
- Changes don't affect real-time scheduling decisions
- Long cache reduces unnecessary network requests

### Absences

**Priority: MEDIUM**

Absences directly affect scheduling availability and emergency coverage.

```typescript
// Configuration
{
  staleTime: 2 * 60 * 1000,       // 2 minutes
  gcTime: 10 * 60 * 1000,         // 10 minutes
  refetchOnWindowFocus: true,
}
```

**Rationale:**
- Emergency absences can be entered at any time
- Affects availability matrix for schedule generation
- Window focus refetch catches new absences entered by others

### Rotation Templates

**Priority: LOW**

Configuration data that changes very rarely.

```typescript
// Configuration
{
  staleTime: 10 * 60 * 1000,      // 10 minutes
  gcTime: 60 * 60 * 1000,         // 1 hour
  refetchOnWindowFocus: false,
}
```

**Rationale:**
- Templates are set up once and rarely modified
- Long cache time is safe and reduces server load
- No need for real-time updates

### Validation Results

**Priority: HIGH**

ACGME compliance data that must be accurate but is computationally expensive.

```typescript
// Configuration
{
  staleTime: 2 * 60 * 1000,       // 2 minutes
  gcTime: 10 * 60 * 1000,         // 10 minutes
  refetchOnWindowFocus: false,    // Avoid expensive recalculation
}
```

**Rationale:**
- Validation is computationally expensive on the backend
- Results only change when assignments change
- Explicit invalidation after mutations is preferred over automatic refetch

---

## Cache Invalidation Rules

### Mutation-Based Invalidation

When a mutation occurs, related queries must be invalidated to ensure consistency.

#### Schedule Generation

```typescript
// When a new schedule is generated
invalidateQueries({ queryKey: ['schedule'] })
invalidateQueries({ queryKey: ['validation'] })
invalidateQueries({ queryKey: ['assignments'] })
```

#### Assignment CRUD

```typescript
// When an assignment is created, updated, or deleted
invalidateQueries({ queryKey: ['assignments'] })
invalidateQueries({ queryKey: ['schedule'] })
invalidateQueries({ queryKey: ['validation'] })
```

#### Absence CRUD

```typescript
// When an absence is created, updated, or deleted
invalidateQueries({ queryKey: ['absences'] })
invalidateQueries({ queryKey: ['schedule'] })  // Availability changed
```

#### Person CRUD

```typescript
// When a person is created, updated, or deleted
invalidateQueries({ queryKey: ['people'] })
invalidateQueries({ queryKey: ['residents'] })
invalidateQueries({ queryKey: ['faculty'] })
// Note: Don't invalidate schedule - existing assignments remain valid
```

#### Rotation Template CRUD

```typescript
// When a template is created, updated, or deleted
invalidateQueries({ queryKey: ['rotation-templates'] })
// Note: Don't invalidate schedule - existing assignments reference by ID
```

### Cross-Entity Invalidation Matrix

| Mutation On | Invalidate |
|-------------|------------|
| Schedule (generate) | schedule, validation, assignments |
| Assignment (C/U/D) | assignments, schedule, validation |
| Absence (C/U/D) | absences, schedule |
| Person (C/U/D) | people, residents, faculty |
| Template (C/U/D) | rotation-templates |
| Emergency Coverage | schedule, assignments, absences, validation |

---

## Optimistic Updates

For better UX, certain mutations should update the cache immediately before the server responds.

### Recommended for Optimistic Updates

1. **Assignment Updates** - Immediate visual feedback when editing
2. **Absence Creation** - Show absence immediately in calendar
3. **Person Updates** - Name/email changes should appear instantly

### Implementation Pattern

```typescript
export function useUpdateAssignmentOptimistic() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }) => put(`/assignments/${id}`, data),

    // Optimistically update before mutation completes
    onMutate: async ({ id, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['assignments'] })

      // Snapshot previous value
      const previousAssignments = queryClient.getQueryData(['assignments'])

      // Optimistically update
      queryClient.setQueryData(['assignments'], (old) => ({
        ...old,
        items: old.items.map(a =>
          a.id === id ? { ...a, ...data } : a
        )
      }))

      return { previousAssignments }
    },

    // Rollback on error
    onError: (err, variables, context) => {
      queryClient.setQueryData(['assignments'], context.previousAssignments)
    },

    // Always refetch after mutation settles
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
    },
  })
}
```

### NOT Recommended for Optimistic Updates

1. **Schedule Generation** - Complex server-side logic, can't predict result
2. **Validation** - Computed on server, impossible to replicate client-side
3. **Delete Operations** - Risky; prefer showing loading state

---

## Background Refetching

### Automatic Refetching Strategy

```typescript
// Global defaults in QueryClient
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,        // 1 minute default
      gcTime: 10 * 60 * 1000,      // 10 minute garbage collection
      retry: 3,                     // Retry failed requests
      retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30000),
      refetchOnWindowFocus: true,   // Refetch when tab focused
      refetchOnReconnect: true,     // Refetch after network recovery
    },
  },
})
```

### Polling for Real-Time Data

Only the schedule view should poll, and only when actively being viewed:

```typescript
export function useScheduleWithPolling(startDate, endDate) {
  const [isPollingEnabled, setIsPollingEnabled] = useState(true)

  return useQuery({
    queryKey: ['schedule', startDate, endDate],
    queryFn: () => get(`/schedule/${startDate}/${endDate}`),
    refetchInterval: isPollingEnabled ? 5 * 60 * 1000 : false,
    refetchIntervalInBackground: false, // Don't poll when tab is hidden
  })
}
```

---

## Implementation Patterns

### Query Key Best Practices

Use structured query keys for granular cache control:

```typescript
export const queryKeys = {
  // List queries with filters
  schedule: (startDate: string, endDate: string) =>
    ['schedule', startDate, endDate] as const,

  people: (filters?: PeopleFilters) =>
    ['people', filters] as const,

  // Single entity queries
  person: (id: string) =>
    ['people', 'detail', id] as const,

  // Nested/related queries
  personAbsences: (personId: string) =>
    ['people', personId, 'absences'] as const,
}
```

### Prefetching Strategy

Prefetch data the user is likely to need:

```typescript
// When hovering over a person in the schedule
function PersonCell({ personId }) {
  const queryClient = useQueryClient()

  const handleMouseEnter = () => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.person(personId),
      queryFn: () => get(`/people/${personId}`),
      staleTime: 5 * 60 * 1000,
    })
  }

  return <div onMouseEnter={handleMouseEnter}>...</div>
}
```

### Dependent Queries

For queries that depend on other data:

```typescript
function useScheduleWithValidation(startDate, endDate) {
  // Primary query
  const scheduleQuery = useSchedule(startDate, endDate)

  // Dependent query - only runs after schedule loads
  const validationQuery = useValidateSchedule(startDate, endDate, {
    enabled: scheduleQuery.isSuccess,
  })

  return { scheduleQuery, validationQuery }
}
```

---

## Error Handling in Cache

### Stale-While-Revalidate Pattern

React Query implements SWR by default:
- Show cached data immediately
- Refetch in background if stale
- Update UI when new data arrives

### Error Recovery

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors (client errors)
        if (error.status >= 400 && error.status < 500) {
          return false
        }
        // Retry up to 3 times for server errors
        return failureCount < 3
      },
    },
  },
})
```

---

## Performance Considerations

### Avoiding Over-Invalidation

Don't invalidate queries unnecessarily:

```typescript
// BAD: Invalidates everything
onSuccess: () => {
  queryClient.invalidateQueries()
}

// GOOD: Targeted invalidation
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: ['assignments'] })
}
```

### Selective Refetching

Use `refetchType` to control which queries actually refetch:

```typescript
// Only refetch active queries (visible on screen)
queryClient.invalidateQueries({
  queryKey: ['schedule'],
  refetchType: 'active',
})
```

---

## Monitoring and Debugging

### React Query Devtools

Enable in development:

```typescript
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
```

### Cache State Logging

```typescript
// Log cache state on mutation
onSuccess: () => {
  if (process.env.NODE_ENV === 'development') {
    console.log('Cache state:', queryClient.getQueryCache().getAll())
  }
}
```

---

*End of Caching Strategy Document*
