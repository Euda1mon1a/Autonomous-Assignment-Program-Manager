"""Repository for conflict alert data access."""
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Dict
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.conflict_alert import ConflictAlert, ConflictAlertStatus, ConflictSeverity, ConflictType


class ConflictRepository:
    """
    Repository for ConflictAlert data access.

    Provides clean data access patterns separate from business logic.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==========================================================================
    # CRUD Operations
    # ==========================================================================

    def create(
        self,
        faculty_id: UUID,
        conflict_type: ConflictType,
        fmit_week: date,
        description: str,
        severity: ConflictSeverity = ConflictSeverity.WARNING,
        leave_id: Optional[UUID] = None,
        swap_id: Optional[UUID] = None,
    ) -> ConflictAlert:
        """Create a new conflict alert."""
        from uuid import uuid4

        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=faculty_id,
            conflict_type=conflict_type,
            severity=severity,
            fmit_week=fmit_week,
            leave_id=leave_id,
            swap_id=swap_id,
            status=ConflictAlertStatus.NEW,
            description=description,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def get_by_id(self, alert_id: UUID) -> Optional[ConflictAlert]:
        """Get an alert by ID."""
        return self.db.query(ConflictAlert).filter(
            ConflictAlert.id == alert_id
        ).first()

    def update(
        self,
        alert_id: UUID,
        **kwargs
    ) -> Optional[ConflictAlert]:
        """Update an alert with arbitrary fields."""
        alert = self.get_by_id(alert_id)
        if not alert:
            return None

        for key, value in kwargs.items():
            if hasattr(alert, key):
                setattr(alert, key, value)

        self.db.commit()
        self.db.refresh(alert)
        return alert

    def delete(self, alert_id: UUID) -> bool:
        """Delete an alert."""
        alert = self.get_by_id(alert_id)
        if not alert:
            return False

        self.db.delete(alert)
        self.db.commit()
        return True

    def bulk_delete(self, alert_ids: List[UUID]) -> int:
        """Delete multiple alerts."""
        count = self.db.query(ConflictAlert).filter(
            ConflictAlert.id.in_(alert_ids)
        ).delete(synchronize_session=False)
        self.db.commit()
        return count

    # ==========================================================================
    # Query Methods
    # ==========================================================================

    def find_by_faculty(
        self,
        faculty_id: UUID,
        include_resolved: bool = False,
    ) -> List[ConflictAlert]:
        """Find alerts for a faculty member."""
        query = self.db.query(ConflictAlert).filter(
            ConflictAlert.faculty_id == faculty_id
        )

        if not include_resolved:
            query = query.filter(
                ConflictAlert.status.in_([
                    ConflictAlertStatus.NEW,
                    ConflictAlertStatus.ACKNOWLEDGED
                ])
            )

        return query.order_by(ConflictAlert.created_at.desc()).all()

    def find_by_status(
        self,
        status: ConflictAlertStatus,
        faculty_id: Optional[UUID] = None,
    ) -> List[ConflictAlert]:
        """Find alerts by status."""
        query = self.db.query(ConflictAlert).filter(
            ConflictAlert.status == status
        )

        if faculty_id:
            query = query.filter(ConflictAlert.faculty_id == faculty_id)

        return query.order_by(ConflictAlert.created_at.desc()).all()

    def find_by_severity(
        self,
        severity: ConflictSeverity,
        unresolved_only: bool = True,
    ) -> List[ConflictAlert]:
        """Find alerts by severity."""
        query = self.db.query(ConflictAlert).filter(
            ConflictAlert.severity == severity
        )

        if unresolved_only:
            query = query.filter(
                ConflictAlert.status.in_([
                    ConflictAlertStatus.NEW,
                    ConflictAlertStatus.ACKNOWLEDGED
                ])
            )

        return query.order_by(ConflictAlert.fmit_week).all()

    def find_by_week(
        self,
        fmit_week: date,
        faculty_id: Optional[UUID] = None,
    ) -> List[ConflictAlert]:
        """Find alerts for a specific FMIT week."""
        query = self.db.query(ConflictAlert).filter(
            ConflictAlert.fmit_week == fmit_week
        )

        if faculty_id:
            query = query.filter(ConflictAlert.faculty_id == faculty_id)

        return query.all()

    def find_by_leave(self, leave_id: UUID) -> List[ConflictAlert]:
        """Find alerts related to a leave record."""
        return self.db.query(ConflictAlert).filter(
            ConflictAlert.leave_id == leave_id
        ).all()

    def find_by_type(
        self,
        conflict_type: ConflictType,
        unresolved_only: bool = True,
    ) -> List[ConflictAlert]:
        """Find alerts by conflict type."""
        query = self.db.query(ConflictAlert).filter(
            ConflictAlert.conflict_type == conflict_type
        )

        if unresolved_only:
            query = query.filter(
                ConflictAlert.status.in_([
                    ConflictAlertStatus.NEW,
                    ConflictAlertStatus.ACKNOWLEDGED
                ])
            )

        return query.all()

    def find_upcoming(
        self,
        days_ahead: int = 30,
        faculty_id: Optional[UUID] = None,
    ) -> List[ConflictAlert]:
        """Find alerts for upcoming FMIT weeks."""
        cutoff = date.today() + timedelta(days=days_ahead)

        query = self.db.query(ConflictAlert).filter(
            ConflictAlert.fmit_week >= date.today(),
            ConflictAlert.fmit_week <= cutoff,
            ConflictAlert.status.in_([
                ConflictAlertStatus.NEW,
                ConflictAlertStatus.ACKNOWLEDGED
            ]),
        )

        if faculty_id:
            query = query.filter(ConflictAlert.faculty_id == faculty_id)

        return query.order_by(ConflictAlert.fmit_week).all()

    def find_with_pagination(
        self,
        page: int = 1,
        page_size: int = 20,
        faculty_id: Optional[UUID] = None,
        status: Optional[ConflictAlertStatus] = None,
        severity: Optional[ConflictSeverity] = None,
        conflict_type: Optional[ConflictType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Tuple[List[ConflictAlert], int]:
        """Find alerts with pagination and filters."""
        query = self.db.query(ConflictAlert)

        if faculty_id:
            query = query.filter(ConflictAlert.faculty_id == faculty_id)
        if status:
            query = query.filter(ConflictAlert.status == status)
        if severity:
            query = query.filter(ConflictAlert.severity == severity)
        if conflict_type:
            query = query.filter(ConflictAlert.conflict_type == conflict_type)
        if start_date:
            query = query.filter(ConflictAlert.fmit_week >= start_date)
        if end_date:
            query = query.filter(ConflictAlert.fmit_week <= end_date)

        total = query.count()

        records = query.order_by(
            ConflictAlert.fmit_week,
            ConflictAlert.severity.desc(),
        ).offset((page - 1) * page_size).limit(page_size).all()

        return records, total

    # ==========================================================================
    # Existence Checks
    # ==========================================================================

    def exists_similar(
        self,
        faculty_id: UUID,
        conflict_type: ConflictType,
        fmit_week: date,
    ) -> Optional[ConflictAlert]:
        """Check if a similar unresolved alert exists."""
        return self.db.query(ConflictAlert).filter(
            ConflictAlert.faculty_id == faculty_id,
            ConflictAlert.conflict_type == conflict_type,
            ConflictAlert.fmit_week == fmit_week,
            ConflictAlert.status.in_([
                ConflictAlertStatus.NEW,
                ConflictAlertStatus.ACKNOWLEDGED
            ]),
        ).first()

    # ==========================================================================
    # Statistics
    # ==========================================================================

    def count_by_status(
        self,
        faculty_id: Optional[UUID] = None,
    ) -> Dict[str, int]:
        """Count alerts by status."""
        query = self.db.query(
            ConflictAlert.status,
            func.count(ConflictAlert.id)
        )

        if faculty_id:
            query = query.filter(ConflictAlert.faculty_id == faculty_id)

        result = query.group_by(ConflictAlert.status).all()
        return {status.value: count for status, count in result}

    def count_by_severity(
        self,
        unresolved_only: bool = True,
        faculty_id: Optional[UUID] = None,
    ) -> Dict[str, int]:
        """Count alerts by severity."""
        query = self.db.query(
            ConflictAlert.severity,
            func.count(ConflictAlert.id)
        )

        if unresolved_only:
            query = query.filter(
                ConflictAlert.status.in_([
                    ConflictAlertStatus.NEW,
                    ConflictAlertStatus.ACKNOWLEDGED
                ])
            )

        if faculty_id:
            query = query.filter(ConflictAlert.faculty_id == faculty_id)

        result = query.group_by(ConflictAlert.severity).all()
        return {severity.value: count for severity, count in result}

    def count_unresolved(self, faculty_id: Optional[UUID] = None) -> int:
        """Count unresolved alerts."""
        query = self.db.query(ConflictAlert).filter(
            ConflictAlert.status.in_([
                ConflictAlertStatus.NEW,
                ConflictAlertStatus.ACKNOWLEDGED
            ])
        )

        if faculty_id:
            query = query.filter(ConflictAlert.faculty_id == faculty_id)

        return query.count()

    def count_critical_unresolved(self) -> int:
        """Count critical unresolved alerts."""
        return self.db.query(ConflictAlert).filter(
            ConflictAlert.severity == ConflictSeverity.CRITICAL,
            ConflictAlert.status.in_([
                ConflictAlertStatus.NEW,
                ConflictAlertStatus.ACKNOWLEDGED
            ]),
        ).count()
