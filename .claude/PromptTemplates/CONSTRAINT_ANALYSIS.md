# CONSTRAINT_ANALYSIS - Prompt Template

> **Purpose:** Analyze scheduling constraints to identify conflicts, quantify trade-offs, and recommend resolution strategies
> **Complexity:** Medium
> **Typical Duration:** 5-15 minutes
> **Prerequisites:** List of constraints, scheduling context, stakeholder priorities
> **Version:** 1.0.0
> **Last Updated:** 2025-12-26

---

## Input Parameters

### Required

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `{{constraints}}` | List[Dict] | Constraints to analyze | `[{name: "80-hour rule", type: "hard"}, {name: "Weekend preference", type: "soft"}]` |
| `{{context}}` | String | Scheduling scenario | `"February 2024 inpatient coverage planning"` |

### Optional

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `{{analysis_goal}}` | String | `"conflict_detection"` | What to analyze for | `"conflict_detection"`, `"feasibility"`, `"optimization"`, `"trade_off_assessment"` |
| `{{date_range}}` | String | `null` | Temporal scope (if relevant) | `"2024-02-01 to 2024-02-29"` |
| `{{residents}}` | List[String] | `[]` | Affected residents | `["PGY1-01", "PGY2-01"]` |
| `{{existing_schedule}}` | Dict | `null` | Current schedule to validate against | `{assignments: [...]}` |
| `{{priority_ranking}}` | List[String] | Auto | Constraint priority order | `["ACGME compliance", "Coverage", "Equity", "Preferences"]` |
| `{{conflict_resolution}}` | String | `"recommend"` | How to handle conflicts | `"recommend"`, `"enumerate_options"`, `"auto_resolve"` |
| `{{output_detail}}` | String | `"standard"` | Output depth | `"brief"`, `"standard"`, `"comprehensive"` |

---

## Template

