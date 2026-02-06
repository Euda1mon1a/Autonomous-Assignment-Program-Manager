# MCP Orchestration Guide

**Purpose**: Master reference for orchestrating complex multi-tool MCP workflows
**Audience**: AI agents, system integrators, advanced users
**Version**: 1.0
**Last Updated**: 2025-12-31

---

## Quick Start

If you're new to MCP orchestration:

1. **Read this**: MCP_TOOL_CHEATSHEET.md (5 min quick reference)
2. **Pick a use case**: One of the 4 workflows below
3. **Review the workflow**: WORKFLOW_*.md file (10-15 min)
4. **Execute**: Implement workflow steps in your code
5. **Reference**: Consult dependency graph when connecting tools

---

## Orchestration Architecture

### 4 Primary Workflows

```
1. SCHEDULE GENERATION
   Purpose: Generate new schedules with full validation
   Duration: 12-25 seconds
   Safety: TIER 2 (review before apply)
   Stages: Validation → Contingency → Warning → Risk Assessment → Generation → Validation
   File: WORKFLOW_SCHEDULE_GENERATION.md

2. COMPLIANCE CHECK
   Purpose: Validate existing schedule for violations
   Duration: 2-3 seconds
   Safety: TIER 1 (read-only)
   Stages: ACGME Rules → Detailed Analysis → Advanced Metrics → Synthesis
   File: WORKFLOW_COMPLIANCE_CHECK.md

3. SWAP EXECUTION
   Purpose: Execute schedule swaps with multi-stage validation
   Duration: 2-5 seconds + human review
   Safety: TIER 2 (preview + approval)
   Stages: Validation → Candidates → Impact → Review → Execution
   File: WORKFLOW_SWAP_EXECUTION.md

4. RESILIENCE ASSESSMENT
   Purpose: System-wide health and vulnerability analysis
   Duration: 5-8 seconds
   Safety: TIER 1 (read-only analysis)
   Stages: Quick Status → Contingency → Epidemiology → Analytics → Synthesis
   File: WORKFLOW_RESILIENCE_ASSESSMENT.md
```

### Cross-Cutting Concerns

```
Error Handling:
├─ Reference: WORKFLOW_ERROR_HANDLING.md
├─ Retry strategies, fallbacks, escalation
└─ Per-error-type handling patterns

Confidence Framework:
├─ Reference: MCP_CONFIDENCE_FRAMEWORK.md
├─ Confidence levels 0-1 in all responses
└─ Decision thresholds per workflow

Tool Health:
├─ Reference: MCP_TOOL_HEALTH_MONITOR.md
├─ Circuit breaker integration
└─ Performance SLAs and alerts

Dependency Management:
├─ Reference: MCP_TOOL_DEPENDENCY_GRAPH.md
├─ Tool sequencing and parallelization
└─ Circular dependency detection
```

---

## Orchestration Patterns

### Pattern 1: Serial Dependency Chain

**When**: Tools must run in sequence (output of T1 feeds T2)

```
T1 → T2 → T3 → Result

Example: Schedule Generation Phase 5
├─ Phase 1 validate_schedule → COMPLETE
├─ Proceed to Phase 2 run_contingency_analysis
├─ Which requires Phase 1 result
└─ Then execute Phase 3 early_warning (parallel)
```

**Implementation**:
```python
async def serial_workflow():
    # Phase 1 (required for Phase 2)
    validation = await validate_schedule(...)
    if not validation.is_compliant:
        raise ComplianceError("Phase 1 failed")

    # Phase 2 (depends on Phase 1)
    contingency = await run_contingency_analysis(
        schedule_id=validation.schedule_id
    )

    # Phase 3 (independent, can parallel with Phase 2)
    early_warning = await run_spc_analysis(...)

    return combine_results(validation, contingency, early_warning)
```

---

### Pattern 2: Parallel Batch (Fan-out)

**When**: Multiple independent tools, combine results after

```
      ┌─ T1
    ──┼─ T2
      ├─ T3
      └─ T4 (all parallel)
        │
        └─ Aggregate → Result
```

