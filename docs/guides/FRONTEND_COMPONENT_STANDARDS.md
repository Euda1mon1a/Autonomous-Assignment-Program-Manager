# Frontend Component Standards & Patterns Guide

**Created:** 2025-12-31
**Source:** SESSION_2_FRONTEND Component Architecture Analysis
**Status:** Complete Reference
**Target:** All frontend component development

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Top 5 Components Needing Pattern Updates](#top-5-components-needing-pattern-updates)
3. [Standardized Component Template](#standardized-component-template)
4. [Component Composition Best Practices](#component-composition-best-practices)
5. [Component Testing Checklist](#component-testing-checklist)
6. [Atomic Design Structure](#atomic-design-structure)
7. [Component Communication Patterns](#component-communication-patterns)

---

## Executive Summary

The Residency Scheduler frontend has **209 TSX files** with strong TypeScript compliance but shows **inconsistent memoization practices** and **over-componentization** in certain areas. Currently only **1 component uses React.memo()**, and error boundary coverage is limited to root level.

### Key Metrics
- **22,129 LOC** in `/components/` directory
- **85 exported interfaces/types** - good but unorganized
- **30 barrel (index) files** for modular exports
- **42 useEffect hooks** - investigate for over-fetching
- **Only 1 memoized component** - significant optimization opportunity

---

## Top 5 Components Needing Pattern Updates

### 1. ConflictDashboard (Prop Drilling & Memoization)

**File:** `src/features/conflicts/ConflictDashboard.tsx`

**Issues:**
- Deep prop drilling: 6+ props passed to child lists
- 4 useState + 2 useQuery - over-complex local state
- ConflictCard rendered 100+ times without memoization
- No error boundaries at feature level

**Updates Needed:**
```typescript
// BEFORE: Prop drilling
<ConflictList
  conflicts={conflictsData?.items}
  statistics={statistics}
  onSelect={handleConflictSelect}
  onBatchSelect={setBatchConflicts}
/>

// AFTER: Context-based approach
const ConflictContext = createContext<ConflictContextType>(null!);
<ConflictProvider>
  <ConflictList />
</ConflictProvider>

// Child can now use
const { statistics, conflicts, onSelect } = useConflictContext();
```

**Memoization Fix:**
```typescript
// Add React.memo() wrapper
export const ConflictCard = memo(function ConflictCard({
  conflict,
  onSelect,
  isSelected,
}: ConflictCardProps) {
  return (
    <div
      onClick={() => onSelect(conflict)}
      className={isSelected ? 'border-blue-500' : 'border-gray-200'}
    >
      {conflict.title}
    </div>
  );
});
```

---

### 2. ScheduleCalendar (Complex State Management)

**File:** `src/components/schedule/ScheduleCalendar.tsx`

**Issues:**
- 421 lines in single file
- Good use of useMemo (2 instances) but not on rendered components
- No memoization of DayCell, PersonRow subcomponents
- Inline object literals in render

**Updates Needed:**
```typescript
// Extract as memoized component
export const DayCell = memo(function DayCell({
  day,
  people,
  schedule
}: DayCellProps) {
  return (
    <div className="grid grid-cols-${people.length}">
      {/* Render assignments */}
    </div>
  );
});

// Use in parent
const days = useMemo(
  () => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)),
  [weekStart]
);

return (
  <div>
    {days.map(day => (
      <DayCell
        key={day.toISOString()}
        day={day}
        people={people}
        schedule={schedule}
      />
    ))}
  </div>
);
```

---

### 3. EditAssignmentModal (Modal Anti-Patterns)

**File:** `src/components/EditAssignmentModal.tsx`

**Issues:**
- Callback chains: `onSuccess?.() → onError?.()` unclear responsibility
- No focus management (focus not returned after close)
- No focus trap inside modal
- Deep prop drilling

**Updates Needed:**
```typescript
// BEFORE: Unclear callback pattern
interface EditAssignmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  assignment: Assignment | null;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

// AFTER: Single callback with result union type
interface EditAssignmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  assignment: Assignment | null;
  onResult: (result: {
    success: boolean;
    data?: Assignment;
    error?: string
  }) => void;
  triggerRef?: RefObject<HTMLElement>;  // For focus restoration
}

// Implementation
const handleSuccess = async () => {
  // 1. Restore focus to trigger element
  triggerRef?.current?.focus();
  // 2. Notify parent with result
  onResult({ success: true, data: updatedAssignment });
  // 3. Close modal
  onClose();
};

const handleError = (error: Error) => {
  onResult({ success: false, error: error.message });
};
```

---

### 4. SwapMarketplace (State Complexity)

**File:** `src/features/swap-marketplace/SwapMarketplace.tsx`

**Issues:**
- 3 useState + 2 useMutation in single component
- No query filter persistence (resets on refresh)
- No optimistic updates
- SwapRequestCard needs memoization

**Updates Needed:**
```typescript
// Extract hook for state management
export function useSwapMarketplaceState() {
  const [filters, setFilters] = useState<SwapFilters>({});
  const [selectedSwap, setSelectedSwap] = useState<SwapRequest | null>(null);
  const [showForm, setShowForm] = useState(false);

  // Persist filters to URL/localStorage
  useEffect(() => {
    localStorage.setItem('swap-filters', JSON.stringify(filters));
  }, [filters]);

  return {
    filters,
    setFilters,
    selectedSwap,
    setSelectedSwap,
    showForm,
    setShowForm,
  };
}

// Memoize card component
export const SwapRequestCard = memo(function SwapRequestCard({
  swap,
  isSelected,
  onSelect,
}: SwapRequestCardProps) {
  return (
    <Card
      onClick={() => onSelect(swap)}
      className={isSelected ? 'ring-2 ring-blue-500' : ''}
    >
      {swap.title}
    </Card>
  );
});
```

---

### 5. LoadingStates (Over-Component)

**File:** `src/components/LoadingStates.tsx` - 495 lines

**Issue:**
- 495 lines in single "skeleton" component
- Should be split into multiple atomic skeletons
- No reusable pattern

**Updates Needed:**
```typescript
// BEFORE: Monolithic file
// - CalendarSkeleton
// - CardSkeleton
// - PersonCardSkeleton
// - ComplianceCardSkeleton
// - TableRowSkeleton
// All in one file

// AFTER: Atomic components
// skeletons/CalendarSkeleton.tsx
export const CalendarSkeleton = memo(function CalendarSkeleton() {
  return <div className="space-y-4 animate-pulse">...</div>;
});

// skeletons/CardSkeleton.tsx
export const CardSkeleton = memo(function CardSkeleton() {
  return <div className="rounded-lg bg-gray-200 h-64 animate-pulse" />;
});

// skeletons/index.ts
export { CalendarSkeleton } from './CalendarSkeleton';
export { CardSkeleton } from './CardSkeleton';
// etc.
```

---

## Standardized Component Template

### Minimal Component (Atom)

```typescript
/**
 * Button - Clickable action element
 *
 * Supports loading state, disabled state, and multiple variants.
 * Properly typed with TypeScript strict mode.
 */

import { memo, forwardRef, ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual variant of button */
  variant?: 'primary' | 'secondary' | 'danger';

  /** Button size */
  size?: 'sm' | 'md' | 'lg';

  /** Show loading indicator */
  isLoading?: boolean;

  /** Disable button interaction */
  isDisabled?: boolean;
}

/**
 * Reusable button component with multiple style variants.
 * Uses forwardRef for DOM access and memo for performance.
 */
export const Button = memo(
  forwardRef<HTMLButtonElement, ButtonProps>(
    (
      {
        variant = 'primary',
        size = 'md',
        isLoading = false,
        isDisabled = false,
        children,
        className = '',
        ...props
      },
      ref
    ) => {
      const baseStyles = 'font-medium rounded-lg focus:outline-none focus:ring-2 transition-colors';

      const variantStyles: Record<string, string> = {
        primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
        secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-400',
        danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
      };

      const sizeStyles: Record<string, string> = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-4 py-2 text-base',
        lg: 'px-6 py-3 text-lg',
      };

      return (
        <button
          ref={ref}
          disabled={isDisabled || isLoading}
          className={`
            ${baseStyles}
            ${variantStyles[variant]}
            ${sizeStyles[size]}
            ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            ${className}
          `}
          aria-busy={isLoading}
          {...props}
        >
          {isLoading ? <span className="inline-block animate-spin">⟳</span> : children}
        </button>
      );
    }
  )
);

Button.displayName = 'Button';
```

### Complex Feature Component

```typescript
/**
 * ConflictDashboard - Feature component for conflict resolution
 *
 * Manages conflict data, selection state, and resolution workflows.
 * Uses context to avoid prop drilling and enables feature-level error boundary.
 */

import { memo, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ConflictContext } from './ConflictContext';
import { useConflictData } from './hooks';
import { ErrorBoundary } from '@/components/ErrorBoundary';

interface ConflictDashboardProps {
  initialFilters?: ConflictFilters;
}

/**
 * Container component that manages all conflict resolution UI
 */
export const ConflictDashboard = memo(function ConflictDashboard({
  initialFilters = {},
}: ConflictDashboardProps) {
  // ============================================
  // State Management
  // ============================================

  const [activeView, setActiveView] = useLocalStorage<ViewType>(
    'conflict-view',
    'list'
  );
  const [filters, setFilters] = useLocalStorage('conflict-filters', initialFilters);
  const [selectedConflict, setSelectedConflict] = useState<Conflict | null>(null);
  const [batchConflicts, setBatchConflicts] = useState<Conflict[]>([]);

  // ============================================
  // Data Fetching
  // ============================================

  const { data: conflictsData, refetch: refetchConflicts } = useConflictData(filters);
  const { data: statistics } = useConflictStatistics();

  // ============================================
  // Computed Values
  // ============================================

  const filteredConflicts = useMemo(
    () => conflictsData?.items ?? [],
    [conflictsData?.items]
  );

  // ============================================
  // Event Handlers
  // ============================================

  const handleConflictSelect = useCallback((conflict: Conflict) => {
    setSelectedConflict(conflict);
    setActiveView('suggestions');
  }, []);

  const handleTabChange = useCallback((newTab: ViewType) => {
    setActiveView(newTab);
  }, []);

  const handleFilterChange = useCallback((newFilters: ConflictFilters) => {
    setFilters(newFilters);
    setSelectedConflict(null);  // Clear selection on filter change
  }, [setFilters]);

  // ============================================
  // Context Value
  // ============================================

  const contextValue = useMemo(
    () => ({
      conflicts: filteredConflicts,
      statistics,
      selectedConflict,
      filters,
      activeView,
      onSelectConflict: handleConflictSelect,
      onChangeTab: handleTabChange,
      onChangeFilters: handleFilterChange,
      onRefresh: refetchConflicts,
    }),
    [filteredConflicts, statistics, selectedConflict, filters, activeView, handleConflictSelect, handleTabChange, handleFilterChange, refetchConflicts]
  );

  // ============================================
  // Render
  // ============================================

  return (
    <ErrorBoundary fallback={<ConflictErrorState onRetry={refetchConflicts} />}>
      <ConflictContext.Provider value={contextValue}>
        <div className="space-y-6">
          <ConflictHeader />
          <ConflictFilters />
          <ConflictTabs />
        </div>
      </ConflictContext.Provider>
    </ErrorBoundary>
  );
});
```

---

## Component Composition Best Practices

### 1. Server vs Client Component Strategy

```typescript
// ============================================
// LAYOUT (Server Component) ✓
// ============================================

// src/app/layout.tsx
export const metadata: Metadata = {
  title: 'Residency Scheduler',
  description: 'Medical residency scheduling',
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode
}) {
  return (
    <html>
      <head>{/* Metadata */}</head>
      <body>
        <Providers>           {/* Client boundary here */}
          <Navigation />      {/* Implicitly client */}
          <main>{children}</main>
        </Providers>
      </body>
    </html>
  );
}

// ============================================
// PAGE ROUTES (Should be Minimal Client) ⚠️
// ============================================

// CURRENT: 'use client' at page level - all children forced to client
'use client';
export default function SchedulePage() {
  // Everything is client-rendered
}

// RECOMMENDED: Minimal 'use client' boundary
export default function SchedulePage() {
  // This stays server component, fetches data at build time
  const schedule = await getSchedule();

  return (
    <ScheduleClient initialSchedule={schedule} />
  );
}

// Only the interactive part is client
'use client';
function ScheduleClient({ initialSchedule }) {
  // Interactive logic here
}
```

### 2. Component Hierarchy Pattern

```
Page (Server)
├── PageLayout (Client boundary)
│   ├── Header (Memoized Atom)
│   ├── Sidebar (Memoized Molecule)
│   └── Content Area (Provider)
│       └── FeatureContainer
│           ├── ErrorBoundary ✓ Feature-level
│           ├── FeatureContext.Provider
│           │   ├── Toolbar
│           │   ├── List (Virtualized)
│           │   │   └── Card[] (Memoized)
│           │   └── DetailPanel
│           └── Modal
│               └── Form
```

### 3. Memoization Guidelines

**Always Memoize:**
- ✓ Components rendered in lists (100+ items)
- ✓ Components with expensive computations
- ✓ Form primitives (Input, Button, Select)
- ✓ Cards that don't need frequent updates

**Don't Memoize:**
- ✗ Page-level components (rendered once)
- ✗ Simple presentational components
- ✗ Components that always have different props

**Example:**
```typescript
// ✓ DO MEMOIZE - rendered in list
export const AssignmentCard = memo(function AssignmentCard({
  assignment,
  onSelect,
}: AssignmentCardProps) {
  return <div onClick={() => onSelect(assignment)} />;
});

// ✗ DON'T MEMOIZE - page wrapper
export default function SchedulePage() {
  return <div>Schedule</div>;
}
```

---

## Component Testing Checklist

### Before Committing Component

```checklist
[ ] TypeScript
  [ ] No 'any' types used
  [ ] All props typed with interfaces
  [ ] Return types explicit
  [ ] Strict mode enabled

[ ] Memoization
  [ ] List items wrapped in memo()
  [ ] Callbacks wrapped in useCallback()
  [ ] Expensive computations use useMemo()
  [ ] No inline objects/arrays in props

[ ] Accessibility
  [ ] aria-labels on icon-only buttons
  [ ] aria-describedby for error messages
  [ ] Semantic HTML elements (button not div)
  [ ] Keyboard navigation support

[ ] Testing
  [ ] Component test file created
  [ ] Rendering test exists
  [ ] Event handlers tested
  [ ] Error state tested
  [ ] Loading state tested
  [ ] Accessibility assertions included

[ ] Error Handling
  [ ] Try/catch around async operations
  [ ] User-friendly error messages (no stack traces)
  [ ] Fallback UI for error state
  [ ] Error boundaries at feature level

[ ] Performance
  [ ] No N+1 query issues
  [ ] No memory leaks (cleanup in useEffect)
  [ ] Props drilling minimized
  [ ] Context used instead of prop chains

[ ] Documentation
  [ ] JSDoc comments on component
  [ ] Props interface documented
  [ ] Usage example in comments
  [ ] displayName set if using memo()
```

### Component Test Template

```typescript
describe('YourComponent', () => {
  // ============================================
  // Setup
  // ============================================

  const mockProps = {
    title: 'Test Title',
    onSubmit: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ============================================
  // Rendering
  // ============================================

  describe('Rendering', () => {
    it('should render with provided props', () => {
      render(<YourComponent {...mockProps} />);
      expect(screen.getByText('Test Title')).toBeInTheDocument();
    });

    it('should render loading skeleton when data is loading', () => {
      render(<YourComponent isLoading {...mockProps} />);
      expect(screen.getByTestId('skeleton')).toBeInTheDocument();
    });
  });

  // ============================================
  // Interactions
  // ============================================

  describe('Interactions', () => {
    it('should call onSubmit when form submitted', async () => {
      const user = userEvent.setup();
      render(<YourComponent {...mockProps} />);

      const button = screen.getByRole('button', { name: /submit/i });
      await user.click(button);

      expect(mockProps.onSubmit).toHaveBeenCalled();
    });
  });

  // ============================================
  // States
  // ============================================

  describe('States', () => {
    it('should show error message on error state', () => {
      render(<YourComponent error="Something went wrong" {...mockProps} />);
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    });

    it('should disable button when disabled prop is true', () => {
      render(<YourComponent isDisabled {...mockProps} />);
      expect(screen.getByRole('button')).toBeDisabled();
    });
  });

  // ============================================
  // Accessibility
  // ============================================

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<YourComponent {...mockProps} />);
      expect(screen.getByRole('button')).toHaveAttribute('aria-label');
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      render(<YourComponent {...mockProps} />);

      const button = screen.getByRole('button');
      await user.tab();

      expect(button).toHaveFocus();
    });
  });
});
```

---

## Atomic Design Structure

**Recommended Directory Layout:**

```
components/
├── atoms/
│   ├── Button.tsx
│   ├── Badge.tsx
│   ├── Icon.tsx
│   ├── Label.tsx
│   └── index.ts
│
├── molecules/
│   ├── Card.tsx
│   ├── Modal.tsx
│   ├── Toast.tsx
│   ├── FormGroup.tsx
│   ├── SearchInput.tsx
│   └── index.ts
│
├── organisms/
│   ├── ScheduleCalendar.tsx
│   ├── PersonForm.tsx
│   ├── ConflictResolutionPanel.tsx
│   └── index.ts
│
├── templates/
│   ├── DashboardLayout.tsx
│   ├── AdminLayout.tsx
│   ├── AuthLayout.tsx
│   └── index.ts
│
└── common/
    ├── ErrorBoundary.tsx
    ├── Navigation.tsx
    └── index.ts
```

---

## Component Communication Patterns

### Pattern 1: Context for Shared State (Replace Prop Drilling)

```typescript
// ✓ Use when: 3+ levels of prop drilling, shared across many components

interface ConflictContextType {
  conflicts: Conflict[];
  selectedConflict: Conflict | null;
  filters: ConflictFilters;
  onSelectConflict: (c: Conflict) => void;
}

const ConflictContext = createContext<ConflictContextType | null>(null);

export function ConflictProvider({ children }: { children: React.ReactNode }) {
  const [selectedConflict, setSelectedConflict] = useState<Conflict | null>(null);
  const [filters, setFilters] = useState<ConflictFilters>({});
  const { data: conflicts } = useConflicts(filters);

  return (
    <ConflictContext.Provider value={{
      conflicts: conflicts ?? [],
      selectedConflict,
      filters,
      onSelectConflict: setSelectedConflict,
    }}>
      {children}
    </ConflictContext.Provider>
  );
}

export function useConflictContext() {
  const ctx = useContext(ConflictContext);
  if (!ctx) throw new Error('useConflictContext must be used inside ConflictProvider');
  return ctx;
}
```

### Pattern 2: Callback Props for Parent Communication

```typescript
// ✓ Use when: Simple one-way communication, parent controls behavior

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  onError?: (error: string) => void;
}

export function EditModal({
  isOpen,
  onClose,
  onSuccess,
  onError
}: ModalProps) {
  const handleSubmit = async (data: FormData) => {
    try {
      await updateAssignment(data);
      onSuccess(); // Parent handles what's next
    } catch (error) {
      onError?.(error.message);
    }
  };

  return <Modal isOpen={isOpen} onClose={onClose} onSubmit={handleSubmit} />;
}
```

### Pattern 3: Render Props for Maximum Flexibility

```typescript
// ✓ Use when: Consumer needs control over rendering

interface ListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  renderEmpty?: () => React.ReactNode;
}

export function List<T>({
  items,
  renderItem,
  renderEmpty
}: ListProps<T>) {
  if (items.length === 0) {
    return renderEmpty?.() ?? <div>No items</div>;
  }

  return (
    <div>
      {items.map((item, i) => (
        <div key={i}>{renderItem(item, i)}</div>
      ))}
    </div>
  );
}

// Usage
<List
  items={assignments}
  renderItem={(assignment) => (
    <AssignmentCard key={assignment.id} assignment={assignment} />
  )}
/>
```

---

## Summary of Standards

| Aspect | Standard | Reasoning |
|--------|----------|-----------|
| **Max Lines per Component** | 300-400 | Easier to reason about, test, review |
| **Max Props per Component** | 6-8 | Signal to use Context or custom hooks |
| **State Complexity** | 3-4 useState | Extract to custom hook if more |
| **Error Boundaries** | Feature-level minimum | Prevent entire app crash |
| **Memoization** | List items, atoms | Balance performance vs complexity |
| **Tests per Component** | Rendering + Interactions + States + A11y | Minimum for production |
| **Accessibility** | WCAG AA minimum | Medical data requires care |
| **TypeScript** | Strict mode always | Catches bugs at compile time |

---

**Document Version:** 1.0
**Last Updated:** 2025-12-31
**Next Review:** 2026-03-31
