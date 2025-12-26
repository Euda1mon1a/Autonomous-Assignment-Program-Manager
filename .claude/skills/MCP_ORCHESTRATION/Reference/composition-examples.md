# Tool Composition Examples

Real-world examples of multi-tool workflows with complete pseudocode and error handling.

## Overview

This document provides production-ready examples of complex tool orchestration patterns, including error handling, data transformation, and result synthesis.

---

## Example 1: Schedule Generation Chain

**Goal:** Generate validated schedule with resilience checks

**Tools Used:**
1. `check_utilization_threshold_tool` - Pre-flight capacity check
2. `generate_schedule` (via API) - Create schedule
3. `validate_schedule_tool` - ACGME validation
4. `detect_conflicts_tool` - Conflict detection
5. `run_contingency_analysis_resilience_tool` - N-1/N-2 vulnerability check

**Pattern:** Linear chain with conditional branching

```python
async def safe_schedule_generation(
    start_date: str,
    end_date: str,
    algorithm: str = "cp_sat",
) -> dict:
    """
    Generate schedule with comprehensive validation.

    Returns:
        dict with generation status, validation results, and recommendations
    """

    # Step 1: Pre-flight capacity check
    logger.info("Step 1/5: Checking utilization capacity")

    try:
        utilization = await call_tool_with_retry(
            "check_utilization_threshold_tool",
            available_faculty=10,  # Get from DB in production
            required_blocks=730,   # Calculate based on date range
        )

        if utilization.level in ["red", "black"]:
            logger.error(f"Utilization at {utilization.level} - cannot generate schedule")
            return {
                "status": "blocked",
                "reason": f"System utilization at {utilization.level} level",
                "utilization": utilization,
                "recommendation": "Reduce load or add capacity before generating",
            }

    except Exception as e:
        logger.warning(f"Utilization check failed: {e}. Proceeding anyway.")
        utilization = None

    # Step 2: Generate schedule
    logger.info("Step 2/5: Generating schedule")

    try:
        gen_result = await call_tool_with_retry(
            "generate_schedule",  # This calls backend API
            start_date=start_date,
            end_date=end_date,
            algorithm=algorithm,
            timeout_seconds=120,
            clear_existing=True,
        )

        if gen_result.status != "success":
            logger.error(f"Schedule generation failed: {gen_result.message}")
            return {
                "status": "failed",
                "reason": gen_result.message,
                "details": gen_result.details,
            }

    except Exception as e:
        logger.error(f"Schedule generation error: {e}")
        return {
            "status": "error",
            "reason": str(e),
        }

    # Step 3: Validate generated schedule
    logger.info("Step 3/5: Validating ACGME compliance")

    try:
        validation = await call_tool_with_retry(
            "validate_schedule_tool",
            start_date=start_date,
            end_date=end_date,
        )

        if not validation.is_valid:
            logger.warning(
                f"Generated schedule has {validation.critical_issues} critical issues"
            )

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        validation = None

    # Step 4: Detect conflicts
    logger.info("Step 4/5: Detecting conflicts")

    try:
        conflicts = await call_tool_with_retry(
            "detect_conflicts_tool",
            start_date=start_date,
            end_date=end_date,
            include_auto_resolution=True,
        )

    except Exception as e:
        logger.error(f"Conflict detection failed: {e}")
        conflicts = None

    # Step 5: Run contingency analysis
    logger.info("Step 5/5: Running N-1/N-2 contingency analysis")

    try:
        # Start as background task (takes 2-5 minutes)
        contingency_task = await call_tool_with_retry(
            "start_background_task_tool",
            task_type="resilience_contingency",
            params={"days_ahead": 90},
        )

        # Poll for completion (with timeout)
        contingency = None
        for _ in range(60):  # 5 minutes max
            await asyncio.sleep(5)

            status = await call_tool_with_retry(
                "get_task_status_tool",
                task_id=contingency_task.task_id,
            )

            if status.status == "success":
                contingency = status.result
                break

            elif status.status == "failure":
                logger.error(f"Contingency analysis failed: {status.error}")
                break

        if contingency is None:
            logger.warning("Contingency analysis incomplete")

    except Exception as e:
        logger.error(f"Contingency analysis error: {e}")
        contingency = None

    # Synthesize results
    overall_status = "success"
    issues = []

    if validation and not validation.is_valid:
        overall_status = "needs_review"
        issues.append(f"{validation.critical_issues} critical ACGME violations")

    if conflicts and conflicts.total_conflicts > 0:
        overall_status = "needs_review"
        issues.append(f"{conflicts.total_conflicts} scheduling conflicts")

    if contingency and not contingency.n1_pass:
        issues.append("System fails N-1 contingency (single faculty loss)")

    if contingency and not contingency.n2_pass:
        issues.append("System fails N-2 contingency (dual faculty loss)")

    return {
        "status": overall_status,
        "generation": gen_result,
        "validation": validation,
        "conflicts": conflicts,
        "contingency": contingency,
        "utilization": utilization,
        "issues": issues,
        "recommendations": _generate_recommendations(
            validation, conflicts, contingency, utilization
        ),
    }


def _generate_recommendations(validation, conflicts, contingency, utilization) -> list[str]:
    """Generate actionable recommendations from analysis results."""

    recommendations = []

    if validation and validation.critical_issues > 0:
        recommendations.append(
            f"Address {validation.critical_issues} critical ACGME violations before deployment"
        )

    if conflicts and conflicts.auto_resolvable_count > 0:
        recommendations.append(
            f"Apply auto-resolution to {conflicts.auto_resolvable_count} conflicts"
        )

    if contingency and not contingency.n1_pass:
        recommendations.append(
            "Add backup faculty or cross-train to pass N-1 contingency"
        )

    if utilization and utilization.level == "orange":
        recommendations.append(
            "Utilization in orange zone - monitor closely and prepare contingency plans"
        )

    return recommendations
```

