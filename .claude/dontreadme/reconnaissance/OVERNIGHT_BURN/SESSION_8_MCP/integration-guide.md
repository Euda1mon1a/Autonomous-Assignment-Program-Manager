# MCP Tool Integration Guide
## Patterns, dependencies, and best practices for using 81 MCP tools

---

## Overview

The MCP server exposes 81 tools across 8 functional domains. This guide provides:
1. Integration patterns (how tools work together)
2. Dependency graphs (which tools depend on which)
3. Common workflows (multi-step operations)
4. Error handling (what can go wrong)
5. Performance optimization (efficient tool usage)

---

## Architecture Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Assistant (Claude)                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    MCP Protocol (JSON-RPC)
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    FastMCP Server                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 81 Registered Tools (organized across 8 domains)        │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                (httpx AsyncClient, retry logic)
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼────────┐              ┌─────────────▼──────┐
│  FastAPI       │              │    Celery          │
│  Backend       │              │    (async tasks)   │
│  (Database)    │              │    (Redis broker)  │
└────────────────┘              └────────────────────┘
```

---

## Tool Categories & Dependencies

### Category 1: Core Scheduling (No Dependencies)

**Tools:** `validate_schedule_*`, `detect_conflicts_*`, `analyze_swap_*`, `run_contingency_*`

**Dependencies:** None (call API directly)

**Typical Flow:**
```
User Input → Validation Tool → Conflict Detection → Swap Analysis → User Output
```

---

### Category 2: Async Task Management (Depends on: Celery, Redis)

**Tools:** `start_background_task_*`, `get_task_status_*`, `cancel_task_*`, `list_active_tasks_*`

**Prerequisites:**
```bash
# Start Celery worker
cd backend
../scripts/start-celery.sh worker

# Start Redis
docker-compose up -d redis
```

**Typical Flow:**
```
AI: Start task
    ↓
MCP: Submit to Celery broker
    ↓
Worker: Process in background
    ↓
AI: Poll for status (polling loop)
    ↓
AI: Retrieve result when complete
```

**Example:**
```python
# Step 1: Start task
task = start_background_task_tool(
    task_type=TaskType.RESILIENCE_CONTINGENCY,
    params={"days_ahead": 90}
)
# Returns: BackgroundTaskResult(task_id="abc123", status="pending")

# Step 2: Poll until complete
import time
while True:
    status = get_task_status_tool(task.task_id)
    if status.status == TaskStatus.SUCCESS:
        result = status.result  # Contingency analysis data
        break
    elif status.status == TaskStatus.FAILURE:
        error = status.error  # Error details
        break
    time.sleep(5)  # Poll every 5 seconds
```

---

### Category 3: Resilience Framework (Depends on: API Backend, Analytics)

**Tier 1 (No dependencies):**
- `check_utilization_threshold_tool()` - Pure calculation
- `get_defense_level_tool(coverage_rate)` - Pure calculation
- `run_contingency_analysis_resilience_tool()` - Calls API

**Tier 2 (Depends on: Tier 1 results):**
- `execute_sacrifice_hierarchy_tool()` - Uses utilization context
- `analyze_homeostasis_tool()` - Analyzes equilibrium

**Tier 3+ (Depends on: Analytics data):**
- `run_spc_analysis_tool()` - Requires schedule history
- `calculate_process_capability_tool()` - Requires compliance data
- `optimize_erlang_coverage_tool()` - Requires coverage metrics

**Typical Emergency Workflow:**
```
1. check_utilization_threshold_tool()
   ↓ (if RED/BLACK)
2. get_defense_level_tool()
   ↓ (if escalation_needed)
3. run_contingency_analysis_resilience_tool()
   ↓ (if feasible_alternatives > 0)
4. execute_sacrifice_hierarchy_tool()
   ↓
