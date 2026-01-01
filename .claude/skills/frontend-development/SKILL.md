---
name: frontend-development
description: Modern frontend development with Next.js 14, React 18, TailwindCSS, and TanStack Query. Use when building UI components, implementing pages, optimizing performance, or following Next.js App Router patterns.
model_tier: sonnet
parallel_hints:
  can_parallel_with: [react-typescript, test-writer, code-review]
  must_serialize_with: []
  preferred_batch_size: 5
context_hints:
  max_file_context: 60
  compression_level: 1
  requires_git_context: true
  requires_db_context: false
escalation_triggers:
  - pattern: "authentication|auth|session"
    reason: "Authentication UI requires security-audit review"
  - pattern: "third-party|external"
    reason: "Third-party integrations need human evaluation"
  - keyword: ["SEO", "metadata", "design system"]
    reason: "Architectural decisions require human input"
---

# Frontend Development Skill

Comprehensive frontend development expertise for Next.js applications with React, TailwindCSS, and modern data fetching patterns.

## When This Skill Activates

- Building new React components or pages
- Implementing Next.js App Router patterns
- Styling with TailwindCSS
- Data fetching with TanStack Query
- Performance optimization
- Responsive design implementation
- Component architecture decisions

## Project Context

```
frontend/
├── src/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # Reusable UI components
│   │   ├── common/       # Shared components (Modal, Button, etc.)
│   │   ├── dashboard/    # Dashboard-specific components
│   │   └── admin/        # Admin panel components
│   ├── features/         # Feature-based modules
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utilities and API client
│   ├── types/            # TypeScript type definitions
│   └── styles/           # Global styles
├── public/               # Static assets
└── __tests__/            # Test files
```

## Next.js 14 App Router Patterns

### Page Structure

```typescript
// src/app/schedules/page.tsx
import { Suspense } from 'react';
import { ScheduleList } from '@/components/ScheduleList';
import { ScheduleListSkeleton } from '@/components/skeletons';

export const metadata = {
  title: 'Schedules | Residency Scheduler',
  description: 'View and manage residency schedules',
};

export default function SchedulesPage() {
  return (
    <main className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Schedules</h1>
      <Suspense fallback={<ScheduleListSkeleton />}>
        <ScheduleList />
      </Suspense>
    </main>
  );
}
```

### Layout Pattern

```typescript
// src/app/admin/layout.tsx
import { AdminSidebar } from '@/components/admin/AdminSidebar';
import { AdminHeader } from '@/components/admin/AdminHeader';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  return (
    <div className="flex h-screen bg-gray-100">
      <AdminSidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminHeader />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
```

### Loading States

```typescript
// src/app/schedules/loading.tsx
export default function Loading() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-gray-200 rounded w-1/4" />
      <div className="h-64 bg-gray-200 rounded" />
    </div>
  );
}
```

### Error Handling

```typescript
// src/app/schedules/error.tsx
'use client';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px]">
      <h2 className="text-xl font-semibold text-red-600 mb-4">
        Something went wrong
      </h2>
      <p className="text-gray-600 mb-4">{error.message}</p>
      <button
        onClick={reset}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Try again
      </button>
    </div>
  );
}
```

## Component Patterns

### Base Component Structure

```typescript
// src/components/common/Card.tsx
import { cn } from '@/lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'outlined' | 'elevated';
}

export function Card({
  children,
  className,
  variant = 'default'
}: CardProps) {
  return (
    <div
      className={cn(
        'rounded-lg p-4',
        {
          'bg-white shadow-sm': variant === 'default',
          'border border-gray-200': variant === 'outlined',
          'bg-white shadow-lg': variant === 'elevated',
        },
        className
      )}
    >
      {children}
    </div>
  );
}
```

### Compound Components

```typescript
// src/components/common/DataTable.tsx
interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  onRowClick?: (row: T) => void;
}

interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

export function DataTable<T extends { id: string }>({
  data,
  columns,
  onRowClick,
}: DataTableProps<T>) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row) => (
            <tr
              key={row.id}
              onClick={() => onRowClick?.(row)}
              className={cn(
                onRowClick && 'cursor-pointer hover:bg-gray-50'
              )}
            >
              {columns.map((col) => (
                <td
                  key={String(col.key)}
                  className={cn('px-6 py-4 whitespace-nowrap', col.className)}
                >
                  {col.render
                    ? col.render(row)
                    : String(row[col.key as keyof T] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Modal Component

```typescript
// src/components/common/Modal.tsx
'use client';

