# Frontend Component Patterns - Quick Reference

**Document:** `frontend-component-patterns.md` (1,553 lines)
**Analysis Date:** 2025-12-30
**Codebase Scope:** 209 TSX files, 22,129 LOC in components/

---

## Critical Findings

### 1. Server/Client Component Strategy (ANTI-PATTERN)
- **All 18 page routes are 'use client'** - aggressive client rendering
- **Should:** Convert static pages to server components to reduce JS bundle
- **Impact:** Heavy initial client-side load
- **Fix Complexity:** Medium (4-6 hours)

### 2. Memoization Gap (PERFORMANCE ISSUE)
- **Only 1 component uses memoization** (Input.tsx with forwardRef)
- **Risk areas:** ScheduleCalendar, ConflictCard, PersonCard (lists)
- **Impact:** Unnecessary re-renders of 100+ components
- **Fix Complexity:** Low (3 hours)

### 3. Error Boundary Coverage (RELIABILITY ISSUE)
- **Only 1 root ErrorBoundary** exists
- **Missing:** Feature-level boundaries (conflicts, swaps, etc.)
- **Risk:** Single feature crash crashes entire app
- **Fix Complexity:** Low (2-3 hours)

### 4. Prop Drilling (MAINTAINABILITY ISSUE)
- **ConflictDashboard → ConflictList → ConflictCard** shows prop threading
- **Risk:** Hard to refactor, props unclear at depth
- **Solution:** Extract to Context (SelectionContext)
- **Fix Complexity:** Low (2 hours)

---

## Performance Scorecard

| Metric | Score | Status |
|--------|-------|--------|
| Memoization | 2/10 | Critical |
| Bundle Size | 5/10 | Poor (400KB+ unminified) |
| Re-renders | 5/10 | Many unnecessary |
| Error Handling | 5/10 | Root only |
| TypeScript | 9/10 | Excellent |
| Form UX | 7/10 | Good |

---

## Component Inventory Summary

```
/components/           22,129 LOC
├── atoms/            Forms (Input, Select, TextArea, DatePicker)
├── molecules/        Modal, Toast, Cards, Buttons
├── organisms/        ScheduleCalendar, Feature components (NOT separated)
├── skeletons/        Loading placeholders
└── ... (misc)

/features/           ~12+ feature modules
├── conflicts/        Conflict resolution (280+ LOC)
├── swap-marketplace/ Swap management (300+ LOC)
├── my-dashboard/     User dashboard (200+ LOC)
├── holographic-hub/  3D visualization (tested!)
├── audit/            Audit logging
├── analytics/        Charts & metrics
└── ... (more)

/hooks/              19 custom hooks
├── useSchedule()    Schedule CRUD + queries
├── useSwaps()       Swap management
├── usePeople()      Person CRUD
├── useAuth()        Authentication
└── ... (more)

/contexts/           3 context providers
├── AuthContext      Auth state + login/logout
├── ToastContext     Toast notifications
└── ClaudeChatContext AI chat integration

/pages/              18 routes (ALL 'use client')
├── /schedule
├── /people
├── /conflicts
├── /swaps
├── /compliance
└── ... (more)
```

---

## Code Quality Metrics

| Aspect | Status | Evidence |
|--------|--------|----------|
| **TypeScript Strict Mode** | ENABLED ✓ | tsconfig.json: `"strict": true` |
| **Prop Types** | 85 interfaces exported | All major components typed |
| **Error Categorization** | 5 categories | ErrorBoundary.ts categorizes: Network, Auth, Validation, NotFound, Unknown |
| **Form Validation** | Centralized | Pydantic backend validation |
| **Data Fetching** | TanStack Query | useQuery + useMutation patterns |
| **State Management** | Context + Query | AuthContext, ToastContext, ClaudeChatContext |

---

## Top 5 Action Items

