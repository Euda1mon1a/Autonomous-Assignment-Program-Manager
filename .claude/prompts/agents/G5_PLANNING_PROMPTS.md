# G5 Planning Agent - Prompt Templates

> **Role:** Schedule generation, optimization, ACGME compliance validation, constraint management
> **Model:** Claude Opus 4.5
> **Mission:** Generate compliant, optimized schedules

## 1. MISSION BRIEFING TEMPLATE

```
You are the G5 Planning Agent for the Residency Scheduler.

**MISSION:** ${MISSION_OBJECTIVE}

**SCHEDULE PARAMETERS:**
- Block date range: ${START_DATE} to ${END_DATE}
- Total slots to fill: ${TOTAL_SLOTS}
- Personnel count: ${PERSONNEL_COUNT}
- Rotation types: ${ROTATION_TYPES}

**OPTIMIZATION OBJECTIVES:**
1. 100% ACGME compliance (80-hour, 1-in-7, supervision ratios)
2. Coverage >= ${COVERAGE_TARGET}%
3. Workload balance (coefficient of variation <= ${BALANCE_TARGET})
4. Rotation distribution (variance <= ${ROTATION_VARIANCE}%)
5. Minimize schedule disruption (change from baseline <= ${DISRUPTION_LIMIT}%)

**CONSTRAINTS TO RESPECT:**
- Hard constraints (must satisfy): ${HARD_CONSTRAINTS}
- Soft constraints (prefer to satisfy): ${SOFT_CONSTRAINTS}
- Personnel preferences: ${PREFERENCE_WEIGHT}
- Credential requirements: ${CREDENTIAL_REQUIREMENTS}

**SOLVER CONFIGURATION:**
- Solver type: ${SOLVER_TYPE}
- Time limit: ${SOLVER_TIME_LIMIT} seconds
- Optimality gap: ${OPTIMALITY_GAP}%
- Parallel workers: ${PARALLEL_WORKERS}

**SUCCESS CRITERIA:**
- Feasible schedule found: ${FEASIBILITY_REQUIRED}
- ACGME compliance: 100%
- Coverage: >= ${COVERAGE_TARGET}%
- Schedule quality score: >= ${QUALITY_THRESHOLD}

Generate schedule. Report feasibility and quality metrics.
```

## 2. CONSTRAINT VALIDATION TEMPLATE

```
**TASK:** Validate constraints for ${CONSTRAINT_COUNT} rules

**CONSTRAINT CATEGORIES:**

### Hard Constraints (Must satisfy)
1. **ACGME Compliance:**
   - 80-hour rule: Max ${MAX_HOURS}/week rolling
   - 1-in-7 rule: Min 1 day off per 7 days
   - Supervision ratios: ${SUPERVISION_SPEC}

2. **Credential Requirements:**
   - Slot type requirements: ${CREDENTIAL_MAPPING}
   - Personnel credentials: ${PERSONNEL_CREDS}

3. **Personnel Constraints:**
   - Unavailable dates: ${UNAVAILABLE_DATES}
   - Time-off requests: ${TIMEOFF_REQUESTS}
   - Preferences (hard): ${HARD_PREFERENCES}

### Soft Constraints (Try to satisfy)
1. Rotation balance: variance <= ${ROTATION_VARIANCE}%
2. Workload distribution: ${WORKLOAD_CRITERION}
3. Personnel preferences (soft): ${SOFT_PREFERENCES}
4. Minimize changes from baseline: ${CHANGE_LIMIT}%

**VALIDATION METHOD:**
- Check each constraint against personnel data
- Identify conflicting constraints
- Calculate feasibility score
- Report validation results

**OUTPUT FORMAT:**
\`\`\`json
{
  "validation_date": "${TODAY}",
  "constraints_total": ${TOTAL},
  "constraints_valid": ${VALID},
  "constraint_conflicts": ${CONFLICTS},
  "feasibility_score": ${FEASIBILITY_0_100},
  "critical_issues": [...]
}
\`\`\`

Validate constraints and report feasibility.
```

## 3. SCHEDULE GENERATION TEMPLATE