```markdown
# Constraint Analysis: {{context}}

[IF date_range]
**Date Range:** {{date_range}}
[ENDIF]

[IF residents]
**Affected Personnel:** {{residents|join(", ")}}
[ENDIF]

**Analysis Goal:** {{analysis_goal|"Identify and resolve constraint conflicts"}}

---

## Constraints Inventory

### Hard Constraints (Must Satisfy)

[FOR constraint IN constraints WHERE constraint.type == "hard"]
#### {{loop.index}}. {{constraint.name}}

**Description:** {{constraint.description}}

**Type:** {{constraint.category|"regulatory/institutional/operational"}}

**Validation:** {{constraint.validation_rule}}

**Scope:** {{constraint.scope|"applies to all residents/rotations"}}

**Source:** {{constraint.source|"ACGME/Institutional Policy/Other"}}

**Penalty for Violation:** {{constraint.penalty|"Compliance violation, may affect accreditation"}}

[IF constraint.exceptions]
**Exceptions:**
[FOR exception IN constraint.exceptions]
- {{exception.condition}}: {{exception.allowance}}
[ENDFOR]
[ENDIF]

[ENDFOR]

**Total Hard Constraints:** {{constraints|filter(type="hard")|count}}

---

### Soft Constraints (Should Satisfy, Optimize)

[FOR constraint IN constraints WHERE constraint.type == "soft"]
#### {{loop.index}}. {{constraint.name}}

**Description:** {{constraint.description}}

**Type:** {{constraint.category|"preference/equity/quality"}}

**Optimization Weight:** {{constraint.weight|"1-10 scale"}}

**Validation:** {{constraint.validation_rule}}

**Scope:** {{constraint.scope}}

**Stakeholder:** {{constraint.requested_by|"Who wants this constraint"}}

**Benefit if Satisfied:** {{constraint.benefit}}

**Cost if Violated:** {{constraint.cost}}

[ENDFOR]

**Total Soft Constraints:** {{constraints|filter(type="soft")|count}}

---

## Conflict Detection

[IF analysis_goal == "conflict_detection" OR analysis_goal == "feasibility"]

### Pairwise Conflict Matrix

Identify which constraints conflict with each other:

| Constraint A | Constraint B | Conflict? | Severity | Explanation |
|--------------|--------------|-----------|----------|-------------|
[FOR a IN constraints]
[FOR b IN constraints WHERE b.id > a.id]
| {{a.name}} | {{b.name}} | [Yes/No/Conditional] | [Low/Medium/High] | [Why they conflict] |
[ENDFOR]
[ENDFOR]

### Conflict Details

[FOR conflict IN detected_conflicts]
#### Conflict {{loop.index}}: {{conflict.constraint_a}} ↔ {{conflict.constraint_b}}

**Severity:** {{conflict.severity|"High/Medium/Low"}}

**Description:**
{{conflict.explanation}}

**Scenario:**
{{conflict.example_scenario}}

**Mathematical Representation:**
```
{{conflict.mathematical_form}}
```

**Example:**
[Concrete example showing the conflict]

**Affected Scope:**
- **When:** {{conflict.when_occurs}}
- **Where:** {{conflict.which_rotations_or_dates}}
- **Who:** {{conflict.which_residents}}

**Frequency:**
{{conflict.frequency|"Always/Often/Rarely/Conditional"}}

[ENDFOR]

[ENDIF]

---

## Feasibility Analysis

[IF analysis_goal == "feasibility"]

### Overall Assessment

**Question:** Can all hard constraints be simultaneously satisfied?

**Answer:** [Yes / No / Conditional]

[IF feasible]
✅ **FEASIBLE**: All hard constraints can be satisfied simultaneously.

**Confidence Level:** {{confidence_level|"High/Medium/Low"}}

**Assumptions Required:**
[List any assumptions necessary for feasibility]
- [Assumption 1]
- [Assumption 2]

**Margin:** {{margin_description|"How much slack exists in the system"}

[ELIF infeasible]
❌ **INFEASIBLE**: Hard constraints cannot all be satisfied.

**Proof of Infeasibility:**
[Show why impossible - e.g., mathematical contradiction, resource shortage]

**Minimum Relaxation Required:**
To make feasible, at least one of these must be relaxed:
1. {{constraint_to_relax_1}} - Impact if relaxed: [...]
2. {{constraint_to_relax_2}} - Impact if relaxed: [...]

**Recommended Path Forward:**
[Which constraint to relax and why]

[ELSE]
⚠️ **CONDITIONAL**: Feasibility depends on specific circumstances.

**Conditions for Feasibility:**
[List conditions that must be met]
- [Condition 1]
- [Condition 2]

**Risk Factors:**
[What could make this infeasible]
- [Risk 1]
- [Risk 2]

[ENDIF]

### Resource Analysis

**Required Resources:**
- **Residents:** {{required_resident_count}} (Available: {{available_residents}})
- **Faculty:** {{required_faculty_count}} (Available: {{available_faculty}})
- **Blocks/Time:** {{required_blocks}} (Available: {{available_blocks}})

**Utilization Rates:**
- **Resident utilization:** {{resident_utilization_pct}}% (Target: <80% for sustainability)
- **Faculty utilization:** {{faculty_utilization_pct}}%

[IF resident_utilization_pct > 80]
⚠️ **Warning:** Resident utilization >80% indicates high risk of constraint violations and burnout.
[ENDIF]

[ENDIF]

---

## Trade-Off Assessment

[IF analysis_goal == "trade_off_assessment" OR analysis_goal == "optimization"]

### Trade-Off Matrix

When constraints conflict, assess the cost of satisfying one vs. the other:

[FOR trade_off IN trade_offs]
#### Trade-Off {{loop.index}}: {{trade_off.constraint_a}} vs. {{trade_off.constraint_b}}

**Scenario:**
{{trade_off.scenario_description}}

**Option A:** Satisfy {{trade_off.constraint_a}}, relax {{trade_off.constraint_b}}
- **Pros:**
  [FOR pro IN trade_off.option_a.pros]
  - {{pro}}
  [ENDFOR]
- **Cons:**
  [FOR con IN trade_off.option_a.cons]
  - {{con}}
  [ENDFOR]
- **Quantitative Impact:** {{trade_off.option_a.impact_metrics}}

**Option B:** Satisfy {{trade_off.constraint_b}}, relax {{trade_off.constraint_a}}
- **Pros:**
  [FOR pro IN trade_off.option_b.pros]
  - {{pro}}
  [ENDFOR]
- **Cons:**
  [FOR con IN trade_off.option_b.cons]
  - {{con}}
  [ENDFOR]
- **Quantitative Impact:** {{trade_off.option_b.impact_metrics}}

**Recommendation:**
{{trade_off.recommendation}}

**Rationale:**
{{trade_off.rationale}}

[ENDFOR]

### Pareto Frontier Analysis

[IF analysis_goal == "optimization"]

Identify the set of non-dominated solutions (where improving one objective requires worsening another):

**Objectives to Optimize:**
[FOR objective IN optimization_objectives]
- {{objective.name}}: {{objective.description}} (Weight: {{objective.weight}})
[ENDFOR]

**Pareto-Optimal Solutions:**

| Solution | {{objectives|map("name")|join(" | ")}} | Trade-off |
|----------|{{objectives|map(lambda x: "----")|join("|")}}|-----------|
[FOR solution IN pareto_solutions]
| {{solution.id}} | {{solution.objective_values|join(" | ")}} | {{solution.trade_off_description}} |
[ENDFOR]

**Visualization:**
[If possible, include 2D scatter plot of two main objectives]

**Recommended Solution:**
{{recommended_pareto_solution}}

**Why This Point on Frontier:**
{{recommendation_rationale}}

[ENDIF]

[ENDIF]

---

## Constraint Relaxation Analysis

If infeasible, analyze impact of relaxing each constraint:

### Relaxation Options

[FOR constraint IN constraints WHERE constraint.type == "hard"]
#### Option {{loop.index}}: Relax "{{constraint.name}}"

**Original Requirement:** {{constraint.description}}

**Proposed Relaxation:** {{constraint.relaxation_proposal}}

**Impact:**
- **Compliance:** {{constraint.relaxation_impact.compliance}}
- **Operations:** {{constraint.relaxation_impact.operations}}
- **Risk:** {{constraint.relaxation_impact.risk}}

**Stakeholder Approval Needed:** {{constraint.relaxation_approval_needed}}

**Reversibility:** {{constraint.relaxation_reversibility|"Can this be temporary or must it be permanent?"}}

**Precedent:** {{constraint.relaxation_precedent|"Has this been done before? Where?"}}

[ENDFOR]

### Recommended Relaxation Strategy

[IF conflict_resolution == "recommend"]
**Recommendation:** {{relaxation_recommendation}}

**Justification:**
{{relaxation_justification}}

**Implementation:**
1. {{relaxation_step_1}}
2. {{relaxation_step_2}}
3. {{relaxation_step_3}}

**Mitigation:**
[How to minimize negative impact of relaxation]
- {{mitigation_1}}
- {{mitigation_2}}

[ELIF conflict_resolution == "enumerate_options"]
**Options Presented for Decision:**
1. {{option_1.description}} - Impact: {{option_1.impact}}
2. {{option_2.description}} - Impact: {{option_2.impact}}
3. {{option_3.description}} - Impact: {{option_3.impact}}

**Decision Needed From:** {{decision_maker|"Program Director"}}

[ELIF conflict_resolution == "auto_resolve"]
**Auto-Resolved Using Priority Hierarchy:**

Priority Order: {{priority_ranking|join(" > ")}}

**Resolution:**
{{auto_resolution_explanation}}

**Constraints Satisfied:** {{satisfied_constraints|join(", ")}}
**Constraints Relaxed:** {{relaxed_constraints|join(", ")}}

[ENDIF]

---

## Validation Against Existing Schedule

[IF existing_schedule]

### Current Schedule Validation

**Constraint Compliance:**

| Constraint | Status | Violations | Details |
|------------|--------|------------|---------|
[FOR constraint IN constraints]
| {{constraint.name}} | [✅ Pass / ⚠️ Warning / ❌ Fail] | {{violation_count}} | {{violation_details}} |
[ENDFOR]

**Overall Compliance:** {{overall_compliance_pct}}%

[IF violations_found]
### Violations Found

[FOR violation IN violations]
#### {{violation.constraint_name}} Violation

**Date/Time:** {{violation.when}}
**Resident(s):** {{violation.who}}
**Details:** {{violation.what}}
**Severity:** {{violation.severity}}

**Remediation:**
{{violation.how_to_fix}}

[ENDFOR]
[ENDIF]

[ENDIF]

---

## Recommendations

[IF output_detail == "brief"]
### Summary Recommendations

1. **Immediate:** {{immediate_recommendation}}
2. **Short-term:** {{short_term_recommendation}}
3. **Long-term:** {{long_term_recommendation}}

[ELIF output_detail == "comprehensive"]
### Detailed Recommendations

#### Immediate Actions (0-7 days)
[Actions to take right now to address critical conflicts]

- [ ] {{immediate_action_1}}
  - **Purpose:** {{purpose_1}}
  - **Impact:** {{impact_1}}
  - **Effort:** {{effort_1}}

- [ ] {{immediate_action_2}}
  - **Purpose:** {{purpose_2}}
  - **Impact:** {{impact_2}}
  - **Effort:** {{effort_2}}

#### Short-term Solutions (1-4 weeks)
[Process or policy adjustments to reduce conflicts]

- [ ] {{short_term_action_1}}
  - **Purpose:** {{purpose}}
  - **Impact:** {{impact}}
  - **Effort:** {{effort}}

- [ ] {{short_term_action_2}}
  - **Purpose:** {{purpose}}
  - **Impact:** {{impact}}
  - **Effort:** {{effort}}

#### Long-term Strategy (1-6 months)
[Systemic changes to prevent conflicts]

- [ ] {{long_term_action_1}}
  - **Purpose:** {{purpose}}
  - **Impact:** {{impact}}
  - **Effort:** {{effort}}

- [ ] {{long_term_action_2}}
  - **Purpose:** {{purpose}}
  - **Impact:** {{impact}}
  - **Effort:** {{effort}}

[ELSE]
### Standard Recommendations

#### Critical Issues
[Must address immediately]

1. {{critical_issue_1}}: {{recommendation_1}}
2. {{critical_issue_2}}: {{recommendation_2}}

#### Process Improvements
[Would reduce future conflicts]

1. {{process_improvement_1}}
2. {{process_improvement_2}}

#### Policy Considerations
[May need PD/leadership decision]

1. {{policy_question_1}}
2. {{policy_question_2}}

[ENDIF]

---

## Stakeholder Communication

### Key Messages

**For Program Director:**
{{pd_message}}

**For Schedulers:**
{{scheduler_message}}

**For Residents:**
{{resident_message}}

### Decision Points

[List any decisions that need stakeholder input]

1. **Decision:** {{decision_question_1}}
   - **Options:** {{options}}
   - **Recommendation:** {{recommendation}}
   - **Deadline:** {{decision_deadline}}

2. **Decision:** {{decision_question_2}}
   - **Options:** {{options}}
   - **Recommendation:** {{recommendation}}
   - **Deadline:** {{decision_deadline}}

---

```

