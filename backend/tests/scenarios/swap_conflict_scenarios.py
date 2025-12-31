"""Swap conflict and scheduling conflict test scenarios."""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.swap import SwapStatus, SwapType
from tests.factories.person_factory import PersonFactory
from tests.factories.swap_factory import SwapFactory


class SwapConflictScenarios:
    """Pre-built scenarios for swap conflict testing."""

    @staticmethod
    def create_conflicting_swap_requests(db: Session) -> dict:
        """
        Create conflicting swap requests.

        Same faculty requests to swap same week with multiple other faculty.
        """
        # Create faculty
        faculty = PersonFactory.create_batch_faculty(
            db, count=5, include_leadership=False
        )

        # Create conflicting swaps (same source, same week, different targets)
        same_week = date.today() + timedelta(days=14)
        conflicting_swaps = SwapFactory.create_conflicting_swaps(
            db,
            faculty=faculty[0],
            other_faculty=faculty[1:4],
            same_week=same_week,
        )

        return {
            "faculty": faculty,
            "source_faculty": faculty[0],
            "conflicting_swaps": conflicting_swaps,
            "conflict_type": "multiple_requests_same_week",
        }

    @staticmethod
    def create_circular_swap_chain(db: Session) -> dict:
        """
        Create circular swap chain.

        A swaps with B, B swaps with C, C swaps with A (circular dependency).
        """
        # Create 3 faculty
        faculty = PersonFactory.create_batch_faculty(
            db, count=3, include_leadership=False
        )

        week1 = date.today() + timedelta(days=7)
        week2 = week1 + timedelta(days=7)
        week3 = week2 + timedelta(days=7)

        # A gives week1, gets week2 from B
        swap_ab = SwapFactory.create_one_to_one_swap(
            db,
            source_faculty=faculty[0],
            target_faculty=faculty[1],
            source_week=week1,
            target_week=week2,
        )

        # B gives week2, gets week3 from C
        swap_bc = SwapFactory.create_one_to_one_swap(
            db,
            source_faculty=faculty[1],
            target_faculty=faculty[2],
            source_week=week2,
            target_week=week3,
        )

        # C gives week3, gets week1 from A
        swap_ca = SwapFactory.create_one_to_one_swap(
            db,
            source_faculty=faculty[2],
            target_faculty=faculty[0],
            source_week=week3,
            target_week=week1,
        )

        return {
            "faculty": faculty,
            "swaps": [swap_ab, swap_bc, swap_ca],
            "conflict_type": "circular_dependency",
        }

    @staticmethod
    def create_overlapping_absorb_requests(db: Session) -> dict:
        """
        Create overlapping absorb requests.

        Multiple faculty trying to absorb same week.
        """
        # Create faculty
        faculty = PersonFactory.create_batch_faculty(
            db, count=4, include_leadership=False
        )

        target_week = date.today() + timedelta(days=14)

        # Faculty 0 gives away week, multiple faculty want to absorb
        absorb_swaps = []
        for target_faculty in faculty[1:]:
            swap = SwapFactory.create_absorb_swap(
                db,
                source_faculty=faculty[0],
                target_faculty=target_faculty,
                source_week=target_week,
            )
            absorb_swaps.append(swap)

        return {
            "faculty": faculty,
            "source_faculty": faculty[0],
            "absorb_swaps": absorb_swaps,
            "conflict_type": "multiple_absorb_requests",
        }

    @staticmethod
    def create_cascade_swap_failure(db: Session) -> dict:
        """
        Create cascade swap failure scenario.

        Swap A depends on Swap B, which depends on Swap C. If C fails, all fail.
        """
        # Create 4 faculty
        faculty = PersonFactory.create_batch_faculty(
            db, count=4, include_leadership=False
        )

        week1 = date.today() + timedelta(days=7)
        week2 = week1 + timedelta(days=7)
        week3 = week2 + timedelta(days=7)

        # Swap chain: A->B->C->D
        swap_ab = SwapFactory.create_one_to_one_swap(
            db,
            source_faculty=faculty[0],
            target_faculty=faculty[1],
            source_week=week1,
            target_week=week2,
            status=SwapStatus.APPROVED,
        )

        swap_bc = SwapFactory.create_one_to_one_swap(
            db,
            source_faculty=faculty[1],
            target_faculty=faculty[2],
            source_week=week2,
            target_week=week3,
            status=SwapStatus.APPROVED,
        )

        # This swap gets rejected (breaks the chain)
        swap_cd = SwapFactory.create_rejected_swap(
            db,
            source_faculty=faculty[2],
            target_faculty=faculty[3],
            reason="Insufficient coverage",
        )

        return {
            "faculty": faculty,
            "swaps": [swap_ab, swap_bc, swap_cd],
            "failed_swap": swap_cd,
            "conflict_type": "cascade_failure",
        }

    @staticmethod
    def create_rollback_conflict(db: Session) -> dict:
        """
        Create swap rollback conflict scenario.

        Swap is executed then needs to be rolled back due to emergency.
        """
        # Create faculty
        faculty = PersonFactory.create_batch_faculty(
            db, count=2, include_leadership=False
        )

        # Create executed swap
        executed_swap = SwapFactory.create_executed_swap(
            db, source_faculty=faculty[0], target_faculty=faculty[1]
        )

        # Now rollback due to emergency
        rolled_back_swap = SwapFactory.create_rolled_back_swap(
            db,
            source_faculty=faculty[0],
            target_faculty=faculty[1],
            rollback_reason="Emergency deployment - original faculty unavailable",
        )

        return {
            "faculty": faculty,
            "executed_swap": executed_swap,
            "rolled_back_swap": rolled_back_swap,
            "conflict_type": "rollback_conflict",
        }

    @staticmethod
    def create_approval_deadlock(db: Session) -> dict:
        """
        Create swap approval deadlock.

        Mutual swaps that both require approval but neither approves the other.
        """
        # Create faculty
        faculty = PersonFactory.create_batch_faculty(
            db, count=2, include_leadership=False
        )

        week1 = date.today() + timedelta(days=7)
        week2 = week1 + timedelta(days=7)

        # A wants B's week
        swap_a_wants_b = SwapFactory.create_one_to_one_swap(
            db,
            source_faculty=faculty[0],
            target_faculty=faculty[1],
            source_week=week1,
            target_week=week2,
            status=SwapStatus.PENDING,
        )

        # B wants A's week (conflict)
        swap_b_wants_a = SwapFactory.create_one_to_one_swap(
            db,
            source_faculty=faculty[1],
            target_faculty=faculty[0],
            source_week=week2,
            target_week=week1,
            status=SwapStatus.PENDING,
        )

        return {
            "faculty": faculty,
            "swaps": [swap_a_wants_b, swap_b_wants_a],
            "conflict_type": "approval_deadlock",
        }

    @staticmethod
    def create_equity_violation_swap(db: Session) -> dict:
        """
        Create swap that violates call equity.

        Faculty already has max Sunday calls, tries to swap for another.
        """
        from tests.factories.person_factory import PersonFactory

        # Create faculty with already high Sunday call count
        overloaded_faculty = PersonFactory.create_faculty(db)
        overloaded_faculty.sunday_call_count = 6  # Already at max
        db.commit()

        target_faculty = PersonFactory.create_faculty(db)

        # Try to swap for another Sunday (would violate equity)
        # Source week = Sunday, target week = weekday
        source_week = date.today() + timedelta(
            days=(6 - date.today().weekday())
        )  # Next Sunday
        target_week = source_week + timedelta(days=2)  # Tuesday

        swap = SwapFactory.create_one_to_one_swap(
            db,
            source_faculty=target_faculty,
            target_faculty=overloaded_faculty,
            source_week=source_week,
            target_week=target_week,
            status=SwapStatus.PENDING,
        )

        return {
            "overloaded_faculty": overloaded_faculty,
            "target_faculty": target_faculty,
            "swap": swap,
            "conflict_type": "equity_violation",
        }

    @staticmethod
    def create_batch_swap_conflicts(db: Session, num_conflicts: int = 5) -> dict:
        """
        Create multiple swap conflicts for load testing.

        Args:
            db: Database session
            num_conflicts: Number of conflict scenarios to create

        Returns:
            dict: Multiple conflict scenarios
        """
        # Create large faculty pool
        faculty = PersonFactory.create_batch_faculty(
            db, count=num_conflicts * 2, include_leadership=False
        )

        # Create various conflicts
        swaps = SwapFactory.create_batch_swaps(
            db, faculty=faculty, num_swaps=num_conflicts, swap_type=None
        )

        return {
            "faculty": faculty,
            "swaps": swaps,
            "conflict_type": "batch_conflicts",
        }