```
**OBJECTIVE:** Generate schedule for ${DATE_RANGE}

**GENERATION PARAMETERS:**
- Start block: ${START_BLOCK}
- End block: ${END_BLOCK}
- Personnel: ${PERSONNEL_LIST}
- Rotations available: ${ROTATION_LIST}

**GENERATION WORKFLOW:**
1. Pre-solver validation (${VALIDATION_TIME}s)
2. Constraint compilation (${COMPILATION_TIME}s)
3. Initial solution (${INITIAL_TIME}s)
4. Optimization (${OPTIMIZATION_TIME}s)
5. Post-solver validation (${POST_VALIDATION_TIME}s)

**SOLVER PARAMETERS:**
- Type: ${SOLVER_TYPE}
- Time limit: ${TIME_LIMIT}s
- Workers: ${WORKERS}
- Optimality gap: ${OPTIMALITY_GAP}%

**GENERATION MILESTONES:**
- Initial feasible solution: ${INITIAL_TARGET}s
- Optimal solution: ${OPTIMAL_TARGET}s
- Final validation: ${VALIDATION_TARGET}s

**SUCCESS CRITERIA:**
- Feasible schedule found: YES/NO
- ACGME compliance: 100%
- Coverage: >= ${COVERAGE_TARGET}%
- Solver status: OPTIMAL/FEASIBLE/INFEASIBLE

**OUTPUT:**
- Schedule file: ${OUTPUT_FILE}
- Quality report: ${REPORT_FILE}
- Backup schedule: ${BACKUP_FILE}

Report generation status and schedule quality.
```

## 4. FEASIBILITY ANALYSIS TEMPLATE

```
**ANALYSIS:** Schedule Feasibility Assessment

**ANALYSIS DATE:** ${TODAY}
**SCOPE:** ${ANALYSIS_SCOPE}

**FEASIBILITY VERDICT:** ${VERDICT} (${CONFIDENCE}% confidence)

**FEASIBILITY FACTORS:**

### Coverage Feasibility
- Required slots: ${REQUIRED_SLOTS}
- Available capacity: ${AVAILABLE_CAPACITY}
- Capacity ratio: ${CAPACITY_RATIO}
- Verdict: ${COVERAGE_FEASIBLE}

### Constraint Feasibility
- Hard constraints: ${HARD_CONSTRAINT_COUNT}
- Satisfiable constraints: ${SATISFIABLE_COUNT}
- Conflicting constraints: ${CONFLICTING_COUNT}
- Verdict: ${CONSTRAINT_FEASIBLE}

### Credential Feasibility
- Credentialed slots: ${CREDENTIALED_SLOTS}
- Personnel with creds: ${CREDENTIALED_PERSONNEL}
- Shortage: ${CREDENTIAL_SHORTAGE}
- Verdict: ${CREDENTIAL_FEASIBLE}

**INFEASIBILITY ANALYSIS (if applicable):**
- Root causes: ${ROOT_CAUSES}
- Conflicting constraints: ${CONFLICTS}
- Relaxation options: ${RELAXATION_OPTIONS}

**RECOMMENDATIONS:**
- If feasible: Proceed to optimization
- If infeasible: ${RECOMMENDATIONS}

Report feasibility verdict and recommendations.
```

## 5. OPTIMIZATION TEMPLATE

```
**OBJECTIVE:** Optimize schedule quality for ${OPTIMIZATION_SCOPE}

**OPTIMIZATION OBJECTIVES (Ranked):**
1. ${OBJECTIVE_1}: Target value ${TARGET_1}
2. ${OBJECTIVE_2}: Target value ${TARGET_2}
3. ${OBJECTIVE_3}: Target value ${TARGET_3}

**OPTIMIZATION METRICS:**

### Coverage Optimization
- Current coverage: ${CURRENT_COVERAGE}%
- Target coverage: ${TARGET_COVERAGE}%
- Gap: ${COVERAGE_GAP}%

### Workload Balance
- Current balance (CV): ${CURRENT_BALANCE}
- Target balance (CV): ${TARGET_BALANCE}
- Imbalance: ${IMBALANCE_PERCENT}%

### Rotation Balance
- Current variance: ${CURRENT_VARIANCE}%
- Target variance: ${TARGET_VARIANCE}%
- Gap: ${VARIANCE_GAP}%

### Change Minimization
- Baseline schedule: ${BASELINE}
- Proposed schedule: ${PROPOSED}
- Changes from baseline: ${CHANGE_COUNT}
- Change percentage: ${CHANGE_PERCENT}%

**OPTIMIZATION ALGORITHM:**
1. Generate initial feasible schedule
2. Identify improvement opportunities
3. Apply optimization moves (reassignments, swaps)
4. Validate compliance after each move
5. Repeat until time limit or convergence

**PARETO FRONTIER:**
- Top solutions ranked by composite score
- Solution 1: Coverage ${COV_1}%, Balance ${BAL_1}
- Solution 2: Coverage ${COV_2}%, Balance ${BAL_2}

Report optimized schedule and quality metrics.
```

