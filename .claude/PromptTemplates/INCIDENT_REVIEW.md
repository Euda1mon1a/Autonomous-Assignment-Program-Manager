***REMOVED*** INCIDENT_REVIEW - Prompt Template

> **Purpose:** Conduct systematic post-incident analysis for scheduling failures, coverage gaps, or compliance violations
> **Complexity:** Medium
> **Typical Duration:** 10-20 minutes
> **Prerequisites:** Incident data (timeline, affected parties, system state), access to relevant logs/schedules
> **Version:** 1.0.0
> **Last Updated:** 2025-12-26

---

***REMOVED******REMOVED*** Input Parameters

***REMOVED******REMOVED******REMOVED*** Required

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `{{incident_id}}` | String | Unique incident identifier | `"INC-2024-001"` |
| `{{incident_type}}` | String | Category of incident | `"coverage_gap"`, `"compliance_violation"`, `"system_failure"`, `"safety_event"` |
| `{{incident_date}}` | String | When incident occurred | `"2024-01-15"` |
| `{{description}}` | String | Brief incident summary | `"Double-booking resulted in no anesthesia coverage for OR"` |

***REMOVED******REMOVED******REMOVED*** Optional

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `{{severity}}` | String | `"medium"` | Impact level | `"low"`, `"medium"`, `"high"`, `"critical"` |
| `{{affected_parties}}` | List[String] | `[]` | People/systems impacted | `["PGY2-01", "OR schedule", "attending Smith"]` |
| `{{timeline_events}}` | List[Dict] | `[]` | Known sequence of events | `[{time: "06:00", event: "Resident called in sick"}]` |
| `{{contributing_factors}}` | List[String] | `[]` | Known contributing issues | `["No backup coverage plan", "Late notification"]` |
| `{{remediation_taken}}` | List[String] | `[]` | Immediate fixes applied | `["Called moonlighter", "Cancelled elective cases"]` |
| `{{stakeholders}}` | List[String] | `["Program Director"]` | Who needs this report | `["PD", "Chief Resident", "QI Committee"]` |
| `{{root_cause_depth}}` | String | `"standard"` | How deep to analyze | `"quick"`, `"standard"`, `"deep"` (5-whys iterations) |
| `{{include_prevention}}` | Boolean | `true` | Generate prevention plan | `true`/`false` |

---

***REMOVED******REMOVED*** Template