---

## Examples

### Example 1: Conflicting ACGME and Coverage Constraints

**Instantiation:**
```
constraints: [
  {
    name: "80-hour rule",
    type: "hard",
    description: "Residents cannot exceed 80 clinical hours per week averaged over 4 weeks",
    validation_rule: "avg_hours_4week(resident, date) <= 80",
    source: "ACGME CPR Section VI",
    category: "regulatory"
  },
  {
    name: "Inpatient coverage minimum",
    type: "hard",
    description: "Minimum 3 residents on inpatient service during weekdays",
    validation_rule: "count_residents(rotation='inpatient', day_type='weekday') >= 3",
    source: "Institutional policy",
    category: "operational"
  },
  {
    name: "Night Float consecutive limit",
    type: "hard",
    description: "No more than 6 consecutive night shifts",
    validation_rule: "consecutive_nights(resident) <= 6",
    source: "Institutional policy (2023-04)",
    category: "institutional"
  }
]
context: "February 2024 scheduling with 1 resident on unexpected medical leave"
analysis_goal: "conflict_detection"
residents: ["PGY1-01", "PGY1-02", "PGY2-01", "PGY2-02", "PGY3-01"]
date_range: "2024-02-01 to 2024-02-29"
priority_ranking: ["ACGME compliance", "Coverage minimums", "Institutional policies"]
conflict_resolution: "recommend"
output_detail: "standard"
```