5. Result: actionable crisis response plan
```

---

### Category 4: Early Warning System (Depends on: Schedule History, Analytics)

**Data Requirements:**
- Minimum 14 days of historical data
- Person assignments
- Work hour records
- Absence patterns

**Tool Dependencies:**
```
detect_burnout_precursors_tool() → STA/LTA algorithm
predict_burnout_magnitude_tool() → Signal analysis
run_spc_analysis_tool() → 8 Western Electric rules
calculate_fire_danger_index_tool() → CFFDRS model
```

**Typical Monitoring Workflow:**
```
# Run daily/weekly
1. detect_burnout_precursors_tool()
   ↓ (if signal detected)
2. predict_burnout_magnitude_tool()
   ↓ (if magnitude > threshold)
3. run_spc_analysis_tool()  // Confirm via independent method
   ↓ (if out-of-control detected)
4. calculate_fire_danger_index_tool()  // Multi-temporal check
   ↓
5. Alert: "Burnout risk elevated"
```

---

### Category 5: Deployment Pipeline (Depends on: External Services)

**Tool Sequence:**
```
validate_deployment_tool()
    ↓ (passes)
run_security_scan_tool()
    ↓ (no vulns)
run_smoke_tests_tool()
    ↓ (passes)
benchmark_resilience_tool()  [optional]
    ↓
promote_to_production_tool()
    ↓
get_deployment_status_tool()  [verify]
    ↓
(If failure)
rollback_deployment_tool()
```

**Safety Gate Implementation:**
```python
def safe_deployment(env_from, env_to):
    # 1. Validation
    val = validate_deployment_tool(environment=env_from)
    if not val.passed:
        return {"status": "blocked", "reason": "validation failed"}

    # 2. Security
    sec = run_security_scan_tool(environment=env_from)
    if sec.vulnerabilities > 0:
        return {"status": "blocked", "reason": f"{sec.vulnerabilities} vulns"}

    # 3. Smoke tests
    tests = run_smoke_tests_tool(environment=env_from)
    if not tests.passed:
        return {"status": "blocked", "reason": "tests failed"}

    # 4. Promote
    try:
        result = promote_to_production_tool(source=env_from, target=env_to)
        return {"status": "success", "deployment_id": result.deployment_id}
    except Exception as e:
        rollback_deployment_tool(deployment_id=result.deployment_id)
        return {"status": "rolled_back", "reason": str(e)}
```

---

### Category 6: Metrics & Analytics (Depends on: Schedule Data)

**Fairness Analysis Chain:**
```
1. calculate_shapley_workload_tool()
   ↓ (gives workload attribution)
2. generate_lorenz_curve_tool()
   ↓ (visualizes inequality)
3. calculate_equity_metrics_tool()
   ↓ (computes indices)
Result: Fairness assessment with specific improvement targets
```

**Stability Analysis Chain:**
```
1. analyze_schedule_rigidity_tool()
   ↓ (measure changeability)
2. detect_critical_slowing_down_tool()
   ↓ (detect tipping points)
3. detect_schedule_changepoints_tool()
   ↓ (find behavior changes)
4. analyze_schedule_periodicity_tool()
   ↓ (detect natural cycles)
Result: Schedule structure understanding
```

---

### Category 7: Advanced Analytics (Research Tools)

**Hopfield Network Analysis:**
```
1. calculate_hopfield_energy_tool()
   ↓ (current state energy)
2. find_nearby_attractors_tool()
   ↓ (discover stable alternatives)
3. measure_basin_depth_tool()
   ↓ (assess robustness)
4. detect_spurious_attractors_tool()
   ↓ (identify anti-patterns)
Result: Schedule stability landscape
```

**Game Theory Analysis:**
```
1. analyze_nash_stability_tool()
   ↓ (find equilibria)
2. find_deviation_incentives_tool()
   ↓ (predict swap requests)
3. detect_coordination_failures_tool()
   ↓ (find Pareto gaps)
Result: Behavioral prediction model
```

**Risk Assessment:**
```
1. calculate_coverage_var_tool()
   ↓ (probabilistic bounds)
