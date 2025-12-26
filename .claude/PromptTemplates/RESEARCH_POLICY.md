# RESEARCH_POLICY - Prompt Template

> **Purpose:** Systematically investigate policies, regulations, or guidelines and synthesize actionable findings
> **Complexity:** Medium
> **Typical Duration:** 5-15 minutes
> **Prerequisites:** Access to relevant documentation sources (ACGME site, institutional policies, etc.)
> **Version:** 1.0.0
> **Last Updated:** 2025-12-26

---

## Input Parameters

### Required

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `{{policy_name}}` | String | Name/identifier of policy to research | `"ACGME 2023 Common Program Requirements"` |
| `{{policy_topic}}` | String | Specific aspect or question to investigate | `"duty hour limits for PGY-1 residents"` |

### Optional

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `{{search_terms}}` | List[String] | Auto-generated | Specific keywords for search | `["80-hour rule", "first-year residents", "supervision"]` |
| `{{source_types}}` | List[String] | `["official docs", "guidelines"]` | Types of sources to consult | `["ACGME PDFs", "institutional policy DB"]` |
| `{{time_period}}` | String | `"current"` | Temporal scope of research | `"July 2023 - June 2024"` or `"historical changes since 2011"` |
| `{{urgency}}` | String | `"standard"` | Priority level | `"urgent"`, `"standard"`, `"background"` |
| `{{output_detail}}` | String | `"standard"` | Depth of output | `"brief"`, `"standard"`, `"comprehensive"` |
| `{{scheduling_context}}` | String | `null` | Specific scheduling scenario | `"Night Float rotation planning"` |

---

## Template

