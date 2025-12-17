"""Repository for swap data access."""
from datetime import date, datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.swap import SwapRecord, SwapApproval, SwapStatus, SwapType


class SwapRepository:
    """
    Repository for SwapRecord and SwapApproval data access.

    Provides clean data access patterns separate from business logic.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==========================================================================
    # SwapRecord CRUD
    # ==========================================================================

    def create(
        self,
        source_faculty_id: UUID,
        source_week: date,
        target_faculty_id: UUID,
        swap_type: SwapType,
        target_week: Optional[date] = None,
        reason: Optional[str] = None,
        requested_by_id: Optional[UUID] = None,
    ) -> SwapRecord:
        """Create a new swap record."""
        from uuid import uuid4

        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=source_faculty_id,
            source_week=source_week,
            target_faculty_id=target_faculty_id,
            target_week=target_week,
            swap_type=swap_type,
            status=SwapStatus.PENDING,
            reason=reason,
            requested_by_id=requested_by_id,
            requested_at=datetime.utcnow(),
        )
        self.db.add(swap)
        self.db.commit()
        self.db.refresh(swap)
        return swap

    def get_by_id(self, swap_id: UUID) -> Optional[SwapRecord]:
        """Get a swap record by ID."""
        return self.db.query(SwapRecord).filter(SwapRecord.id == swap_id).first()

    def update_status(
        self,
        swap_id: UUID,
        status: SwapStatus,
        user_id: Optional[UUID] = None,
    ) -> Optional[SwapRecord]:
        """Update swap status with appropriate timestamp."""
        swap = self.get_by_id(swap_id)
        if not swap:
            return None

        swap.status = status
        now = datetime.utcnow()

        if status == SwapStatus.APPROVED:
            swap.approved_at = now
            swap.approved_by_id = user_id
        elif status == SwapStatus.EXECUTED:
            swap.executed_at = now
            swap.executed_by_id = user_id
        elif status == SwapStatus.ROLLED_BACK:
            swap.rolled_back_at = now
            swap.rolled_back_by_id = user_id

        self.db.commit()
        self.db.refresh(swap)
        return swap

    def delete(self, swap_id: UUID) -> bool:
        """Delete a swap record."""
        swap = self.get_by_id(swap_id)
        if not swap:
            return False

        self.db.delete(swap)
        self.db.commit()
        return True

    # ==========================================================================
    # Query Methods
    # ==========================================================================

    def find_by_faculty(
        self,
        faculty_id: UUID,
        as_source: bool = True,
        as_target: bool = True,
    ) -> List[SwapRecord]:
        """Find swaps involving a faculty member."""
        conditions = []
        if as_source:
            conditions.append(SwapRecord.source_faculty_id == faculty_id)
        if as_target:
            conditions.append(SwapRecord.target_faculty_id == faculty_id)

        if not conditions:
            return []

        return self.db.query(SwapRecord).filter(
            or_(*conditions)
        ).order_by(SwapRecord.requested_at.desc()).all()

    def find_by_status(
        self,
        status: SwapStatus,
        faculty_id: Optional[UUID] = None,
    ) -> List[SwapRecord]:
        """Find swaps by status."""
        query = self.db.query(SwapRecord).filter(SwapRecord.status == status)

        if faculty_id:
            query = query.filter(
                or_(
                    SwapRecord.source_faculty_id == faculty_id,
                    SwapRecord.target_faculty_id == faculty_id,
                )
            )

        return query.order_by(SwapRecord.requested_at.desc()).all()

    def find_by_week(
        self,
        week: date,
        faculty_id: Optional[UUID] = None,
    ) -> List[SwapRecord]:
        """Find swaps for a specific week."""
        query = self.db.query(SwapRecord).filter(
            or_(
                SwapRecord.source_week == week,
                SwapRecord.target_week == week,
            )
        )

        if faculty_id:
            query = query.filter(
                or_(
                    SwapRecord.source_faculty_id == faculty_id,
                    SwapRecord.target_faculty_id == faculty_id,
                )
            )

        return query.all()

    def find_pending_for_faculty(self, faculty_id: UUID) -> List[SwapRecord]:
        """Find pending swaps where faculty is target (needs response)."""
        return self.db.query(SwapRecord).filter(
            SwapRecord.target_faculty_id == faculty_id,
            SwapRecord.status == SwapStatus.PENDING,
        ).order_by(SwapRecord.requested_at.desc()).all()

    def find_recent(
        self,
        faculty_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> List[SwapRecord]:
        """Find recent completed swaps."""
        query = self.db.query(SwapRecord).filter(
            SwapRecord.status == SwapStatus.EXECUTED
        )

        if faculty_id:
            query = query.filter(
                or_(
                    SwapRecord.source_faculty_id == faculty_id,
                    SwapRecord.target_faculty_id == faculty_id,
                )
            )

        return query.order_by(SwapRecord.executed_at.desc()).limit(limit).all()

    def find_with_pagination(
        self,
        page: int = 1,
        page_size: int = 20,
        faculty_id: Optional[UUID] = None,
        status: Optional[SwapStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Tuple[List[SwapRecord], int]:
        """
        Find swaps with pagination and filters.

        Returns:
            Tuple of (records, total_count)
        """
        query = self.db.query(SwapRecord)

        if faculty_id:
            query = query.filter(
                or_(
                    SwapRecord.source_faculty_id == faculty_id,
                    SwapRecord.target_faculty_id == faculty_id,
                )
            )
        if status:
            query = query.filter(SwapRecord.status == status)
        if start_date:
            query = query.filter(SwapRecord.source_week >= start_date)
        if end_date:
            query = query.filter(SwapRecord.source_week <= end_date)

        total = query.count()

        records = query.order_by(SwapRecord.requested_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return records, total

    # ==========================================================================
    # Approval Methods
    # ==========================================================================

    def create_approval(
        self,
        swap_id: UUID,
        faculty_id: UUID,
        role: str,
    ) -> SwapApproval:
        """Create an approval record for a swap."""
        from uuid import uuid4

        approval = SwapApproval(
            id=uuid4(),
            swap_id=swap_id,
            faculty_id=faculty_id,
            role=role,
        )
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def get_approvals(self, swap_id: UUID) -> List[SwapApproval]:
        """Get all approvals for a swap."""
        return self.db.query(SwapApproval).filter(
            SwapApproval.swap_id == swap_id
        ).all()

    def record_approval_response(
        self,
        approval_id: UUID,
        approved: bool,
        notes: Optional[str] = None,
    ) -> Optional[SwapApproval]:
        """Record response for an approval."""
        approval = self.db.query(SwapApproval).filter(
            SwapApproval.id == approval_id
        ).first()

        if not approval:
            return None

        approval.approved = approved
        approval.responded_at = datetime.utcnow()
        approval.response_notes = notes

        self.db.commit()
        self.db.refresh(approval)
        return approval

    def is_fully_approved(self, swap_id: UUID) -> bool:
        """Check if all required approvals are granted."""
        approvals = self.get_approvals(swap_id)
        if not approvals:
            return False

        return all(a.approved is True for a in approvals)

    # ==========================================================================
    # Statistics
    # ==========================================================================

    def count_by_status(self, faculty_id: Optional[UUID] = None) -> dict:
        """Count swaps by status."""
        query = self.db.query(
            SwapRecord.status,
            func.count(SwapRecord.id)
        )

        if faculty_id:
            query = query.filter(
                or_(
                    SwapRecord.source_faculty_id == faculty_id,
                    SwapRecord.target_faculty_id == faculty_id,
                )
            )

        result = query.group_by(SwapRecord.status).all()
        return {status.value: count for status, count in result}

    def count_executed_for_faculty(
        self,
        faculty_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """Count executed swaps for a faculty member."""
        query = self.db.query(SwapRecord).filter(
            SwapRecord.status == SwapStatus.EXECUTED,
            or_(
                SwapRecord.source_faculty_id == faculty_id,
                SwapRecord.target_faculty_id == faculty_id,
            ),
        )

        if start_date:
            query = query.filter(SwapRecord.executed_at >= start_date)
        if end_date:
            query = query.filter(SwapRecord.executed_at <= end_date)

        return query.count()