2. calculate_workload_var_tool()
   ↓ (distribution risk)
3. simulate_disruption_scenarios_tool()
   ↓ (Monte Carlo stress)
4. calculate_conditional_var_tool()
   ↓ (tail risk)
Result: Risk profile with confidence intervals
```

---

## Common Workflows

### Workflow 1: Morning Health Check (5 min)

```python
async def daily_health_check():
    """Quick morning system health assessment."""

    # 1. Utilization (30ms)
    util = check_utilization_threshold_tool()

    # 2. Burnout (300ms)
    precursors = detect_burnout_precursors_tool()

    # 3. Fatigue (200ms)
    fatigue = get_fatigue_score_tool()

    # 4. Drift (500ms)
    spc = run_spc_analysis_tool(window_days=7)

    # 5. Unified index (400ms)
    health = get_unified_critical_index_tool()

    # Synthesize
    report = {
        "timestamp": datetime.now(),
        "overall_health": health.score,  # 0-1
        "utilization_level": util.level,  # GREEN/YELLOW/ORANGE/RED/BLACK
        "burnout_signal": precursors.detected,
        "fatigue_score": fatigue.score,  # 0-100
        "drift_detected": spc.out_of_control,
    }

    # Alert if problems
    if health.score < 0.3:
        print("CRITICAL: System health degraded")
    elif precursors.detected:
        print("WARNING: Burnout signal detected")

    return report
```

**Estimated Duration:** 1.5-2 seconds

---

### Workflow 2: Emergency Response (10 min)

```python
async def emergency_response():
    """Crisis activation protocol."""

    # 1. Assess severity
    util = check_utilization_threshold_tool()

    if util.level not in ["RED", "BLACK"]:
        return {"status": "no_emergency"}

    # 2. Get defense status
    defense = get_defense_level_tool(util.utilization_rate)

    # 3. Run contingency analysis
    contingency = run_contingency_analysis_resilience_tool(
        include_fallbacks=True
    )

    # 4. Get sacrifice plan
    sacrifices = execute_sacrifice_hierarchy_tool(
        criteria="minimize_burnout",
        max_affected_people=50  # Limit scope
    )

    # 5. Start background task for detailed analysis
    task = start_background_task_tool(
        TaskType.RESILIENCE_CRISIS_ACTIVATION,
        {
            "severity": util.level,
            "reason": "Emergency activation",
            "approved_by": "duty_officer"
        }
    )

    return {
        "status": "activated",
        "defense_level": defense.current_level,
        "sacrifices": sacrifices.recommendations,
        "task_id": task.task_id  # For monitoring
    }
```

**Estimated Duration:** 2-5 seconds (+ background task)

---

### Workflow 3: Schedule Validation (15 min)

```python
async def validate_and_fix_schedule(start_date, end_date):
    """Comprehensive schedule validation with auto-fix suggestions."""

    # 1. Validate schedule
    validation = validate_schedule_tool(
        start_date=start_date,
        end_date=end_date,
        check_work_hours=True,
        check_supervision=True,
        check_rest_periods=True,
        check_consecutive_duty=True
    )

    if validation.is_valid:
        return {
            "status": "valid",
            "compliance_rate": validation.overall_compliance_rate
        }

    # 2. Analyze issues
    issues_by_type = {}
    for issue in validation.issues:
        issues_by_type.setdefault(issue.rule_type, []).append(issue)

    # 3. Detect conflicts
    conflicts = detect_conflicts_tool(
        date_range=(start_date, end_date),
        conflict_type="all"
    )

    # 4. Find swaps for each conflict
    fixes = []
    for conflict in conflicts.conflicts:
        for person_id in conflict.affected_people:
            swaps = analyze_swap_candidates_tool(
                person_id=person_id,
                date_range=(start_date, end_date)
            )
            if swaps.candidates:
                fixes.append({
                    "person": person_id,
                    "conflict": conflict.conflict_id,
                    "swap_option": swaps.candidates[0]  # Best option
                })

    return {
        "status": "invalid",
        "issues": {
            "critical": validation.critical_issues,
            "warnings": validation.warning_issues,
            "by_type": issues_by_type
        },
        "suggested_fixes": fixes
    }
