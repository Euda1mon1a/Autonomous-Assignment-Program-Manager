# SCHEDULE_GENERATION - Prompt Template

> **Purpose:** Generate compliant, optimized medical residency schedules with full constraint satisfaction and rationale
> **Complexity:** High
> **Typical Duration:** 10-30 minutes (depends on date range and complexity)
> **Prerequisites:** Access to resident/faculty data, rotation templates, ACGME rules, institutional policies
> **Version:** 1.0.0
> **Last Updated:** 2025-12-26

---

## Input Parameters

### Required

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `{{date_range}}` | String | Start and end dates for schedule | `"2024-01-01 to 2024-01-31"` |
| `{{residents}}` | List[String] | Resident IDs or list | `["PGY1-01", "PGY2-01", "PGY3-01"]` |
| `{{rotations}}` | List[String] | Available rotation types | `["inpatient", "clinic", "night_float", "procedures"]` |

### Optional

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `{{constraints}}` | List[Dict] | ACGME defaults | Additional constraints beyond ACGME | `[{type: "max_consecutive_nights", value: 6}]` |
| `{{preferences}}` | List[Dict] | None | Resident preferences (soft constraints) | `[{resident: "PGY2-01", avoid: "weekends in January"}]` |
| `{{fixed_assignments}}` | List[Dict] | None | Pre-determined assignments | `[{resident: "PGY1-01", date: "2024-01-15", rotation: "clinic"}]` |
| `{{coverage_requirements}}` | Dict | Defaults | Minimum coverage per rotation/time | `{inpatient: {weekday: 3, weekend: 2}}` |
| `{{optimization_goals}}` | List[String] | `["compliance", "equity"]` | Prioritized objectives | `["compliance", "preference_satisfaction", "equity", "workload_balance"]` |
| `{{validation_mode}}` | String | `"strict"` | How to handle constraint violations | `"strict"`, `"warn"`, `"preview"` |
| `{{output_format}}` | String | `"detailed"` | Output detail level | `"summary"`, `"detailed"`, `"audit"` |
| `{{include_rationale}}` | Boolean | `true` | Include decision rationale | `true`/`false` |

---

## Template