**Error Handling:**
- Each step wrapped in try/except
- Failures logged but don't abort entire chain
- Missing results handled gracefully
- Final status reflects partial failures

**Output:**
```python
{
    "status": "success",  # or "needs_review", "failed", "blocked"
    "generation": {...},   # Generation details
    "validation": {...},   # Validation results
    "conflicts": {...},    # Conflict detection
    "contingency": {...},  # N-1/N-2 analysis
    "utilization": {...},  # Capacity check
    "issues": [...],       # List of issues found
    "recommendations": [...],  # Actionable recommendations
}
```

---

## Example 2: Swap Validation Chain

**Goal:** Verify schedule swap is safe before executing

**Tools Used:**
1. `analyze_swap_candidates_tool` - Get swap details
2. Backend API - Simulate swap
3. `validate_schedule_tool` - Validate simulated schedule
4. `detect_conflicts_tool` - Check for conflicts
5. `check_utilization_threshold_tool` - Check capacity impact

**Pattern:** Linear chain with data transformation

```python
async def validate_swap_safety(
    requester_id: str,
    assignment_id: str,
    candidate_id: str,
    approval_required: bool = True,
) -> dict:
    """
    Validate if a swap is safe before executing.

    Returns:
        dict with safety status and detailed analysis
    """

    # Step 1: Analyze swap candidates to get details
    logger.info(f"Step 1/5: Analyzing swap for {requester_id}")

    candidates = await call_tool_with_retry(
        "analyze_swap_candidates_tool",
        requester_person_id=requester_id,
        assignment_id=assignment_id,
        max_candidates=10,
    )

    # Find specific candidate
    target_candidate = None
    for c in candidates.candidates:
        if c.candidate_person_id == candidate_id:
            target_candidate = c
            break

    if not target_candidate:
        return {
            "safe": False,
            "reason": "Candidate not found in swap analysis",
            "available_candidates": [c.candidate_person_id for c in candidates.candidates],
        }

    # Step 2: Simulate swap (call backend API)
    logger.info("Step 2/5: Simulating swap in database")

    try:
        # This would be a backend API call to simulate the swap
        # For now, we'll use the assignment date range
        swap_date_range = target_candidate.date_range

    except Exception as e:
        logger.error(f"Failed to simulate swap: {e}")
        return {
            "safe": False,
            "reason": f"Simulation failed: {e}",
        }

    # Step 3: Validate simulated schedule
    logger.info("Step 3/5: Validating simulated schedule")

    try:
        validation = await call_tool_with_retry(
            "validate_schedule_tool",
            start_date=swap_date_range[0].isoformat(),
            end_date=swap_date_range[1].isoformat(),
        )

        if not validation.is_valid:
            logger.warning(
                f"Swap creates {validation.critical_issues} critical violations"
            )

            return {
                "safe": False,
                "reason": "Swap would create ACGME violations",
                "validation": validation,
                "issues": [
                    f"{issue.severity}: {issue.message}"
                    for issue in validation.issues
                    if issue.severity == "critical"
                ],
            }

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        # Conservative - reject swap if validation fails
        return {
            "safe": False,
            "reason": f"Unable to validate: {e}",
        }

    # Step 4: Detect conflicts
    logger.info("Step 4/5: Checking for conflicts")

    try:
        conflicts = await call_tool_with_retry(
            "detect_conflicts_tool",
            start_date=swap_date_range[0].isoformat(),
            end_date=swap_date_range[1].isoformat(),
        )

        if conflicts.total_conflicts > 0:
            logger.warning(f"Swap creates {conflicts.total_conflicts} conflicts")

            return {
                "safe": False,
                "reason": "Swap would create scheduling conflicts",
                "conflicts": conflicts,
                "conflict_details": [
                    f"{c.conflict_type}: {c.description}"
                    for c in conflicts.conflicts[:5]  # Top 5
                ],
            }

    except Exception as e:
        logger.warning(f"Conflict detection failed: {e}")
        # Non-blocking - continue without conflict check

    # Step 5: Check utilization impact
    logger.info("Step 5/5: Checking utilization impact")

    try:
        # Get current faculty count (would query DB in production)
        available_faculty = 10
        required_blocks = 730

        utilization = await call_tool_with_retry(
            "check_utilization_threshold_tool",
            available_faculty=available_faculty,
            required_blocks=required_blocks,
        )

        if utilization.level in ["red", "black"]:
            logger.warning(f"Swap pushes utilization to {utilization.level}")

            # Soft warning - don't block swap
            # But flag for approval
            if approval_required:
                return {
                    "safe": True,
                    "approval_required": True,
                    "reason": f"Swap pushes utilization to {utilization.level} - requires approval",
                    "utilization": utilization,
                }

    except Exception as e:
        logger.warning(f"Utilization check failed: {e}")

    # All checks passed
    logger.info(f"Swap validation passed for {requester_id} ↔ {candidate_id}")

    return {
        "safe": True,
        "candidate": {
            "id": target_candidate.candidate_person_id,
            "match_score": target_candidate.match_score,
            "rotation": target_candidate.rotation,
            "mutual_benefit": target_candidate.mutual_benefit,
        },
        "validation": {
            "is_valid": validation.is_valid,
            "compliance_rate": validation.overall_compliance_rate,
        },
        "conflicts": {
            "total": conflicts.total_conflicts if conflicts else 0,
        },
        "approval_required": approval_required and target_candidate.approval_likelihood == "high",
    }
```

