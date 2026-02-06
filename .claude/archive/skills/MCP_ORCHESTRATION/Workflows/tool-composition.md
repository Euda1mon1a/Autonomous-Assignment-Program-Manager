# Tool Composition Workflow

Patterns for chaining multiple MCP tools into complex workflows.

## Overview

Individual tools provide discrete capabilities. Tool composition creates powerful workflows by connecting tools in directed acyclic graphs (DAGs), handling data transformation between tools, and managing error propagation.

## DAG Patterns

### Pattern 1: Linear Chain

```
Tool A → Tool B → Tool C → Result
```

**Characteristics:**
- Each tool depends on previous tool's output
- Sequential execution (no parallelism)
- Error in any step aborts entire chain
- Result accumulates data from all steps

**Example: Schedule Generation Pipeline**

```python
async def schedule_generation_pipeline(
    start_date: str,
    end_date: str,
    algorithm: str = "cp_sat"
):
    """Generate and validate schedule in linear chain."""

    # Step 1: Generate schedule
    gen_result = await call_tool_with_retry(
        "generate_schedule",
        start_date=start_date,
        end_date=end_date,
        algorithm=algorithm,
        timeout_seconds=120,
        clear_existing=True,
    )

    if gen_result.status != "success":
        raise RuntimeError(f"Generation failed: {gen_result.message}")

    # Step 2: Validate generated schedule
    val_result = await call_tool_with_retry(
        "validate_schedule_tool",
        start_date=start_date,
        end_date=end_date,
    )

    if not val_result.is_valid:
        logger.warning(
            f"Generated schedule has {val_result.critical_issues} critical issues"
        )

    # Step 3: Detect conflicts
    conflict_result = await call_tool_with_retry(
        "detect_conflicts_tool",
        start_date=start_date,
        end_date=end_date,
        include_auto_resolution=True,
    )

    # Step 4: Check utilization
    utilization_result = await call_tool_with_retry(
        "check_utilization_threshold_tool",
        available_faculty=gen_result.details.get("total_faculty", 10),
        required_blocks=gen_result.total_blocks_assigned,
    )

    # Aggregate results
    return {
        "generation": gen_result,
        "validation": val_result,
        "conflicts": conflict_result,
        "utilization": utilization_result,
        "overall_status": "success" if val_result.is_valid else "needs_review",
    }
```

### Pattern 2: Parallel Fan-Out

```
       → Tool B →
Tool A → Tool C → Aggregate
       → Tool D →
```

**Characteristics:**
- Multiple tools execute concurrently on same input
- Significantly faster than sequential
- All tools must complete before aggregation
- Partial failures possible (handle gracefully)

**Example: Comprehensive Schedule Analysis**

```python
import asyncio

async def comprehensive_schedule_analysis(
    start_date: str,
    end_date: str,
):
    """Run multiple analysis tools in parallel."""

    # Fan-out: Execute all analysis tools concurrently
    tasks = [
        call_tool_with_retry(
            "validate_schedule_tool",
            start_date=start_date,
            end_date=end_date,
        ),
        call_tool_with_retry(
            "detect_conflicts_tool",
            start_date=start_date,
            end_date=end_date,
        ),
        call_tool_with_retry(
            "run_contingency_analysis_tool",
            scenario="faculty_absence",
            affected_person_ids=["faculty-001"],
            start_date=start_date,
            end_date=end_date,
        ),
        call_tool_with_retry(
            "check_utilization_threshold_tool",
            available_faculty=10,
            required_blocks=730,
        ),
    ]

    # Gather results (wait for all to complete)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle partial failures
    validation, conflicts, contingency, utilization = results

    if isinstance(validation, Exception):
        logger.error(f"Validation failed: {validation}")
        validation = None

    if isinstance(conflicts, Exception):
        logger.error(f"Conflict detection failed: {conflicts}")
        conflicts = None

    if isinstance(contingency, Exception):
        logger.error(f"Contingency analysis failed: {contingency}")
        contingency = None

    if isinstance(utilization, Exception):
        logger.error(f"Utilization check failed: {utilization}")
        utilization = None

    # Aggregate results (even with partial failures)
    return {
        "validation": validation,
        "conflicts": conflicts,
        "contingency": contingency,
        "utilization": utilization,
        "success_count": sum(1 for r in results if not isinstance(r, Exception)),
        "failure_count": sum(1 for r in results if isinstance(r, Exception)),
    }
```

### Pattern 3: Map-Reduce

```
         → Task 1 →
Input →  → Task 2 → Reduce → Result
         → Task 3 →
```

**Characteristics:**
- Apply same tool to multiple inputs in parallel
- Aggregate/reduce results into single output
- Excellent for batch operations
- Requires result synthesis logic

**Example: Multi-Person Swap Analysis**