```markdown
[IF urgency == "urgent"]
⚠️ **URGENT POLICY RESEARCH REQUIRED**
Priority: HIGH - Time-sensitive decision pending
[ENDIF]

# Policy Research: {{policy_name}}

## Research Objective

Investigate **{{policy_topic}}** as it relates to medical residency scheduling.

[IF scheduling_context]
**Scheduling Context:** {{scheduling_context}}
[ENDIF]

---

## Search Strategy

### Phase 1: Primary Sources
1. **Official Documentation**
   - ACGME official website (www.acgme.org)
   - Institutional policy database
   - Program-specific guidelines

2. **Search Terms**
[IF search_terms]
   [FOR term IN search_terms]
   - "{{term}}"
   [ENDFOR]
[ELSE]
   - "{{policy_name}}"
   - "{{policy_topic}}"
   - "{{policy_topic}} residency"
   - "{{policy_topic}} ACGME"
[ENDIF]

3. **Source Types to Examine**
[FOR source_type IN source_types]
   - {{source_type}}
[ENDFOR]

### Phase 2: Contextual Sources
- Previous years' versions (for change analysis)
- Institutional interpretations/memos
- Program Director communications
- Published FAQs or clarifications

### Phase 3: Cross-Reference
- Related policies that may interact
- Exception processes
- Enforcement/monitoring mechanisms

---

## Temporal Scope

**Time Period:** {{time_period|current academic year}}

**Historical Context Needed:**
- [ ] Has this policy changed recently?
- [ ] Are there pending changes?
- [ ] What's the effective date of current version?

---

## Research Execution

### Step 1: Document Retrieval
Locate and access the following:
1. Official policy text (verbatim)
2. Any supplementary guidance
3. Institution-specific interpretations

### Step 2: Extract Key Requirements
For each requirement, document:
- **Rule Statement**: [Exact wording]
- **Applicability**: [Who/what it applies to]
- **Measurement**: [How compliance is verified]
- **Exceptions**: [Any documented exemptions]

### Step 3: Identify Scheduling Implications
Analyze how this policy affects:
- **Schedule structure** (block design, rotation length)
- **Assignment constraints** (who can be assigned where/when)
- **Coverage requirements** (minimum staffing levels)
- **Validation rules** (what must be checked)

### Step 4: Flag Ambiguities
Note any:
- Unclear language
- Conflicts with other policies
- Implementation questions
- Areas needing clarification from leadership

---

## Output Format

[IF output_detail == "brief"]
### Summary (2-3 sentences)
[Concise overview of findings]

### Key Findings (bullet points)
- [Most important finding]
- [Second most important finding]
- [Third most important finding]

### Immediate Action Needed
[Yes/No - if yes, specify what]

[ELIF output_detail == "comprehensive"]
### Executive Summary
[3-5 sentence overview]

### Detailed Findings

#### Policy Requirements
| Requirement | Details | Compliance Metric | Exceptions |
|-------------|---------|-------------------|------------|
| [Requirement 1] | [Details] | [How measured] | [Any exemptions] |
| [Requirement 2] | [Details] | [How measured] | [Any exemptions] |

#### Historical Context
[Changes over time, if relevant]

#### Institutional Interpretation
[Local policies or clarifications]

#### Cross-Policy Interactions
[Related policies that may conflict or complement]

### Implications for Scheduling

#### Structural Changes Needed
- [Change 1]
- [Change 2]

#### New Validation Rules
- [Rule 1]
- [Rule 2]

#### Assignment Constraints
- [Constraint 1]
- [Constraint 2]

#### Coverage Requirements
- [Requirement 1]
- [Requirement 2]

### Ambiguities and Open Questions
1. [Question 1]
   - **Why unclear:** [Explanation]
   - **Escalate to:** [PD/APD/Coordinator]
2. [Question 2]
   - **Why unclear:** [Explanation]
   - **Escalate to:** [PD/APD/Coordinator]

### Recommendations

#### Immediate Actions (0-7 days)
- [ ] [Action 1]
- [ ] [Action 2]

#### Short-term Actions (1-4 weeks)
- [ ] [Action 1]
- [ ] [Action 2]

#### Long-term Considerations
- [ ] [Action 1]
- [ ] [Action 2]

### References
- [Primary source with URL/citation]
- [Secondary source with URL/citation]
- [Institutional policy reference]

[ELSE]
<!-- Standard output detail -->
### Summary
[2-3 sentence concise overview of the policy and its main requirements]

### Key Findings
- **Finding 1:** [Most critical requirement or implication]
- **Finding 2:** [Second most important point]
- **Finding 3:** [Additional significant finding]
- **Finding 4:** [If applicable]

### Implications for Scheduling

**Structural Impact:**
- [How this affects block design, rotation structure, or schedule layout]

**Constraint Impact:**
- [New rules that must be enforced in schedule generation]

**Validation Impact:**
- [What must be checked/verified for compliance]

**Coverage Impact:**
- [Minimum staffing or supervision requirements]

### Recommendations

#### Must-Do (Required for Compliance)
- [ ] [Action 1]
- [ ] [Action 2]

#### Should-Do (Best Practices)
- [ ] [Action 1]
- [ ] [Action 2]

#### Consider (Optional Improvements)
- [ ] [Action 1]
- [ ] [Action 2]

### Open Questions
1. [Ambiguity or clarification needed]
2. [If any conflicts with existing practices]

### References
- [Primary source]
- [Secondary sources if used]
[ENDIF]

---

## Follow-Up Actions

### Immediate
[IF urgency == "urgent"]
- [ ] **Escalate findings to:** {{escalation_contact|Program Director}}
- [ ] **Decision needed by:** {{deadline|ASAP}}
- [ ] **Implementation timeline:** {{implementation_timeline|Immediate}}
[ENDIF]

### Standard Process
- [ ] Share findings with scheduler/coordinator
- [ ] Update constraint validation rules (if applicable)
- [ ] Document in policy tracking system
- [ ] Schedule implementation (if changes needed)

### Monitoring
- [ ] Set reminder to re-check policy for updates (quarterly)
- [ ] Monitor ACGME website for clarifications
- [ ] Track compliance metrics

---

## Quality Checklist

Before submitting research output, verify:

- [ ] **Accuracy**: All quotes/requirements verified against primary source
- [ ] **Completeness**: All aspects of {{policy_topic}} covered
- [ ] **Clarity**: Findings understandable to non-experts
- [ ] **Actionability**: Recommendations are specific and implementable
- [ ] **Citation**: All sources properly referenced
- [ ] **Relevance**: Findings directly address {{policy_topic}}
- [ ] **Timeliness**: Policy version is current as of {{time_period}}
- [ ] **Conflicts**: Cross-references checked for contradictions

[IF urgency == "urgent"]
- [ ] **Decision Support**: Provides clear recommendation for pending decision
- [ ] **Risk Assessment**: Identifies compliance risks if action not taken
[ENDIF]

```

---

## Examples

### Example 1: ACGME Duty Hour Research (Standard Detail)

