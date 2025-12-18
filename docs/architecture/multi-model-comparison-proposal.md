# Multi-Model Comparison Mode: Feature Proposal

> **Document Version:** 1.0
> **Date:** 2025-12-18
> **Status:** Proposal (Pending Review)
> **Target Release:** v1.2.0 (Q2 2026)

---

## Executive Summary (For Program Directors & Faculty)

### What Is This?

Currently, when you generate a schedule, the system uses **one algorithm** (like "greedy" or "hybrid") to create assignments. This proposal adds a **"Compare All Methods"** button that would:

1. Run **all four** scheduling algorithms on your data
2. Show you **which method produced the best schedule**
3. Let you **pick the winner** based on what matters most to you

Think of it like getting four different scheduling proposals from four different chief residents, then comparing them side-by-side to pick the best one.

### Why Would This Help?

| Scenario | Current Behavior | With This Feature |
|----------|------------------|-------------------|
| **Annual Planning** | You pick one method and hope it's best | You see all options and pick the winner |
| **Complex Months** | Trial-and-error if schedule seems unfair | Clear comparison shows fairest option |
| **New Program** | No way to know which algorithm fits your needs | Run all, learn which works best |
| **Audit Preparation** | Can't prove you chose optimal method | Documentation shows comparison |

### Real-World Example

**Scenario:** Planning July schedules (new interns arrive, maximum complexity)

**Without this feature:**
> "I clicked Generate and got 3 ACGME violations. Is that good? Could it be better? I don't know."

**With this feature:**
> "Greedy gave me 3 violations, PuLP gave me 1, CP-SAT gave me 0, Hybrid gave me 0. CP-SAT also had the fairest workload distribution. I'll use that one."

### How Long Does It Take?

| What You're Scheduling | Approximate Time |
|------------------------|------------------|
| One week | ~30 seconds |
| One month | ~2 minutes |
| Full academic year | ~5-8 minutes |

This is designed for **planning sessions** (not urgent changes). Run it before a meeting, over lunch, or overnight.

---

## Technical Analysis (For Software Engineers)

### Current Architecture

The scheduling engine (`backend/app/scheduling/engine.py`) supports four solvers via `SolverFactory`:

```
┌─────────────────────────────────────────────────────────┐
│                    SolverFactory                         │
├─────────────────────────────────────────────────────────┤
│  "greedy"  → GreedySolver (heuristic, O(n log n))       │
│  "pulp"    → PuLPSolver (LP via CBC, single-threaded)   │
│  "cp_sat"  → CPSATSolver (OR-Tools, multi-threaded)     │
│  "hybrid"  → HybridSolver (CP-SAT → PuLP fallback)      │
└─────────────────────────────────────────────────────────┘
```

**Current limitations:**
- Only one algorithm runs per `/generate` request
- `AnalyticsEngine.compare_schedules()` only supports 2-way comparison
- No batch comparison endpoint exists
- No ranking algorithm for multi-metric optimization

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                POST /api/schedule/generate/batch-compare         │
├─────────────────────────────────────────────────────────────────┤
│  Request:                                                        │
│    - start_date, end_date                                        │
│    - algorithms: ["greedy", "pulp", "cp_sat", "hybrid"]         │
│    - timeout_seconds_per_algorithm: 120                          │
│                                                                  │
│  Processing:                                                     │
│    for algorithm in algorithms:                                  │
│      1. Create ScheduleRun record (status: in_progress)         │
│      2. Run engine.generate(algorithm=algorithm)                 │
│      3. Store results, update ScheduleRun (status: completed)   │
│      4. Collect metrics via analyze_schedule()                   │
│                                                                  │
│  Response:                                                       │
│    - Individual results per algorithm                            │
│    - Comparison metrics (coverage, fairness, violations, time)  │
│    - Ranking with "best overall" recommendation                  │
│    - Trade-off analysis                                          │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Components

