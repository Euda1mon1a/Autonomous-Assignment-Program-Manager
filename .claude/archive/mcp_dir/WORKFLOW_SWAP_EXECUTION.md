# Workflow: Swap Execution

**Purpose**: Execute schedule swaps with safety validation and audit trail
**Safety**: TIER 2 (validation + preview, requires approval for apply)
**Execution Time**: 2-3 seconds (validation + preview)
**Frequency**: On-demand (multiple times per week)
**Operator**: Faculty/residents (request), Coordinator (approval), System (execution)

---

## Workflow Overview

This workflow handles faculty and resident shift swap requests with multi-level validation ensuring ACGME compliance and system integrity.

```
Faculty Swap Request
  │
  ├─→ Phase 1: Request Validation (1 second)
  │     ├─ Validate requester + assignments exist
  │     ├─ Check if swap feasible
  │     └─ Identify possible swap partners
  │
  ├─→ Phase 2: Candidate Analysis (0.5 seconds)
  │     ├─ Find compatible candidates
  │     ├─ Score each candidate
  │     └─ Rank by feasibility
  │
  ├─→ Phase 3: Impact Assessment (1 second)
  │     ├─ Simulate swap in schedule
  │     ├─ Check ACGME compliance
  │     ├─ Measure impact on others
  │     └─ Identify fallback plans
  │
  ├─→ Phase 4: Human Review & Approval
  │     ├─ Present options to requester
  │     ├─ Get mutual consent
  │     └─ Coordinator approval
  │
  └─→ Phase 5: Execution & Audit
        ├─ Apply swap to schedule
        ├─ Log audit trail
        └─ Notify affected parties
```

---

## Phase 1: Request Validation (1 second)

**Goals**:
- Verify requester has valid request
- Check assignment eligibility for swap
- Identify possible partners early

**Tools**:
- `validate_schedule` (check baseline)
- Manual validation (requester + assignment verification)

**Execution**:
```python
async def phase_1_validation(
    requester_id: str,
    assignment_id: str,
    target_date: Optional[date] = None,
) -> Phase1Result:
    """Validate swap request is feasible."""

    # Step 1: Verify requester exists and is active
    requester = await get_person(requester_id)
    if not requester or requester.status != "ACTIVE":
        raise InvalidRequesterError(f"Requester {requester_id} not active")

    # Step 2: Verify assignment exists and belongs to requester
    assignment = await get_assignment(assignment_id)
    if not assignment or assignment.person_id != requester_id:
        raise InvalidAssignmentError(f"Assignment not found or not owned by requester")

    # Step 3: Check if assignment is swappable
    if assignment.is_locked:
        raise SwapBlockedError("Assignment locked - cannot swap")
    if is_past_date(assignment.date):
        raise SwapBlockedError("Cannot swap past assignments")

    # Step 4: Validate current schedule compliance (baseline)
    compliance = await validate_schedule(
        start_date=assignment.date,
        end_date=assignment.date + timedelta(days=30),
    )
    if not compliance.is_compliant:
        raise ComplianceError("Schedule not compliant - cannot modify")

    # Step 5: Get count of same-type assignments nearby (pool)
    swap_pool = await get_similar_assignments(
        assignment.rotation,
        date_window=[assignment.date - timedelta(days=7), assignment.date + timedelta(days=7)]
    )

    return Phase1Result(
        valid=True,
        requester=requester,
        assignment=assignment,
        compliance_baseline=compliance.is_compliant,
        potential_candidates=len(swap_pool),
    )
```

**Phase 1 Validation Checklist**:
```
✓ Requester exists and is active
✓ Assignment belongs to requester
✓ Assignment not locked
✓ Assignment not in past
✓ Current schedule compliant
✓ Swap pool available (3+ potential partners)
```

**Phase 1 Output**:
```json
{
  "request_id": "swap-request-001",
  "status": "valid",
  "requester": {
    "id": "FAC-PD",
    "name_ref": "faculty-001",
    "role": "Faculty"
  },
  "assignment": {
    "id": "assign-001",
    "date": "2025-12-22",
    "rotation": "Inpatient",
    "block": "AM",
    "original_holder": "FAC-PD"
  },
  "validation_results": {
    "compliance_baseline": true,
    "potential_candidates": 7,
    "earliest_notice_ok": true
  }
}
```

