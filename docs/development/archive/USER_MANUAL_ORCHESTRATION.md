# Multi-Model Orchestration User Manual

## How to Run Your AI Development Team

This manual explains how to prompt Opus 4.5, Sonnet 4.5, and Haiku 4.5 to work on this project efficiently, including parallel execution strategies.

---

## Quick Start: Copy-Paste Prompts

### Start All Three Models in Parallel (Maximum Efficiency)

Open three terminal sessions and run simultaneously:

**Terminal 1 - Opus (Strategic Work):**
```
You are working on the Residency Scheduler project.
Read TODO_OPUS.md and MULTI_MODEL_TASK_DISTRIBUTION.md for context.

Your role: Strategic Architect. Focus on high-level design decisions.

Current task: Design the authentication architecture.
- Read the existing backend auth setup in backend/app/
- Design JWT token flow with refresh mechanism
- Define role-based permissions (admin, coordinator, faculty)
- Document in docs/AUTH_ARCHITECTURE.md

Do not implement - only design and document. Sonnet will implement based on your design.
```

**Terminal 2 - Sonnet (Implementation Work):**
```
You are working on the Residency Scheduler project.
Read TODO_SONNET.md and MULTI_MODEL_TASK_DISTRIBUTION.md for context.

Your role: Senior Implementer. Build features and integrate APIs.

Current task: Create the API client and React Query hooks.
1. Create frontend/lib/api.ts with axios instance
2. Create frontend/lib/hooks.ts with useSchedule, usePeople, useAbsences hooks
3. Follow patterns from existing frontend code

Reference backend API routes in backend/app/routes/ for endpoint signatures.
Escalate to Opus if you encounter architectural decisions.
```

**Terminal 3 - Haiku (Execution Work):**
```
You are working on the Residency Scheduler project.
Read TODO_HAIKU.md for your task list with exact templates.

Your role: Rapid Executor. Follow templates exactly.

Current task: Generate TypeScript types and scaffold components.
1. Create frontend/types/api.ts with all entity types (follow template in TODO_HAIKU.md)
2. Create frontend/components/Modal.tsx (copy template exactly)
3. Create frontend/components/forms/ with Input, Select, TextArea components

Do not deviate from templates. Report any issues.
```

---

## Parallel Execution Map

### What Can Run in Parallel (No Dependencies)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PARALLEL EXECUTION ZONES                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ZONE A: Backend/Docs          ZONE B: Frontend Core      ZONE C: Frontend  │
│  (Opus Territory)              (Sonnet Territory)         UI Components     │
│                                                           (Haiku Territory) │
│  ┌─────────────────┐          ┌─────────────────┐       ┌─────────────────┐ │
│  │ • Auth design   │          │ • API client    │       │ • Type defs     │ │
│  │ • Error strategy│          │ • React hooks   │       │ • Modal.tsx     │ │
│  │ • Schema review │          │ • Page wiring   │       │ • Form inputs   │ │
│  │ • Algo research │          │ • Form logic    │       │ • Skeletons     │ │
│  └─────────────────┘          └─────────────────┘       └─────────────────┘ │
│          │                            │                         │           │
│          │                            │                         │           │
│          └────────────────────────────┼─────────────────────────┘           │
│                                       │                                     │
│                              NO CONFLICTS                                   │
│                         (Different files/concerns)                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dependency Graph: What Must Wait

```
                    ┌──────────────────┐
                    │ Opus: Auth Design │
                    └────────┬─────────┘
                             │ BLOCKS
                             ▼
                    ┌──────────────────┐
                    │Sonnet: Auth Impl │
                    └──────────────────┘


┌──────────────────┐
│ Haiku: Types     │
└────────┬─────────┘
         │ SHOULD COMPLETE BEFORE
         ▼
┌──────────────────┐
│Sonnet: API Hooks │ (uses types)
└────────┬─────────┘
         │ SHOULD COMPLETE BEFORE
         ▼
┌──────────────────┐
│Sonnet: Page Wire │ (uses hooks)
└──────────────────┘


┌──────────────────┐     ┌──────────────────┐
│ Haiku: Modal.tsx │     │ Haiku: Form Inputs│
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         └───────────┬────────────┘
                     │ SHOULD COMPLETE BEFORE
                     ▼
            ┌──────────────────┐
            │Sonnet: AddPerson │
            │       Modal      │
            └──────────────────┘
```

---

## Optimal Parallel Execution Sequences

### Phase 1: Foundation (All Three in Parallel)

