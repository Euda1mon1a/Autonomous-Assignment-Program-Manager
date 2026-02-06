# Schedule Alignment Questionnaire

> **Purpose:** Help program coordinators verify that their understanding of the generated schedule matches what the CP-SAT solver actually produced.
> **Target Audience:** Program coordinators with domain knowledge of the residency program
> **Estimated Time:** 15-20 minutes for initial review

---

## Instructions

This questionnaire is designed to be completed AFTER the CP-SAT solver generates a schedule. Walk through each section sequentially, checking the generated output against your expectations.

**How to use this document:**
1. Print or open in split-screen view
2. Review the generated schedule export (Excel or web view)
3. Check each box as you verify that section
4. Note discrepancies in the "Expected vs Actual" sections
5. Escalate any "NO" answers or major discrepancies to the technical team

**Success criteria:** Most boxes should be checked "YES." A few "NO" answers may be expected (solver optimizations), but multiple "NO" answers in critical sections indicate a configuration or data issue.

---

## Section 1: Rotation Distribution

### 1.1 Resident Block Assignments
Review the 4-week block rotations assigned to each resident.

- [ ] **All residents have assigned rotations** (no blank 4-week blocks)
- [ ] **PGY-1 residents are on appropriate rotations** (expected introductory/core rotations)
- [ ] **PGY-2 residents are on appropriate rotations** (expected intermediate rotations)
- [ ] **PGY-3 residents are on appropriate rotations** (expected advanced/elective rotations)
- [ ] **No resident is on a rotation they completed recently** (continuity/variety check)

**Expected vs Actual:**
| Resident | Expected Rotation | Actual Rotation | Match? |
|----------|-------------------|-----------------|--------|
| _________ | _________________ | ________________ | ☐ YES ☐ NO |
| _________ | _________________ | ________________ | ☐ YES ☐ NO |
| _________ | _________________ | ________________ | ☐ YES ☐ NO |

### 1.2 Rotation Coverage
Check that all required rotations have adequate staffing.

- [ ] **FMIT (inpatient) rotations are staffed** (expected number of residents/faculty)
- [ ] **Outpatient rotations are staffed** (expected number of residents)
- [ ] **External rotations (Peds, OB, Neuro, etc.) are staffed** (expected number)
- [ ] **No rotation is over-capacity** (too many residents assigned)
- [ ] **No rotation is under-capacity** (too few residents assigned)

**Notes on surprises:**
_____________________________________________________________________
_____________________________________________________________________

---

## Section 2: Faculty Coverage

### 2.1 Faculty Assignments
Review faculty supervision assignments.

- [ ] **All faculty have clinic slots assigned** (expected number per week)
- [ ] **Faculty roles match assignments** (Core vs Adjunct vs GME/DFM admin)
- [ ] **No faculty member is over-scheduled** (check weekly clinic counts)
- [ ] **Faculty on FMIT weeks have FMIT assigned** (Friday-Thursday blocks)
- [ ] **Faculty NOT on FMIT have regular clinic** (AM/PM slots distributed appropriately)

**Expected vs Actual (sample faculty):**
| Faculty | Expected Weekly Clinics | Actual Weekly Clinics | Match? |
|---------|-------------------------|------------------------|--------|
| _________ | _____ AM + _____ PM | _____ AM + _____ PM | ☐ YES ☐ NO |
| _________ | _____ AM + _____ PM | _____ AM + _____ PM | ☐ YES ☐ NO |
| _________ | _____ AM + _____ PM | _____ AM + _____ PM | ☐ YES ☐ NO |

### 2.2 Faculty Absence Blocking
Check that faculty absences are respected.

- [ ] **Faculty on leave/TDY have no clinic assignments** (absence dates respected)
- [ ] **Faculty absences are visible in the schedule** (blocked out, not just missing)
- [ ] **No faculty assigned to clinic on known absence dates**

**Notes on coverage gaps:**
_____________________________________________________________________
_____________________________________________________________________

---

## Section 3: ACGME Compliance

