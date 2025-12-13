***REMOVED*** OPUS 4.5 Task List

***REMOVED******REMOVED*** Role: The Architect & Strategic Director

You are the strategic brain of this project. Your job is to think deeply, make critical decisions, review quality, and intervene when the other models need guidance.

---

***REMOVED******REMOVED*** Active Strategic Tasks

***REMOVED******REMOVED******REMOVED*** 1. Authentication Architecture Design
**Priority: HIGH** | **Status: NOT STARTED**

Design the complete authentication and authorization system.

**Deliverables:**
- [ ] Choose auth strategy (JWT vs session-based)
- [ ] Design token refresh mechanism
- [ ] Define role hierarchy (admin, coordinator, faculty, resident)
- [ ] Map permissions to roles
- [ ] Design protected route middleware pattern
- [ ] Create auth flow diagram

**Technical Considerations:**
- FastAPI already has `python-jose` and `passlib` installed
- Frontend needs to store tokens securely
- Consider HttpOnly cookies vs localStorage tradeoffs
- ACGME compliance audit trail needs user tracking

**Output:** Create `docs/AUTH_ARCHITECTURE.md` with complete design, then delegate implementation to Sonnet.

---

***REMOVED******REMOVED******REMOVED*** 2. API Error Handling Strategy
**Priority: HIGH** | **Status: NOT STARTED**

Define unified error handling across frontend and backend.

**Deliverables:**
- [ ] Define error response schema (code, message, details)
- [ ] Map backend exceptions to HTTP status codes
- [ ] Design frontend error boundary strategy
- [ ] Define retry logic for transient failures
- [ ] Plan user-facing error messages

**Output:** Document in `docs/ERROR_HANDLING.md`, provide to Sonnet for implementation.

---

***REMOVED******REMOVED******REMOVED*** 3. Database Schema Review
**Priority: MEDIUM** | **Status: NOT STARTED**

Review current schema for completeness and optimization opportunities.

**Files to Review:**
- `backend/app/models/person.py`
- `backend/app/models/block.py`
- `backend/app/models/assignment.py`
- `backend/app/models/absence.py`
- `backend/app/models/rotation_template.py`

**Considerations:**
- [ ] Verify indexes on frequently queried columns
- [ ] Check foreign key cascade behaviors
- [ ] Validate ACGME constraint enforcement at DB level
- [ ] Review for N+1 query potential
- [ ] Assess need for materialized views for reporting

**Output:** Document findings and create migration plan if changes needed.

---

***REMOVED******REMOVED******REMOVED*** 4. Scheduling Algorithm Optimization
**Priority: MEDIUM** | **Status: NOT STARTED**

Evaluate current greedy algorithm and design improvements.

**File to Review:** `backend/app/scheduling/engine.py`

**Tasks:**
- [ ] Analyze current algorithm complexity
- [ ] Identify bottlenecks for large datasets (100+ residents)
- [ ] Research constraint satisfaction alternatives (CP-SAT, OR-Tools)
- [ ] Design benchmark suite
- [ ] Recommend optimization path

**Output:** `docs/SCHEDULING_OPTIMIZATION.md` with recommendations.

---

***REMOVED******REMOVED*** Review Queue (Pending Sonnet Completion)

***REMOVED******REMOVED******REMOVED*** Awaiting Review
| Item | Sonnet Task | Priority | Review Focus |
|------|-------------|----------|--------------|
| API Client | `frontend/lib/api.ts` | HIGH | Error handling, type safety |
| Schedule Hook | `useSchedule()` hook | HIGH | Caching strategy, edge cases |
| ACGME UI Logic | Compliance page | HIGH | Validation accuracy |
| Emergency Coverage | Coverage replacement UI | MEDIUM | Edge case handling |

***REMOVED******REMOVED******REMOVED*** Review Checklist Template
When reviewing Sonnet's work:
- [ ] Matches architectural guidelines
- [ ] Error handling is comprehensive
- [ ] No security vulnerabilities
- [ ] Types are strict (no `any`)
- [ ] Edge cases considered
- [ ] ACGME logic is accurate

---

***REMOVED******REMOVED*** Intervention Triggers

**Step in immediately if Sonnet reports:**
- "I'm not sure which approach to take"
- "This affects multiple components"
- "Security concern about..."
- "The ACGME validation logic..."
- "Performance issue with..."

**Proactively check on:**
- Any authentication-related code
- Database migration changes
- Scheduling algorithm modifications
- API contract changes

---

***REMOVED******REMOVED*** Decision Log

Track major decisions here for project continuity.

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| TBD | Auth strategy | TBD | System-wide |
| TBD | Error schema | TBD | All API endpoints |

---

***REMOVED******REMOVED*** Communication Templates

***REMOVED******REMOVED******REMOVED*** Delegating to Sonnet
```markdown
***REMOVED******REMOVED*** Task: [Name]
***REMOVED******REMOVED******REMOVED*** Context
[Why this matters to the project]

***REMOVED******REMOVED******REMOVED*** Requirements
- [Specific requirement]

***REMOVED******REMOVED******REMOVED*** Technical Guidance
- Pattern: [reference existing code]
- Avoid: [anti-pattern]

***REMOVED******REMOVED******REMOVED*** Acceptance Criteria
- [ ] Criterion

***REMOVED******REMOVED******REMOVED*** Escalate If
- [Condition requiring Opus review]
```

***REMOVED******REMOVED******REMOVED*** Requesting Haiku Batch Work (via Sonnet)
```markdown
***REMOVED******REMOVED*** Batch Task: [Name]
***REMOVED******REMOVED******REMOVED*** Template
[Exact pattern to follow]

***REMOVED******REMOVED******REMOVED*** Items (N total)
1. [Item 1]
2. [Item 2]
...

***REMOVED******REMOVED******REMOVED*** Constraints
- No deviations from template
- Report any anomalies
```

---

***REMOVED******REMOVED*** Weekly Focus Areas

***REMOVED******REMOVED******REMOVED*** This Sprint
1. Complete authentication architecture design
2. Review API client implementation from Sonnet
3. Define error handling strategy

***REMOVED******REMOVED******REMOVED*** Next Sprint
1. Scheduling algorithm optimization research
2. Review authentication implementation
3. Security audit of completed features

---

***REMOVED******REMOVED*** Notes & Observations

*Use this section to capture insights during code review and planning.*

---

*Last Updated: 2024-12-13*
