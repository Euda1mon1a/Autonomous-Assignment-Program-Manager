# MCP Tool Index

Complete catalog of all 36 MCP tools with input/output schemas, use cases, and dependencies.

## Tool Categories

- [Core Scheduling Tools](#core-scheduling-tools) (5 tools)
- [Resilience Framework Tools](#resilience-framework-tools) (13 tools)
- [Background Task Management](#background-task-management) (4 tools)
- [Deployment Workflow Tools](#deployment-workflow-tools) (7 tools)
- [Empirical Testing Tools](#empirical-testing-tools) (5 tools)
- [Resource Tools](#resource-tools) (2 tools)

---

## Core Scheduling Tools

### 1. validate_schedule_tool

**Purpose:** Validate schedule against ACGME regulations

**Input Schema:**
```python
{
    "start_date": str,           # YYYY-MM-DD format
    "end_date": str,             # YYYY-MM-DD format
    "check_work_hours": bool,    # Default: True
    "check_supervision": bool,   # Default: True
    "check_rest_periods": bool,  # Default: True
    "check_consecutive_duty": bool  # Default: True
}
```

**Output Schema:**
```python
{
    "is_valid": bool,
    "overall_compliance_rate": float,  # 0.0-1.0
    "total_issues": int,
    "critical_issues": int,
    "warning_issues": int,
    "info_issues": int,
    "issues": list[ValidationIssue],
    "validated_at": datetime,
    "date_range": tuple[date, date]
}
```

**Use Cases:**
- Pre-deployment validation
- ACGME compliance audits
- Schedule quality checks

**Dependencies:**
- Requires: DATABASE_URL, API_BASE_URL
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** 2-30 seconds (depending on date range)

---

### 2. validate_schedule_by_id_tool

**Purpose:** Validate specific schedule by ID using ConstraintService

**Input Schema:**
```python
{
    "schedule_id": str,              # UUID or alphanumeric ID
    "constraint_config": str,        # "default", "minimal", "strict", "resilience"
    "include_suggestions": bool      # Default: True
}
```

**Output Schema:**
```python
{
    "is_valid": bool,
    "critical_count": int,
    "warning_count": int,
    "info_count": int,
    "violations": list[ConstraintViolation],
    "suggestions": list[str],
    "validated_at": datetime
}
```

**Use Cases:**
- Targeted schedule validation
- Post-generation verification
- Deep constraint analysis

**Dependencies:**
- Requires: DATABASE_URL, ConstraintService
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** 5-60 seconds

---

### 3. detect_conflicts_tool

**Purpose:** Detect scheduling conflicts (double-bookings, violations, gaps)

**Input Schema:**
```python
{
    "start_date": str,               # YYYY-MM-DD
    "end_date": str,                 # YYYY-MM-DD
    "conflict_types": list[str] | None,  # Filter specific types
    "include_auto_resolution": bool  # Default: True
}
```

**Conflict Types:**
- `double_booking`
- `work_hour_violation`
- `rest_period_violation`
- `supervision_gap`
- `leave_overlap`
- `credential_mismatch`

**Output Schema:**
```python
{
    "total_conflicts": int,
    "conflicts_by_type": dict[str, int],
    "conflicts": list[ConflictInfo],
    "auto_resolvable_count": int,
    "detected_at": datetime
}
```

**Use Cases:**
- Post-generation conflict detection
- Schedule troubleshooting
- Automated conflict resolution

**Dependencies:**
- Requires: DATABASE_URL, API_BASE_URL
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** 2-20 seconds

---

### 4. analyze_swap_candidates_tool

**Purpose:** Find optimal swap partners for schedule changes

**Input Schema:**
```python
{
    "requester_person_id": str,
    "assignment_id": str,
    "preferred_start_date": str | None,  # YYYY-MM-DD
    "preferred_end_date": str | None,    # YYYY-MM-DD
    "max_candidates": int                # Default: 10, max: 50
}
```

**Output Schema:**
```python
{
    "requester_person_id": str,
    "original_assignment_id": str,
    "candidates": list[SwapCandidate],
    "top_candidate_id": str | None,
    "analyzed_at": datetime
}

SwapCandidate:
{
    "candidate_person_id": str,
    "match_score": float,       # 0.0-1.0
    "rotation": str,
    "date_range": tuple[date, date],
    "compatibility_factors": dict,
    "mutual_benefit": bool,
    "approval_likelihood": str  # "low", "medium", "high"
}
```

**Use Cases:**
- Swap request processing
- Schedule flexibility analysis
- Faculty satisfaction optimization

**Dependencies:**
- Requires: DATABASE_URL, API_BASE_URL
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** 1-5 seconds

---

### 5. run_contingency_analysis_tool

**Purpose:** Simulate workforce scenarios (absences, emergencies)

**Input Schema:**
```python
{
    "scenario": str,              # "faculty_absence", "resident_absence",
                                  # "emergency_coverage", "mass_absence"
    "affected_person_ids": list[str],
    "start_date": str,            # YYYY-MM-DD
    "end_date": str,              # YYYY-MM-DD
    "auto_resolve": bool          # Default: False
}
```

**Output Schema:**
```python
{
    "scenario": str,
    "impact": ImpactAssessment,
    "resolution_options": list[ResolutionOption],
    "recommended_option_id": str | None,
    "analyzed_at": datetime
}

ImpactAssessment:
{
    "affected_rotations": list[str],
    "coverage_gaps": int,
    "compliance_violations": int,
    "workload_increase_percent": float,
    "feasibility_score": float,  # 0.0-1.0
    "critical_gaps": list[str]
}

ResolutionOption:
{
    "option_id": str,
    "strategy": str,
    "description": str,
    "affected_people": list[str],
    "estimated_effort": str,     # "low", "medium", "high"
    "success_probability": float  # 0.0-1.0
}
```

**Use Cases:**
- Deployment/TDY planning
- Emergency response
- Workforce resilience testing

**Dependencies:**
- Requires: DATABASE_URL (optional), business logic
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** 1-3 seconds

---

## Resilience Framework Tools

### 6. check_utilization_threshold_tool

**Purpose:** Check 80% utilization threshold (queuing theory)

**Input Schema:**
```python
{
    "available_faculty": int,
    "required_blocks": int,
    "blocks_per_faculty_per_day": float,  # Default: 2.0
    "days_in_period": int                 # Default: 1
}
```

**Output Schema:**
```python
{
    "level": str,                  # "green", "yellow", "orange", "red", "black"
    "utilization_rate": float,     # 0.0-1.0
    "effective_utilization": float,
    "buffer_remaining": float,
    "total_capacity": int,
    "required_coverage": int,
    "current_assignments": int,
    "safe_maximum": int,
    "wait_time_multiplier": float,
    "message": str,
    "recommendations": list[str],
    "severity": str               # "healthy", "warning", "critical", "emergency"
}
```

**Use Cases:**
- Capacity planning
- Cascade failure prevention
- Workload monitoring

**Dependencies:**
- Requires: None (pure calculation)
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** <1 second

---

### 7. get_defense_level_tool

**Purpose:** Get defense-in-depth level (nuclear safety paradigm)

**Input Schema:**
```python
{
    "coverage_rate": float  # 0.0-1.0
}
```

**Output Schema:**
```python
{
    "current_level": str,      # "prevention", "control", "safety_systems",
                               # "containment", "emergency"
    "recommended_level": str,
    "status": str,             # "ready", "active", "degraded"
    "active_actions": list[dict],
    "automation_status": dict[str, bool],
    "escalation_needed": bool,
    "coverage_rate": float,
    "severity": str            # "normal", "elevated", "critical"
}
```

**Use Cases:**
- Crisis level determination
- Automated response triggering
- Safety monitoring

**Dependencies:**
- Requires: None
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** <1 second

---

### 8. run_contingency_analysis_resilience_tool

**Purpose:** N-1/N-2 contingency analysis (power grid planning)

**Input Schema:**
```python
{
    "analyze_n1": bool,                    # Default: True
    "analyze_n2": bool,                    # Default: True
    "include_cascade_simulation": bool,    # Default: False
    "critical_faculty_only": bool          # Default: True
}
```

**Output Schema:**
```python
{
    "analysis_date": str,
    "period_start": str,
    "period_end": str,
    "n1_pass": bool,
    "n1_vulnerabilities": list[VulnerabilityInfo],
    "n2_pass": bool,
    "n2_fatal_pairs": list[FatalPairInfo],
    "most_critical_faculty": list[str],
    "phase_transition_risk": str,  # "low", "medium", "high", "critical"
    "leading_indicators": list[str],
    "recommended_actions": list[str],
    "severity": str                # "healthy", "vulnerable", "critical"
}
```

**Use Cases:**
- Vulnerability assessment
- Critical faculty identification
- Resilience planning

**Dependencies:**
- Requires: DATABASE_URL, Resilience Framework
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** 2-5 minutes (use background task)

---

### 9. get_static_fallbacks_tool

**Purpose:** Get pre-computed fallback schedules (AWS static stability)

**Input Schema:** None

**Output Schema:**
```python
{
    "active_fallbacks": list[FallbackScheduleInfo],
    "available_fallbacks": list[FallbackScheduleInfo],
    "recommended_scenario": str | None,
    "precomputed_scenarios_count": int,
    "last_precomputed": str | None,
    "message": str
}

FallbackScheduleInfo:
{
    "scenario": str,          # "single_absence", "dual_absence", "pcs_season", etc.
    "is_active": bool,
    "activated_at": str | None,
    "approved_by": str | None,
    "assignments_count": int,
    "coverage_rate": float,
    "description": str
}
```

**Use Cases:**
- Emergency failover
- Crisis response
- Pre-planned schedule activation

**Dependencies:**
- Requires: DATABASE_URL, Resilience Framework
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** 1-2 seconds

---

### 10. execute_sacrifice_hierarchy_tool

**Purpose:** Execute triage-based load shedding

**Input Schema:**
```python
{
    "target_level": str,      # "normal", "yellow", "orange", "red", "black"
    "simulate_only": bool     # Default: True
}
```

**Output Schema:**
```python
{
    "current_level": str,
    "activities_suspended": list[str],
    "activities_protected": list[str],
    "simulation_mode": bool,
    "estimated_capacity_freed": float,
    "recovery_plan": list[dict],
    "message": str,
    "severity": str
}
```

**Use Cases:**
- Crisis load shedding
- Non-essential activity suspension
- Capacity freeing

**Dependencies:**
- Requires: DATABASE_URL (if not simulating)
- Rate Limit: None
- Idempotent: No (when simulate_only=False)

**Estimated Duration:** 1-2 seconds

---

### 11-18. Additional Resilience Tools

Abbreviated for brevity (see full signatures in source code):

- **analyze_homeostasis_tool** - Feedback loops and allostatic load
- **calculate_blast_radius_tool** - Zone isolation analysis
- **analyze_le_chatelier_tool** - Equilibrium shift analysis
- **analyze_hub_centrality_tool** - Network centrality metrics
- **assess_cognitive_load_tool** - Decision queue complexity
- **get_behavioral_patterns_tool** - Stigmergy patterns
- **analyze_stigmergy_tool** - Optimization signals
- **check_mtf_compliance_tool** - MTF/DRRS compliance

---

## Background Task Management

### 19. start_background_task_tool

**Purpose:** Start long-running Celery tasks

**Input Schema:**
```python
{
    "task_type": str,           # See TaskType enum
    "params": dict | None       # Task-specific parameters
}
```

**Task Types:**
- `resilience_health_check`
- `resilience_contingency`
- `resilience_fallback_precompute`
- `resilience_utilization_forecast`
- `resilience_crisis_activation`
- `metrics_computation`
- `metrics_snapshot`
- `metrics_cleanup`
- `metrics_fairness_report`
- `metrics_version_diff`

**Output Schema:**
```python
{
    "task_id": str,
    "task_type": str,
    "status": str,
    "estimated_duration": str,
    "queued_at": datetime,
    "message": str
}
```

**Use Cases:**
- Long-running analysis (>30s)
- Asynchronous schedule generation
- Background metrics computation

**Dependencies:**
- Requires: Celery, Redis
- Rate Limit: None
- Idempotent: No

**Estimated Duration:** <1 second (to queue)

---

### 20. get_task_status_tool

**Purpose:** Poll Celery task status

**Input Schema:**
```python
{
    "task_id": str
}
```

**Output Schema:**
```python
{
    "task_id": str,
    "status": str,        # "pending", "started", "success", "failure", "revoked"
    "progress": int,      # 0-100
    "result": any | None,
    "error": str | None,
    "started_at": datetime | None,
    "completed_at": datetime | None
}
```

**Use Cases:**
- Task monitoring
- Result retrieval
- Progress tracking

**Dependencies:**
- Requires: Celery, Redis
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** <1 second

---

### 21. cancel_task_tool

**Purpose:** Cancel running/queued task

**Input Schema:**
```python
{
    "task_id": str
}
```

**Output Schema:**
```python
{
    "task_id": str,
    "status": str,
    "message": str,
    "canceled_at": datetime
}
```

**Use Cases:**
- User cancellation
- Timeout handling
- Resource cleanup

**Dependencies:**
- Requires: Celery, Redis
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** <1 second

---

### 22. list_active_tasks_tool

**Purpose:** List all active Celery tasks

**Input Schema:**
```python
{
    "task_type": str | None  # Optional filter
}
```

**Output Schema:**
```python
{
    "total_active": int,
    "tasks": list[ActiveTaskInfo],
    "queried_at": datetime
}

ActiveTaskInfo:
{
    "task_id": str,
    "task_name": str,
    "task_type": str | None,
    "status": str,
    "started_at": datetime | None
}
```

**Use Cases:**
- Worker monitoring
- Task queue visibility
- Resource usage tracking

**Dependencies:**
- Requires: Celery workers running
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** 1-2 seconds

---

## Deployment Workflow Tools

### 23. validate_deployment_tool

**Purpose:** Validate deployment readiness

**Input Schema:**
```python
{
    "environment": str,         # "staging" or "production"
    "git_ref": str,
    "dry_run": bool,            # Default: False
    "skip_tests": bool,         # Default: False
    "skip_security_scan": bool  # Default: False
}
```

**Output Schema:**
```python
{
    "valid": bool,
    "environment": str,
    "git_ref": str,
    "checks": list[DeploymentCheck],
    "blockers": list[str],
    "warnings": list[str],
    "validated_at": datetime,
    "validation_duration_ms": int
}
```

**Use Cases:**
- Pre-deployment validation
- CI/CD pipeline checks
- Automated deployment gating

**Dependencies:**
- Requires: Git, test suite
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** 1-5 minutes

---

### 24. run_security_scan_tool

**Purpose:** Scan for security vulnerabilities

**Input Schema:**
```python
{
    "git_ref": str,
    "scan_dependencies": bool,  # Default: True
    "scan_code": bool,          # Default: True
    "scan_secrets": bool,       # Default: True
    "dry_run": bool             # Default: False
}
```

**Output Schema:**
```python
{
    "git_ref": str,
    "vulnerabilities": list[Vulnerability],
    "severity_summary": dict[str, int],
    "passed": bool,
    "scan_duration_ms": int,
    "scanned_at": datetime,
    "blockers": list[str]
}
```

**Use Cases:**
- Security auditing
- Vulnerability detection
- Compliance verification

**Dependencies:**
- Requires: Security scanning tools
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** 2-10 minutes

---

### 25-29. Additional Deployment Tools

Abbreviated:

- **run_smoke_tests_tool** - Execute smoke tests
- **promote_to_production_tool** - Promote staging to production
- **rollback_deployment_tool** - Rollback failed deployment
- **get_deployment_status_tool** - Check deployment status
- **list_deployments_tool** - List deployment history

---

## Empirical Testing Tools

### 30. benchmark_solvers_tool

**Purpose:** Compare scheduling solvers head-to-head

**Input Schema:**
```python
{
    "solvers": list[str] | None,  # Default: all
    "scenario_count": int,         # Default: 10
    "timeout_per_run": int         # Default: 60 seconds
}
```

**Output Schema:**
```python
{
    "timestamp": datetime,
    "scenarios_run": int,
    "solvers_tested": list[str],
    "results_by_solver": dict[str, SolverMetrics],
    "winner_by_metric": dict[str, str],
    "recommendation": str,
    "raw_data": list[dict]
}
```

**Use Cases:**
- Solver selection
- Performance optimization
- Algorithm comparison

**Dependencies:**
- Requires: Scheduling engine
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** Variable (scenario_count × timeout_per_run)

---

### 31-34. Additional Empirical Tools

Abbreviated:

- **benchmark_constraints_tool** - Measure constraint effectiveness
- **ablation_study_tool** - Test impact of removing module
- **benchmark_resilience_tool** - Compare resilience modules
- **module_usage_analysis_tool** - Find dead code

---

## Resource Tools

### 35. schedule_status_resource

**Purpose:** Get current schedule status (read-only resource)

**Input Schema:**
```python
{
    "start_date": str | None,  # Default: today
    "end_date": str | None     # Default: 30 days from start
}
```

**Output Schema:**
```python
{
    "period": {
        "start_date": date,
        "end_date": date
    },
    "total_assignments": int,
    "coverage_metrics": dict,
    "active_issues": list[dict],
    "last_updated": datetime
}
```

**Use Cases:**
- Dashboard data
- Schedule overview
- Quick status check

**Dependencies:**
- Requires: DATABASE_URL
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** 1-3 seconds

---

### 36. compliance_summary_resource

**Purpose:** Get ACGME compliance summary (read-only resource)

**Input Schema:**
```python
{
    "start_date": str | None,
    "end_date": str | None
}
```

**Output Schema:**
```python
{
    "period": {
        "start_date": date,
        "end_date": date
    },
    "compliance_rate": float,
    "violations": list[dict],
    "work_hour_summary": dict,
    "supervision_summary": dict,
    "rest_period_summary": dict,
    "last_updated": datetime
}
```

**Use Cases:**
- Compliance dashboard
- ACGME audits
- Regulatory reporting

**Dependencies:**
- Requires: DATABASE_URL
- Rate Limit: None
- Idempotent: Yes

**Estimated Duration:** 1-3 seconds

---

## Tool Dependency Matrix

| Tool | Requires DB | Requires API | Requires Celery | Requires Git |
|------|-------------|--------------|-----------------|--------------|
| validate_schedule_tool | ✓ | ✓ | ✗ | ✗ |
| detect_conflicts_tool | ✓ | ✓ | ✗ | ✗ |
| analyze_swap_candidates_tool | ✓ | ✓ | ✗ | ✗ |
| check_utilization_threshold_tool | ✗ | ✗ | ✗ | ✗ |
| start_background_task_tool | ✗ | ✗ | ✓ | ✗ |
| validate_deployment_tool | ✗ | ✗ | ✗ | ✓ |
| benchmark_solvers_tool | ✓ | ✗ | ✗ | ✗ |

---

## Rate Limits

Currently no tools have rate limits. Future considerations:
- GitHub API calls: 5000/hour
- External security scans: TBD
- Background task queue: Limited by Celery worker count

---

## Version History

- **2025-12-26**: Initial catalog (36 tools)
- **MCP Server**: v0.1.0
- **Backend API**: v1.0.0