### 3.1 Work Hour Limits
Check for 80-hour rule violations.

- [ ] **No resident exceeds 80 hours/week** (check 4-week rolling average)
- [ ] **Call nights are distributed fairly** (no one resident has excessive call)
- [ ] **Post-call residents have recovery time** (not scheduled for heavy clinic next day)

**Known violations (if any):**
_____________________________________________________________________
_____________________________________________________________________

### 3.2 Day-Off Requirements
Check 1-in-7 rule compliance.

- [ ] **All residents have at least one 24-hour period off per week** (check DO/OFF slots)
- [ ] **Day-off patterns are reasonable** (not always Sunday, varied across residents)
- [ ] **No resident works 8+ consecutive days** (check for extended stretches)

**Patterns to note:**
_____________________________________________________________________
_____________________________________________________________________

### 3.3 Supervision Ratios
Check faculty-to-resident supervision ratios.

- [ ] **All clinical sessions have adequate faculty supervision** (AT, PCAT, or coverage)
- [ ] **PGY-1 residents never work without supervision** (supervision codes present)
- [ ] **Supervision ratios meet program standards** (check FM clinic, procedures)

**Supervision gaps (if any):**
_____________________________________________________________________
_____________________________________________________________________

---

## Section 4: Activity Codes

### 4.1 Expected Activity Codes
Verify that the right activity codes appear in the right contexts.

**Common activity codes in Family Medicine:**
- **C** = FM Clinic (core resident clinic activity)
- **AT** = Attending supervision (faculty supervising residents)
- **PCAT** = Post-Call Attending (faculty supervising post-call residents)
- **DO** = Day Off (ACGME-mandated rest)
- **VAS** = Vasectomy clinic (procedure requiring credentialing)
- **PROC** = General procedures clinic
- **W** = Weekend duty
- **CV** = Continuity clinic (longitudinal patient panel)
- **LEC** = Protected lecture time (typically Wednesday PM)
- **OFF** = Time off (scheduled leave, vacation)
- **FMIT** = Family Medicine Inpatient Team

### 4.2 Activity Code Verification

- [ ] **C (FM Clinic) appears in expected slots** (AM/PM weekdays)
- [ ] **AT (Attending) is paired with resident clinic** (supervision present when needed)
- [ ] **PCAT appears after call nights** (post-call supervision assigned)
- [ ] **DO appears regularly** (1-in-7 day off pattern visible)
- [ ] **VAS/PROC appear in appropriate slots** (faculty with credentials assigned)
- [ ] **LEC appears on expected days** (typically Wednesday PM for all residents)
- [ ] **No unexpected activity codes** (unfamiliar abbreviations)

**Unexpected activity codes:**
| Code | Where Seen | Expected Meaning? |
|------|------------|-------------------|
| _____ | _____________ | ☐ YES ☐ NO ☐ UNKNOWN |
| _____ | _____________ | ☐ YES ☐ NO ☐ UNKNOWN |

---

## Section 5: Credential Matching

### 5.1 Procedure Assignments
Check that credentialed procedures are assigned appropriately.

- [ ] **VAS (Vasectomy) assigned only to credentialed faculty** (check credentials table)
- [ ] **SM (Sports Medicine) assigned only to credentialed faculty**
- [ ] **VASC (Vascular procedures) assigned only to credentialed faculty**
- [ ] **No procedure assignments without credentials** (penalty weight should discourage this)

**Credential mismatches (if any):**
| Procedure | Faculty Assigned | Credentialed? |
|-----------|------------------|---------------|
| _________ | ________________ | ☐ YES ☐ NO |
| _________ | ________________ | ☐ YES ☐ NO |

### 5.2 Credential Gaps
Identify missing credentials that may cause under-staffing.

- [ ] **All procedures have at least one credentialed faculty available**
- [ ] **No procedure clinics cancelled due to lack of credentials**

**Notes:**
_____________________________________________________________________
_____________________________________________________________________

---

## Section 6: Call Schedule

### 6.1 Overnight Call Distribution
Review the overnight call assignments (typically Sunday-Thursday).