```markdown
# Schedule Generation: {{date_range}}

[IF validation_mode == "preview"]
🔍 **PREVIEW MODE**: This is a draft schedule. Constraints may not be fully satisfied.
[ENDIF]

[IF validation_mode == "strict"]
✅ **STRICT VALIDATION**: Schedule will fail if any hard constraint is violated.
[ENDIF]

---

## Schedule Parameters

### Temporal Scope
- **Date Range:** {{date_range}}
- **Total Days:** [Calculated from date_range]
- **Total Blocks:** [Days × 2 (AM/PM)]
- **Weekdays:** [Count]
- **Weekends:** [Count]
- **Holidays:** [List any holidays in range]

### Personnel
**Residents:**
[FOR resident IN residents]
- {{resident.id}} ({{resident.level}}) - {{resident.status}}
  [IF resident.on_leave]
  ⚠️ On leave: {{resident.leave_start}} to {{resident.leave_end}}
  [ENDIF]
[ENDFOR]

**Total Residents:** {{residents|count}}

### Rotations Available
[FOR rotation IN rotations]
- **{{rotation.name}}**: {{rotation.description}}
  - Duration: {{rotation.typical_duration}}
  - Supervision ratio: {{rotation.supervision_ratio}}
  - Credential requirements: {{rotation.required_credentials}}
[ENDFOR]

---

## Constraints

### Hard Constraints (MUST satisfy)

#### ACGME Requirements (Non-Negotiable)
1. **80-Hour Rule**
   - Max 80 clinical hours per week
   - Averaged over rolling 4-week period
   - Calculation: `avg_hours_4week(resident, date) <= 80` for all dates

2. **1-in-7 Rest**
   - One 24-hour period free of clinical duties every 7 days
   - Averaged over 4 weeks
   - Calculation: `free_days_per_4weeks(resident) >= 4`

3. **Supervision Ratios**
   - PGY-1: 1 faculty per 2 residents (minimum)
   - PGY-2/3: 1 faculty per 4 residents (minimum)
   - Calculation: `faculty_count / resident_count >= required_ratio`

4. **Continuous Duty Limits**
   - PGY-1: Max 16 hours continuous
   - PGY-2+: Max 24 hours + 4 hours transition (28 total)
   - Calculation: `shift_duration(resident, date) <= max_duration[resident.level]`

5. **Rest Between Shifts**
   - Minimum 8 hours between shifts (14 hours preferred)
   - Minimum 14 hours after 24-hour shifts
   - Calculation: `time_between_shifts(resident, shift1, shift2) >= minimum`

[IF constraints]
#### Additional Institutional Constraints
[FOR constraint IN constraints]
{{loop.index}}. **{{constraint.name}}**
   - Rule: {{constraint.description}}
   - Validation: {{constraint.validation_logic}}
   [IF constraint.exceptions]
   - Exceptions: {{constraint.exceptions}}
   [ENDIF]
[ENDFOR]
[ENDIF]

[IF fixed_assignments]
#### Pre-Determined Assignments (Fixed)
These assignments are locked and cannot be changed:
[FOR assignment IN fixed_assignments]
- {{assignment.resident}} → {{assignment.rotation}} on {{assignment.date}} ({{assignment.reason}})
[ENDFOR]
[ENDIF]

### Soft Constraints (SHOULD satisfy, optimize if possible)

#### Coverage Requirements
[FOR rotation, coverage IN coverage_requirements.items()]
**{{rotation}}:**
- Weekday minimum: {{coverage.weekday}} residents
- Weekend minimum: {{coverage.weekend}} residents
- Overnight minimum: {{coverage.overnight|default("N/A")}} residents
[ENDFOR]

[IF preferences]
#### Resident Preferences
[FOR pref IN preferences]
- **{{pref.resident}}**: {{pref.description}}
  - Priority: {{pref.priority|default("standard")}}
  - Reason: {{pref.reason|default("personal request")}}
[ENDFOR]
[ENDIF]

#### Equity Goals
- Distribute desirable rotations fairly across residents
- Balance total hours worked (target within 5% of mean)
- Equalize night shift burden (target within 10% of mean)
- Minimize clustering of undesirable shifts for any individual

---

## Optimization Strategy

### Primary Objectives (in order)
[FOR goal IN optimization_goals]
{{loop.index}}. **{{goal}}**: [Explain what this means]
[ENDFOR]

### Conflict Resolution Hierarchy
When constraints conflict, apply this priority order:
1. **ACGME compliance** (absolute priority - never compromise)
2. **Safety requirements** (supervision ratios, rest periods)
3. **Coverage minimums** (patient care continuity)
4. **Institutional policies** (local rules)
5. **Equity** (fair distribution of workload)
6. **Preferences** (individual requests - lowest priority)

[IF validation_mode == "strict"]
**Strict Mode:** Schedule generation will FAIL if any constraint in categories 1-4 cannot be satisfied.
[ENDIF]

[IF validation_mode == "warn"]
**Warning Mode:** Schedule will be generated but violations in categories 1-4 will trigger warnings for manual review.
[ENDIF]

---

## Schedule Generation Execution

### Phase 1: Initialization
1. Load resident data (current rotations, hours worked, leave status)
2. Load rotation templates and requirements
3. Validate input parameters
4. Check for conflicts in fixed_assignments

### Phase 2: Constraint Modeling
1. Encode ACGME rules as hard constraints
2. Encode institutional policies
3. Encode coverage requirements
4. Encode preferences as soft constraints with weights

### Phase 3: Solver Execution
1. Run constraint satisfaction algorithm (OR-Tools CP-SAT)
2. Apply optimization objectives in priority order
3. Track solver progress and decision points
4. Handle infeasibilities (backtrack or relax soft constraints)

### Phase 4: Validation
1. Verify all hard constraints satisfied
2. Calculate compliance metrics (duty hours, rest days)
3. Check coverage adequacy
4. Assess equity metrics (workload distribution)
5. Evaluate preference satisfaction rate

### Phase 5: Rationale Generation
[IF include_rationale]
For each assignment, document:
- **Why this resident?** (skill match, availability, equity)
- **Why this rotation?** (educational goals, coverage need)
- **Why this date?** (timing, sequencing, continuity)
- **Trade-offs made** (if any preferences sacrificed)
[ENDIF]

---

## Output Format

[IF output_format == "summary"]
### Schedule Summary

**Generation Status:** [Success/Partial/Failed]
**Compliance:** [100% / XX% with warnings]

#### Assignments by Week
[FOR week IN weeks]
**Week {{loop.index}} ({{week.start_date}} to {{week.end_date}})**
[FOR resident IN residents]
- {{resident.id}}: {{resident.rotation_this_week}}
[ENDFOR]
[ENDFOR]

#### Compliance Metrics
- **Duty hours:** All residents within 80-hour limit ✅
- **Rest days:** All residents have 1-in-7 ✅
- **Supervision:** Ratios maintained ✅

[ELIF output_format == "audit"]
<!-- Comprehensive audit trail format -->

### Schedule Generation Report

**Metadata:**
- Generated: [Timestamp]
- Generated by: [System/User]
- Date range: {{date_range}}
- Solver runtime: [Seconds]
- Iterations: [Count]

#### Input Summary
[Complete list of all inputs including residents, constraints, preferences]

#### Solver Log
[Detailed log of solver decisions, backtracks, optimizations]

#### Full Assignment Table
| Date | Block | Resident | Rotation | Hours | Cumulative Hours (4wk) | Notes |
|------|-------|----------|----------|-------|------------------------|-------|
| [Each row] | | | | | | |

#### Constraint Verification
[FOR constraint IN all_constraints]
**{{constraint.name}}**
- Status: ✅ Satisfied / ⚠️ Warning / ❌ Violated
- Check: [Details of validation]
- [IF violated] Violation details: [Explain]
[ENDFOR]

#### Equity Analysis
| Resident | Total Hours | Night Shifts | Weekend Shifts | Preference Satisfaction |
|----------|-------------|--------------|----------------|------------------------|
| [Each resident] | | | | |

**Variance metrics:**
- Hours worked std dev: [Value]
- Night shift distribution fairness: [Metric]

#### Decision Rationale
[FOR assignment IN all_assignments]
**{{assignment.date}} - {{assignment.resident}} → {{assignment.rotation}}**
- **Reason:** [Why this assignment was made]
- **Alternatives considered:** [Other options]
- **Trade-offs:** [What was sacrificed, if anything]
[ENDFOR]

[ELSE]
<!-- Detailed output format (default) -->

### Schedule: {{date_range}}

**Generation Status:** ✅ Success
**Compliance:** 100% ACGME compliant
**Preference Satisfaction:** [Percentage]%
**Solver Runtime:** [Seconds]

---

#### Week-by-Week Schedule

[FOR week IN date_range|split_by_week]
### Week {{loop.index}}: {{week.start_date}} to {{week.end_date}}

| Resident | Mon | Tue | Wed | Thu | Fri | Sat | Sun | Hours |
|----------|-----|-----|-----|-----|-----|-----|-----|-------|
[FOR resident IN residents]
| {{resident.id}} | {{mon_rotation}} | {{tue_rotation}} | {{wed_rotation}} | {{thu_rotation}} | {{fri_rotation}} | {{sat_rotation}} | {{sun_rotation}} | {{week_hours}} |
[ENDFOR]

**Week Summary:**
- Total resident hours: [Sum]
- Coverage achieved: [Percentages per rotation]
- Preferences honored this week: [Count]

[ENDFOR]

---

#### Compliance Verification

##### Duty Hours (80-Hour Rule)
[FOR resident IN residents]
**{{resident.id}}:**
- Week 1: {{hours_week1}} / 80
- Week 2: {{hours_week2}} / 80
- Week 3: {{hours_week3}} / 80
- Week 4: {{hours_week4}} / 80
- 4-week average: {{avg_hours}} / 80 [STATUS]
[ENDFOR]

##### Rest Days (1-in-7 Rule)
[FOR resident IN residents]
**{{resident.id}}:** {{rest_days_count}} days off in 28-day period ✅ (minimum 4 required)
[ENDFOR]

##### Supervision Ratios
[FOR rotation IN rotations]
**{{rotation}}:**
- Required ratio: {{rotation.required_ratio}}
- Actual ratio: {{rotation.actual_ratio}}
- Status: [✅/❌]
[ENDFOR]

---

#### Workload Equity

| Resident | Total Hours | Avg Hours/Week | Night Shifts | Weekend Shifts | Pref Satisfied |
|----------|-------------|----------------|--------------|----------------|----------------|
[FOR resident IN residents]
| {{resident.id}} | {{total_hours}} | {{avg_weekly}} | {{night_count}} | {{weekend_count}} | {{pref_pct}}% |
[ENDFOR]

**Fairness Metrics:**
- **Hours distribution:** Mean = {{mean_hours}}, StdDev = {{stddev_hours}} (target <5%)
- **Night shift equity:** [Coefficient of variation]
- **Weekend equity:** [Coefficient of variation]

---

[IF include_rationale]
#### Assignment Rationale

[FOR date IN date_range|iterate_days]
##### {{date}}

[FOR assignment IN assignments_on_date(date)]
**{{assignment.resident}} → {{assignment.rotation}}**
- **Why this resident?**
  {{assignment.rationale.why_resident}}
- **Educational value:**
  {{assignment.rationale.educational_benefit}}
- **Alternatives considered:**
  {{assignment.rationale.alternatives}}
  [IF assignment.rationale.alternatives_rejected]
  - Rejected because: {{assignment.rationale.rejection_reason}}
  [ENDIF]
- **Constraint impact:**
  - Hours after assignment: {{assignment.hours_after}}
  - Rest days remaining: {{assignment.rest_days_remaining}}
[ENDFOR]

[ENDFOR]
[ENDIF]

---

#### Warnings and Notes

[IF warnings]
⚠️ **Warnings:**
[FOR warning IN warnings]
- {{warning.type}}: {{warning.message}} ({{warning.date}}, {{warning.resident}})
[ENDFOR]
[ENDIF]

[IF notes]
📝 **Notes:**
[FOR note IN notes]
- {{note}}
[ENDFOR]
[ENDIF]

[ENDIF]

---

## Recommendations

### Immediate Actions
- [ ] Review generated schedule for reasonableness
- [ ] Obtain resident feedback on assignments
- [ ] Confirm coverage with faculty
- [ ] Publish schedule to scheduling system

### Monitoring
- [ ] Track actual hours worked vs. scheduled
- [ ] Monitor for swap requests (may indicate issues)
- [ ] Check ACGME compliance weekly

### Continuous Improvement
- [ ] Collect preference satisfaction data
- [ ] Analyze which constraints caused most conflict
- [ ] Consider adjusting coverage requirements if consistently hard to meet
- [ ] Update rotation templates based on actual experience

```

