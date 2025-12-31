# Scheduler Agent - Prompt Templates

> **Role:** Schedule optimization, resource allocation, rotation balancing
> **Model:** Claude Opus 4.5
> **Mission:** Create optimal, balanced schedules

## 1. SCHEDULE GENERATION TEMPLATE

```
**SCHEDULE GENERATION MISSION**

**OBJECTIVE:** Generate schedule for ${SCHEDULE_PERIOD}

**INPUT PARAMETERS:**
- Personnel: ${PERSONNEL_COUNT}
- Rotations: ${ROTATION_TYPES}
- Duration: ${DURATION_DAYS} days
- Constraints: ${CONSTRAINT_COUNT}

**OPTIMIZATION OBJECTIVES:**
1. ACGME compliance (hard constraint)
2. Coverage >= ${COVERAGE_TARGET}%
3. Rotation balance (variance <= ${BALANCE_TARGET}%)
4. Workload distribution (CV <= ${WORKLOAD_TARGET})
5. Minimize disruption (<= ${DISRUPTION_LIMIT}% change)

**SCHEDULE GENERATION WORKFLOW:**
1. Validate input constraints
2. Initialize solver with parameters
3. Generate initial feasible solution (${TIME_1}s budget)
4. Optimize solution (${TIME_2}s budget)
5. Validate ACGME compliance
6. Generate backup schedule
7. Report metrics

**SUCCESS CRITERIA:**
- Feasible schedule found: YES
- ACGME compliance: 100%
- Coverage: >= ${COVERAGE_TARGET}%
- Generation time: <= ${TIME_LIMIT}s
- Quality score: >= ${QUALITY_THRESHOLD}

Generate schedule optimally.
```

## 2. ROTATION BALANCING TEMPLATE

```
**ROTATION BALANCE ANALYSIS**

**OBJECTIVE:** Balance rotations across personnel

**CURRENT DISTRIBUTION:**
- Rotation A: ${PEOPLE_A} people (expected: ${EXPECTED_A})
- Rotation B: ${PEOPLE_B} people (expected: ${EXPECTED_B})
- Rotation C: ${PEOPLE_C} people (expected: ${EXPECTED_C})

**BALANCE METRICS:**
- Variance: ${VARIANCE}%
- Coefficient of variation: ${CV}
- Fairness score: ${FAIRNESS_SCORE}

**TARGET BALANCE:**
- Each rotation gets equal exposure: ${ROTATION_WEIGHT}%
- Variance target: <= ${TARGET_VARIANCE}%
- Fairness target: >= ${FAIRNESS_TARGET}

**IMBALANCE ISSUES:**
- Over-allocated: ${OVER_ALLOCATED}
- Under-allocated: ${UNDER_ALLOCATED}
- Preference conflicts: ${PREFERENCE_CONFLICTS}

**REBALANCING STRATEGY:**
1. Identify personnel in over-rotations
2. Find eligible positions in under-rotations
3. Swap assignments while preserving constraints
4. Validate ACGME compliance after each swap
5. Measure improvement

**REBALANCING RESULTS:**
- Variance after: ${VARIANCE_AFTER}%
- Personnel affected: ${AFFECTED_COUNT}
- Changes required: ${CHANGE_COUNT}
- Fairness improved: ${FAIRNESS_IMPROVEMENT}%

Balance rotations fairly.
```

## 3. WORKLOAD DISTRIBUTION TEMPLATE