- [ ] **Every eligible night has exactly one faculty assigned** (no gaps)
- [ ] **Call nights are distributed fairly** (no one faculty has excessive call)
- [ ] **FMIT faculty have Friday/Saturday call during their FMIT week** (mandatory FMIT call)
- [ ] **ADJUNCT faculty are excluded from call** (if applicable)
- [ ] **Faculty on leave/TDY are not assigned call**

**Call distribution (sample check):**
| Week | Sun | Mon | Tue | Wed | Thu | Fri (FMIT) | Sat (FMIT) |
|------|-----|-----|-----|-----|-----|------------|------------|
| Week 1 | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| Week 2 | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| Week 3 | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| Week 4 | ___ | ___ | ___ | ___ | ___ | ___ | ___ |

- [ ] **Distribution feels fair** (no outliers)

### 6.2 Post-Call Coverage
Check that post-call residents have appropriate next-day assignments.

- [ ] **PCAT (post-call attending) assigned after call nights**
- [ ] **DO (day off) assigned after heavy call** (check for back-to-back shifts)
- [ ] **No post-call resident has heavy clinic next morning**

**Post-call gaps:**
_____________________________________________________________________
_____________________________________________________________________

---

## Section 7: Leave and FMIT Absence Blocking

### 7.1 Known Absences
Verify that known absences are properly blocked out.

- [ ] **All known leave dates are blocked** (annual leave, sick leave)
- [ ] **All TDY/conference dates are blocked** (military deployments, training)
- [ ] **All FMIT weeks are blocked from regular clinic** (faculty on FMIT have no regular clinic)
- [ ] **Post-FMIT Friday is blocked** (recovery day after FMIT week)

**Missing absence blocks:**
| Person | Absence Type | Dates | Blocked? |
|--------|--------------|-------|----------|
| _________ | _____________ | ________ | ☐ YES ☐ NO |
| _________ | _____________ | ________ | ☐ YES ☐ NO |

### 7.2 FMIT Week Structure
Verify that FMIT weeks follow the Friday-Thursday pattern.

- [ ] **FMIT weeks start on Friday** (Friday-Thursday structure)
- [ ] **FMIT faculty have Friday/Saturday call** (mandatory weekend call)
- [ ] **FMIT faculty are blocked from Sun-Thurs call** (during their FMIT week)
- [ ] **Post-FMIT Friday is completely blocked** (recovery day)

**FMIT structure issues:**
_____________________________________________________________________
_____________________________________________________________________

---

## Section 8: Weekend Coverage

### 8.1 Weekend Assignments
Check that weekend clinic and call are staffed.

- [ ] **Weekend clinic slots are filled** (Saturday/Sunday if applicable)
- [ ] **Weekend call is assigned** (Friday/Saturday nights covered)
- [ ] **Weekend assignments are distributed fairly** (not always same people)

**Weekend gaps:**
_____________________________________________________________________
_____________________________________________________________________

### 8.2 Weekend Activity Codes
Verify that weekend activity codes are appropriate.

- [ ] **W (Weekend duty) appears on appropriate days**
- [ ] **FMIT call appears on Friday/Saturday nights**
- [ ] **No unexpected weekend assignments** (check for residents on leave)

**Notes:**
_____________________________________________________________________
_____________________________________________________________________

---

## Section 9: Institutional Events

### 9.1 Protected Time
Check that protected educational time is blocked out.

- [ ] **LEC (Lecture) appears on expected days** (typically Wednesday PM)
- [ ] **All residents have LEC at the same time** (protected educational time)
- [ ] **No clinic scheduled during LEC time**

### 9.2 Special Events
Verify that special events (retreats, conferences, holidays) are accounted for.

- [ ] **USAFP (Air Force Family Medicine Conference) dates are blocked**
- [ ] **Program retreats are blocked**
- [ ] **Federal holidays are respected** (or appropriately staffed)

**Missing event blocks:**
_____________________________________________________________________
_____________________________________________________________________

---