| Opus | Sonnet | Haiku |
|------|--------|-------|
| Design auth architecture | Create `api.ts` client | Generate `types/api.ts` |
| Design error handling | Set up hook structure | Create `Modal.tsx` |
| Review database schema | — | Create form components |

**Duration:** ~30-45 minutes
**Files touched:** No overlap

---

### Phase 2: Core Features (All Three in Parallel)

| Opus | Sonnet | Haiku |
|------|--------|-------|
| Review Sonnet's api.ts | Implement `useSchedule` hook | Create loading skeletons |
| Design caching strategy | Implement `usePeople` hook | Scaffold test files |
| Algorithm optimization research | Implement `useAbsences` hook | — |

**Duration:** ~1-2 hours
**Dependencies:** Haiku's types should be done before Sonnet starts hooks

---

### Phase 3: Integration (Sonnet Heavy, Others Support)

| Opus | Sonnet | Haiku |
|------|--------|-------|
| Review ACGME compliance UI | Wire Home page to API | Update imports if needed |
| Security review | Wire People page to API | Add new types as discovered |
| — | Build AddPerson modal | — |

**Duration:** ~1-2 hours
**Dependencies:** Hooks must be complete

---

### Phase 4: Polish (All Three in Parallel)

| Opus | Sonnet | Haiku |
|------|--------|-------|
| Final architecture review | Implement auth (from Opus design) | Add JSDoc comments |
| Documentation review | Error boundary implementation | Code formatting cleanup |
| Performance audit | Integration tests | Unit test scaffolds |

---

## Detailed Prompts for Each Phase

### Phase 1 Prompts

#### Opus - Phase 1
```
Project: Residency Scheduler
Reference: TODO_OPUS.md, MULTI_MODEL_TASK_DISTRIBUTION.md

Execute these tasks (design/documentation only, no implementation):

1. Authentication Architecture Design
   - Read backend/app/main.py and any existing auth code
   - Design JWT flow with access/refresh tokens
   - Define roles: admin (full access), coordinator (scheduling), faculty (view + own schedule)
   - Map permissions to API endpoints
   - Output: Create docs/AUTH_ARCHITECTURE.md

2. Error Handling Strategy
   - Define error response schema: { code, message, details, timestamp }
   - Map Python exceptions to HTTP codes
   - Define frontend error boundary strategy
   - Output: Create docs/ERROR_HANDLING.md

You are working in parallel with Sonnet (API client) and Haiku (types/components).
Do not touch frontend/lib/ or frontend/components/ - those are their zones.
```

#### Sonnet - Phase 1
```
Project: Residency Scheduler
Reference: TODO_SONNET.md, MULTI_MODEL_TASK_DISTRIBUTION.md

Execute these tasks:

1. Create API Client (frontend/lib/api.ts)
   - Axios instance with NEXT_PUBLIC_API_URL base
   - Request interceptor for auth token (stub for now)
   - Response interceptor for error transformation
   - Typed helpers: get<T>, post<T>, put<T>, del

2. Create Hook File Structure (frontend/lib/hooks.ts)
   - Set up React Query client configuration
   - Create useSchedule hook skeleton
   - Create usePeople hook skeleton

Reference backend/app/routes/ for API endpoint signatures.
Haiku is creating types in frontend/types/api.ts - import from there once available.
Do not create components - Haiku is handling Modal and form inputs.
```

#### Haiku - Phase 1
```
Project: Residency Scheduler
Reference: TODO_HAIKU.md (contains exact templates)

Execute these tasks - follow templates EXACTLY:

1. Create frontend/types/api.ts
   - Copy the type definitions from TODO_HAIKU.md Task 1
   - Generate types for: Person, Block, Assignment, Absence, RotationTemplate, ScheduleRun
   - Reference backend/app/models/ for field names

2. Create frontend/components/Modal.tsx
   - Copy the exact template from TODO_HAIKU.md Task 2
   - Do not modify the template

3. Create frontend/components/forms/Input.tsx
   - Copy exact template from TODO_HAIKU.md Task 3a

4. Create frontend/components/forms/Select.tsx
   - Copy exact template from TODO_HAIKU.md Task 3b

5. Create frontend/components/forms/TextArea.tsx
   - Copy exact template from TODO_HAIKU.md Task 3c

6. Create frontend/components/forms/index.ts
   - Barrel export all form components

Report when complete. Do not touch frontend/lib/ - Sonnet is working there.
```

---

### Phase 2 Prompts