**Data Transformations:**
- Extract date range from swap candidate
- Transform validation issues to simple strings
- Aggregate checks into single safety decision

**Error Handling:**
- Validation failure = reject swap (conservative)
- Conflict detection failure = warning only
- Utilization check failure = warning only

---

## Example 3: Resilience Analysis Chain

**Goal:** Comprehensive system health assessment

**Tools Used:**
1. `check_utilization_threshold_tool` - Current capacity
2. `run_contingency_analysis_resilience_tool` - N-1/N-2 analysis
3. `analyze_hub_centrality_tool` - Single points of failure
4. `get_static_fallbacks_tool` - Emergency readiness
5. `check_mtf_compliance_tool` - MTF status

**Pattern:** Parallel fan-out with result synthesis

```python
async def comprehensive_resilience_analysis() -> dict:
    """
    Run complete resilience analysis in parallel.

    Returns:
        dict with health score, severity, and detailed analysis
    """

    logger.info("Starting comprehensive resilience analysis")

    # Fan-out: Run all checks in parallel
    results = await asyncio.gather(
        # Tier 1: Critical resilience
        call_tool_with_retry(
            "check_utilization_threshold_tool",
            available_faculty=10,
            required_blocks=730,
        ),

        # N-1/N-2 via background task
        _run_contingency_background(),

        # Tier 2: Strategic resilience
        call_tool_with_retry("analyze_hub_centrality_tool"),

        # Tier 1: Static stability
        call_tool_with_retry("get_static_fallbacks_tool"),

        # Military compliance
        call_tool_with_retry(
            "check_mtf_compliance_tool",
            check_circuit_breaker=True,
            generate_sitrep=True,
        ),

        return_exceptions=True,
    )

    # Unpack results (handle exceptions)
    utilization, contingency, hub_analysis, fallbacks, mtf_compliance = results

    # Handle partial failures
    if isinstance(utilization, Exception):
        logger.error(f"Utilization check failed: {utilization}")
        utilization = None

    if isinstance(contingency, Exception):
        logger.error(f"Contingency analysis failed: {contingency}")
        contingency = None

    if isinstance(hub_analysis, Exception):
        logger.error(f"Hub analysis failed: {hub_analysis}")
        hub_analysis = None

    if isinstance(fallbacks, Exception):
        logger.error(f"Fallback check failed: {fallbacks}")
        fallbacks = None

    if isinstance(mtf_compliance, Exception):
        logger.error(f"MTF compliance failed: {mtf_compliance}")
        mtf_compliance = None

    # Synthesize health score (0-100)
    health_score = 100.0
    issues = []
    recommendations = []

    # Utilization (30 points)
    if utilization:
        if utilization.level == "green":
            pass  # Full points
        elif utilization.level == "yellow":
            health_score -= 10
            issues.append("Utilization in yellow zone")
        elif utilization.level == "orange":
            health_score -= 20
            issues.append("Utilization in orange zone - approaching cascade risk")
            recommendations.append("Reduce load or add capacity immediately")
        elif utilization.level == "red":
            health_score -= 30
            issues.append("Utilization in red zone - cascade failure imminent")
            recommendations.append("URGENT: Activate load shedding and add capacity")
    else:
        health_score -= 15  # Penalty for missing data

    # Contingency (40 points)
    if contingency:
        if not contingency.n1_pass:
            health_score -= 20
            issues.append("System fails N-1 contingency")
            recommendations.append("Add backup capacity or cross-train faculty")

        if not contingency.n2_pass:
            health_score -= 20
            issues.append("System fails N-2 contingency")
            recommendations.append("Increase redundancy for critical specialties")

    else:
        health_score -= 20  # Penalty for missing data

    # Hub analysis (15 points)
    if hub_analysis:
        critical_hubs = [
            h for h in hub_analysis.faculty_centrality
            if h.get("is_critical_hub", False)
        ]

        if len(critical_hubs) > 3:
            health_score -= 15
            issues.append(f"{len(critical_hubs)} single points of failure identified")
            recommendations.append("Distribute workload from hub faculty")

    # Fallbacks (10 points)
    if fallbacks:
        if fallbacks.precomputed_scenarios_count < 3:
            health_score -= 10
            issues.append("Insufficient pre-computed fallback scenarios")
            recommendations.append("Generate fallback schedules for common scenarios")

    # MTF compliance (5 points)
    if mtf_compliance:
        if mtf_compliance.severity in ["critical", "emergency"]:
            health_score -= 5
            issues.append(f"MTF compliance: {mtf_compliance.severity}")

    # Floor at 0
    health_score = max(0, health_score)

    # Determine severity
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
        "issues": issues,
        "recommendations": recommendations,
        "detailed_analysis": {
            "utilization": utilization,
            "contingency": contingency,
            "hub_analysis": hub_analysis,
            "fallbacks": fallbacks,
            "mtf_compliance": mtf_compliance,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


async def _run_contingency_background() -> dict:
    """Run contingency analysis as background task."""

    task = await call_tool_with_retry(
        "start_background_task_tool",
        task_type="resilience_contingency",
        params={"days_ahead": 90},
    )

    # Poll for completion (max 5 minutes)
    for _ in range(60):
        await asyncio.sleep(5)

        status = await call_tool_with_retry(
            "get_task_status_tool",
            task_id=task.task_id,
        )

        if status.status == "success":
            return status.result

        elif status.status == "failure":
            raise RuntimeError(f"Contingency analysis failed: {status.error}")

    raise TimeoutError("Contingency analysis did not complete within 5 minutes")
```

