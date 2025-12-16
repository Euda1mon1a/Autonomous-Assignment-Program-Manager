# 3x Opus Parallel Execution Guide

## Running Three Opus 4.5 Instances Simultaneously

This guide is for running **three identical Opus 4.5 instances** in parallel terminals, each owning specific files to avoid conflicts.

---

## Core Principle: Strict File Ownership

Each Opus instance **owns** specific directories/files. No instance touches another's territory.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    3x OPUS FILE OWNERSHIP                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  TERMINAL 1 (Opus-API)      TERMINAL 2 (Opus-UI)      TERMINAL 3   │
│  "API & Data Layer"         "Components & Pages"      (Opus-Docs)  │
│                                                       "Docs & Mail"│
│  ┌─────────────────┐       ┌─────────────────┐      ┌─────────────┐│
│  │ frontend/lib/   │       │ frontend/       │      │ docs/       ││
│  │  ├── api.ts     │       │  components/    │      │ backend/    ││
│  │  └── hooks.ts   │       │   ├── Modal     │      │  tests/     ││
│  │                 │       │   ├── forms/    │      │ README      ││
│  │ frontend/types/ │       │   ├── skeletons/│      │ *.md files  ││
│  │  └── api.ts     │       │   └── *Modal.tsx│      │             ││
│  │                 │       │                 │      │             ││
│  │ frontend/       │       │ frontend/app/   │      │ frontend/   ││
│  │  __tests__/     │       │  ├── page.tsx   │      │  __tests__/ ││
│  │  hooks/         │       │  ├── people/    │      │  components/││
│  │                 │       │  ├── compliance/│      │             ││
│  │                 │       │  ├── templates/ │      │             ││
│  │                 │       │  └── settings/  │      │             ││
│  └─────────────────┘       └─────────────────┘      └─────────────┘│
│                                                                     │
│  DO NOT TOUCH:             DO NOT TOUCH:            DO NOT TOUCH:  │
│  - components/             - lib/                   - lib/         │
│  - app/ pages              - types/                 - components/  │
│  - docs/                   - docs/                  - app/ pages   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start: Copy-Paste These Prompts

### Before Starting - Setup

All three terminals should be in the same repo directory:
```bash
cd /path/to/Autonomous-Assignment-Program-Manager
```

---

## TERMINAL 1: Opus-API (API & Data Layer)

**Copy this entire prompt:**

```
You are Opus-API, working on the Residency Scheduler project.

## YOUR TERRITORY (files you OWN - only you touch these):
- frontend/lib/api.ts (CREATE)
- frontend/lib/hooks.ts (CREATE)
- frontend/types/api.ts (CREATE - move types from types/index.ts)
- frontend/__tests__/hooks/*.test.ts (CREATE)

## DO NOT TOUCH (other Opus instances own these):
- frontend/components/* (Opus-UI owns this)
- frontend/app/* pages (Opus-UI owns this)
- docs/* (Opus-Docs owns this)

## YOUR TASKS:

### Task 1: Create API Client
Create `frontend/lib/api.ts`:
- Axios instance with baseURL from NEXT_PUBLIC_API_URL (default: http://localhost:8000)
- Response interceptor for error handling
- Typed helpers: get<T>, post<T>, put<T>, del

### Task 2: Create React Query Hooks
Create `frontend/lib/hooks.ts`:
- useSchedule(startDate: Date, endDate: Date) - GET /api/assignments
- usePeople(filters?) - GET /api/people
- useRotationTemplates() - GET /api/rotation-templates
- useAbsences(personId?) - GET /api/absences
- useValidateSchedule(startDate, endDate) - GET /api/schedule/validate
- useGenerateSchedule() - POST /api/schedule/generate mutation
- useCreatePerson() - POST /api/people mutation
- useUpdatePerson() - PUT /api/people/{id} mutation
- useDeletePerson() - DELETE /api/people/{id} mutation
- useCreateAbsence() - POST /api/absences mutation

### Task 3: Create/Update Types
Create `frontend/types/api.ts` with request/response types for all hooks.
Keep existing types in types/index.ts, add API-specific types.

### Task 4: Scaffold Hook Tests
Create `frontend/__tests__/hooks/` with test files for each hook.

## IMPORTANT:
- Reference backend/app/routes/*.py for exact API endpoints and schemas
- Import types from '@/types'
- Use React Query v5 patterns (@tanstack/react-query)
- Export all hooks from hooks.ts

When done with each task, commit with message starting with "[Opus-API]"

START with Task 1 (api.ts) - this unblocks everything else.
```

---

## TERMINAL 2: Opus-UI (Components & Pages)

**Copy this entire prompt:**