```python
async def find_best_swaps_for_team(
    faculty_ids: list[str],
    target_date_range: tuple[str, str],
):
    """Find optimal swap candidates for multiple faculty members."""

    # Map: Analyze swaps for each faculty member in parallel
    swap_tasks = [
        call_tool_with_retry(
            "analyze_swap_candidates_tool",
            requester_person_id=faculty_id,
            assignment_id=f"assign-{faculty_id}",
            preferred_start_date=target_date_range[0],
            preferred_end_date=target_date_range[1],
            max_candidates=10,
        )
        for faculty_id in faculty_ids
    ]

    swap_results = await asyncio.gather(*swap_tasks, return_exceptions=True)

    # Reduce: Aggregate and rank all candidates
    all_candidates = []
    for faculty_id, result in zip(faculty_ids, swap_results):
        if isinstance(result, Exception):
            logger.warning(f"Swap analysis failed for {faculty_id}: {result}")
            continue

        for candidate in result.candidates:
            all_candidates.append({
                "requester": faculty_id,
                "candidate": candidate.candidate_person_id,
                "match_score": candidate.match_score,
                "rotation": candidate.rotation,
                "mutual_benefit": candidate.mutual_benefit,
            })

    # Sort by match score
    all_candidates.sort(key=lambda c: c["match_score"], reverse=True)

    return {
        "total_candidates": len(all_candidates),
        "top_10_matches": all_candidates[:10],
        "mutual_benefit_count": sum(1 for c in all_candidates if c["mutual_benefit"]),
    }
```

### Pattern 4: Conditional Routing

```
Tool A → Decision
           ├→ (condition A) → Tool B
           ├→ (condition B) → Tool C
           └→ (else)        → Tool D
```

**Characteristics:**
- Route to different tools based on intermediate results
- Enables complex business logic
- Supports early termination on certain conditions

**Example: Deployment with Conditional Rollback**

```python
async def smart_deployment_workflow(
    git_ref: str,
    approval_token: str,
):
    """Deploy with conditional rollback based on validation."""

    # Step 1: Validate deployment
    validation = await call_tool_with_retry(
        "validate_deployment_tool",
        environment="staging",
        git_ref=git_ref,
        dry_run=False,
    )

    # Conditional routing based on validation
    if not validation.valid:
        logger.error(f"Deployment validation failed: {validation.blockers}")

        # Route to rollback (even though nothing deployed yet)
        return {
            "status": "blocked",
            "blockers": validation.blockers,
            "recommended_action": "Fix validation issues before deploying",
        }

    # Step 2: Run security scan
    security_scan = await call_tool_with_retry(
        "run_security_scan_tool",
        git_ref=git_ref,
    )

    # Conditional routing based on security
    if not security_scan.passed:
        critical_vulns = security_scan.severity_summary.get("critical", 0)

        if critical_vulns > 0:
            logger.error(f"Critical vulnerabilities detected: {critical_vulns}")

            return {
                "status": "blocked",
                "reason": "Critical security vulnerabilities",
                "vulnerabilities": security_scan.vulnerabilities,
                "recommended_action": "Patch vulnerabilities before deploying",
            }

    # Step 3: Run smoke tests on staging
    smoke_tests = await call_tool_with_retry(
        "run_smoke_tests_tool",
        environment="staging",
        test_suite="full",
    )

    # Conditional routing based on smoke tests
    if not smoke_tests.passed:
        logger.error("Smoke tests failed on staging")

        return {
            "status": "blocked",
            "reason": "Staging smoke tests failed",
            "failed_tests": [
                r for r in smoke_tests.results if r.status == "failed"
            ],
            "recommended_action": "Fix failing tests before promoting to production",
        }

    # All checks passed - promote to production
    logger.info("All checks passed. Promoting to production.")

    promotion = await call_tool_with_retry(
        "promote_to_production_tool",
        staging_version=git_ref,
        approval_token=approval_token,
    )

    return {
        "status": "deployed",
        "deployment_id": promotion.deployment_id,
        "version": promotion.production_version,
    }
```

## Data Transformation Between Tools

### Type Mapping

Tools have different input/output schemas. Transform data between tools:

```python
from datetime import date

def transform_schedule_status_to_validation_input(
    schedule_status: dict,
) -> dict:
    """Transform schedule_status output to validate_schedule input."""

    return {
        "start_date": schedule_status["period"]["start_date"],
        "end_date": schedule_status["period"]["end_date"],
        "check_work_hours": True,
        "check_supervision": True,
        "check_rest_periods": True,
        "check_consecutive_duty": True,
    }


def transform_validation_to_conflict_detection(
    validation_result: dict,
) -> dict:
    """Extract conflict types from validation issues."""

    conflict_types = set()

    for issue in validation_result.get("issues", []):
        rule_type = issue.get("rule_type", "")

        if "work_hour" in rule_type:
            conflict_types.add("work_hour_violation")
        elif "supervision" in rule_type:
            conflict_types.add("supervision_gap")
        elif "rest" in rule_type:
            conflict_types.add("rest_period_violation")

    return {
        "start_date": validation_result["date_range"][0],
        "end_date": validation_result["date_range"][1],
        "conflict_types": list(conflict_types) if conflict_types else None,
        "include_auto_resolution": True,
    }
```

