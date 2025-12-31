# G2_RECON SEARCH_PARTY: ACGME Moonlighting Investigation Summary
**Session 3 - Complete**
**Date:** 2025-12-30
**Status:** Delivered

---

## INVESTIGATION SCOPE

**Target:** ACGME moonlighting rules and their implementation in the Residency Scheduler codebase

**10 SEARCH_PARTY Probes Executed:**

1. **PERCEPTION** - Current moonlighting tracking in codebase
   - Found: `AdvancedACGMEValidator.validate_moonlighting_hours()`
   - Status: Validates internal + external hours against 80h limit

2. **INVESTIGATION** - Hour counting integration
   - Found: 6-hour half-day block model
   - Found: Rolling 4-week average calculation
   - Gap: No granular tracking (WHEN/WHERE/WHO)

3. **ARCANA** - Internal vs. external moonlighting
   - Internal: Institution-based shifts (direct oversight)
   - External: Off-campus work (resident self-report)
   - Gap: No differentiation in approval process

4. **HISTORY** - Moonlighting policy evolution
   - ACGME VI.F.6 (Section VI.F.6): Counts toward 80-hour limit
   - ACGME VI.F.1: Total 80 hours/week averaged over 4 weeks
   - Regulatory framework unchanged since 2022

5. **INSIGHT** - Financial vs. educational balance
   - Internal: Stipend-based (institutional control)
   - External: Hourly/per-case (resident choice)
   - Gap: No educational value assessment

6. **RELIGION** - All moonlighting counted?
   - Includes: All clinical shifts at any facility
   - Excludes: Personal study, non-clinical work
   - Risk: External hours depend on resident honesty

7. **NATURE** - Overly restrictive policies?
   - Current: Binary 80-hour violation detection
   - Gap: No threshold-based warnings (75h, 78h)
   - Gap: No escalation process

8. **MEDICINE** - Resident fatigue concerns
   - Gap: No fatigue monitoring integrated
   - Gap: No post-TDY recovery protocols
   - Risk: Moonlighting + deployment = burnout cascade

9. **SURVIVAL** - Emergency moonlighting
   - Context: Military TDY/deployment recovery scenarios
   - Risk: Compensatory moonlighting without protection
   - Gap: No schedule protection policies

10. **STEALTH** - Unreported moonlighting
    - Risk: HIGH - External hours are self-reported
    - Gap: No cross-facility verification
    - Gap: No audit trail for approvals

---

## DELIVERABLE

**File:** `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/Scratchpad/OVERNIGHT_BURN/SESSION_3_ACGME/acgme-moonlighting-policies.md`

**Size:** 41 KB, 1,167 lines

**Structure:**
1. Executive Summary
2. Moonlighting Categories (6 classification schemes)
3. Hour Counting Requirements (what counts, calculation method)
4. Approval Workflows (4-step process + governance model)
5. Compliance Monitoring (real-time detection architecture)
6. Internal vs. External Distinction (risk matrix)
7. Institutional Policies (core policy statements)
8. Operational Risk Zones (7 high-risk scenarios)
9. Implementation Roadmap (codebase integration)
10. ACGME Audit Checklist
11. Military Medical Context (TDY/deployment considerations)
12. Appendices (regulatory references, best practices)

---

## KEY FINDINGS

### Current Implementation
✓ **What Works:**
- Moonlighting hour validation against 80h limit
- Rolling 4-week average calculation
- PGY-specific shift length rules
- Test coverage for violation detection

✗ **Critical Gaps:**
- No approval workflow system
- No granular hour tracking (when/where/who)
- No escalation alerts (75h, 78h thresholds)
- No external facility verification
- No audit documentation trail
- No fatigue monitoring

### Compliance Risk Assessment

| Risk Area | Current State | Audit Vulnerability |
|-----------|---------------|-------------------|
| **Approval documentation** | Missing | CRITICAL |
| **Hour verification** | Resident self-report | HIGH |
| **Escalation process** | None | HIGH |
| **Fatigue monitoring** | None | MEDIUM |
| **Educational value** | Not tracked | MEDIUM |
| **Audit trail** | No system | CRITICAL |

### Required Implementations (Priority Order)

**CRITICAL (Audit Failure Risk):**
1. Approval workflow system with digital signatures
2. Audit trail for all approvals + changes
3. Granular hour logging (date/time/facility/approver)
4. Hour verification mechanism for external work

**HIGH (Compliance Gap):**
5. Escalation alerts (GREEN/YELLOW/ORANGE/RED/BLACK)
6. Auto-restriction of new requests if ≥78h
7. Quarterly compliance reporting for PD
8. Monthly hour verification (resident + supervisor)

**MEDIUM (Program Improvement):**
9. Fatigue screening integration
10. Educational value assessment
11. Trend analysis (increasing/decreasing)
12. Post-TDY recovery protocols

---

## MOONLIGHTING CATEGORIES IDENTIFIED

### By Location + Employment
- **Internal:** Same MTF/institution (direct oversight)
- **External:** Different facility (resident self-report)

### By Educational Value
- **High:** Learning new procedures/skills
- **Medium:** General clinical experience
- **Low/Exploitative:** Pure labor, no learning

