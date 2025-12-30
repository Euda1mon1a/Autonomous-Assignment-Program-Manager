# Session Learnings and Cross-Session Knowledge

## Overview

This document captures patterns, learnings, and best practices discovered across development sessions that compound in value over time. These insights help future sessions make better decisions faster by avoiding repeated mistakes and leveraging proven approaches.

## Multi-Agent Delegation Patterns

### Coordinator-Led Parallelization

**Pattern Discovered:** Session 020 (2025-12-30)

When tackling large-scale work (21+ technical debt items), use **coordinators as force multipliers** rather than direct agent spawning.

**Structure:**
```
ORCHESTRATOR
├── COORD_PLATFORM (infrastructure + cross-cutting concerns)
├── COORD_QUALITY (testing, linting, code review)
├── COORD_RESILIENCE (resilience framework specialists)
├── COORD_FRONTEND (UI/UX specialists)
└── Direct specialists for isolated tasks
```

**Why Coordinators Work:**
- **Context compression:** Coordinators maintain domain context that specialists inherit
- **Reduced overhead:** One coordinator manages 4-6 specialists vs. ORCHESTRATOR managing 16 individually
- **Failure isolation:** If a specialist fails, coordinator can reassign without escalating to ORCHESTRATOR
- **Parallelization:** Each coordinator can run specialists in parallel independently

**Delegation Metrics (Session 020):**
- 26+ agents spawned across 4 phases
- 85% delegated work, 15% direct orchestration
- Max 16 concurrent agents
- 100% hierarchy compliance

### Phased Parallel Execution

**Pattern:** Break large work into phases based on dependencies, not arbitrary groupings.

**Session 020 Example:**
| Phase | Focus | Agents | Coordinator |
|-------|-------|--------|-------------|
| 0 | Container fixes (blocking) | 1 | COORD_PLATFORM |
| 1 | Critical (P0) items | 2 | COORD_QUALITY |
| 2 | High priority (P1) items | 6 | Mixed |
| 3 | Medium priority (P2) items | 6 | Mixed |
| 4 | Quality assurance | 4 | COORD_QUALITY |

**Key Insight:** P0 items block everything else. Identify and resolve blockers before parallelizing.

### When to Use Coordinators vs Direct Delegation

**Use Coordinators When:**
- Work spans 3+ related tasks in a domain
- Domain requires specialized context (resilience math, frontend patterns)
- Parallelization within the domain is possible
- Failure recovery needs domain expertise

**Use Direct Delegation When:**
- Single isolated task
- Task requires cross-domain coordination at ORCHESTRATOR level
- Urgent/time-sensitive work where coordinator overhead adds latency

## Security Implementation Patterns

### Role-Based Access Control (RBAC)

**Pattern Discovered:** DEBT-002 resolution (Session 020)

When implementing role-based restrictions:

1. **Define role hierarchy explicitly:**
```python
ROLE_HIERARCHY = {
    "admin": 100,      # Can do everything
    "coordinator": 80, # Can manage schedules, users within scope
    "faculty": 60,     # Can view/modify own schedule
    "resident": 40,    # Can view/request changes
    "read_only": 20    # Can only view
}
```

2. **Implement audience restrictions per endpoint:**
```python
ENDPOINT_AUDIENCE_RESTRICTIONS = {
    "schedule:write": ["admin", "coordinator"],
    "schedule:read": ["admin", "coordinator", "faculty", "resident"],
    "user:create": ["admin"],
    "swap:request": ["faculty", "resident"]
}
```

3. **Always verify token ownership:**
```python
def verify_token_ownership(token_id: str, current_user_id: str) -> bool:
    token = get_token(token_id)
    return (
        token.owner_id == current_user_id or
        current_user_role_level >= ROLE_HIERARCHY["admin"]
    )
```

### Security TODO Resolution Workflow

**Pattern:** When security TODOs are found in codebase:
1. **Audit scope:** Find all related TODOs (`grep -r "TODO.*security" --include="*.py"`)
2. **Categorize by risk:** P0 (exploitable now), P1 (exploitable with effort), P2 (theoretical)
3. **Implement in priority order:** Never leave P0 items for later
4. **Add regression tests:** Security fixes need test coverage

## Technical Debt Sprint Methodology

### Discovery Phase

**Full-Stack Layer Review Pattern:**

Session 020 deployed 16 parallel exploration agents across these layers:
1. Frontend Architecture
2. Frontend Components
3. State Management
4. Backend Middleware
5. Database/ORM
6. Authentication
7. Docker/Deployment
8. CI/CD Pipeline
9. MCP Server
10. Celery Tasks
11. WebSocket/Real-time
12. API Routes
13. Frontend-Backend Integration
14. Environment Configuration
15. Error Handling
16. Performance

**Key Insight:** Parallel exploration finds issues faster than sequential review. Issues often span multiple layers.

### Prioritization Framework

**Priority Matrix:**
| Priority | Meaning | Timeline | Examples |
|----------|---------|----------|----------|
| P0 | Blocks launch | Fix immediately | Security vulnerabilities, critical infrastructure gaps |
| P1 | Affects functionality | Fix this week | Missing API wiring, performance indexes |
| P2 | Quality/maintainability | Fix within month | Accessibility, code cleanup |
| P3 | Nice to have | Backlog | Test calibration, observability |

**Key Insight:** P0 items often hide in infrastructure (Celery queues missing, env vars wrong) rather than application code.

### Resolution Tracking