```
You are Opus-UI, working on the Residency Scheduler project.

## YOUR TERRITORY (files you OWN - only you touch these):
- frontend/components/Modal.tsx (CREATE)
- frontend/components/forms/*.tsx (CREATE directory and files)
- frontend/components/skeletons/*.tsx (CREATE directory and files)
- frontend/components/AddPersonModal.tsx (CREATE)
- frontend/components/AddAbsenceModal.tsx (CREATE)
- frontend/components/GenerateScheduleDialog.tsx (CREATE)
- frontend/app/page.tsx (MODIFY - wire to API)
- frontend/app/people/page.tsx (MODIFY - wire to API)
- frontend/app/compliance/page.tsx (MODIFY - wire to API)
- frontend/app/templates/page.tsx (MODIFY - wire to API)
- frontend/app/settings/page.tsx (MODIFY - add form submission)

## DO NOT TOUCH (other Opus instances own these):
- frontend/lib/* (Opus-API owns this)
- frontend/types/* (Opus-API owns this)
- docs/* (Opus-Docs owns this)

## YOUR TASKS:

### Task 1: Create Base Components
Create `frontend/components/Modal.tsx`:
- Props: isOpen, onClose, title, children
- Escape key closes, click outside closes
- Use Tailwind for styling

Create `frontend/components/forms/` directory with:
- Input.tsx (label, error, ...inputProps)
- Select.tsx (label, options, error, ...selectProps)
- TextArea.tsx (label, error, ...textareaProps)
- DatePicker.tsx (label, error, value, onChange)
- index.ts (barrel export)

Create `frontend/components/skeletons/` directory with:
- CardSkeleton.tsx
- TableRowSkeleton.tsx
- CalendarSkeleton.tsx
- index.ts (barrel export)

### Task 2: Create Modal Components
Create `frontend/components/AddPersonModal.tsx`:
- Form: name, email, role (resident/faculty), pgy_level (1-3 if resident)
- Uses Modal, form components
- Calls useCreatePerson() on submit (import from @/lib/hooks when available)
- For now, stub the hook import with a TODO comment if hooks.ts doesn't exist yet

Create `frontend/components/AddAbsenceModal.tsx`:
- Form: person (dropdown), type, start_date, end_date, notes
- Similar pattern

Create `frontend/components/GenerateScheduleDialog.tsx`:
- Form: start_date, end_date, options
- Shows progress during generation
- Displays validation results

### Task 3: Wire Pages to API
Update each page in frontend/app/ to:
- Import hooks from '@/lib/hooks'
- Replace mock data with hook data
- Add loading states (use skeletons)
- Add error states with retry
- Connect buttons to modals/mutations

## DEPENDENCY NOTE:
Opus-API is creating hooks.ts in parallel. If hooks aren't ready yet:
- Create components with TODO comments for hook imports
- Use placeholder data that matches expected hook return types
- Components should be ready to swap in real hooks

When done with each task, commit with message starting with "[Opus-UI]"

START with Task 1 (Modal.tsx, forms/, skeletons/) - these are needed by Task 2.
```

---

## TERMINAL 3: Opus-Docs (Documentation & Backend)

**Copy this entire prompt:**

```
You are Opus-Docs, working on the Residency Scheduler project.

## YOUR TERRITORY (files you OWN - only you touch these):
- docs/ directory (CREATE and all files within)
- docs/AUTH_ARCHITECTURE.md (CREATE)
- docs/ERROR_HANDLING.md (CREATE)
- docs/CACHING_STRATEGY.md (CREATE)
- docs/API_REFERENCE.md (CREATE)
- backend/tests/ (CREATE test files)
- README.md (UPDATE if needed)
- Any *.md files in root

## DO NOT TOUCH (other Opus instances own these):
- frontend/lib/* (Opus-API owns this)
- frontend/components/* (Opus-UI owns this)
- frontend/app/* (Opus-UI owns this)
- frontend/types/* (Opus-API owns this)

## YOUR TASKS:

### Task 1: Create docs/ Directory Structure
```
docs/
├── AUTH_ARCHITECTURE.md
├── ERROR_HANDLING.md
├── CACHING_STRATEGY.md
└── API_REFERENCE.md
```

### Task 2: Write AUTH_ARCHITECTURE.md
Document the authentication system design:
- Review backend/app/core/security.py and backend/app/core/config.py
- JWT token strategy (access + refresh tokens)
- Token storage (HttpOnly cookies vs localStorage - recommend HttpOnly)
- Role definitions: admin, coordinator, faculty, resident
- Permission matrix (who can do what)
- Protected route middleware pattern for frontend
- Session management

### Task 3: Write ERROR_HANDLING.md
Document unified error handling:
- Standard error response schema: { code, message, details, timestamp }
- Map Python exceptions to HTTP status codes
- Frontend error boundary strategy
- Toast/notification patterns
- Retry logic for transient failures
- User-facing error messages (friendly, not technical)

### Task 4: Write CACHING_STRATEGY.md
Document React Query caching for frontend:
- Cache keys for each entity type
- Stale times (when to refetch)
- Cache invalidation rules (what to invalidate on mutations)
- Optimistic updates strategy
- Background refetch patterns

### Task 5: Write API_REFERENCE.md
Document all backend API endpoints:
- Read backend/app/routes/*.py
- Document each endpoint: method, path, request body, response, errors
- Include example requests/responses
- Group by resource (People, Assignments, Schedule, etc.)

### Task 6: Backend Tests (if time permits)
Create pytest tests in backend/tests/ for:
- ACGME validator logic
- Scheduling engine edge cases
- API endpoint integration tests

## IMPORTANT:
- Read the actual backend code before documenting
- Be accurate - this documentation will guide the other Opus instances
- Keep docs concise but complete

When done with each task, commit with message starting with "[Opus-Docs]"

START with Task 2 (AUTH_ARCHITECTURE.md) - this is highest priority for security design.
```