**Result Synthesis:**
- Health score calculated from weighted components
- Missing data penalized but doesn't fail entire analysis
- Severity determined by threshold ranges
- Actionable recommendations generated

---

## Example 4: Deployment Pipeline Chain

**Goal:** Safe production deployment with rollback on failure

**Tools Used:**
1. `validate_deployment_tool` - Pre-deployment checks
2. `run_security_scan_tool` - Vulnerability scanning
3. `run_smoke_tests_tool` - Staging validation
4. `promote_to_production_tool` - Production deployment
5. `get_deployment_status_tool` - Monitor deployment
6. `rollback_deployment_tool` - Emergency rollback

**Pattern:** Sequential with conditional branching and automatic rollback

```python
async def safe_production_deployment(
    git_ref: str,
    approval_token: str,
    auto_rollback: bool = True,
) -> dict:
    """
    Deploy to production with safety checks and auto-rollback.

    Returns:
        dict with deployment status and details
    """

    deployment_id = None

    try:
        # Step 1: Validate deployment
        logger.info("Step 1/6: Validating deployment")

        validation = await call_tool_with_retry(
            "validate_deployment_tool",
            environment="staging",
            git_ref=git_ref,
            dry_run=False,
        )

        if not validation.valid:
            logger.error(f"Deployment validation failed: {validation.blockers}")

            return {
                "status": "blocked",
                "stage": "validation",
                "blockers": validation.blockers,
                "warnings": validation.warnings,
            }

        # Step 2: Security scan
        logger.info("Step 2/6: Running security scan")

        security_scan = await call_tool_with_retry(
            "run_security_scan_tool",
            git_ref=git_ref,
            dry_run=False,
        )

        critical_vulns = security_scan.severity_summary.get("critical", 0)
        if critical_vulns > 0:
            logger.error(f"Critical vulnerabilities detected: {critical_vulns}")

            return {
                "status": "blocked",
                "stage": "security_scan",
                "critical_vulnerabilities": critical_vulns,
                "vulnerabilities": [
                    v for v in security_scan.vulnerabilities
                    if v.severity == "critical"
                ],
            }

        # Step 3: Smoke tests on staging
        logger.info("Step 3/6: Running smoke tests on staging")

        smoke_tests = await call_tool_with_retry(
            "run_smoke_tests_tool",
            environment="staging",
            test_suite="full",
            timeout_seconds=600,
        )

        if not smoke_tests.passed:
            logger.error("Staging smoke tests failed")

            return {
                "status": "blocked",
                "stage": "smoke_tests",
                "failed_tests": [
                    r.check_name for r in smoke_tests.results
                    if r.status == "failed"
                ],
            }

        # Step 4: Promote to production
        logger.info("Step 4/6: Promoting to production")

        promotion = await call_tool_with_retry(
            "promote_to_production_tool",
            staging_version=git_ref,
            approval_token=approval_token,
            dry_run=False,
        )

        deployment_id = promotion.deployment_id

        # Step 5: Monitor deployment
        logger.info(f"Step 5/6: Monitoring deployment {deployment_id}")

        deployment_succeeded = False
        for attempt in range(20):  # 10 minutes max
            await asyncio.sleep(30)

            status = await call_tool_with_retry(
                "get_deployment_status_tool",
                deployment_id=deployment_id,
            )

            if status.deployment.status == "success":
                logger.info(f"Deployment {deployment_id} succeeded")
                deployment_succeeded = True
                break

            elif status.deployment.status == "failure":
                logger.error(f"Deployment {deployment_id} failed")

                if auto_rollback:
                    # Step 6: Automatic rollback
                    logger.warning("Initiating automatic rollback")
                    await _execute_rollback(deployment_id, git_ref)

                return {
                    "status": "failed",
                    "stage": "deployment",
                    "deployment_id": deployment_id,
                    "error": status.deployment.error,
                    "auto_rollback": auto_rollback,
                }

        if not deployment_succeeded:
            logger.warning(f"Deployment {deployment_id} still in progress")

            return {
                "status": "in_progress",
                "deployment_id": deployment_id,
                "message": "Deployment taking longer than expected. Monitor manually.",
            }

        # Success!
        return {
            "status": "success",
            "deployment_id": deployment_id,
            "version": promotion.production_version,
            "validation_checks_passed": len(validation.checks),
            "security_scan_passed": True,
            "smoke_tests_passed": True,
        }

    except Exception as e:
        logger.error(f"Deployment error: {e}")

        if deployment_id and auto_rollback:
            logger.warning("Exception during deployment - attempting rollback")
            await _execute_rollback(deployment_id, git_ref)

        return {
            "status": "error",
            "error": str(e),
            "deployment_id": deployment_id,
            "auto_rollback": auto_rollback,
        }


async def _execute_rollback(deployment_id: str, failed_version: str):
    """Execute rollback with error handling."""

    try:
        rollback = await call_tool_with_retry(
            "rollback_deployment_tool",
            environment="production",
            reason=f"Automatic rollback of failed deployment {deployment_id}",
            target_version=None,  # Rollback to previous
            dry_run=False,
        )

        logger.info(
            f"Rollback initiated: {rollback.from_version} → {rollback.to_version}"
        )

        return rollback

    except Exception as e:
        logger.critical(f"ROLLBACK FAILED: {e}")

        # Escalate to human
        await escalate_error(
            EscalationLevel.EMERGENCY,
            "rollback_deployment_tool",
            e,
            {
                "deployment_id": deployment_id,
                "failed_version": failed_version,
                "action_required": "MANUAL ROLLBACK REQUIRED",
            },
        )

        raise
```