### Schema Adapter Pattern

```python
from typing import Any, Callable

class ToolAdapter:
    """Adapter to transform data between incompatible tools."""

    def __init__(
        self,
        source_tool: str,
        target_tool: str,
        transform_fn: Callable[[Any], dict],
    ):
        self.source_tool = source_tool
        self.target_tool = target_tool
        self.transform_fn = transform_fn

    async def execute_chain(self, **source_params):
        """Execute source tool, transform, execute target tool."""

        # Execute source tool
        source_result = await call_tool_with_retry(
            self.source_tool,
            **source_params
        )

        # Transform result to target input
        target_params = self.transform_fn(source_result)

        # Execute target tool
        target_result = await call_tool_with_retry(
            self.target_tool,
            **target_params
        )

        return {
            "source": source_result,
            "target": target_result,
        }


# Usage example
validation_to_conflicts_adapter = ToolAdapter(
    source_tool="validate_schedule_tool",
    target_tool="detect_conflicts_tool",
    transform_fn=transform_validation_to_conflict_detection,
)

result = await validation_to_conflicts_adapter.execute_chain(
    start_date="2025-01-01",
    end_date="2025-01-31",
)
```

## Error Propagation in Chains

### Fail-Fast Strategy

Stop execution on first error:

```python
async def fail_fast_chain(*tool_calls):
    """Execute tools sequentially, abort on first error."""

    results = []

    for tool_name, params in tool_calls:
        try:
            result = await call_tool_with_retry(tool_name, **params)
            results.append(result)

        except Exception as e:
            logger.error(f"Chain aborted at {tool_name}: {e}")
            raise  # Propagate error, abort chain

    return results
```

### Graceful Degradation Strategy

Continue execution even if some tools fail:

```python
async def graceful_chain(*tool_calls):
    """Execute tools sequentially, continue on errors."""

    results = []
    errors = []

    for tool_name, params in tool_calls:
        try:
            result = await call_tool_with_retry(tool_name, **params)
            results.append(result)

        except Exception as e:
            logger.warning(f"Tool {tool_name} failed (continuing): {e}")
            errors.append({"tool": tool_name, "error": str(e)})
            results.append(None)  # Placeholder

    return {
        "results": results,
        "errors": errors,
        "success_rate": sum(1 for r in results if r is not None) / len(results),
    }
```

### Retry Chain Strategy

Retry entire chain on failure:

```python
async def retry_entire_chain(tool_calls: list, max_retries: int = 3):
    """Retry entire chain if any tool fails."""

    for attempt in range(max_retries):
        try:
            results = []

            for tool_name, params in tool_calls:
                result = await call_tool_with_retry(tool_name, **params)
                results.append(result)

            # All succeeded
            return results

        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Chain failed after {max_retries} retries: {e}")
                raise

            logger.warning(f"Chain retry {attempt + 1}/{max_retries}: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Result Synthesis

### Aggregation Strategies

#### Sum/Count Aggregation

```python
def aggregate_counts(results: list[dict]) -> dict:
    """Aggregate counts from multiple results."""

    return {
        "total_issues": sum(r.get("total_issues", 0) for r in results),
        "critical_count": sum(r.get("critical_issues", 0) for r in results),
        "warning_count": sum(r.get("warning_issues", 0) for r in results),
    }
```

#### Max/Min Aggregation

```python
def aggregate_severity(results: list[dict]) -> dict:
    """Find highest severity across results."""

    severity_order = ["info", "warning", "critical", "emergency"]

    max_severity = "info"
    for result in results:
        result_severity = result.get("severity", "info")
        if severity_order.index(result_severity) > severity_order.index(max_severity):
            max_severity = result_severity

    return {"max_severity": max_severity}
```

#### Merge Aggregation

```python
def merge_recommendations(results: list[dict]) -> dict:
    """Merge recommendations from multiple tools."""

    all_recommendations = []

    for result in results:
        all_recommendations.extend(result.get("recommendations", []))

    # Deduplicate
    unique_recommendations = list(set(all_recommendations))

    return {"recommendations": unique_recommendations}