```
**WORKLOAD DISTRIBUTION ANALYSIS**

**OBJECTIVE:** Minimize workload variance across personnel

**CURRENT WORKLOAD:**
- Total hours available: ${TOTAL_HOURS}
- Personnel count: ${PERSONNEL_COUNT}
- Target per person: ${TARGET_HOURS} hours
- Current distribution: ${DISTRIBUTION_STATS}

**WORKLOAD METRICS:**
- Mean: ${MEAN_HOURS}
- Std Dev: ${STD_DEV}
- Coefficient of Variation: ${CV}
- Max: ${MAX_HOURS}
- Min: ${MIN_HOURS}
- Range: ${RANGE}

**TARGETS:**
- Target CV: <= ${TARGET_CV}
- Max variance: ±${MAX_VARIANCE}%
- Fairness: All within ±${FAIRNESS_MARGIN}% of mean

**OVER-LOADED PERSONNEL:**
- Person A: ${HOURS_A} hours (${EXCESS_A}% over target)
- Person B: ${HOURS_B} hours (${EXCESS_B}% over target)

**UNDER-LOADED PERSONNEL:**
- Person C: ${HOURS_C} hours (${DEFICIT_C}% under target)
- Person D: ${HOURS_D} hours (${DEFICIT_D}% under target)

**OPTIMIZATION:**
1. Identify load balancing swaps
2. Minimize cascading changes
3. Respect personnel constraints
4. Preserve rotation balance
5. Validate ACGME compliance

**RESULTS AFTER REBALANCING:**
- New CV: ${NEW_CV}
- Improvement: ${IMPROVEMENT}%
- Changes required: ${CHANGES}
- Personnel satisfied: ${SATISFACTION}%

Optimize workload distribution.
```

## 4. CONSTRAINT SATISFACTION TEMPLATE

```
**CONSTRAINT SATISFACTION ANALYSIS**

**HARD CONSTRAINTS (Must satisfy):**
1. ACGME 80-hour rule: ${SATISFIED_80H}
2. ACGME 1-in-7 rule: ${SATISFIED_1IN7}
3. Supervision ratios: ${SATISFIED_RATIOS}
4. Credential requirements: ${SATISFIED_CREDS}
5. Personnel unavailability: ${SATISFIED_UNAVAIL}

**SATISFACTION SCORE:** ${SATISFACTION_SCORE}/5

**SOFT CONSTRAINTS (Prefer to satisfy):**
1. Rotation balance: ${SAT_ROTATION}% satisfaction
2. Workload balance: ${SAT_WORKLOAD}% satisfaction
3. Personnel preferences: ${SAT_PREFERENCES}% satisfaction
4. Minimize changes: ${SAT_STABILITY}% satisfaction

**OVERALL SATISFACTION:** ${OVERALL_SATISFACTION}%

**CONSTRAINT CONFLICTS:**
${CONFLICTS}

**CONSTRAINT RELAXATION OPTIONS:**
If infeasible, options to relax:
- Relax rotation balance: Allow ${RELAX_ROTATION}% variance
- Relax workload balance: Allow ±${RELAX_WORKLOAD}%
- Reduce time window: Generate for shorter period

Validate constraint satisfaction.
```

## 5. PERSONNEL PREFERENCE HANDLING TEMPLATE

```
**PERSONNEL PREFERENCES**

**PREFERENCE TYPES:**
1. Preferred rotations: ${PREF_ROTATION_COUNT}
2. Rotation avoidance: ${AVOID_ROTATION_COUNT}
3. Time-off requests: ${TIMEOFF_COUNT}
4. Co-location requests: ${COLOCATION_COUNT}
5. Separation requests: ${SEPARATION_COUNT}

**PREFERENCE SATISFACTION:**
- Tier 1 (Hard): 100% must satisfy
- Tier 2 (High): 90%+ satisfaction
- Tier 3 (Medium): 70%+ satisfaction
- Tier 4 (Low): 50%+ satisfaction

**CURRENT SATISFACTION:**
- Tier 1 preferences: ${SAT_TIER1}%
- Tier 2 preferences: ${SAT_TIER2}%
- Tier 3 preferences: ${SAT_TIER3}%
- Tier 4 preferences: ${SAT_TIER4}%

**CONFLICTING PREFERENCES:**
- Preference 1: ${CONFLICT_1}
- Preference 2: ${CONFLICT_2}

**RESOLUTION STRATEGY:**
1. Prioritize by tier
2. Satisfy tier 1 (hard constraints)
3. Maximize satisfaction of lower tiers
4. Use randomization for tied options
5. Report unsatisfied preferences

**FEEDBACK TO PERSONNEL:**
- Preferences granted: ${GRANTED}/${TOTAL}
- Satisfaction rate: ${SATISFACTION}%
- Explanation for denials: Provided

Handle personnel preferences fairly.
```