**Example: Compliance Check Phase 1**
```
├─ validate_schedule
├─ validate_schedule_by_id
├─ (both parallel, aggregate confidence)
└─ Pass/Fail
```

**Implementation**:
```python
async def parallel_batch_workflow():
    tasks = [
        validate_schedule(...),
        validate_schedule_by_id(...),
        detect_conflicts(...),
        analyze_workload_trend(...),
    ]

    results = await asyncio.gather(*tasks)

    # Aggregate
    all_passed = all(r.is_valid for r in results)
    avg_confidence = sum(r.confidence for r in results) / len(results)

    return {
        "passed": all_passed,
        "confidence": avg_confidence,
        "details": results,
    }
```

---

### Pattern 3: Tiered Execution (Fast→Medium→Slow)

**When**: Progressive deepening, stop early if all clear

```
Tier 1 (Fast): 0.5s
├─ Critical check
├─ If PASS → Maybe stop here
└─ If FAIL → Escalate

Tier 2 (Medium): 2-3s
├─ Detailed analysis (if Tier 1 needed it)
├─ If PASS → Stop
└─ If FAIL → Escalate

Tier 3 (Slow): 5+ s
├─ Exhaustive analysis (if Tier 2 needed it)
└─ Final decision
```

**Example: Resilience Assessment**
```
Tier 1 (Quick Status):
├─ check_utilization_threshold (instant)
├─ get_defense_level (instant)
└─ Quick decision on health

If Tier 1 shows YELLOW/RED:
Tier 2 (Contingency):
├─ run_contingency_analysis_deep (2-3s)
├─ calculate_blast_radius (1s)
└─ Identify vulnerabilities

If Tier 2 shows issues:
Tier 3 (Full Analysis):
├─ Parallel: all 8 early warning tools
├─ Aggregation
└─ get_unified_critical_index
```

**Implementation**:
```python
async def tiered_execution():
    # Tier 1
    utilization = await check_utilization_threshold()
    defense = await get_defense_level()

    if defense.level >= 3:  # YELLOW or worse
        # Tier 2
        contingency = await run_contingency_analysis_deep()
        blast = await calculate_blast_radius()

        if len(contingency.gaps) > 10:
            # Tier 3
            unified = await get_unified_critical_index()
            return {"severity": "critical", "index": unified}

    return {"severity": "ok", "defense_level": defense.level}
```

---

### Pattern 4: Star Topology (Hub Aggregation)

**When**: One central tool aggregates many inputs

```
    ┌─ T1 ──┐
    ├─ T2 ──┤
    ├─ T3 ──┤─→ HUB → Result
    ├─ T4 ──┤
    └─ T5 ──┘
```

**Example: Unified Critical Index**
```
Inputs (all parallel):
├─ run_contingency_analysis_deep
├─ analyze_hub_centrality
├─ calculate_burnout_rt
├─ detect_burnout_precursors
├─ run_spc_analysis
├─ calculate_fire_danger_index
├─ assess_creep_fatigue
└─ Plus 3 more

Hub: get_unified_critical_index
Output: Single unified risk score
```

**Implementation**:
```python
async def star_topology():
    # All tools in parallel
    results = await asyncio.gather(
        run_contingency_analysis_deep(...),
        analyze_hub_centrality(...),
        calculate_burnout_rt(...),
        detect_burnout_precursors(...),
        run_spc_analysis(...),
        # ... more tools
    )

    # Aggregate into unified index
    unified = await get_unified_critical_index(
        contingency=results[0],
        hub_analysis=results[1],
        epidemiology=results[2],
        # ... etc
    )

    return unified
```

---

### Pattern 5: Conditional Branch

**When**: Tool A result determines whether to run T2 or T3

```
    T1
    │
    ├─ If result = A → T2
    ├─ If result = B → T3
    └─ If result = C → Skip
```

**Example: Swap Execution Phase 3**
```
Phase 2: Find candidates
├─ If 3+ candidates found
│  └─ Phase 3: Impact assessment
├─ If 1-2 candidates
│  └─ Phase 3: Manual review
└─ If 0 candidates
   └─ Escalate to coordinator
```