import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
}: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
  };

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => e.target === overlayRef.current && onClose()}
    >
      <div
        className={cn(
          'bg-white rounded-lg shadow-xl w-full mx-4',
          sizeClasses[size]
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <div className="flex items-center justify-between p-4 border-b">
          <h2 id="modal-title" className="text-lg font-semibold">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
            aria-label="Close modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}
```

## TailwindCSS Patterns

### Utility Class Organization

```typescript
// Order: layout → sizing → spacing → typography → colors → effects → states
<div
  className={cn(
    // Layout
    'flex flex-col items-center justify-center',
    // Sizing
    'w-full max-w-md h-screen',
    // Spacing
    'p-6 gap-4',
    // Typography
    'text-lg font-medium',
    // Colors
    'bg-white text-gray-900',
    // Effects
    'shadow-lg rounded-lg',
    // States
    'hover:shadow-xl transition-shadow'
  )}
/>
```

### Responsive Design

```typescript
// Mobile-first approach
<div className="
  grid
  grid-cols-1
  sm:grid-cols-2
  lg:grid-cols-3
  xl:grid-cols-4
  gap-4
">
  {items.map(item => <Card key={item.id} {...item} />)}
</div>

// Responsive text
<h1 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-bold">
  Schedule Dashboard
</h1>

// Responsive spacing
<section className="py-8 md:py-12 lg:py-16 px-4 md:px-6 lg:px-8">
  {/* content */}
</section>
```

### Dark Mode Support

```typescript
// Tailwind dark mode classes
<div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  <h2 className="text-gray-800 dark:text-gray-200">Title</h2>
  <p className="text-gray-600 dark:text-gray-400">Description</p>
</div>
```

### Common Utility Patterns

```typescript
// Status badges
const statusColors = {
  active: 'bg-green-100 text-green-800',
  pending: 'bg-yellow-100 text-yellow-800',
  inactive: 'bg-gray-100 text-gray-800',
  error: 'bg-red-100 text-red-800',
} as const;

<span className={cn(
  'px-2 py-1 text-xs font-medium rounded-full',
  statusColors[status]
)}>
  {status}
</span>

// Truncate text
<p className="truncate max-w-xs" title={fullText}>
  {fullText}
</p>

// Line clamp
<p className="line-clamp-3">{description}</p>
```

## Data Fetching with TanStack Query

### Query Hook Pattern

```typescript
// src/hooks/useSchedules.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Schedule, ScheduleCreate } from '@/types';

export const scheduleKeys = {
  all: ['schedules'] as const,
  lists: () => [...scheduleKeys.all, 'list'] as const,
  list: (filters: string) => [...scheduleKeys.lists(), { filters }] as const,
  details: () => [...scheduleKeys.all, 'detail'] as const,
  detail: (id: string) => [...scheduleKeys.details(), id] as const,
};

export function useSchedules(filters?: ScheduleFilters) {
  return useQuery({
    queryKey: scheduleKeys.list(JSON.stringify(filters)),
    queryFn: () => api.schedules.list(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useSchedule(id: string) {
  return useQuery({
    queryKey: scheduleKeys.detail(id),
    queryFn: () => api.schedules.get(id),
    enabled: !!id,
  });
}

export function useCreateSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ScheduleCreate) => api.schedules.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scheduleKeys.lists() });
    },
  });
}
```

### Optimistic Updates

```typescript
export function useUpdateSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Schedule> }) =>
      api.schedules.update(id, data),
    onMutate: async ({ id, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: scheduleKeys.detail(id) });

      // Snapshot previous value
      const previous = queryClient.getQueryData(scheduleKeys.detail(id));

      // Optimistically update
      queryClient.setQueryData(scheduleKeys.detail(id), (old: Schedule) => ({
        ...old,
        ...data,
      }));

      return { previous };
    },
    onError: (err, { id }, context) => {
      // Rollback on error
      queryClient.setQueryData(scheduleKeys.detail(id), context?.previous);
    },
    onSettled: (data, error, { id }) => {
      // Refetch after mutation
      queryClient.invalidateQueries({ queryKey: scheduleKeys.detail(id) });
    },
  });
}
```

## Form Patterns

### Controlled Form

```typescript
'use client';

import { useState } from 'react';
import type { ScheduleCreate } from '@/types';