**Phase 1 Failure Modes**:

| Failure | Action |
|---------|--------|
| Requester not found | Reject immediately |
| Assignment locked | Reject (show lock reason) |
| Past assignment | Reject (too late) |
| Current compliance fail | Reject (fix first) |
| No candidates available | Warn (may need coordinator help) |

---

## Phase 2: Candidate Analysis (0.5 seconds)

**Goals**:
- Identify all feasible swap partners
- Score by compatibility
- Rank by desirability

**Tools**:
- `analyze_swap_candidates` - Multi-factor scoring

**Execution**:
```python
async def phase_2_candidate_analysis(
    requester_id: str,
    assignment_id: str,
) -> Phase2Result:
    """Find and score swap candidates."""

    candidates = await analyze_swap_candidates(
        requester_id=requester_id,
        assignment_id=assignment_id,
        preferences={
            "prefer_mutual": True,  # Both parties benefit
            "prefer_similar_rotation": True,  # Same rotation
            "prefer_similar_date": True,  # Close dates
        },
        max_candidates=10,
    )

    # Enrich with compatibility details
    for candidate in candidates:
        # Check if mutual benefit (candidate also wants to swap)
        candidate.mutual_benefit = await check_mutual_interest(
            candidate.candidate_id,
            candidate.target_assignment_id,
            requester_id,
            assignment_id,
        )

        # Check if both are in good standing
        candidate.both_active = (
            await is_active(requester_id) and
            await is_active(candidate.candidate_id)
        )

        # Calculate risk score
        candidate.risk_score = calculate_risk_score(candidate)

    # Sort by combined score
    candidates.sort(key=lambda c: c.match_score * (1 + (0.5 if c.mutual_benefit else 0)))

    return Phase2Result(
        candidates=candidates,
        total_available=len(candidates),
        top_recommendation=candidates[0] if candidates else None,
    )
```

**Candidate Scoring Algorithm**:
```
match_score = (
    (date_proximity_score * 0.25) +
    (preference_alignment_score * 0.30) +
    (workload_balance_score * 0.20) +
    (swap_history_score * 0.15) +
    (availability_score * 0.10)
)

Bonus multipliers:
├─ Mutual benefit: +1.5x
├─ Past successful swaps: +1.2x
├─ Same rotation type: +1.1x
└─ Clear workload improvement: +1.1x
```

**Phase 2 Output**:
```json
{
  "request_id": "swap-request-001",
  "candidates": [
    {
      "rank": 1,
      "candidate_id": "FAC-005",
      "match_score": 0.92,
      "target_assignment": {
        "id": "assign-005",
        "date": "2025-12-23",
        "rotation": "Inpatient",
        "block": "AM"
      },
      "compatibility_factors": {
        "date_proximity": 0.95,
        "preference_alignment": 0.90,
        "workload_balance": 0.88,
        "swap_history": 1.0,
        "availability": 1.0
      },
      "mutual_benefit": true,
      "mutual_interest": {
        "candidate_also_wants_swap": true,
        "with_requester": true
      },
      "risk_score": 0.05,
      "notes": "Previous successful swap, mutual interest confirmed"
    },
    {
      "rank": 2,
      "candidate_id": "FAC-002",
      "match_score": 0.85,
      ...
    }
  ],
  "total_candidates": 7,
  "recommendation": {
    "candidate_id": "FAC-005",
    "reason": "Highest match score with mutual benefit"
  }
}
```

**Phase 2 Success Criteria**:
```
✓ At least 3 candidates available
✓ Top candidate match score >= 0.80
✓ Risk scores < 0.15 for top 3
```

---

## Phase 3: Impact Assessment (1 second)

**Goals**:
- Simulate swap in schedule
- Verify ACGME compliance maintained
- Measure impact on other staff
- Identify fallback contingencies

**Tools** (Parallel):
- `detect_conflicts` - Check for new conflicts
- `validate_schedule` - Verify compliance with swap
- `run_contingency_analysis` - Check impact on contingencies

