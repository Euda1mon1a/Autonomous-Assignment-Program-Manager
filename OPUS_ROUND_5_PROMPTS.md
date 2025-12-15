# Opus Round 5 - 5 Parallel Instances (Final Polish)

Project is at 94%! This round focuses on polish, testing, and production-readiness.

Run these 5 prompts in separate terminals simultaneously.

---

## Terminal 1: Opus-E2E-Testing

```
You are Opus-E2E-Testing. Your task is to add comprehensive end-to-end test coverage.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/e2e/auth.spec.ts (CREATE)
- frontend/e2e/dashboard.spec.ts (CREATE)
- frontend/e2e/absences.spec.ts (CREATE)
- frontend/e2e/people.spec.ts (CREATE)
- frontend/playwright.config.ts (CREATE)
- frontend/package.json (UPDATE - add playwright deps)

IMPLEMENTATION REQUIREMENTS:

1. Install Playwright:
   - Add to package.json devDependencies: @playwright/test
   - Create playwright.config.ts with baseURL http://localhost:3000

2. frontend/e2e/auth.spec.ts:
   - Test: Navigate to / redirects to /login when not authenticated
   - Test: Login with valid credentials redirects to dashboard
   - Test: Login with invalid credentials shows error
   - Test: Logout clears session and redirects to login

3. frontend/e2e/dashboard.spec.ts:
   - Test: Dashboard loads with 4 widgets
   - Test: Quick Actions buttons navigate correctly
   - Test: Schedule summary shows stats

4. frontend/e2e/absences.spec.ts:
   - Test: Absences page loads with calendar view
   - Test: Toggle between calendar and list view
   - Test: Filter by absence type works
   - Test: Add absence modal opens

5. frontend/e2e/people.spec.ts:
   - Test: People page loads with list
   - Test: Add person modal opens
   - Test: Edit person modal works

Use Playwright best practices:
```typescript
import { test, expect } from '@playwright/test'

test.describe('Auth', () => {
  test('redirects to login when not authenticated', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL('/login')
  })
})
```

DO NOT modify any source files, only test files.
Commit with prefix: [Opus-E2E]
```

---

## Terminal 2: Opus-Form-Validation

```
You are Opus-Form-Validation. Your task is to add comprehensive form validation.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/lib/validation.ts (CREATE)
- frontend/src/components/LoginForm.tsx (UPDATE - add validation)
- frontend/src/components/AddPersonModal.tsx (UPDATE - add validation)
- frontend/src/components/AddAbsenceModal.tsx (UPDATE - add validation)
- frontend/src/components/forms/Input.tsx (UPDATE - add error state)

IMPLEMENTATION REQUIREMENTS:

1. frontend/src/lib/validation.ts:
   ```typescript
   export interface ValidationResult {
     valid: boolean
     errors: Record<string, string>
   }

   export function validateEmail(email: string): string | null
   export function validateRequired(value: string, fieldName: string): string | null
   export function validateDateRange(start: string, end: string): string | null
   export function validatePassword(password: string): string | null
   ```

2. Update Input.tsx to support error state:
   - Add `error?: string` prop
   - Show red border when error exists
   - Display error message below input

3. Update LoginForm.tsx:
   - Validate email format
   - Validate password not empty
   - Show inline error messages
   - Disable submit until valid

4. Update AddPersonModal.tsx:
   - Validate name required (min 2 chars)
   - Validate email format if provided
   - Validate PGY level 1-8 for residents

5. Update AddAbsenceModal.tsx:
   - Validate person selected
   - Validate dates selected
   - Validate end_date >= start_date
   - Show error if date range invalid

Use consistent error styling:
```typescript
<Input
  label="Email"
  value={email}
  onChange={setEmail}
  error={errors.email}
/>
```

DO NOT modify backend or non-form components.
Commit with prefix: [Opus-Validation]
```

---

## Terminal 3: Opus-Loading-States

```
You are Opus-Loading-States. Your task is to enhance loading and empty states throughout the app.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/components/EmptyState.tsx (CREATE)
- frontend/src/components/dashboard/ScheduleSummary.tsx (UPDATE)
- frontend/src/components/dashboard/ComplianceAlert.tsx (UPDATE)
- frontend/src/components/dashboard/UpcomingAbsences.tsx (UPDATE)
- frontend/src/app/people/page.tsx (UPDATE - add empty state)
- frontend/src/app/templates/page.tsx (UPDATE - add empty state)

IMPLEMENTATION REQUIREMENTS:

1. frontend/src/components/EmptyState.tsx:
   ```typescript
   interface EmptyStateProps {
     icon?: React.ElementType
     title: string
     description?: string
     action?: {
       label: string
       onClick: () => void
     }
   }
   ```
   - Centered layout with icon, title, description
   - Optional action button
   - Consistent styling with the app

2. Update dashboard widgets to show proper empty states:
   - ScheduleSummary: "No schedule generated" with Generate button
   - ComplianceAlert: "No compliance data" when no schedule
   - UpcomingAbsences: "No upcoming absences" message

3. Update People page:
   - Show EmptyState when no people exist
   - Icon: Users
   - Title: "No people added yet"
   - Action: "Add Person" button

4. Update Templates page:
   - Show EmptyState when no templates exist
   - Icon: FileText
   - Title: "No rotation templates"
   - Action: "Create Template" button

Empty state styling:
```typescript
<EmptyState
  icon={Users}
  title="No people added yet"
  description="Add residents and attendings to get started"
  action={{ label: "Add Person", onClick: () => setIsAddModalOpen(true) }}