**Implementation**:
```python
async def conditional_branch():
    # Phase 2: Get candidates
    candidates = await analyze_swap_candidates(...)

    if len(candidates) >= 3:
        # Path A: Automated impact assessment
        impact = await run_contingency_analysis(
            candidate_ids=[c.id for c in candidates[:3]]
        )
        return {"path": "automated", "impact": impact}

    elif len(candidates) > 0:
        # Path B: Manual coordinator review
        return {"path": "manual_review", "candidates": candidates}

    else:
        # Path C: Escalation
        return {"path": "escalate", "reason": "no_candidates"}
```

---

### Pattern 6: Retry Loop with Exponential Backoff

**When**: Tool may timeout transiently

```
Attempt 1 (100ms wait if fail)
Attempt 2 (500ms wait if fail)
Attempt 3 (2000ms wait if fail)
Success or Fail
```

**Implementation**:
```python
async def retry_with_backoff(tool_func, args, max_retries=3):
    """Retry tool with exponential backoff."""
    delay_ms = 100
    max_delay_ms = 5000

    for attempt in range(max_retries + 1):
        try:
            return await asyncio.wait_for(
                tool_func(*args),
                timeout=tool_timeout
            )
        except asyncio.TimeoutError:
            if attempt == max_retries:
                logger.error(f"{tool_func.__name__} failed after {max_retries} retries")
                raise

            await asyncio.sleep(delay_ms / 1000)
            delay_ms = min(delay_ms * 2, max_delay_ms)
            logger.warning(f"Retry {attempt + 1}/{max_retries} for {tool_func.__name__}")
```

---

## Decision Trees

### Schedule Generation Orchestration

```
START: Generate Schedule
  │
  ├─→ [PHASE 1] Validate Baseline
  │     ├─ validate_schedule
  │     ├─ check_utilization_threshold
  │     └─ detect_conflicts
  │     │
  │     └─ If FAIL:
  │        └─ Return ERROR (request manual fix)
  │     └─ If PASS:
  │        └─ Continue to Phase 2
  │
  ├─→ [PHASE 2] Contingency Analysis
  │     ├─ run_contingency_analysis_deep
  │     ├─ calculate_blast_radius
  │     └─ execute_sacrifice_hierarchy (preview)
  │     │
  │     └─ If critical gaps > 50%:
  │        └─ WARN (request contingency planning)
  │     └─ Else continue to Phase 3
  │
  ├─→ [PHASE 3] Early Warning (Parallel)
  │     ├─ detect_burnout_precursors
  │     ├─ run_spc_analysis
  │     ├─ calculate_fire_danger_index
  │     └─ predict_burnout_magnitude
  │     │
  │     └─ If CRITICAL signals: WARN
  │
  ├─→ [PHASE 4] Unified Risk Assessment
  │     ├─ get_unified_critical_index
  │     └─ If risk > 70: REQUEST REVIEW
  │
  ├─→ [PHASE 5] Execute Generation
  │     ├─ Call backend /schedules/generate
  │     └─ If timeout:
  │        └─ Retry with greedy algorithm
  │
  ├─→ [PHASE 6] Post-Validation
  │     ├─ validate_schedule (new schedule)
  │     ├─ detect_conflicts
  │     └─ run_contingency_analysis
  │     │
  │     └─ If COMPLIANT: Ready for review
  │     └─ If NOT COMPLIANT: Show violations
  │
  ├─→ [PHASE 7] Human Approval
  │     ├─ Present to coordinator
  │     ├─ Review checklist
  │     └─ Get approval signature
  │
  └─→ [PHASE 8] Deploy
        ├─ Update schedule in database
        └─ Send notifications
```

### Compliance Check Orchestration