| Component | File | Estimated LOC | Complexity |
|-----------|------|---------------|------------|
| Request/Response schemas | `schemas/schedule.py` | ~80 | Low |
| Batch comparison endpoint | `api/routes/schedule.py` | ~120 | Medium |
| Multi-way comparison logic | `scheduling/comparison.py` (new) | ~150 | Medium |
| Ranking algorithm | `scheduling/comparison.py` | ~50 | Low |
| Database migration | `alembic/versions/` | ~30 | Low |
| Unit tests | `tests/test_batch_comparison.py` | ~200 | Medium |
| **Total** | | **~630** | **Medium** |

### Key Technical Decisions

#### 1. Synchronous vs Asynchronous

**Recommendation: Synchronous first, async as enhancement**

| Approach | Pros | Cons |
|----------|------|------|
| **Synchronous** | Simple, no new infrastructure, follows existing patterns | Blocks for 5-8 min on full year |
| **Asynchronous (Celery)** | Non-blocking, progress updates | Adds complexity, polling required |

The existing codebase uses synchronous patterns with idempotency. Start there.

#### 2. Storage Strategy

**Recommendation: Link to existing ScheduleRun records**

```python
class BatchComparisonRun(Base):
    id: UUID
    algorithm_runs: list[UUID]  # FK to ScheduleRun.id
    comparison_json: JSON       # Cached comparison results
    best_algorithm: str
    created_at: datetime
```

Each algorithm creates its own `ScheduleRun`. The batch links them together.

#### 3. Ranking Algorithm

**Recommendation: Weighted multi-objective scoring**

```python
def compute_ranking_score(result: AlgorithmResult) -> float:
    """
    Higher score = better schedule.
    Weights reflect clinical priorities.
    """
    return (
        (1 - result.violation_rate) * 40 +     # 40% - ACGME compliance
        result.coverage_rate * 30 +             # 30% - Block coverage
        result.fairness_index * 20 +            # 20% - Workload equity
        (1 - result.normalized_runtime) * 10    # 10% - Speed (tiebreaker)
    )
```

---

## Pros and Cons Analysis

### PROS: Arguments FOR Building This Feature

#### 1. Clinical Quality Improvement
**For physicians:** You currently have no way to know if the schedule could be better. This gives you objective evidence that you're using the best available method.

**For engineers:** The infrastructure already exists (4 solvers, analytics engine). We're exposing capability that's already built but hidden.

#### 2. Audit & Compliance Documentation
**For physicians:** ACGME site visitors may ask "How do you ensure optimal scheduling?" This provides documented proof of systematic optimization.

**For engineers:** Creates audit trail via `BatchComparisonRun` records. Comparison results are stored, not just final schedules.

#### 3. Program-Specific Tuning
**For physicians:** Different programs have different needs. A procedure-heavy program might prefer CP-SAT; a simple clinic might do fine with Greedy. This helps you discover what works.

**For engineers:** Enables data-driven algorithm selection. Over time, we can analyze which algorithms work best for which program characteristics.

#### 4. Confidence in Edge Cases
**For physicians:** July transitions, holiday coverage, conference season - these are when schedules are hardest. Comparison mode lets you verify you're handling complexity well.

**For engineers:** Stress-tests the constraint system. If algorithms produce very different results, it may indicate constraint gaps.

#### 5. Low Marginal Cost
**For engineers:**
- No new dependencies required
- Existing Celery infrastructure (if we go async later)
- Reuses `AnalyticsEngine` metrics
- ~630 LOC estimated (2-3 days implementation)

---

### CONS: Arguments AGAINST Building This Feature

#### 1. Runtime is Non-Trivial
**For physicians:** A full-year comparison takes 5-8 minutes. This isn't suitable for urgent mid-day changes. It's a planning tool, not an operational tool.

**For engineers:**
- 4 sequential solver runs = 4x single-run time
- Blocks other requests during execution (if synchronous)
- May need async pattern for Render deployment (30s HTTP timeout)

#### 2. Complexity for Limited Benefit
**For physicians:** In practice, `hybrid` mode already provides intelligent fallback. For 90% of cases, you don't need to see all four - hybrid picks the best automatically.

**For engineers:**
- Feature may be rarely used after initial curiosity
- Adds maintenance burden (new schemas, tests, endpoint)
- Could invest the same effort in other roadmap items