### 1. Add Feature-Level Error Boundaries (HIGH PRIORITY)
```typescript
// Wrap each feature
<ErrorBoundary>
  <ConflictDashboard />
</ErrorBoundary>
```
**Time:** 2 hours | **Impact:** Prevents cascading failures

### 2. Memoize High-Rerender Components (HIGH PRIORITY)
```typescript
export const ConflictCard = memo(function ConflictCard(props) {
  return <div>...</div>;
});
```
**Time:** 3 hours | **Impact:** 30-40% re-render reduction

### 3. Extract Selection State to Context (MEDIUM PRIORITY)
```typescript
const SelectionContext = createContext<SelectionContextValue>();
```
**Time:** 2 hours | **Impact:** Cleaner prop drilling

### 4. Convert Static Pages to Server Components (MEDIUM PRIORITY)
- schedule/page.tsx → can be static
- templates/page.tsx → can be static
- call-roster/page.tsx → can be static

**Time:** 4-6 hours | **Impact:** ~50KB bundle reduction

### 5. Add Component Virtualization (LOW PRIORITY)
- Use react-window for lists 100+ items
- Improves scroll performance
- ~3 hours implementation

---

## Component Type Distribution

```
Functional Components: ~205 (98%)
├─ with 'use client': ~116 (55%)
├─ with 'use server': 0
└─ Server (implicit): ~9 (4%)

Class Components: 1
└─ ErrorBoundary (class required for error handling)

Total TSX Files: 209
```

---

## Hook Usage Analysis

**Most Common Hooks (by frequency):**
1. useState() - 42 useEffect patterns found
2. useQuery() - TanStack Query integration
3. useMutation() - Form submissions, state updates
4. useMemo() - Data transformations
5. useCallback() - Event handlers
6. useContext() - Context consumption
7. useRef() - DOM access, refs
8. useId() - Unique IDs (form labels)

---

## TypeScript Compliance

**Status:** 95%+ Compliant with Strict Mode

**Violations Found:**
1. `useState<any>()` in holographic-hub (rare)
2. Type assertions (`as`) in rare cases
3. No optional chaining omitted - all proper

**Strengths:**
- Discriminated unions used properly
- Generic typing throughout
- Proper null coalescing
- Interface exports for all major props

---

## Key Files to Review

### Architecture
- `/frontend/src/app/layout.tsx` - Root layout
- `/frontend/src/app/providers.tsx` - Provider setup
- `/frontend/tsconfig.json` - TS configuration

### Component Examples
- `/frontend/src/components/ErrorBoundary.tsx` - Best practice error handling
- `/frontend/src/components/forms/Input.tsx` - Atomic component pattern
- `/frontend/src/features/conflicts/ConflictDashboard.tsx` - Feature module example
- `/frontend/src/contexts/AuthContext.tsx` - Context pattern

### Problematic Areas
- `/frontend/src/features/holographic-hub/` - Contains `any` types
- `/frontend/src/app/admin/game-theory/page.tsx` - Potentially experimental
- All pages (`use client`) - Should evaluate for server conversion

---

## Terminology Reference

- **use client:** Marks component for client-side rendering (Next.js 14)
- **Props drilling:** Passing props through multiple component layers
- **Memoization:** Caching render results to prevent re-computation
- **Error boundary:** Class component catching child render errors
- **TanStack Query:** Data fetching library (successor to React Query)
- **Context API:** Built-in React state management
- **Atomic design:** UI design system (atoms → molecules → organisms → templates → pages)

---

## Questions for Owner

1. **Why are all pages 'use client'?** Should evaluate static pages for server rendering
2. **Is holographic-hub in production?** Has `any` types, needs review
3. **Is voxel-schedule experimental?** Minimal test coverage
4. **Performance baseline?** Have metrics on bundle size, Core Web Vitals?
5. **Error reporting service?** ErrorBoundary ready for Sentry/LogRocket integration

---

**For Details:** See `frontend-component-patterns.md` (1,553 lines)
**Generated:** 2025-12-30 | **Analysis Method:** SEARCH_PARTY Reconnaissance
