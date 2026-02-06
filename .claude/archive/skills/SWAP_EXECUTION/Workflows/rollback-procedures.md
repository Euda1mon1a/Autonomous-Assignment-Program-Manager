# Rollback Procedures

Phase 5 of swap execution: Safely undo executed swaps within the 24-hour rollback window.

## Purpose

Provide a **safety net** for swap execution by allowing reversal within 24 hours if:
- Mistake was made in request
- Conflict discovered post-execution
- Dispute arises between parties
- Data integrity issue detected

## Rollback Window

**Duration:** 24 hours from `executed_at` timestamp

```python
ROLLBACK_WINDOW_HOURS = 24

def is_rollback_eligible(swap: SwapRecord) -> bool:
    """
    Check if swap can still be rolled back.

    Args:
        swap: SwapRecord to check

    Returns:
        bool: True if within rollback window and status is EXECUTED
    """
    if swap.status != SwapStatus.EXECUTED:
        return False

    if not swap.executed_at:
        return False

    time_since_execution = datetime.utcnow() - swap.executed_at
    rollback_window = timedelta(hours=ROLLBACK_WINDOW_HOURS)

    return time_since_execution <= rollback_window
```

**Why 24 hours?**
- Long enough to catch mistakes
- Short enough to prevent disruption
- Standard industry practice for "undo" operations
- Balances flexibility with stability

---

## Snapshot Creation Before Execution

**Critical:** Before executing any swap, create a snapshot of the current state for easy restoration.

### What to Snapshot

```python
from dataclasses import dataclass
from datetime import date
from uuid import UUID

@dataclass
class SwapSnapshot:
    """
    Pre-execution snapshot for rollback capability.

    Stores the exact state of assignments before swap execution,
    enabling perfect restoration if rollback is needed.
    """

    swap_id: UUID
    created_at: datetime

    # Original assignments for source week
    source_week_assignments: list[dict]
    """
    Example:
    [
        {
            "assignment_id": "uuid-1",
            "block_id": "uuid-block-1",
            "person_id": "uuid-john",  # Original person
            "rotation": "FMIT",
            "date": "2025-02-03",
            "session": "AM"
        },
        # ... 13 more (7 days × 2 sessions)
    ]
    """

    # Original assignments for target week (if one-to-one swap)
    target_week_assignments: list[dict] | None

    # Original call assignments (Friday/Saturday)
    call_assignments: list[dict]
    """
    Example:
    [
        {
            "call_assignment_id": "uuid-call-1",
            "person_id": "uuid-john",  # Original person on call
            "date": "2025-02-07"  # Friday
        },
        {
            "call_assignment_id": "uuid-call-2",
            "person_id": "uuid-john",
            "date": "2025-02-08"  # Saturday
        }
    ]
    """


def create_swap_snapshot(db: Session, swap_request: StructuredSwapRequest) -> SwapSnapshot:
    """
    Create pre-execution snapshot for rollback.

    Args:
        db: Database session
        swap_request: Validated swap request

    Returns:
        SwapSnapshot: Complete snapshot of current state
    """
    from app.models.block import Block
    from app.models.assignment import Assignment
    from app.models.call_assignment import CallAssignment
    from sqlalchemy.orm import selectinload

    # Calculate week boundaries
    source_week_end = swap_request.source_week + timedelta(days=6)

    # Snapshot source week assignments
    source_blocks = (
        db.query(Block)
        .options(selectinload(Block.assignments))
        .filter(
            Block.date >= swap_request.source_week,
            Block.date <= source_week_end
        )
        .all()
    )

    source_week_assignments = []
    for block in source_blocks:
        for assignment in block.assignments:
            source_week_assignments.append({
                "assignment_id": str(assignment.id),
                "block_id": str(block.id),
                "person_id": str(assignment.person_id),
                "rotation": assignment.rotation,
                "date": block.date.isoformat(),
                "session": block.session
            })

    # Snapshot target week assignments (if one-to-one)
    target_week_assignments = None
    if swap_request.target_week:
        target_week_end = swap_request.target_week + timedelta(days=6)
        target_blocks = (
            db.query(Block)
            .options(selectinload(Block.assignments))
            .filter(
                Block.date >= swap_request.target_week,
                Block.date <= target_week_end
            )
            .all()
        )

        target_week_assignments = []
        for block in target_blocks:
            for assignment in block.assignments:
                target_week_assignments.append({
                    "assignment_id": str(assignment.id),
                    "block_id": str(block.id),
                    "person_id": str(assignment.person_id),
                    "rotation": assignment.rotation,
                    "date": block.date.isoformat(),
                    "session": block.session
                })

    # Snapshot call assignments
    call_assignments_snapshot = []
    current_date = swap_request.source_week
    while current_date <= source_week_end:
        if current_date.weekday() in [4, 5]:  # Friday or Saturday
            call_records = (
                db.query(CallAssignment)
                .filter(CallAssignment.date == current_date)
                .all()
            )
            for call in call_records:
                call_assignments_snapshot.append({
                    "call_assignment_id": str(call.id),
                    "person_id": str(call.person_id),
                    "date": current_date.isoformat()
                })
        current_date += timedelta(days=1)

    snapshot = SwapSnapshot(
        swap_id=swap_request.request_id,
        created_at=datetime.utcnow(),
        source_week_assignments=source_week_assignments,
        target_week_assignments=target_week_assignments,
        call_assignments=call_assignments_snapshot
    )

    # Persist snapshot to database or cache
    # (Could use Redis for 24h TTL, or dedicated snapshot table)
    store_snapshot(snapshot)

    return snapshot
```

