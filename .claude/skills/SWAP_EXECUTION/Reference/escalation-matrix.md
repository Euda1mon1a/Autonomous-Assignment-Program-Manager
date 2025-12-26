# Escalation Matrix

Decision tree for when to involve human oversight in swap execution.

## Overview

Not all swaps can be auto-approved. Some require **human judgment** due to:
- Regulatory complexity (ACGME edge cases)
- Fairness considerations (equity, morale)
- Sensitive circumstances (medical, personal)
- System-wide impact (resilience degradation)

This matrix defines **who approves what** and **when to escalate**.

---

## Decision Authority Matrix

| Swap Scenario | Auto-Approve | Coordinator | Faculty/PD | Architect |
|---------------|--------------|-------------|------------|-----------|
| **Clean swap (all checks pass)** | ✅ | - | - | - |
| **Tier 2 warning (non-critical)** | ✅ with notification | - | - | - |
| **Tier 2 violation (critical)** | - | ✅ | - | - |
| **ACGME edge case** | - | ✅ | Review | - |
| **Sensitive reason (medical, accommodation)** | - | - | ✅ | - |
| **Fellowship interview** | - | - | ✅ | - |
| **Fairness violation (>2 std dev)** | - | ✅ | - | - |
| **Resilience degradation >10%** | - | - | - | ✅ |
| **Multiple failed attempts (3+)** | - | ✅ | - | - |
| **Moonlighting conflict (within limits)** | - | ✅ | - | - |
| **Coverage gap (replacement available)** | - | ✅ | - | - |
| **Coverage gap (no replacement)** | - | - | ✅ | - |
| **Dispute between parties** | - | ✅ | ✅ (mediation) | - |
| **Rollback request >24h** | - | - | ✅ | - |
| **System-wide impact (>10 assignments)** | - | - | - | ✅ |

**Legend:**
- ✅ = Decision authority
- Review = Advisory input
- `-` = Not involved

---

## Escalation Tier Definitions

### Tier 1: Auto-Approve (No Human Involvement)

**Criteria:**
- All Tier 1 hard constraints PASS
- All Tier 2 soft constraints PASS (or only non-critical warnings)
- Tier 3 resilience impact <5%
- Standard swap reasons (conference, PTO, schedule preference)
- Both parties within normal swap balance range

**Process:**
```python
def is_auto_approvable(safety_result: SafetyCheckResult) -> bool:
    """
    Determine if swap can be auto-approved.

    Returns:
        True if meets auto-approval criteria, False otherwise
    """
    # Check Tier 1 (hard constraints)
    if safety_result.tier1_violations:
        return False  # Any hard constraint violation = no auto-approve

    # Check Tier 2 (soft constraints)
    critical_tier2 = [
        "BACK_TO_BACK_FMIT",
        "COVERAGE_GAP",
        "EXTERNAL_CONFLICT"
    ]
    if any(w.code in critical_tier2 for w in safety_result.tier2_warnings):
        return False  # Critical soft constraint = escalate

    # Check Tier 3 (resilience)
    if safety_result.tier3_metrics.get("utilization_delta", 0) > 0.05:
        return False  # >5% degradation = escalate

    # Check reason sensitivity
    sensitive_reasons = [
        "fellowship_interview",
        "medical_accommodation",
        "family_emergency"
    ]
    if any(r in swap_request.reason.lower() for r in sensitive_reasons):
        return False  # Sensitive = escalate for privacy

    return True  # All checks passed, auto-approve

# Execute if auto-approvable
if is_auto_approvable(safety_result):
    execute_swap_immediately(swap_request)
else:
    escalate_for_approval(swap_request, safety_result)
```

---

### Tier 2: Coordinator Approval

**When to escalate to Coordinator:**

#### 2.1 Tier 2 Soft Constraint Violations

```python
COORDINATOR_ESCALATION_CODES = [
    "BACK_TO_BACK_FMIT",      # Burnout risk
    "COVERAGE_GAP",            # Staffing concern
    "IMMINENT_SWAP",           # <7 days notice
    "MOONLIGHTING_CONFLICT",   # External work overlap
    "FAIRNESS_VIOLATION"       # Equity concern
]

if any(w.code in COORDINATOR_ESCALATION_CODES for w in safety_result.tier2_warnings):
    escalate_to_coordinator(
        swap_request=swap_request,
        reason=f"Tier 2 violation: {w.code}",
        safety_result=safety_result
    )
```