**Execution**:
```python
async def phase_3_impact_assessment(
    requester_id: str,
    assignment_id: str,
    candidate: CandidateInfo,
) -> Phase3Result:
    """Assess impact of proposed swap."""

    # Create hypothetical schedule with swap applied
    hypothetical_schedule = await create_hypothetical_schedule(
        current_schedule=get_current_schedule(),
        swap_operations=[
            SwapOperation(
                from_person=requester_id,
                from_assignment=assignment_id,
                to_person=candidate.candidate_id,
                to_assignment=candidate.target_assignment_id,
            )
        ],
    )

    # Task 1: Check for new conflicts
    conflicts_task = detect_conflicts(
        schedule_id=hypothetical_schedule.id,
        conflict_types=None,  # All types
    )

    # Task 2: Validate ACGME compliance
    compliance_task = validate_schedule(
        start_date=min(assignment.date, candidate.target_assignment.date),
        end_date=max(assignment.date, candidate.target_assignment.date) + timedelta(days=30),
    )

    # Task 3: Check contingency impact
    contingency_task = run_contingency_analysis(
        start_date=assignment.date,
        end_date=assignment.date + timedelta(days=30),
    )

    # Wait for all tasks
    conflicts, compliance, contingency = await asyncio.gather(
        conflicts_task, compliance_task, contingency_task
    )

    # Calculate impact metrics
    impact = calculate_impact(
        original_schedule=get_current_schedule(),
        hypothetical_schedule=hypothetical_schedule,
        conflicts=conflicts,
        compliance=compliance,
        contingency=contingency,
    )

    return Phase3Result(
        swap_id=f"swap-{requester_id}-{assignment_id}",
        compliance_maintained=compliance.is_compliant and conflicts.critical_count == 0,
        new_conflicts=conflicts.conflicts,
        impact_on_others=impact.affected_people,
        contingency_impact=contingency,
        fallback_plans=generate_fallback_plans(conflicts),
        approval_recommendation="APPROVE" if compliance_maintained else "REVIEW",
    )
```

**Impact Assessment Output**:
```json
{
  "swap_id": "swap-FAC-PD-assign-001",
  "hypothetical_schedule_created": true,
  "compliance_maintained": true,
  "acgme_check": {
    "result": "compliant",
    "requester_hours": {
      "before": [62, 58, 65],
      "after": [60, 58, 65]
    },
    "candidate_hours": {
      "before": [59, 62, 61],
      "after": [61, 62, 61]
    }
  },
  "conflicts_check": {
    "new_conflicts": 0,
    "existing_conflicts_resolved": 0,
    "status": "no_new_issues"
  },
  "contingency_impact": {
    "n1_gaps_before": 3,
    "n1_gaps_after": 3,
    "no_impact": true
  },
  "affected_people": [],
  "fallback_plans": [
    {
      "scenario": "If swap executed and requester absent next week",
      "coverage": "Adequate",
      "workarounds": ["Use backup faculty pool"]
    }
  ],
  "approval_ready": true,
  "recommendation": "APPROVE - Swap maintains compliance, no negative impact"
}
```

**Phase 3 Validation Checks**:

| Check | Passing Criteria | Failure Action |
|-------|-----------------|----------------|
| **ACGME Compliance** | is_compliant = true | Show violations, request revise |
| **New Conflicts** | critical_count = 0 | List conflicts, offer resolution |
| **Contingency Impact** | n1_gaps unchanged | Warn but may approve |
| **No Negative Externalities** | affected_people < 3 | Review impact on affected staff |

---

## Phase 4: Human Review & Approval (Varies)

**Goals**:
- Get confirmation from both parties
- Obtain coordinator approval
- Document decision rationale

**Process**:

```
Step 1: Mutual Consent
  ├─ Notify Requester
  │  ├─ Show top 3 candidates
  │  ├─ Show impact assessment
  │  └─ Request selection + confirm
  │
  └─ Notify Candidate (if auto-matched)
     ├─ Show swap details
     ├─ Show impact assessment
     └─ Request confirmation

Step 2: Coordinator Review (if needed)
  ├─ If mutual + compliant → Auto-approve (fast path)
  └─ Otherwise → Manual review + approval

Step 3: Document Decision
  ├─ Record approval timestamp
  ├─ Log approver identity
  └─ Capture any comments/rationale
```

