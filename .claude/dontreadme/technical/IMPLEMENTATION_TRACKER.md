# Implementation Tracker - Swap System

This document tracks the implementation status of the swap system, which has several incomplete features identified via TODO comments in the codebase.

## Current Status

| Component | Status | Completion |
|-----------|--------|------------|
| Swap Request Creation | Complete | 100% |
| Swap Matching | Complete | 100% |
| Swap Execution | Partial | ~40% |
| Swap Notification | Partial | ~60% |
| Swap History | Partial | ~50% |

---

## Swap Executor Implementation

### File: `backend/app/services/swap_executor.py`

The swap executor is responsible for executing approved swaps. Current TODOs indicate incomplete implementation.

### Required Tasks

#### Task 1: Persist SwapRecord Model (Line 60)

**Current State:**
```python
# TODO: Persist SwapRecord when model is wired
```

**Required Implementation:**
```python
async def persist_swap_record(
    self,
    db: AsyncSession,
    swap_request: SwapRequest,
    execution_result: SwapExecutionResult
) -> SwapRecord:
    """Persist the swap record to the database."""
    swap_record = SwapRecord(
        id=str(uuid.uuid4()),
        request_id=swap_request.id,
        source_faculty_id=swap_request.source_faculty_id,
        target_faculty_id=swap_request.target_faculty_id,
        source_week=swap_request.source_week,
        target_week=swap_request.target_week,
        executed_at=datetime.utcnow(),
        executed_by=execution_result.executed_by,
        status=SwapRecordStatus.COMPLETED,
    )
    db.add(swap_record)
    await db.commit()
    await db.refresh(swap_record)
    return swap_record
```

**Database Migration Required:**
```python
# alembic/versions/xxx_add_swap_record.py
def upgrade():
    op.create_table(
        'swap_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('request_id', sa.String(36), sa.ForeignKey('swap_requests.id')),
        sa.Column('source_faculty_id', sa.String(36)),
        sa.Column('target_faculty_id', sa.String(36)),
        sa.Column('source_week', sa.Date),
        sa.Column('target_week', sa.Date),
        sa.Column('executed_at', sa.DateTime),
        sa.Column('executed_by', sa.String(36)),
        sa.Column('status', sa.String(20)),
    )
```

#### Task 2: Update Schedule Assignments (Line 61)

**Current State:**
```python
# TODO: Update schedule assignments
```

**Required Implementation:**
```python
async def update_schedule_assignments(
    self,
    db: AsyncSession,
    source_faculty_id: str,
    target_faculty_id: str,
    source_week: date,
    target_week: date
) -> None:
    """Swap schedule assignments between faculty members."""
    # Get source assignment
    source_assignment = await db.execute(
        select(Assignment).where(
            Assignment.faculty_id == source_faculty_id,
            Assignment.week_start == source_week
        )
    )
    source = source_assignment.scalar_one_or_none()

    # Get target assignment
    target_assignment = await db.execute(
        select(Assignment).where(
            Assignment.faculty_id == target_faculty_id,
            Assignment.week_start == target_week
        )
    )
    target = target_assignment.scalar_one_or_none()

    # Perform swap
    if source and target:
        source.faculty_id, target.faculty_id = target.faculty_id, source.faculty_id
        await db.commit()
```

#### Task 3: Update Call Cascade (Line 62)

**Current State:**
```python
# TODO: Update call cascade
```

**Required Implementation:**
```python
async def update_call_cascade(
    self,
    db: AsyncSession,
    source_faculty_id: str,
    target_faculty_id: str,
    source_week: date,
    target_week: date
) -> None:
    """Update call cascade after swap execution."""
    # Update call schedule entries
    await db.execute(
        update(CallSchedule).where(
            CallSchedule.faculty_id == source_faculty_id,
            CallSchedule.week == source_week
        ).values(faculty_id=target_faculty_id)
    )

    await db.execute(
        update(CallSchedule).where(
            CallSchedule.faculty_id == target_faculty_id,
            CallSchedule.week == target_week
        ).values(faculty_id=source_faculty_id)
    )

    await db.commit()
```

---

## Swap Request Service Implementation

### File: `backend/app/services/swap_request_service.py`

#### Task: FMIT Week Verification (Line 668)

**Current State:**
```python
# TODO: Implement proper FMIT week verification
```