**Coordinator decision criteria:**
- **Back-to-back FMIT:** Approve if faculty explicitly confirms willingness
- **Coverage gap:** Approve if replacement identified
- **Imminent swap:** Approve if handoff plan provided
- **Moonlighting conflict:** Approve if within 80-hour limit
- **Fairness violation:** Approve if justified (e.g., medical reason)

**Approval SLA:** 4 hours (business hours)

---

#### 2.2 Multiple Failed Attempts

```python
def check_failed_attempt_pattern(person_id: UUID) -> int:
    """
    Count failed swap attempts in last 30 days.

    Returns:
        Number of failed attempts
    """
    thirty_days_ago = date.today() - timedelta(days=30)

    failed_count = db.query(SwapRecord).filter(
        SwapRecord.requested_by_id == person_id,
        SwapRecord.requested_at >= thirty_days_ago,
        SwapRecord.status.in_([SwapStatus.REJECTED, SwapStatus.CANCELLED])
    ).count()

    return failed_count

failed_attempts = check_failed_attempt_pattern(swap_request.requested_by.id)

if failed_attempts >= 3:
    escalate_to_coordinator(
        swap_request=swap_request,
        reason=f"Pattern: {failed_attempts} failed swap attempts in 30 days",
        suggestion="Possible scheduling issue or user confusion. Review needed."
    )
```

**Coordinator action:**
- Review rejection reasons
- Check if systemic scheduling issue
- Provide user guidance if confusion
- Manually facilitate swap if justified

---

#### 2.3 Dispute Resolution

```python
if swap_request.status == SwapStatus.DISPUTED:
    escalate_to_coordinator(
        swap_request=swap_request,
        reason="Parties cannot agree on swap terms",
        parties=[
            swap_request.source_faculty.name,
            swap_request.target_faculty.name
        ],
        required_action="Mediation"
    )
```

**Coordinator mediation process:**
1. Interview both parties separately
2. Identify root cause of dispute
3. Propose compromise solution
4. Facilitate agreement or rollback

---

### Tier 3: Faculty/Program Director Approval

**When to escalate to Faculty/PD:**

#### 3.1 Sensitive Reasons (Privacy/Accommodation)

```python
SENSITIVE_REASON_KEYWORDS = [
    "fellowship_interview",
    "medical_accommodation",
    "family_emergency",
    "bereavement",
    "mental_health",
    "disability_accommodation"
]

if any(keyword in swap_request.reason.lower() for keyword in SENSITIVE_REASON_KEYWORDS):
    escalate_to_program_director(
        swap_request=swap_request,
        reason="Sensitive circumstances requiring PD discretion",
        privacy_level="HIGH",
        required_action="Private approval with source faculty"
    )
```

**Why PD approval?**
- **Privacy:** Protect resident's sensitive information
- **Fairness:** Ensure accommodations don't create inequity
- **Policy:** Some reasons require command notification
- **Legal:** Medical/disability accommodations have legal implications

**PD decision criteria:**
- Verify legitimacy of reason (may require documentation)
- Ensure fairness to other residents
- Document approval for legal compliance
- Notify chain of command if required

**Approval SLA:** 24 hours (sensitive timing)

---

#### 3.2 Fellowship Interviews

```python
if "fellowship" in swap_request.reason.lower() or "interview" in swap_request.reason.lower():
    escalate_to_program_director(
        swap_request=swap_request,
        reason="Fellowship interview - requires PD approval for fairness",
        required_action="Verify interview legitimacy and approve"
    )
```

**Why PD approval?**
- **Fairness:** All residents should get equal interview opportunities
- **Verification:** Prevent abuse of "interview" excuse
- **Support:** PD can provide reference letter, scheduling assistance
- **Tracking:** Monitor fellowship application patterns

**PD approval process:**
1. Verify fellowship interview is legitimate (program, date)
2. Ensure resident isn't exceeding reasonable interview count
3. Approve swap and note in resident file
4. Offer to write recommendation if appropriate

---

#### 3.3 Coverage Gap with No Replacement

```python
if coverage_gap_detected and not replacement_available:
    escalate_to_program_director(
        swap_request=swap_request,
        reason="Critical coverage gap - no replacement faculty available",
        impact="Week {swap_request.source_week} would have zero FMIT coverage",
        required_action="PD must find replacement or deny swap"
    )
```