interface ScheduleFormProps {
  onSubmit: (data: ScheduleCreate) => void;
  isLoading?: boolean;
}

export function ScheduleForm({ onSubmit, isLoading }: ScheduleFormProps) {
  const [formData, setFormData] = useState<ScheduleCreate>({
    name: '',
    startDate: '',
    endDate: '',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof ScheduleCreate, string>>>({});

  const validate = (): boolean => {
    const newErrors: typeof errors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    if (!formData.startDate) {
      newErrors.startDate = 'Start date is required';
    }
    if (!formData.endDate) {
      newErrors.endDate = 'End date is required';
    }
    if (formData.startDate && formData.endDate && formData.startDate > formData.endDate) {
      newErrors.endDate = 'End date must be after start date';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(formData);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
          Name
        </label>
        <input
          type="text"
          id="name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className={cn(
            'mt-1 block w-full rounded-md shadow-sm',
            'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
            errors.name && 'border-red-500'
          )}
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600">{errors.name}</p>
        )}
      </div>

      {/* Additional fields... */}

      <button
        type="submit"
        disabled={isLoading}
        className={cn(
          'w-full py-2 px-4 rounded-md text-white',
          'bg-blue-600 hover:bg-blue-700',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
      >
        {isLoading ? 'Saving...' : 'Save Schedule'}
      </button>
    </form>
  );
}
```

## Performance Optimization

### Code Splitting

```typescript
// Dynamic imports for heavy components
import dynamic from 'next/dynamic';

const HeavyChart = dynamic(
  () => import('@/components/charts/HeavyChart'),
  {
    loading: () => <div className="h-64 bg-gray-100 animate-pulse rounded" />,
    ssr: false, // Disable SSR for client-only components
  }
);
```

### Memoization

```typescript
import { memo, useMemo, useCallback } from 'react';

// Memoize expensive components
export const ScheduleRow = memo(function ScheduleRow({
  schedule,
  onEdit,
}: ScheduleRowProps) {
  // Component logic
});

// Memoize expensive calculations
function ScheduleStats({ assignments }: { assignments: Assignment[] }) {
  const stats = useMemo(() => {
    return {
      total: assignments.length,
      completed: assignments.filter(a => a.status === 'completed').length,
      pending: assignments.filter(a => a.status === 'pending').length,
    };
  }, [assignments]);

  return <StatsDisplay stats={stats} />;
}

// Memoize callbacks passed to children
function ParentComponent() {
  const handleUpdate = useCallback((id: string, data: UpdateData) => {
    // Update logic
  }, [/* dependencies */]);

  return <ChildComponent onUpdate={handleUpdate} />;
}
```

## Accessibility Patterns

```typescript
// Proper button with loading state
<button
  type="submit"
  disabled={isLoading}
  aria-busy={isLoading}
  aria-describedby={error ? 'error-message' : undefined}
>
  {isLoading ? 'Loading...' : 'Submit'}
</button>

// Screen reader only text
<span className="sr-only">Close navigation menu</span>

// Focus management
import { useEffect, useRef } from 'react';

function Modal({ isOpen, onClose, children }) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) {
      closeButtonRef.current?.focus();
    }
  }, [isOpen]);

  return (/* ... */);
}

// ARIA labels for icons
<button aria-label="Delete schedule">
  <Trash className="h-5 w-5" aria-hidden="true" />
</button>
```

## Commands

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/frontend

# Development
npm run dev                    # Start dev server

# Build & Check
npm run build                  # Production build
npm run type-check             # TypeScript check
npm run lint                   # ESLint check
npm run lint:fix               # Auto-fix lint issues

# Testing
npm test                       # Run tests
npm run test:coverage          # With coverage
npm run test:e2e               # Playwright E2E
```

## Integration with Other Skills

### With react-typescript
For TypeScript-specific patterns, defer to react-typescript skill for:
- Generic component typing
- TanStack Query type inference
- Complex type definitions

### With test-writer
When creating components:
1. Build component with proper props interface
2. test-writer generates RTL tests
3. Verify accessibility with jest-axe

### With code-review
Frontend review checklist:
- Responsive design verified
- Loading/error states handled
- Accessibility attributes present
- Performance optimizations applied

## Escalation Rules

**Escalate to human when:**

1. Complex animation requirements
2. Third-party library integration issues
3. SEO/metadata optimization questions
4. Authentication flow UI decisions
5. Design system architecture changes