---

## Execution Timeline

```
Time ──────────────────────────────────────────────────────────────────►
0min                    30min                   60min                 90min

Opus-API:  ████ api.ts ████│████████ hooks.ts █████████│██ tests ██│
           [20 min]        [40 min]                    [20 min]

Opus-UI:   ██ Modal ██│██ forms ██│████ Modals ████│███ Page Wiring ███│
           [15 min]   [15 min]    [30 min]         [30 min]

Opus-Docs: ████ Auth ████│████ Errors ████│██ Cache ██│████ API Ref ████│
           [25 min]       [20 min]         [15 min]    [30 min]
```

---

## Merge Order

Since all three work on completely separate files, **merge order doesn't matter for conflicts**.

However, for logical completeness:

```bash
# After all three complete, merge in any order:
git checkout integration-branch

# Opus-API first (provides types and hooks)
git merge opus-api-branch -m "[Opus-API] Add API client, hooks, and types"

# Opus-UI second (uses hooks)
git merge opus-ui-branch -m "[Opus-UI] Add components and wire pages"

# Opus-Docs third (documentation)
git merge opus-docs-branch -m "[Opus-Docs] Add architecture documentation"

# Verify build
cd frontend && npm run build
```

---

## Monitoring Progress

### Check Status (run in any terminal)

```bash
# See what each Opus has committed
git log --oneline --all | grep -E "\[Opus-(API|UI|Docs)\]"

# See uncommitted changes by directory
git status

# Check if frontend builds
cd frontend && npm run build
```

### Status Check Prompt (paste into any terminal)

```
What is your current status?
1. What files have you created/modified?
2. What task are you currently on?
3. Any blockers or questions?
4. Estimated time to completion?
```

---

## Handling Dependencies

### If Opus-UI needs hooks but Opus-API isn't done yet:

```typescript
// In AddPersonModal.tsx, temporarily:
// TODO: Import from @/lib/hooks when available
// import { useCreatePerson } from '@/lib/hooks';

const useCreatePerson = () => ({
  mutate: (data: any) => console.log('TODO: implement', data),
  isPending: false,
});
```

### If Opus-API needs types that don't exist:

Create them in `frontend/types/api.ts` - this is Opus-API's territory.

### If anyone is blocked:

```
I'm blocked on [specific issue].
The file I need is owned by Opus-[API/UI/Docs].
Can you check their progress or have them prioritize [specific file]?
```

---

## Quick Reference Card

| Terminal | Name | Creates | Doesn't Touch |
|----------|------|---------|---------------|
| 1 | Opus-API | lib/, types/, __tests__/hooks/ | components/, app/, docs/ |
| 2 | Opus-UI | components/, app/ pages | lib/, types/, docs/ |
| 3 | Opus-Docs | docs/, backend/tests/, *.md | frontend/* |

---

## Commit Message Convention

```
[Opus-API] feat: Add axios client with error handling
[Opus-API] feat: Implement useSchedule and usePeople hooks
[Opus-UI] feat: Create Modal and form components
[Opus-UI] feat: Wire Home page to useSchedule hook
[Opus-Docs] docs: Add authentication architecture design
```

This makes it easy to track which instance did what.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Two instances touched same file | One backs out, recommits. Check file ownership. |
| Build fails after merge | Usually missing import - check error, have owner fix |
| Instance finished early | Give them tasks from another's "if time permits" list |
| Instance stuck | Paste status check prompt, identify blocker |

---

*Last Updated: 2024-12-13*