**Output:**

```markdown
# Constraint Analysis: February 2024 scheduling with 1 resident on unexpected medical leave

**Date Range:** 2024-02-01 to 2024-02-29
**Affected Personnel:** PGY1-01, PGY1-02, PGY2-01, PGY2-02, PGY3-01
**Analysis Goal:** Identify and resolve constraint conflicts

---

## Constraints Inventory

### Hard Constraints (Must Satisfy)

#### 1. 80-hour rule

**Description:** Residents cannot exceed 80 clinical hours per week averaged over 4 weeks

**Type:** Regulatory

**Validation:** `avg_hours_4week(resident, date) <= 80`

**Scope:** Applies to all residents

**Source:** ACGME CPR Section VI

**Penalty for Violation:** ACGME compliance violation, may affect accreditation status

**Exceptions:** None (only rare circumstances with PD documentation)

---

#### 2. Inpatient coverage minimum

**Description:** Minimum 3 residents on inpatient service during weekdays

**Validation:** `count_residents(rotation='inpatient', day_type='weekday') >= 3`

**Scope:** Inpatient rotation, weekdays only

**Source:** Institutional policy

**Penalty for Violation:** Inadequate patient supervision, potential patient safety risk

---

#### 3. Night Float consecutive limit

**Description:** No more than 6 consecutive night shifts

**Validation:** `consecutive_nights(resident) <= 6`

**Scope:** Night Float rotation

**Source:** Institutional policy (2023-04)

**Penalty for Violation:** Circadian disruption, resident wellness concern

---

**Total Hard Constraints:** 3

---

## Conflict Detection

### Pairwise Conflict Matrix

| Constraint A | Constraint B | Conflict? | Severity | Explanation |
|--------------|--------------|-----------|----------|-------------|
| 80-hour rule | Inpatient coverage minimum | Yes | High | With only 5 residents (N-1 situation), maintaining 3-person weekday coverage while respecting 80-hour limit may be impossible |
| 80-hour rule | Night Float consecutive limit | No | N/A | These constraints are orthogonal (address different aspects) |
| Inpatient coverage minimum | Night Float consecutive limit | Conditional | Medium | If Night Float resident needed to cover inpatient gaps, may conflict |

---

### Conflict Details

#### Conflict 1: 80-hour rule ↔ Inpatient coverage minimum

**Severity:** High

**Description:**
With 5 residents instead of the normal 6 (due to medical leave), maintaining minimum inpatient coverage of 3 residents on weekdays while keeping all residents under 80 hours per week creates a resource constraint. The math doesn't add up.

**Scenario:**
- Weekdays in February: 20 days (excluding weekends)
- Minimum coverage: 3 residents/day
- Total resident-days needed: 20 × 3 = 60 resident-days
- Available resident-days (5 residents × 20 weekdays): 100 resident-days
- BUT: Must also cover weekends, nights, other rotations (clinic, procedures)

**Mathematical Representation:**
```
Let:
- R = number of available residents = 5
- C_inpatient = minimum inpatient coverage = 3
- C_other = minimum coverage for other rotations
- H_max = maximum hours per week per resident = 80
- H_inpatient = hours per inpatient block ≈ 12

