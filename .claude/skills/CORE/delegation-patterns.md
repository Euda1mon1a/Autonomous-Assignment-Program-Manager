# Delegation Patterns - Subagent Spawning Rules

> **Purpose:** Define when and how to spawn subagents for parallel and specialized work
> **Version:** 1.0.0
> **Last Updated:** 2025-12-26

---

## I. OVERVIEW

This document establishes patterns for:
1. **When to Delegate**: Decision criteria for spawning subagents
2. **Parallel vs Sequential**: Choosing execution strategy
3. **Result Synthesis**: Combining outputs from multiple agents
4. **Error Propagation**: Handling failures in delegated work

**Core Principle:** Delegate when specialization, parallelism, or isolation provides clear benefit. Don't delegate for delegation's sake.

---

## II. DELEGATION DECISION FRAMEWORK

### A. When to Spawn Subagents

**Delegate When:**

1. **Specialization Needed**
   - Task requires deep domain expertise not in current agent's skill set
   - Example: Main agent handling user request delegates ACGME validation to compliance specialist

2. **Parallelism Beneficial**
   - Multiple independent tasks can run simultaneously
   - Wall-clock time reduction > coordination overhead
   - Example: Code review, security audit, and test generation run in parallel

3. **Context Isolation Desired**
   - Task might pollute main agent's context window
   - Need to preserve main agent's working memory
   - Example: Long document analysis delegated to separate agent

4. **Permission Boundaries**
   - Task requires different access level than main agent
   - Principle of least privilege
   - Example: Read-only agent delegates write operations to authorized agent

5. **Load Distribution**
   - Main agent approaching resource limits (context, compute, memory)
   - Distributing work prevents bottleneck
   - Example: Processing 100 schedules for compliance - distribute to 10 agents

6. **Fault Isolation**
   - Task has risk of failure that shouldn't affect main workflow
   - Crash isolation
   - Example: Experimental optimization run in isolated agent

**Do NOT Delegate When:**

1. **Overhead > Benefit**
   - Task takes < 5 seconds (delegation overhead not worth it)
   - Simple lookup or calculation main agent can do instantly

2. **Context Critical**
   - Task requires nuanced understanding from prior conversation
   - Context transfer would be lossy or expensive

3. **Serial Dependency**
   - Task must wait for previous results anyway
   - No parallelism benefit

4. **Single-Step Task**
   - Task is atomic, no multi-step workflow
   - Example: "What's the capital of France?" - just answer, don't delegate

---

### B. Decision Tree

```
Task Received
    |
    ├─ Can I do this in < 5 seconds? ──YES──> Execute directly
    |                                  |
    |                                  NO
    |                                  |
    ├─ Do I have the required skill? ──NO──> DELEGATE to specialist
    |                                 |
    |                                 YES
    |                                 |
    ├─ Are there independent subtasks? ──YES──> DELEGATE to parallel agents
    |                                      |
    |                                      NO
    |                                      |
    ├─ Will this exhaust my context? ──YES──> DELEGATE to isolated agent
    |                                  |
    |                                  NO
    |                                  |
    └──> Execute directly
```

---

## III. PARALLEL VS SEQUENTIAL EXECUTION

### A. Parallel Execution (Scatter-Gather)

**Use When:**
- Tasks are independent (no data dependencies)
- Order doesn't matter
- Results can be merged or processed independently

**Pattern:**
```
Main Agent
    |
    ├─ Spawn Agent 1 (Task A) ───┐
    ├─ Spawn Agent 2 (Task B) ───┤
    ├─ Spawn Agent 3 (Task C) ───┤
    |                            |
    └─ Gather Results ───────────┘
         ↓
    Synthesize & Return
```