```

**Estimated Duration:** 3-5 seconds

---

### Workflow 4: Fairness Audit (20 min)

```python
async def fairness_audit(start_date, end_date):
    """Comprehensive equity analysis with improvement plan."""

    # 1. Calculate Shapley values
    shapley = calculate_shapley_workload_tool(
        date_range=(start_date, end_date),
        method="shapley"
    )

    # 2. Get equality metrics
    equity = calculate_equity_metrics_tool(
        date_range=(start_date, end_date),
        include_roles=True
    )

    # 3. Generate Lorenz curve for visualization
    lorenz = generate_lorenz_curve_tool()

    # 4. Identify unfair allocations
    inequitable_people = [
        p for p in shapley.person_contributions
        if p.fairness_score < 0.7  # Below 70% fairness
    ]

    # 5. Find swap options to improve fairness
    improvement_plan = []
    for person in inequitable_people:
        swaps = analyze_swap_candidates_tool(
            person_id=person.person_id,
            date_range=(start_date, end_date)
        )
        if swaps.candidates:
            improvement_plan.append({
                "person": person.person_id,
                "current_fairness": person.fairness_score,
                "target_fairness": 0.85,
                "swap_option": swaps.candidates[0]
            })

    return {
        "equity_metrics": equity.metrics,
        "gini_coefficient": equity.gini,  # 0 = perfect equality
        "lorenz_curve": lorenz.curve_data,
        "unfair_allocations": len(inequitable_people),
        "improvement_plan": improvement_plan
    }
```

**Estimated Duration:** 2-3 seconds

---

### Workflow 5: Burnout Risk Assessment (10 min)

```python
async def burnout_risk_assessment():
    """Multi-method burnout analysis with interventions."""

    # Method 1: STA/LTA early warning
    sta_lta = detect_burnout_precursors_tool()

    # Method 2: SIR epidemiology model
    burnout_rt = calculate_burnout_rt_tool()

    # Method 3: CFFDRS fire danger index
    fire_danger = calculate_fire_danger_index_tool()

    # Method 4: FRMS fatigue assessment
    frms = run_frms_assessment_tool()

    # Method 5: Cognitive load
    cognitive = assess_cognitive_load_tool()

    # Synthesize consensus
    methods_detecting_risk = sum([
        sta_lta.signal_detected,
        burnout_rt.rt > 1.0,  # Spreading
        fire_danger.danger_level in ["EXTREME", "VERY_HIGH"],
        frms.overall_risk in ["HIGH", "CRITICAL"],
        cognitive.load_level in ["HEAVY", "EXTREME"]
    ])

    consensus_level = methods_detecting_risk / 5  # Consensus %

    # If multiple methods agree, escalate
    if consensus_level >= 0.6:  # 3+ methods agree
        # Start background contingency analysis
        task = start_background_task_tool(
            TaskType.RESILIENCE_CONTINGENCY,
            {"days_ahead": 30}
        )

        return {
            "status": "high_risk",
            "consensus_methods": methods_detecting_risk,
            "recommended_action": "reduce_workload",
            "intervention_task_id": task.task_id
        }
    else:
        return {
            "status": "manageable",
            "consensus_methods": methods_detecting_risk,
            "monitoring": "continue_daily_checks"
        }
```

**Estimated Duration:** 1-2 seconds

---

## Error Handling Patterns

### Pattern 1: Graceful Degradation

```python
async def resilient_health_check():
    """Health check with fallback if any tool fails."""

    results = {}

    # Primary: Unified index
    try:
        results["unified"] = get_unified_critical_index_tool()
    except Exception as e:
        logger.warning(f"Unified index failed: {e}")
        # Fallback: Use individual metrics
        try:
            util = check_utilization_threshold_tool()
            burnout = calculate_burnout_rt_tool()
            results["unified"] = {
                "score": (util.level_numeric + burnout.rt) / 2,
                "method": "fallback"
            }
        except Exception as e2:
            logger.error(f"Health check failed: {e2}")
            results["unified"] = {"score": None, "error": str(e2)}

    return results
