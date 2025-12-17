"""Tests for FMIT swap models."""
import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4

from app.models.swap import SwapRecord, SwapApproval, SwapStatus, SwapType


class TestSwapStatus:
    """Tests for SwapStatus enum."""

    def test_status_values(self):
        """Test all status values exist."""
        assert SwapStatus.PENDING == "pending"
        assert SwapStatus.APPROVED == "approved"
        assert SwapStatus.EXECUTED == "executed"
        assert SwapStatus.REJECTED == "rejected"
        assert SwapStatus.CANCELLED == "cancelled"
        assert SwapStatus.ROLLED_BACK == "rolled_back"

    def test_status_count(self):
        """Test we have all expected statuses."""
        assert len(SwapStatus) == 6


class TestSwapType:
    """Tests for SwapType enum."""

    def test_type_values(self):
        """Test all swap type values."""
        assert SwapType.ONE_TO_ONE == "one_to_one"
        assert SwapType.ABSORB == "absorb"

    def test_type_count(self):
        """Test we have expected number of types."""
        assert len(SwapType) == 2


class TestSwapRecordModel:
    """Tests for SwapRecord model."""

    def test_create_swap_record(self, db, sample_faculty_members):
        """Test creating a basic swap record."""
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=source.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=target.id,
            target_week=date.today() + timedelta(days=21),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()
        db.refresh(swap)

        assert swap.id is not None
        assert swap.source_faculty_id == source.id
        assert swap.target_faculty_id == target.id
        assert swap.status == SwapStatus.PENDING
        assert swap.swap_type == SwapType.ONE_TO_ONE

    def test_absorb_swap_no_target_week(self, db, sample_faculty_members):
        """Test absorb swap can have null target_week."""
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=source.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=target.id,
            target_week=None,  # Absorb - no reciprocal week
            swap_type=SwapType.ABSORB,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()

        assert swap.target_week is None
        assert swap.swap_type == SwapType.ABSORB

    def test_swap_with_audit_fields(self, db, sample_faculty_members, admin_user):
        """Test swap record with full audit trail."""
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=source.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=target.id,
            target_week=date.today() + timedelta(days=21),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.EXECUTED,
            requested_at=datetime.utcnow() - timedelta(hours=2),
            requested_by_id=admin_user.id,
            executed_at=datetime.utcnow(),
            executed_by_id=admin_user.id,
            reason="TDY conflict",
            notes="Coordinated via email",
        )
        db.add(swap)
        db.commit()
        db.refresh(swap)

        assert swap.requested_at is not None
        assert swap.executed_at is not None
        assert swap.reason == "TDY conflict"

    def test_swap_foreign_keys(self, db, sample_faculty_members):
        """Test swap record stores foreign key references correctly."""
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=source.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=target.id,
            target_week=date.today() + timedelta(days=21),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()
        db.refresh(swap)

        # Verify foreign keys are stored correctly
        assert swap.source_faculty_id == source.id
        assert swap.target_faculty_id == target.id

        # Verify we can query and find the swap
        retrieved_swap = db.query(SwapRecord).filter(
            SwapRecord.id == swap.id
        ).first()
        assert retrieved_swap is not None
        assert retrieved_swap.source_faculty_id == source.id


class TestSwapApprovalModel:
    """Tests for SwapApproval model."""

    def test_create_approval(self, db, sample_faculty_members):
        """Test creating a swap approval record."""
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        # First create a swap
        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=source.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=target.id,
            swap_type=SwapType.ABSORB,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()

        # Create approval for target
        approval = SwapApproval(
            id=uuid4(),
            swap_id=swap.id,
            faculty_id=target.id,
            role="target",
            approved=None,  # Pending
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)

        assert approval.swap_id == swap.id
        assert approval.faculty_id == target.id
        assert approval.role == "target"
        assert approval.approved is None

    def test_approval_response(self, db, sample_faculty_members):
        """Test recording an approval response."""
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=source.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=target.id,
            swap_type=SwapType.ABSORB,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()

        approval = SwapApproval(
            id=uuid4(),
            swap_id=swap.id,
            faculty_id=target.id,
            role="target",
            approved=True,
            responded_at=datetime.utcnow(),
            response_notes="Happy to help!",
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)

        assert approval.approved is True
        assert approval.responded_at is not None
        assert approval.response_notes == "Happy to help!"

    def test_approval_swap_relationship(self, db, sample_faculty_members):
        """Test approval relationship to swap."""
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=source.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=target.id,
            swap_type=SwapType.ABSORB,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()

        approval = SwapApproval(
            id=uuid4(),
            swap_id=swap.id,
            faculty_id=target.id,
            role="target",
        )
        db.add(approval)
        db.commit()
        db.refresh(swap)

        # Access approvals through relationship
        assert len(swap.approvals) == 1
        assert swap.approvals[0].role == "target"