---

## Examples

### Example 1: Simple Monthly Schedule (Standard Detail)

**Instantiation:**
```
date_range: "2024-02-01 to 2024-02-29"
residents: ["PGY1-01", "PGY1-02", "PGY2-01", "PGY2-02", "PGY3-01"]
rotations: ["inpatient", "clinic", "night_float", "procedures", "admin"]
constraints: [
  {name: "Max consecutive nights", type: "consecutive_shifts", value: 6, applies_to: "night_float"}
]
preferences: [
  {resident: "PGY2-01", avoid: "2024-02-14 to 2024-02-16", reason: "family event", priority: "high"}
]
fixed_assignments: [
  {resident: "PGY3-01", date: "2024-02-01 to 2024-02-05", rotation: "admin", reason: "Chief resident admin week"}
]
coverage_requirements: {
  inpatient: {weekday: 2, weekend: 1},
  clinic: {weekday: 1, weekend: 0},
  night_float: {overnight: 1}
}
optimization_goals: ["compliance", "preference_satisfaction", "equity"]
validation_mode: "strict"
output_format: "detailed"
include_rationale: true
```

**Output:** [Would produce a detailed schedule as shown in template above]

---

### Example 2: Emergency Coverage Rescheduling (Urgent, Preview Mode)

**Instantiation:**
```
date_range: "2024-01-20 to 2024-01-31"
residents: ["PGY1-01", "PGY2-01", "PGY2-02", "PGY3-01"]  # One resident removed due to illness
rotations: ["inpatient", "night_float", "procedures"]
constraints: [
  {name: "PGY1-01 needs reduced hours", type: "max_hours_per_week", value: 60, applies_to: "PGY1-01", reason: "recovering from illness"}
]
preferences: []  # Ignored in emergency mode
fixed_assignments: []
coverage_requirements: {
  inpatient: {weekday: 2, weekend: 1},  # Reduced from normal 3/2 due to shortage
  night_float: {overnight: 1}
}
optimization_goals: ["compliance", "coverage_minimums"]  # Dropped equity due to emergency
validation_mode: "warn"  # Allow some flexibility
output_format: "summary"
include_rationale: false  # Speed up generation
```

