# Lessons Learned - Cross-Session Synthesis

**Purpose:** Aggregate insights from development sessions to accelerate future work and avoid repeating mistakes.

**Format:** Organized by theme, chronologically within theme

**Last Updated:** 2025-12-31 (Session 37)

---

## Table of Contents

1. [Multi-Agent Coordination](#multi-agent-coordination)
2. [Testing Strategies](#testing-strategies)
3. [Performance Optimization](#performance-optimization)
4. [Documentation Practices](#documentation-practices)
5. [Constraint Development](#constraint-development)
6. [Frontend Development](#frontend-development)
7. [Deployment & Infrastructure](#deployment--infrastructure)
8. [AI Agent Workflows](#ai-agent-workflows)

---

## Multi-Agent Coordination

### Session 16: The Parallelization Revelation

**Insight:** 10 parallel terminals can execute independent tasks 10x faster

**Context:** Realized most tasks are embarrassingly parallel (tests, docs, linting)

**Implementation:**
- Terminal 1: Backend tests
- Terminal 2: Frontend tests
- Terminal 3: Linting
- Terminal 4-10: Documentation, feature work

**Impact:** Reduced session time from 3 hours to 30 minutes for multi-task sprints

**Caution:** Ensure tasks are truly independent (no shared database, file conflicts)

**See:** `.claude/dontreadme/sessions/SESSION_016_THE_PARALLELIZATION_REVELATION.md`

---

### Session 36: SEARCH_PARTY Protocol

**Insight:** Specialized reconnaissance agents outperform general-purpose exploration

**Context:** Needed to map 500+ files for issue diagnosis

**Implementation:**
- 10 D&D-inspired agent archetypes (Explorer, Historian, Auditor, etc.)
- Each agent has specific search patterns and heuristics
- Parallel execution, aggregated synthesis

**Impact:** Completed 8-hour reconnaissance in 45 minutes

**Pattern:** Use specialized agents for large-scale codebase exploration

**See:** `.claude/skills/SEARCH_PARTY/`

---

## Testing Strategies

### Session 15: Test-Driven Debugging Workflow

**Insight:** Writing failing tests first prevents fixing the wrong thing

**Context:** Spent 2 hours debugging before realizing root cause was elsewhere

**Workflow:**
1. Write test that reproduces bug
2. Confirm test fails
3. Hypothesize root cause
4. Fix implementation
5. Test passes

**Benefit:** Forces clear problem definition before solution

**Caution:** Don't modify tests during fix (defeats the purpose)

**See:** `docs/development/DEBUGGING_WORKFLOW.md`

---

### Session 26: Frontend Testing Coverage

**Insight:** Component testing catches integration issues unit tests miss

**Context:** Backend tests passed, but frontend crashed on API integration

**Solution:** Add integration tests with Mock Service Worker (MSW)

```typescript
test('renders schedule when API returns data', async () => {
  server.use(
    rest.get('/api/schedule', (req, res, ctx) => {
      return res(ctx.json(mockScheduleData));
    })
  );
  render(<ScheduleView />);
  expect(await screen.findByText('Block 10')).toBeInTheDocument();
});
```

**Impact:** Caught 12 frontend-backend mismatches before deployment

---

## Performance Optimization

### Session 10: Load Testing Before Optimization

**Insight:** Measure first, optimize second

**Context:** Assumed database was bottleneck, spent day optimizing wrong layer

**Approach:**
1. Run k6 load tests to establish baseline
2. Identify actual bottleneck (was API serialization, not DB)
3. Optimize identified bottleneck
4. Re-test to verify improvement

**Tool:** k6 load tests (`load-tests/scenarios/`)

**Lesson:** Never optimize without profiling data

**See:** `.claude/dontreadme/sessions/SESSION_10_LOAD_TESTING.md`

---

### Session 28: Rate Limiting Prevents Abuse

**Insight:** Rate limiting is critical for public-facing APIs

**Context:** Security audit revealed unlimited API access

**Implementation:**
- Token bucket algorithm (Redis-backed)
- Per-endpoint limits (auth: 5/min, read: 100/min, write: 20/min)
- 429 responses with Retry-After header

**Impact:** Mitigated brute-force attacks on auth endpoints

**See:** `backend/app/core/rate_limit.py`

---

## Documentation Practices

### Session 14: Documentation Needs Curation

**Insight:** More docs ≠ better docs (documentation debt accumulates)

**Context:** 200+ markdown files, 35% were stale or LLM-focused

**Problem:**
- Humans struggled to find relevant docs
- Outdated docs caused confusion
- LLM context pollution

**Solution (Session 37):**
- Separate human docs (`/docs/`) from LLM context (`.claude/dontreadme/`)
- Quarterly documentation pruning
- Each doc has "Last Updated" date

**Lesson:** Documentation is code - it needs refactoring

---

### Session 25: Context Indexing Reduces Cognitive Load

**Insight:** Master index accelerates onboarding and session startup

**Context:** New sessions spent 20 minutes finding relevant context

**Implementation:**
- Created `.claude/dontreadme/INDEX.md` - Master index for LLMs
- Created `docs/README.md` - Human navigation guide
- Cross-referenced related documents

**Impact:** Session startup reduced from 20 min to 2 min

---

## Constraint Development

### Session 29: Constraint Preflight Prevents Broken Commits

**Insight:** Missing constraint registration causes silent failures

**Context:** Added new constraint, forgot to register it, schedule generation silently ignored it

**Solution:** Created `constraint-preflight` skill

**Checks:**
1. Constraint exported from module?
2. Registered in constraint registry?
3. Tests exist for constraint?
4. Tests passing?

**Impact:** Zero constraint registration bugs since implementation

**See:** `.claude/skills/constraint-preflight/`

---

### Session 20: ACGME Compliance is Non-Negotiable

**Insight:** Never relax ACGME rules for optimization

**Context:** Solver struggled to find solution, considered softening 1-in-7 rule

**Decision:** Keep all ACGME rules as hard constraints, adjust preferences instead

**Rationale:**
- Regulatory compliance cannot be compromised
- Violating rules risks program accreditation
- Better to report "infeasible" than generate non-compliant schedule

**Lesson:** Safety > convenience

---

## Frontend Development

### Session 21: TanStack Query Eliminates Race Conditions

**Insight:** Manual state management causes race conditions, use TanStack Query

**Context:** Multiple components fetching same data, state desynchronization

**Before:**
```typescript
const [data, setData] = useState(null);
useEffect(() => {
  fetch('/api/schedule').then(setData);
}, []);
```

**After:**
```typescript
const { data } = useQuery({
  queryKey: ['schedule'],
  queryFn: fetchSchedule,
});
```

**Benefits:**
- Automatic caching
- Deduplication (multiple components share same request)
- Background refetch
- Optimistic updates

**Impact:** Eliminated 8 race condition bugs

---

### Session 26: TypeScript Strict Mode is Worth It

**Insight:** Strict mode catches bugs at compile time

**Context:** Runtime errors from `undefined` property access

**Solution:** Enable TypeScript strict mode

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true
  }
}
```

**Impact:** Caught 40+ potential runtime errors before deployment

**Tradeoff:** More type annotations required, but worth it

---

## Deployment & Infrastructure

### Session 8: Docker Compose Simplifies Multi-Service Orchestration

**Insight:** Docker Compose reduces "works on my machine" issues

**Context:** Local dev required manual setup of Postgres, Redis, backend, frontend

**Solution:** Single `docker-compose up -d` starts all services

**Benefits:**
- Consistent environments (dev = staging = prod)
- Easy onboarding (one command)
- Service dependencies managed automatically

**Gotcha:** Docker layer caching - rebuild after dependency changes

---

### Session 30: Load Testing Reveals Scalability Limits

**Insight:** Production load often 10x higher than development testing

**Context:** Application crashed under real-world load

**Approach:**
1. Smoke test (1 VU, 1 min) - Validates functionality
2. Load test (50 VUs, 5 min) - Normal load
3. Stress test (200 VUs, 10 min) - Peak load
4. Soak test (20 VUs, 1 hour) - Memory leaks

**Findings:**
- Database connection pool exhaustion at 50 VUs
- Memory leak in schedule generation
- Rate limiting needed

**Lesson:** Load test before launch

**See:** `load-tests/`

---

## AI Agent Workflows

### Session 12: Context Size Matters

**Insight:** Large context slows responses, curate aggressively

**Context:** Session with 100+ file reads became sluggish

**Solution:**
- Read only necessary files
- Use `/compact` or manual "Document & Clear" pattern
- Create session notes before clearing context

**Tradeoff:** Context refresh takes time, but improves response speed

---

### Session 19: Multi-Agent Handoffs Need Protocol

**Insight:** Unstructured handoffs lose context

**Context:** Agent B couldn't continue Agent A's work

**Solution:** Handoff protocol

```markdown
# Handoff Context
## Current State
- Task: [description]
- Progress: [completed work]
- Blockers: [issues]

## Next Steps
1. [action]
2. [action]
```

**Impact:** Seamless cross-agent collaboration

**See:** `.claude/dontreadme/sessions/SESSION_*_HANDOFF.md`

---

### Session 13: Skills Reduce Repetitive Prompts

**Insight:** Common workflows should be skills, not repeated prompts

**Context:** Repeated "review code, write tests, run tests" pattern

**Solution:** Created `test-writer`, `code-review`, `pr-reviewer` skills

**Benefits:**
- Consistent execution
- Reduced prompt length
- Encapsulated best practices

**Guideline:** If you type the same prompt 3+ times, make it a skill

**See:** `.claude/skills/`

---

## Meta-Lessons (Lessons About Learning)

### Session 14: The Block Revelation

**Insight:** Understanding domain model is critical before implementation

**Context:** Confused "blocks" (AM/PM sessions) with "rotations" (clinic, call, etc.) for 3 sessions

**Impact:** Rewrote schedule generation after understanding correct model

**Lesson:** Invest time upfront to understand domain before coding

**See:** `.claude/Scratchpad/histories/SESSION_014_THE_BLOCK_REVELATION.md`

---

### Session 20: Cross-Disciplinary Analogies Accelerate Innovation

**Insight:** Borrowing concepts from other fields solves novel problems

**Context:** Traditional scheduling metrics missed burnout precursors

**Approach:**
- Queuing theory (80% utilization threshold)
- Epidemiology (SIR models, Rt reproduction number)
- Seismology (STA/LTA for precursor detection)
- Materials science (creep/fatigue models)

**Impact:** Built early warning system for burnout

**Lesson:** Don't limit to domain expertise, explore adjacent fields

**See:** `docs/architecture/cross-disciplinary-resilience.md`

---

### Session 37: Separate Human and LLM Documentation

**Insight:** 35% of docs were "chaff" for humans (session reports, technical jargon)

**Problem:**
- Humans struggled to find relevant docs
- LLMs needed deep technical context
- Mixed audiences caused confusion

**Solution:**
- `/docs/` - Human-readable (users, admins, developers)
- `.claude/dontreadme/` - LLM-focused (sessions, recon, technical)

**Impact:** Reduced human documentation noise by 70%

**Lesson:** Know your audience, tailor content accordingly

---

## Patterns for Success

Across 37 sessions, these meta-patterns emerge:

1. **Measure first, optimize second** - Always profile before optimizing
2. **Write tests first** - TDD prevents fixing the wrong thing
3. **Document decisions** - Future you will forget why
4. **Automate repetition** - If you do it 3 times, make it a skill
5. **Parallelize ruthlessly** - Most tasks are embarrassingly parallel
6. **Fail fast** - Validate early (startup checks, preflight checks)
7. **Borrow from other fields** - Cross-disciplinary analogies unlock innovation
8. **Keep docs fresh** - Stale docs are worse than no docs
9. **Context curation** - Less is more (remove noise, keep signal)
10. **Know your audience** - Different readers need different content

---

**See Also:**
- `.claude/dontreadme/synthesis/PATTERNS.md` - Recurring patterns
- `.claude/dontreadme/synthesis/DECISIONS.md` - Architectural decisions
- `.claude/dontreadme/sessions/` - Session-specific reports