Maintain a technical debt tracker with:
- Unique IDs (DEBT-001, DEBT-002, etc.)
- Location (file path + line number)
- Category (Security, Infrastructure, Performance, etc.)
- Status (Open, In Progress, Resolved)
- Resolution PR reference

## Performance Optimization Patterns

### N+1 Query Prevention

**Pattern Discovered:** DEBT-011 investigation

**Problem:** Lazy loading in loops causes N+1 queries:
```python
# BAD: N+1 queries
people = db.query(Person).all()
for person in people:
    assignments = person.assignments  # Triggers query per person!
```

**Solution:** Use eager loading:
```python
# GOOD: 1 query with joins
from sqlalchemy.orm import selectinload

people = db.query(Person).options(
    selectinload(Person.assignments)
).all()
```

**Monitoring:** Use `/backend/app/db/optimization/` prefetch utilities for complex queries.

### Database Index Strategy

**Critical indexes identified (DEBT-004):**
```sql
CREATE INDEX idx_block_date ON blocks(date);
CREATE INDEX idx_assignment_person_id ON assignments(person_id);
CREATE INDEX idx_assignment_block_id ON assignments(block_id);
CREATE INDEX idx_swap_source_faculty ON swap_records(source_faculty_id);
CREATE INDEX idx_swap_target_faculty ON swap_records(target_faculty_id);
```

**Key Insight:** Index columns used in:
- WHERE clauses (filtering)
- JOIN conditions (foreign keys)
- ORDER BY clauses (sorting)
- Date range queries (especially for schedule views)

## Frontend Integration Patterns

### Environment Variable Conventions

**Next.js Pattern:**
- Use `NEXT_PUBLIC_` prefix for client-accessible vars
- Never use `REACT_APP_` (React CRA pattern, incompatible with Next.js)

**Centralized API Configuration:**
```typescript
// lib/config.ts
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const API_VERSION = '/api/v1';
export const API_URL = `${API_BASE_URL}${API_VERSION}`;
```

### Token Refresh Strategy

**Dual-Layer Pattern:**
1. **Proactive refresh:** Refresh token 1 minute before expiry
2. **Reactive refresh:** On 401 response, attempt refresh before failing

```typescript
// Proactive (in auth context)
useEffect(() => {
  const checkTokenExpiry = () => {
    const expiresAt = getTokenExpiry();
    if (expiresAt && Date.now() > expiresAt - 60_000) {
      refreshToken();
    }
  };
  const interval = setInterval(checkTokenExpiry, 30_000);
  return () => clearInterval(interval);
}, []);

// Reactive (in API client)
const response = await fetch(url, options);
if (response.status === 401) {
  const refreshed = await refreshToken();
  if (refreshed) return fetch(url, options);
  throw new AuthError('Session expired');
}
```

## Infrastructure Patterns

### Celery Queue Configuration

**All 6 queues must be declared:**
```yaml
# docker-compose.yml
celery-worker:
  command: celery -A app.core.celery_app worker -Q default,resilience,notifications,metrics,exports,security
```

**Queue Purposes:**
| Queue | Purpose |
|-------|---------|
| default | General background tasks |
| resilience | Health checks, N-1/N-2 analysis |
| notifications | Email, WebSocket alerts |
| metrics | Analytics, reporting |
| exports | PDF generation, Excel exports |
| security | Token rotation, audit logging |

**Key Insight:** Workers only process queues they're subscribed to. Missing queues means silent task failures.

### API Response Model Coverage

**Pattern:** All endpoints should have explicit `response_model` declarations:
```python
@router.get("/resilience/health", response_model=ResilienceHealthResponse)
async def get_resilience_health(db: Session = Depends(get_db)):
    # Implementation
```

**Benefits:**
- OpenAPI documentation auto-generated
- Response validation ensures consistency
- Client type generation possible

## Resilience Framework Learnings

### Test Coverage Priorities

From Session 020 MVP verification:

**High-Value Test Targets:**
- le_chatelier.py: Equilibrium detection, stress response, recovery
- homeostasis.py: Feedback loop registration, self-correction
- SIR models: Burnout epidemiology calculations

**Calibration vs Structural Issues:**
- Structural issues (wrong method calls, missing attributes): Fix immediately
- Calibration issues (numeric thresholds): Document and defer to domain expert

### Response Model Patterns

For resilience APIs, create explicit response models:
```python
class ResilienceHealthResponse(BaseModel):
    defense_level: DefenseLevel
    utilization: float
    n1_status: N1ContingencyResult
    burnout_rt: float
    recommendations: list[str]
```

## Cross-Session Learning Principles

### What to Embed (G4 Curation Guidelines)

**SHOULD Embed:**
- Key architectural decisions with rationale
- Bug fixes with root cause analysis
- New patterns discovered (coordinator delegation, phased execution)
- ACGME or domain knowledge updates
- Cross-session learnings that compound

**SHOULD NOT Embed:**
- Routine task completion logs
- Temporary debugging output
- Session-specific file paths
- Credentials or sensitive data
- Duplicate content already in knowledge base

### Context Isolation Awareness

**Critical for Multi-Agent Work:**
- Spawned agents have **isolated context windows**
- Must explicitly pass all necessary context in prompts
- Cannot rely on "the other agent knows" assumptions
- Use absolute file paths, not relative references

**Delegation Checklist:**
- [ ] Decision context explicitly passed
- [ ] Critical assumptions included
- [ ] Related prior decisions retrieved if relevant
- [ ] Expected outcomes clearly defined
- [ ] Return path documented

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-30 | Initial session learnings from Session 020 |

---

*This document is maintained by G4_CONTEXT_MANAGER and updated after significant sessions.*
