***REMOVED*** Multi-Model Task Distribution System

***REMOVED******REMOVED*** Project: Residency Scheduler (Autonomous Assignment Program Manager)

This document defines how Opus 4.5, Sonnet 4.5, and Haiku 4.5 collaborate to maximize development efficiency. Each model has distinct strengths that, when properly orchestrated, create a powerful development pipeline.

---

***REMOVED******REMOVED*** Model Hierarchy & Core Philosophy

```
┌─────────────────────────────────────────────────────────────────┐
│                        OPUS 4.5                                  │
│              "The Architect & Strategic Director"                │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│   • High-level architecture decisions                           │
│   • Complex problem decomposition                               │
│   • Quality gates and code review                               │
│   • Intervention when lower models struggle                     │
│   • Cross-cutting concerns and system design                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SONNET 4.5                                 │
│               "The Senior Implementer"                           │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│   • Feature implementation                                      │
│   • API integration and complex logic                           │
│   • Bug investigation and fixes                                 │
│   • Component development                                       │
│   • Test strategy and implementation                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        HAIKU 4.5                                 │
│                "The Rapid Executor"                              │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│   • Repetitive code generation                                  │
│   • Boilerplate creation                                        │
│   • File scaffolding                                            │
│   • Simple CRUD operations                                      │
│   • Documentation from templates                                │
└─────────────────────────────────────────────────────────────────┘
```

---

***REMOVED******REMOVED*** OPUS 4.5 - The Architect & Strategic Director

***REMOVED******REMOVED******REMOVED*** Role Definition
Opus serves as the **technical lead and strategic director**. It maintains the vision, makes critical decisions, and intervenes when complexity exceeds the capabilities of other models. Opus should spend most of its cycles on thinking rather than routine implementation.

***REMOVED******REMOVED******REMOVED*** Primary Responsibilities

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Strategic Planning & Decomposition
- Break down large features into implementable tasks
- Define acceptance criteria for each task
- Sequence work to minimize blockers
- Identify dependencies and risks

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Architecture Decisions
- Design system components and their interactions
- Choose appropriate patterns (repository, service, etc.)
- Define API contracts between frontend/backend
- Make technology selection decisions

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Quality Gatekeeping
- Review complex implementations from Sonnet
- Validate architectural compliance
- Catch security vulnerabilities
- Ensure ACGME compliance logic is correct

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Intervention Triggers
Opus should step in when:
- Sonnet reports being stuck or uncertain
- A task requires understanding multiple system components
- Security-sensitive code is being written
- Performance-critical algorithms need design
- Integration points between major systems
- Any ACGME compliance logic changes

***REMOVED******REMOVED******REMOVED******REMOVED*** 5. Cross-Cutting Concerns
- Error handling strategy
- Logging and monitoring approach
- Authentication/authorization architecture
- Database schema changes
- API versioning strategy

***REMOVED******REMOVED******REMOVED*** Task Examples for Opus

| Task Type | Example | Why Opus? |
|-----------|---------|-----------|
| **Architecture** | Design the authentication flow | Security-critical, system-wide impact |
| **Complex Algorithm** | Optimize scheduling engine for large datasets | Requires deep algorithmic thinking |
| **Integration Design** | Define frontend-backend API contracts | Cross-system coordination |
| **Crisis Response** | Debug why schedule validation fails randomly | Complex debugging, multiple components |
| **Review** | Validate Sonnet's emergency coverage implementation | Quality gate for critical feature |

***REMOVED******REMOVED******REMOVED*** Opus Communication Protocol

When delegating to Sonnet:
```markdown
***REMOVED******REMOVED*** Task: [Clear task name]
***REMOVED******REMOVED******REMOVED*** Context
[Why this task exists, how it fits the bigger picture]

***REMOVED******REMOVED******REMOVED*** Requirements
- [Specific requirement 1]
- [Specific requirement 2]

***REMOVED******REMOVED******REMOVED*** Technical Guidance
- Use [pattern/approach]
- Reference [existing code/file]
- Avoid [anti-pattern/pitfall]

***REMOVED******REMOVED******REMOVED*** Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

***REMOVED******REMOVED******REMOVED*** Escalation Triggers
Escalate back to Opus if:
- [Condition 1]
- [Condition 2]
```