### By Approval Status
- **Approved:** Formal written approval (compliant if under 80h)
- **Conditional:** Approved with hour limits
- **Denied:** Too risky or would exceed 80h
- **Unreported:** Resident worked without approval (violation)

---

## HOUR COUNTING REQUIREMENTS

**Included (counts toward 80h limit):**
- All clinical shifts (internal or external)
- Call shifts (in-house or at-home, if active)
- Telemedicine shifts
- Procedure training (if clinical hours)
- Locum tenens work
- Pro-bono clinical work

**Not Included:**
- Personal study/reading
- Non-clinical research
- Administrative work
- Certification exam prep

**Calculation Method:**
```
For each 28-day window:
  total_hours = internal_program_hours + external_moonlighting_hours
  weekly_average = total_hours / 4

  if weekly_average > 80:
    VIOLATION
```

---

## APPROVAL WORKFLOW (4-Step)

```
1. RESIDENT REQUESTS → PD EVALUATES → APPROVAL DECISION → HOUR TRACKING

Step 1: Resident submits:
  - Facility name
  - Proposed hours
  - Educational justification
  - Supervisor contact info

Step 2: PD checks:
  - Would it exceed 80h/week? (If yes → deny)
  - Educational value vs. pure labor
  - Resident fatigue risk
  - Program impact

Step 3: Decision:
  - APPROVED (no conditions)
  - CONDITIONAL (with hour limits)
  - DENIED (too risky)

Step 4: Monthly tracking:
  - Resident logs hours
  - System calculates rolling 4-week average
  - Alerts if approaching 80h
```

---

## COMPLIANCE MONITORING ESCALATION

| Status | Threshold | Action |
|--------|-----------|--------|
| **GREEN** | <75 h/wk | Monitor quarterly |
| **YELLOW** | 75-78 h/wk | Review schedule, counsel resident |
| **ORANGE** | 78-80 h/wk | Restrict new moonlighting requests |
| **RED** | >80 h/wk | Halt new requests immediately |
| **BLACK** | >85 h/wk | Escalate to Compliance Officer |

---

## IMPLEMENTATION ROADMAP

### Phase 1: Approval Workflow (CRITICAL)
- Add `MoonlightingApproval` model (approval tracking)
- Add `MoonlightingHourLog` model (weekly logging)
- Create approval request form + API endpoints
- Implement digital signature workflow

### Phase 2: Enhanced Validation (HIGH)
- Add threshold-based alerts (75h, 78h)
- Auto-restrict requests if ≥78h
- Build escalation notification system
- Add severity classification (GREEN → BLACK)

### Phase 3: Compliance Reporting (HIGH)
- Quarterly PD report (moonlighting summary)
- Resident-level trend analysis
- Aggregate program statistics
- ACGME audit documentation

### Phase 4: Advanced Features (MEDIUM)
- Fatigue screening integration
- Educational value assessment
- Post-TDY recovery protocols
- Cross-facility verification (where possible)

---

## MILITARY MEDICAL CONTEXT CONSIDERATIONS

### TDY/Deployment Recovery
- Residents return fatigued from deployments
- Risk: Program encourages moonlighting to "catch up"
- Mitigation: Schedule protection, not intensification
- Policy: No new moonlighting approval within 30 days post-deployment

### Locum Tenens at Other Military Facilities
- Military residents often locum at other MTFs during leave
- Rule: **Still counts toward primary program's 80-hour limit**
- Requirement: PD approval required even if at military facility

### Humanitarian/Disaster Response
- High educational value
- But: 80-hour limit generally applies
- Mitigation: Document justification if limits exceeded

---

## AUDITOR CHECKPOINTS

**ACGME will ask:**
1. Did resident request permission? → **Document: Approval form**
2. Did PD approve in writing? → **Document: Signed approval letter**
3. Were hours tracked? → **Document: Weekly logs**
4. Was resident over 80 hours? → **Document: Rolling average calc**
5. What corrective action was taken? → **Document: PD intervention**

**Current Readiness: 30%** (Only #4 partially addressed)

---

## NEXT STEPS FOR OPERATIONS

1. **Immediate:** Review approval workflow design with PD/Compliance
2. **Week 1:** Implement Phase 1 (approval workflow + models)
3. **Week 2:** Add API endpoints for approval requests
4. **Week 3:** Build escalation alert system
5. **Week 4:** Create quarterly compliance reporting
6. **Month 2:** Add fatigue screening + educational value tracking

---

## DOCUMENT USAGE

This investigation output is designed for:

**Operational Teams:**
- Compliance Officers (audit preparation)
- Program Directors (approval policy)
- Resident Services (counseling on rules)

**Development Teams:**
- Backend engineers (API implementation)
- QA teams (test scenario creation)
- Database architects (schema design)

**Audit Preparation:**
- ACGME compliance self-assessment
- Documentation of policies + procedures
- Audit trail demonstration

---

**Investigation Complete** ✓
**Operational Status:** Ready for Integration
**Audit Risk:** CRITICAL (missing approval system)

---

*G2_RECON ready for next assignment.*