```markdown
***REMOVED*** Incident Review: {{incident_id}}

> **Type:** {{incident_type}}
> **Date:** {{incident_date}}
> **Severity:** {{severity|MEDIUM}}
> **Status:** Under Review
> **Reviewers:** {{stakeholders|join(", ")}}

---

***REMOVED******REMOVED*** Executive Summary

**What Happened:**
{{description}}

[IF severity == "critical"]
🚨 **CRITICAL INCIDENT**: This event posed immediate risk to patient safety or residency program accreditation.
[ENDIF]

[IF severity == "high"]
⚠️ **HIGH SEVERITY**: This event had significant operational impact and/or compliance implications.
[ENDIF]

**Immediate Impact:**
[IF affected_parties]
- **People affected:** {{affected_parties|join(", ")}}
[ENDIF]
- **Operations affected:** [Specify clinical services, schedules, or processes impacted]
- **Duration:** [How long did disruption last?]

**Resolution:**
[IF remediation_taken]
[FOR action IN remediation_taken]
- {{action}}
[ENDFOR]
[ELSE]
[Document how the incident was resolved]
[ENDIF]

**Preview of Findings:**
- **Root cause:** [One sentence summary - to be detailed below]
- **Preventable?** [Yes/No + brief explanation]

---

***REMOVED******REMOVED*** Incident Timeline

Reconstruct the complete sequence of events:

***REMOVED******REMOVED******REMOVED*** Timeline Reconstruction Format

| Time | Event | Actor/System | Impact | Notes |
|------|-------|--------------|--------|-------|
[IF timeline_events]
[FOR event IN timeline_events]
| {{event.time}} | {{event.description}} | {{event.actor|"System"}} | {{event.impact}} | {{event.notes|""}} |
[ENDFOR]
[ELSE]
| [T-X hours] | [Event description] | [Who/what caused this] | [What changed] | [Additional context] |
| ... | ... | ... | ... | ... |
[ENDIF]

***REMOVED******REMOVED******REMOVED*** Key Milestones

Identify critical decision points and inflection points:

1. **Initiating Event** (T=0):
   - What: [First event in causal chain]
   - When: [Timestamp]
   - Why significant: [This started the sequence]

2. **Point of No Return**:
   - What: [Event after which incident became inevitable]
   - When: [Timestamp]
   - Why significant: [Last chance to prevent was missed]

3. **Detection**:
   - What: [When incident was first noticed]
   - When: [Timestamp]
   - Delay from initiation: [Time elapsed]
   - Why significant: [Earlier detection could have helped]

4. **Response Initiated**:
   - What: [First remediation action]
   - When: [Timestamp]
   - Delay from detection: [Time elapsed]

5. **Resolution**:
   - What: [When normal operations restored]
   - When: [Timestamp]
   - Total incident duration: [Time from initiation to resolution]

---

***REMOVED******REMOVED*** Root Cause Analysis

[IF root_cause_depth == "quick"]
***REMOVED******REMOVED******REMOVED*** Quick Analysis (Single-Why)

**Direct Cause:**
[What immediately caused the incident?]

**System Factor:**
[What system weakness allowed this?]

**Recommendation:**
[One primary fix]

[ELIF root_cause_depth == "deep"]
***REMOVED******REMOVED******REMOVED*** Deep Analysis (5-Whys Method)

**Problem Statement:**
{{description}}

**Why ***REMOVED***1:** Why did this happen?
→ Answer: [First-level cause]

**Why ***REMOVED***2:** Why did [Answer ***REMOVED***1] occur?
→ Answer: [Second-level cause]

**Why ***REMOVED***3:** Why did [Answer ***REMOVED***2] occur?
→ Answer: [Third-level cause]

**Why ***REMOVED***4:** Why did [Answer ***REMOVED***3] occur?
→ Answer: [Fourth-level cause]

**Why ***REMOVED***5:** Why did [Answer ***REMOVED***4] occur?
→ Answer: [Root cause - usually process/system level]

**True Root Cause:**
[Synthesis of the 5-whys analysis - what is the fundamental system weakness?]

[ELSE]
***REMOVED******REMOVED******REMOVED*** Standard Analysis (3-Whys)

**Problem Statement:**
{{description}}

**Why ***REMOVED***1:** Why did this incident occur?
→ **Answer:** [Direct/immediate cause]

**Why ***REMOVED***2:** Why was the system vulnerable to this cause?
→ **Answer:** [Contributing factor - process/policy gap]

**Why ***REMOVED***3:** Why didn't existing safeguards prevent this?
→ **Answer:** [System-level weakness]

**Root Cause Conclusion:**
[Summary: What is the fundamental issue that needs addressing?]

[ENDIF]

---

***REMOVED******REMOVED*** Contributing Factors

***REMOVED******REMOVED******REMOVED*** Technical Factors
[IF contributing_factors]
[FOR factor IN contributing_factors WHERE factor.category == "technical"]
- **{{factor.name}}**: {{factor.description}}
[ENDFOR]
[ELSE]
Analyze technical/system issues:
- Was there a software bug or system limitation?
- Did data integrity issues contribute?
- Were integrations working correctly?
- Did validation checks fail?
[ENDIF]

***REMOVED******REMOVED******REMOVED*** Process Factors
[Analyze procedural issues:]
- Were standard operating procedures followed?
- Were procedures adequate for this scenario?
- Were there gaps in the workflow?
- Was training/documentation sufficient?

***REMOVED******REMOVED******REMOVED*** Human Factors
[Analyze human decisions/actions:]
- Were cognitive biases at play? (e.g., confirmation bias, recency bias)
- Was workload/fatigue a factor?
- Were communication channels clear?
- Was adequate supervision present?

***REMOVED******REMOVED******REMOVED*** Organizational Factors
[Analyze systemic/cultural issues:]
- Did time pressure influence decisions?
- Were resources adequate?
- Was there cultural reluctance to escalate?
- Do incentives align with desired behavior?

***REMOVED******REMOVED******REMOVED*** External Factors
[Analyze outside influences:]
- Unexpected events (illness, weather, etc.)
- Changes in external requirements
- Vendor/third-party issues

---

***REMOVED******REMOVED*** Impact Assessment

***REMOVED******REMOVED******REMOVED*** Immediate Impact

**Patient Care:**
[IF incident_type == "coverage_gap" OR incident_type == "safety_event"]
- Number of patients affected: [Count]
- Type of impact: [Delayed care, cancelled procedures, etc.]
- Clinical risk level: [Low/Medium/High]
- Actual harm: [None / Near miss / Adverse event]
[ELSE]
- Not directly patient-facing OR No patient impact
[ENDIF]

**Resident Education:**
- Residents affected: {{affected_parties|filter("resident")|join(", ")}}
- Educational impact: [Missed rotations, overwork, etc.]
- ACGME compliance risk: [Yes/No - specify rule]

**Operational:**
- Services disrupted: [List affected clinical areas]
- Duration of disruption: [Hours/days]
- Workaround burden: [Extra shifts, reassignments, etc.]

**Financial:**
- Estimated cost: [If quantifiable]
- Revenue impact: [Cancelled cases, etc.]

***REMOVED******REMOVED******REMOVED*** Downstream/Secondary Impact

**Morale:**
- Resident/faculty satisfaction affected?
- Trust in scheduling system affected?
- Burnout risk increased?

**Compliance:**
- ACGME violations: [Yes/No - specify which rules]
- Institutional policy violations: [Yes/No - specify]
- Reportable to oversight bodies: [Yes/No]

**Systemic:**
- Does this reveal a pattern? [Check for similar past incidents]
- Could this happen elsewhere in the system?
- What other scenarios might be vulnerable?

---

***REMOVED******REMOVED*** Prevention Measures

[IF include_prevention]

***REMOVED******REMOVED******REMOVED*** Defense in Depth Strategy

Apply multiple layers of protection to prevent recurrence:

***REMOVED******REMOVED******REMOVED******REMOVED*** Layer 1: Elimination (Remove the hazard)
**Goal:** Make the incident impossible

[FOR recommendation IN prevention_recommendations WHERE recommendation.layer == "elimination"]
- {{recommendation.action}}
  - **Implementation:** {{recommendation.how}}
  - **Timeline:** {{recommendation.when}}
  - **Owner:** {{recommendation.owner}}
[ENDFOR]

Example:
- Remove manual scheduling step that caused error
- Automate validation that was previously manual

***REMOVED******REMOVED******REMOVED******REMOVED*** Layer 2: Substitution (Replace with safer alternative)
**Goal:** Reduce likelihood by changing approach

[FOR recommendation IN prevention_recommendations WHERE recommendation.layer == "substitution"]
- {{recommendation.action}}
  - **Implementation:** {{recommendation.how}}
  - **Timeline:** {{recommendation.when}}
  - **Owner:** {{recommendation.owner}}
[ENDFOR]

Example:
- Replace paper-based process with digital workflow
- Use automated alerts instead of relying on memory

***REMOVED******REMOVED******REMOVED******REMOVED*** Layer 3: Engineering Controls (Hard barriers)
**Goal:** System prevents error automatically

[FOR recommendation IN prevention_recommendations WHERE recommendation.layer == "engineering"]
- {{recommendation.action}}
  - **Implementation:** {{recommendation.how}}
  - **Timeline:** {{recommendation.when}}
  - **Owner:** {{recommendation.owner}}
[ENDFOR]

Example:
- Add validation rule to scheduling system
- Implement database constraint to prevent double-booking

***REMOVED******REMOVED******REMOVED******REMOVED*** Layer 4: Administrative Controls (Policies/procedures)
**Goal:** Guide behavior through rules

[FOR recommendation IN prevention_recommendations WHERE recommendation.layer == "administrative"]
- {{recommendation.action}}
  - **Implementation:** {{recommendation.how}}
  - **Timeline:** {{recommendation.when}}
  - **Owner:** {{recommendation.owner}}
[ENDFOR]

Example:
- Update SOP for coverage escalation
- Require sign-off for schedule changes

***REMOVED******REMOVED******REMOVED******REMOVED*** Layer 5: PPE/Human Vigilance (Weakest layer)
**Goal:** Rely on people to catch issues

⚠️ **Warning:** This layer alone is insufficient. Always combine with higher layers.

[FOR recommendation IN prevention_recommendations WHERE recommendation.layer == "vigilance"]
- {{recommendation.action}}
  - **Implementation:** {{recommendation.how}}
  - **Timeline:** {{recommendation.when}}
  - **Owner:** {{recommendation.owner}}
[ENDFOR]

Example:
- Train schedulers to double-check coverage
- Remind residents to verify schedules weekly

---

***REMOVED******REMOVED******REMOVED*** Recommended Preventive Actions

***REMOVED******REMOVED******REMOVED******REMOVED*** Immediate (0-7 days)
[These should be quick wins to prevent immediate recurrence]

- [ ] [Action 1]
  - **Purpose:** [Why this helps]
  - **Owner:** [Who implements]
  - **Effort:** [Hours/days]

- [ ] [Action 2]
  - **Purpose:** [Why this helps]
  - **Owner:** [Who implements]
  - **Effort:** [Hours/days]

***REMOVED******REMOVED******REMOVED******REMOVED*** Short-term (1-4 weeks)
[Process improvements, policy updates]

- [ ] [Action 1]
  - **Purpose:** [Why this helps]
  - **Owner:** [Who implements]
  - **Effort:** [Days/weeks]

- [ ] [Action 2]
  - **Purpose:** [Why this helps]
  - **Owner:** [Who implements]
  - **Effort:** [Days/weeks]

***REMOVED******REMOVED******REMOVED******REMOVED*** Long-term (1-6 months)
[System redesign, major process changes]

- [ ] [Action 1]
  - **Purpose:** [Why this helps]
  - **Owner:** [Who implements]
  - **Effort:** [Weeks/months]

- [ ] [Action 2]
  - **Purpose:** [Why this helps]
  - **Owner:** [Who implements]
  - **Effort:** [Weeks/months]

---

***REMOVED******REMOVED******REMOVED*** Early Warning System

**Detection Improvements:**
How can we detect similar issues earlier in the future?

- **Monitoring:** [What metrics/logs to watch]
- **Alerts:** [When to trigger notifications]
- **Thresholds:** [What values indicate problems]

**Example:**
- Monitor "unfilled shift" count daily
- Alert if >0 unfilled shifts within 72 hours of shift start
- Escalate if >2 unfilled shifts in same week

[ENDIF]

---

***REMOVED******REMOVED*** Lessons Learned

***REMOVED******REMOVED******REMOVED*** What Worked Well
[Identify positive aspects - effective responses, resilient processes, good decisions]

- [Positive finding 1]
- [Positive finding 2]

***REMOVED******REMOVED******REMOVED*** What Didn't Work
[Identify failures - ineffective processes, poor decisions, gaps]

- [Failure 1]
- [Failure 2]

***REMOVED******REMOVED******REMOVED*** Surprises
[Unexpected findings - things that behaved differently than expected]

- [Surprise 1]
- [Surprise 2]

***REMOVED******REMOVED******REMOVED*** Transferable Insights
[Knowledge applicable to other scenarios or systems]

- **Insight:** [Lesson learned]
  - **Applies to:** [Other scenarios/systems]
  - **Action:** [What to do differently]

---

***REMOVED******REMOVED*** Action Plan

***REMOVED******REMOVED******REMOVED*** Summary Table

| Action | Priority | Owner | Deadline | Status | Verification |
|--------|----------|-------|----------|--------|--------------|
| [Action 1] | High | [Name] | [Date] | Not Started | [How to verify completed] |
| [Action 2] | High | [Name] | [Date] | Not Started | [How to verify completed] |
| [Action 3] | Medium | [Name] | [Date] | Not Started | [How to verify completed] |

***REMOVED******REMOVED******REMOVED*** Follow-Up Review

- **Review Date:** [30/60/90 days from incident]
- **Participants:** {{stakeholders}}
- **Agenda:**
  - Verify all actions completed
  - Assess effectiveness of changes
  - Check for similar incidents since implementation
  - Identify any new issues introduced by changes

---

***REMOVED******REMOVED*** Stakeholder Communication

***REMOVED******REMOVED******REMOVED*** Internal Communication
[How to share findings with team]

**Audience:** [Program Director, Chief Residents, Schedulers, etc.]
**Format:** [Email summary, presentation, written report]
**Key Messages:**
1. [What happened]
2. [Root cause]
3. [How we're preventing recurrence]

***REMOVED******REMOVED******REMOVED*** External Communication
[If incident requires reporting to external bodies]

[IF severity == "critical" OR incident_type == "safety_event"]
⚠️ **External Reporting Required:**
- **Entity:** [ACGME, institutional patient safety committee, etc.]
- **Deadline:** [Reporting requirement timeline]
- **Contact:** [Who submits report]
[ENDIF]

---

***REMOVED******REMOVED*** Attachments/References

***REMOVED******REMOVED******REMOVED*** Supporting Documentation
- [ ] Incident timeline (detailed)
- [ ] System logs/screenshots
- [ ] Schedule snapshots (before/after)
- [ ] Communication records (emails, texts)
- [ ] Related policy documents

***REMOVED******REMOVED******REMOVED*** Related Incidents
[Link to similar past incidents for pattern analysis]

- [INC-YYYY-XXX]: [Brief description] - [Similar how?]

---

```