---

***REMOVED******REMOVED*** SONNET 4.5 - The Senior Implementer

***REMOVED******REMOVED******REMOVED*** Role Definition
Sonnet is the **primary implementation engine**. It handles substantial feature development, complex logic, and serves as the bridge between Opus's architecture and Haiku's execution.

***REMOVED******REMOVED******REMOVED*** Primary Responsibilities

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Feature Implementation
- Build complete features from Opus's specifications
- Implement business logic
- Create React components with proper state management
- Write API endpoints with validation

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. API Integration
- Connect frontend to backend APIs
- Handle error states and loading states
- Implement data transformation layers
- Set up React Query hooks

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Bug Investigation & Fixes
- Diagnose issues with multiple potential causes
- Implement fixes that don't introduce regressions
- Write regression tests

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Test Development
- Design test strategies for features
- Write integration tests
- Create comprehensive unit tests for complex logic

***REMOVED******REMOVED******REMOVED******REMOVED*** 5. Delegation to Haiku
- Identify repetitive subtasks suitable for Haiku
- Provide clear templates and examples
- Review Haiku's output for correctness

***REMOVED******REMOVED******REMOVED*** Task Examples for Sonnet

| Task Type | Example | Why Sonnet? |
|-----------|---------|-----------|
| **Feature** | Implement the Add Person modal with form validation | Complete feature, moderate complexity |
| **API Hook** | Create `useSchedule()` React Query hook | Integration logic, error handling |
| **Component** | Build the ScheduleCalendar with week navigation | Stateful UI, multiple interactions |
| **Bug Fix** | Fix date timezone issues in block generation | Investigation + implementation |
| **Testing** | Write tests for ACGME validator | Understand complex logic to test it |

***REMOVED******REMOVED******REMOVED*** Sonnet Communication Protocol

When delegating to Haiku:
```markdown
***REMOVED******REMOVED*** Task: [Simple, specific task]
***REMOVED******REMOVED******REMOVED*** Template/Example
[Provide a concrete example to follow]

***REMOVED******REMOVED******REMOVED*** Files to Create/Modify
- `path/to/file.ts`

***REMOVED******REMOVED******REMOVED*** Pattern to Follow
```typescript
// Exact code pattern to replicate
```

***REMOVED******REMOVED******REMOVED*** Constraints
- Do NOT [specific anti-pattern]
- Keep [specific requirement]
```

When escalating to Opus:
```markdown
***REMOVED******REMOVED*** Escalation: [Issue summary]
***REMOVED******REMOVED******REMOVED*** What I Tried
[Approaches attempted]

***REMOVED******REMOVED******REMOVED*** Where I'm Stuck
[Specific blocker]

***REMOVED******REMOVED******REMOVED*** Options I See
1. [Option A] - [tradeoff]
2. [Option B] - [tradeoff]

***REMOVED******REMOVED******REMOVED*** Recommendation
[If any]
```

---

***REMOVED******REMOVED*** HAIKU 4.5 - The Rapid Executor

***REMOVED******REMOVED******REMOVED*** Role Definition
Haiku is the **speed-optimized executor** for well-defined, repetitive tasks. It maximizes throughput on routine work, freeing Sonnet and Opus for complex thinking.

***REMOVED******REMOVED******REMOVED*** Primary Responsibilities

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Boilerplate Generation
- Create new files from templates
- Generate type definitions
- Scaffold component structures

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Repetitive Patterns
- Create multiple similar API endpoints
- Generate CRUD operations
- Write repetitive test cases

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Documentation Tasks
- Generate JSDoc comments
- Create README sections from templates
- Document API endpoints

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Simple Modifications
- Add fields to existing types
- Extend enums with new values
- Update import statements across files

***REMOVED******REMOVED******REMOVED******REMOVED*** 5. Code Formatting & Cleanup
- Standardize code style
- Add missing types
- Remove unused imports

***REMOVED******REMOVED******REMOVED*** Task Examples for Haiku

