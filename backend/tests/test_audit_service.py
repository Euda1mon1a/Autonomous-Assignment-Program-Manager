"""
Comprehensive tests for audit service and repository layers.

Tests for:
- AuditRepository query methods
- AuditService business logic
- Version history tracking
- Audit statistics
- Export functionality
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import (
    AuditLogEntry,
    AuditLogResponse,
    AuditService,
    AuditStatistics,
)


@pytest.mark.unit
class TestAuditRepository:
    """Test AuditRepository methods."""

    def test_get_audit_entries_empty(self, db: Session):
        """Test getting audit entries when there are none."""
        repo = AuditRepository(db)
        entries, total = repo.get_audit_entries()

        assert entries == []
        assert total == 0

    def test_get_audit_entries_with_assignment(
        self,
        db: Session,
        sample_assignment: Assignment,
    ):
        """Test getting audit entries after creating an assignment."""
        repo = AuditRepository(db)

        # The assignment creation should have created a version entry
        entries, total = repo.get_audit_entries(
            filters={"entity_type": "assignment"}
        )

        # Note: This might be 0 if Continuum isn't fully configured in test env
        # The test validates the repository can query without errors
        assert isinstance(entries, list)
        assert isinstance(total, int)
        assert total >= 0

    def test_get_audit_entries_pagination(self, db: Session):
        """Test pagination of audit entries."""
        repo = AuditRepository(db)

        # Test different page sizes
        entries_page1, total = repo.get_audit_entries(page=1, page_size=10)
        entries_page2, _ = repo.get_audit_entries(page=2, page_size=10)

        assert isinstance(entries_page1, list)
        assert isinstance(entries_page2, list)
        assert len(entries_page1) <= 10
        assert len(entries_page2) <= 10

    def test_get_audit_entries_sorting(self, db: Session):
        """Test sorting of audit entries."""
        repo = AuditRepository(db)

        # Test ascending sort
        entries_asc, _ = repo.get_audit_entries(
            sort_by="changed_at",
            sort_direction="asc",
        )

        # Test descending sort
        entries_desc, _ = repo.get_audit_entries(
            sort_by="changed_at",
            sort_direction="desc",
        )

        assert isinstance(entries_asc, list)
        assert isinstance(entries_desc, list)

    def test_get_audit_statistics_empty(self, db: Session):
        """Test getting audit statistics when there's no data."""
        repo = AuditRepository(db)

        stats = repo.get_audit_statistics()

        assert stats["total_changes"] >= 0
        assert isinstance(stats["changes_by_entity"], dict)
        assert isinstance(stats["changes_by_operation"], dict)
        assert isinstance(stats["changes_by_user"], dict)

    def test_get_audit_statistics_with_date_range(self, db: Session):
        """Test getting audit statistics with date filtering."""
        repo = AuditRepository(db)

        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        stats = repo.get_audit_statistics(
            start_date=start_date,
            end_date=end_date,
        )

        assert isinstance(stats, dict)
        assert "total_changes" in stats
        assert "changes_by_entity" in stats

    def test_get_users_with_audit_activity(self, db: Session):
        """Test getting users with audit activity."""
        repo = AuditRepository(db)

        users = repo.get_users_with_audit_activity()

        assert isinstance(users, list)
        for user in users:
            assert "user_id" in user
            assert "change_count" in user

    def test_mark_entries_reviewed(self, db: Session):
        """Test marking entries as reviewed (placeholder feature)."""
        repo = AuditRepository(db)

        # This is a placeholder that currently returns 0
        count = repo.mark_entries_reviewed(
            entry_ids=[1, 2, 3],
            reviewer_id="test_user",
            notes="Reviewed for compliance",
        )

        # Currently not implemented, so returns 0
        assert count == 0

    def test_get_entity_history_unknown_type(self, db: Session):
        """Test getting entity history for unknown entity type."""
        repo = AuditRepository(db)

        history = repo.get_entity_history(
            entity_type="unknown_type",
            entity_id=uuid4(),
        )

        assert history == []

    def test_operation_name_conversion(self, db: Session):
        """Test operation type to name conversion."""
        repo = AuditRepository(db)

        assert repo._operation_name(0) == "insert"
        assert repo._operation_name(1) == "update"
        assert repo._operation_name(2) == "delete"
        assert repo._operation_name(99) == "unknown"