---

***REMOVED******REMOVED*** Examples

***REMOVED******REMOVED******REMOVED*** Example 1: Coverage Gap Incident (Standard Analysis)

**Instantiation:**
```
incident_id: "INC-2024-015"
incident_type: "coverage_gap"
incident_date: "2024-01-15"
description: "No anesthesia resident assigned to OR for morning cases due to scheduling system error"
severity: "high"
affected_parties: ["PGY2-03", "OR scheduler", "Attending Johnson", "3 surgical patients"]
timeline_events: [
  {time: "06:00", event: "PGY2-03 called in sick", actor: "PGY2-03", impact: "Lost 1 anesthesia resident"},
  {time: "06:30", event: "Backup coverage not automatically assigned", actor: "Scheduling system", impact: "Gap not filled"},
  {time: "07:00", event: "OR team realized no anesthesia coverage", actor: "OR nurse", impact: "First case delayed"},
  {time: "07:15", event: "Chief resident notified", actor: "OR nurse", impact: "Escalation initiated"},
  {time: "07:30", event: "Moonlighter called", actor: "Chief resident", impact: "Coverage arranged"},
  {time: "08:30", event: "Moonlighter arrived, cases resumed", actor: "Moonlighter", impact: "Operations restored"}
]
contributing_factors: [
  {name: "No automated backup assignment", category: "technical"},
  {name: "Call-in occurred too late for normal escalation", category: "timing"},
  {name: "Chief resident was off-site, response delayed", category: "human"}
]
remediation_taken: ["Called moonlighter", "Delayed first case 90 minutes", "Cancelled one elective case"]
stakeholders: ["Program Director", "Chief Resident", "QI Committee"]
root_cause_depth: "standard"
include_prevention: true
```