**Instantiation:**
```
policy_name: "ACGME 2023 Common Program Requirements Section VI"
policy_topic: "duty hour limits and exceptions for PGY-2 residents"
search_terms: ["80-hour week", "PGY-2", "duty hours", "averaging period"]
source_types: ["ACGME official PDFs", "institutional policy memos"]
time_period: "July 2023 - June 2024"
urgency: "standard"
output_detail: "standard"
scheduling_context: "Planning February call schedule"
```

**Output:**

```markdown
# Policy Research: ACGME 2023 Common Program Requirements Section VI

## Research Objective
Investigate **duty hour limits and exceptions for PGY-2 residents** as it relates to medical residency scheduling.

**Scheduling Context:** Planning February call schedule

---

### Summary
ACGME 2023 CPR Section VI specifies that PGY-2 residents (and above) are limited to 80 clinical work hours per week, averaged over 4 weeks. Unlike PGY-1 residents, PGY-2+ may work up to 24 hours continuous duty plus up to 4 hours for transitions. No exceptions to the 80-hour limit exist except for rare circumstances with Program Director documentation.

### Key Findings
- **80-Hour Limit (Strict):** Maximum 80 clinical hours/week averaged over any rolling 4-week period. No exceptions without PD documentation of "rare circumstances."
- **24+4 Rule:** PGY-2+ may work 24 hours continuous duty PLUS up to 4 additional hours for transitions/handoffs (total 28 hours max).
- **1-in-7 Rest:** Must have at least one 24-hour period free of clinical duties every 7 days (averaged over 4 weeks).
- **Monitoring Required:** Programs must have systems to monitor compliance and alert when approaching limits.

### Implications for Scheduling

**Structural Impact:**
- Call blocks for PGY-2+ can be 24+4 hours (28 hours max), longer than PGY-1's 16-hour limit
- February schedule must ensure 4-week rolling average never exceeds 80 hours for any resident
- Post-call days must allow for adequate rest before next duty period

**Constraint Impact:**
- Validation rule: For each resident, calculate 4-week rolling average for every day in February
- Constraint: `avg_hours_4week(resident, date) <= 80` for all dates
- Constraint: `continuous_duty(PGY2+) <= 28` hours

**Validation Impact:**
- Must check all 28 possible 4-week windows in February (if 28-day month)
- Alert scheduler if any resident approaches 75 hours in current 4-week window (buffer for safety)

**Coverage Impact:**
- No change to minimum coverage requirements
- PGY-2+ residents can take longer call shifts than PGY-1, potentially reducing number of residents needed per call cycle

### Recommendations

#### Must-Do (Required for Compliance)
- [ ] Implement 4-week rolling average validation in schedule generation algorithm
- [ ] Add pre-assignment check: "Will this assignment push resident over 80hr average?"
- [ ] Configure alerts when residents reach 75 hours in any 4-week window

#### Should-Do (Best Practices)
- [ ] Target 70-75 hour average for sustainable workload (not maximum 80)
- [ ] Build in buffer for unexpected coverage needs
- [ ] Track trends: Are certain rotations consistently pushing limits?

#### Consider (Optional Improvements)
- [ ] Create dashboard showing each resident's current 4-week average
- [ ] Weekly report to PD: "Residents within 5 hours of limit"
- [ ] Predictive modeling: "If we schedule X this week, what's the impact on next week's flexibility?"

### Open Questions
1. **Rare Circumstances Exception:** What qualifies? Need clarification from PD on when/how to invoke.
2. **Moonlighting Counting:** Does external moonlighting count toward 80-hour limit? (Answer: Yes per ACGME, need to track)

### References
- ACGME Common Program Requirements (Residency), Section VI, Effective July 1, 2023
  https://www.acgme.org/globalassets/pfassets/programrequirements/cprresidency_2023.pdf
- Institutional Policy Memo: "Duty Hour Monitoring Process" (2023-08-15)
```

---

### Example 2: Night Float Policy (Urgent, Comprehensive)

**Instantiation:**
```
policy_name: "Institutional Night Float Guidelines"
policy_topic: "maximum consecutive nights and rest requirements"
search_terms: ["night float", "consecutive nights", "circadian disruption"]
source_types: ["institutional policy", "ACGME CPR", "resident wellness guidelines"]
time_period: "current"
urgency: "urgent"
output_detail: "comprehensive"
scheduling_context: "Resident raised concern about 10 consecutive nights scheduled"
escalation_contact: "Program Director"
deadline: "48 hours"
implementation_timeline: "Must revise schedule before next rotation"
```