**Output:**
```markdown
# Schedule Generation: 2024-01-20 to 2024-01-31

⚠️ **WARNING MODE**: Schedule may have soft constraint violations flagged for review.

---

## Schedule Summary

**Generation Status:** ✅ Success (with warnings)
**Compliance:** 100% ACGME compliant
**Coverage:** Met minimums (reduced from normal levels)

#### Assignments by Week

**Week 1 (2024-01-20 to 2024-01-26)**
- PGY1-01: Procedures (reduced hours)
- PGY2-01: Inpatient
- PGY2-02: Night Float
- PGY3-01: Inpatient

**Week 2 (2024-01-27 to 2024-01-31)**
- PGY1-01: Procedures (reduced hours)
- PGY2-01: Night Float
- PGY2-02: Inpatient
- PGY3-01: Inpatient

#### Compliance Metrics
- **Duty hours:** All residents within 80-hour limit ✅
  - PGY1-01: 55 hours/week (reduced as requested)
  - Others: 72-78 hours/week
- **Rest days:** All residents have 1-in-7 ✅
- **Supervision:** Ratios maintained ✅

#### Coverage Summary
- **Inpatient:** Met minimums (2 weekday, 1 weekend) ✅
- **Night Float:** Met minimums (1 overnight) ✅
- **Procedures:** Reduced availability (only PGY1-01) ⚠️

#### Warnings
⚠️ **Workload imbalance**: PGY2-01, PGY2-02, PGY3-01 working 72-78 hours/week (higher than ideal due to N-1 situation)
⚠️ **Procedures coverage**: Below normal levels (only 1 resident available)

#### Recommendations
- [ ] Monitor PGY1-01 recovery - can hours be increased next week?
- [ ] Consider requesting moonlighter for procedures coverage
- [ ] Plan to rebalance workload in March schedule
```