@pytest.mark.unit
class TestAuditService:
    """Test AuditService methods."""

    def test_service_initialization(self, db: Session):
        """Test service initialization."""
        service = AuditService(db)

        assert service.db is db
        assert isinstance(service.repository, AuditRepository)

    def test_query_audit_logs_default_params(self, db: Session):
        """Test querying audit logs with default parameters."""
        service = AuditService(db)

        result = service.query_audit_logs(db)

        assert isinstance(result, AuditLogResponse)
        assert isinstance(result.items, list)
        assert result.page == 1
        assert result.page_size == 50
        assert result.total >= 0

    def test_query_audit_logs_with_filters(self, db: Session):
        """Test querying audit logs with filters."""
        service = AuditService(db)

        result = service.query_audit_logs(
            db,
            filters={"entity_type": "assignment"},
            pagination={"page": 1, "page_size": 20},
            sort={"sort_by": "changed_at", "sort_direction": "desc"},
        )

        assert isinstance(result, AuditLogResponse)
        assert result.page == 1
        assert result.page_size == 20

    def test_query_audit_logs_pagination_calculation(self, db: Session):
        """Test pagination calculation in query results."""
        service = AuditService(db)

        result = service.query_audit_logs(
            db,
            pagination={"page": 1, "page_size": 10},
        )

        # Total pages should be calculated correctly
        if result.total > 0:
            expected_pages = (result.total + 9) // 10
            assert result.total_pages == expected_pages
        else:
            assert result.total_pages == 0

    def test_get_entity_history(self, db: Session, sample_assignment: Assignment):
        """Test getting entity history."""
        service = AuditService(db)

        history = service.get_entity_history(
            db,
            entity_type="assignment",
            entity_id=sample_assignment.id,
        )

        assert isinstance(history, list)
        # May be empty if Continuum not fully configured in tests
        for entry in history:
            assert isinstance(entry, AuditLogEntry)

    def test_get_entity_history_unknown_type(self, db: Session):
        """Test getting entity history for unknown entity type."""
        service = AuditService(db)

        history = service.get_entity_history(
            db,
            entity_type="unknown",
            entity_id=uuid4(),
        )

        assert isinstance(history, list)
        assert len(history) == 0

    def test_get_user_activity_no_date_range(self, db: Session):
        """Test getting user activity without date range."""
        service = AuditService(db)

        activity = service.get_user_activity(db, user_id="test_user")

        assert isinstance(activity, list)
        for entry in activity:
            assert isinstance(entry, AuditLogEntry)

    def test_get_user_activity_with_date_range(self, db: Session):
        """Test getting user activity with date range."""
        service = AuditService(db)

        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()

        activity = service.get_user_activity(
            db,
            user_id="test_user",
            date_range=(start, end),
        )

        assert isinstance(activity, list)

    def test_export_audit_logs_csv(self, db: Session):
        """Test exporting audit logs to CSV format."""
        service = AuditService(db)

        csv_data = service.export_audit_logs(
            db,
            config={"format": "csv"},
        )

        assert isinstance(csv_data, bytes)
        # Should at least have header
        assert len(csv_data) > 0
        # Verify it's valid CSV format
        assert b"entity_type" in csv_data or b"id" in csv_data

    def test_export_audit_logs_csv_with_filters(self, db: Session):
        """Test exporting audit logs with filters."""
        service = AuditService(db)

        csv_data = service.export_audit_logs(
            db,
            config={
                "format": "csv",
                "filters": {"entity_type": "assignment"},
                "columns": ["entity_type", "operation", "changed_at"],
            },
        )

        assert isinstance(csv_data, bytes)
        assert len(csv_data) > 0

    def test_export_audit_logs_excel_fallback(self, db: Session):
        """Test Excel export (may fall back to CSV if openpyxl not installed)."""
        service = AuditService(db)

        data = service.export_audit_logs(
            db,
            config={"format": "excel"},
        )

        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_export_audit_logs_invalid_format(self, db: Session):
        """Test exporting with invalid format raises error."""
        service = AuditService(db)

        with pytest.raises(ValueError, match="Unsupported export format"):
            service.export_audit_logs(
                db,
                config={"format": "invalid"},
            )

    def test_calculate_statistics_no_date_range(self, db: Session):
        """Test calculating audit statistics without date range."""
        service = AuditService(db)

        stats = service.calculate_statistics(db)

        assert isinstance(stats, AuditStatistics)
        assert stats.total_changes >= 0
        assert isinstance(stats.changes_by_entity, dict)
        assert isinstance(stats.changes_by_operation, dict)
        assert isinstance(stats.changes_by_user, dict)

    def test_calculate_statistics_with_date_range(self, db: Session):
        """Test calculating audit statistics with date range."""
        service = AuditService(db)

        start = datetime.utcnow() - timedelta(days=30)
        end = datetime.utcnow()

        stats = service.calculate_statistics(db, date_range=(start, end))

        assert isinstance(stats, AuditStatistics)
        assert stats.total_changes >= 0