**Output:**

```markdown
⚠️ **URGENT POLICY RESEARCH REQUIRED**
Priority: HIGH - Time-sensitive decision pending

# Policy Research: Institutional Night Float Guidelines

## Research Objective
Investigate **maximum consecutive nights and rest requirements** as it relates to medical residency scheduling.

**Scheduling Context:** Resident raised concern about 10 consecutive nights scheduled

---

### Executive Summary
Current institutional policy (effective 2023) limits Night Float rotations to maximum 6 consecutive nights, based on circadian disruption research and ACGME wellness requirements. The scheduled 10 consecutive nights **violates institutional policy** and should be revised immediately. ACGME does not specify a hard limit on consecutive nights but requires programs to minimize circadian disruption and ensure adequate rest. Recommend splitting into two 5-night blocks with 48-hour break between, or transitioning to different rotation type after night 6.

### Detailed Findings

#### Policy Requirements
| Requirement | Details | Compliance Metric | Exceptions |
|-------------|---------|-------------------|------------|
| Max 6 consecutive nights | Institutional policy (2023-04-01) | Count consecutive night shifts (19:00-07:00) | PD approval for "critical coverage need" with wellness mitigation |
| 48-hour rest after 6 nights | Institutional guideline (recommended) | Calendar check: 48 hours before next shift | Emergency situations only |
| Circadian wellness check | ACGME CPR VI.F (wellness requirement) | PD/wellness committee review | None |
| Max 4 weeks on Night Float | ACGME recommendation | Block length tracking | None |

#### Historical Context
- **2019:** No limit on consecutive nights (old policy)
- **2021:** Wellness committee recommended 7-night max after resident burnout incidents
- **2023-04:** Revised to 6-night max based on sleep medicine consultation
- **No pending changes** as of Dec 2025

#### Institutional Interpretation
From Program Director memo (2023-04-15):
> "While ACGME does not mandate a specific consecutive night limit, our institution has adopted a 6-night maximum to prioritize resident wellness and align with circadian rhythm research. Any schedule exceeding 6 consecutive nights requires PD pre-approval and documented mitigation plan (e.g., reduced subsequent workload, wellness check-in)."

#### Cross-Policy Interactions
- **Conflicts with ACGME:** None (institutional policy is stricter, which is allowed)
- **Complements duty hours:** Night shifts count toward 80-hour weekly limit
- **Interacts with rest requirements:** Still must have 1-in-7 days off
- **Affects moonlighting:** Night Float residents prohibited from external moonlighting during rotation

### Implications for Scheduling

#### Structural Changes Needed
- **Immediate:** Revise current schedule to cap at 6 consecutive nights
- **Future:** Update scheduling algorithm to enforce 6-night max constraint

#### New Validation Rules
```python
# Constraint: No more than 6 consecutive night shifts
def validate_consecutive_nights(resident, schedule):
    consecutive = 0
    for shift in schedule:
        if shift.type == "night" and shift.start_time >= 19:00:
            consecutive += 1
            if consecutive > 6:
                return ValidationError(f"Consecutive night limit exceeded: {consecutive}")
        else:
            consecutive = 0  # Reset on non-night shift
    return Valid