## Section 10: Overall Gut Check

### 10.1 Schedule "Feel"
This section is subjective but important. As someone who knows the program, does the schedule make sense?

- [ ] **The schedule looks reasonable** (no obviously absurd patterns)
- [ ] **Workload feels balanced** (no one resident/faculty is clearly overloaded)
- [ ] **The schedule reflects program priorities** (e.g., continuity, resident autonomy)
- [ ] **No major surprises** (nothing that makes you say "that can't be right")

**Gut feelings / concerns:**
_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________

### 10.2 What the Solver Changed
Identify where the solver made decisions you didn't expect.

- [ ] **Solver moved assignments I expected to stay fixed** (if so, why?)
- [ ] **Solver created patterns I didn't anticipate** (good or bad?)
- [ ] **Solver violated soft preferences** (understand the trade-offs?)

**Solver surprises:**
_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________

### 10.3 Readiness for Publication
Final decision: Is this schedule ready to publish?

- [ ] **YES** — Schedule is ready to publish with minor/no edits
- [ ] **MAYBE** — Schedule needs a few manual tweaks, then ready
- [ ] **NO** — Schedule has major issues, needs regeneration or escalation

**If NO or MAYBE, what needs to change?**
_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________

---

## Section 11: Known Solver Behaviors

Understanding these may reduce false alarms when reviewing the schedule.

### 11.1 Optimization Trade-offs
The CP-SAT solver balances multiple competing objectives. Be aware of these trade-offs:

- **Equity vs Preferences:** The solver may ignore individual preferences to balance workload.
- **Coverage vs Continuity:** The solver prioritizes filling gaps over keeping residents on the same rotation.
- **Credential matching:** The solver has a soft penalty (weight: 15) for credential mismatches. If no credentialed faculty are available, it MAY assign non-credentialed faculty.
- **Template balance:** The solver tries to distribute residents evenly across rotation types (prevents clustering).

### 11.2 What the Solver CANNOT Do
These require manual intervention:

- **Respect verbal agreements** ("I promised resident X they'd get rotation Y")
- **Account for personalities** ("These two faculty work well together")
- **Handle mid-block changes** ("This resident will be deployed starting week 3")
- **Fix bad input data** ("Oops, I forgot to mark faculty Z as on leave")

**Expectations to adjust:**
_____________________________________________________________________
_____________________________________________________________________

---

## Appendix: Common Activity Code Reference

| Code | Full Name | Applies To | Description |
|------|-----------|------------|-------------|
| **C** | FM Clinic | Residents | Core family medicine clinic activity (patient care) |
| **AT** | Attending | Faculty | Supervision of residents in clinic |
| **PCAT** | Post-Call Attending | Faculty | Supervision of post-call residents (next day after call) |
| **DO** | Day Off | Residents/Faculty | ACGME-mandated 24-hour rest period |
| **VAS** | Vasectomy Clinic | Faculty | Vasectomy procedure clinic (requires credentials) |
| **VASC** | Vascular Procedures | Faculty | Vascular access procedures (requires credentials) |
| **PROC** | Procedures Clinic | Faculty | General procedures (may require credentials) |
| **SM** | Sports Medicine | Faculty | Sports medicine clinic (requires credentials) |
| **W** | Weekend Duty | Residents/Faculty | Weekend clinic or call coverage |
| **CV** | Continuity Clinic | Residents | Longitudinal continuity clinic (patient panel) |
| **LEC** | Lecture | Residents | Protected educational time (typically Wed PM) |
| **OFF** | Time Off | Residents/Faculty | Scheduled leave, vacation, or absence |
| **FMIT** | Inpatient Team | Faculty | Family Medicine Inpatient Teaching service |
| **GME** | GME Admin | Faculty | Graduate Medical Education administrative time |
| **DFM** | DFM Admin | Faculty | Department of Family Medicine admin time |

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-06 | 1.0 | Initial creation based on CP-SAT solver domain analysis |

---

*This questionnaire is a living document. Update as solver behavior evolves or program needs change.*