**Output:** [Would produce detailed incident report with timeline, 3-whys analysis, and prevention plan]

---

***REMOVED******REMOVED******REMOVED*** Example 2: ACGME Compliance Violation (Deep Analysis)

**Instantiation:**
```
incident_id: "INC-2024-023"
incident_type: "compliance_violation"
incident_date: "2024-02-10"
description: "PGY1-02 worked 86 hours in one week, exceeding 80-hour limit"
severity: "critical"
affected_parties: ["PGY1-02"]
timeline_events: [
  {time: "2024-02-04", event: "Week started with standard assignments", actor: "Scheduler", impact: "Baseline 72 hours planned"},
  {time: "2024-02-07", event: "PGY1-01 went on emergency medical leave", actor: "PGY1-01", impact: "Lost coverage"},
  {time: "2024-02-07", event: "PGY1-02 volunteered to cover shifts", actor: "Chief Resident", impact: "Added 14 hours"},
  {time: "2024-02-08", event: "No validation check before assigning extra shifts", actor: "Scheduling system", impact: "Violation not detected"},
  {time: "2024-02-10", event: "Weekly hours report flagged violation", actor: "Automated report", impact: "Issue discovered"},
  {time: "2024-02-11", event: "PD notified ACGME of violation", actor: "Program Director", impact: "Formal reporting"}
]
contributing_factors: [
  {name: "Real-time hours validation not enabled", category: "technical"},
  {name: "Pressure to maintain coverage overrode compliance", category: "organizational"},
  {name: "Chief Resident not trained on duty hour limits for emergencies", category: "process"}
]
remediation_taken: [
  "Gave PGY1-02 compensatory time off",
  "Reported to ACGME",
  "Enabled real-time validation in scheduling system"
]
stakeholders: ["Program Director", "DIO", "ACGME", "Resident Wellness Committee"]
root_cause_depth: "deep"
include_prevention: true
```

