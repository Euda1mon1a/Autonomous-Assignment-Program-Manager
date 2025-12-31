# N-1/N-2 Contingency Analysis & Procedures

**Status:** Operational Procedure Guide
**Date:** 2025-12-31
**Purpose:** Detect and prepare for single-point-of-failure vulnerabilities
**Audience:** Program Directors, Chiefs, Scheduling Coordinators

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Contingency Scanning Schedule](#contingency-scanning-schedule)
3. [Vulnerability Detection Procedures](#vulnerability-detection-procedures)
4. [Fallback Activation Procedures](#fallback-activation-procedures)
5. [Test Scenarios](#test-scenarios)
6. [Contingency Dashboard](#contingency-dashboard)

---

## Executive Summary

### What are N-1 and N-2 Vulnerabilities?

**N-1 Vulnerability:** The system cannot safely operate if one specific person is absent.

**Example:** Dr. Smith is the only faculty qualified to supervise Level 2 procedures. If she's absent, Level 2 procedures cannot be performed.

**N-2 Vulnerability:** The system cannot operate if any two specific people are simultaneously absent.

**Example:** Dr. A and Dr. B together cover Critical Care. If both are absent, Critical Care has zero coverage.

### Impact

- **N-1 Vulnerabilities** create immediate single points of failure
- **N-2 Vulnerabilities** are slightly less critical but still dangerous
- **Cascade Vulnerabilities** are secondary failures triggered by N-1 loss (e.g., Dr. Smith absent → Dr. Jones overloaded → Dr. Jones departs)

### Goal

Identify vulnerabilities BEFORE they cause problems, then:
1. **Reduce** the dependency (cross-train others)
2. **Prepare fallbacks** (pre-authorized backup plans)
3. **Monitor** the critical person (extra support)
4. **Test** the fallback (practice before crisis)

---

## Contingency Scanning Schedule

### Automated Scanning (Weekly)

**Time:** Every Monday 0200 UTC (after week's assignments finalized)

**Procedure:**
```python
@celery_app.task(bind=True, name="scan_n1_n2_vulnerabilities")
def scan_contingencies(self, program_id: str):
    """
    Weekly vulnerability scan.
    Runs Monday after assignments complete.
    """
    program = get_program(program_id)

    # 1. Get current assignments
    assignments = get_week_assignments(program_id)

    # 2. Run N-1 analysis
    n1_vulns = analyze_n1_vulnerabilities(
        program,
        assignments,
        threshold_critical=0.20  # >20% blocks affected = CRITICAL
    )

    # 3. Run N-2 analysis (only test critical pairs)
    critical_faculty = {v.person_id for v in n1_vulns if v.severity == "CRITICAL"}
    n2_vulns = analyze_n2_vulnerabilities(
        program,
        assignments,
        faculty_to_test=critical_faculty,
        threshold_dangerous=0.10  # >10% blocks uncovered = DANGEROUS
    )

    # 4. Update contingency tracking
    store_contingency_analysis(program, n1_vulns, n2_vulns)

    # 5. Alert on new critical vulnerabilities
    previous_critical = get_previous_week_critical_vulns(program)
    new_critical = n1_vulns - previous_critical
    if new_critical:
        alert_program_director(
            f"NEW N-1 VULNERABILITIES DETECTED: {len(new_critical)} new critical"
        )

    # 6. Generate contingency dashboard update
    update_contingency_dashboard(program, n1_vulns, n2_vulns)

    return {
        "n1_vulnerabilities": len(n1_vulns),
        "n2_vulnerabilities": len(n2_vulns),
        "critical_count": sum(1 for v in n1_vulns if v.severity == "CRITICAL"),
        "timestamp": datetime.now(timezone.utc)
    }
```

### Manual Scanning (On-Demand)

**When to trigger:**
- Before critical rotation (surgery block, critical care week)
- After major staffing change (new hire, departure)
- When new dependency identified
- After contingency activation (verify fallback worked)

**Procedure:**
1. [ ] Program Director initiates scan via dashboard button
2. [ ] System runs same algorithm as weekly scan
3. [ ] Results displayed immediately
4. [ ] Director reviews and takes action if needed

### Quarterly Deep Dive

**Time:** Last Friday of every quarter (1400 UTC)

**Participants:** Program Director + Chiefs + Senior Faculty

**Agenda:**
1. [ ] Review year-to-date vulnerabilities (trends?)
2. [ ] Analyze if critical vulnerabilities were resolved
3. [ ] Plan cross-training for persistent dependencies
4. [ ] Update contingency playbooks
5. [ ] Practice a contingency scenario (tabletop exercise)

---

## Vulnerability Detection Procedures

### N-1 Analysis Algorithm

**Input:** Current assignments, coverage requirements

**Output:** Ranked list of N-1 vulnerabilities

```python
def analyze_n1_vulnerabilities(program, assignments, threshold_critical=0.20):
    """
    For each faculty member, calculate impact of their absence.
    """
    vulnerabilities = []

    for faculty in program.active_faculty:
        # 1. Create "removed" assignment state
        assignments_without_faculty = [
            a for a in assignments
            if a.person_id != faculty.id
        ]

        # 2. For each block this faculty is assigned to
        affected_blocks = set()
        uncovered_blocks = set()

        for block in program.all_blocks:
            remaining_coverage = count_coverage(
                block,
                assignments_without_faculty
            )
            required_coverage = get_coverage_requirement(block)

            if remaining_coverage < required_coverage:
                affected_blocks.add(block.id)

            if remaining_coverage == 0:
                uncovered_blocks.add(block.id)

        # 3. Calculate severity
        affect_percentage = len(affected_blocks) / len(program.all_blocks)
        uncovered_percentage = len(uncovered_blocks) / len(program.all_blocks)

        if len(uncovered_blocks) > 0:
            severity = "CRITICAL"  # Any uncovered blocks = critical
        elif affect_percentage >= threshold_critical:
            severity = "CRITICAL"
        elif affect_percentage >= 0.10:
            severity = "HIGH"
        elif affect_percentage >= 0.05:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        vulnerability = N1Vulnerability(
            person_id=faculty.id,
            person_name=faculty.name,
            severity=severity,
            affected_blocks=affected_blocks,
            uncovered_blocks=uncovered_blocks,
            affect_percentage=affect_percentage,
            reason=identify_reason(faculty, affected_blocks)
        )

        vulnerabilities.append(vulnerability)

    return sorted(
        vulnerabilities,
        key=lambda v: (
            SEVERITY_RANK[v.severity],
            -len(v.uncovered_blocks),
            -v.affect_percentage
        )
    )
```

### Identifying Vulnerability Reasons

**Code identifies why person is critical:**

```python
def identify_reason(faculty, affected_blocks):
    """
    Classify the type of dependency.
    """
    # Count blocks where sole provider
    sole_provider_blocks = {
        b for b in affected_blocks
        if is_sole_provider(faculty, b)
    }

    # Count blocks where high workload
    high_load_blocks = {
        b for b in affected_blocks
        if get_block_utilization(faculty, b) > 0.7
    }

    # Unique qualifications
    unique_qualifications = get_unique_credentials(faculty)

    if sole_provider_blocks:
        return {
            "type": "SOLE_PROVIDER",
            "blocks": sole_provider_blocks,
            "note": f"Sole provider for {len(sole_provider_blocks)} blocks"
        }

    elif unique_qualifications:
        return {
            "type": "UNIQUE_QUALIFICATION",
            "qualifications": unique_qualifications,
            "note": f"Only faculty with {', '.join(unique_qualifications)}"
        }

    elif high_load_blocks:
        return {
            "type": "HIGH_WORKLOAD",
            "blocks": high_load_blocks,
            "note": f"Carries {len(high_load_blocks)} high-load blocks"
        }

    else:
        return {
            "type": "UNKNOWN",
            "note": "Reason unclear; requires manual review"
        }
```

### N-2 Analysis Algorithm

**Input:** N-1 critical vulnerabilities, program assignments

**Optimization:** Only test pairs of critical faculty (reduces O(n²) to O(k²) where k << n)

```python
def analyze_n2_vulnerabilities(program, assignments, faculty_to_test):
    """
    For each pair of critical faculty, detect dangerous dependencies.
    """
    vulnerabilities = []

    # Generate all pairs
    pairs = list(itertools.combinations(faculty_to_test, 2))

    for faculty_1, faculty_2 in pairs:
        # 1. Create "removed" state (both absent)
        assignments_without_pair = [
            a for a in assignments
            if a.person_id not in (faculty_1.id, faculty_2.id)
        ]

        # 2. Collect all blocks where at least one was assigned
        affected_blocks = set()
        uncoverable_blocks = set()

        for block in program.all_blocks:
            if has_assignment(faculty_1, block, assignments) or \
               has_assignment(faculty_2, block, assignments):

                remaining_coverage = count_coverage(
                    block,
                    assignments_without_pair
                )
                required = get_coverage_requirement(block)

                if remaining_coverage < required:
                    affected_blocks.add(block.id)

                if remaining_coverage == 0:
                    uncoverable_blocks.add(block.id)

        # 3. Classify severity
        if len(uncoverable_blocks) > 0:
            severity = "DANGEROUS"
        elif len(affected_blocks) / len(program.all_blocks) > 0.15:
            severity = "RISKY"
        else:
            severity = "ACCEPTABLE"

        if severity != "ACCEPTABLE":
            pair_vuln = N2Vulnerability(
                person_1_id=faculty_1.id,
                person_2_id=faculty_2.id,
                person_1_name=faculty_1.name,
                person_2_name=faculty_2.name,
                severity=severity,
                affected_blocks=affected_blocks,
                uncoverable_blocks=uncoverable_blocks,
                reason=identify_pair_reason(faculty_1, faculty_2, affected_blocks)
            )
            vulnerabilities.append(pair_vuln)

    return sorted(
        vulnerabilities,
        key=lambda v: (-len(v.uncoverable_blocks), SEVERITY_RANK[v.severity])
    )
```

### Example: Full Vulnerability Report

**Program:** Military Medical Center, 20 Faculty, Current Week

```
CONTINGENCY ANALYSIS REPORT
Generated: 2025-12-30 0200 UTC
Period: Week of 2025-12-29

─── N-1 CRITICAL VULNERABILITIES ───

[CRITICAL] Dr. Sarah Chen (Chief Resident)
├─ Affected: 12 blocks (60% of week)
├─ Uncovered: 3 blocks (Critical Care Monday-Wednesday)
├─ Reason: Sole supervisor for Critical Care
├─ Current Status: In ICE
├─ Workload: 82 hours/week (HIGH BURNOUT RISK)
└─ Recommendation: URGENT - Cross-train backup immediately

[HIGH] Dr. James Rodriguez (Trauma Surgeon)
├─ Affected: 8 blocks (40% of week)
├─ Uncovered: 0 blocks
├─ Reason: Only Level 3 trauma surgeon
├─ Current Status: Healthy
├─ Workload: 78 hours/week
└─ Recommendation: Cross-train second surgeon ASAP

[MEDIUM] Dr. Amanda Liu (Pediatrics)
├─ Affected: 3 blocks (15% of week)
├─ Uncovered: 0 blocks
├─ Reason: Pediatric specialty knowledge
├─ Current Status: Healthy
└─ Recommendation: Defer for 3 months until summer

─── N-2 DANGEROUS PAIRS ───

[DANGEROUS] Dr. Chen + Dr. Rodriguez
├─ Combined coverage loss: 15 blocks (75% of week)
├─ Uncoverable: Critical Care + Trauma = 0 coverage
├─ Risk Level: EXTREME (both absent simultaneously = no coverage)
├─ Probability: ~0.2% annually (low probability but high impact)
└─ Mitigation: Pre-plan OR train backup for both

─── SUMMARY ───

Critical Vulnerabilities: 1 (Dr. Chen)
High Vulnerabilities: 1 (Dr. Rodriguez)
Medium Vulnerabilities: 1 (Dr. Liu)
Dangerous Pairs: 1 (Chen + Rodriguez)

Overall Risk: MODERATE
Action Priority: URGENT (Cross-train for Chen's role)

Estimated Time to Resolve: 4-8 weeks (cross-training)
Interim Mitigation: 1. Hire temporary backup; 2. Reduce Chen's workload
```

---

## Fallback Activation Procedures

### Pre-Planned Fallbacks

**For each N-1 CRITICAL vulnerability, must have pre-authorized fallback:**

```
N-1 Critical: Dr. Sarah Chen (sole Critical Care supervisor)

FALLBACK PLAN (pre-authorized):
├─ Primary Fallback: Dr. James Rodriguez (trauma → critical care)
│  └─ Authorization: Requires 2 hours notice
│  └─ Credentialing: Already current (co-certified)
├─ Secondary Fallback: Dr. Michael Park (internal medicine → critical care)
│  └─ Authorization: Requires 4 hours notice
│  └─ Credentialing: Needs quarterly re-validation
└─ Tertiary Option: External locum service
   ├─ Authorization: Program Director + Hospital VP
   ├─ Cost: $3,500/day (pre-contracted)
   └─ Lead Time: 24 hours
```

### Fallback Activation Triggers

**Fallback activated when:**
1. [ ] Vulnerable person calls in sick/absent
2. [ ] OR vulnerability identified during weekly scan with elevated risk
3. [ ] OR contingency test/drill in progress

**Activation Procedure:**

**Step 1: Immediate Notification (Within 5 minutes)**
```
Program Director calls:
  ├─ Chief Resident (brief on situation)
  ├─ Primary Fallback person (notify of potential need)
  ├─ Hospital Scheduling (update assignment)
  └─ Patient Care Coordinator (notify of coverage change)

Message Template:
"Dr. Chen is unexpectedly absent. Activating fallback plan.
Dr. Rodriguez will cover Critical Care today. Any questions
call me immediately."
```

**Step 2: Coverage Verification (Within 30 minutes)**
```
Scheduling Coordinator confirms:
  ├─ [ ] Fallback person confirmed available
  ├─ [ ] All Critical Care assignments transferred
  ├─ [ ] Handoff briefing completed
  ├─ [ ] Electronic records updated
  └─ [ ] Notify patients if schedule changed
```

**Step 3: Ongoing Monitoring**
```
Chief Resident monitors:
  ├─ Fallback person's workload (check every 4 hours)
  ├─ Coverage adequacy (any new gaps?)
  ├─ Quality of care maintained?
  └─ Any escalation needed?
```

**Step 4: Deactivation / Transition**
```
When Dr. Chen returns:
  ├─ Reintegrate at normal pace (no overload for return day)
  ├─ Review with fallback person (lessons learned)
  ├─ Document in contingency log
  └─ Update fallback plan if needed
```

### Fallback Maintenance

**Quarterly Validation (Every 3 months):**

```python
@celery_app.task(name="validate_fallback_plans")
def validate_fallback_plans(program_id):
    """
    Quarterly: Verify all fallback plans are still current.
    """
    program = get_program(program_id)

    for fallback in program.fallback_plans:
        # 1. Verify credentialing current
        if not is_credentialing_current(fallback.backup_person):
            alert_program_director(
                f"FALLBACK CREDENTIAL EXPIRED: {fallback.backup_person.name}"
            )

        # 2. Verify authorization still valid
        if fallback.expires_at < datetime.now():
            alert_program_director(
                f"FALLBACK AUTHORIZATION EXPIRED: {fallback.id}"
            )

        # 3. Contact fallback person (verify still willing)
        notify_fallback_person(fallback.backup_person,
            message=f"Confirming your availability as fallback for {fallback.primary_person}")

        # 4. Record validation
        log_fallback_validation(fallback, validated_at=datetime.now())

    return {"validated_count": len(program.fallback_plans)}
```

---

## Test Scenarios

### Monthly Contingency Drills

**Schedule:** First Friday of each month (1400 UTC)

**Duration:** 30-45 minutes (simulated, no actual schedule change)

**Procedure:**

```python
@celery_app.task(name="monthly_contingency_drill")
def monthly_contingency_drill(program_id):
    """
    Monthly simulated contingency test (tabletop exercise).
    """
    program = get_program(program_id)

    # 1. Select random critical vulnerability
    critical_vulns = get_critical_vulnerabilities(program)
    test_vuln = random.choice(critical_vulns)

    print(f"CONTINGENCY DRILL: {test_vuln.person_name} is unavailable")

    # 2. Ask: "What happens if they're absent next Monday?"
    # 3. Review fallback plan
    # 4. Walk through activation steps
    # 5. Verify fallback person is available/willing
    # 6. Discuss any issues/improvements

    # 7. Document results
    drill_result = ContingencyDrillResult(
        program_id=program.id,
        vulnerable_person_id=test_vuln.person_id,
        fallback_person_id=test_vuln.fallback_plan.backup_person_id,
        status="successful" or "issues_found",
        issues=["Issue 1", "Issue 2"],
        improvements=["Improvement 1"],
        recorded_by=current_user.id,
        timestamp=datetime.now()
    )
    store_drill_result(drill_result)

    return {
        "test_person": test_vuln.person_name,
        "fallback_person": test_vuln.fallback_plan.backup_person.name,
        "status": drill_result.status
    }
```

### Scenario 1: Single Faculty Absence

**Setup:**
```
Normal week: 20 faculty, all available
Scenario: Dr. Chen (Critical Care) calls in sick Monday morning

Question: Can you maintain coverage?
```

**Walkthrough:**
1. Immediate response (5 min): Notify team, activate fallback
2. Coverage check (15 min): Confirm Rodriguez can cover
3. Patient notification (20 min): Contact patients with schedule change
4. Day execution (full day): Monitor Rodriguez's workload
5. Debrief (next day): Lessons learned

**Success Criteria:**
- [ ] Coverage maintained with no uncovered blocks
- [ ] Fallback person confirmed available <15 minutes
- [ ] All assignments updated in system <30 minutes
- [ ] Patients notified before shift start
- [ ] Quality of care maintained (no incidents)

### Scenario 2: Multiple Absences

**Setup:**
```
Scenario: Dr. Chen + Dr. Rodriguez both unavailable
(sick child + car accident)

Question: Can you operate without both?
```

**Walkthrough:**
1. Identify N-2 vulnerability (both unavailable)
2. Activate both fallbacks (Rodriguez → Park, Chen → external locum)
3. Assess coverage adequacy
4. Contact external locum service (24-hour lead time?)
5. Discuss temporary service reduction (defer electives?)

**Success Criteria:**
- [ ] Secondary fallbacks identified and available
- [ ] Coverage remains ≥85%
- [ ] External resources engaged if needed
- [ ] Service modifications planned if necessary
- [ ] Escalation triggered appropriately

### Scenario 3: Fallback Unavailable (Chain of Failure)

**Setup:**
```
Scenario: Dr. Chen absent, but Dr. Rodriguez also has emergency

Question: What's Plan C?
```

**Walkthrough:**
1. Primary fallback unavailable
2. Activate secondary fallback (Dr. Park)
3. If Park unavailable → external locum
4. If locum unavailable → service reduction
5. Escalate to hospital VP if needed

**Success Criteria:**
- [ ] Tertiary plan exists and is executable
- [ ] Coverage maintained or gracefully reduced
- [ ] No critical gap in essential services

---

## Contingency Dashboard

### Key Metrics

**Panel 1: Current Vulnerabilities**

```
N-1 Critical Count:    1 (Dr. Chen)
N-1 High Count:        1 (Dr. Rodriguez)
N-2 Dangerous Pairs:   1 (Chen + Rodriguez)

Last Scan: 2025-12-30 0200 UTC
Next Scan: 2025-12-31 0200 UTC
Status: ✓ All fallbacks current
```

**Panel 2: Vulnerability Trend (30-day)**

```
Chart: Line graph showing count of critical vulnerabilities over time

Target: <2 CRITICAL at all times
Current: 1 (acceptable)
Trend: Stable → Declining (good)

Interpretation: Dr. Chen dependency identified weeks ago,
still unresolved. Urgent cross-training needed.
```

**Panel 3: Fallback Status**

```
Person          Fallback Plan    Status              Next Validation
─────────────────────────────────────────────────────────────────
Dr. Chen        Dr. Rodriguez    ✓ Current           2026-02-01
Dr. Rodriguez   Dr. Park         ✓ Current           2026-02-01
Dr. Liu         Rotation coverage ✓ Current           2026-02-01
```

**Panel 4: Contingency Test Results**

```
Last Test: 2025-12-06 (Scenario 1: Single absence)
Result: ✓ Successful
Issues: None
Next Test: 2026-01-03

Monthly Drill Schedule:
  ├─ 2025-12-06: Single absence (Complete)
  ├─ 2026-01-03: Multiple absence (Scheduled)
  └─ 2026-02-07: Fallback chain failure (Scheduled)
```

---

## Appendix: Contingency Checklist

### For Each Critical N-1 Vulnerability:

- [ ] **Identification**: Confirmed as N-1 critical by system
- [ ] **Fallback Plan**: Written and authorized
- [ ] **Fallback Person**: Confirmed available and trained
- [ ] **Credentialing**: Fallback's credentials current
- [ ] **Authorization**: Hospital VP sign-off obtained
- [ ] **Testing**: Tested in contingency drill
- [ ] **Documentation**: Plan uploaded to system
- [ ] **Communication**: Fallback person briefed
- [ ] **Quarterly Validation**: Last validated within 90 days

### For Each Critical N-2 Pair:

- [ ] **Identification**: Confirmed as N-2 dangerous by system
- [ ] **Mitigation Option 1**: Cross-train third person OR
- [ ] **Mitigation Option 2**: Pre-plan service reduction OR
- [ ] **Mitigation Option 3**: Hire temporary backup
- [ ] **Testing**: Tested in contingency drill
- [ ] **Cost Estimate**: Determined and budgeted

---

**Document Classification:** OPERATIONAL
**Approved for:** Program Directors, Chiefs, Scheduling Coordinators
**Effective Date:** 2025-12-31
**Review Cycle:** Quarterly (by chief resident) + Annual (by director)