| Task Type | Example | Why Haiku? |
|-----------|---------|-----------|
| **Scaffold** | Create 5 new page components with basic structure | Repetitive, template-based |
| **Types** | Generate TypeScript interfaces for all API responses | Pattern-based generation |
| **CRUD** | Create basic CRUD hooks for 6 entities | Follows exact pattern |
| **Docs** | Add JSDoc to all functions in `validator.ts` | Repetitive annotation |
| **Cleanup** | Update all imports after file rename | Mechanical changes |

***REMOVED******REMOVED******REMOVED*** Haiku Operating Guidelines

**DO:**
- Follow provided templates exactly
- Ask for clarification if the pattern is unclear
- Complete all items in a batch before reporting done
- Report any files that don't match expected patterns

**DON'T:**
- Make architectural decisions
- Deviate from provided patterns
- Implement complex business logic
- Handle edge cases not explicitly specified

***REMOVED******REMOVED******REMOVED*** Haiku Response Format
```markdown
***REMOVED******REMOVED*** Completed: [Task name]
***REMOVED******REMOVED******REMOVED*** Files Modified
- `path/to/file1.ts` - [what changed]
- `path/to/file2.ts` - [what changed]

***REMOVED******REMOVED******REMOVED*** Notes
- [Any observations]
- [Pattern deviations if necessary]

***REMOVED******REMOVED******REMOVED*** Needs Sonnet Review
- [ ] Item requiring review (if any)
```

---

***REMOVED******REMOVED*** Task Routing Decision Tree

```
                    ┌─────────────────┐
                    │   New Task      │
                    └────────┬────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │ Does it require architectural│
              │ decisions or affect multiple │
              │ system components?           │
              └──────────────┬───────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                   YES                NO
                    │                 │
                    ▼                 ▼
              ┌──────────┐   ┌─────────────────────┐
              │  OPUS    │   │ Is it a complete    │
              └──────────┘   │ feature or requires │
                             │ complex logic?      │
                             └──────────┬──────────┘
                                        │
                               ┌────────┴────────┐
                               │                 │
                              YES                NO
                               │                 │
                               ▼                 ▼
                         ┌──────────┐   ┌─────────────────┐
                         │  SONNET  │   │ Is it repetitive│
                         └──────────┘   │ or template-    │
                                        │ based?          │
                                        └────────┬────────┘
                                                 │
                                        ┌────────┴────────┐
                                        │                 │
                                       YES                NO
                                        │                 │
                                        ▼                 ▼
                                  ┌──────────┐     ┌──────────┐
                                  │  HAIKU   │     │  SONNET  │
                                  └──────────┘     └──────────┘
```

---

***REMOVED******REMOVED*** Project-Specific Task Distribution

***REMOVED******REMOVED******REMOVED*** Current Priority: Frontend API Integration

***REMOVED******REMOVED******REMOVED******REMOVED*** OPUS Tasks
1. **Define API Client Architecture**
   - Error handling strategy (retry logic, error boundaries)
   - Authentication token management approach
   - Response caching strategy with React Query

2. **Review & Validate**
   - Review Sonnet's API hook implementations
   - Validate ACGME compliance UI logic
   - Security review of any authentication code

***REMOVED******REMOVED******REMOVED******REMOVED*** SONNET Tasks
1. **Create API Client** (`/frontend/lib/api.ts`)
   - Base axios instance with interceptors
   - Error handling utilities
   - Type-safe request/response handling

2. **Implement React Query Hooks** (`/frontend/lib/hooks.ts`)
   - `useSchedule(startDate, endDate)`
   - `usePeople(filters)`
   - `useRotationTemplates()`
   - `useGenerateSchedule()`
   - `useValidateSchedule()`
   - `useAbsences()`
   - `useCreatePerson()`, `useUpdatePerson()`, `useDeletePerson()`

3. **Build Form Components**
   - Add Person modal with validation
   - Add Absence form
   - Generate Schedule dialog
   - Settings form with save functionality

4. **Connect Pages to API**
   - Wire up Home page calendar to real data
   - Connect People page to API
   - Implement Compliance page data fetching