#### Opus - Phase 2
```
Project: Residency Scheduler
Previous: Auth and Error docs should be complete

Execute these review and research tasks:

1. Review Sonnet's Work
   - Read frontend/lib/api.ts
   - Check: error handling, type safety, no 'any' types
   - Provide feedback if issues found

2. Design Caching Strategy
   - Define React Query cache times for each entity type
   - Design cache invalidation rules
   - Document in docs/CACHING_STRATEGY.md

3. Scheduling Algorithm Research
   - Read backend/app/scheduling/engine.py
   - Analyze complexity and bottlenecks
   - Research OR-Tools/CP-SAT as alternatives
   - Begin docs/SCHEDULING_OPTIMIZATION.md

Sonnet is implementing hooks. Haiku is creating skeletons.
```

#### Sonnet - Phase 2
```
Project: Residency Scheduler
Dependency: Haiku's types should be in frontend/types/api.ts

Implement React Query hooks in frontend/lib/hooks.ts:

1. useSchedule(startDate: Date, endDate: Date)
   - GET /api/assignments with date params
   - Cache key: ['schedule', startDate.toISOString(), endDate.toISOString()]
   - Refetch on window focus

2. usePeople(filters?: { role?: string, pgy_level?: number })
   - GET /api/people with optional query params
   - Cache key: ['people', filters]

3. useAbsences(personId?: number)
   - GET /api/absences with optional person filter
   - Cache key: ['absences', personId]

4. useRotationTemplates()
   - GET /api/rotation-templates
   - Cache key: ['rotation-templates']
   - Stale time: 10 minutes

5. Mutation hooks:
   - useCreatePerson, useUpdatePerson, useDeletePerson
   - Invalidate ['people'] on success

Import types from '@/types/api'.
Haiku is creating skeletons - do not create loading components.
```

#### Haiku - Phase 2
```
Project: Residency Scheduler
Reference: TODO_HAIKU.md Task 4

Create loading skeleton components - follow templates EXACTLY:

1. Create frontend/components/skeletons/CardSkeleton.tsx
   - Copy template from TODO_HAIKU.md

2. Create frontend/components/skeletons/TableRowSkeleton.tsx
   - Copy template from TODO_HAIKU.md

3. Create frontend/components/skeletons/CalendarSkeleton.tsx
   - Copy template from TODO_HAIKU.md

4. Create frontend/components/skeletons/index.ts
   - Barrel export all skeletons

Then scaffold test files:

5. Create frontend/__tests__/hooks/useSchedule.test.ts
   - Use template from TODO_HAIKU.md Task 5

6. Create frontend/__tests__/hooks/usePeople.test.ts
7. Create frontend/__tests__/hooks/useAbsences.test.ts

Report completion to allow Sonnet to use skeletons in pages.
```

---

### Phase 3 Prompts

#### Opus - Phase 3
```
Project: Residency Scheduler
Focus: Quality review and ACGME compliance

1. Review Compliance Page Logic
   - Read frontend/app/compliance/page.tsx (after Sonnet wires it)
   - Verify ACGME rules are displayed correctly
   - Check: 80-hour rule, 1-in-7 day rule, supervision ratios

2. Security Review
   - Review all API calls for proper error handling
   - Check for data exposure risks
   - Verify no sensitive data in client state

3. Provide Implementation Guidance
   - If Sonnet has questions in escalation queue, address them
   - Make decisions on any architectural blockers

Document any issues found for Sonnet to fix.
```

#### Sonnet - Phase 3
```
Project: Residency Scheduler
Dependencies: Hooks and components from Phase 2

Wire pages to API:

1. frontend/app/page.tsx (Home)
   - Import useSchedule hook
   - Replace mock data with API data
   - Add CalendarSkeleton while loading
   - Add error state with retry

2. frontend/app/people/page.tsx
   - Import usePeople hook
   - Add filter dropdowns (role, PGY level)
   - Wire "Add Person" button to modal
   - Add CardSkeleton while loading

3. frontend/components/AddPersonModal.tsx
   - Use Modal from components/Modal
   - Use form inputs from components/forms
   - Use useCreatePerson mutation
   - Validate: name required, email format, PGY 1-3 for residents

4. frontend/app/compliance/page.tsx
   - Fetch validation results
   - Display ACGME violations
   - Show compliance metrics

Opus will review compliance logic for accuracy.
```

#### Haiku - Phase 3
```
Project: Residency Scheduler
Support tasks while Sonnet does integration:

1. Add any missing types discovered during integration
   - If Sonnet reports missing types, add them to frontend/types/api.ts

2. Create additional skeleton components if needed
   - PersonCardSkeleton
   - ComplianceCardSkeleton

3. Update barrel exports
   - Ensure all new components are exported from index files

4. Fix any import issues
   - If files were moved or renamed, update imports

Stand by for requests from Sonnet. Report any issues immediately.
```