**Output:**
```markdown
***REMOVED*** Incident Review: INC-2024-023

> **Type:** compliance_violation
> **Date:** 2024-02-10
> **Severity:** CRITICAL
> **Status:** Under Review
> **Reviewers:** Program Director, DIO, ACGME, Resident Wellness Committee

🚨 **CRITICAL INCIDENT**: This event posed immediate risk to patient safety or residency program accreditation.

---

***REMOVED******REMOVED*** Executive Summary

**What Happened:**
PGY1-02 worked 86 hours in one week, exceeding the ACGME 80-hour limit by 6 hours due to emergency coverage needs not being validated against duty hour constraints.

**Immediate Impact:**
- **People affected:** PGY1-02
- **Operations affected:** ACGME compliance status, resident well-being
- **Duration:** One week (2024-02-04 to 2024-02-10)

**Resolution:**
- Gave PGY1-02 compensatory time off
- Reported to ACGME
- Enabled real-time validation in scheduling system

**Preview of Findings:**
- **Root cause:** Organizational pressure to maintain coverage combined with lack of technical safeguards created environment where compliance could be overridden
- **Preventable?** Yes - real-time validation would have prevented the assignment

---

[... timeline section ...]

---

***REMOVED******REMOVED*** Root Cause Analysis

***REMOVED******REMOVED******REMOVED*** Deep Analysis (5-Whys Method)

**Problem Statement:**
PGY1-02 worked 86 hours in one week, exceeding 80-hour limit

**Why ***REMOVED***1:** Why did this happen?
→ **Answer:** Chief Resident assigned PGY1-02 14 additional hours of coverage without checking duty hour impact

**Why ***REMOVED***2:** Why did Chief Resident assign without checking?
→ **Answer:** Scheduling system did not prevent or warn about the assignment, and manual calculation was not performed under time pressure

**Why ***REMOVED***3:** Why did the system not prevent the assignment?
→ **Answer:** Real-time duty hour validation was disabled (only weekly retrospective reporting was active)

**Why ***REMOVED***4:** Why was real-time validation disabled?
→ **Answer:** System performance concerns led to disabling real-time checks; only batch processing was used

**Why ***REMOVED***5:** Why was coverage prioritized over compliance checking?
→ **Answer:** Organizational culture emphasized "coverage at all costs" and lacked clear escalation procedures for N-1 situations that balanced both coverage and compliance

**True Root Cause:**
Organizational culture prioritized operational coverage over compliance monitoring, combined with deliberate removal of technical safeguards due to performance concerns. No compensating procedural controls (e.g., manual validation checklists) were implemented when technical controls were disabled.

---

***REMOVED******REMOVED*** Prevention Measures

***REMOVED******REMOVED******REMOVED*** Defense in Depth Strategy

***REMOVED******REMOVED******REMOVED******REMOVED*** Layer 1: Elimination
- **Action:** Implement N-1 contingency staffing pool
  - **Implementation:** Hire 2 swing residents who can flex into any rotation
  - **Timeline:** 6 months (requires budget approval)
  - **Owner:** Program Director

***REMOVED******REMOVED******REMOVED******REMOVED*** Layer 2: Substitution
- **Action:** Replace manual emergency coverage assignments with automated backup assignment algorithm
  - **Implementation:** When resident goes on leave, system auto-assigns backup from pool based on current hours
  - **Timeline:** 2 months (requires development)
  - **Owner:** IT + Chief Resident

***REMOVED******REMOVED******REMOVED******REMOVED*** Layer 3: Engineering Controls
- **Action:** Re-enable real-time duty hour validation with performance optimization
  - **Implementation:** Optimize database queries, add caching layer, test under load
  - **Timeline:** 2 weeks
  - **Owner:** IT Team
  - **Status:** ✅ COMPLETED 2024-02-11

- **Action:** Add hard block in system preventing assignment if it would violate duty hours
  - **Implementation:** Pre-assignment validation with clear error message and suggested alternatives
  - **Timeline:** 2 weeks
  - **Owner:** IT Team

***REMOVED******REMOVED******REMOVED******REMOVED*** Layer 4: Administrative Controls
- **Action:** Create SOP for emergency coverage that includes duty hour check as required step
  - **Implementation:** Document procedure, train chief residents, add to orientation
  - **Timeline:** 1 week
  - **Owner:** Chief Resident + PD

- **Action:** Establish "compliance override" process requiring PD approval
  - **Implementation:** If emergency truly requires violation, PD must approve in writing with mitigation plan
  - **Timeline:** 1 week
  - **Owner:** Program Director

***REMOVED******REMOVED******REMOVED******REMOVED*** Layer 5: PPE/Human Vigilance
- **Action:** Train all chief residents on duty hour limits and consequences
  - **Implementation:** Quarterly training session + annual refresher
  - **Timeline:** Ongoing
  - **Owner:** Program Director

⚠️ **Note:** Relying solely on human vigilance proved insufficient. All upper layers must be in place.

---

***REMOVED******REMOVED******REMOVED*** Early Warning System

**Detection Improvements:**
- **Monitoring:** Track each resident's current week hours in real-time dashboard
- **Alerts:**
  - Yellow alert at 70 hours
  - Orange alert at 75 hours
  - Red alert if any assignment would exceed 80 hours
- **Thresholds:**
  - Send PD daily summary if any resident >70 hours
  - Auto-escalate if resident assigned >80 hours (should be impossible with new controls)

---

***REMOVED******REMOVED*** Lessons Learned

***REMOVED******REMOVED******REMOVED*** What Worked Well
- **Detection:** Automated weekly report successfully identified violation within 24 hours
- **Response:** PD immediately reported to ACGME (transparency)
- **Remediation:** Resident given compensatory time off quickly

***REMOVED******REMOVED******REMOVED*** What Didn't Work
- **Prevention:** Disabling real-time validation created vulnerability
- **Culture:** "Coverage at all costs" mentality overrode compliance concerns
- **Training:** Chief Resident lacked clear guidance on N-1 emergency procedures

***REMOVED******REMOVED******REMOVED*** Surprises
- **Performance concerns were overstated:** Re-enabling validation with optimization had minimal performance impact (<50ms added latency)
- **No existing SOP for emergencies:** Despite years of operation, no documented procedure existed

***REMOVED******REMOVED******REMOVED*** Transferable Insights
- **Insight:** Disabling safety checks for performance reasons requires compensating controls
  - **Applies to:** Any technical safeguard (validation, rate limiting, error checking)
  - **Action:** Always implement procedural backup if technical control removed

- **Insight:** Cultural values ("coverage first") can override written policies
  - **Applies to:** All high-pressure decision scenarios
  - **Action:** Make compliance checks automatic/enforced, not discretionary

[... rest of report ...]
```

