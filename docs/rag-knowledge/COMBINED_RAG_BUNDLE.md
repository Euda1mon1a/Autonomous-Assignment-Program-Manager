# Residency Scheduler Knowledge Base

> **Combined RAG Bundle**
> **Version:** 2026-01-10
> **Total Sections:** 13 documents
> **Purpose:** Single-file knowledge base for RAG ingestion

---

# TABLE OF CONTENTS

1. [ACGME Rules](#section-1-acgme-rules)
2. [Scheduling Policies](#section-2-scheduling-policies)
3. [Swap System](#section-3-swap-system)
4. [Resilience Concepts](#section-4-resilience-concepts)
5. [Delegation Patterns](#section-5-delegation-patterns)
6. [User Guide FAQ](#section-6-user-guide-faq)
7. [Agent Capabilities](#section-7-agent-capabilities)
8. [Session Protocols](#section-8-session-protocols)
9. [Session Learnings](#section-9-session-learnings)
10. [Exotic Concepts](#section-10-exotic-concepts)
11. [Architecture Overview](#section-11-architecture-overview)
12. [API Patterns](#section-12-api-patterns)
13. [Troubleshooting Guide](#section-13-troubleshooting-guide)

---

# SECTION 1: ACGME RULES

## ACGME Duty Hour Requirements

### Maximum Work Hours

**80-Hour Maximum Work Week:**
- Residents must not exceed **80 hours per week** averaged over **4-week rolling period**
- Includes clinical work, educational activities, administrative duties, moonlighting
- Does NOT include personal study, voluntary research outside scheduled time

**What Counts:** Direct patient care, conferences, admin duties, in-house call (including sleep), moonlighting

### Mandatory Time Off

**1-in-7 Rule:**
- At least one **24-hour period free** every 7 days (averaged over 4 weeks)
- Must be continuous 24-hour period
- Cannot be scheduled immediately before/after night float

**Minimum Rest Between Shifts:**
- **10 hours free** between scheduled clinical work periods
- May remain on-site 4 additional hours after 24-hour shift for continuity

### Maximum Shift Length

- **24 consecutive hours** maximum clinical duty
- **+4 hours** for continuity of care and handoff (28 hours total)
- **Every 3rd night** maximum in-house call frequency (4-week average)

### PGY-1 Specific Restrictions

- **16 hours maximum** shift length (strict limit, no exceptions)
- Enhanced supervision required
- Cannot take independent home call

### Supervision Ratios

- **1:2** faculty-to-PGY-1 supervision ratio
- **1:4** faculty-to-PGY-2/3 supervision ratio

### Key Numbers Summary

| Limit | Value |
|-------|-------|
| Weekly hours (4-week avg) | 80 hours max |
| Day off per 7 days (4-week avg) | 1 day minimum |
| Rest between shifts | 10 hours min |
| Maximum shift | 24 + 4 hours |
| In-house call frequency | Every 3rd night max |
| PGY-1 max shift | 16 hours |

---

# SECTION 2: SCHEDULING POLICIES

## Block Structure

- **Academic Year:** 365 days (366 leap year)
- **Total Blocks:** 730 blocks per year
- **Block Definition:** AM (7 AM - 7 PM) and PM (7 PM - 7 AM)

## Rotation Types

1. **Inpatient:** Wards, subspecialty, ICU (24/7 coverage)
2. **Outpatient:** Continuity clinic, subspecialty clinics
3. **Procedure:** Endoscopy, cath lab, OR
4. **Night Float:** Dedicated overnight coverage (1-2 weeks)
5. **Elective:** Resident-selected, research, away rotations
6. **Conference/Education:** Protected educational time

## Coverage Requirements

**Minimum Staffing:**
- Day: 1 resident per 8-10 patients
- Night: 1 resident per 15-20 patients
- ICU: 1 resident per 6-8 patients

**Coverage Gap Prevention:**
- Real-time gap detection
- Automated conflict resolution
- N-1/N-2 contingency planning

## Schedule Publication Timeline

- **4-6 weeks:** Core rotations published
- **2-3 weeks:** Call and weekend coverage finalized
- **1 week:** Final adjustments

---

# SECTION 3: SWAP SYSTEM

## Swap Types

**One-to-One Swap:** Two individuals exchange equivalent blocks (bilateral trade)
**Absorb Swap:** One person gives away shift without receiving anything in return
**Partial Swap:** Exchange only part of assignment

## Swap Request Process

1. **Initiate:** Select shift, choose swap type
2. **Find Partner:** Auto-matcher, direct request, or swap board
3. **Partner Accepts:** 48 hours to respond
4. **System Validation:** ACGME compliance, coverage, credentials
5. **Approval Workflow:** Tier 1-4 based on timing/complexity
6. **Execution:** Schedule updated, notifications sent

## Auto-Matcher Compatibility Factors

- 100%: Perfect swap, no issues
- 80-99%: Good swap, minor considerations
- 60-79%: Acceptable, some limitations
- <60%: Challenging, may require override

## 24-Hour Rollback Window

- Either party can cancel within 24 hours
- After 24 hours: requires new approval
- Emergency cancellations always permitted

## Swap Frequency Limits

- **Per month:** Maximum 4 requests
- **Per block:** Maximum 2 swaps
- **Per year:** Maximum 20 swaps

---

# SECTION 4: RESILIENCE CONCEPTS

## 80% Utilization Threshold

From queuing theory: systems above 80% capacity experience non-linear degradation.

- **Below 80%:** Absorbs variations smoothly
- **80-90%:** Performance degradation noticeable
- **90-95%:** Minor disruptions cause major delays
- **Above 95%:** Constant crisis mode

## N-1/N-2 Contingency Analysis

From power grid engineering:

**N-1:** Can schedule survive loss of any single resident?
**N-2:** Can critical services survive loss of any two residents?

## Defense in Depth (5 Levels)

| Level | Conditions | Actions |
|-------|-----------|---------|
| GREEN | <75% utilization, passes N-2 | Normal operations |
| YELLOW | 75-85% utilization, fails N-2 | Increase monitoring |
| ORANGE | 85-95% utilization, fails N-1 | Implement mitigations |
| RED | 90%+ utilization, ACGME violations | Emergency interventions |
| BLACK | System failure, patient safety | Crisis management |

## Sacrifice Hierarchy (Load Shedding)

**Tier 1 (Never Sacrifice):** ED, ICU, inpatient, required conferences
**Tier 2 (Sacrifice If Necessary):** Subspecialty consults, procedures
**Tier 3 (Sacrifice Before Higher):** Elective procedures, non-urgent clinics
**Tier 4 (Sacrifice First):** Research, professional development

## Burnout Epidemiology (SIR Model)

- **Rt > 1:** Burnout spreading (epidemic)
- **Rt = 1:** Stable (endemic)
- **Rt < 1:** Declining (containment)

---

# SECTION 5: DELEGATION PATTERNS

## Auftragstaktik (Mission-Type Orders)

**Principle:** Higher level provides intent, lower level decides how.

**Litmus Test:**
- Recipe = micromanaging
- Mission orders = delegating

## 99/1 Rule

**ORCHESTRATOR delegates 99% of the time. Direct action is the 1% nuclear option.**

Decision Gate: Before using Read/Edit/Write/Bash directly, ask "Which Deputy handles this domain?"

## Routing Table

| Task Domain | Spawn |
|-------------|-------|
| Database, API, infrastructure | ARCHITECT → COORD_PLATFORM |
| Tests, code quality, CI | ARCHITECT → COORD_QUALITY |
| Scheduling engine | ARCHITECT → COORD_ENGINE |
| Documentation, releases | SYNTHESIZER → COORD_OPS |
| Resilience, compliance | SYNTHESIZER → COORD_RESILIENCE |
| Frontend, UX | SYNTHESIZER → COORD_FRONTEND |

## Embarrassingly Parallel Pattern

**Anti-Pattern:** 1 agent doing N file edits serially (context collapse)
**Correct Pattern:** N agents doing 1 task each (parallel isolation)

Token cost identical, but parallel approach is faster with 100% success rate.

---

# SECTION 6: USER GUIDE FAQ

## Schedule Access

- Web interface, mobile app, calendar export
- Schedule shows: rotations, blocks, location, supervisor, call schedule
- Can view colleagues' schedules (limited to program)

## Requesting Time Off

- Submit 4-6 weeks in advance
- Approval workflow: coordinator → program director
- Emergency: Call chief resident immediately

## Managing Swaps

1. Click shift in "My Schedule"
2. Select "Request Swap"
3. Use auto-matcher or direct request
4. Partner accepts → system validates → approval workflow

## ACGME Compliance Monitoring

- Real-time dashboard shows hours, days off, call frequency
- Color codes: Green (compliant), Yellow (approaching), Red (at limit)
- Contact chief resident immediately if concerned about violations

---

# SECTION 7: AGENT CAPABILITIES

## MCP Tools (34+ available)

All prefixed with `mcp__residency-scheduler__`

**Schedule Operations:** get_schedule, create_assignment, generate_schedule, validate_schedule
**Compliance:** check_work_hours, check_day_off, check_supervision, get_violations
**Swaps:** create_swap, find_swap_matches, execute_swap, rollback_swap
**Resilience:** get_defense_level, get_utilization, run_n1_analysis, get_burnout_rt
**RAG:** rag_search, rag_context, rag_health

## Key Skills

- `/scheduling` - Generate ACGME-compliant schedules
- `/check-compliance` - Audit for violations
- `/swap` - Execute swaps with safety
- `/search-party` - 120-probe codebase reconnaissance
- `/qa-party` - Parallel test/lint/build

---

# SECTION 8: SESSION PROTOCOLS

## Session End Protocol

**Trigger phrases:** "wrapping up", "finishing up", "end of session"

**Required Actions:**
1. Deploy audit team (DELEGATION_AUDITOR, QA_TESTER)
2. Deploy G-Staff (G4_CONTEXT_MANAGER, META_UPDATER)
3. Documentation (HISTORIAN if significant)

## Session Start Protocol

1. Load core context (CLAUDE.md, AI rules, HUMAN_TODO)
2. Check git state
3. Query RAG for recent learnings
4. Check Codex feedback on PR

---

# SECTION 9: SESSION LEARNINGS

## Coordinator-Led Parallelization

Structure: ORCHESTRATOR → COORDs → Specialists

**Why coordinators work:**
- Context compression
- Reduced overhead
- Failure isolation
- Parallelization

## Phased Parallel Execution

Break work into phases based on dependencies:
1. P0 blockers first
2. P1 high priority parallel
3. P2 medium priority parallel
4. Quality assurance

## Context Isolation Awareness

- Spawned agents have isolated context windows
- Must explicitly pass all necessary context
- Use absolute file paths

---

# SECTION 10: EXOTIC CONCEPTS

## 10 Frontier Concepts

1. **Metastability Detection** - Unstick trapped solvers
2. **Spin Glass Model** - Generate diverse schedules
3. **Circadian PRC** - Mechanistic burnout prediction
4. **Penrose Process** - Boundary optimization
5. **Anderson Localization** - 12-45x faster updates
6. **Persistent Homology** - Structural anomaly detection
7. **Free Energy Principle** - Predictive scheduling
8. **Keystone Species** - N-1 critical resource identification
9. **Quantum Zeno Effect** - Prevent over-monitoring
10. **Catastrophe Theory** - Early failure warning

---

# SECTION 11: ARCHITECTURE OVERVIEW

## Tech Stack

**Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Pydantic, PostgreSQL, Redis, Celery
**Frontend:** Next.js 14, React 18, TypeScript, TailwindCSS, TanStack Query
**Infrastructure:** Docker, MCP Server (34+ tools), Prometheus, Grafana

## Layered Architecture

```
Route → Controller → Service → Repository → Model
```

- Routes: API endpoints (thin)
- Controllers: Request handling, validation
- Services: Business logic
- Repositories: Database operations
- Models: SQLAlchemy ORM

## Port Reference

| Service | Port |
|---------|------|
| Frontend | 3000 |
| Backend | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| MCP | 8081 |

---

# SECTION 12: API PATTERNS

## Type Naming Convention (CRITICAL)

| Layer | Convention |
|-------|------------|
| Backend (Python) | snake_case |
| Frontend (TypeScript) | camelCase |
| API Wire Format | snake_case |

Axios interceptor automatically converts between them.

**Common Bug:** TypeScript interface uses snake_case but axios returns camelCase → undefined at runtime

```typescript
// ❌ Wrong
interface Person { pgy_level: number; }

// ✓ Correct
interface Person { pgyLevel: number; }
```

## Backend API Pattern

```python
@router.get("/{id}", response_model=PersonResponse)
async def get_person(
    id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PersonResponse:
    ...
```

## Frontend API Pattern

```typescript
const { data } = useQuery({
  queryKey: ['people'],
  queryFn: () => api.get<Person[]>('/people'),
});
```

---

# SECTION 13: TROUBLESHOOTING GUIDE

## Quick Diagnostic Commands

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
docker logs scheduler-local-backend --tail 50
curl http://localhost:8000/api/v1/health/ready
```

## Common Issues

**Database Connection Failed:**
```bash
docker-compose up -d db
docker-compose logs db
```

**Migration Name Too Long:**
- Must be ≤64 characters
- Use: `20260109_add_person_pgy`

**Container Won't Start:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**API Returns Undefined:**
- Check TypeScript interface uses camelCase
- Axios converts snake_case → camelCase automatically

## Pre-PR Checklist

- [ ] TypeScript interfaces use camelCase
- [ ] All async functions have await on DB operations
- [ ] Migration name ≤64 characters
- [ ] No secrets in code
- [ ] Tests pass: pytest and npm test
- [ ] Linting passes: ruff check and npm run lint

---

# METADATA

## Document Sources

1. acgme-rules.md - ACGME compliance documentation
2. scheduling-policies.md - Block structure and rotation types
3. swap-system.md - Swap workflows and validation
4. resilience-concepts.md - Cross-disciplinary resilience
5. delegation-patterns.md - Auftragstaktik and orchestration
6. user-guide-faq.md - End-user documentation
7. agent-capabilities.md - MCP tools and skills
8. session-protocols.md - Session start/end workflows
9. session-learnings.md - Cross-session patterns
10. exotic-concepts.md - Frontier physics/math concepts
11. architecture-overview.md - System design
12. api-patterns.md - API conventions and patterns
13. troubleshooting-guide.md - Common issues and fixes

## Last Updated

2026-01-10

## RAG Ingestion

This file is designed for single-document RAG ingestion. Each section is self-contained with clear headers for semantic chunking.

```python
# Ingest this bundle
mcp__residency-scheduler__rag_ingest(
    content="[COMBINED_RAG_BUNDLE.md contents]",
    doc_type="user_guide_faq"
)
```