Constraint 1: C_inpatient * blocks_per_week >= 3 * 10 (weekday blocks)
Constraint 2: sum(hours_worked[r]) <= 80 for all r in R

With R=5, satisfying C_inpatient=3 leaves only 2 residents for all other rotations.
If those 2 must cover nights + clinic + procedures, they will exceed 80 hours.
```

**Example:**
Week 1 assignments:
- PGY1-01: Inpatient (72 hours)
- PGY1-02: Inpatient (72 hours)
- PGY2-01: Inpatient (72 hours)
- PGY2-02: Night Float (60 hours) + Clinic backup (20 hours) = 80 hours
- PGY3-01: Procedures (40 hours) + Call coverage (40 hours) = 80 hours

**Problem:** This barely works for week 1, but rotations need to change. When residents rotate off inpatient, there aren't enough people to maintain 3-person coverage AND cover other rotations AND stay under 80 hours.

**Affected Scope:**
- **When:** Entire month of February
- **Where:** Primarily inpatient and night coverage rotations
- **Who:** All 5 residents (but especially PGY2-02 and PGY3-01 who must flex between rotations)

**Frequency:** Always (conflict exists for entire N-1 duration)

---

## Feasibility Analysis

### Overall Assessment

**Question:** Can all hard constraints be simultaneously satisfied?

**Answer:** No - Infeasible under current N-1 conditions

❌ **INFEASIBLE**: Hard constraints cannot all be satisfied with only 5 residents.

**Proof of Infeasibility:**

**Resource calculation:**
- Total hours needed per week:
  - Inpatient: 3 residents × 72 hours = 216 hours
  - Night Float: 1 resident × 60 hours = 60 hours
  - Clinic: 1 resident × 40 hours = 40 hours
  - Procedures: 1 resident × 40 hours = 40 hours
  - **Total: 356 hours/week**

- Total hours available (respecting 80-hour limit):
  - 5 residents × 80 hours = 400 hours/week

- **Margin: 400 - 356 = 44 hours (11% slack)**

**Why still infeasible despite positive margin:**
While total hours show slack, the constraint is not just total hours but *distribution*. Inpatient requires 3 specific residents simultaneously, which locks them into 216 hours. The remaining 2 residents have 160 hours available but need to cover 140 hours of rotations (Night Float, Clinic, Procedures). This works in theory, but:

1. **Rotation continuity:** Residents can't be split across multiple rotations per week easily
2. **Rest requirements:** 1-in-7 rule reduces usable hours
3. **Variability:** Emergency coverage needs will push some residents over 80 hours

**Minimum Relaxation Required:**
To make feasible, at least one of these must be relaxed:

1. **Inpatient coverage minimum (3 → 2 on weekdays)**
   - Impact: Reduces required hours by 72/week
   - Creates slack: 116 hours/week (29%)
   - Allows sustainable rotation scheduling
   - **Requires:** Institutional policy waiver + enhanced faculty supervision

2. **80-hour limit (80 → 85 hours temporarily)**
   - Impact: Adds 25 hours/week to available pool (5 × 5)
   - Creates slack: 69 hours/week (17%)
   - **Requires:** ACGME exception (unlikely to be granted except rare circumstances)

**Recommended Path Forward:**
Relax inpatient coverage minimum to 2 residents on weekdays (not the 80-hour rule, which is non-negotiable ACGME requirement).

**Justification:**
- Institutional policies can be waived with PD approval
- ACGME rules cannot
- Patient safety can be maintained with enhanced attending supervision
- This is a temporary measure during medical leave (1-2 months)

---

### Resource Analysis

**Required Resources:**
- **Residents:** 6 for sustainable scheduling (Available: 5)
- **Faculty:** 4 (Available: 4) ✅
- **Blocks/Time:** 232 blocks (Available: 232) ✅

**Utilization Rates:**
- **Resident utilization:** 89% (356/400) ⚠️ (Target: <80% for sustainability)
- **Faculty utilization:** 72% ✅

⚠️ **Warning:** Resident utilization >80% indicates high risk of constraint violations and burnout. This is an N-1 situation requiring either reduced coverage or additional personnel.

---

## Trade-Off Assessment

### Trade-Off 1: ACGME Compliance vs. Coverage Adequacy

**Scenario:**
During N-1 staffing shortage, must choose between maintaining full inpatient coverage (3 residents) or respecting 80-hour limits.

**Option A:** Satisfy 80-hour rule, relax inpatient coverage minimum
- **Pros:**
  - ACGME compliance maintained
  - Residents protected from overwork
  - No accreditation risk
  - Defensible from wellness perspective
- **Cons:**
  - Reduced inpatient coverage (2 instead of 3)
  - Increased faculty supervision burden
  - Potential patient care concerns (mitigated by attending coverage)
- **Quantitative Impact:**
  - Resident hours: All <80/week
  - Inpatient coverage: 67% of normal (2/3)
  - Faculty workload: +15% supervision time

**Option B:** Satisfy inpatient coverage, relax 80-hour rule
- **Pros:**
  - Full inpatient coverage maintained
  - No changes to patient care model
  - Faculty workload unchanged
- **Cons:**
  - ACGME violation (some residents >80 hours)
  - Accreditation risk
  - Resident wellness risk
  - Violates federal work hour regulations
- **Quantitative Impact:**
  - Resident hours: 2-3 residents will exceed 80 hours (estimated 82-85 hours)
  - Inpatient coverage: 100% (3 residents)
  - Compliance: Violation

**Recommendation:** **Option A** - Reduce inpatient coverage to 2 residents

**Rationale:**
1. **ACGME compliance is non-negotiable:** Violations affect program accreditation
2. **Patient safety can be maintained:** Increase attending supervision to compensate
3. **Temporary measure:** Medical leave is time-limited (expected 6-8 weeks)
4. **Precedent:** Other programs have used enhanced supervision during N-1 situations
5. **Risk mitigation:** Document PD approval, notify department chair, increase faculty rounding

---

## Constraint Relaxation Analysis

### Relaxation Options

#### Option 1: Relax "Inpatient coverage minimum"

**Original Requirement:** Minimum 3 residents on inpatient service during weekdays

**Proposed Relaxation:** Reduce to 2 residents on weekdays during medical leave period (Feb 1 - estimated March 15)

**Impact:**
- **Compliance:** No ACGME violation (ACGME sets supervision ratios, not absolute coverage numbers)
- **Operations:** Reduced resident coverage compensated by increased attending presence
- **Risk:** Patient care risk mitigated by enhanced faculty supervision + triage protocols

**Stakeholder Approval Needed:** Program Director (must approve), Department Chair (should notify), Residents (inform)

**Reversibility:** Fully reversible - return to 3-resident coverage when medical leave ends

**Precedent:** Similar approach used during 2023 deployment (reference: INC-2023-042)

---

#### Option 2: Relax "80-hour rule"

**Original Requirement:** Residents cannot exceed 80 clinical hours per week averaged over 4 weeks

**Proposed Relaxation:** Allow up to 85 hours per week during February

**Impact:**
- **Compliance:** ACGME violation - reportable to ACGME
- **Operations:** Allows full 3-resident inpatient coverage
- **Risk:** High - accreditation risk, resident wellness concern, violation of work hour regulations

**Stakeholder Approval Needed:** ACGME (would need rare circumstances exception), Institutional GME office, DIO

**Reversibility:** Difficult - violation remains on record even after corrected

**Precedent:** Rarely granted; typically only for natural disasters or extreme circumstances

---

### Recommended Relaxation Strategy

**Recommendation:** Relax inpatient coverage minimum from 3 to 2 residents during medical leave period (Option 1)

**Justification:**
1. **Legal compliance:** Maintains ACGME compliance, avoids work hour violations
2. **Patient safety:** Enhanced faculty supervision compensates for reduced resident coverage
3. **Reversibility:** Easily reversed when medical leave ends
4. **Precedent:** Successfully used in past during deployment situations
5. **Risk profile:** Lower risk than ACGME violation

**Implementation:**
1. **Document PD approval** - Written approval memo with specific dates and mitigation plan
2. **Notify stakeholders** - Department Chair, GME office, affected faculty
3. **Enhance supervision** - Add attending physician rounding on inpatient service (7am and 5pm)
4. **Set expiration** - Policy reverts to 3-resident minimum on March 15 or return of resident from medical leave
5. **Monitor closely** - Daily check-ins with inpatient team, weekly QI review

**Mitigation:**
- **Attending coverage:** Add attending rounding twice daily (morning and evening)
- **Triage protocol:** Increase use of hospitalist service for admissions
- **Backup plan:** Moonlighter on standby for high-census days
- **Communication:** Daily huddles between residents and attendings

---

## Recommendations

### Critical Issues
[Must address immediately]

1. **N-1 staffing requires coverage reduction:** Inpatient coverage must be reduced to 2 residents to maintain ACGME compliance
   - **Action:** Obtain PD written approval for temporary policy waiver
   - **Timeline:** Before February 1
   - **Owner:** Chief Resident + PD

2. **Enhanced supervision plan needed:** Compensate for reduced coverage with increased faculty presence
   - **Action:** Schedule attending physician rounding twice daily
   - **Timeline:** Concurrent with coverage reduction
   - **Owner:** Inpatient Service Director

### Process Improvements
[Would reduce future conflicts]

1. **Implement N-1 contingency planning:** Pre-approved protocols for staffing shortages
   - Reference: `.claude/Methodologies/N-1_Contingency_Protocol.md`

2. **Create coverage flexibility pool:** Identify moonlighters or swing residents in advance

### Policy Considerations
[May need PD/leadership decision]

1. **Should institutional coverage minimums include N-1 exceptions?** Current policy doesn't address staffing shortages
   - Recommend: Add exception clause to institutional policy for documented staffing shortages

2. **What is threshold for calling moonlighter vs. reducing coverage?** Need decision criteria

---

## Stakeholder Communication

### Key Messages

**For Program Director:**
"Due to medical leave, we face a resource constraint where maintaining 3-person inpatient coverage would force 80-hour violations. Recommend reducing inpatient coverage to 2 residents (temporary, until March 15) with enhanced attending supervision. This maintains ACGME compliance while ensuring patient safety through increased faculty presence. Need your written approval."

**For Schedulers:**
"February schedule will use 2-resident inpatient coverage (not 3) due to medical leave. Adjust schedule templates accordingly. Watch for duty hour totals - margin is tight. Flag any residents approaching 75 hours."

**For Residents:**
"PGY2-03 is on medical leave through mid-March. To maintain ACGME compliance, inpatient coverage will be 2 residents instead of 3 during this period. Attendings will increase rounding presence (twice daily). Workload will be slightly higher but within duty hour limits. Moonlighter available for backup."

### Decision Points

1. **Decision:** Approve temporary reduction of inpatient coverage from 3 to 2 residents?
   - **Options:** (A) Approve, (B) Deny - find alternative solution, (C) Approve with conditions
   - **Recommendation:** Approve (Option A)
   - **Deadline:** January 28 (before February schedule starts)

2. **Decision:** Set threshold for calling moonlighter backup
   - **Options:** (A) Call if census >12 patients, (B) Call if any resident >70 hours, (C) Call proactively 1 day/week
   - **Recommendation:** Option B (reactive based on hours)
   - **Deadline:** February 1

---
```