---

***REMOVED******REMOVED*** Validation Checklist

Before finalizing incident review:

- [ ] **Timeline complete** (from initiating event to resolution)
- [ ] **Root cause identified** (not just surface-level symptoms)
- [ ] **Contributing factors analyzed** (technical, process, human, organizational)
- [ ] **Impact assessed** (immediate and downstream effects)
- [ ] **Prevention measures specific and actionable** (not vague recommendations)
- [ ] **Ownership assigned** (clear DRI for each action)
- [ ] **Defense in depth applied** (multiple layers of protection)
- [ ] **Lessons documented** (both positive and negative)
- [ ] **Follow-up scheduled** (verify actions completed and effective)

[IF severity == "critical" OR severity == "high"]
- [ ] **Stakeholders notified** (PD, DIO, relevant committees)
- [ ] **External reporting completed** (if required)
[ENDIF]

---

***REMOVED******REMOVED*** Notes

***REMOVED******REMOVED******REMOVED*** 5-Whys Guidance

Stop asking "why" when you reach one of these endpoints:
- **Process level:** "Because we don't have a procedure for this"
- **System level:** "Because the system doesn't prevent this"
- **Cultural level:** "Because organizational incentives don't align with desired behavior"

If you reach 5 whys and are still at individual blame ("because Bob made a mistake"), keep going—you haven't found the root cause yet.

***REMOVED******REMOVED******REMOVED*** Integration with Other Templates

Typical workflow:
1. **INCIDENT_REVIEW** → Identify root cause and prevention needs
2. **RESEARCH_POLICY** → Investigate if policies need updating
3. **CONSTRAINT_ANALYSIS** → Determine if new constraints needed
4. **SCHEDULE_GENERATION** → Implement prevention in next schedule

***REMOVED******REMOVED******REMOVED*** Swiss Cheese Model

Use the "Swiss Cheese" model to visualize how multiple failures aligned:
- Each layer of defense (technical, process, human) has "holes" (weaknesses)
- Incident occurs when holes align across all layers
- Prevention requires closing holes in multiple layers (defense in depth)

***REMOVED******REMOVED******REMOVED*** Version History

- **v1.0.0** (2025-12-26): Initial template creation
  - Based on healthcare incident reporting best practices
  - Incorporates 5-whys, Swiss Cheese model, defense in depth
  - Tailored for medical residency scheduling context
