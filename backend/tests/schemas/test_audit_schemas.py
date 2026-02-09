"""Tests for audit log schemas (aliases, Field bounds, nested models)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.audit import (
    AuditUser,
    FieldChange,
    AuditLogEntry,
    AuditLogResponse,
    DateRange,
    AuditLogFilters,
    AuditStatistics,
    AuditExportConfig,
    MarkReviewedRequest,
)


class TestAuditUser:
    def test_valid_minimal(self):
        r = AuditUser(id="user-1", name="Admin")
        assert r.email is None
        assert r.role is None

    def test_full(self):
        r = AuditUser(
            id="user-1", name="Admin User", email="admin@example.com", role="admin"
        )
        assert r.email == "admin@example.com"

    # --- name min_length=1 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            AuditUser(id="user-1", name="")


class TestFieldChange:
    def test_valid_with_aliases(self):
        r = FieldChange(field="status", oldValue="pending", newValue="approved")
        assert r.old_value == "pending"
        assert r.new_value == "approved"
        assert r.display_name is None

    def test_with_snake_case(self):
        r = FieldChange(field="status", old_value="pending", new_value="approved")
        assert r.old_value == "pending"

    def test_with_display_name(self):
        r = FieldChange(
            field="role",
            oldValue="resident",
            newValue="faculty",
            displayName="Role",
        )
        assert r.display_name == "Role"


class TestAuditLogEntry:
    def _make_entry(self, **overrides):
        defaults = {
            "id": "audit-1",
            "timestamp": "2026-03-01T00:00:00Z",
            "entityType": "assignment",
            "entityId": "asgn-1",
            "action": "create",
            "severity": "info",
            "user": AuditUser(id="user-1", name="Admin"),
        }
        defaults.update(overrides)
        return AuditLogEntry(**defaults)

    def test_valid_minimal(self):
        r = self._make_entry()
        assert r.entity_name is None
        assert r.changes is None
        assert r.metadata is None
        assert r.ip_address is None
        assert r.user_agent is None
        assert r.session_id is None
        assert r.reason is None
        assert r.acgme_override is None
        assert r.acgme_justification is None

    def test_with_acgme_override(self):
        r = self._make_entry(
            acgmeOverride=True,
            acgmeJustification="PD approved 80-hour exception",
        )
        assert r.acgme_override is True
        assert r.acgme_justification == "PD approved 80-hour exception"

    def test_with_changes(self):
        change = FieldChange(field="status", oldValue="pending", newValue="approved")
        r = self._make_entry(changes=[change])
        assert len(r.changes) == 1


class TestAuditLogResponse:
    def test_valid(self):
        r = AuditLogResponse(items=[], total=0, page=1, pageSize=20, totalPages=0)
        assert r.page_size == 20
        assert r.total_pages == 0


class TestDateRange:
    def test_valid(self):
        r = DateRange(start="2026-03-01", end="2026-03-31")
        assert r.start == "2026-03-01"


class TestAuditLogFilters:
    def test_all_none(self):
        r = AuditLogFilters()
        assert r.date_range is None
        assert r.entity_types is None
        assert r.actions is None
        assert r.user_ids is None
        assert r.severity is None
        assert r.search_query is None
        assert r.entity_id is None
        assert r.acgme_overrides_only is None

    def test_with_filters(self):
        dr = DateRange(start="2026-03-01", end="2026-03-31")
        r = AuditLogFilters(
            dateRange=dr,
            entityTypes=["assignment"],
            actions=["create", "update"],
            acgmeOverridesOnly=True,
        )
        assert r.date_range is not None
        assert r.acgme_overrides_only is True


class TestAuditStatistics:
    def test_valid(self):
        dr = DateRange(start="2026-03-01", end="2026-03-31")
        r = AuditStatistics(
            totalEntries=100,
            entriesByAction={"create": 50, "update": 30, "delete": 20},
            entriesByEntityType={"assignment": 80, "person": 20},
            entriesBySeverity={"info": 90, "warning": 10},
            acgmeOverrideCount=5,
            uniqueUsers=10,
            dateRange=dr,
        )
        assert r.total_entries == 100
        assert r.acgme_override_count == 5


class TestAuditExportConfig:
    def test_valid_minimal(self):
        r = AuditExportConfig(format="csv")
        assert r.filters is None
        assert r.include_metadata is None
        assert r.include_changes is None
        assert r.date_format is None

    def test_full(self):
        filters = AuditLogFilters(actions=["create"])
        r = AuditExportConfig(
            format="pdf",
            filters=filters,
            includeMetadata=True,
            includeChanges=True,
            dateFormat="YYYY-MM-DD",
        )
        assert r.include_metadata is True


class TestMarkReviewedRequest:
    def test_valid(self):
        r = MarkReviewedRequest(ids=["audit-1", "audit-2"], reviewedBy="admin-1")
        assert len(r.ids) == 2
        assert r.notes is None

    # --- ids min_length=1 ---

    def test_ids_empty(self):
        with pytest.raises(ValidationError):
            MarkReviewedRequest(ids=[], reviewedBy="admin-1")

    # --- notes max_length=1000 ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            MarkReviewedRequest(ids=["audit-1"], reviewedBy="admin-1", notes="x" * 1001)