**Approval Request Format**:
```json
{
  "swap_request_id": "swap-FAC-PD-assign-001",
  "stage": "MUTUAL_CONSENT",
  "requester": {
    "id": "FAC-PD",
    "action_required": true,
    "prompt": "Confirm swap with FAC-005? Your Inpatient AM on 2025-12-22 for their AM on 2025-12-23"
  },
  "candidate": {
    "id": "FAC-005",
    "action_required": true,
    "prompt": "Confirm swap with FAC-PD? Your Inpatient AM on 2025-12-23 for their AM on 2025-12-22"
  },
  "impact_summary": {
    "your_workload_change": "-2 hours (62→60)",
    "their_workload_change": "+2 hours (59→61)",
    "compliance_impact": "No issues",
    "others_affected": 0
  },
  "next_step": "Waiting for mutual consent"
}
```

**Approval Paths**:

```
Path A: Fast Approval (60 seconds)
  Requester selects FAC-005
    ↓
  Mutual benefit detected (FAC-005 also wants to swap)
    ↓
  Compliance verified, no impact on others
    ↓
  AUTO-APPROVE (Coordinator notified, can override)
    ↓
  Execute swap

Path B: Manual Approval (5-15 minutes)
  Requester selects FAC-002
    ↓
  FAC-002 contacted, requests confirmation
    ↓
  One party needs more time to decide
    ↓
  Waiting for mutual consent (up to 24h)
    ↓
  Coordinator escalation if needed

Path C: Escalation (1-2 hours)
  Compliance issue detected
    ↓
  Coordinator manual review
    ↓
  Decision: Approve with conditions / Reject / Request modification
    ↓
  Outcome documented
```

---

## Phase 5: Execution & Audit (< 1 second)

**Goals**:
- Apply swap to schedule
- Log audit trail
- Notify all parties
- Store for future reference

**Execution**:
```python
async def phase_5_execution(
    swap_request_id: str,
    approved_by: str,
) -> Phase5Result:
    """Execute approved swap and log audit trail."""

    # Step 1: Retrieve approval
    approval = await get_swap_approval(swap_request_id)
    if approval.status != "APPROVED":
        raise UnapprovedSwapError(f"Swap {swap_request_id} not approved")

    # Step 2: Create backup of schedule (for rollback)
    backup_id = await backup_schedule(approval.schedule_id)

    # Step 3: Apply swap to database
    try:
        swap_result = await execute_swap_in_database(
            requester_id=approval.requester_id,
            assignment_id=approval.assignment_id,
            candidate_id=approval.candidate_id,
            target_assignment_id=approval.target_assignment_id,
            audit_user=approved_by,
        )
    except Exception as e:
        # Rollback on failure
        await rollback_schedule(backup_id)
        raise SwapExecutionError(f"Swap failed: {e}")

    # Step 4: Log audit trail
    audit_log = await log_swap_audit(
        swap_request_id=swap_request_id,
        requester_id=approval.requester_id,
        candidate_id=approval.candidate_id,
        status="EXECUTED",
        executed_by=approved_by,
        executed_at=datetime.now(),
        backup_id=backup_id,  # For rollback if needed
        impact_summary=approval.impact_assessment,
    )

    # Step 5: Notify parties
    notifications = await notify_parties(
        requester_id=approval.requester_id,
        candidate_id=approval.candidate_id,
        swap_details=swap_result,
        effective_date=approval.effective_date,
    )

    # Step 6: Update metrics
    await update_swap_metrics(swap_request_id, "executed")

    return Phase5Result(
        swap_id=swap_request_id,
        status="EXECUTED",
        backup_id=backup_id,
        audit_log_id=audit_log.id,
        notifications_sent=len(notifications),
        rollback_available_until=datetime.now() + timedelta(hours=24),
    )
```

