"""Tests for audit API routes."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient


class TestAuditLogsEndpoint:
    """Tests for GET /api/audit/logs endpoint."""

    def test_get_logs_default_params(self, client: TestClient):
        """Test getting audit logs with default parameters."""
        response = client.get("/api/audit/logs")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pageSize" in data
        assert "totalPages" in data
        assert isinstance(data["items"], list)
        assert data["page"] == 1
        assert data["pageSize"] == 25

    def test_get_logs_custom_pagination(self, client: TestClient):
        """Test pagination parameters."""
        response = client.get(
            "/api/audit/logs",
            params={"page": 2, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["pageSize"] == 10

    def test_get_logs_filter_by_entity_type(self, client: TestClient):
        """Test filtering by entity types."""
        response = client.get(
            "/api/audit/logs",
            params={"entity_types": "assignment,person"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)

        # All returned items should be assignment or person
        for item in data["items"]:
            assert item["entityType"] in ["assignment", "person"]

    def test_get_logs_filter_by_action(self, client: TestClient):
        """Test filtering by action types."""
        response = client.get(
            "/api/audit/logs",
            params={"actions": "create,update"}
        )

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert item["action"] in ["create", "update"]

    def test_get_logs_filter_by_severity(self, client: TestClient):
        """Test filtering by severity levels."""
        response = client.get(
            "/api/audit/logs",
            params={"severity": "warning,critical"}
        )

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert item["severity"] in ["warning", "critical"]

    def test_get_logs_filter_by_user(self, client: TestClient):
        """Test filtering by user IDs."""
        response = client.get(
            "/api/audit/logs",
            params={"user_ids": "user-001,user-002"}
        )

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert item["user"]["id"] in ["user-001", "user-002"]

    def test_get_logs_acgme_overrides_only(self, client: TestClient):
        """Test filtering for ACGME overrides only."""
        response = client.get(
            "/api/audit/logs",
            params={"acgme_overrides_only": True}
        )

        assert response.status_code == 200
        data = response.json()

        # All returned items should have ACGME override
        for item in data["items"]:
            assert item.get("acgmeOverride") is True

    def test_get_logs_search_query(self, client: TestClient):
        """Test search functionality."""
        response = client.get(
            "/api/audit/logs",
            params={"search": "ACGME"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)

    def test_get_logs_date_range_filter(self, client: TestClient):
        """Test filtering by date range."""
        now = datetime.utcnow()
        start = (now - timedelta(days=7)).isoformat()
        end = now.isoformat()

        response = client.get(
            "/api/audit/logs",
            params={
                "start_date": start,
                "end_date": end
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)

    def test_get_logs_entity_id_filter(self, client: TestClient):
        """Test filtering by specific entity ID."""
        response = client.get(
            "/api/audit/logs",
            params={"entity_id": "assign-123"}
        )

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert item["entityId"] == "assign-123"

    def test_get_logs_sorting(self, client: TestClient):
        """Test sorting parameters."""
        response = client.get(
            "/api/audit/logs",
            params={
                "sort_by": "timestamp",
                "sort_direction": "asc"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)

    def test_get_logs_combined_filters(self, client: TestClient):
        """Test multiple filters combined."""
        response = client.get(
            "/api/audit/logs",
            params={
                "entity_types": "assignment",
                "actions": "override",
                "severity": "warning,critical",
                "page": 1,
                "page_size": 50
            }
        )

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert item["entityType"] == "assignment"
            assert item["action"] == "override"
            assert item["severity"] in ["warning", "critical"]

    def test_get_logs_invalid_page(self, client: TestClient):
        """Test validation for invalid page number."""
        response = client.get(
            "/api/audit/logs",
            params={"page": 0}
        )

        assert response.status_code == 422  # Validation error

    def test_get_logs_invalid_page_size(self, client: TestClient):
        """Test validation for invalid page size."""
        response = client.get(
            "/api/audit/logs",
            params={"page_size": 200}  # Over 100 limit
        )

        assert response.status_code == 422


class TestAuditLogByIdEndpoint:
    """Tests for GET /api/audit/logs/{id} endpoint."""

    def test_get_log_by_id_exists(self, client: TestClient):
        """Test getting an existing audit log by ID."""
        # First get a list to find a valid ID
        list_response = client.get("/api/audit/logs")
        items = list_response.json()["items"]

        if items:
            log_id = items[0]["id"]
            response = client.get(f"/api/audit/logs/{log_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == log_id
            assert "timestamp" in data
            assert "entityType" in data
            assert "action" in data
            assert "user" in data

    def test_get_log_by_id_not_found(self, client: TestClient):
        """Test getting a non-existent audit log."""
        response = client.get("/api/audit/logs/nonexistent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_log_with_changes(self, client: TestClient):
        """Test audit log includes field changes."""
        # Get a log with changes (like audit-001)
        response = client.get("/api/audit/logs/audit-001")

        if response.status_code == 200:
            data = response.json()
            if data.get("changes"):
                assert isinstance(data["changes"], list)
                for change in data["changes"]:
                    assert "field" in change
                    assert "oldValue" in change
                    assert "newValue" in change

    def test_get_log_with_acgme_override(self, client: TestClient):
        """Test audit log with ACGME override information."""
        # Get a log with ACGME override (like audit-002)
        response = client.get("/api/audit/logs/audit-002")

        if response.status_code == 200:
            data = response.json()
            if data.get("acgmeOverride"):
                assert data["acgmeOverride"] is True
                assert "acgmeJustification" in data


class TestAuditStatisticsEndpoint:
    """Tests for GET /api/audit/statistics endpoint."""

    def test_get_statistics_default(self, client: TestClient):
        """Test getting statistics with default parameters."""
        response = client.get("/api/audit/statistics")

        assert response.status_code == 200
        data = response.json()
        assert "totalEntries" in data
        assert "entriesByAction" in data
        assert "entriesByEntityType" in data
        assert "entriesBySeverity" in data
        assert "acgmeOverrideCount" in data
        assert "uniqueUsers" in data
        assert "dateRange" in data

        # Validate structure of grouped counts
        assert isinstance(data["entriesByAction"], dict)
        assert isinstance(data["entriesByEntityType"], dict)
        assert isinstance(data["entriesBySeverity"], dict)

        # Validate date range
        assert "start" in data["dateRange"]
        assert "end" in data["dateRange"]

    def test_get_statistics_with_date_range(self, client: TestClient):
        """Test statistics with custom date range."""
        now = datetime.utcnow()
        start = (now - timedelta(days=30)).isoformat()
        end = now.isoformat()

        response = client.get(
            "/api/audit/statistics",
            params={
                "start_date": start,
                "end_date": end
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["totalEntries"], int)
        assert data["totalEntries"] >= 0

    def test_statistics_counts_accuracy(self, client: TestClient):
        """Test that statistics counts are consistent."""
        response = client.get("/api/audit/statistics")

        assert response.status_code == 200
        data = response.json()

        # Sum of all action counts should be <= total entries
        action_sum = sum(data["entriesByAction"].values())
        assert action_sum <= data["totalEntries"] or action_sum == data["totalEntries"]

        # ACGME override count should be <= total
        assert data["acgmeOverrideCount"] <= data["totalEntries"]

        # Unique users should be > 0 if there are entries
        if data["totalEntries"] > 0:
            assert data["uniqueUsers"] > 0


class TestAuditUsersEndpoint:
    """Tests for GET /api/audit/users endpoint."""

    def test_get_users_list(self, client: TestClient):
        """Test getting list of users with audit activity."""
        response = client.get("/api/audit/users")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Validate user structure
        if data:
            user = data[0]
            assert "id" in user
            assert "name" in user
            # email and role are optional

    def test_users_list_not_empty(self, client: TestClient):
        """Test that users list contains expected users."""
        response = client.get("/api/audit/users")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0


class TestAuditExportEndpoint:
    """Tests for POST /api/audit/export endpoint."""

    def test_export_json_format(self, client: TestClient):
        """Test exporting audit logs in JSON format."""
        response = client.post(
            "/api/audit/export",
            json={
                "format": "json",
                "includeMetadata": True,
                "includeChanges": True
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers.get("content-disposition", "")
        assert "audit_logs.json" in response.headers.get("content-disposition", "")

    def test_export_csv_format(self, client: TestClient):
        """Test exporting audit logs in CSV format."""
        response = client.post(
            "/api/audit/export",
            json={
                "format": "csv",
                "includeMetadata": False,
                "includeChanges": True
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
        assert "audit_logs.csv" in response.headers.get("content-disposition", "")

    def test_export_pdf_format(self, client: TestClient):
        """Test exporting audit logs in PDF format."""
        response = client.post(
            "/api/audit/export",
            json={
                "format": "pdf",
                "includeMetadata": True,
                "includeChanges": True
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "audit_logs.pdf" in response.headers.get("content-disposition", "")

    def test_export_with_filters(self, client: TestClient):
        """Test exporting with filters applied."""
        response = client.post(
            "/api/audit/export",
            json={
                "format": "json",
                "filters": {
                    "entityTypes": ["assignment"],
                    "actions": ["override"],
                    "severity": ["critical"],
                    "acgmeOverridesOnly": True
                }
            }
        )

        assert response.status_code == 200

    def test_export_with_date_range(self, client: TestClient):
        """Test exporting with date range filter."""
        now = datetime.utcnow()
        start = (now - timedelta(days=7)).isoformat()
        end = now.isoformat()

        response = client.post(
            "/api/audit/export",
            json={
                "format": "csv",
                "filters": {
                    "dateRange": {
                        "start": start,
                        "end": end
                    }
                }
            }
        )

        assert response.status_code == 200

    def test_export_invalid_format(self, client: TestClient):
        """Test export with invalid format."""
        response = client.post(
            "/api/audit/export",
            json={
                "format": "xml"  # Unsupported format
            }
        )

        assert response.status_code == 400
        assert "unsupported" in response.json()["detail"].lower()

    def test_export_json_contains_data(self, client: TestClient):
        """Test that JSON export contains valid data."""
        response = client.post(
            "/api/audit/export",
            json={"format": "json"}
        )

        assert response.status_code == 200
        # The response should be valid JSON
        import json
        data = json.loads(response.content)
        assert isinstance(data, list)

    def test_export_csv_has_headers(self, client: TestClient):
        """Test that CSV export has proper headers."""
        response = client.post(
            "/api/audit/export",
            json={"format": "csv"}
        )

        assert response.status_code == 200
        content = response.content.decode('utf-8')
        lines = content.split('\n')

        # First line should be headers
        assert len(lines) > 0
        headers = lines[0]
        assert "ID" in headers
        assert "Timestamp" in headers
        assert "Entity Type" in headers


class TestMarkReviewedEndpoint:
    """Tests for POST /api/audit/mark-reviewed endpoint."""

    def test_mark_reviewed_success(self, client: TestClient):
        """Test successfully marking entries as reviewed."""
        response = client.post(
            "/api/audit/mark-reviewed",
            json={
                "ids": ["audit-001", "audit-002"],
                "reviewedBy": "user-001",
                "notes": "Reviewed for monthly compliance check"
            }
        )

        assert response.status_code == 204

    def test_mark_reviewed_no_notes(self, client: TestClient):
        """Test marking reviewed without notes."""
        response = client.post(
            "/api/audit/mark-reviewed",
            json={
                "ids": ["audit-001"],
                "reviewedBy": "user-002"
            }
        )

        assert response.status_code == 204

    def test_mark_reviewed_empty_ids(self, client: TestClient):
        """Test validation for empty IDs list."""
        response = client.post(
            "/api/audit/mark-reviewed",
            json={
                "ids": [],
                "reviewedBy": "user-001"
            }
        )

        assert response.status_code == 400
        assert "no audit entry ids" in response.json()["detail"].lower()

    def test_mark_reviewed_missing_reviewer(self, client: TestClient):
        """Test validation for missing reviewer."""
        response = client.post(
            "/api/audit/mark-reviewed",
            json={
                "ids": ["audit-001"]
            }
        )

        assert response.status_code == 422  # Validation error

    def test_mark_reviewed_single_entry(self, client: TestClient):
        """Test marking a single entry as reviewed."""
        response = client.post(
            "/api/audit/mark-reviewed",
            json={
                "ids": ["audit-007"],  # Critical ACGME override
                "reviewedBy": "user-002",
                "notes": "Reviewed emergency override - appropriate justification"
            }
        )

        assert response.status_code == 204

    def test_mark_reviewed_multiple_entries(self, client: TestClient):
        """Test marking multiple entries as reviewed."""
        response = client.post(
            "/api/audit/mark-reviewed",
            json={
                "ids": ["audit-002", "audit-007"],
                "reviewedBy": "user-001",
                "notes": "Batch review of ACGME overrides for Q4"
            }
        )

        assert response.status_code == 204


class TestAuditLogStructure:
    """Tests for audit log entry structure and fields."""

    def test_audit_entry_has_required_fields(self, client: TestClient):
        """Test that audit entries have all required fields."""
        response = client.get("/api/audit/logs")
        data = response.json()

        if data["items"]:
            entry = data["items"][0]

            # Required fields
            assert "id" in entry
            assert "timestamp" in entry
            assert "entityType" in entry
            assert "entityId" in entry
            assert "action" in entry
            assert "severity" in entry
            assert "user" in entry

            # User structure
            assert "id" in entry["user"]
            assert "name" in entry["user"]

    def test_audit_entry_timestamp_format(self, client: TestClient):
        """Test that timestamps are in ISO format."""
        response = client.get("/api/audit/logs")
        data = response.json()

        if data["items"]:
            entry = data["items"][0]
            timestamp = entry["timestamp"]

            # Should be parseable as ISO datetime
            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {timestamp}")

    def test_audit_entry_changes_structure(self, client: TestClient):
        """Test field changes structure when present."""
        response = client.get("/api/audit/logs")
        data = response.json()

        for entry in data["items"]:
            if entry.get("changes"):
                for change in entry["changes"]:
                    assert "field" in change
                    assert "oldValue" in change
                    assert "newValue" in change
                    # displayName is optional