#### 3. Decision Paralysis Risk
**For physicians:** Four options with slightly different trade-offs could lead to overthinking. "Greedy has 1 more violation but is 10x faster - which do I pick?" The system should guide, not burden.

**For engineers:** Ranking algorithm is subjective. Different weighting produces different "winners." We're imposing our priorities.

#### 4. Resource Constraints on Render
**For engineers:**
- Render's practical HTTP timeout is ~30 seconds
- Full comparison would require async Celery pattern
- Adds ~$7-14/month for additional worker
- Greedy works fine synchronously; others need background processing

#### 5. Opportunity Cost
**Current roadmap priorities (v1.1.0):**
- Email notifications (user-requested)
- Bulk import/export (operational need)
- FMIT improvements (program-specific)

**This feature:**
- Not user-requested
- Nice-to-have, not need-to-have
- Could delay higher-priority items

---

## Comparison Matrix

| Factor | Build It | Refine Existing |
|--------|----------|-----------------|
| **User Value** | High for planning, low for daily ops | Hybrid already handles most cases |
| **Development Cost** | ~630 LOC, 2-3 days | 0 (already built) |
| **Maintenance Cost** | Medium (new endpoint, schemas) | Low |
| **Infrastructure Cost** | +$7-14/mo on Render (if async) | $0 |
| **Audit Value** | High (documented comparison) | Low (single algorithm, no proof) |
| **Learning Value** | High (understand algorithm behavior) | Low |
| **Risk** | Low (isolated feature, no breaking changes) | N/A |

---

## Alternative: Refining What We Have

Instead of batch comparison, we could invest the same effort in:

### Option A: Smarter Hybrid Mode
Enhance the existing `HybridSolver` to:
- Log why it chose CP-SAT vs PuLP
- Expose confidence scores to the UI
- Auto-tune based on problem characteristics

**Effort:** ~200 LOC
**Benefit:** Invisible improvement, no new UI needed

### Option B: Algorithm Recommendations
Add a pre-generation step that analyzes the problem and recommends which algorithm to use:

```
"Based on 20 residents, 730 blocks, and 15% absence rate,
we recommend CP-SAT for optimal results (estimated 45 seconds)
or Greedy for quick preview (estimated 3 seconds)."
```

**Effort:** ~150 LOC
**Benefit:** Guidance without running all four

### Option C: Historical Analytics
Track which algorithm was used for past schedules and correlate with outcomes:

```
"In the past 6 months, CP-SAT schedules had 40% fewer swap requests
than Greedy schedules."
```

**Effort:** ~300 LOC
**Benefit:** Data-driven without real-time comparison

---

## Recommendation

### For Immediate Term (v1.1.0): **Do Not Build**

The hybrid solver already provides good-enough optimization for operational use. The roadmap priorities (email notifications, bulk import) have clearer user demand.

### For Planning Term (v1.2.0): **Build as Optional Feature**

When users have stabilized on v1.1.0 and are asking "how do I optimize further?", this becomes valuable. Implementation as a "Planning Mode" feature:

1. **Gate behind feature flag** - Only enable for users who want it
2. **Async-first on Render** - Use Celery from day one
3. **Start with 2-algorithm comparison** - Greedy vs Hybrid, not all four
4. **Expand based on usage** - Add CP-SAT/PuLP if users request

### If Built Today: Implementation Order

1. **Week 1:** Schemas + synchronous endpoint (local dev only)
2. **Week 2:** Celery task wrapper (production-ready)
3. **Week 3:** Frontend comparison UI
4. **Week 4:** Documentation + testing

---

## Hosting Considerations

### M1 Max (Local Development)

| Component | Status | Notes |
|-----------|--------|-------|
| OR-Tools (CP-SAT) | Native ARM64 | Works out of the box |
| PuLP (CBC) | Requires workaround | `brew install cbc` |
| Memory | Sufficient | ~100 MB peak per solver |
| CPU | Optimal | Use 6-8 workers vs default 4 |

**Verdict:** Fully viable for local development and testing.

### Render (Cloud Hosting)

| Component | Status | Notes |
|-----------|--------|-------|
| HTTP Timeout | Problematic | 30s practical limit |
| Celery Workers | Supported | +$7/mo per worker |
| Memory | Sufficient | Pro plan (4GB) adequate |
| PostgreSQL | Supported | Standard managed DB |