---

### Example 2: Preference vs. Equity Conflict (Brief Output)

**Instantiation:**
```
constraints: [
  {
    name: "Resident preference: PGY2-01 avoid weekends in January",
    type: "soft",
    description: "PGY2-01 requests to avoid weekend shifts in January for family event",
    weight: 7,
    requested_by: "PGY2-01",
    benefit: "Increased resident satisfaction, family event attendance"
  },
  {
    name: "Equity in weekend distribution",
    type: "soft",
    description: "All residents should work roughly equal number of weekend shifts",
    weight: 8,
    benefit: "Fair workload distribution, prevents resentment"
  }
]
context: "January 2024 schedule generation"
analysis_goal: "trade_off_assessment"
priority_ranking: ["Equity", "Preferences"]
conflict_resolution: "recommend"
output_detail: "brief"
```

**Output:**

```markdown
# Constraint Analysis: January 2024 schedule generation

**Analysis Goal:** Assess trade-offs between constraints

---

## Trade-Off Assessment

### Trade-Off 1: Equity in weekend distribution vs. Resident preference (PGY2-01 avoid weekends)

**Scenario:**
PGY2-01 requests to avoid weekend shifts in January for family event, but this would create inequity (other residents work 3-4 weekend shifts, PGY2-01 works 0).

**Option A:** Honor PGY2-01 preference (0 weekend shifts in January)
- **Impact:** PGY2-01 works 0 weekends, others work 4-5 weekends (inequality)
- **Equity metric:** Coefficient of variation = 0.82 (high inequality)

**Option B:** Maintain equity (PGY2-01 works 3-4 weekend shifts like others)
- **Impact:** Preference denied, resident may miss family event
- **Equity metric:** Coefficient of variation = 0.12 (low inequality)

**Recommendation:** **Partial compromise** - PGY2-01 works 2 weekend shifts (reduced but not zero)

**Rationale:** Balance between honoring request and maintaining equity. Other residents also have family obligations; completely exempting PGY2-01 sets problematic precedent.

---

## Recommendations

### Summary Recommendations

1. **Immediate:** Assign PGY2-01 to 2 weekend shifts in January (not 0, not 4) - partial accommodation
2. **Short-term:** Communicate decision to PGY2-01 with explanation (equity rationale)
3. **Long-term:** Create formal preference request policy (criteria, limits, fairness guidelines)
```