**PD options:**
- Recruit volunteer from available pool
- Reassign another faculty member
- Split FMIT week between multiple faculty
- Deny swap if coverage cannot be ensured

---

### Tier 4: Architect/System Owner Approval

**When to escalate to Architect:**

#### 4.1 Resilience Degradation >10%

```python
if safety_result.tier3_metrics.get("utilization_delta", 0) > 0.10:
    escalate_to_architect(
        swap_request=swap_request,
        reason=f"Resilience degradation: {safety_result.tier3_metrics['utilization_delta']:.1%}",
        impact="System-wide utilization would increase significantly",
        metrics=safety_result.tier3_metrics
    )
```

**Why Architect approval?**
- **System health:** Large impact on overall schedule resilience
- **Cascade risk:** Swap might trigger cascade failure
- **N-1 violation:** Might break contingency planning
- **Policy decision:** Trade-off between individual flexibility and system stability

**Architect decision criteria:**
- Review alternative weeks with lower impact
- Check if degradation is temporary or sustained
- Assess N-1/N-2 contingency impact
- Approve only if benefits outweigh risks

---

#### 4.2 Large Blast Radius (>10 Assignments Affected)

```python
from app.resilience.blast_radius import calculate_blast_radius

blast_radius = calculate_blast_radius(swap_request, max_depth=3)

if blast_radius.affected_assignments > 10:
    escalate_to_architect(
        swap_request=swap_request,
        reason=f"Large blast radius: {blast_radius.affected_assignments} assignments affected",
        impact="Cascading changes across multiple weeks/rotations",
        affected_entities=blast_radius.affected_persons
    )
```

**Why Architect approval?**
- **Complexity:** Large cascading changes hard to predict
- **Risk:** Higher chance of unintended consequences
- **Rollback difficulty:** Harder to undo if problems arise

**Architect decision:**
- Simulate full impact before approving
- Require detailed rollback plan
- Consider phased execution
- Approve only if cascade is well-understood

---

## Escalation Notification Templates

### Template 1: Coordinator Escalation

```python
def notify_coordinator_approval_needed(swap_request: StructuredSwapRequest, reason: str):
    """Send approval request to coordinator."""
    subject = f"Swap Approval Needed: {swap_request.source_faculty.name} ↔ {swap_request.target_faculty.name}"

    body = f"""
    A swap request requires your approval:

    **Request Details:**
    - Request ID: {swap_request.request_id}
    - Type: {swap_request.swap_type.value}
    - Source: {swap_request.source_faculty.name} (week {swap_request.source_week})
    - Target: {swap_request.target_faculty.name} (week {swap_request.target_week or 'ABSORB'})
    - Reason: {swap_request.reason}

    **Escalation Reason:**
    {reason}

    **Action Required:**
    Review and approve/reject within 4 business hours.

    **Approve:** [Approve Link]
    **Reject:** [Reject Link]
    **View Details:** [Dashboard Link]
    """

    send_email(to=COORDINATOR_EMAIL, subject=subject, body=body)
    send_slack_alert(channel="#swap-approvals", message=body)
```

---

### Template 2: Program Director Escalation

```python
def notify_pd_approval_needed(swap_request: StructuredSwapRequest, reason: str):
    """Send approval request to Program Director."""
    subject = f"PD Approval Required: Swap Request {swap_request.request_id}"

    body = f"""
    A swap request requires Program Director approval due to sensitive circumstances:

    **Request Details:**
    - Request ID: {swap_request.request_id}
    - Source: {swap_request.source_faculty.name}
    - Week: {swap_request.source_week}
    - Reason: [REDACTED - See private dashboard]

    **Escalation Reason:**
    {reason}

    **Privacy Notice:**
    This request involves sensitive information. View details in secure dashboard.

    **Action Required:**
    Review and approve/reject within 24 hours.

    **View Secure Details:** [PD Dashboard Link]
    """

    send_email(to=PROGRAM_DIRECTOR_EMAIL, subject=subject, body=body, priority="HIGH")
```

---

### Template 3: Architect Escalation

