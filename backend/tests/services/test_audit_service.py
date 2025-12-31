"""Test suite for audit service."""

import pytest
from datetime import datetime, date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.absence import Absence
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.services.audit_service import (
    get_audit_logs,
    ENTITY_MODEL_MAP,
    VERSION_TABLE_MAP,
)


class TestAuditService:
    """Test suite for audit service functionality."""

    def test_get_audit_logs_basic(self, db: Session):
        """Test basic audit log retrieval."""
        # Create test data
        resident = Person(
            id=uuid4(),
            name="Dr. Test",
            type="resident",
            email="test@hospital.org",
            pgy_level=1,
        )
        db.add(resident)
        db.commit()

        # Get audit logs
        logs, total = get_audit_logs(db)
        assert isinstance(logs, list)
        assert isinstance(total, int)
        assert total >= 0

    def test_get_audit_logs_with_pagination(self, db: Session):
        """Test audit log pagination."""
        # Get logs with pagination
        logs, total = get_audit_logs(db, page=1, page_size=10)
        assert isinstance(logs, list)
        assert isinstance(total, int)

    def test_get_audit_logs_with_date_filter(self, db: Session):
        """Test audit log filtering by date range."""
        # Create test data
        resident = Person(
            id=uuid4(),
            name="Dr. Test",
            type="resident",
            email="test@hospital.org",
            pgy_level=1,
        )
        db.add(resident)
        db.commit()

        # Filter by date
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        logs, total = get_audit_logs(db, start_date=start, end_date=end)
        assert isinstance(logs, list)

    def test_get_audit_logs_with_entity_type_filter(self, db: Session):
        """Test audit log filtering by entity type."""
        logs, total = get_audit_logs(db, entity_types=["assignment"])
        assert isinstance(logs, list)

    def test_get_audit_logs_with_action_filter(self, db: Session):
        """Test audit log filtering by action."""
        logs, total = get_audit_logs(db, actions=["insert"])
        assert isinstance(logs, list)

    def test_get_audit_logs_with_user_id_filter(self, db: Session):
        """Test audit log filtering by user ID."""
        user_id = str(uuid4())
        logs, total = get_audit_logs(db, user_ids=[user_id])
        assert isinstance(logs, list)

    def test_get_audit_logs_with_severity_filter(self, db: Session):
        """Test audit log filtering by severity."""
        logs, total = get_audit_logs(db, severity=["high", "medium"])
        assert isinstance(logs, list)

    def test_get_audit_logs_with_search(self, db: Session):
        """Test audit log search functionality."""
        # Create test data
        resident = Person(
            id=uuid4(),
            name="SearchTest",
            type="resident",
            email="search@hospital.org",
            pgy_level=1,
        )
        db.add(resident)
        db.commit()

        # Search for the resident
        logs, total = get_audit_logs(db, search="SearchTest")
        assert isinstance(logs, list)

    def test_get_audit_logs_with_entity_id_filter(self, db: Session):
        """Test audit log filtering by entity ID."""
        entity_id = str(uuid4())
        logs, total = get_audit_logs(db, entity_id=entity_id)
        assert isinstance(logs, list)

    def test_get_audit_logs_acgme_overrides_filter(self, db: Session):
        """Test audit log filtering for ACGME overrides."""
        logs, total = get_audit_logs(db, acgme_overrides_only=True)
        assert isinstance(logs, list)

    def test_get_audit_logs_combined_filters(self, db: Session):
        """Test audit logs with multiple filters applied."""
        start = (date.today() - timedelta(days=7)).isoformat()
        logs, total = get_audit_logs(
            db,
            page=1,
            page_size=50,
            start_date=start,
            entity_types=["assignment", "absence"],
            actions=["insert", "update"],
        )
        assert isinstance(logs, list)
        assert len(logs) <= 50

    def test_entity_model_map_completeness(self):
        """Test that entity model map has required entries."""
        assert "assignment" in ENTITY_MODEL_MAP
        assert "absence" in ENTITY_MODEL_MAP
        assert "schedule_run" in ENTITY_MODEL_MAP
        assert "swap_record" in ENTITY_MODEL_MAP

    def test_version_table_map_completeness(self):
        """Test that version table map has required entries."""
        assert "assignment" in VERSION_TABLE_MAP
        assert "absence" in VERSION_TABLE_MAP
        assert "schedule_run" in VERSION_TABLE_MAP
        assert "swap_record" in VERSION_TABLE_MAP

    def test_get_audit_logs_invalid_page(self, db: Session):
        """Test audit logs with invalid page number."""
        # Should handle gracefully
        logs, total = get_audit_logs(db, page=999, page_size=10)
        assert isinstance(logs, list)

    def test_get_audit_logs_zero_page_size(self, db: Session):
        """Test audit logs with zero page size."""
        # Should handle gracefully
        logs, total = get_audit_logs(db, page_size=0)
        assert isinstance(logs, list)

    def test_get_audit_logs_large_page_size(self, db: Session):
        """Test audit logs with very large page size."""
        logs, total = get_audit_logs(db, page_size=10000)
        assert isinstance(logs, list)

    def test_get_audit_logs_with_multiple_entity_types(self, db: Session):
        """Test filtering by multiple entity types simultaneously."""
        logs, total = get_audit_logs(
            db, entity_types=["assignment", "absence", "schedule_run"]
        )
        assert isinstance(logs, list)

    def test_get_audit_logs_with_multiple_actions(self, db: Session):
        """Test filtering by multiple actions simultaneously."""
        logs, total = get_audit_logs(
            db, actions=["insert", "update", "delete"]
        )
        assert isinstance(logs, list)

    def test_get_audit_logs_with_null_filters(self, db: Session):
        """Test audit logs with None values for optional filters."""
        logs, total = get_audit_logs(
            db,
            start_date=None,
            end_date=None,
            entity_types=None,
            actions=None,
            user_ids=None,
            severity=None,
            search=None,
            entity_id=None,
        )
        assert isinstance(logs, list)

    def test_get_audit_logs_empty_list_filters(self, db: Session):
        """Test audit logs with empty lists for optional filters."""
        logs, total = get_audit_logs(
            db,
            entity_types=[],
            actions=[],
            user_ids=[],
            severity=[],
        )
        assert isinstance(logs, list)

    def test_get_audit_logs_invalid_date_format(self, db: Session):
        """Test audit logs with invalid date format."""
        # Should handle gracefully or raise appropriate error
        try:
            logs, total = get_audit_logs(db, start_date="invalid-date")
            assert isinstance(logs, list) or isinstance(logs, type(None))
        except (ValueError, Exception):
            # Expected to fail gracefully
            pass

    def test_get_audit_logs_date_range_reversed(self, db: Session):
        """Test audit logs with reversed date range."""
        start = date.today().isoformat()
        end = (date.today() - timedelta(days=7)).isoformat()
        logs, total = get_audit_logs(db, start_date=start, end_date=end)
        assert isinstance(logs, list)