**Required Implementation:**
```python
async def verify_fmit_week(
    self,
    db: AsyncSession,
    faculty_id: str,
    week: date
) -> bool:
    """Verify the week is an FMIT (Faculty Member In Training) week."""
    # Check FMIT schedule
    fmit_schedule = await db.execute(
        select(FMITSchedule).where(
            FMITSchedule.faculty_id == faculty_id,
            FMITSchedule.week_start <= week,
            FMITSchedule.week_end >= week
        )
    )
    result = fmit_schedule.scalar_one_or_none()
    return result is not None
```

---

## Leave Routes Implementation

### File: `backend/app/api/routes/leave.py`

#### Task: FMIT Conflict Checking (Line 180)

**Implementation:**
```python
async def check_fmit_conflicts(
    db: AsyncSession,
    faculty_id: str,
    leave_start: date,
    leave_end: date
) -> list[ConflictAlert]:
    """Check for FMIT schedule conflicts with leave request."""
    conflicts = []

    # Query FMIT assignments during leave period
    fmit_assignments = await db.execute(
        select(FMITSchedule).where(
            FMITSchedule.faculty_id == faculty_id,
            FMITSchedule.week_start >= leave_start,
            FMITSchedule.week_end <= leave_end
        )
    )

    for assignment in fmit_assignments.scalars():
        conflicts.append(ConflictAlert(
            type="fmit_leave_conflict",
            severity="high",
            message=f"Leave conflicts with FMIT duty on {assignment.week_start}"
        ))

    return conflicts
```

#### Task: Background Conflict Detection (Line 236)

**Implementation:**
```python
from app.core.celery_app import celery_app

@celery_app.task
def detect_leave_conflicts_background(leave_id: str):
    """Background task to detect conflicts after leave approval."""
    # Implementation in tasks.py
    pass

# In route:
# After leave approval:
detect_leave_conflicts_background.delay(leave.id)
```

---

## Portal Routes Implementation

### File: `backend/app/api/routes/portal.py`

#### Task: Conflict Checking for Available Weeks (Line 102)

**Implementation:**
```python
async def get_available_weeks_with_conflicts(
    db: AsyncSession,
    faculty_id: str,
    start_date: date,
    end_date: date
) -> list[AvailableWeek]:
    """Get available weeks with conflict status."""
    weeks = []
    current = start_date

    while current <= end_date:
        # Check for conflicts
        conflict = await db.execute(
            select(ConflictAlert).where(
                ConflictAlert.faculty_id == faculty_id,
                ConflictAlert.week == current,
                ConflictAlert.resolved == False
            )
        )
        has_conflict = conflict.scalar_one_or_none() is not None

        weeks.append(AvailableWeek(
            date=current,
            has_conflict=has_conflict
        ))
        current += timedelta(weeks=1)

    return weeks
```

#### Task: Candidate Notifications (Line 306)

**Implementation:**
```python
async def notify_swap_candidates(
    db: AsyncSession,
    notification_service: NotificationService,
    swap_request: SwapRequest,
    candidates: list[str]
) -> int:
    """Notify matching candidates about swap opportunity."""
    notified_count = 0

    for candidate_id in candidates:
        notification = Notification(
            user_id=candidate_id,
            type="swap_candidate",
            title="New Swap Opportunity",
            message=f"A swap opportunity matching your preferences is available for {swap_request.source_week}",
            data={
                "swap_request_id": swap_request.id,
                "week": str(swap_request.source_week)
            }
        )

        await notification_service.send(db, notification)
        notified_count += 1

    return notified_count
```

---

## Testing Requirements

Each implementation should include:

1. **Unit Tests** - Test individual functions
2. **Integration Tests** - Test database operations
3. **API Tests** - Test endpoint behavior

Example test structure:
```python
# tests/services/test_swap_executor.py
class TestSwapExecutor:
    async def test_persist_swap_record(self, db_session, swap_request):
        executor = SwapExecutor()
        result = await executor.persist_swap_record(
            db_session, swap_request, execution_result
        )
        assert result.id is not None
        assert result.status == SwapRecordStatus.COMPLETED

    async def test_update_schedule_assignments(self, db_session):
        # Test implementation
        pass
```

---

## Implementation Priority

1. **High Priority** (Week 1-2)
   - Persist SwapRecord Model
   - Update Schedule Assignments
   - Update Call Cascade

2. **Medium Priority** (Week 3-4)
   - FMIT Week Verification
   - Conflict Checking

3. **Lower Priority** (Week 5+)
   - Background Conflict Detection
   - Candidate Notifications

---

*Last updated: 2025-12-18*
*Owner: Backend Team*
