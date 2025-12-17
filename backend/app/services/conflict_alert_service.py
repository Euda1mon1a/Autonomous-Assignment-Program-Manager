"""Service for managing FMIT conflict alerts."""
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.conflict_alert import (
    ConflictAlert,
    ConflictAlertStatus,
    ConflictSeverity,
    ConflictType,
)


class ConflictAlertService:
    """
    Service for managing conflict alerts.

    Handles CRUD operations, status transitions, and queries
    for conflict alerts.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_alert(
        self,
        faculty_id: UUID,
        conflict_type: ConflictType,
        fmit_week: date,
        description: str,
        severity: ConflictSeverity = ConflictSeverity.WARNING,
        leave_id: UUID | None = None,
        swap_id: UUID | None = None,
    ) -> ConflictAlert:
        """
        Create a new conflict alert.

        Args:
            faculty_id: The affected faculty member
            conflict_type: Type of conflict
            fmit_week: The FMIT week with the conflict
            description: Human-readable description
            severity: Severity level (default: warning)
            leave_id: Optional related absence ID
            swap_id: Optional related swap ID

        Returns:
            The created ConflictAlert
        """
        # Check for existing similar alert
        existing = self.db.query(ConflictAlert).filter(
            ConflictAlert.faculty_id == faculty_id,
            ConflictAlert.conflict_type == conflict_type,
            ConflictAlert.fmit_week == fmit_week,
            ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]),
        ).first()

        if existing:
            # Update existing alert instead of creating duplicate
            existing.description = description
            existing.severity = severity
            self.db.commit()
            return existing

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

    def get_alert(self, alert_id: UUID) -> ConflictAlert | None:
        """Get an alert by ID."""
        return self.db.query(ConflictAlert).filter(
            ConflictAlert.id == alert_id
        ).first()

    def get_alerts_for_faculty(
        self,
        faculty_id: UUID,
        status: ConflictAlertStatus | None = None,
        include_resolved: bool = False,
    ) -> list[ConflictAlert]:
        """
        Get alerts for a faculty member.

        Args:
            faculty_id: The faculty member's ID
            status: Optional filter by status
            include_resolved: Whether to include resolved/ignored alerts
        """
        query = self.db.query(ConflictAlert).filter(
            ConflictAlert.faculty_id == faculty_id
        )

        if status:
            query = query.filter(ConflictAlert.status == status)
        elif not include_resolved:
            query = query.filter(
                ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
            )

        return query.order_by(ConflictAlert.created_at.desc()).all()

    def get_alerts_for_week(
        self,
        fmit_week: date,
        faculty_id: UUID | None = None,
    ) -> list[ConflictAlert]:
        """Get all alerts for a specific FMIT week."""
        query = self.db.query(ConflictAlert).filter(
            ConflictAlert.fmit_week == fmit_week
        )

        if faculty_id:
            query = query.filter(ConflictAlert.faculty_id == faculty_id)

        return query.all()

    def get_unresolved_alerts(
        self,
        faculty_id: UUID | None = None,
        severity: ConflictSeverity | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[ConflictAlert]:
        """
        Get unresolved alerts with optional filters.

        Args:
            faculty_id: Filter by faculty
            severity: Filter by severity
            start_date: Filter FMIT weeks >= start_date
            end_date: Filter FMIT weeks <= end_date
        """
        query = self.db.query(ConflictAlert).filter(
            ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED])
        )

        if faculty_id:
            query = query.filter(ConflictAlert.faculty_id == faculty_id)
        if severity:
            query = query.filter(ConflictAlert.severity == severity)
        if start_date:
            query = query.filter(ConflictAlert.fmit_week >= start_date)
        if end_date:
            query = query.filter(ConflictAlert.fmit_week <= end_date)

        return query.order_by(ConflictAlert.fmit_week).all()

    def acknowledge_alert(
        self,
        alert_id: UUID,
        user_id: UUID,
    ) -> ConflictAlert | None:
        """
        Mark an alert as acknowledged.

        Args:
            alert_id: The alert to acknowledge
            user_id: The user acknowledging

        Returns:
            The updated alert or None if not found
        """
        alert = self.get_alert(alert_id)
        if not alert:
            return None

        if alert.status == ConflictAlertStatus.NEW:
            alert.status = ConflictAlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by_id = user_id
            self.db.commit()
            self.db.refresh(alert)

        return alert

    def resolve_alert(
        self,
        alert_id: UUID,
        user_id: UUID,
        notes: str | None = None,
    ) -> ConflictAlert | None:
        """
        Mark an alert as resolved.

        Args:
            alert_id: The alert to resolve
            user_id: The user resolving
            notes: Optional resolution notes

        Returns:
            The updated alert or None if not found
        """
        alert = self.get_alert(alert_id)
        if not alert:
            return None

        if alert.status in [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]:
            alert.status = ConflictAlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by_id = user_id
            if notes:
                alert.resolution_notes = notes
            self.db.commit()
            self.db.refresh(alert)

        return alert

    def ignore_alert(
        self,
        alert_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> ConflictAlert | None:
        """
        Mark an alert as ignored (false positive).

        Args:
            alert_id: The alert to ignore
            user_id: The user ignoring
            reason: Reason for ignoring

        Returns:
            The updated alert or None if not found
        """
        alert = self.get_alert(alert_id)
        if not alert:
            return None

        if alert.status in [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]:
            alert.status = ConflictAlertStatus.IGNORED
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by_id = user_id
            alert.resolution_notes = f"Ignored: {reason}"
            self.db.commit()
            self.db.refresh(alert)

        return alert

    def delete_alert(self, alert_id: UUID) -> bool:
        """
        Delete an alert.

        Args:
            alert_id: The alert to delete

        Returns:
            True if deleted, False if not found
        """
        alert = self.get_alert(alert_id)
        if not alert:
            return False

        self.db.delete(alert)
        self.db.commit()
        return True

    def count_unresolved_by_faculty(self, faculty_id: UUID) -> int:
        """Count unresolved alerts for a faculty member."""
        return self.db.query(ConflictAlert).filter(
            ConflictAlert.faculty_id == faculty_id,
            ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]),
        ).count()

    def get_critical_alerts(self) -> list[ConflictAlert]:
        """Get all unresolved critical alerts."""
        return self.db.query(ConflictAlert).filter(
            ConflictAlert.severity == ConflictSeverity.CRITICAL,
            ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]),
        ).order_by(ConflictAlert.fmit_week).all()

    def auto_resolve_for_leave_deletion(self, leave_id: UUID) -> int:
        """
        Auto-resolve alerts when the related leave is deleted.

        Args:
            leave_id: The deleted leave ID

        Returns:
            Number of alerts auto-resolved
        """
        alerts = self.db.query(ConflictAlert).filter(
            ConflictAlert.leave_id == leave_id,
            ConflictAlert.status.in_([ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]),
        ).all()

        count = 0
        for alert in alerts:
            alert.status = ConflictAlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.resolution_notes = "Auto-resolved: Related leave record was deleted"
            count += 1

        if count > 0:
            self.db.commit()

        return count