---

## Monitoring Parallel Execution

### Status Check Prompts

**Check Opus Progress:**
```
What is your current status?
- What tasks have you completed?
- What are you currently working on?
- Any blockers or decisions needed?
- Any feedback for Sonnet/Haiku?
```

**Check Sonnet Progress:**
```
What is your current status?
- What tasks have you completed?
- What are you currently working on?
- Any blockers requiring Opus decision?
- Any tasks to delegate to Haiku?
```

**Check Haiku Progress:**
```
What is your current status?
- List all files created
- Any templates that didn't fit?
- Any errors encountered?
- Ready for next batch?
```

---

## Conflict Resolution

### If Models Touch Same File

**Situation:** Both Sonnet and Haiku edited `frontend/types/api.ts`

**Resolution Prompt (to Sonnet):**
```
Haiku has been adding types to frontend/types/api.ts.
Pull the latest version and merge your changes.
Haiku's types are the source of truth for entity shapes.
Add your custom types (like hook return types) in a separate section.
```

### If Dependency Not Ready

**Situation:** Sonnet needs types but Haiku hasn't finished

**Resolution Prompt (to Sonnet):**
```
Haiku is still working on types. While waiting:
1. Create a temporary types.ts in lib/ with the types you need
2. Add a TODO comment: "// TODO: Import from @/types/api when available"
3. Continue with hook implementation
4. We'll consolidate types later
```

### If Architectural Decision Needed Mid-Task

**Situation:** Sonnet encounters design question

**Escalation Prompt (to Opus):**
```
URGENT: Sonnet needs architectural guidance.

Question: [paste Sonnet's question]

Please provide:
1. Your decision
2. Brief rationale
3. Any patterns to follow

Keep response concise - Sonnet is waiting.
```

---

## Efficiency Tips

### DO:
- Start all three models at the same time for Phase 1
- Give Haiku the most specific templates possible
- Let Opus review while Sonnet implements
- Have Haiku scaffold ahead of what Sonnet needs

### DON'T:
- Wait for Opus to finish design before starting Sonnet on unrelated features
- Have multiple models edit the same file simultaneously
- Give Haiku tasks requiring decisions
- Skip the Phase 1 foundation work

### Optimal Model Utilization:
```
Time →
     ┌─────────────────────────────────────────────────────────────┐
Opus │████ Design ████│░░░ Review ░░░│████ Design ████│░░ Review ░░│
     ├─────────────────────────────────────────────────────────────┤
Son. │████████████ Implement █████████████████████████████████████│
     ├─────────────────────────────────────────────────────────────┤
Haiku│██ Gen ██│██ Gen ██│░ Wait ░│██ Gen ██│██ Gen ██│░░ Cleanup ░│
     └─────────────────────────────────────────────────────────────┘

████ = Active work
░░░░ = Light work / review / standby
```

---

## Quick Reference Card

### Start Parallel Work:
```
Terminal 1 (Opus):  "Read TODO_OPUS.md. Start with Task 1: Auth Architecture Design."
Terminal 2 (Sonnet): "Read TODO_SONNET.md. Start with Task 1: API Client Base."
Terminal 3 (Haiku):  "Read TODO_HAIKU.md. Start with Task 1: Generate API Types."
```

### Check Status:
```
All models: "What is your current status? List completed and in-progress tasks."
```

### Handoff:
```
Opus → Sonnet: "Auth design complete. See docs/AUTH_ARCHITECTURE.md. Implement per spec."
Sonnet → Haiku: "Need 5 more skeleton components. Templates: [provide exact code]"
Haiku → Sonnet: "Types complete in frontend/types/api.ts. Ready for import."
```

### Escalate:
```
Haiku → Sonnet: "Template doesn't fit [situation]. Need guidance."
Sonnet → Opus: "Architectural decision needed: [question]. Options: A or B."
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Haiku deviates from template | Re-prompt with stricter instructions: "Copy EXACTLY, no modifications" |
| Sonnet blocked on Opus decision | Have Sonnet work on independent task while waiting |
| Opus doing implementation | Redirect: "Design only. Document in markdown. Sonnet implements." |
| Merge conflicts | Designate one model as owner of conflicted file |
| Model forgot context | Re-share the relevant TODO_*.md file |

---

*Last Updated: 2024-12-13*
*Version: 1.0*