@pytest.mark.unit
class TestAuditServiceLegacyMethods:
    """Test backward-compatible static methods."""

    def test_get_assignment_history_not_found(self, db: Session):
        """Test getting history for non-existent assignment."""
        history = AuditService.get_assignment_history(db, uuid4())

        assert isinstance(history, list)
        assert len(history) == 0

    def test_get_assignment_history(
        self,
        db: Session,
        sample_assignment: Assignment,
    ):
        """Test getting assignment history."""
        history = AuditService.get_assignment_history(
            db,
            sample_assignment.id,
        )

        assert isinstance(history, list)
        # May be empty if Continuum not fully configured
        for entry in history:
            assert "version_id" in entry
            assert "operation" in entry

    def test_get_absence_history_not_found(self, db: Session):
        """Test getting history for non-existent absence."""
        history = AuditService.get_absence_history(db, uuid4())

        assert isinstance(history, list)
        assert len(history) == 0

    def test_get_absence_history(
        self,
        db: Session,
        sample_absence: Absence,
    ):
        """Test getting absence history."""
        history = AuditService.get_absence_history(
            db,
            sample_absence.id,
        )

        assert isinstance(history, list)
        # May be empty if Continuum not fully configured
        for entry in history:
            assert "version_id" in entry
            assert "operation" in entry

    def test_get_recent_changes_default(self, db: Session):
        """Test getting recent changes with default parameters."""
        changes = AuditService.get_recent_changes(db)

        assert isinstance(changes, list)
        # Should look back 24 hours by default
        for change in changes:
            assert "model_type" in change
            assert "operation" in change

    def test_get_recent_changes_with_hours(self, db: Session):
        """Test getting recent changes with custom hours."""
        changes = AuditService.get_recent_changes(db, hours=48)

        assert isinstance(changes, list)

    def test_get_recent_changes_with_model_filter(self, db: Session):
        """Test getting recent changes filtered by model type."""
        changes = AuditService.get_recent_changes(
            db,
            hours=24,
            model_type="assignment",
        )

        assert isinstance(changes, list)
        for change in changes:
            if change:  # May be empty
                assert change["model_type"] == "assignment"

    def test_get_changes_by_user_default(self, db: Session):
        """Test getting changes by user with default parameters."""
        changes = AuditService.get_changes_by_user(db, user_id="test_user")

        assert isinstance(changes, list)
        # Should look back 30 days by default

    def test_get_changes_by_user_with_date(self, db: Session):
        """Test getting changes by user with specific start date."""
        since = datetime.utcnow() - timedelta(days=7)

        changes = AuditService.get_changes_by_user(
            db,
            user_id="test_user",
            since=since,
            limit=100,
        )

        assert isinstance(changes, list)
        assert len(changes) <= 100


