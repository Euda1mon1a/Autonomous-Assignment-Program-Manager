# HAIKU 4.5 Task List

## Role: The Rapid Executor

You execute well-defined, repetitive tasks at high speed. Follow templates exactly. Do not make architectural decisions. Report completion or issues to Sonnet.

---

## Operating Rules

1. **Follow templates exactly** - No deviations unless pattern doesn't fit
2. **Ask if unclear** - Better to clarify than guess wrong
3. **Batch work** - Complete all items in a task before reporting
4. **Report anomalies** - Note anything that doesn't match expected pattern
5. **No architecture** - If a decision is needed, escalate to Sonnet

---

## Current Task Queue

### Task 1: Generate API Response Types
**Priority: P0** | **Status: READY** | **Assigned by: Sonnet**

**File to Create:** `frontend/types/api.ts`

**Template:**
```typescript
// Follow this exact pattern for each type

export interface Person {
  id: number;
  name: string;
  email: string;
  role: 'resident' | 'faculty';
  pgy_level: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PersonCreate {
  name: string;
  email: string;
  role: 'resident' | 'faculty';
  pgy_level?: number;
}

export interface PersonUpdate {
  name?: string;
  email?: string;
  role?: 'resident' | 'faculty';
  pgy_level?: number;
  is_active?: boolean;
}
```

**Types to Generate:**

| Entity | Response Type | Create Type | Update Type |
|--------|--------------|-------------|-------------|
| Person | ✓ (example above) | ✓ | ✓ |
| Block | BlockResponse | BlockCreate | BlockUpdate |
| Assignment | AssignmentResponse | AssignmentCreate | AssignmentUpdate |
| Absence | AbsenceResponse | AbsenceCreate | AbsenceUpdate |
| RotationTemplate | RotationTemplateResponse | RotationTemplateCreate | RotationTemplateUpdate |
| ScheduleRun | ScheduleRunResponse | N/A | N/A |
| ValidationResult | ValidationResultResponse | N/A | N/A |

**Reference Backend Models:**
- `backend/app/models/*.py` - Field names and types
- `backend/app/schemas/*.py` - If available, Pydantic schemas

**Constraints:**
- Use `string` for datetime fields (ISO format from API)
- Use union types for enums: `'value1' | 'value2'`
- Optional fields use `?` in Create/Update types
- Response types have all fields required

**Completion Checklist:**
- [ ] Person types (example provided)
- [ ] Block types
- [ ] Assignment types
- [ ] Absence types
- [ ] RotationTemplate types
- [ ] ScheduleRun types (response only)
- [ ] ValidationResult types (response only)
- [ ] Export all types

---

### Task 2: Create Modal Component
**Priority: P1** | **Status: READY** | **Assigned by: Sonnet**

**File to Create:** `frontend/components/Modal.tsx`

**Template:**
```typescript
'use client';

import { ReactNode, useEffect } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}

export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  // Close on escape key
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {children}
        </div>
      </div>
    </div>
  );
}
```

**Requirements:**
- Copy template exactly
- Ensure imports are correct
- Test that file has no syntax errors

**Completion Checklist:**
- [ ] File created at correct path
- [ ] All imports present
- [ ] No TypeScript errors

---

### Task 3: Create Form Input Components
**Priority: P1** | **Status: READY** | **Assigned by: Sonnet**

**Directory:** `frontend/components/forms/`

**Files to Create:**

#### a) `Input.tsx`
```typescript
import { InputHTMLAttributes, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    return (
      <div className="space-y-1">
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
        <input
          ref={ref}
          className={`
            w-full px-3 py-2 border rounded-md shadow-sm
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            ${error ? 'border-red-500' : 'border-gray-300'}
            ${className}
          `}
          {...props}
        />
        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
```

#### b) `Select.tsx`
```typescript
import { SelectHTMLAttributes, forwardRef } from 'react';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: SelectOption[];
  error?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, options, error, className = '', ...props }, ref) => {
    return (
      <div className="space-y-1">
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
        <select
          ref={ref}
          className={`
            w-full px-3 py-2 border rounded-md shadow-sm
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            ${error ? 'border-red-500' : 'border-gray-300'}
            ${className}
          `}
          {...props}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';
```

#### c) `TextArea.tsx`
```typescript
import { TextareaHTMLAttributes, forwardRef } from 'react';

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
}

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ label, error, className = '', ...props }, ref) => {
    return (
      <div className="space-y-1">
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
        <textarea
          ref={ref}
          className={`
            w-full px-3 py-2 border rounded-md shadow-sm
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            ${error ? 'border-red-500' : 'border-gray-300'}
            ${className}
          `}
          {...props}
        />
        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}
      </div>
    );
  }
);

TextArea.displayName = 'TextArea';
```