**Execution Output**:
```json
{
  "swap_id": "swap-FAC-PD-assign-001",
  "status": "EXECUTED",
  "execution_timestamp": "2025-12-31T14:30:00Z",
  "executed_by": "coordinator-001",
  "backup_created": true,
  "backup_id": "backup-schedule-2025-12-31-143000",
  "rollback_available_until": "2026-01-01T14:30:00Z",
  "audit_log": {
    "id": "audit-swap-001",
    "entries": [
      {
        "timestamp": "2025-12-31T14:30:00Z",
        "action": "swap_executed",
        "requester_id": "FAC-PD",
        "candidate_id": "FAC-005",
        "old_assignments": [...],
        "new_assignments": [...],
        "reason": "Mutual swap request approved"
      }
    ]
  },
  "notifications": {
    "sent_to": ["FAC-PD", "FAC-005"],
    "count": 2,
    "delivery_status": "success"
  },
  "next_actions": [
    "Monitor next 24h for issues",
    "Can rollback if problems detected"
  ]
}
```

**Audit Trail Fields**:
```
swap_id | swap-FAC-PD-assign-001
requester | FAC-PD
candidate | FAC-005
request_date | 2025-12-28
approval_date | 2025-12-31
execution_date | 2025-12-31
executed_by | coordinator-001
status | EXECUTED
impact_summary | Minimal (2h workload shift)
backup_id | backup-schedule-2025-12-31-143000
rollback_deadline | 2026-01-01T14:30:00Z
```

---

## Rollback Capability (24-hour window)

**Purpose**: Undo swap if unforeseen consequences emerge

```python
async def rollback_swap(
    swap_id: str,
    reason: str,
    requested_by: str,
) -> RollbackResult:
    """Roll back a swap within 24h window."""

    swap = await get_swap(swap_id)
    if datetime.now() > swap.rollback_deadline:
        raise RollbackExpiredError("Swap outside 24h rollback window")

    # Restore schedule from backup
    await restore_schedule(swap.backup_id)

    # Log rollback
    await log_rollback(
        swap_id=swap_id,
        reason=reason,
        requested_by=requested_by,
    )

    # Notify parties
    await notify_parties_of_rollback(swap)

    return RollbackResult(status="ROLLED_BACK")
```

---

## Error Handling & Failure Modes

| Failure Mode | Trigger | Recovery |
|--------------|---------|----------|
| **Invalid Requester** | Phase 1 | Reject immediately |
| **No Candidates** | Phase 2 | Notify requester, suggest alternatives |
| **Compliance Violation** | Phase 3 | Show violation, request adjustment |
| **Mutual Consent Timeout** | Phase 4 | Cancel after 24h, allow restart |
| **Execution Failure** | Phase 5 | Auto-rollback to backup, alert coordinator |
| **Notification Failure** | Phase 5 | Retry 3x, log failure |

---

## Performance Targets

| Phase | Duration | Critical |
|-------|----------|----------|
| 1: Validation | 0.5s | High |
| 2: Candidates | 0.5s | Medium |
| 3: Impact | 1.0s | High |
| 4: Review | 5-300s (varies) | Medium |
| 5: Execution | 0.5s | Critical |
| **Total** | **2-5s + review** | |

---

## Configuration Variants

### Quick Swap (Express)
```python
"mode": "express",
"skip_contingency_check": True,
"auto_approve_mutual": True,
"timeout": 1.0,
```

### Standard Swap (Default)
```python
"mode": "standard",
"full_validation": True,
"contingency_check": True,
"timeout": 3.0,
```

### Audit Swap (Thorough)
```python
"mode": "audit",
"full_validation": True,
"contingency_check": True,
"require_manual_approval": True,
"timeout": 10.0,
```

---

## Success Metrics

After swap execution, measure:

```
✓ Swap executed without errors
✓ Both parties satisfied (survey)
✓ Schedule remains compliant
✓ No new conflicts introduced
✓ Contingency unchanged
✓ All notifications delivered
✓ Audit trail complete
```

---

**Last Updated**: 2025-12-31
**Version**: 1.0
**Safety**: TIER 2 (preview + approval required)
**Rollback**: 24-hour window available