---

## Validation Checklist

Before finalizing constraint analysis:

- [ ] **All constraints cataloged** (hard and soft separated)
- [ ] **Conflicts identified** (pairwise matrix completed)
- [ ] **Feasibility assessed** (mathematical validation if possible)
- [ ] **Trade-offs quantified** (pros/cons with metrics)
- [ ] **Recommendations specific** (not vague advice)
- [ ] **Stakeholder communication drafted** (tailored to each audience)
- [ ] **Priority hierarchy applied** (clear basis for resolution)

[IF existing_schedule]
- [ ] **Schedule validated** (violations identified)
[ENDIF]

---

## Notes

### Mathematical Modeling

For rigorous feasibility analysis, constraints can be modeled as:
- **Linear constraints:** `a1*x1 + a2*x2 + ... <= b`
- **Boolean constraints:** `x AND y` or `x OR y`
- **Temporal constraints:** `before(x, y)`, `overlap(x, y)`

Use constraint programming (CP-SAT) or linear programming (LP) solvers to check satisfiability.

### Integration with Other Templates

Typical workflow:
1. **CONSTRAINT_ANALYSIS** → Identify conflicts and infeasibilities
2. **RESEARCH_POLICY** → Investigate if constraints can be relaxed
3. **SCHEDULE_GENERATION** → Generate schedule with resolved constraints
4. **INCIDENT_REVIEW** → Analyze failures if constraints were violated

### Common Conflict Patterns

- **Resource scarcity:** Coverage requirements exceed available personnel
- **Regulatory vs. operational:** ACGME limits conflict with coverage needs
- **Equity vs. preference:** Individual requests create unfair distribution
- **Temporal impossibility:** Sequencing constraints create circular dependencies

### Version History

- **v1.0.0** (2025-12-26): Initial template creation
  - Based on constraint programming and operations research methods
  - Includes feasibility analysis, trade-off assessment, and Pareto optimization
  - Tailored for medical residency scheduling constraints