```

### Pattern 2: Timeout Handling

```python
async def timeout_safe_analysis(timeout_seconds=30):
    """Tool call with timeout."""
    import asyncio

    try:
        result = await asyncio.wait_for(
            analyze_schedule_rigidity_tool(),
            timeout=timeout_seconds
        )
        return result
    except asyncio.TimeoutError:
        logger.error(f"Tool timeout after {timeout_seconds}s")
        return {"error": "timeout", "recommend_action": "retry_later"}
```

### Pattern 3: Retry Logic

```python
async def retry_tool_call(tool_func, max_retries=3, backoff=2):
    """Exponential backoff retry."""
    import time

    for attempt in range(max_retries):
        try:
            return await tool_func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = backoff ** attempt
            logger.warning(f"Attempt {attempt+1} failed, retrying in {wait_time}s")
            time.sleep(wait_time)
```

---

## Performance Optimization

### Optimization 1: Parallel Execution

```python
async def parallel_metrics():
    """Fetch independent metrics in parallel."""
    import asyncio

    util, burnout, fatigue, entropy = await asyncio.gather(
        check_utilization_threshold_tool(),
        calculate_burnout_rt_tool(),
        get_fatigue_score_tool(),
        get_entropy_monitor_state_tool()
    )

    return {
        "util": util,
        "burnout": burnout,
        "fatigue": fatigue,
        "entropy": entropy
    }
    # ~500ms instead of 1.5s sequential
```

### Optimization 2: Caching

```python
from functools import lru_cache
import time

cache_time = {}

async def cached_check_utilization(cache_duration=60):
    """Cache utilization check for 60 seconds."""
    now = time.time()

    if "util_cache" in cache_time:
        if now - cache_time["util_cache"] < cache_duration:
            return cache_time["util_result"]

    result = check_utilization_threshold_tool()
    cache_time["util_cache"] = now
    cache_time["util_result"] = result
    return result
```

### Optimization 3: Batch Operations

```python
async def batch_swap_analysis(person_ids, date_range):
    """Analyze swaps for multiple people in parallel."""
    import asyncio

    tasks = [
        analyze_swap_candidates_tool(pid, date_range)
        for pid in person_ids
    ]

    results = await asyncio.gather(*tasks)
    return dict(zip(person_ids, results))
```

---

## Tool Interdependencies Map

```
                    ┌─────────────────────────────────────┐
                    │  get_unified_critical_index_tool()  │
                    │  (Master synthesizer)               │
                    └──────────────┬──────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
check_utilization_         calculate_burnout_rt     get_entropy_monitor
_threshold_tool()          _tool()                   _state_tool()
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   │
                   detect_burnout_precursors_tool()
                   predict_burnout_magnitude_tool()
                   run_spc_analysis_tool()
                   (Independent verification methods)
```

---

## Recommendation: Tool Orchestration Framework

**Current State:** Tools are independent; AI orchestrates manually

**Recommended Improvement:** Create higher-order tools

```python
# Example: Composite tool (not yet implemented)
@mcp.tool()
async def morning_briefing() -> MorningBriefingResponse:
    """
    Single tool that internally chains:
    1. check_utilization_threshold_tool()
    2. detect_burnout_precursors_tool()
    3. get_fatigue_score_tool()
    4. run_spc_analysis_tool()
    5. get_unified_critical_index_tool()

    Returns: Single synthesized report
    """
```

Benefits:
- Reduced API calls
- Consistent error handling
- Documented tool chains
- Better performance (parallel execution)

---

**Version:** 1.0
**Date:** 2025-12-30