**Verdict:** Viable with async Celery pattern. Synchronous will timeout.

### Recommended Render Configuration

```yaml
# render.yaml addition for batch comparison support
services:
  - type: worker
    name: celery-batch-worker
    runtime: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: celery -A app.core.celery_app worker -Q batch_comparison -c 2
    envVars:
      - key: CELERY_TASK_TIME_LIMIT
        value: "600"  # 10 minutes for full year comparison
```

**Additional Cost:** ~$7-14/month

---

## Appendix A: Problem Size Reference

| Scenario | Variables | Constraints | Single Solver | All 4 Solvers |
|----------|-----------|-------------|---------------|---------------|
| 1 week | ~1,400 | ~500 | 2-5 sec | 30-45 sec |
| 1 month | ~5,600 | ~2,000 | 15-30 sec | 1-2 min |
| 3 months | ~16,800 | ~6,000 | 30-60 sec | 2-4 min |
| Full year | ~73,000 | ~17,000 | 45-90 sec | 5-8 min |

---

## Appendix B: API Specification (Draft)

### Request

```http
POST /api/schedule/generate/batch-compare
Content-Type: application/json
Idempotency-Key: optional-uuid

{
  "start_date": "2025-07-01",
  "end_date": "2026-06-30",
  "algorithms": ["greedy", "cp_sat", "hybrid"],
  "timeout_seconds_per_algorithm": 120,
  "pgy_levels": [1, 2, 3],
  "rotation_template_ids": null
}
```

### Response

```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-18T14:30:00Z",
  "date_range": {
    "start": "2025-07-01",
    "end": "2026-06-30"
  },
  "results": [
    {
      "algorithm": "greedy",
      "run_id": "...",
      "status": "success",
      "coverage_rate": 0.982,
      "fairness_index": 0.89,
      "violations": {"total": 3, "critical": 0, "high": 1, "medium": 2},
      "runtime_seconds": 4.2
    },
    {
      "algorithm": "cp_sat",
      "run_id": "...",
      "status": "success",
      "coverage_rate": 0.998,
      "fairness_index": 0.94,
      "violations": {"total": 0, "critical": 0, "high": 0, "medium": 0},
      "runtime_seconds": 52.1
    },
    {
      "algorithm": "hybrid",
      "run_id": "...",
      "status": "success",
      "coverage_rate": 0.998,
      "fairness_index": 0.94,
      "violations": {"total": 0, "critical": 0, "high": 0, "medium": 0},
      "runtime_seconds": 48.7
    }
  ],
  "ranking": [
    {"rank": 1, "algorithm": "cp_sat", "score": 96.2},
    {"rank": 2, "algorithm": "hybrid", "score": 96.2},
    {"rank": 3, "algorithm": "greedy", "score": 87.4}
  ],
  "recommendation": {
    "best_overall": "hybrid",
    "reasoning": "Same quality as CP-SAT but 7% faster. Both achieve zero violations.",
    "trade_offs": [
      "Greedy is 12x faster but has 3 violations",
      "CP-SAT guarantees optimality but takes longer"
    ]
  }
}
```

---

## Appendix C: Glossary

| Term | Plain English | Technical Definition |
|------|---------------|---------------------|
| **Algorithm** | A method for solving a problem | A step-by-step procedure for computation |
| **Greedy** | Quick and simple, picks the obvious choice | Heuristic that makes locally optimal choices |
| **CP-SAT** | Thorough, checks all possibilities | Constraint programming with satisfiability |
| **PuLP** | Mathematical optimization | Linear programming via branch-and-cut |
| **Hybrid** | Best of both worlds | Tries CP-SAT first, falls back to PuLP |
| **Coverage** | How many slots got assigned | Percentage of blocks with assignments |
| **Fairness** | Everyone gets equal work | Gini coefficient of workload distribution |
| **Violation** | Something that breaks ACGME rules | Constraint that couldn't be satisfied |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-18 | Claude | Initial proposal |

---

## Approval

- [ ] Program Director Review
- [ ] Technical Lead Review
- [ ] Merge to main branch