---

## Rollback Triggers

Rollback can be triggered by:

### 1. Manual Request (Most Common)

Faculty/coordinator realizes mistake and requests rollback:

```http
POST /api/swap/{swap_id}/rollback
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
    "reason": "Resident reported schedule conflict with clinic"
}
```

### 2. Automatic Detection (System-Initiated)

System detects critical issue post-execution:

```python
def check_post_execution_compliance(swap_id: UUID) -> None:
    """
    Verify swap didn't introduce undetected violations.

    Run asynchronously 5 minutes after execution to catch issues
    that weren't apparent during pre-execution validation.
    """
    from app.services.acgme_validator import ACGMEValidator

    swap = db.query(SwapRecord).filter(SwapRecord.id == swap_id).first()

    # Re-run full ACGME validation
    validator = ACGMEValidator(db)
    result = validator.validate_week(swap.source_week)

    if result.has_violations:
        logger.critical(
            f"Post-execution validation failed for swap {swap_id}: "
            f"{result.violations}"
        )

        # Auto-rollback critical violations
        if any(v.severity == "critical" for v in result.violations):
            auto_rollback(
                swap_id=swap_id,
                reason=f"Auto-rollback: Critical ACGME violation detected - {result.violations[0].message}"
            )
```

### 3. Dispute Resolution

Both parties can't agree on the swap outcome:

```python
def initiate_dispute_rollback(swap_id: UUID, initiated_by: User) -> None:
    """
    Handle swap dispute by rolling back and escalating.

    Args:
        swap_id: Swap to rollback
        initiated_by: User initiating dispute
    """
    rollback_result = rollback_swap(
        swap_id=swap_id,
        reason=f"Dispute initiated by {initiated_by.name}",
        rolled_back_by_id=initiated_by.id
    )

    if rollback_result.success:
        # Escalate to coordinator for mediation
        escalate_to_coordinator(
            swap_id=swap_id,
            reason="Dispute requires mediation",
            parties=[swap.source_faculty, swap.target_faculty]
        )
```

---

## State Restoration Process

### Step 1: Verify Eligibility

