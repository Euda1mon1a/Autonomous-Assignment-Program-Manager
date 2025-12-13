***REMOVED*** SONNET 4.5 Task List

***REMOVED******REMOVED*** Role: The Senior Implementer

You are the primary implementation engine. Build features, integrate APIs, fix bugs, and coordinate with Haiku for repetitive subtasks. Escalate to Opus when you encounter architectural decisions or complex cross-cutting concerns.

---

***REMOVED******REMOVED*** Current Sprint: Frontend API Integration

***REMOVED******REMOVED******REMOVED*** Priority Legend
- **P0**: Blocking other work, do immediately
- **P1**: Critical path, high priority
- **P2**: Important, normal priority
- **P3**: Nice to have, lower priority

---

***REMOVED******REMOVED*** P0 - Blocking Tasks

***REMOVED******REMOVED******REMOVED*** 1. Create API Client Base
**Status: NOT STARTED** | **Estimate: 30 min**

**File:** `frontend/lib/api.ts`

**Requirements:**
```typescript
// Create axios instance with:
// - baseURL from environment (NEXT_PUBLIC_API_URL)
// - Request interceptor for auth token
// - Response interceptor for error transformation
// - Typed request/response helpers

export const api = axios.create({...})

export async function get<T>(url: string): Promise<T>
export async function post<T>(url: string, data: unknown): Promise<T>
export async function put<T>(url: string, data: unknown): Promise<T>
export async function del(url: string): Promise<void>
```

**Acceptance Criteria:**
- [ ] Base URL configurable via env
- [ ] Auth token attached to requests (when available)
- [ ] Errors transformed to consistent shape
- [ ] TypeScript generics for type safety

**Delegate to Haiku:** None (foundational code)

---

***REMOVED******REMOVED*** P1 - Critical Path Tasks

***REMOVED******REMOVED******REMOVED*** 2. Implement Core React Query Hooks
**Status: NOT STARTED** | **Estimate: 2 hours**

**File:** `frontend/lib/hooks.ts`

**Hooks to Implement:**

***REMOVED******REMOVED******REMOVED******REMOVED*** a) `useSchedule(startDate: Date, endDate: Date)`
```typescript
// Fetch assignments for date range
// Endpoint: GET /api/assignments?start_date=X&end_date=Y
// Cache key: ['schedule', startDate, endDate]
// Refetch: on window focus, every 5 min
```

***REMOVED******REMOVED******REMOVED******REMOVED*** b) `usePeople(filters?: PeopleFilters)`
```typescript
// Fetch residents and faculty
// Endpoint: GET /api/people?role=X&pgy_level=Y
// Cache key: ['people', filters]
// Support filtering by role, PGY level, active status
```