/>
```

DO NOT modify backend or create new pages.
Commit with prefix: [Opus-EmptyStates]
```

---

## Terminal 4: Opus-Accessibility

```
You are Opus-Accessibility. Your task is to improve accessibility (a11y) across the app.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/components/Modal.tsx (UPDATE)
- frontend/src/components/Navigation.tsx (UPDATE)
- frontend/src/components/MobileNav.tsx (UPDATE)
- frontend/src/components/forms/Input.tsx (UPDATE)
- frontend/src/components/forms/Select.tsx (UPDATE)
- frontend/src/components/ProtectedRoute.tsx (UPDATE)

IMPLEMENTATION REQUIREMENTS:

1. Update Modal.tsx:
   - Add aria-modal="true"
   - Add role="dialog"
   - Add aria-labelledby pointing to title
   - Focus trap: focus first input on open
   - Close on Escape key
   - Return focus to trigger on close

2. Update Navigation.tsx:
   - Add aria-label="Main navigation"
   - Add aria-current="page" to active link
   - Ensure keyboard navigation works

3. Update MobileNav.tsx:
   - Add aria-expanded to hamburger button
   - Add aria-controls pointing to menu
   - Add aria-hidden to menu when closed

4. Update Input.tsx:
   - Add aria-invalid when error exists
   - Add aria-describedby pointing to error message
   - Generate unique IDs for accessibility

5. Update Select.tsx:
   - Add aria-label if no visible label
   - Ensure proper labeling

6. Update ProtectedRoute.tsx:
   - Add aria-live="polite" to loading/error states
   - Ensure screen readers announce state changes

Accessibility patterns:
```typescript
<input
  id={inputId}
  aria-invalid={!!error}
  aria-describedby={error ? errorId : undefined}
/>
{error && <span id={errorId} role="alert">{error}</span>}
```

DO NOT modify backend or business logic.
Commit with prefix: [Opus-A11y]
```

---

## Terminal 5: Opus-Performance

```
You are Opus-Performance. Your task is to optimize performance and add production configs.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/lib/hooks.ts (UPDATE - add staleTime, cacheTime)
- frontend/src/app/layout.tsx (UPDATE - add metadata)
- frontend/next.config.js (UPDATE - production optimizations)
- frontend/src/components/ScheduleCalendar.tsx (UPDATE - memoization)
- frontend/src/components/AbsenceCalendar.tsx (UPDATE - memoization)

IMPLEMENTATION REQUIREMENTS:

1. Update hooks.ts - Add caching config to all queries:
   ```typescript
   useQuery({
     queryKey: ['people'],
     queryFn: fetchPeople,
     staleTime: 5 * 60 * 1000, // 5 minutes
     gcTime: 30 * 60 * 1000, // 30 minutes (was cacheTime)
   })
   ```

2. Update layout.tsx - Add SEO metadata:
   ```typescript
   export const metadata: Metadata = {
     title: 'Residency Scheduler',
     description: 'Medical residency scheduling with ACGME compliance',
     robots: 'noindex, nofollow', // Private app
   }
   ```

3. Update next.config.js:
   ```javascript
   const nextConfig = {
     reactStrictMode: true,
     poweredByHeader: false,
     compress: true,
     images: {
       unoptimized: true, // No external images
     },
   }
   ```

4. Memoize expensive calendar components:
   - Wrap ScheduleCalendar day cells with React.memo
   - Wrap AbsenceCalendar day cells with React.memo
   - Add useMemo for date calculations

Example memoization:
```typescript
const DayCell = React.memo(function DayCell({ date, absences }: Props) {
  return (...)
})

const memoizedDates = useMemo(() => generateDates(month), [month])
```

DO NOT modify backend or add new features.
Commit with prefix: [Opus-Perf]
```

---

## Merge Order

After all 5 complete:
1. Opus-Form-Validation (foundational)
2. Opus-Loading-States (UI polish)
3. Opus-Accessibility (improves existing components)
4. Opus-Performance (optimizations)
5. Opus-E2E-Testing (tests the final state)

## Conflict Prevention

Each Opus has strict file ownership. Shared files:
- `hooks.ts` - Only Opus-Performance modifies (caching config)
- `Input.tsx` - Only Opus-Validation modifies (both need it but different changes)
  - If conflict: Opus-Accessibility adds aria attrs, Opus-Validation adds error prop

Potential conflict: Input.tsx
- Resolution: Merge both changes - error prop AND aria attributes

---

## Expected Deliverables

| Opus Instance | New Files | Updated Files |
|--------------|-----------|---------------|
| E2E-Testing | 5 files | 1 file |
| Form-Validation | 1 file | 4 files |
| Loading-States | 1 file | 5 files |
| Accessibility | 0 files | 6 files |
| Performance | 0 files | 5 files |

**Total: 7 new files, 21 updated files**

After this round, project should be at **99% complete** - production ready!