```python
def verify_rollback_eligibility(swap_id: UUID) -> tuple[bool, str]:
    """
    Check if rollback is allowed.

    Returns:
        (eligible, reason): True if can rollback, else False with reason
    """
    swap = db.query(SwapRecord).filter(SwapRecord.id == swap_id).first()

    if not swap:
        return False, "Swap record not found"

    if swap.status != SwapStatus.EXECUTED:
        return False, f"Swap status is {swap.status}, must be EXECUTED"

    if not swap.executed_at:
        return False, "Swap has no execution timestamp"

    time_since = datetime.utcnow() - swap.executed_at
    if time_since > timedelta(hours=ROLLBACK_WINDOW_HOURS):
        return False, f"Rollback window expired ({time_since.total_seconds() / 3600:.1f} hours ago)"

    return True, "Eligible"
```

### Step 2: Load Snapshot

```python
def load_snapshot(swap_id: UUID) -> SwapSnapshot:
    """
    Load pre-execution snapshot for rollback.

    Args:
        swap_id: Swap to rollback

    Returns:
        SwapSnapshot: Original state before execution

    Raises:
        ValueError: If snapshot not found
    """
    snapshot = retrieve_snapshot(swap_id)

    if not snapshot:
        raise ValueError(
            f"Snapshot not found for swap {swap_id}. "
            f"Cannot safely rollback without snapshot."
        )

    return snapshot
```

### Step 3: Restore Database State

```python
def restore_from_snapshot(db: Session, snapshot: SwapSnapshot) -> None:
    """
    Restore all assignments to pre-swap state.

    Args:
        db: Database session
        snapshot: Pre-execution snapshot

    Raises:
        IntegrityError: If restoration fails
    """
    from app.models.assignment import Assignment
    from app.models.call_assignment import CallAssignment

    try:
        # Restore source week assignments
        for assignment_data in snapshot.source_week_assignments:
            assignment = db.query(Assignment).filter(
                Assignment.id == assignment_data["assignment_id"]
            ).first()

            if assignment:
                assignment.person_id = UUID(assignment_data["person_id"])
                assignment.notes = "Restored from swap rollback"

        # Restore target week assignments (if one-to-one)
        if snapshot.target_week_assignments:
            for assignment_data in snapshot.target_week_assignments:
                assignment = db.query(Assignment).filter(
                    Assignment.id == assignment_data["assignment_id"]
                ).first()

                if assignment:
                    assignment.person_id = UUID(assignment_data["person_id"])
                    assignment.notes = "Restored from swap rollback"

        # Restore call assignments
        for call_data in snapshot.call_assignments:
            call = db.query(CallAssignment).filter(
                CallAssignment.id == call_data["call_assignment_id"]
            ).first()

            if call:
                call.person_id = UUID(call_data["person_id"])

        db.flush()
        logger.info(f"Successfully restored state from snapshot {snapshot.swap_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to restore snapshot {snapshot.swap_id}: {e}", exc_info=True)
        raise
```

### Step 4: Update SwapRecord Status

```python
def finalize_rollback(
    db: Session,
    swap_id: UUID,
    reason: str,
    rolled_back_by_id: UUID
) -> None:
    """
    Update swap record to reflect rollback.

    Args:
        db: Database session
        swap_id: Swap that was rolled back
        reason: Why rollback was performed
        rolled_back_by_id: User who initiated rollback
    """
    swap = db.query(SwapRecord).filter(SwapRecord.id == swap_id).first()

    swap.status = SwapStatus.ROLLED_BACK
    swap.rolled_back_at = datetime.utcnow()
    swap.rolled_back_by_id = rolled_back_by_id
    swap.rollback_reason = reason

    db.commit()

    logger.info(
        f"Swap {swap_id} rolled back successfully. "
        f"Reason: {reason}. "
        f"By user: {rolled_back_by_id}"
    )
```

---

## Post-Rollback Validation

After rollback, **verify state was correctly restored**:

```python
def validate_rollback(snapshot: SwapSnapshot) -> bool:
    """
    Verify database state matches snapshot after rollback.

    Args:
        snapshot: Original snapshot to compare against

    Returns:
        bool: True if state matches, False if discrepancies found
    """
    from app.models.assignment import Assignment

    # Check source week assignments
    for assignment_data in snapshot.source_week_assignments:
        assignment = db.query(Assignment).filter(
            Assignment.id == assignment_data["assignment_id"]
        ).first()

        if not assignment:
            logger.error(f"Assignment {assignment_data['assignment_id']} not found after rollback")
            return False

        if str(assignment.person_id) != assignment_data["person_id"]:
            logger.error(
                f"Assignment {assignment.id} person mismatch: "
                f"expected {assignment_data['person_id']}, "
                f"got {assignment.person_id}"
            )
            return False

    # Similar checks for target week and call assignments...

    logger.info(f"Rollback validation passed for swap {snapshot.swap_id}")
    return True
```

---

## Notification After Rollback

Inform all affected parties:

```python
def notify_rollback(swap: SwapRecord) -> None:
    """
    Send notifications after swap rollback.

    Args:
        swap: SwapRecord that was rolled back
    """
    from app.services.swap_notification_service import SwapNotificationService

    notifier = SwapNotificationService()

    # Notify source faculty
    notifier.send_rollback_notification(
        recipient=swap.source_faculty,
        swap=swap,
        message=f"Swap rolled back: {swap.rollback_reason}. "
                f"You are back on FMIT for week {swap.source_week}."
    )

    # Notify target faculty
    notifier.send_rollback_notification(
        recipient=swap.target_faculty,
        swap=swap,
        message=f"Swap rolled back: {swap.rollback_reason}. "
                f"You are no longer on FMIT for week {swap.source_week}."
    )

    # Notify coordinator (for awareness)
    notifier.send_coordinator_alert(
        swap=swap,
        alert_type="rollback",
        message=f"Swap {swap.id} was rolled back. Reason: {swap.rollback_reason}"
    )
```

---

## Rollback Failure Handling

If rollback fails (rare but critical):

```python
def handle_rollback_failure(
    swap_id: UUID,
    error: Exception,
    snapshot: SwapSnapshot
) -> None:
    """
    Emergency procedure when rollback fails.

    Args:
        swap_id: Swap that failed to rollback
        error: Exception that caused failure
        snapshot: Snapshot that failed to restore
    """
    logger.critical(
        f"ROLLBACK FAILED for swap {swap_id}: {error}",
        exc_info=True,
        extra={
            "swap_id": str(swap_id),
            "snapshot": snapshot.__dict__,
            "error": str(error)
        }
    )

    # 1. Flag swap as in error state
    swap = db.query(SwapRecord).filter(SwapRecord.id == swap_id).first()
    swap.status = SwapStatus.PENDING  # Revert to pending for manual fix
    swap.notes = f"ROLLBACK FAILED: {error}. Manual intervention required."
    db.commit()

    # 2. Create incident ticket
    create_incident(
        severity="CRITICAL",
        title=f"Swap Rollback Failed: {swap_id}",
        description=f"Automated rollback failed for swap {swap_id}. "
                    f"Database may be in inconsistent state. "
                    f"Error: {error}",
        affected_entities=[
            str(swap.source_faculty_id),
            str(swap.target_faculty_id)
        ],
        snapshot_data=snapshot.__dict__
    )

    # 3. Alert on-call engineer
    send_pagerduty_alert(
        title="Database Inconsistency: Swap Rollback Failed",
        details={
            "swap_id": str(swap_id),
            "error": str(error),
            "action_required": "Manual database restoration needed"
        }
    )

    # 4. Freeze schedule modifications (prevent further damage)
    enable_read_only_mode(reason=f"Swap rollback failure: {swap_id}")
```

---

## Common Rollback Scenarios

### Scenario 1: Requestor Changed Mind

**Trigger:** Faculty realizes they actually can't give up the week