## 6. SCHEDULE VERSIONING TEMPLATE

```
**SCHEDULE VERSIONING**

**CURRENT SCHEDULE:**
- Version: ${VERSION}
- Generated: ${GENERATED_DATE}
- Period: ${START_DATE} to ${END_DATE}
- Quality score: ${QUALITY_SCORE}

**PREVIOUS VERSIONS:**
- Version N-1: ${PREV_VERSION}
- Version N-2: ${PREV_VERSION_2}
- Archive location: ${ARCHIVE_PATH}

**CHANGES FROM PREVIOUS:**
- Assignments changed: ${CHANGE_COUNT}
- Rotation changes: ${ROTATION_CHANGES}
- Personnel affected: ${AFFECTED_PERSONNEL}
- Stability score: ${STABILITY_SCORE}

**SCHEDULE COMPARISON:**
\`\`\`json
{
  "change_analysis": {
    "total_assignments": ${TOTAL},
    "unchanged": ${UNCHANGED},
    "changed": ${CHANGED},
    "new": ${NEW},
    "deleted": ${DELETED},
    "change_rate": ${CHANGE_RATE}%
  }
}
\`\`\`

**ROLLBACK CAPABILITY:**
- Previous version available: YES
- Rollback time: < 5 minutes
- Data consistency: Ensured

Manage schedule versions and changes.
```

## 7. SCHEDULE VALIDATION TEMPLATE

```
**POST-GENERATION VALIDATION**

**SCHEDULE:** ${SCHEDULE_ID}
**VALIDATION DATE:** ${TODAY}

**VALIDATION CHECKLIST:**

### Coverage
- [ ] All slots assigned: ${ALL_ASSIGNED}
- [ ] Coverage >= target: ${COVERAGE_MET}
- [ ] No double-booked personnel: ${NO_DOUBLE_BOOK}
- [ ] Backup coverage available: ${BACKUP_AVAILABLE}

### ACGME Compliance
- [ ] 80-hour rule: ${RULE_80H_PASS}
- [ ] 1-in-7 rule: ${RULE_1IN7_PASS}
- [ ] Supervision ratios: ${RATIO_PASS}
- [ ] Clinical supervision: ${CLINICAL_PASS}

### Balance
- [ ] Rotations balanced: ${ROTATION_BALANCED}
- [ ] Workload balanced: ${WORKLOAD_BALANCED}
- [ ] Preferences satisfied: ${PREFS_SATISFIED}

### Data Integrity
- [ ] No orphaned assignments: ${NO_ORPHANS}
- [ ] All references valid: ${REFS_VALID}
- [ ] Database consistency: ${DB_CONSISTENT}

**VALIDATION RESULT:** ${RESULT}

**BLOCKERS:** ${BLOCKERS}

Validate schedule comprehensively.
```

## 8. STATUS REPORT TEMPLATE

```
**SCHEDULER STATUS REPORT**

**REPORT DATE:** ${TODAY}

**SCHEDULE METRICS:**
- Schedules generated: ${SCHEDULE_COUNT}
- Success rate: ${SUCCESS_RATE}%
- Average quality score: ${AVG_QUALITY}
- Average generation time: ${AVG_TIME}s

**OPTIMIZATION METRICS:**
- ACGME compliance: ${COMPLIANCE}%
- Coverage: ${COVERAGE}%
- Rotation balance: ${ROTATION_BALANCE}
- Workload balance: ${WORKLOAD_BALANCE}
- Preference satisfaction: ${PREF_SATISFACTION}%

**ISSUES:**
- Infeasible schedules: ${INFEASIBLE}
- Failed generations: ${FAILED}
- User complaints: ${COMPLAINTS}

**NEXT:** ${NEXT_GOALS}
```

---

*Last Updated: 2025-12-31*
*Agent: Scheduler*
*Version: 1.0*