***REMOVED******REMOVED******REMOVED******REMOVED*** c) `useRotationTemplates()`
```typescript
// Fetch all rotation templates
// Endpoint: GET /api/rotation-templates
// Cache key: ['rotation-templates']
// Stale time: 10 minutes (rarely changes)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** d) `useAbsences(personId?: number, dateRange?: DateRange)`
```typescript
// Fetch absences, optionally filtered
// Endpoint: GET /api/absences
// Cache key: ['absences', personId, dateRange]
```

***REMOVED******REMOVED******REMOVED******REMOVED*** e) `useValidateSchedule(scheduleRunId: number)`
```typescript
// Fetch ACGME validation results
// Endpoint: GET /api/schedule/validate/{id}
// Cache key: ['validation', scheduleRunId]
```

**Acceptance Criteria:**
- [ ] All hooks use React Query properly
- [ ] Loading and error states exposed
- [ ] Cache invalidation on mutations
- [ ] TypeScript types match backend responses

**Delegate to Haiku:** Type definitions for API responses

---

***REMOVED******REMOVED******REMOVED*** 3. Implement Mutation Hooks
**Status: NOT STARTED** | **Estimate: 1.5 hours**

**File:** `frontend/lib/hooks.ts` (continued)

**Mutations to Implement:**

***REMOVED******REMOVED******REMOVED******REMOVED*** a) Person CRUD
```typescript
useCreatePerson()   // POST /api/people
useUpdatePerson()   // PUT /api/people/{id}
useDeletePerson()   // DELETE /api/people/{id}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** b) Absence Management
```typescript
useCreateAbsence()  // POST /api/absences
useUpdateAbsence()  // PUT /api/absences/{id}
useDeleteAbsence()  // DELETE /api/absences/{id}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** c) Schedule Generation
```typescript
useGenerateSchedule()  // POST /api/schedule/generate
// Payload: { start_date, end_date, options }
// Invalidates: ['schedule'], ['validation']
```

***REMOVED******REMOVED******REMOVED******REMOVED*** d) Rotation Templates
```typescript
useCreateTemplate()  // POST /api/rotation-templates
useUpdateTemplate()  // PUT /api/rotation-templates/{id}
useDeleteTemplate()  // DELETE /api/rotation-templates/{id}
```

**Acceptance Criteria:**
- [ ] Optimistic updates where appropriate
- [ ] Cache invalidation after mutations
- [ ] Error handling with rollback
- [ ] Success callbacks for UI feedback

---

***REMOVED******REMOVED******REMOVED*** 4. Build Add Person Modal
**Status: NOT STARTED** | **Estimate: 1 hour**

**File:** `frontend/components/AddPersonModal.tsx`

**Requirements:**
- Form fields: name, email, role (resident/faculty), PGY level (if resident)
- Validation: required fields, email format, PGY 1-3 only for residents
- Submit calls `useCreatePerson()`
- Close modal on success
- Show error message on failure

**UI Pattern:**
```
┌─────────────────────────────────┐
│ Add New Person              [X] │
├─────────────────────────────────┤
│ Name:     [________________]    │
│ Email:    [________________]    │
│ Role:     [Resident     ▼]      │
│ PGY Level:[1 ▼] (if resident)   │
│                                 │
│         [Cancel] [Add Person]   │
└─────────────────────────────────┘
```

**Delegate to Haiku:** Modal wrapper component, form input components

---

***REMOVED******REMOVED******REMOVED*** 5. Build Add Absence Modal
**Status: NOT STARTED** | **Estimate: 1 hour**

**File:** `frontend/components/AddAbsenceModal.tsx`

**Requirements:**
- Form fields: person (dropdown), absence type, start date, end date, notes
- Absence types: VACATION, DEPLOYMENT, TDY, MEDICAL, OTHER
- Date validation: end >= start
- Submit calls `useCreateAbsence()`

**Delegate to Haiku:** DatePicker component styling

---

***REMOVED******REMOVED******REMOVED*** 6. Build Generate Schedule Dialog
**Status: NOT STARTED** | **Estimate: 45 min**

**File:** `frontend/components/GenerateScheduleDialog.tsx`

**Requirements:**
- Date range picker (start/end)
- Options: include weekends, respect existing assignments
- Progress indicator during generation
- Show validation summary on completion
- Link to full compliance report

---

***REMOVED******REMOVED*** P2 - Important Tasks

***REMOVED******REMOVED******REMOVED*** 7. Wire Home Page to API
**Status: NOT STARTED** | **Estimate: 1 hour**

**File:** `frontend/app/page.tsx`

**Changes:**
- Replace mock data with `useSchedule()` hook
- Add loading skeleton while fetching
- Add error state with retry button
- Update stats cards with real counts
- Connect "Generate Schedule" button to dialog

---

***REMOVED******REMOVED******REMOVED*** 8. Wire People Page to API
**Status: NOT STARTED** | **Estimate: 45 min**

**File:** `frontend/app/people/page.tsx`

**Changes:**
- Use `usePeople()` hook with filters
- Add "Add Person" button opening modal
- Add edit/delete actions to person cards
- Implement filter dropdowns (role, PGY level)

---

***REMOVED******REMOVED******REMOVED*** 9. Wire Compliance Page to API
**Status: NOT STARTED** | **Estimate: 1 hour**

**File:** `frontend/app/compliance/page.tsx`

**Changes:**
- Fetch latest schedule run validation
- Display ACGME violation details
- Show compliance percentage metrics
- Add drill-down to specific violations

**Escalate to Opus:** If ACGME display logic is unclear

---

***REMOVED******REMOVED******REMOVED*** 10. Wire Templates Page to API
**Status: NOT STARTED** | **Estimate: 30 min**

**File:** `frontend/app/templates/page.tsx`

**Changes:**
- Use `useRotationTemplates()` hook
- Add create/edit/delete functionality
- Show template constraints and requirements

---

***REMOVED******REMOVED*** P3 - Lower Priority Tasks

***REMOVED******REMOVED******REMOVED*** 11. Settings Page Form Submission
**Status: NOT STARTED** | **Estimate: 30 min**

- Connect form to backend settings API
- Add save confirmation
- Validate inputs

---

***REMOVED******REMOVED******REMOVED*** 12. Emergency Coverage UI
**Status: NOT STARTED** | **Estimate: 1.5 hours**

- Display current absences affecting schedule
- Show suggested replacements from API
- Allow coordinator to approve/reject suggestions
- Trigger schedule regeneration

**Escalate to Opus:** Review replacement algorithm logic

---

***REMOVED******REMOVED*** Delegation Queue for Haiku

***REMOVED******REMOVED******REMOVED*** Ready to Delegate

| Task | Template/Example | Files | Priority |
|------|-----------------|-------|----------|
| API Response Types | See backend schemas | `frontend/types/api.ts` | P0 |
| Modal Component | Tailwind modal pattern | `frontend/components/Modal.tsx` | P1 |
| Form Input Components | Tailwind form inputs | `frontend/components/forms/` | P1 |
| Loading Skeletons | Animate-pulse pattern | `frontend/components/skeletons/` | P2 |
| Test File Scaffolds | Jest/RTL structure | `frontend/__tests__/` | P3 |

***REMOVED******REMOVED******REMOVED*** Delegation Template
```markdown
***REMOVED******REMOVED*** Haiku Task: [Name]