```

#### Assignment Constraints
- Block type "Night Float" duration <= 6 nights without interruption
- If Night Float needed for >6 nights: Insert 48-hour break, then resume
- Alternatively: Rotate different resident in after night 6

#### Coverage Requirements
- No change to minimum overnight coverage (still need X residents per night)
- May need additional residents in pool to maintain coverage with 6-night limit

### Ambiguities and Open Questions
1. **"Critical coverage need" exception:**
   - **Why unclear:** Policy allows PD exception for "critical coverage" but doesn't define what qualifies
   - **Escalate to:** Program Director - Does current situation qualify?

2. **Definition of "night shift":**
   - **Why unclear:** Policy says "night shifts" but doesn't specify exact hours
   - **Assumption:** 19:00-07:00 based on institutional scheduling practice
   - **Escalate to:** None (documented in memos, confirmed acceptable)

3. **What counts as "break" in consecutive nights:**
   - **Why unclear:** If resident has 12-hour day shift between two night shifts, does that break the consecutive count?
   - **Escalate to:** Wellness Committee Chair
   - **Interim interpretation:** Only complete calendar days off break the count (conservative approach)

### Recommendations

#### Immediate Actions (0-7 days)
- [ ] **URGENT:** Notify resident(s) currently scheduled for 10 consecutive nights
- [ ] **URGENT:** Revise schedule to one of these options:
  - Option A: 6 nights, 48-hour break, 4 nights
  - Option B: 5 nights, 48-hour break, 5 nights
  - Option C: 6 nights, switch to different rotation type
- [ ] Document incident and policy violation in QI tracking
- [ ] Send apology/explanation to affected resident

#### Short-term Actions (1-4 weeks)
- [ ] Update scheduling algorithm with 6-night max constraint
- [ ] Add validation step: "Check all Night Float blocks for consecutive night count"
- [ ] Create alert in scheduler UI: "Warning: This assignment would create 7+ consecutive nights"
- [ ] Review all future schedules (next 3 months) for similar violations

#### Long-term Considerations
- [ ] Policy awareness training for schedulers and chief residents
- [ ] Quarterly audit: "Any Night Float blocks >6 nights in last 90 days?"
- [ ] Consider adding constraint to MCP scheduling tools
- [ ] Wellness committee review: Is 6 nights still appropriate? (annual)

### References
- Institutional Night Float Policy (v2.0, effective 2023-04-01)
  Internal Policy Database, Doc ID: RES-NF-001
- ACGME Common Program Requirements, Section VI.F (Professionalism and Well-Being)
  https://www.acgme.org/globalassets/pfassets/programrequirements/cprresidency_2023.pdf, pp. 58-60
- Program Director Memo: "Night Float Scheduling Guidance" (2023-04-15)
  Internal email archive
- Sleep Medicine Consultation Report: "Optimal Night Shift Patterns for Resident Wellness" (2023-02)
  Institutional research, filed with Wellness Committee

---

## Follow-Up Actions

### Immediate
- [ ] **Escalate findings to:** Program Director (within 2 hours)
- [ ] **Decision needed by:** 48 hours (before resident starts affected rotation)
- [ ] **Implementation timeline:** Immediate (revise schedule this week)

### Standard Process
- [ ] Share findings with scheduler/coordinator ✅ (include in urgent communication)
- [ ] Update constraint validation rules (within 1 week)
- [ ] Document in policy tracking system (after resolution)
- [ ] Schedule implementation (ASAP - see immediate actions)

### Monitoring
- [ ] Set reminder to re-check policy for updates (quarterly)
- [ ] Monitor ACGME website for clarifications (annual)
- [ ] Track compliance metrics: "Night Float blocks exceeding 6 nights = 0 per quarter"
```

---

## Validation Checklist

Before submitting research output, verify:

- [ ] **Accuracy**: All quotes/requirements verified against primary source
- [ ] **Completeness**: All aspects of {{policy_topic}} covered
- [ ] **Clarity**: Findings understandable to non-experts
- [ ] **Actionability**: Recommendations are specific and implementable
- [ ] **Citation**: All sources properly referenced
- [ ] **Relevance**: Findings directly address the research objective
- [ ] **Timeliness**: Policy version is current
- [ ] **Conflicts**: Cross-references checked for contradictions
- [IF urgency == "urgent"] **Decision Support**: Provides clear recommendation
- [IF urgency == "urgent"] **Risk Assessment**: Compliance risks identified

---

## Notes

### Adaptation Guidelines

This template is designed for regulatory and institutional policy research. For other research types:
- **Clinical guidelines:** Add sections for evidence grading, clinical applicability
- **Best practices:** Include section for comparative analysis (what other programs do)
- **Vendor/tool research:** Add cost-benefit analysis section

### Integration with Other Templates

Typical workflow:
1. **RESEARCH_POLICY** → Gather requirements
2. **CONSTRAINT_ANALYSIS** → Identify conflicts with existing rules
3. **SCHEDULE_GENERATION** → Implement findings in next schedule

### Version History

- **v1.0.0** (2025-12-26): Initial template creation
  - Based on 15+ policy research sessions
  - Includes ACGME, institutional, and clinical guideline patterns
  - Added urgent research variant for time-sensitive decisions