**Example - Comprehensive Schedule Validation:**
```python
async def validate_schedule_parallel(schedule_id):
    tasks = [
        {
            "agent": "acgme-compliance",
            "action": "validate",
            "params": {"schedule_id": schedule_id, "rule": "80_hour"}
        },
        {
            "agent": "acgme-compliance",
            "action": "validate",
            "params": {"schedule_id": schedule_id, "rule": "1_in_7"}
        },
        {
            "agent": "resilience-framework",
            "action": "check_utilization",
            "params": {"schedule_id": schedule_id}
        },
        {
            "agent": "schedule-verification",
            "action": "sanity_check",
            "params": {"schedule_id": schedule_id}
        }
    ]

    # All run in parallel
    results = await parallel_execute(tasks)

    # Synthesize (any failure = overall failure)
    return synthesize_validation_results(results)
```

**Benefits:**
- Reduced wall-clock time (4x speedup in example above)
- Utilizes multiple compute resources
- Fault isolation (one failure doesn't block others from completing)

**Drawbacks:**
- Coordination overhead
- More complex error handling
- Potential resource contention

---

### B. Sequential Execution (Pipeline)

**Use When:**
- Tasks have dependencies (output of A is input to B)
- Order matters
- Each step must validate before next proceeds

**Pattern:**
```
Main Agent
    |
    └─ Spawn Agent 1 (Task A)
         ↓ (result)
       Spawn Agent 2 (Task B)
         ↓ (result)
       Spawn Agent 3 (Task C)
         ↓ (result)
       Return
```

**Example - Schedule Generation Pipeline:**
```python
async def generate_schedule_sequential(params):
    # Step 1: Backup database (must complete first)
    backup_result = await delegate_to_agent(
        agent="safe-schedule-generation",
        action="backup",
        params={"tables": ["assignments", "blocks"]}
    )
    if not backup_result.success:
        return error("Backup failed - cannot proceed")

    # Step 2: Generate schedule (needs backup complete)
    schedule_result = await delegate_to_agent(
        agent="schedule-optimization",
        action="generate",
        params=params
    )
    if not schedule_result.success:
        await delegate_to_agent("safe-schedule-generation", "rollback")
        return error("Generation failed")

    # Step 3: Validate (needs generated schedule)
    validation_result = await delegate_to_agent(
        agent="acgme-compliance",
        action="validate",
        params={"schedule": schedule_result.data}
    )
    if validation_result.violations:
        await delegate_to_agent("safe-schedule-generation", "rollback")
        return error("ACGME violations detected")

    # Step 4: Human verification (needs validated schedule)
    verification = await delegate_to_agent(
        agent="schedule-verification",
        action="checklist",
        params={"schedule": schedule_result.data}
    )

    return success(schedule_result.data, verification)
```

**Benefits:**
- Clear workflow, easy to understand
- Each step validated before proceeding
- Simple error handling (abort pipeline on failure)

**Drawbacks:**
- Serial execution (sum of all step times)
- Cannot utilize parallelism
- Blocked if any step slow

---

### C. Hybrid Execution (Pipeline of Parallel Stages)

**Best of Both Worlds:**
- Parallel execution within stages
- Sequential stages for dependencies

**Pattern:**
```
Main Agent
    |
    ├─ Stage 1: Parallel Validation
    |   ├─ Agent A (ACGME check)
    |   ├─ Agent B (Resilience check)
    |   └─ Agent C (Conflict check)
    |       ↓ (all must pass)
    |
    ├─ Stage 2: Parallel Optimization
    |   ├─ Agent D (Fairness optimization)
    |   ├─ Agent E (Coverage optimization)
    |   └─ Agent F (Continuity optimization)
    |       ↓ (select best)
    |
    └─ Stage 3: Final Validation
        └─ Agent G (Comprehensive check)
            ↓
          Return
```

**Example - Multi-Objective Schedule Optimization:**
```python
async def optimize_schedule_hybrid(schedule):
    # Stage 1: Parallel pre-validation (must all pass)
    validation_tasks = [
        ("acgme-compliance", "validate", {"schedule": schedule}),
        ("resilience-framework", "check", {"schedule": schedule}),
        ("conflict-detector", "scan", {"schedule": schedule})
    ]
    validations = await parallel_execute(validation_tasks)
    if any(not v.success for v in validations):
        return error("Pre-validation failed", validations)

    # Stage 2: Parallel optimization attempts
    optimization_tasks = [
        ("schedule-optimization", "optimize", {"objective": "fairness", "schedule": schedule}),
        ("schedule-optimization", "optimize", {"objective": "coverage", "schedule": schedule}),
        ("schedule-optimization", "optimize", {"objective": "continuity", "schedule": schedule})
    ]
    optimizations = await parallel_execute(optimization_tasks)

    # Select best result (Pareto-optimal)
    best_schedule = pareto_select(optimizations)

    # Stage 3: Final validation (sequential, on best result)
    final_validation = await delegate_to_agent(
        agent="acgme-compliance",
        action="comprehensive_validate",
        params={"schedule": best_schedule}
    )

    return success(best_schedule, final_validation)
```

---

## IV. DELEGATION MECHANISMS

### A. Fire-and-Forget Delegation

**Use When:**
- Result not immediately needed
- Main agent can continue other work
- Eventually retrieve result later

**Pattern:**
```python
# Delegate and get future reference
task_id = await delegate_async(
    agent="schedule-optimization",
    action="generate",
    params={"period": "Q2-2025"}
)

# Continue other work
await do_other_work()

# Later, retrieve result
result = await get_task_result(task_id, timeout=60)
```

**Example Use Cases:**
- Background report generation
- Asynchronous notifications
- Non-blocking analytics

---

### B. Blocking Delegation

**Use When:**
- Result needed immediately
- Cannot proceed without it

**Pattern:**
```python
# Wait for result
result = await delegate_and_wait(
    agent="acgme-compliance",
    action="validate",
    params={"schedule_id": "uuid"},
    timeout=30
)

# Use result immediately
if result.violations:
    return error("Validation failed")
```

**Example Use Cases:**
- Validation checks before commit
- Critical path operations
- User-blocking requests

---

### C. Streaming Delegation

**Use When:**
- Long-running task
- Want incremental results
- Provide user feedback during execution

**Pattern:**
```python
# Get async stream
stream = await delegate_streaming(
    agent="schedule-optimization",
    action="generate",
    params={"period": "Q2-2025"}
)

# Process results as they arrive
async for update in stream:
    if update.type == "progress":
        show_progress(update.percentage)
    elif update.type == "partial_result":
        display_intermediate(update.data)
    elif update.type == "final_result":
        return success(update.data)
```

**Example Use Cases:**
- Schedule generation with progress bar
- Large data processing
- Multi-phase operations

---

## V. RESULT SYNTHESIS PATTERNS

### A. All-or-Nothing (AND Logic)

**Rule:** All subagents must succeed; any failure = overall failure.

**Use For:**
- Safety-critical validation
- Compliance checks
- Quality gates

**Implementation:**
```python
def synthesize_all_or_nothing(results):
    failures = [r for r in results if not r.success]

    if failures:
        return {
            "success": False,
            "errors": merge_errors(failures),
            "message": f"{len(failures)} of {len(results)} checks failed"
        }
    else:
        return {
            "success": True,
            "results": [r.data for r in results],
            "message": "All checks passed"
        }
```

**Example:**
```python
# ACGME compliance: ALL rules must pass
validation_results = await parallel_execute([
    validate_80_hour_rule(),
    validate_1_in_7_rule(),
    validate_supervision_ratios()
])

# Any violation = schedule rejected
return synthesize_all_or_nothing(validation_results)
```

---

### B. Best-Effort (OR Logic)

**Rule:** Any success is sufficient; failure only if all fail.

**Use For:**
- Fault-tolerant operations
- Multiple data sources (fallbacks)
- Alternative approaches

**Implementation:**
```python
def synthesize_best_effort(results):
    successes = [r for r in results if r.success]

    if successes:
        return {
            "success": True,
            "result": successes[0].data,  # First success
            "alternatives": [s.data for s in successes[1:]],
            "failures": [r for r in results if not r.success]
        }
    else:
        return {
            "success": False,
            "errors": merge_errors(results),
            "message": "All attempts failed"
        }
```

**Example:**
```python
# Try multiple swap candidates (any match works)
swap_attempts = await parallel_execute([
    try_swap_with_faculty("FAC-01"),
    try_swap_with_faculty("FAC-02"),
    try_swap_with_faculty("FAC-03")
])

# Return first successful swap
return synthesize_best_effort(swap_attempts)
```

---

### C. Majority Vote (Consensus)

**Rule:** Majority agreement wins; ties require tiebreaker.

**Use For:**
- Ambiguous decisions
- Multi-perspective analysis
- Conflict resolution

**Implementation:**
```python
def synthesize_majority_vote(results):
    votes = {}
    for r in results:
        decision = r.data.get("decision")
        votes[decision] = votes.get(decision, 0) + 1

    total = len(results)
    for decision, count in votes.items():
        if count > total / 2:
            return {
                "success": True,
                "decision": decision,
                "confidence": count / total,
                "dissenting_opinions": [
                    r for r in results if r.data.get("decision") != decision
                ]
            }

    # No majority - escalate
    return {
        "success": False,
        "message": "No majority consensus",
        "votes": votes,
        "requires_escalation": True
    }
```

**Example:**
```python
# Multiple agents review code quality
reviews = await parallel_execute([
    agent_review("code-review"),
    agent_review("security-audit"),
    agent_review("performance-analyzer")
])

# Majority "approve" = approved
return synthesize_majority_vote(reviews)
```

---

### D. Weighted Aggregation

**Rule:** Weight results by agent expertise or confidence.

**Use For:**
- Multi-objective optimization
- Expert opinions with different credibility
- Risk assessment

**Implementation:**
```python
def synthesize_weighted(results, weights):
    if len(results) != len(weights):
        raise ValueError("Results and weights must match")

    total_weight = sum(weights)
    weighted_score = 0

    for result, weight in zip(results, weights):
        weighted_score += result.data.get("score", 0) * weight

    return {
        "success": True,
        "weighted_score": weighted_score / total_weight,
        "individual_scores": [
            {"agent": r.agent, "score": r.data.get("score"), "weight": w}
            for r, w in zip(results, weights)
        ]
    }
```

**Example:**
```python
# Multi-objective schedule scoring
objectives = await parallel_execute([
    evaluate_fairness(schedule),      # Weight: 0.4
    evaluate_coverage(schedule),      # Weight: 0.3
    evaluate_continuity(schedule)     # Weight: 0.3
])

weights = [0.4, 0.3, 0.3]
return synthesize_weighted(objectives, weights)
```

---

### E. Merge-and-Deduplicate

**Rule:** Combine all results, removing duplicates.

**Use For:**
- Information gathering
- Search across multiple sources
- Comprehensive reporting

**Implementation:**
```python
def synthesize_merge_dedupe(results):
    merged = []
    seen = set()

    for result in results:
        for item in result.data.get("items", []):
            item_id = item.get("id")
            if item_id not in seen:
                seen.add(item_id)
                merged.append(item)

    return {
        "success": True,
        "items": merged,
        "total_count": len(merged),
        "sources": len(results)
    }
```

**Example:**
```python
# Find all scheduling conflicts from multiple detectors
conflict_scans = await parallel_execute([
    scan_time_conflicts(),
    scan_acgme_conflicts(),
    scan_credential_conflicts()
])

# Merge, removing duplicates
return synthesize_merge_dedupe(conflict_scans)
```

---

## VI. ERROR PROPAGATION

### A. Fail-Fast Strategy

**Rule:** First error aborts entire operation.

**Use When:**
- Safety-critical operations
- No point continuing if one step fails
- Minimize wasted work

**Implementation:**
```python
async def execute_fail_fast(tasks):
    for task in tasks:
        result = await delegate_to_agent(**task)
        if not result.success:
            # Abort immediately
            return error(f"Task {task['agent']} failed", result.errors)

    return success("All tasks completed")
```

**Example:**
```python
# Schedule generation pipeline (sequential fail-fast)
steps = [
    {"agent": "safe-schedule-generation", "action": "backup"},
    {"agent": "schedule-optimization", "action": "generate"},
    {"agent": "acgme-compliance", "action": "validate"}
]

# Any step failure = abort entire pipeline
return await execute_fail_fast(steps)
```

---

### B. Fail-Tolerant Strategy

**Rule:** Continue despite failures, collect all results.

**Use When:**
- Best-effort operations
- Partial results still valuable
- Independent tasks

**Implementation:**
```python
async def execute_fail_tolerant(tasks):
    results = []

    for task in tasks:
        try:
            result = await delegate_to_agent(**task)
            results.append({"success": True, "data": result})
        except Exception as e:
            results.append({"success": False, "error": str(e)})

    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]

    return {
        "success": len(successes) > 0,
        "results": successes,
        "errors": failures,
        "partial": len(failures) > 0
    }
```

**Example:**
```python
# Generate multiple report formats (any success is good)
reports = [
    {"agent": "pdf", "action": "generate"},
    {"agent": "xlsx", "action": "generate"},
    {"agent": "html", "action": "generate"}
]

# Continue even if some formats fail
return await execute_fail_tolerant(reports)
```

---

### C. Retry-with-Backoff Strategy

**Rule:** Retry failed tasks with exponential backoff.

**Use When:**
- Transient failures expected
- External dependencies (network, database)
- Eventually consistent operations

**Implementation:**
```python
async def execute_with_retry(task, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            result = await delegate_to_agent(**task)
            if result.success:
                return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Final attempt failed

            delay = base_delay * (2 ** attempt)  # Exponential backoff
            await asyncio.sleep(delay)

    return error(f"Failed after {max_retries} attempts")
```

**Example:**
```python
# Database-dependent task (may have transient connection issues)
result = await execute_with_retry(
    task={"agent": "database-migration", "action": "apply"},
    max_retries=3,
    base_delay=2
)
```

---

### D. Circuit-Breaker Strategy

**Rule:** Stop trying if agent consistently fails.

**Use When:**
- Preventing cascading failures
- Resource protection
- Downstream service degraded

**Implementation:**
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failures = 0
        self.threshold = failure_threshold
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.opened_at = None
        self.timeout = timeout

    async def execute(self, task):
        if self.state == "OPEN":
            if time.time() - self.opened_at > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitOpenError(f"Circuit breaker OPEN for {task['agent']}")

        try:
            result = await delegate_to_agent(**task)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            if self.failures >= self.threshold:
                self.state = "OPEN"
                self.opened_at = time.time()
            raise
```

**Example:**
```python
# Protect against failing external service
external_api_breaker = CircuitBreaker(failure_threshold=3, timeout=60)

try:
    result = await external_api_breaker.execute(
        {"agent": "external-integration", "action": "fetch"}
    )
except CircuitOpenError:
    # Use cached data or fallback
    result = get_cached_data()
```

---

## VII. RESOURCE MANAGEMENT

### A. Concurrency Limits

**Problem:** Too many parallel agents overwhelm resources.

**Solution:** Limit concurrent delegations.

```python
from asyncio import Semaphore

# Global semaphore (max 10 concurrent agents)
delegation_semaphore = Semaphore(10)

async def delegate_with_limit(task):
    async with delegation_semaphore:
        return await delegate_to_agent(**task)
```

**Example:**
```python
# Process 100 schedules, but only 10 at a time
async def process_schedules(schedule_ids):
    tasks = [
        delegate_with_limit({"agent": "acgme-compliance", "action": "validate", "params": {"id": sid}})
        for sid in schedule_ids
    ]

    return await asyncio.gather(*tasks)
```

---

### B. Timeout Management

**Problem:** Agents hang indefinitely.

**Solution:** Set timeouts on all delegations.

```python
async def delegate_with_timeout(task, timeout=60):
    try:
        return await asyncio.wait_for(
            delegate_to_agent(**task),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return error(f"Agent {task['agent']} timed out after {timeout}s")
```

**Timeout Guidelines:**

| Task Type | Recommended Timeout |
|-----------|---------------------|
| Validation checks | 10-30 seconds |
| Schedule generation | 5-10 minutes |
| Database migrations | 2-5 minutes |
| Report generation | 1-3 minutes |
| External API calls | 15-30 seconds |

---

### C. Memory Management

**Problem:** Delegated tasks consume excessive memory.

**Solution:** Stream results, limit payload sizes.

```python
async def delegate_large_dataset(task):
    # Stream results instead of loading all into memory
    async for chunk in delegate_streaming(**task):
        process_chunk(chunk)
        # Chunk processed and can be garbage collected
```

---

## VIII. MONITORING & OBSERVABILITY

### A. Delegation Metrics

**Track:**
- Delegation rate (delegations per minute)
- Success rate by agent type
- Average delegation time
- Resource utilization (concurrent agents)
- Error rate by error type

**Alerts:**
- Delegation success rate < 90%
- Average delegation time > 2x baseline
- Concurrent agents > 80% of limit
- Error rate > 10%

---

### B. Tracing Delegation Chains

**Use Correlation IDs:**
```
User Request (correlation_id: abc123)
  └─ Main Agent
      ├─ Delegate to Agent A (correlation_id: abc123, depth: 1)
      │   └─ Agent A delegates to Agent D (correlation_id: abc123, depth: 2)
      ├─ Delegate to Agent B (correlation_id: abc123, depth: 1)
      └─ Delegate to Agent C (correlation_id: abc123, depth: 1)
```

**Query Traces:**
```sql
SELECT agent_id, action, depth, duration_ms
FROM delegation_log
WHERE correlation_id = 'abc123'
ORDER BY timestamp ASC;
```

**Visualize:**
```
Main [150ms]
├── Agent A [45ms]
│   └── Agent D [20ms]
├── Agent B [67ms]
└── Agent C [38ms]

Total: 150ms (parallel execution)
```

---

## IX. BEST PRACTICES

### A. Delegation Hygiene

**DO:**
- Set explicit timeouts on all delegations
- Use correlation IDs for tracing
- Provide complete context to subagents
- Handle failures gracefully
- Monitor delegation metrics

**DON'T:**
- Delegate tasks smaller than delegation overhead
- Create circular delegations (A→B→A)
- Delegate without error handling
- Ignore partial failures
- Exceed concurrency limits

---

### B. Context Transfer

**DO:**
- Include all necessary data in delegation message
- Reference large datasets (don't copy)
- Version message schemas
- Document expected input/output formats

**DON'T:**
- Assume subagent has prior context
- Send unbounded payloads
- Include sensitive data unnecessarily
- Use ambiguous references

---

### C. Error Handling

**DO:**
- Choose appropriate error strategy (fail-fast vs fail-tolerant)
- Log all delegation failures with context
- Provide actionable error messages
- Implement retries for transient failures
- Use circuit breakers for failing services

**DON'T:**
- Fail silently
- Retry indefinitely
- Ignore partial failures
- Leak sensitive data in errors

---

## X. ANTI-PATTERNS

### A. Over-Delegation

**Problem:** Delegating trivial tasks, adding overhead without benefit.

**Example:**
```python
# WRONG - delegation overhead > task time
result = await delegate_to_agent(
    agent="calculator",
    action="add",
    params={"a": 2, "b": 3}
)

# RIGHT - do simple calculations directly
result = 2 + 3
```

---

### B. Delegation Ping-Pong

**Problem:** Agents delegating back and forth.

**Example:**
```
Agent A: "I need schedule validation"
  └─> Delegates to Agent B

Agent B: "I need schedule data"
  └─> Delegates back to Agent A (!)

Agent A: "I need data formatted"
  └─> Delegates to Agent C

Agent C: "I need validation"
  └─> Delegates to Agent B (!)
```

**Solution:** Plan delegation graph, avoid cycles.

---

### C. Context Loss

**Problem:** Important context lost during handoff.

**Example:**
```python
# WRONG - incomplete context
await delegate_to_agent(
    agent="acgme-compliance",
    action="validate",
    params={"schedule_id": "uuid"}
    # Missing: which rules to check, validation depth, etc.
)

# RIGHT - complete context
await delegate_to_agent(
    agent="acgme-compliance",
    action="validate",
    params={
        "schedule_id": "uuid",
        "rules": ["80_hour", "1_in_7", "supervision"],
        "validation_depth": "comprehensive",
        "period": "Q2-2025"
    }
)
```

---

### D. Unbounded Parallelism

**Problem:** Spawning unlimited parallel agents.

**Example:**
```python
# WRONG - could spawn thousands of agents
tasks = [
    delegate_to_agent(agent="validator", action="check", params={"id": id})
    for id in all_schedule_ids  # Could be 10,000+
]
results = await asyncio.gather(*tasks)  # Resource exhaustion!

# RIGHT - batch with concurrency limit
async def process_in_batches(ids, batch_size=10):
    results = []
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        batch_results = await asyncio.gather(*[
            delegate_to_agent(agent="validator", action="check", params={"id": id})
            for id in batch
        ])
        results.extend(batch_results)
    return results

results = await process_in_batches(all_schedule_ids, batch_size=10)
```

---

## XI. QUICK REFERENCE

### A. Delegation Patterns Cheat Sheet

| Pattern | When to Use | Example |
|---------|-------------|---------|
| **Parallel (Scatter-Gather)** | Independent tasks | Multi-perspective code review |
| **Sequential (Pipeline)** | Dependent steps | Schedule generation workflow |
| **Hybrid** | Parallel stages + sequential flow | Multi-objective optimization |
| **Fire-and-Forget** | Non-blocking background work | Report generation |
| **Blocking** | Need immediate result | Validation check |
| **Streaming** | Long task with incremental output | Large data processing |

### B. Synthesis Patterns Cheat Sheet

| Pattern | Logic | Example Use Case |
|---------|-------|------------------|
| **All-or-Nothing** | AND (all must succeed) | ACGME compliance validation |
| **Best-Effort** | OR (any success sufficient) | Multiple swap candidates |
| **Majority Vote** | Consensus (>50% agreement) | Code review approval |
| **Weighted Aggregation** | Weighted average | Multi-objective scoring |
| **Merge-Deduplicate** | Combine unique items | Conflict detection |

### C. Error Strategies Cheat Sheet

| Strategy | Behavior | Example Use Case |
|----------|----------|------------------|
| **Fail-Fast** | Abort on first error | Safety-critical pipeline |
| **Fail-Tolerant** | Continue despite errors | Best-effort reporting |
| **Retry-with-Backoff** | Retry with delays | Transient network errors |
| **Circuit-Breaker** | Stop if consistently failing | Protect against cascading failures |

---

## XII. DECISION FLOWCHART

```
Task Analysis
    |
    ├─ Single simple task? ──YES──> Execute directly (no delegation)
    |                        |
    |                        NO
    |                        |
    ├─ Multiple independent tasks? ──YES──> Parallel Delegation (Scatter-Gather)
    |                                  |
    |                                  NO
    |                                  |
    ├─ Sequential dependencies? ──YES──> Sequential Delegation (Pipeline)
    |                             |
    |                             NO
    |                             |
    ├─ Requires specialization? ──YES──> Delegate to Specialist
    |                             |
    |                             NO
    |                             |
    └─ Execute directly (edge case)
```

---

**END OF DELEGATION PATTERNS**

*Effective delegation amplifies agent capabilities while maintaining system coherence. Delegate wisely: when specialization, parallelism, or isolation provides clear value.*