**Error Handling:**
- Validation/scan failures block deployment
- Deployment failure triggers automatic rollback
- Rollback failure escalates to emergency
- All stages logged for audit trail

---

## Example 5: Performance Optimization Chain

**Goal:** Identify and remove low-value code

**Tools Used:**
1. `benchmark_solvers_tool` - Solver comparison
2. `benchmark_constraints_tool` - Constraint effectiveness
3. `benchmark_resilience_tool` - Resilience module value
4. `module_usage_analysis_tool` - Dead code detection
5. `ablation_study_tool` - Safe removal verification

**Pattern:** Map-reduce with iterative refinement

```python
async def identify_code_to_remove(
    min_removal_threshold_lines: int = 100,
) -> dict:
    """
    Identify code that can be safely removed.

    Returns:
        dict with removal candidates and justification
    """

    logger.info("Starting code optimization analysis")

    # Phase 1: Parallel benchmarking (map)
    benchmark_results = await asyncio.gather(
        call_tool_with_retry(
            "benchmark_solvers_tool",
            scenario_count=20,
            timeout_per_run=60,
        ),
        call_tool_with_retry(
            "benchmark_constraints_tool",
            test_schedules="historical",
        ),
        call_tool_with_retry(
            "benchmark_resilience_tool",
            modules=None,  # All modules
        ),
        call_tool_with_retry(
            "module_usage_analysis_tool",
            entry_points=["main", "api", "scheduling"],
        ),
        return_exceptions=True,
    )

    solver_bench, constraint_bench, resilience_bench, usage_analysis = benchmark_results

    # Phase 2: Identify removal candidates (reduce)
    removal_candidates = []

    # From solver benchmarks
    if not isinstance(solver_bench, Exception):
        # Remove solvers that consistently lose
        for solver, metrics in solver_bench.results_by_solver.items():
            if metrics.failures > metrics.successes * 0.5:
                removal_candidates.append({
                    "module": f"scheduling/solvers/{solver}.py",
                    "reason": f"Solver failure rate: {metrics.failures}/{metrics.runs}",
                    "estimated_lines": 200,  # Estimate
                    "confidence": "high",
                })

    # From constraint benchmarks
    if not isinstance(constraint_bench, Exception):
        for constraint in constraint_bench.candidates_for_removal:
            removal_candidates.append({
                "module": f"scheduling/constraints/{constraint}.py",
                "reason": f"Low yield constraint (false positives > true positives)",
                "estimated_lines": 50,
                "confidence": "medium",
            })

    # From resilience benchmarks
    if not isinstance(resilience_bench, Exception):
        for module in resilience_bench.cut_candidates:
            removal_candidates.append({
                "module": f"resilience/{module}.py",
                "reason": "Low detection rate or high false alarm rate",
                "estimated_lines": 150,
                "confidence": "medium",
            })

    # From usage analysis
    if not isinstance(usage_analysis, Exception):
        for module in usage_analysis.unreachable_modules:
            removal_candidates.append({
                "module": module,
                "reason": "Dead code - unreachable from any entry point",
                "estimated_lines": usage_analysis.dead_code_lines // len(usage_analysis.unreachable_modules),
                "confidence": "high",
            })

    # Phase 3: Ablation study for high-value candidates (sequential)
    verified_removals = []

    for candidate in removal_candidates:
        if candidate["estimated_lines"] < min_removal_threshold_lines:
            continue  # Skip small modules

        logger.info(f"Running ablation study for {candidate['module']}")

        try:
            ablation = await call_tool_with_retry(
                "ablation_study_tool",
                module_path=candidate["module"],
            )

            if ablation.safe_to_remove:
                verified_removals.append({
                    **candidate,
                    "ablation_study": {
                        "safe": True,
                        "module_size_lines": ablation.module_size_lines,
                        "tests_affected": ablation.tests_affected,
                        "imported_by": ablation.imported_by,
                    },
                })

        except Exception as e:
            logger.warning(f"Ablation study failed for {candidate['module']}: {e}")

    # Synthesize results
    total_lines_to_remove = sum(c["ablation_study"]["module_size_lines"] for c in verified_removals)

    return {
        "total_candidates": len(removal_candidates),
        "verified_safe_removals": len(verified_removals),
        "estimated_lines_saved": total_lines_to_remove,
        "removal_candidates": verified_removals,
        "recommendation": (
            f"Remove {len(verified_removals)} modules totaling {total_lines_to_remove} lines. "
            f"Run tests before committing."
        ),
    }
```

**Map-Reduce Pattern:**
- Map: Run all benchmarks in parallel
- Reduce: Aggregate removal candidates
- Refine: Verify with ablation studies

---

## Best Practices from Examples

1. **Always handle partial failures** - Use `return_exceptions=True`
2. **Log every step** - Aids debugging complex chains
3. **Synthesize results explicitly** - Don't assume caller will aggregate
4. **Provide recommendations** - Make results actionable
5. **Use background tasks for >30s operations** - Avoid timeouts
6. **Implement automatic rollback** - Reduce MTTR
7. **Cache expensive results** - Avoid recomputation
8. **Validate inputs early** - Fail fast on bad data
9. **Monitor chain performance** - Identify bottlenecks
10. **Test error paths** - Ensure chains handle failures correctly

---

## Version History

- **2025-12-26**: Initial composition examples
- **MCP Server**: v0.1.0