```

### Complex Synthesis Example

```python
async def synthesize_schedule_health_report(start_date: str, end_date: str):
    """Create comprehensive health report from multiple tools."""

    # Run tools in parallel
    validation, conflicts, contingency, utilization = await asyncio.gather(
        call_tool_with_retry("validate_schedule_tool", start_date=start_date, end_date=end_date),
        call_tool_with_retry("detect_conflicts_tool", start_date=start_date, end_date=end_date),
        call_tool_with_retry("run_contingency_analysis_resilience_tool"),
        call_tool_with_retry("check_utilization_threshold_tool", available_faculty=10, required_blocks=730),
        return_exceptions=True,
    )

    # Synthesize overall health score
    health_score = 100.0

    # Validation: -10 per critical issue
    if not isinstance(validation, Exception):
        health_score -= validation.critical_issues * 10

    # Conflicts: -5 per conflict
    if not isinstance(conflicts, Exception):
        health_score -= conflicts.total_conflicts * 5

    # Contingency: -20 if N-1 fails, -50 if N-2 fails
    if not isinstance(contingency, Exception):
        if not contingency.n1_pass:
            health_score -= 20
        if not contingency.n2_pass:
            health_score -= 50

    # Utilization: -30 if in red zone
    if not isinstance(utilization, Exception):
        if utilization.level == "red":
            health_score -= 30
        elif utilization.level == "orange":
            health_score -= 15

    health_score = max(0, health_score)  # Floor at 0

    # Synthesize severity
    if health_score >= 80:
        severity = "healthy"
    elif health_score >= 60:
        severity = "warning"
    elif health_score >= 40:
        severity = "critical"
    else:
        severity = "emergency"

    return {
        "health_score": health_score,
        "severity": severity,
        "validation": validation if not isinstance(validation, Exception) else None,
        "conflicts": conflicts if not isinstance(conflicts, Exception) else None,
        "contingency": contingency if not isinstance(contingency, Exception) else None,
        "utilization": utilization if not isinstance(utilization, Exception) else None,
        "timestamp": datetime.utcnow().isoformat(),
    }
```

## Example: Check Swap Safety Chain

**Goal:** Verify a schedule swap is safe before executing

```python
async def check_swap_safety(
    requester_id: str,
    assignment_id: str,
    candidate_id: str,
):
    """Multi-tool chain to verify swap safety."""

    # Step 1: Analyze swap candidates to get swap details
    candidates = await call_tool_with_retry(
        "analyze_swap_candidates_tool",
        requester_person_id=requester_id,
        assignment_id=assignment_id,
    )

    # Find the specific candidate
    target_candidate = None
    for c in candidates.candidates:
        if c.candidate_person_id == candidate_id:
            target_candidate = c
            break

    if not target_candidate:
        return {"safe": False, "reason": "Candidate not found"}

    # Step 2: Simulate swap (update database in memory)
    # This would call a backend endpoint to simulate the swap

    # Step 3: Validate the simulated schedule
    validation = await call_tool_with_retry(
        "validate_schedule_tool",
        start_date=target_candidate.date_range[0].isoformat(),
        end_date=target_candidate.date_range[1].isoformat(),
    )

    if not validation.is_valid:
        return {
            "safe": False,
            "reason": "Swap would create validation errors",
            "issues": validation.issues,
        }

    # Step 4: Check utilization impact
    # (Simplified - would need actual faculty counts)
    utilization = await call_tool_with_retry(
        "check_utilization_threshold_tool",
        available_faculty=10,
        required_blocks=730,
    )

    if utilization.level in ["red", "black"]:
        return {
            "safe": False,
            "reason": f"Swap would push utilization to {utilization.level}",
            "utilization": utilization,
        }

    # Step 5: Detect conflicts in swapped schedule
    conflicts = await call_tool_with_retry(
        "detect_conflicts_tool",
        start_date=target_candidate.date_range[0].isoformat(),
        end_date=target_candidate.date_range[1].isoformat(),
    )

    if conflicts.total_conflicts > 0:
        return {
            "safe": False,
            "reason": "Swap would create conflicts",
            "conflicts": conflicts.conflicts,
        }

    # All checks passed
    return {
        "safe": True,
        "candidate": target_candidate,
        "validation": validation,
        "utilization": utilization,
        "conflicts": conflicts,
    }
```

## Best Practices

1. **Design DAGs, not cyclic graphs** - Avoid circular dependencies
2. **Parallelize independent tools** - Significant performance gains
3. **Handle partial failures** - Don't assume all parallel tasks succeed
4. **Transform data explicitly** - Make schema conversions clear
5. **Log intermediate results** - Debug complex chains
6. **Use timeouts for entire chains** - Prevent infinite hangs
7. **Cache expensive results** - Avoid recomputing same data
8. **Document tool dependencies** - Make composition logic clear
9. **Test error propagation** - Ensure chains handle failures correctly
10. **Monitor chain performance** - Identify bottlenecks

## Related Files

- `error-handling.md` - Error recovery in chains
- `tool-discovery.md` - Finding tools for composition
- `../Reference/composition-examples.md` - Real-world examples