```
START: Check Compliance
  │
  ├─→ [PHASE 1] ACGME Rules (Parallel)
  │     ├─ validate_schedule
  │     └─ validate_schedule_by_id
  │     └─ If any FAIL: Report violations
  │
  ├─→ [PHASE 2] Detailed Analysis (Parallel)
  │     ├─ detect_conflicts
  │     ├─ analyze_workload_trend
  │     └─ analyze_supply_demand_cycles
  │
  ├─→ [PHASE 3] Advanced Metrics (Parallel)
  │     ├─ run_spc_analysis
  │     ├─ calculate_process_capability
  │     ├─ calculate_equity_metrics
  │     └─ check_utilization_threshold
  │
  ├─→ [PHASE 4] Synthesis
  │     ├─ Aggregate all violations
  │     ├─ Rank by severity
  │     └─ Generate recommendations
  │
  └─→ [OUTPUT] Compliance Report
        ├─ Score: 0-100
        ├─ Status: COMPLIANT / ISSUES / CRITICAL
        └─ Recommendations: [list]
```

---

## Error Recovery Scenarios

### Scenario 1: Tool Timeout in Critical Path

```
Tool: validate_schedule (Phase 1)
Error: Timeout after 5 seconds
Dependency: Phase 2 requires Phase 1 result
Recovery:

Step 1: Retry (exponential backoff)
  └─ Retry up to 2 more times
  └─ If succeeds: Continue normally

Step 2: Fallback to Cached Result
  └─ If validate_schedule cached (< 6h): Use it
  └─ Mark result: "Using cached validation"
  └─ Continue to Phase 2

Step 3: Simplified Validation
  └─ Run quick validation (100ms)
  └─ Mark as "Quick validation only"
  └─ Continue to Phase 2 with caveats

Step 4: Block Workflow (Critical Failure)
  └─ If all above fail
  └─ Return error to user
  └─ "Cannot proceed - validation unavailable"
```

### Scenario 2: Compliance Violation Detected in Phase 6

```
Situation: Post-validation shows ACGME violation
Tool: validate_schedule (Phase 6)
Error: Generated schedule violates 80-hour rule
Recovery:

Step 1: Detailed Violation Report
  └─ Identify exact violation
  └─ Show affected people
  └─ Suggest specific fix

Step 2: Request Modification
  └─ Return schedule with annotations
  └─ Suggest: "Reduce Jane's assignments by 2 blocks"
  └─ Allow user to modify and resubmit

Step 3: Manual Override (if approved)
  └─ Coordinator can approve violation
  └─ Must document reason
  └─ Create exception record
  └─ Log for compliance audit

Step 4: Regenerate (if requested)
  └─ Go back to Phase 1
  └─ Tighten constraints
  └─ Re-run generation with new constraints
```

### Scenario 3: Circuit Breaker Open

```
Tool: run_contingency_analysis_deep (Phase 2)
Status: Circuit breaker OPEN (too many failures)
Recovery:

Step 1: Fast Fail
  └─ Reject request immediately
  └─ Don't waste time trying to execute
  └─ Return: "Service temporarily unavailable"

Step 2: Use Fallback
  └─ If cached contingency available (< 12h)
  └─ Return cached analysis
  └─ Mark as: "Using cached data from X hours ago"

Step 3: Skip Phase / Reduce Scope
  └─ Continue workflow without this tool
  └─ Skip detailed contingency analysis
  └─ Focus on core validation
  └─ Flag for human review

Step 4: Wait for Recovery
  └─ Circuit breaker tries recovery every 30-60s
  └─ When service recovers → Close circuit
  └─ Resume normal operation

Step 5: Manual Intervention
  └─ If circuit open > 5 minutes
  └─ Alert coordinator
  └─ Provide diagnostic info
  └─ Offer manual override
```

---

## Integration Checklist

Before deploying a new workflow:

```
Workflow Planning:
  ☐ Defined all workflow phases
  ☐ Identified tool sequence
  ☐ Mapped dependencies (parallelizable sections)
  ☐ Set confidence thresholds per phase
  ☐ Documented decision points

Error Handling:
  ☐ Defined recovery strategy for each tool
  ☐ Set timeout values (SLA)
  ☐ Identified fallback data sources
  ☐ Planned escalation paths
  ☐ Documented retry logic

Testing:
  ☐ Unit tests for each tool
  ☐ Integration tests for workflow
  ☐ Error scenario tests
  ☐ Load testing (concurrent users)
  ☐ Timeout/recovery testing

Monitoring:
  ☐ Health check configured per tool
  ☐ Alert thresholds set
  ☐ Metrics collection enabled
  ☐ Dashboard created
  ☐ Incident response documented

Documentation:
  ☐ Workflow overview written
  ☐ Decision trees documented
  ☐ User guide created
  ☐ Troubleshooting guide
  ☐ Example code provided

Deployment:
  ☐ Code reviewed
  ☐ Security audited
  ☐ Load tested
  ☐ Staged rollout plan
  ☐ Rollback procedure ready
```

---

## Performance Optimization

### Parallel Execution Strategy

```
For Schedule Generation:
├─ Phase 1: 3 tools parallel (0.5s)
├─ Phase 2: Sequential (2-3s)
├─ Phase 3: 5 tools parallel (1-2s)
├─ Phase 4: 1 tool (0.5s)
├─ Phase 5: Backend (5-10s)
├─ Phase 6: 4 tools parallel (1-2s)
└─ Total: 12-19s (vs 30s if all serial)

For Resilience Assessment:
├─ Phase 1: 3 tools parallel (0.5s)
├─ Phase 2: Sequential (2-3s)
├─ Phase 3: 2 tools parallel (1-2s)
├─ Phase 4: 8 tools parallel (1-2s)
├─ Phase 5: 1 tool (0.5s)
└─ Total: 5-8s (vs 15s if all serial)
```

### Caching Strategy

```
Cache Tool Results:
├─ validate_schedule: 6 hours (ACGME never changes)
├─ contingency_analysis: 12 hours (stable if no roster changes)
├─ early_warning: 2 hours (data refreshes frequently)
├─ unified_critical_index: 4 hours (aggregate of others)
└─ On data change: Invalidate related caches

Cache Keys:
├─ By date range: cache_key = f"validate_schedule:{start_date}:{end_date}"
├─ By person: cache_key = f"workload_trend:{person_id}:{end_date}"
├─ By system: cache_key = f"unified_index:{system_id}:{date.today()}"
└─ TTL: Set based on data volatility
```

### Dependency Prefetching

```
If workflow will need tool B:
├─ Trigger tool A's dependencies early
├─ Cache/warm database connections
├─ Pre-load frequently-accessed data
└─ Example: Before schedule generation, pre-load all assignments

Benefits:
├─ Reduces critical path latency
├─ Smoother execution
├─ Better user experience
```

---

## Advanced Topics

### Multi-User Orchestration

When multiple operators use system simultaneously:

```
Scheduling:
├─ Lock schedule during generation
├─ Queue conflicting operations
├─ Maintain audit trail
└─ Notify blocked users

Swap Execution:
├─ Detect race conditions (both trying same swap)
├─ Serialize approval checks
├─ Version schedule before apply
└─ Rollback if conflict detected

Resilience Assessment:
├─ Can run in parallel (read-only)
├─ Combine results safely
├─ Eventual consistency OK
└─ No locking needed
```

### Scheduled Execution (Cron)

```
Daily (6 AM):
├─ Run resilience assessment
├─ Check all tool health
├─ Generate morning report

Weekly (Monday 8 AM):
├─ Generate next week's schedule
├─ Deep compliance check
├─ Equity analysis

On-demand:
├─ User-triggered via API
├─ Immediate execution
└─ Real-time results
```

---

## References

- **MCP_TOOL_DEPENDENCY_GRAPH.md**: Detailed dependencies
- **MCP_CONFIDENCE_FRAMEWORK.md**: Confidence decision logic
- **MCP_TOOL_HEALTH_MONITOR.md**: Health check integration
- **WORKFLOW_ERROR_HANDLING.md**: Error recovery patterns
- **4 Workflow files**: Phase-by-phase orchestration

---

**Last Updated**: 2025-12-31
**Version**: 1.0
**Status**: Production-Ready
**Review Frequency**: Quarterly