#### d) `index.ts` (barrel export)
```typescript
export { Input } from './Input';
export { Select } from './Select';
export { TextArea } from './TextArea';
```

**Completion Checklist:**
- [ ] `Input.tsx` created
- [ ] `Select.tsx` created
- [ ] `TextArea.tsx` created
- [ ] `index.ts` barrel export created
- [ ] All files have no syntax errors

---

### Task 4: Create Loading Skeleton Components
**Priority: P2** | **Status: READY** | **Assigned by: Sonnet**

**Directory:** `frontend/components/skeletons/`

**Files to Create:**

#### a) `CardSkeleton.tsx`
```typescript
export function CardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow p-4 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
      <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
      <div className="h-8 bg-gray-200 rounded w-full"></div>
    </div>
  );
}
```

#### b) `TableRowSkeleton.tsx`
```typescript
export function TableRowSkeleton({ columns = 4 }: { columns?: number }) {
  return (
    <tr className="animate-pulse">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-gray-200 rounded"></div>
        </td>
      ))}
    </tr>
  );
}
```

#### c) `CalendarSkeleton.tsx`
```typescript
export function CalendarSkeleton() {
  return (
    <div className="animate-pulse">
      {/* Header */}
      <div className="flex justify-between mb-4">
        <div className="h-6 bg-gray-200 rounded w-32"></div>
        <div className="flex gap-2">
          <div className="h-8 w-8 bg-gray-200 rounded"></div>
          <div className="h-8 w-8 bg-gray-200 rounded"></div>
        </div>
      </div>

      {/* Day headers */}
      <div className="grid grid-cols-7 gap-2 mb-2">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="h-4 bg-gray-200 rounded"></div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-2">
        {Array.from({ length: 35 }).map((_, i) => (
          <div key={i} className="h-20 bg-gray-200 rounded"></div>
        ))}
      </div>
    </div>
  );
}
```

#### d) `index.ts`
```typescript
export { CardSkeleton } from './CardSkeleton';
export { TableRowSkeleton } from './TableRowSkeleton';
export { CalendarSkeleton } from './CalendarSkeleton';
```

**Completion Checklist:**
- [ ] `CardSkeleton.tsx` created
- [ ] `TableRowSkeleton.tsx` created
- [ ] `CalendarSkeleton.tsx` created
- [ ] `index.ts` barrel export created

---

### Task 5: Scaffold Test Files
**Priority: P3** | **Status: READY** | **Assigned by: Sonnet**

**Directory:** `frontend/__tests__/`

**Template for Hook Tests:**
```typescript
// __tests__/hooks/useSchedule.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSchedule } from '@/lib/hooks';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useSchedule', () => {
  it('should fetch schedule data', async () => {
    // TODO: Implement test
  });

  it('should handle errors', async () => {
    // TODO: Implement test
  });

  it('should refetch on date change', async () => {
    // TODO: Implement test
  });
});
```

**Files to Create:**
| File | Hook |
|------|------|
| `__tests__/hooks/useSchedule.test.ts` | useSchedule |
| `__tests__/hooks/usePeople.test.ts` | usePeople |
| `__tests__/hooks/useAbsences.test.ts` | useAbsences |
| `__tests__/hooks/useRotationTemplates.test.ts` | useRotationTemplates |
| `__tests__/hooks/useValidateSchedule.test.ts` | useValidateSchedule |

**Completion Checklist:**
- [ ] All 5 test files created
- [ ] Each follows template structure
- [ ] Import paths are correct

---

## Completed Tasks

| Task | Date | Files Created | Notes |
|------|------|---------------|-------|
| - | - | - | - |

---

## Reporting Format

When completing a task, report to Sonnet:

```markdown
## Completed: [Task Name]

### Files Created/Modified
- `path/to/file1.ts` - [brief description]
- `path/to/file2.ts` - [brief description]

### Anomalies (if any)
- [Anything that didn't match expected pattern]

### Ready for Review
- [ ] Yes / No
```

---

## Escalation to Sonnet

Escalate if:
- Template doesn't fit the situation
- Decision needed between two approaches
- Error you can't resolve
- Pattern unclear

**Escalation Format:**
```markdown
## Need Clarification: [Topic]

### Task
[What I'm trying to do]

### Issue
[What's unclear or doesn't fit]

### Question
[Specific question for Sonnet]
```

---

*Last Updated: 2024-12-13*