```python
# Request
POST /api/swap/{swap_id}/rollback
{
    "reason": "Changed mind - unable to attend conference"
}

# Response
{
    "success": true,
    "swap_id": "uuid",
    "message": "Swap rolled back successfully. You are back on FMIT for week 2025-02-03.",
    "rolled_back_at": "2025-01-15T18:30:00Z",
    "time_remaining_in_window": "5h 30m"
}
```

### Scenario 2: Discovered Conflict Post-Execution

**Trigger:** System detects ACGME violation 5 minutes after execution

```python
# Automated check
result = check_post_execution_compliance(swap_id)

# Auto-rollback triggered
{
    "success": true,
    "swap_id": "uuid",
    "message": "Auto-rollback: Target faculty exceeded 80-hour limit after swap",
    "rolled_back_at": "2025-01-15T10:35:00Z",
    "triggered_by": "system"
}
```

### Scenario 3: Data Entry Error

**Trigger:** Wrong week was entered in swap request

```python
# Request
POST /api/swap/{swap_id}/rollback
{
    "reason": "Data entry error - meant to swap week 2025-02-10, not 2025-02-03"
}

# After rollback, submit corrected request
POST /api/swap/request
{
    "source_faculty_id": "uuid-a",
    "source_week": "2025-02-10",  # Corrected week
    "target_faculty_id": "uuid-b",
    "target_week": "2025-02-17",
    "swap_type": "one_to_one",
    "reason": "Conference attendance (corrected request)"
}
```

---

## Rollback Rate Monitoring

Track rollback rate as **quality metric**:

```python
def calculate_rollback_rate(start_date: date, end_date: date) -> dict:
    """
    Calculate swap rollback rate for quality monitoring.

    Args:
        start_date: Start of period
        end_date: End of period

    Returns:
        dict: Rollback statistics
    """
    total_executed = db.query(SwapRecord).filter(
        SwapRecord.executed_at >= start_date,
        SwapRecord.executed_at < end_date,
        SwapRecord.status.in_([SwapStatus.EXECUTED, SwapStatus.ROLLED_BACK])
    ).count()

    total_rolled_back = db.query(SwapRecord).filter(
        SwapRecord.rolled_back_at >= start_date,
        SwapRecord.rolled_back_at < end_date,
        SwapRecord.status == SwapStatus.ROLLED_BACK
    ).count()

    rollback_rate = (total_rolled_back / total_executed) if total_executed > 0 else 0

    return {
        "period": f"{start_date} to {end_date}",
        "total_executed": total_executed,
        "total_rolled_back": total_rolled_back,
        "rollback_rate_percent": rollback_rate * 100,
        "quality_status": "GOOD" if rollback_rate < 0.05 else "NEEDS_IMPROVEMENT"
    }

# Example output:
{
    "period": "2025-01-01 to 2025-02-01",
    "total_executed": 42,
    "total_rolled_back": 2,
    "rollback_rate_percent": 4.76,
    "quality_status": "GOOD"  # <5% rollback rate is healthy
}
```

**Target:** <5% rollback rate

**Action thresholds:**
- <5%: Healthy - no action needed
- 5-10%: Review recent rollbacks for patterns
- >10%: Investigate validation gaps or user training needs

---

## Quick Reference

### Key Functions

| Function | Purpose | Location |
|----------|---------|----------|
| `rollback_swap()` | Execute rollback | `app/services/swap_executor.py` |
| `can_rollback()` | Check eligibility | `app/services/swap_executor.py` |
| `create_swap_snapshot()` | Pre-execution snapshot | `app/services/swap_snapshot.py` |
| `restore_from_snapshot()` | State restoration | `app/services/swap_snapshot.py` |

### Rollback Window

```python
ROLLBACK_WINDOW_HOURS = 24
SNAPSHOT_TTL_HOURS = 25  # Keep slightly longer than rollback window
```

### Status Transitions

```
EXECUTED → (rollback) → ROLLED_BACK
```

No further status changes allowed after `ROLLED_BACK`.