```python
def notify_architect_approval_needed(swap_request: StructuredSwapRequest, metrics: dict):
    """Send approval request to Architect."""
    subject = f"System Impact Review: Swap {swap_request.request_id}"

    body = f"""
    A swap request requires Architect review due to significant system impact:

    **Request Details:**
    - Request ID: {swap_request.request_id}
    - Source: {swap_request.source_faculty.name} → {swap_request.target_faculty.name}
    - Week: {swap_request.source_week}

    **System Impact:**
    - Utilization Delta: {metrics['utilization_delta']:.1%}
    - Blast Radius: {metrics['blast_radius']} assignments
    - N-1 Status: {metrics['n1_contingency']}
    - Resilience Score Change: {metrics['resilience_delta']}

    **Risk Assessment:**
    System-wide resilience may degrade. Manual review required.

    **Action Required:**
    Approve only if impact is acceptable.

    **View Impact Analysis:** [Architect Dashboard Link]
    """

    send_email(to=ARCHITECT_EMAIL, subject=subject, body=body, priority="HIGH")
    create_jira_ticket(
        project="SCHEDULER",
        issue_type="System Review",
        summary=subject,
        description=body
    )
```

---

## Escalation SLAs

| Escalation Tier | SLA | After-Hours Handling |
|----------------|-----|---------------------|
| Coordinator | 4 business hours | Next business day |
| Program Director | 24 hours | On-call PD notified |
| Architect | 48 hours | Email only (non-urgent) |

**Emergency escalation:**
- Coverage gaps affecting <24h from now → Immediate phone call to PD
- System-critical issue → Page on-call engineer

---

## Approval Tracking

All approvals must be logged:

```python
@dataclass
class ApprovalRecord:
    """Track human approval decisions."""

    swap_id: UUID
    approver_role: str  # "coordinator" | "program_director" | "architect"
    approver_id: UUID
    approver_name: str
    decision: str  # "approved" | "rejected"
    decision_timestamp: datetime
    decision_notes: str
    escalation_reason: str

# Store in database
def record_approval(approval: ApprovalRecord):
    db.add(SwapApproval(
        swap_id=approval.swap_id,
        approver_id=approval.approver_id,
        approver_role=approval.approver_role,
        decision=approval.decision,
        decided_at=approval.decision_timestamp,
        notes=approval.decision_notes
    ))
    db.commit()
```

---

## Override Procedures

In rare cases, **emergency override** may be needed:

```python
def emergency_override(
    swap_id: UUID,
    override_by: User,
    reason: str,
    authorization: str  # Command approval reference
) -> None:
    """
    Execute swap despite validation failures.

    CAUTION: Use only for genuine emergencies with command authorization.

    Args:
        swap_id: Swap to override
        override_by: User authorizing override (must be admin/PD)
        reason: Emergency justification
        authorization: Command approval reference (e.g., "PD verbal approval 2025-01-15")
    """
    if override_by.role not in ["admin", "program_director"]:
        raise PermissionError("Only admin/PD can emergency override")

    logger.critical(
        f"EMERGENCY OVERRIDE: Swap {swap_id} executed despite validation failures. "
        f"Reason: {reason}. Authorization: {authorization}",
        extra={
            "swap_id": str(swap_id),
            "override_by": str(override_by.id),
            "reason": reason,
            "authorization": authorization
        }
    )

    # Execute swap with override flag
    execute_swap_with_override(
        swap_id=swap_id,
        override_by=override_by.id,
        override_reason=reason,
        override_authorization=authorization
    )

    # Alert command
    notify_chain_of_command(
        severity="EMERGENCY",
        message=f"Schedule swap executed with emergency override: {reason}"
    )
```

**Override usage (last 12 months):** Target <5 per year

---

## Quick Reference

### Decision Flowchart

```
[Swap Request]
    ↓
[All checks PASS?]
    ├─ YES → Auto-Approve ✅
    ├─ NO → Tier 2 violation?
           ├─ YES → Coordinator ✅
           ├─ NO → Sensitive reason?
                  ├─ YES → Program Director ✅
                  ├─ NO → System impact >10%?
                         ├─ YES → Architect ✅
                         └─ NO → Reject ❌
```

### Contact Information

| Role | Email | Phone | Slack |
|------|-------|-------|-------|
| Coordinator | coordinator@... | (555) 123-4567 | @coordinator |
| Program Director | pd@... | (555) 123-4568 | @program-director |
| Architect | architect@... | (555) 123-4569 | @system-architect |
| On-Call (After Hours) | oncall@... | (555) 123-4570 | @oncall |