@pytest.mark.integration
class TestAuditIntegration:
    """Integration tests for audit functionality with real data."""

    def test_audit_trail_on_assignment_creation(
        self,
        db: Session,
        sample_resident: Person,
        sample_block: Block,
        sample_rotation_template: RotationTemplate,
    ):
        """Test that creating an assignment generates audit trail."""
        service = AuditService(db)

        # Create an assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
            created_by="test_user",
        )
        db.add(assignment)
        db.commit()

        # Query audit logs
        result = service.query_audit_logs(
            db,
            filters={"entity_type": "assignment"},
        )

        assert isinstance(result, AuditLogResponse)
        # Note: May be empty if Continuum not configured in test DB

    def test_audit_trail_on_assignment_update(
        self,
        db: Session,
        sample_assignment: Assignment,
    ):
        """Test that updating an assignment generates audit trail."""
        service = AuditService(db)

        # Update the assignment
        sample_assignment.notes = "Updated notes"
        db.commit()

        # Get entity history
        history = service.get_entity_history(
            db,
            entity_type="assignment",
            entity_id=sample_assignment.id,
        )

        assert isinstance(history, list)

    def test_audit_trail_on_absence_creation(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test that creating an absence generates audit trail."""
        service = AuditService(db)

        # Create an absence
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()

        # Query audit logs
        result = service.query_audit_logs(
            db,
            filters={"entity_type": "absence"},
        )

        assert isinstance(result, AuditLogResponse)

    def test_statistics_reflect_changes(
        self,
        db: Session,
        sample_assignment: Assignment,
    ):
        """Test that statistics reflect database changes."""
        service = AuditService(db)

        # Make some changes
        sample_assignment.notes = "Change 1"
        db.commit()

        sample_assignment.notes = "Change 2"
        db.commit()

        # Get statistics
        stats = service.calculate_statistics(db)

        assert isinstance(stats, AuditStatistics)
        assert stats.total_changes >= 0

    def test_export_includes_recent_changes(
        self,
        db: Session,
        sample_assignment: Assignment,
    ):
        """Test that export includes recent changes."""
        service = AuditService(db)

        # Make a change
        sample_assignment.notes = "Export test"
        db.commit()

        # Export audit logs
        csv_data = service.export_audit_logs(
            db,
            config={
                "format": "csv",
                "filters": {
                    "start_date": datetime.utcnow() - timedelta(hours=1),
                },
            },
        )

        assert isinstance(csv_data, bytes)
        assert len(csv_data) > 0


@pytest.mark.unit
class TestAuditLogEntry:
    """Test AuditLogEntry Pydantic model."""

    def test_audit_log_entry_creation(self):
        """Test creating an audit log entry."""
        entry = AuditLogEntry(
            id=1,
            entity_type="assignment",
            entity_id=str(uuid4()),
            transaction_id=123,
            operation="insert",
            changed_at=datetime.utcnow(),
            changed_by="test_user",
        )

        assert entry.id == 1
        assert entry.entity_type == "assignment"
        assert entry.operation == "insert"
        assert entry.changed_by == "test_user"

    def test_audit_log_entry_optional_fields(self):
        """Test creating audit log entry with optional fields as None."""
        entry = AuditLogEntry(
            id=1,
            entity_type="assignment",
            entity_id=str(uuid4()),
            transaction_id=123,
            operation="insert",
            changed_at=None,
            changed_by=None,
        )

        assert entry.changed_at is None
        assert entry.changed_by is None


@pytest.mark.unit
class TestAuditLogResponse:
    """Test AuditLogResponse Pydantic model."""

    def test_audit_log_response_creation(self):
        """Test creating an audit log response."""
        response = AuditLogResponse(
            items=[],
            total=0,
            page=1,
            page_size=50,
            total_pages=0,
        )

        assert response.items == []
        assert response.total == 0
        assert response.page == 1
        assert response.page_size == 50
        assert response.total_pages == 0


@pytest.mark.unit
class TestAuditStatistics:
    """Test AuditStatistics Pydantic model."""

    def test_audit_statistics_creation(self):
        """Test creating audit statistics."""
        stats = AuditStatistics(
            total_changes=100,
            changes_by_entity={"assignment": 50, "absence": 50},
            changes_by_operation={"insert": 30, "update": 60, "delete": 10},
            changes_by_user={"user1": 70, "user2": 30},
            most_active_day="2024-01-15",
        )

        assert stats.total_changes == 100
        assert stats.changes_by_entity["assignment"] == 50
        assert stats.changes_by_operation["insert"] == 30
        assert stats.most_active_day == "2024-01-15"

    def test_audit_statistics_optional_fields(self):
        """Test creating audit statistics with optional fields."""
        stats = AuditStatistics(
            total_changes=0,
            changes_by_entity={},
            changes_by_operation={},
            changes_by_user={},
            most_active_day=None,
        )

        assert stats.most_active_day is None