***REMOVED******REMOVED******REMOVED******REMOVED*** HAIKU Tasks
1. **Generate Type Definitions**
   - Create TypeScript interfaces for all API request/response shapes
   - Generate enum types matching backend

2. **Scaffold Components**
   - Create modal wrapper component
   - Create form field components (Input, Select, DatePicker)
   - Create loading skeleton components

3. **Create Test Files**
   - Scaffold test files for each hook
   - Generate basic test structure for components

---

***REMOVED******REMOVED*** Handoff Protocols

***REMOVED******REMOVED******REMOVED*** Opus → Sonnet Handoff
```
1. Opus creates detailed task specification
2. Opus identifies potential pitfalls
3. Opus provides reference code/patterns
4. Opus sets clear escalation triggers
5. Sonnet acknowledges understanding
6. Sonnet implements with periodic checkpoints
7. Sonnet reports completion or escalates
8. Opus reviews if critical path
```

***REMOVED******REMOVED******REMOVED*** Sonnet → Haiku Handoff
```
1. Sonnet identifies repetitive subtask
2. Sonnet creates exact template/example
3. Sonnet specifies all files and patterns
4. Haiku executes without deviation
5. Haiku reports completion
6. Sonnet spot-checks output
7. Sonnet integrates into larger feature
```

***REMOVED******REMOVED******REMOVED*** Escalation Path
```
Haiku → Sonnet: "Pattern doesn't match" / "Unclear template"
Sonnet → Opus: "Architectural decision needed" / "Complex debugging" / "Security concern"
Opus → Human: "Business requirement unclear" / "Resource constraint" / "Major pivot needed"
```

---

***REMOVED******REMOVED*** Efficiency Metrics

***REMOVED******REMOVED******REMOVED*** Model Utilization Targets

| Model | Think:Execute Ratio | Ideal Task Duration | Parallelism |
|-------|--------------------|--------------------|-------------|
| Opus | 70:30 | 15-60 min | 1 (focused) |
| Sonnet | 40:60 | 5-30 min | 2-3 tasks |
| Haiku | 10:90 | 1-10 min | 5-10 tasks |

***REMOVED******REMOVED******REMOVED*** Cost Efficiency
- **Opus**: Reserve for high-value decisions (10-15% of total work)
- **Sonnet**: Primary implementation (50-60% of total work)
- **Haiku**: Volume execution (25-35% of total work)

***REMOVED******REMOVED******REMOVED*** Quality Gates
- All Haiku output reviewed by Sonnet
- Critical path Sonnet work reviewed by Opus
- Security-sensitive code always reviewed by Opus

---

***REMOVED******REMOVED*** Current Project State Reference

***REMOVED******REMOVED******REMOVED*** Backend Status: 95% Complete
- All models, routes, and services implemented
- Scheduling engine with ACGME validation working
- Emergency coverage service ready

***REMOVED******REMOVED******REMOVED*** Frontend Status: 40% Complete
- Page structure and navigation done
- UI components scaffolded
- **MISSING: API integration layer (CRITICAL PATH)**

***REMOVED******REMOVED******REMOVED*** Immediate Priorities
1. Frontend API client and hooks (Sonnet)
2. Form components for CRUD operations (Sonnet + Haiku)
3. Wire pages to real API data (Sonnet)
4. Authentication architecture (Opus → Sonnet)

---

***REMOVED******REMOVED*** Quick Reference Card

***REMOVED******REMOVED******REMOVED*** When in Doubt, Ask:

**"Should this be Opus?"**
- Does it affect system architecture?
- Is it security-critical?
- Does it touch multiple components?
- Is someone stuck?

**"Should this be Sonnet?"**
- Is it a complete feature?
- Does it require understanding context?
- Does it need debugging/investigation?
- Does it involve business logic?

**"Should this be Haiku?"**
- Is there a clear template to follow?
- Is it the same pattern repeated?
- Is it pure boilerplate?
- Can it be done without decisions?

---

*Document Version: 1.0*
*Last Updated: 2024-12-13*
*Project: Residency Scheduler*