***REMOVED******REMOVED******REMOVED*** Template to Follow
[Exact code example]

***REMOVED******REMOVED******REMOVED*** Files to Create
- `path/to/file.ts`

***REMOVED******REMOVED******REMOVED*** Pattern
- Follow exact structure
- No additional logic
- Report any issues

***REMOVED******REMOVED******REMOVED*** Count: X items
```

---

***REMOVED******REMOVED*** Escalation Triggers

**Escalate to Opus when:**
- [ ] Architectural decision needed (new pattern, library choice)
- [ ] Security concern (auth, data exposure)
- [ ] ACGME logic seems incorrect
- [ ] Performance issue (slow queries, large payloads)
- [ ] Cross-cutting change (affects multiple systems)
- [ ] Stuck for more than 30 minutes

**Escalation Template:**
```markdown
***REMOVED******REMOVED*** Escalation: [Title]

***REMOVED******REMOVED******REMOVED*** Context
[What I'm working on]

***REMOVED******REMOVED******REMOVED*** Issue
[What's blocking me]

***REMOVED******REMOVED******REMOVED*** Options I See
1. [Option A] - tradeoff
2. [Option B] - tradeoff

***REMOVED******REMOVED******REMOVED*** My Recommendation
[If any]
```

---

***REMOVED******REMOVED*** Completed Tasks

| Task | Date | Notes |
|------|------|-------|
| - | - | - |

---

***REMOVED******REMOVED*** Dependencies

***REMOVED******REMOVED******REMOVED*** Blocked By
- Opus: Auth architecture (blocks protected routes)
- Opus: Error handling strategy (blocks API client completion)

***REMOVED******REMOVED******REMOVED*** Blocking
- Haiku: Waiting for type definitions task
- Integration tests: Waiting for hooks completion

---

***REMOVED******REMOVED*** Notes

*Capture implementation notes, gotchas, and learnings here.*

---

*Last Updated: 2024-12-13*
