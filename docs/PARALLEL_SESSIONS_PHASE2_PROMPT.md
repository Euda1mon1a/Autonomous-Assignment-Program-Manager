***REMOVED*** FMIT Scheduling - Phase 2: Parallel Development Sessions (10 Terminals)

***REMOVED******REMOVED*** Overview
This document defines 10 parallel terminal sessions for Priorities 2-5 with **zero file overlap**.
Each session creates NEW files only - no modifications to existing files.

**Prerequisites:** Priority 1 tests must be passing (completed in Phase 1).

---

***REMOVED******REMOVED*** Session Allocation Matrix

| Terminal | Branch Suffix | Priority | Focus | New Files Created |
|----------|---------------|----------|-------|-------------------|
| T1 | `-swap-models` | P2 | Swap data models | models/swap.py |
| T2 | `-swap-schemas` | P2 | Swap API schemas | schemas/swap.py |
| T3 | `-swap-validation` | P2 | Swap validation logic | services/swap_validation.py |
| T4 | `-swap-executor` | P2 | Swap execution logic | services/swap_executor.py |
| T5 | `-leave-providers` | P3 | Leave provider package | services/leave_providers/*.py |
| T6 | `-leave-schemas` | P3 | Leave API schemas | schemas/leave.py |
| T7 | `-conflict-detector` | P3 | Conflict auto-detection | services/conflict_auto_detector.py |
| T8 | `-conflict-model` | P3 | Conflict alert model | models/conflict_alert.py |
| T9 | `-portal-model` | P5 | Faculty preference model | models/faculty_preference.py |
| T10 | `-portal-schemas` | P5 | Portal API schemas | schemas/portal.py |

---

***REMOVED******REMOVED*** Terminal 1: Swap Models

**Branch:** `claude/fmit-swap-models-{SESSION_ID}`

***REMOVED******REMOVED******REMOVED*** Files OWNED (CREATE NEW):
- `backend/app/models/swap.py`

***REMOVED******REMOVED******REMOVED*** Files DO NOT MODIFY:
- `backend/app/models/__init__.py` (wiring session handles this)
- Any other model files
- Any service or schema files

***REMOVED******REMOVED******REMOVED*** Task:
Create the SwapRecord and SwapRequest models for tracking FMIT swap history.

***REMOVED******REMOVED******REMOVED*** Implementation Requirements:

```python
"""
Models for FMIT swap tracking.

SwapRecord tracks executed swaps with full audit history.
SwapRequest tracks pending swap requests awaiting approval.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Text, Date
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class SwapStatus(str, Enum):
    """Status of a swap request/record."""
    PENDING = "pending"           ***REMOVED*** Awaiting approval
    APPROVED = "approved"         ***REMOVED*** Approved, not yet executed
    EXECUTED = "executed"         ***REMOVED*** Swap completed
    REJECTED = "rejected"         ***REMOVED*** Rejected by faculty/admin
    CANCELLED = "cancelled"       ***REMOVED*** Cancelled by requester
    ROLLED_BACK = "rolled_back"   ***REMOVED*** Undone after execution


class SwapType(str, Enum):
    """Type of swap."""
    ONE_TO_ONE = "one_to_one"     ***REMOVED*** A takes week X, gives week Y to B
    ABSORB = "absorb"             ***REMOVED*** A takes week X, gives nothing back


class SwapRecord(Base):
    """
    Record of an FMIT swap between faculty members.

    Tracks who swapped with whom, which weeks were exchanged,
    and the full audit trail of the swap lifecycle.
    """
    __tablename__ = "swap_records"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    ***REMOVED*** Source faculty (person requesting to offload a week)
    source_faculty_id = Column(PGUUID(as_uuid=True), ForeignKey("people.id"), nullable=False)
    source_week = Column(Date, nullable=False)  ***REMOVED*** Week being offloaded

    ***REMOVED*** Target faculty (person taking the week)
    target_faculty_id = Column(PGUUID(as_uuid=True), ForeignKey("people.id"), nullable=False)
    target_week = Column(Date, nullable=True)  ***REMOVED*** Week given in exchange (null for absorb)

    ***REMOVED*** Swap details
    swap_type = Column(SQLEnum(SwapType), nullable=False)
    status = Column(SQLEnum(SwapStatus), default=SwapStatus.PENDING, nullable=False)

    ***REMOVED*** Audit fields
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    requested_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    approved_at = Column(DateTime, nullable=True)
    approved_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    executed_at = Column(DateTime, nullable=True)
    executed_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    rolled_back_at = Column(DateTime, nullable=True)
    rolled_back_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rollback_reason = Column(Text, nullable=True)

    ***REMOVED*** Notes and context
    reason = Column(Text, nullable=True)  ***REMOVED*** Why the swap was requested
    notes = Column(Text, nullable=True)   ***REMOVED*** Additional notes

    ***REMOVED*** Relationships
    source_faculty = relationship("Person", foreign_keys=[source_faculty_id])
    target_faculty = relationship("Person", foreign_keys=[target_faculty_id])

    ***REMOVED*** Enable SQLAlchemy-Continuum versioning
    __versioned__ = {}


class SwapApproval(Base):
    """
    Approval record for a swap request.

    Both source and target faculty must approve before execution.
    """
    __tablename__ = "swap_approvals"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    swap_id = Column(PGUUID(as_uuid=True), ForeignKey("swap_records.id"), nullable=False)

    ***REMOVED*** Who is approving
    faculty_id = Column(PGUUID(as_uuid=True), ForeignKey("people.id"), nullable=False)
    role = Column(String(20), nullable=False)  ***REMOVED*** "source" or "target"

    ***REMOVED*** Approval status
    approved = Column(Boolean, nullable=True)  ***REMOVED*** True=approved, False=rejected, None=pending
    responded_at = Column(DateTime, nullable=True)
    response_notes = Column(Text, nullable=True)

    ***REMOVED*** Relationships
    swap = relationship("SwapRecord", backref="approvals")
    faculty = relationship("Person")
```

***REMOVED******REMOVED******REMOVED*** Success Criteria:
- Model file created with SwapRecord, SwapStatus, SwapType, SwapApproval
- All fields documented with comments
- SQLAlchemy-Continuum versioning enabled
- No imports from other new files (swap_validation, etc.)

---

***REMOVED******REMOVED*** Terminal 2: Swap Schemas

**Branch:** `claude/fmit-swap-schemas-{SESSION_ID}`

***REMOVED******REMOVED******REMOVED*** Files OWNED (CREATE NEW):
- `backend/app/schemas/swap.py`

***REMOVED******REMOVED******REMOVED*** Files DO NOT MODIFY:
- `backend/app/schemas/__init__.py`
- `backend/app/schemas/schedule.py`
- Any other schema files

***REMOVED******REMOVED******REMOVED*** Task:
Create Pydantic schemas for swap API requests and responses.

***REMOVED******REMOVED******REMOVED*** Implementation Requirements:

```python
"""
Pydantic schemas for FMIT swap API.

Handles validation for swap requests, responses, and execution.
"""
from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SwapStatusSchema(str, Enum):
    """Status of a swap."""
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


class SwapTypeSchema(str, Enum):
    """Type of swap."""
    ONE_TO_ONE = "one_to_one"
    ABSORB = "absorb"


***REMOVED*** ============================================================================
***REMOVED*** Request Schemas
***REMOVED*** ============================================================================

class SwapExecuteRequest(BaseModel):
    """Request to execute a swap between faculty."""
    source_faculty_id: UUID
    source_week: date
    target_faculty_id: UUID
    target_week: Optional[date] = None  ***REMOVED*** None for absorb swaps
    swap_type: SwapTypeSchema
    reason: Optional[str] = Field(None, max_length=500)

    @field_validator('target_week')
    @classmethod
    def validate_swap_type_consistency(cls, v, info):
        """Ensure target_week is set for one-to-one swaps."""
        if info.data.get('swap_type') == SwapTypeSchema.ONE_TO_ONE and v is None:
            raise ValueError("target_week required for one-to-one swaps")
        return v


class SwapApprovalRequest(BaseModel):
    """Request to approve or reject a swap."""
    approved: bool
    notes: Optional[str] = Field(None, max_length=500)


class SwapRollbackRequest(BaseModel):
    """Request to rollback an executed swap."""
    reason: str = Field(..., min_length=10, max_length=500)


class SwapHistoryFilter(BaseModel):
    """Filters for swap history query."""
    faculty_id: Optional[UUID] = None
    status: Optional[SwapStatusSchema] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


***REMOVED*** ============================================================================
***REMOVED*** Response Schemas
***REMOVED*** ============================================================================

class SwapValidationResult(BaseModel):
    """Result of swap validation."""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    back_to_back_conflict: bool = False
    external_conflict: Optional[str] = None


class SwapRecordResponse(BaseModel):
    """Response schema for a swap record."""
    id: UUID
    source_faculty_id: UUID
    source_faculty_name: str
    source_week: date
    target_faculty_id: UUID
    target_faculty_name: str
    target_week: Optional[date]
    swap_type: SwapTypeSchema
    status: SwapStatusSchema
    reason: Optional[str]
    requested_at: datetime
    executed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SwapExecuteResponse(BaseModel):
    """Response after executing a swap."""
    success: bool
    swap_id: UUID
    message: str
    validation: SwapValidationResult
    swap: Optional[SwapRecordResponse] = None


class SwapHistoryResponse(BaseModel):
    """Paginated swap history response."""
    items: List[SwapRecordResponse]
    total: int
    page: int
    page_size: int
    pages: int


class SwapApprovalResponse(BaseModel):
    """Response for swap approval status."""
    swap_id: UUID
    source_approved: Optional[bool]
    target_approved: Optional[bool]
    fully_approved: bool
    can_execute: bool
```

***REMOVED******REMOVED******REMOVED*** Success Criteria:
- All request/response schemas created
- Field validators for business rules
- Proper Optional typing
- No imports from models/swap.py (keep decoupled)

---

***REMOVED******REMOVED*** Terminal 3: Swap Validation Service

**Branch:** `claude/fmit-swap-validation-{SESSION_ID}`

***REMOVED******REMOVED******REMOVED*** Files OWNED (CREATE NEW):
- `backend/app/services/swap_validation.py`

***REMOVED******REMOVED******REMOVED*** Files DO NOT MODIFY:
- `backend/app/services/__init__.py`
- `backend/app/services/xlsx_import.py`
- Any other service files

***REMOVED******REMOVED******REMOVED*** Task:
Create SwapValidationService that validates proposed swaps.

***REMOVED******REMOVED******REMOVED*** Implementation Requirements:

```python
"""
Swap validation service.

Validates proposed swaps against business rules:
- Back-to-back week conflicts
- External conflicts (leave, TDY, etc.)
- Call cascade implications
- Faculty availability
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.models.person import Person
    from app.models.absence import Absence


@dataclass
class ValidationError:
    """A validation error with code and message."""
    code: str
    message: str
    severity: str = "error"  ***REMOVED*** "error" or "warning"


@dataclass
class SwapValidationResult:
    """Result of swap validation."""
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    back_to_back_conflict: bool = False
    external_conflict: Optional[str] = None
    call_cascade_affected: bool = False


class SwapValidationService:
    """
    Service for validating FMIT swap requests.

    Checks business rules before allowing swap execution.
    """

    def __init__(self, db: Session):
        self.db = db

    def validate_swap(
        self,
        source_faculty_id: UUID,
        source_week: date,
        target_faculty_id: UUID,
        target_week: Optional[date] = None,
    ) -> SwapValidationResult:
        """
        Validate a proposed swap.

        Args:
            source_faculty_id: Faculty offloading the week
            source_week: Week being offloaded
            target_faculty_id: Faculty taking the week
            target_week: Week given in exchange (optional for absorb)

        Returns:
            SwapValidationResult with validation status and any errors/warnings
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []
        back_to_back = False
        external_conflict = None

        ***REMOVED*** Load faculty members
        source_faculty = self._get_faculty(source_faculty_id)
        target_faculty = self._get_faculty(target_faculty_id)

        if not source_faculty:
            errors.append(ValidationError("SOURCE_NOT_FOUND", "Source faculty not found"))
        if not target_faculty:
            errors.append(ValidationError("TARGET_NOT_FOUND", "Target faculty not found"))

        if errors:
            return SwapValidationResult(valid=False, errors=errors, warnings=warnings)

        ***REMOVED*** Check back-to-back conflicts for target taking source_week
        target_weeks = self._get_faculty_fmit_weeks(target_faculty_id)
        if self._creates_back_to_back(target_weeks, source_week):
            back_to_back = True
            errors.append(ValidationError(
                "BACK_TO_BACK",
                f"Taking week {source_week} would create back-to-back FMIT for {target_faculty.name}"
            ))

        ***REMOVED*** Check external conflicts
        conflict = self._check_external_conflicts(target_faculty_id, source_week)
        if conflict:
            external_conflict = conflict
            errors.append(ValidationError(
                "EXTERNAL_CONFLICT",
                f"{target_faculty.name} has {conflict} conflict during week {source_week}"
            ))

        ***REMOVED*** Check if source_week is in the past
        if source_week < date.today():
            errors.append(ValidationError(
                "PAST_DATE",
                f"Cannot swap past week {source_week}"
            ))

        ***REMOVED*** Warning for imminent swaps
        if source_week < date.today() + timedelta(days=14):
            warnings.append(ValidationError(
                "IMMINENT_SWAP",
                f"Week {source_week} is within 2 weeks - swap may be difficult to coordinate",
                severity="warning"
            ))

        ***REMOVED*** Check call cascade implications (Fri/Sat call)
        if self._affects_call_cascade(source_week):
            warnings.append(ValidationError(
                "CALL_CASCADE",
                f"Week {source_week} includes Fri/Sat call - cascade update required",
                severity="warning"
            ))

        return SwapValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            back_to_back_conflict=back_to_back,
            external_conflict=external_conflict,
            call_cascade_affected=self._affects_call_cascade(source_week),
        )

    def _get_faculty(self, faculty_id: UUID) -> Optional["Person"]:
        """Load faculty member from database."""
        from app.models.person import Person
        return self.db.query(Person).filter(
            Person.id == faculty_id,
            Person.type == "faculty"
        ).first()

    def _get_faculty_fmit_weeks(self, faculty_id: UUID) -> List[date]:
        """Get FMIT weeks for a faculty member."""
        ***REMOVED*** This would query from schedule data
        ***REMOVED*** For now, return empty list - actual implementation needs schedule source
        return []

    def _creates_back_to_back(self, existing_weeks: List[date], new_week: date) -> bool:
        """Check if adding new_week creates back-to-back conflict."""
        from app.services.xlsx_import import has_back_to_back_conflict
        test_weeks = sorted(existing_weeks + [new_week])
        return has_back_to_back_conflict(test_weeks)

    def _check_external_conflicts(self, faculty_id: UUID, week: date) -> Optional[str]:
        """Check for external conflicts (leave, TDY, etc.)."""
        from app.models.absence import Absence

        week_end = week + timedelta(days=6)

        conflict = self.db.query(Absence).filter(
            Absence.person_id == faculty_id,
            Absence.start_date <= week_end,
            Absence.end_date >= week,
            Absence.is_blocking == True,
        ).first()

        if conflict:
            return conflict.absence_type
        return None

    def _affects_call_cascade(self, week: date) -> bool:
        """Check if the week includes call cascade (Fri/Sat)."""
        ***REMOVED*** FMIT weeks typically include Fri-Sat call on the weekend
        ***REMOVED*** Per domain spec, swapping FMIT affects Fri-Sat call assignments
        return True  ***REMOVED*** All FMIT weeks affect call cascade
```

***REMOVED******REMOVED******REMOVED*** Success Criteria:
- SwapValidationService class created
- Validation for back-to-back, external conflicts, past dates
- Warning system for imminent swaps and call cascade
- Uses existing xlsx_import.has_back_to_back_conflict

---

***REMOVED******REMOVED*** Terminal 4: Swap Executor Service

**Branch:** `claude/fmit-swap-executor-{SESSION_ID}`

***REMOVED******REMOVED******REMOVED*** Files OWNED (CREATE NEW):
- `backend/app/services/swap_executor.py`

***REMOVED******REMOVED******REMOVED*** Files DO NOT MODIFY:
- `backend/app/services/__init__.py`
- `backend/app/services/swap_validation.py`
- Any other service files

***REMOVED******REMOVED******REMOVED*** Task:
Create SwapExecutor that executes validated swaps and handles rollback.

***REMOVED******REMOVED******REMOVED*** Implementation Requirements:

```python
"""
Swap execution service.

Executes validated swaps and handles rollback within the allowed window.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    pass  ***REMOVED*** Avoid circular imports


@dataclass
class ExecutionResult:
    """Result of swap execution."""
    success: bool
    swap_id: Optional[UUID] = None
    message: str = ""
    error_code: Optional[str] = None


@dataclass
class RollbackResult:
    """Result of swap rollback."""
    success: bool
    message: str = ""
    error_code: Optional[str] = None


class SwapExecutor:
    """
    Service for executing FMIT swaps.

    Handles the actual swap execution and rollback capability.
    """

    ROLLBACK_WINDOW_HOURS = 24  ***REMOVED*** Swaps can be rolled back within 24 hours

    def __init__(self, db: Session):
        self.db = db

    def execute_swap(
        self,
        source_faculty_id: UUID,
        source_week: date,
        target_faculty_id: UUID,
        target_week: Optional[date],
        swap_type: str,
        reason: Optional[str] = None,
        executed_by_id: Optional[UUID] = None,
    ) -> ExecutionResult:
        """
        Execute a swap after validation.

        Args:
            source_faculty_id: Faculty offloading the week
            source_week: Week being offloaded
            target_faculty_id: Faculty taking the week
            target_week: Week given in exchange (None for absorb)
            swap_type: "one_to_one" or "absorb"
            reason: Reason for the swap
            executed_by_id: User executing the swap

        Returns:
            ExecutionResult with success status and swap_id
        """
        from uuid import uuid4

        try:
            ***REMOVED*** Create swap record
            swap_id = uuid4()

            ***REMOVED*** In actual implementation:
            ***REMOVED*** 1. Create SwapRecord in database
            ***REMOVED*** 2. Update schedule assignments
            ***REMOVED*** 3. Handle call cascade updates
            ***REMOVED*** 4. Send notifications

            ***REMOVED*** For now, create the record structure
            swap_data = {
                "id": swap_id,
                "source_faculty_id": source_faculty_id,
                "source_week": source_week,
                "target_faculty_id": target_faculty_id,
                "target_week": target_week,
                "swap_type": swap_type,
                "status": "executed",
                "reason": reason,
                "executed_at": datetime.utcnow(),
                "executed_by_id": executed_by_id,
            }

            ***REMOVED*** TODO: Actually persist to database when SwapRecord model is wired
            ***REMOVED*** swap = SwapRecord(**swap_data)
            ***REMOVED*** self.db.add(swap)
            ***REMOVED*** self.db.commit()

            return ExecutionResult(
                success=True,
                swap_id=swap_id,
                message=f"Swap executed successfully. Source week {source_week} transferred to target.",
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Swap execution failed: {str(e)}",
                error_code="EXECUTION_FAILED",
            )

    def rollback_swap(
        self,
        swap_id: UUID,
        reason: str,
        rolled_back_by_id: Optional[UUID] = None,
    ) -> RollbackResult:
        """
        Rollback an executed swap within the allowed window.

        Args:
            swap_id: ID of the swap to rollback
            reason: Reason for rollback
            rolled_back_by_id: User performing the rollback

        Returns:
            RollbackResult with success status
        """
        ***REMOVED*** TODO: Implement when SwapRecord model is wired
        ***REMOVED*** 1. Load swap record
        ***REMOVED*** 2. Verify within rollback window
        ***REMOVED*** 3. Reverse schedule changes
        ***REMOVED*** 4. Update swap status to rolled_back
        ***REMOVED*** 5. Handle call cascade reversal

        return RollbackResult(
            success=False,
            message="Rollback not yet implemented - awaiting model wiring",
            error_code="NOT_IMPLEMENTED",
        )

    def can_rollback(self, swap_id: UUID) -> bool:
        """Check if a swap can still be rolled back."""
        ***REMOVED*** TODO: Implement when SwapRecord model is wired
        ***REMOVED*** Check if swap exists, is executed, and within rollback window
        return False

    def _update_schedule_assignments(
        self,
        source_faculty_id: UUID,
        source_week: date,
        target_faculty_id: UUID,
    ) -> None:
        """Update the actual schedule assignments for the swap."""
        ***REMOVED*** This would update Assignment records for the FMIT week
        ***REMOVED*** Moving assignments from source to target faculty
        pass

    def _update_call_cascade(self, week: date, new_faculty_id: UUID) -> None:
        """
        Update Fri/Sat call assignments for the swapped week.

        Per FMIT domain rules, the faculty doing FMIT also takes
        the Friday and Saturday call for that week.
        """
        ***REMOVED*** This would update CallAssignment records
        pass


from datetime import date  ***REMOVED*** Import at end to avoid issues
```

***REMOVED******REMOVED******REMOVED*** Success Criteria:
- SwapExecutor class with execute_swap and rollback_swap methods
- ExecutionResult and RollbackResult dataclasses
- Placeholder implementations ready for model wiring
- Call cascade handling stubbed out

---

***REMOVED******REMOVED*** Terminal 5: Leave Providers Package

**Branch:** `claude/fmit-leave-providers-{SESSION_ID}`

***REMOVED******REMOVED******REMOVED*** Files OWNED (CREATE NEW):
- `backend/app/services/leave_providers/__init__.py`
- `backend/app/services/leave_providers/base.py`
- `backend/app/services/leave_providers/database.py`
- `backend/app/services/leave_providers/csv_provider.py`
- `backend/app/services/leave_providers/factory.py`

***REMOVED******REMOVED******REMOVED*** Files DO NOT MODIFY:
- `backend/app/services/__init__.py`
- Any other service files

***REMOVED******REMOVED******REMOVED*** Task:
Create a complete leave provider package with pluggable backends.

***REMOVED******REMOVED******REMOVED*** Implementation Requirements:

Create `backend/app/services/leave_providers/__init__.py`:
```python
"""Leave provider package for external conflict integration."""
from app.services.leave_providers.base import LeaveProvider, LeaveRecord
from app.services.leave_providers.database import DatabaseLeaveProvider
from app.services.leave_providers.csv_provider import CSVLeaveProvider
from app.services.leave_providers.factory import LeaveProviderFactory

__all__ = [
    "LeaveProvider",
    "LeaveRecord",
    "DatabaseLeaveProvider",
    "CSVLeaveProvider",
    "LeaveProviderFactory",
]
```

Create `backend/app/services/leave_providers/base.py`:
```python
"""Base classes for leave providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import List, Optional


@dataclass
class LeaveRecord:
    """A leave/absence record."""
    faculty_name: str
    faculty_id: Optional[str]
    start_date: date
    end_date: date
    leave_type: str  ***REMOVED*** vacation, tdy, deployment, conference, medical
    description: Optional[str] = None
    is_blocking: bool = True


class LeaveProvider(ABC):
    """Abstract base class for leave data providers."""

    @abstractmethod
    def get_conflicts(
        self,
        faculty_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[LeaveRecord]:
        """Get leave records matching the criteria."""
        pass

    @abstractmethod
    def sync(self) -> int:
        """Sync data from source. Returns count of records synced."""
        pass

    @abstractmethod
    def get_all_leave(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[LeaveRecord]:
        """Get all leave records in date range."""
        pass
```

Create `backend/app/services/leave_providers/database.py`:
```python
"""Database-backed leave provider."""
from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.services.leave_providers.base import LeaveProvider, LeaveRecord


class DatabaseLeaveProvider(LeaveProvider):
    """
    Leave provider that reads from the Absence model.

    Integrates with existing absence tracking in the database.
    """

    def __init__(self, db: Session, cache_ttl_seconds: int = 300):
        self.db = db
        self.cache_ttl = cache_ttl_seconds
        self._cache: Optional[List[LeaveRecord]] = None
        self._cache_time: Optional[date] = None

    def get_conflicts(
        self,
        faculty_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[LeaveRecord]:
        """Get blocking leave records."""
        records = self.get_all_leave(start_date, end_date)

        ***REMOVED*** Filter by faculty if specified
        if faculty_name:
            records = [r for r in records if r.faculty_name == faculty_name]

        ***REMOVED*** Only return blocking records
        return [r for r in records if r.is_blocking]

    def sync(self) -> int:
        """Clear cache to force refresh."""
        self._cache = None
        self._cache_time = None
        return len(self.get_all_leave())

    def get_all_leave(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[LeaveRecord]:
        """Get all leave records from Absence model."""
        from app.models.absence import Absence
        from app.models.person import Person

        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = date.today() + timedelta(days=365)

        absences = (
            self.db.query(Absence)
            .join(Person)
            .filter(
                Absence.end_date >= start_date,
                Absence.start_date <= end_date,
            )
            .all()
        )

        records = []
        for absence in absences:
            records.append(LeaveRecord(
                faculty_name=absence.person.name,
                faculty_id=str(absence.person_id),
                start_date=absence.start_date,
                end_date=absence.end_date,
                leave_type=absence.absence_type,
                description=absence.notes or absence.replacement_activity,
                is_blocking=absence.should_block_assignment,
            ))

        return records
```

Create `backend/app/services/leave_providers/csv_provider.py` and `factory.py` with similar patterns.

***REMOVED******REMOVED******REMOVED*** Success Criteria:
- Complete leave_providers package created
- All 5 files with proper implementations
- No dependencies on other new files

---

***REMOVED******REMOVED*** Terminal 6: Leave Schemas

**Branch:** `claude/fmit-leave-schemas-{SESSION_ID}`

***REMOVED******REMOVED******REMOVED*** Files OWNED (CREATE NEW):
- `backend/app/schemas/leave.py`

***REMOVED******REMOVED******REMOVED*** Files DO NOT MODIFY:
- `backend/app/schemas/__init__.py`
- Any other schema files

***REMOVED******REMOVED******REMOVED*** Task:
Create Pydantic schemas for leave/webhook API.

***REMOVED******REMOVED******REMOVED*** Implementation:
Create schemas for:
- LeaveWebhookPayload
- LeaveCreateRequest
- LeaveUpdateRequest
- LeaveResponse
- LeaveCalendarResponse

***REMOVED******REMOVED******REMOVED*** Success Criteria:
- All leave-related schemas created
- Webhook payload validation
- Date range validators

---

***REMOVED******REMOVED*** Terminal 7: Conflict Auto-Detector

**Branch:** `claude/fmit-conflict-detector-{SESSION_ID}`

***REMOVED******REMOVED******REMOVED*** Files OWNED (CREATE NEW):
- `backend/app/services/conflict_auto_detector.py`

***REMOVED******REMOVED******REMOVED*** Files DO NOT MODIFY:
- `backend/app/services/__init__.py`
- Any other service files

***REMOVED******REMOVED******REMOVED*** Task:
Create ConflictAutoDetector service that detects FMIT conflicts when leave changes.

***REMOVED******REMOVED******REMOVED*** Implementation:
- ConflictAutoDetector class
- detect_conflicts_for_absence() method
- create_conflict_alerts() method
- Integration point for leave webhooks

***REMOVED******REMOVED******REMOVED*** Success Criteria:
- Service detects conflicts between leave and FMIT schedule
- Creates ConflictAlert records (when model is wired)

---

***REMOVED******REMOVED*** Terminal 8: Conflict Alert Model

**Branch:** `claude/fmit-conflict-model-{SESSION_ID}`

***REMOVED******REMOVED******REMOVED*** Files OWNED (CREATE NEW):
- `backend/app/models/conflict_alert.py`

***REMOVED******REMOVED******REMOVED*** Files DO NOT MODIFY:
- `backend/app/models/__init__.py`
- Any other model files

***REMOVED******REMOVED******REMOVED*** Task:
Create ConflictAlert model for tracking detected schedule conflicts.

***REMOVED******REMOVED******REMOVED*** Implementation:
```python
class ConflictAlertStatus(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    IGNORED = "ignored"

class ConflictAlert(Base):
    __tablename__ = "conflict_alerts"

    id = Column(PGUUID, primary_key=True, default=uuid4)
    faculty_id = Column(PGUUID, ForeignKey("people.id"))
    conflict_type = Column(String(50))  ***REMOVED*** leave_fmit_overlap, back_to_back, etc.
    fmit_week = Column(Date)
    leave_id = Column(PGUUID, ForeignKey("absences.id"), nullable=True)
    status = Column(SQLEnum(ConflictAlertStatus), default=ConflictAlertStatus.NEW)
    severity = Column(String(20))  ***REMOVED*** critical, warning, info
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(PGUUID, ForeignKey("users.id"), nullable=True)
```

***REMOVED******REMOVED******REMOVED*** Success Criteria:
- ConflictAlert model with all fields
- ConflictAlertStatus enum
- Relationships to Person, Absence, User

---

***REMOVED******REMOVED*** Terminal 9: Faculty Preference Model

**Branch:** `claude/fmit-portal-model-{SESSION_ID}`

***REMOVED******REMOVED******REMOVED*** Files OWNED (CREATE NEW):
- `backend/app/models/faculty_preference.py`

***REMOVED******REMOVED******REMOVED*** Files DO NOT MODIFY:
- `backend/app/models/__init__.py`
- Any other model files

***REMOVED******REMOVED******REMOVED*** Task:
Create FacultyPreference model for storing FMIT scheduling preferences.

***REMOVED******REMOVED******REMOVED*** Implementation:
```python
class FacultyPreference(Base):
    __tablename__ = "faculty_preferences"

    id = Column(PGUUID, primary_key=True, default=uuid4)
    faculty_id = Column(PGUUID, ForeignKey("people.id"), unique=True)

    ***REMOVED*** Week preferences (JSON arrays of date strings)
    preferred_weeks = Column(JSON, default=list)  ***REMOVED*** Weeks they prefer
    blocked_weeks = Column(JSON, default=list)    ***REMOVED*** Weeks they can't do

    ***REMOVED*** Limits
    max_weeks_per_month = Column(Integer, default=2)
    max_consecutive_weeks = Column(Integer, default=1)
    min_gap_between_weeks = Column(Integer, default=2)  ***REMOVED*** weeks

    ***REMOVED*** Notification preferences
    notify_swap_requests = Column(Boolean, default=True)
    notify_schedule_changes = Column(Boolean, default=True)

    ***REMOVED*** Notes
    notes = Column(Text, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ***REMOVED*** Relationships
    faculty = relationship("Person", backref="fmit_preferences")
```

***REMOVED******REMOVED******REMOVED*** Success Criteria:
- FacultyPreference model created
- JSON columns for flexible week storage
- Relationship to Person model

---

***REMOVED******REMOVED*** Terminal 10: Portal Schemas

**Branch:** `claude/fmit-portal-schemas-{SESSION_ID}`

***REMOVED******REMOVED******REMOVED*** Files OWNED (CREATE NEW):
- `backend/app/schemas/portal.py`

***REMOVED******REMOVED******REMOVED*** Files DO NOT MODIFY:
- `backend/app/schemas/__init__.py`
- Any other schema files

***REMOVED******REMOVED******REMOVED*** Task:
Create Pydantic schemas for faculty self-service portal.

***REMOVED******REMOVED******REMOVED*** Implementation:
- MyScheduleResponse
- MySwapsResponse
- SwapRequestCreate
- PreferencesUpdate
- PreferencesResponse
- DashboardResponse

***REMOVED******REMOVED******REMOVED*** Success Criteria:
- All portal schemas created
- Proper typing and validators
- Documentation in docstrings

---

***REMOVED******REMOVED*** Execution Order

***REMOVED******REMOVED******REMOVED*** Phase 2A: All 10 Terminals in Parallel (No Dependencies)
All terminals create NEW files only - no conflicts possible.

```
T1:  models/swap.py
T2:  schemas/swap.py
T3:  services/swap_validation.py
T4:  services/swap_executor.py
T5:  services/leave_providers/*
T6:  schemas/leave.py
T7:  services/conflict_auto_detector.py
T8:  models/conflict_alert.py
T9:  models/faculty_preference.py
T10: schemas/portal.py
```

***REMOVED******REMOVED******REMOVED*** Phase 2B: Wiring Session (After All Terminals Complete)
Single session to add imports to __init__.py files:
- `models/__init__.py` - Add SwapRecord, ConflictAlert, FacultyPreference
- `schemas/__init__.py` - Add swap, leave, portal schemas
- `services/__init__.py` - Add swap_validation, swap_executor, conflict_auto_detector

---

***REMOVED******REMOVED*** File Ownership Summary

| File | Terminal | Status |
|------|----------|--------|
| `models/swap.py` | T1 | CREATE NEW |
| `schemas/swap.py` | T2 | CREATE NEW |
| `services/swap_validation.py` | T3 | CREATE NEW |
| `services/swap_executor.py` | T4 | CREATE NEW |
| `services/leave_providers/__init__.py` | T5 | CREATE NEW |
| `services/leave_providers/base.py` | T5 | CREATE NEW |
| `services/leave_providers/database.py` | T5 | CREATE NEW |
| `services/leave_providers/csv_provider.py` | T5 | CREATE NEW |
| `services/leave_providers/factory.py` | T5 | CREATE NEW |
| `schemas/leave.py` | T6 | CREATE NEW |
| `services/conflict_auto_detector.py` | T7 | CREATE NEW |
| `models/conflict_alert.py` | T8 | CREATE NEW |
| `models/faculty_preference.py` | T9 | CREATE NEW |
| `schemas/portal.py` | T10 | CREATE NEW |

**CRITICAL**: Each terminal must ONLY create/modify files in its OWNED list.

---

***REMOVED******REMOVED*** Git Workflow for Each Terminal

```bash
***REMOVED*** 1. Create branch from main development branch
git checkout claude/review-concurrent-execution-m9XX0
git checkout -b claude/fmit-{type}-{SESSION_ID}

***REMOVED*** 2. Create new file(s) as specified

***REMOVED*** 3. Run any relevant tests
cd /home/user/Autonomous-Assignment-Program-Manager/backend
PYTHONPATH=. python -c "from app.models.swap import SwapRecord; print('Import OK')"

***REMOVED*** 4. Commit with descriptive message
git add backend/app/{path}/{file}.py
git commit -m "feat: Add {description}

- Feature 1
- Feature 2"

***REMOVED*** 5. Push to remote
git push -u origin claude/fmit-{type}-{SESSION_ID}
```