---

## Validation Checklist

Before finalizing schedule, verify:

- [ ] **All ACGME constraints satisfied** (80-hour, 1-in-7, supervision, duty limits)
- [ ] **Coverage requirements met** (or explicitly documented why not)
- [ ] **No scheduling conflicts** (residents double-booked, impossible sequences)
- [ ] **Leave/absence respected** (residents not scheduled when unavailable)
- [ ] **Credential requirements met** (residents qualified for assigned rotations)
- [ ] **Fixed assignments honored** (pre-determined slots unchanged)
- [ ] **Rationale documented** (decisions explained for audit trail)
- [ ] **Equity assessed** (no resident unfairly burdened)

[IF validation_mode == "strict"]
- [ ] **Zero hard constraint violations** (strict mode requirement)
[ENDIF]

[IF include_rationale]
- [ ] **Rationale complete** (all assignments explained)
[ENDIF]

---

## Notes

### Solver Strategy

The schedule generation uses **constraint programming (CP-SAT solver from OR-Tools)**:
- Hard constraints modeled as inviolable rules
- Soft constraints modeled as optimization objectives with penalties
- Solver explores assignment space systematically
- Backtracks when constraints violated
- Optimizes objective function (weighted sum of goals)

### Handling Infeasibility

If no feasible solution exists:
1. **Check input validity**: Are constraints contradictory?
2. **Relax soft constraints**: Drop lowest-priority preferences
3. **Extend date range**: More flexibility may resolve conflicts
4. **Add personnel**: May need additional residents/faculty
5. **Reduce coverage**: Negotiate lower coverage minimums

### Integration with Other Templates

Typical workflow:
1. **RESEARCH_POLICY** → Gather constraint requirements
2. **CONSTRAINT_ANALYSIS** → Identify conflicts before generation
3. **SCHEDULE_GENERATION** → Create schedule (this template)
4. **INCIDENT_REVIEW** → Analyze failures if schedule doesn't work in practice

### Performance Optimization

For faster generation:
- Set `include_rationale: false` (saves 30-50% time)
- Use `output_format: "summary"` (faster formatting)
- Limit `date_range` to 1-2 weeks (smaller search space)
- Pre-solve constraint conflicts using CONSTRAINT_ANALYSIS

### Version History

- **v1.0.0** (2025-12-26): Initial template creation
  - Based on OR-Tools CP-SAT solver implementation
  - Includes ACGME 2023 CPR requirements
  - Supports strict/warn/preview validation modes
  - Integrated with constraint analysis workflow