## 6. ACGME COMPLIANCE TEMPLATE

```
**VALIDATION:** ACGME Compliance Report

**VALIDATION DATE:** ${TODAY}
**VALIDATION SCOPE:** ${SCOPE}

**COMPLIANCE RULES VERIFIED:**

### 80-Hour Rule
- Rule: Max 80 hours/week averaged over 4-week periods
- Compliant personnel: ${COMPLIANT_80H}/${TOTAL}
- Violations: ${VIOLATIONS_80H}
- Max hours observed: ${MAX_HOURS_OBSERVED}

### 1-in-7 Rule
- Rule: Min 1 full day off every 7 days
- Compliant personnel: ${COMPLIANT_1IN7}/${TOTAL}
- Violations: ${VIOLATIONS_1IN7}
- Min days off observed: ${MIN_DAYS_OFF}

### Supervision Ratios
- PGY-1 ratio (1:2): ${COMPLIANCE_PGY1}
- PGY-2/3 ratio (1:4): ${COMPLIANCE_PGY23}
- Violations: ${RATIO_VIOLATIONS}

### Clinical Supervision
- Required supervision slots: ${REQUIRED_SUPERVISION}
- Supervised assignments: ${SUPERVISED_ASSIGNMENTS}
- Coverage: ${SUPERVISION_COVERAGE}%

**VIOLATION DETAILS:**
${VIOLATION_LIST}

**COMPLIANCE VERDICT:** ${COMPLIANT}

**REMEDIATION (if needed):**
${REMEDIATION_STEPS}

Report ACGME compliance status.
```

## 7. STATUS REPORT TEMPLATE

```
**G5 PLANNING STATUS REPORT**
**Report Date:** ${TODAY}
**Reporting Period:** ${PERIOD}

**SCHEDULE GENERATION:**
- Schedules generated: ${SCHEDULE_COUNT}
- Successfully generated: ${SUCCESS_COUNT}
- Average quality score: ${AVG_QUALITY}
- Average generation time: ${AVG_TIME}s

**PLANNING METRICS:**
- ACGME compliance: 100%
- Coverage achieved: ${COVERAGE_PERCENT}%
- Workload balance (CV): ${BALANCE_CV}
- Personnel satisfaction: ${SATISFACTION_PERCENT}%

**CONSTRAINT MANAGEMENT:**
- Hard constraints: ${HARD_COUNT}
- Soft constraints: ${SOFT_COUNT}
- Constraint violations: ${VIOLATIONS}
- Conflicting constraints: ${CONFLICTS}

**OPTIMIZATION RESULTS:**
- Optimal solutions found: ${OPTIMAL_COUNT}
- Feasible solutions found: ${FEASIBLE_COUNT}
- Optimization time average: ${AVG_OPT_TIME}s
- Average improvement: ${AVG_IMPROVEMENT}%

**ISSUES & ESCALATIONS:**
${ISSUES}

**RECOMMENDATIONS:**
${RECOMMENDATIONS}

**NEXT PLANNING CYCLE:** ${NEXT_CYCLE_DATE}
```

## 8. ESCALATION TEMPLATE

```
**PLANNING ESCALATION**
**Priority:** ${PRIORITY}
**Escalate To:** G3 Operations / G1 Personnel

**SITUATION:**
${SITUATION}

**PLANNING IMPACT:**
- Schedule infeasible: ${INFEASIBLE}
- ACGME compliance at risk: ${COMPLIANCE_RISK}
- Coverage shortfall: ${COVERAGE_GAP}%

**CONSTRAINT CONFLICT:**
- Conflicting constraints: ${CONFLICTS}
- Cannot satisfy both: ${CONSTRAINT_PAIR}

**REQUESTED AUTHORITY:**
1. ${AUTHORITY_1}
2. ${AUTHORITY_2}

**DECISION DEADLINE:** ${DEADLINE}

Escalate and request authority.
```

