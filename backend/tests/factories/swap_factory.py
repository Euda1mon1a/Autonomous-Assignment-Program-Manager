"""Factory for creating test SwapRecord instances."""

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import uuid4

from faker import Faker
from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.user import User

fake = Faker()


class SwapFactory:
    """Factory for creating SwapRecord instances with random data."""

    @staticmethod
    def create_swap_request(
        db: Session,
        source_faculty: Person,
        target_faculty: Person,
        source_week: date | None = None,
        target_week: date | None = None,
        swap_type: SwapType = SwapType.ONE_TO_ONE,
        status: SwapStatus = SwapStatus.PENDING,
        reason: str | None = None,
        requested_by: User | None = None,
    ) -> SwapRecord:
        """
        Create a swap request.

        Args:
            db: Database session
            source_faculty: Faculty requesting swap (giving away shift)
            target_faculty: Faculty receiving swap (taking shift)
            source_week: Week being given away (Monday date)
            target_week: Week being received (None for ABSORB type)
            swap_type: SwapType.ONE_TO_ONE or SwapType.ABSORB
            status: Swap status
            reason: Reason for swap request
            requested_by: User who requested the swap

        Returns:
            SwapRecord: Created swap request
        """
        if not source_faculty.is_faculty or not target_faculty.is_faculty:
            raise ValueError("Swap requests require faculty persons")

        if source_week is None:
            # Next Monday
            days_until_monday = (7 - date.today().weekday()) % 7
            source_week = date.today() + timedelta(days=days_until_monday)

        if swap_type == SwapType.ONE_TO_ONE and target_week is None:
            # Default to week after source week
            target_week = source_week + timedelta(days=7)

        if swap_type == SwapType.ABSORB:
            target_week = None

        if reason is None:
            reasons = [
                "Family emergency",
                "Medical appointment",
                "Conference attendance",
                "Personal matter",
                "Child care conflict",
                "TDY orders",
            ]
            reason = fake.random_element(reasons)

        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=source_faculty.id,
            target_faculty_id=target_faculty.id,
            source_week=source_week,
            target_week=target_week,
            swap_type=swap_type,
            status=status,
            reason=reason,
            requested_by_id=requested_by.id if requested_by else None,
            requested_at=datetime.utcnow(),
        )
        db.add(swap)
        db.commit()
        db.refresh(swap)
        return swap

    @staticmethod
    def create_one_to_one_swap(
        db: Session,
        source_faculty: Person,
        target_faculty: Person,
        source_week: date | None = None,
        target_week: date | None = None,
        status: SwapStatus = SwapStatus.PENDING,
    ) -> SwapRecord:
        """
        Create a one-to-one swap (faculty A gives week X, gets week Y from faculty B).

        Args:
            db: Database session
            source_faculty: Faculty giving away shift
            target_faculty: Faculty trading shifts
            source_week: Week being given away
            target_week: Week being received
            status: Swap status

        Returns:
            SwapRecord: One-to-one swap request
        """
        return SwapFactory.create_swap_request(
            db,
            source_faculty=source_faculty,
            target_faculty=target_faculty,
            source_week=source_week,
            target_week=target_week,
            swap_type=SwapType.ONE_TO_ONE,
            status=status,
            reason="Trading shifts for better schedule distribution",
        )

    @staticmethod
    def create_absorb_swap(
        db: Session,
        source_faculty: Person,
        target_faculty: Person,
        source_week: date | None = None,
        status: SwapStatus = SwapStatus.PENDING,
    ) -> SwapRecord:
        """
        Create an absorb swap (faculty A gives away week, faculty B absorbs it).

        Args:
            db: Database session
            source_faculty: Faculty giving away shift
            target_faculty: Faculty absorbing shift
            source_week: Week being given away
            status: Swap status

        Returns:
            SwapRecord: Absorb swap request
        """
        return SwapFactory.create_swap_request(
            db,
            source_faculty=source_faculty,
            target_faculty=target_faculty,
            source_week=source_week,
            target_week=None,
            swap_type=SwapType.ABSORB,
            status=status,
            reason="Emergency coverage needed",
        )

    @staticmethod
    def create_approved_swap(
        db: Session,
        source_faculty: Person,
        target_faculty: Person,
        approved_by: User | None = None,
    ) -> SwapRecord:
        """
        Create an approved swap (ready for execution).

        Args:
            db: Database session
            source_faculty: Faculty giving away shift
            target_faculty: Faculty receiving shift
            approved_by: User who approved the swap

        Returns:
            SwapRecord: Approved swap
        """
        swap = SwapFactory.create_one_to_one_swap(
            db,
            source_faculty=source_faculty,
            target_faculty=target_faculty,
            status=SwapStatus.APPROVED,
        )

        swap.approved_at = datetime.utcnow()
        swap.approved_by_id = approved_by.id if approved_by else None
        db.commit()
        db.refresh(swap)

        return swap

    @staticmethod
    def create_executed_swap(
        db: Session,
        source_faculty: Person,
        target_faculty: Person,
        executed_by: User | None = None,
    ) -> SwapRecord:
        """
        Create an executed swap (already completed).

        Args:
            db: Database session
            source_faculty: Faculty who gave away shift
            target_faculty: Faculty who received shift
            executed_by: User who executed the swap

        Returns:
            SwapRecord: Executed swap
        """
        swap = SwapFactory.create_approved_swap(
            db, source_faculty=source_faculty, target_faculty=target_faculty
        )

        swap.status = SwapStatus.EXECUTED
        swap.executed_at = datetime.utcnow()
        swap.executed_by_id = executed_by.id if executed_by else None
        db.commit()
        db.refresh(swap)

        return swap

    @staticmethod
    def create_rejected_swap(
        db: Session,
        source_faculty: Person,
        target_faculty: Person,
        reason: str = "Insufficient coverage",
    ) -> SwapRecord:
        """
        Create a rejected swap.

        Args:
            db: Database session
            source_faculty: Faculty who requested swap
            target_faculty: Faculty who would receive shift
            reason: Rejection reason

        Returns:
            SwapRecord: Rejected swap
        """
        swap = SwapFactory.create_one_to_one_swap(
            db,
            source_faculty=source_faculty,
            target_faculty=target_faculty,
            status=SwapStatus.REJECTED,
        )

        swap.notes = f"Rejected: {reason}"
        db.commit()
        db.refresh(swap)

        return swap

    @staticmethod
    def create_rolled_back_swap(
        db: Session,
        source_faculty: Person,
        target_faculty: Person,
        rollback_reason: str = "Error detected in swap execution",
        rolled_back_by: User | None = None,
    ) -> SwapRecord:
        """
        Create a rolled-back swap (executed then reversed).

        Args:
            db: Database session
            source_faculty: Faculty who gave away shift
            target_faculty: Faculty who received shift
            rollback_reason: Reason for rollback
            rolled_back_by: User who initiated rollback

        Returns:
            SwapRecord: Rolled-back swap
        """
        swap = SwapFactory.create_executed_swap(
            db, source_faculty=source_faculty, target_faculty=target_faculty
        )

        swap.status = SwapStatus.ROLLED_BACK
        swap.rolled_back_at = datetime.utcnow()
        swap.rolled_back_by_id = rolled_back_by.id if rolled_back_by else None
        swap.rollback_reason = rollback_reason
        db.commit()
        db.refresh(swap)

        return swap

    @staticmethod
    def create_batch_swaps(
        db: Session,
        faculty: list[Person],
        num_swaps: int = 5,
        swap_type: SwapType | None = None,
    ) -> list[SwapRecord]:
        """
        Create multiple swap requests between faculty.

        Args:
            db: Database session
            faculty: List of faculty to create swaps between
            num_swaps: Number of swaps to create
            swap_type: Type of swap (random if None)

        Returns:
            list[SwapRecord]: List of created swaps
        """
        if len(faculty) < 2:
            raise ValueError("Need at least 2 faculty members to create swaps")

        swaps = []
        for _ in range(num_swaps):
            source_faculty, target_faculty = fake.random_choices(faculty, length=2)

            if swap_type is None:
                selected_type = fake.random_element(
                    [SwapType.ONE_TO_ONE, SwapType.ABSORB]
                )
            else:
                selected_type = swap_type

            swap = SwapFactory.create_swap_request(
                db,
                source_faculty=source_faculty,
                target_faculty=target_faculty,
                swap_type=selected_type,
            )
            swaps.append(swap)

        return swaps

    @staticmethod
    def create_conflicting_swaps(
        db: Session,
        faculty: Person,
        other_faculty: list[Person],
        same_week: date,
    ) -> list[SwapRecord]:
        """
        Create conflicting swap requests (same faculty, same week, multiple targets).

        Useful for testing conflict detection.

        Args:
            db: Database session
            faculty: Faculty creating conflicting swaps
            other_faculty: List of faculty to swap with
            same_week: Week that's being requested multiple times

        Returns:
            list[SwapRecord]: List of conflicting swaps
        """
        swaps = []
        for other in other_faculty:
            swap = SwapFactory.create_swap_request(
                db,
                source_faculty=faculty,
                target_faculty=other,
                source_week=same_week,
                status=SwapStatus.PENDING,
                reason="Testing conflict detection",
            )
            swaps.append(swap)

        return swaps