## 9. HANDOFF TEMPLATE

```
**G5 PLANNING HANDOFF**
**From:** ${FROM_AGENT}
**To:** ${TO_AGENT}
**Date:** ${TODAY}

**SCHEDULE STATE:**
- Current schedule: ${SCHEDULE_VERSION}
- Planning horizon: ${HORIZON_DAYS} days
- Last generation: ${LAST_GEN_DATE}
- Next generation: ${NEXT_GEN_DATE}

**PENDING PLANS:**
- Block: ${BLOCK_1} (Due: ${DUE_1})
- Block: ${BLOCK_2} (Due: ${DUE_2})

**CONSTRAINT ISSUES:**
${CONSTRAINT_ISSUES}

**BLOCKED ITEMS:**
${BLOCKED_ITEMS}

**OPTIMIZATION SETTINGS:**
- Solver: ${SOLVER_SETTINGS}
- Objectives: ${OBJECTIVES}
- Time limits: ${TIME_LIMITS}

Acknowledge and confirm planning continuity.
```

## 10. DELEGATION TEMPLATE

```
**PLANNING DELEGATION**
**From:** G5 Planning
**Task:** ${TASK_NAME}

**DELEGATEE:** ${DELEGATEE_AGENT}
**Due:** ${DUE_DATE}

**PLANNING OBJECTIVE:**
${OBJECTIVE}

**SCOPE:**
${SCOPE}

**CONSTRAINTS:**
${CONSTRAINTS}

**EXPECTED OUTPUT:**
${EXPECTED_OUTPUT}

**SUCCESS CRITERIA:**
- [ ] Schedule is feasible
- [ ] ACGME compliance: 100%
- [ ] Coverage >= ${COVERAGE_TARGET}%
- [ ] Quality score >= ${QUALITY_TARGET}

Confirm acceptance.
```

## 11. ERROR HANDLING TEMPLATE

```
**PLANNING ERROR**
**Timestamp:** ${TIMESTAMP}
**Severity:** ${SEVERITY}

**ERROR DESCRIPTION:**
${ERROR}

**IMPACT:**
- Schedule generation blocked: ${BLOCKED}
- Planning delay: ${DELAY_MINUTES} minutes
- Cascading impact: ${CASCADING_IMPACT}

**ROOT CAUSE:**
${ROOT_CAUSE}

**RECOVERY:**
1. ${STEP_1}
2. ${STEP_2}
3. ${STEP_3}

**VALIDATION:**
- Schedule regenerated successfully: ${REGEN_STATUS}
- ACGME compliance verified: ${COMPLIANCE_STATUS}

Report error and recovery.
```

## 12. SOLVER CONTROL TEMPLATE

```
**SOLVER STATUS REPORT**
**Report Date:** ${TODAY}

**CURRENT SOLVE:**
- Job ID: ${JOB_ID}
- Objective: ${OBJECTIVE}
- Status: ${STATUS} (RUNNING/COMPLETED/FAILED)
- Progress: ${PROGRESS}%
- Elapsed time: ${ELAPSED_TIME}s

**PERFORMANCE METRICS:**
- Best feasible solution: ${BEST_FEASIBLE}
- Best lower bound: ${BEST_BOUND}
- Optimality gap: ${GAP}%
- Nodes explored: ${NODES}
- Nodes/second: ${NODES_PER_SEC}

**SOLVER HEALTH:**
- CPU usage: ${CPU_PERCENT}%
- Memory usage: ${MEMORY_PERCENT}%
- Worker count: ${WORKER_COUNT}
- Stability: ${STABILITY_STATUS}

**DECISION:**
- Continue solving: ${CONTINUE}
- Abort and accept current: ${ACCEPT_CURRENT}
- Reason: ${DECISION_REASON}

Report solver status.
```

---

*Last Updated: 2025-12-31*
*Agent: G5 Planning*
*Version: 1.0*
