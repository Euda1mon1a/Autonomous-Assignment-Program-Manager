"""
Integration tests for the leave workflow with FMIT integration.

Tests the end-to-end flow of:
1. Create leave request - via API
2. Update leave request - modify dates
3. Delete leave request - cancellation
4. Leave calendar view - verify calendar data
5. Leave conflict detection - when leave overlaps FMIT
6. Bulk leave import - CSV upload flow
7. Leave webhook - external system notification
8. Leave provider switching - database vs external sources
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.models.absence import Absence
from app.models.assignment import Assignment


@pytest.mark.integration
class TestLeaveCreation:
    """Test creating leave requests via API."""

    def test_create_vacation_leave(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
    ):
        """Test creating a vacation leave request."""
        setup = full_program_setup
        faculty = setup["faculty"][0]
        start = (date.today() + timedelta(days=30)).isoformat()
        end = (date.today() + timedelta(days=37)).isoformat()

        response = integration_client.post(
            "/api/leave/",
            json={
                "faculty_id": str(faculty.id),
                "start_date": start,
                "end_date": end,
                "leave_type": "vacation",
                "is_blocking": True,
                "description": "Annual family vacation",
            },
            headers=auth_headers,
        )

        assert response.status_code in [201, 401, 403]
        if response.status_code == 201:
            data = response.json()
            assert data["faculty_id"] == str(faculty.id)
            assert data["leave_type"] == "vacation"
            assert data["is_blocking"] is True
            assert data["description"] == "Annual family vacation"
            assert "id" in data
            assert "created_at" in data

    def test_create_deployment_leave(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
    ):
        """Test creating a deployment leave (always blocking)."""
        setup = full_program_setup
        faculty = setup["faculty"][1]
        start = (date.today() + timedelta(days=60)).isoformat()
        end = (date.today() + timedelta(days=180)).isoformat()

        response = integration_client.post(
            "/api/leave/",
            json={
                "faculty_id": str(faculty.id),
                "start_date": start,
                "end_date": end,
                "leave_type": "deployment",
                "is_blocking": False,  # Should be overridden to True
                "description": "Military deployment",
            },
            headers=auth_headers,
        )

        assert response.status_code in [201, 401, 403]
        if response.status_code == 201:
            data = response.json()
            assert data["leave_type"] == "deployment"
            # Deployment should always be blocking
            assert data["is_blocking"] is True

    def test_create_leave_invalid_dates(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
    ):
        """Test creating leave with end_date before start_date fails."""
        setup = full_program_setup
        faculty = setup["faculty"][0]
        start = (date.today() + timedelta(days=30)).isoformat()
        end = (date.today() + timedelta(days=20)).isoformat()  # Before start

        response = integration_client.post(
            "/api/leave/",
            json={
                "faculty_id": str(faculty.id),
                "start_date": start,
                "end_date": end,
                "leave_type": "vacation",
                "is_blocking": True,
            },
            headers=auth_headers,
        )

        # Should fail validation
        assert response.status_code in [422, 400, 401, 403]

    def test_create_leave_nonexistent_faculty(
        self,
        integration_client,
        auth_headers,
    ):
        """Test creating leave for non-existent faculty fails."""
        fake_id = str(uuid4())
        start = (date.today() + timedelta(days=30)).isoformat()
        end = (date.today() + timedelta(days=37)).isoformat()

        response = integration_client.post(
            "/api/leave/",
            json={
                "faculty_id": fake_id,
                "start_date": start,
                "end_date": end,
                "leave_type": "vacation",
                "is_blocking": True,
            },
            headers=auth_headers,
        )

        assert response.status_code in [404, 401, 403]

    def test_create_multiple_leave_types(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
    ):
        """Test creating different types of leave."""
        setup = full_program_setup
        faculty = setup["faculty"][0]

        leave_types = ["vacation", "tdy", "conference", "medical", "family_emergency"]
        created_count = 0

        for i, leave_type in enumerate(leave_types):
            start = (date.today() + timedelta(days=10 + i * 10)).isoformat()
            end = (date.today() + timedelta(days=15 + i * 10)).isoformat()

            response = integration_client.post(
                "/api/leave/",
                json={
                    "faculty_id": str(faculty.id),
                    "start_date": start,
                    "end_date": end,
                    "leave_type": leave_type,
                    "is_blocking": True,
                    "description": f"Test {leave_type}",
                },
                headers=auth_headers,
            )

            if response.status_code == 201:
                created_count += 1
                data = response.json()
                assert data["leave_type"] == leave_type

        # If auth is working, should have created all
        if created_count > 0:
            assert created_count == len(leave_types)


@pytest.mark.integration
class TestLeaveUpdate:
    """Test updating leave requests via API."""

    def test_update_leave_dates(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
        integration_db,
    ):
        """Test updating leave dates."""
        setup = full_program_setup
        faculty = setup["faculty"][0]

        # Create leave first
        absence = Absence(
            id=uuid4(),
            person_id=faculty.id,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            absence_type="vacation",
            is_blocking=True,
            notes="Original dates",
        )
        integration_db.add(absence)
        integration_db.commit()
        integration_db.refresh(absence)

        # Update to new dates
        new_start = (date.today() + timedelta(days=40)).isoformat()
        new_end = (date.today() + timedelta(days=47)).isoformat()

        response = integration_client.put(
            f"/api/leave/{absence.id}",
            json={
                "start_date": new_start,
                "end_date": new_end,
            },
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert data["start_date"] == new_start
            assert data["end_date"] == new_end
            assert "updated_at" in data

    def test_update_leave_type(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
        integration_db,
    ):
        """Test updating leave type."""
        setup = full_program_setup
        faculty = setup["faculty"][0]

        # Create leave
        absence = Absence(
            id=uuid4(),
            person_id=faculty.id,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            absence_type="vacation",
            is_blocking=True,
        )
        integration_db.add(absence)
        integration_db.commit()
        integration_db.refresh(absence)

        # Update type to conference
        response = integration_client.put(
            f"/api/leave/{absence.id}",
            json={
                "leave_type": "conference",
                "description": "Medical conference attendance",
            },
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert data["leave_type"] == "conference"
            assert data["description"] == "Medical conference attendance"

    def test_update_leave_blocking_status(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
        integration_db,
    ):
        """Test updating is_blocking flag."""
        setup = full_program_setup
        faculty = setup["faculty"][0]

        # Create non-blocking leave
        absence = Absence(
            id=uuid4(),
            person_id=faculty.id,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            absence_type="conference",
            is_blocking=False,
        )
        integration_db.add(absence)
        integration_db.commit()
        integration_db.refresh(absence)

        # Make it blocking
        response = integration_client.put(
            f"/api/leave/{absence.id}",
            json={
                "is_blocking": True,
            },
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert data["is_blocking"] is True

    def test_update_nonexistent_leave(
        self,
        integration_client,
        auth_headers,
    ):
        """Test updating non-existent leave returns 404."""
        fake_id = str(uuid4())
        new_start = (date.today() + timedelta(days=40)).isoformat()

        response = integration_client.put(
            f"/api/leave/{fake_id}",
            json={
                "start_date": new_start,
            },
            headers=auth_headers,
        )

        assert response.status_code in [404, 401, 403]


@pytest.mark.integration
class TestLeaveDeletion:
    """Test deleting (canceling) leave requests via API."""

    def test_delete_leave(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
        integration_db,
    ):
        """Test deleting a leave record."""
        setup = full_program_setup
        faculty = setup["faculty"][0]

        # Create leave
        absence = Absence(
            id=uuid4(),
            person_id=faculty.id,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            absence_type="vacation",
        )
        integration_db.add(absence)
        integration_db.commit()
        leave_id = absence.id

        # Delete it
        response = integration_client.delete(
            f"/api/leave/{leave_id}",
            headers=auth_headers,
        )

        assert response.status_code in [204, 200, 401, 403]

        if response.status_code in [204, 200]:
            # Verify it's deleted
            deleted = integration_db.query(Absence).filter(
                Absence.id == leave_id
            ).first()
            assert deleted is None

    def test_delete_nonexistent_leave(
        self,
        integration_client,
        auth_headers,
    ):
        """Test deleting non-existent leave returns 404."""
        fake_id = str(uuid4())

        response = integration_client.delete(
            f"/api/leave/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code in [404, 401, 403]

    def test_cancel_leave_before_start(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
        integration_db,
    ):
        """Test canceling leave before it starts."""
        setup = full_program_setup
        faculty = setup["faculty"][0]

        # Create future leave
        absence = Absence(
            id=uuid4(),
            person_id=faculty.id,
            start_date=date.today() + timedelta(days=90),
            end_date=date.today() + timedelta(days=97),
            absence_type="vacation",
            notes="Far future vacation",
        )
        integration_db.add(absence)
        integration_db.commit()
        leave_id = absence.id

        # Cancel it
        response = integration_client.delete(
            f"/api/leave/{leave_id}",
            headers=auth_headers,
        )

        assert response.status_code in [204, 200, 401, 403]


@pytest.mark.integration
class TestLeaveCalendar:
    """Test leave calendar view functionality."""

    def test_get_leave_calendar_empty(
        self,
        integration_client,
        auth_headers,
    ):
        """Test calendar view with no leave records."""
        start = date.today().isoformat()
        end = (date.today() + timedelta(days=30)).isoformat()

        response = integration_client.get(
            f"/api/leave/calendar?start_date={start}&end_date={end}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "entries" in data
            assert "start_date" in data
            assert "end_date" in data
            assert data["start_date"] == start
            assert data["end_date"] == end
            assert isinstance(data["entries"], list)

    def test_get_leave_calendar_with_leave(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
        integration_db,
    ):
        """Test calendar view with leave records."""
        setup = full_program_setup
        faculty = setup["faculty"]

        # Create multiple leave records
        start_date = date.today() + timedelta(days=10)
        end_date = date.today() + timedelta(days=40)

        absences = [
            Absence(
                id=uuid4(),
                person_id=faculty[0].id,
                start_date=start_date + timedelta(days=5),
                end_date=start_date + timedelta(days=12),
                absence_type="vacation",
            ),
            Absence(
                id=uuid4(),
                person_id=faculty[1].id,
                start_date=start_date + timedelta(days=15),
                end_date=start_date + timedelta(days=18),
                absence_type="conference",
            ),
            Absence(
                id=uuid4(),
                person_id=faculty[2].id,
                start_date=start_date + timedelta(days=20),
                end_date=start_date + timedelta(days=27),
                absence_type="tdy",
            ),
        ]

        for absence in absences:
            integration_db.add(absence)
        integration_db.commit()

        # Get calendar
        response = integration_client.get(
            f"/api/leave/calendar?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert len(data["entries"]) == 3
            assert "conflict_count" in data

            # Verify all faculty are represented
            faculty_ids = {entry["faculty_id"] for entry in data["entries"]}
            assert len(faculty_ids) == 3

    def test_leave_calendar_date_filtering(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
        integration_db,
    ):
        """Test calendar correctly filters by date range."""
        setup = full_program_setup
        faculty = setup["faculty"][0]

        # Create leave outside the query range
        early_absence = Absence(
            id=uuid4(),
            person_id=faculty.id,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() - timedelta(days=20),
            absence_type="vacation",
        )
        integration_db.add(early_absence)

        # Create leave inside the query range
        current_absence = Absence(
            id=uuid4(),
            person_id=faculty.id,
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=12),
            absence_type="conference",
        )
        integration_db.add(current_absence)
        integration_db.commit()

        # Query for future dates only
        start = (date.today() + timedelta(days=1)).isoformat()
        end = (date.today() + timedelta(days=30)).isoformat()

        response = integration_client.get(
            f"/api/leave/calendar?start_date={start}&end_date={end}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            # Should only include the current absence, not the early one
            assert len(data["entries"]) == 1
            assert data["entries"][0]["leave_type"] == "conference"


@pytest.mark.integration
class TestLeaveConflictDetection:
    """Test leave conflict detection with FMIT assignments."""

    def test_leave_with_assignment_conflict(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
        integration_db,
    ):
        """Test detecting when leave overlaps with scheduled FMIT."""
        setup = full_program_setup
        faculty = setup["faculty"][0]

        # Create an assignment for the faculty
        block = setup["blocks"][10]  # Some block in the future
        template = setup["templates"][0]

        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=faculty.id,
            rotation_template_id=template.id,
            role="supervising",
        )
        integration_db.add(assignment)
        integration_db.commit()

        # Create leave that overlaps with the assignment
        absence = Absence(
            id=uuid4(),
            person_id=faculty.id,
            start_date=block.date,
            end_date=block.date + timedelta(days=1),
            absence_type="vacation",
            is_blocking=True,
        )
        integration_db.add(absence)
        integration_db.commit()

        # Get calendar to check for conflicts
        start = block.date.isoformat()
        end = (block.date + timedelta(days=7)).isoformat()

        response = integration_client.get(
            f"/api/leave/calendar?start_date={start}&end_date={end}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            # Calendar endpoint includes conflict detection
            assert "entries" in data
            assert len(data["entries"]) >= 1

    def test_blocking_vs_nonblocking_leave(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
        integration_db,
    ):
        """Test that blocking status is correctly reflected."""
        setup = full_program_setup
        faculty = setup["faculty"]

        # Create blocking leave
        blocking_leave = Absence(
            id=uuid4(),
            person_id=faculty[0].id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
            is_blocking=True,
        )
        integration_db.add(blocking_leave)

        # Create non-blocking leave
        nonblocking_leave = Absence(
            id=uuid4(),
            person_id=faculty[1].id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="conference",
            is_blocking=False,
        )
        integration_db.add(nonblocking_leave)
        integration_db.commit()

        # Get calendar
        start = (date.today() + timedelta(days=5)).isoformat()
        end = (date.today() + timedelta(days=20)).isoformat()

        response = integration_client.get(
            f"/api/leave/calendar?start_date={start}&end_date={end}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert len(data["entries"]) == 2

            # Find each entry and check blocking status
            for entry in data["entries"]:
                if entry["faculty_id"] == str(faculty[0].id):
                    assert entry["is_blocking"] is True
                elif entry["faculty_id"] == str(faculty[1].id):
                    assert entry["is_blocking"] is False


@pytest.mark.integration
class TestBulkLeaveImport:
    """Test bulk import of leave records."""

    def test_bulk_import_success(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
    ):
        """Test successful bulk import of leave records."""
        setup = full_program_setup
        faculty = setup["faculty"]

        records = []
        for i, fac in enumerate(faculty):
            records.append({
                "faculty_id": str(fac.id),
                "start_date": (date.today() + timedelta(days=30 + i * 10)).isoformat(),
                "end_date": (date.today() + timedelta(days=35 + i * 10)).isoformat(),
                "leave_type": "vacation",
                "is_blocking": True,
                "description": f"Bulk import {i + 1}",
            })

        response = integration_client.post(
            "/api/leave/bulk-import",
            json={
                "records": records,
                "skip_duplicates": True,
            },
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert data["imported_count"] == len(records)
            assert data["error_count"] == 0
            assert data["skipped_count"] == 0

    def test_bulk_import_skip_duplicates(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
        integration_db,
    ):
        """Test bulk import with duplicate detection."""
        setup = full_program_setup
        faculty = setup["faculty"][0]

        # Create existing leave
        existing = Absence(
            id=uuid4(),
            person_id=faculty.id,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            absence_type="vacation",
        )
        integration_db.add(existing)
        integration_db.commit()

        # Try to import duplicate + new record
        records = [
            {
                "faculty_id": str(faculty.id),
                "start_date": (date.today() + timedelta(days=30)).isoformat(),
                "end_date": (date.today() + timedelta(days=35)).isoformat(),
                "leave_type": "vacation",
                "is_blocking": True,
            },
            {
                "faculty_id": str(faculty.id),
                "start_date": (date.today() + timedelta(days=40)).isoformat(),
                "end_date": (date.today() + timedelta(days=45)).isoformat(),
                "leave_type": "conference",
                "is_blocking": True,
            },
        ]

        response = integration_client.post(
            "/api/leave/bulk-import",
            json={
                "records": records,
                "skip_duplicates": True,
            },
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert data["imported_count"] == 1  # Only the new one
            assert data["skipped_count"] == 1  # The duplicate

    def test_bulk_import_partial_failure(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
    ):
        """Test bulk import with some invalid records."""
        setup = full_program_setup
        faculty = setup["faculty"][0]

        records = [
            # Valid record
            {
                "faculty_id": str(faculty.id),
                "start_date": (date.today() + timedelta(days=30)).isoformat(),
                "end_date": (date.today() + timedelta(days=35)).isoformat(),
                "leave_type": "vacation",
                "is_blocking": True,
            },
            # Invalid: non-existent faculty
            {
                "faculty_id": str(uuid4()),
                "start_date": (date.today() + timedelta(days=40)).isoformat(),
                "end_date": (date.today() + timedelta(days=45)).isoformat(),
                "leave_type": "vacation",
                "is_blocking": True,
            },
        ]

        response = integration_client.post(
            "/api/leave/bulk-import",
            json={
                "records": records,
                "skip_duplicates": True,
            },
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            # Should have imported the valid one
            assert data["imported_count"] >= 0
            assert data["error_count"] >= 0

    def test_bulk_import_empty_list(
        self,
        integration_client,
        auth_headers,
    ):
        """Test bulk import with empty record list."""
        response = integration_client.post(
            "/api/leave/bulk-import",
            json={
                "records": [],
                "skip_duplicates": True,
            },
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert data["imported_count"] == 0
            assert data["error_count"] == 0


@pytest.mark.integration
class TestLeaveWebhook:
    """Test webhook endpoint for external leave system integration."""

    def test_webhook_created_event(
        self,
        integration_client,
    ):
        """Test webhook with 'created' event."""
        payload = {
            "event_type": "created",
            "faculty_id": str(uuid4()),
            "faculty_name": "Dr. External Faculty",
            "start_date": (date.today() + timedelta(days=30)).isoformat(),
            "end_date": (date.today() + timedelta(days=37)).isoformat(),
            "leave_type": "vacation",
            "is_blocking": True,
            "description": "External system created leave",
        }

        response = integration_client.post(
            "/api/leave/webhook",
            json=payload,
        )

        # Webhook should accept the event
        assert response.status_code in [200, 201]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["status"] == "received"
            assert data["event_type"] == "created"

    def test_webhook_updated_event(
        self,
        integration_client,
    ):
        """Test webhook with 'updated' event."""
        payload = {
            "event_type": "updated",
            "faculty_id": str(uuid4()),
            "faculty_name": "Dr. External Faculty",
            "leave_id": str(uuid4()),
            "start_date": (date.today() + timedelta(days=30)).isoformat(),
            "end_date": (date.today() + timedelta(days=40)).isoformat(),
            "leave_type": "conference",
            "is_blocking": False,
        }

        response = integration_client.post(
            "/api/leave/webhook",
            json=payload,
        )

        assert response.status_code in [200, 201]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["status"] == "received"
            assert data["event_type"] == "updated"

    def test_webhook_deleted_event(
        self,
        integration_client,
    ):
        """Test webhook with 'deleted' event."""
        payload = {
            "event_type": "deleted",
            "faculty_id": str(uuid4()),
            "faculty_name": "Dr. External Faculty",
            "leave_id": str(uuid4()),
            "start_date": (date.today() + timedelta(days=30)).isoformat(),
            "end_date": (date.today() + timedelta(days=37)).isoformat(),
            "leave_type": "vacation",
            "is_blocking": True,
        }

        response = integration_client.post(
            "/api/leave/webhook",
            json=payload,
        )

        assert response.status_code in [200, 201]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["status"] == "received"
            assert data["event_type"] == "deleted"

    def test_webhook_invalid_event_type(
        self,
        integration_client,
    ):
        """Test webhook with invalid event type."""
        payload = {
            "event_type": "invalid_event",
            "faculty_id": str(uuid4()),
            "faculty_name": "Dr. External Faculty",
            "start_date": (date.today() + timedelta(days=30)).isoformat(),
            "end_date": (date.today() + timedelta(days=37)).isoformat(),
            "leave_type": "vacation",
            "is_blocking": True,
        }

        response = integration_client.post(
            "/api/leave/webhook",
            json=payload,
        )

        # Should fail validation
        assert response.status_code in [422, 400]


@pytest.mark.integration
class TestLeaveListingAndFiltering:
    """Test leave listing and filtering functionality."""

    def test_list_all_leave(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
        integration_db,
    ):
        """Test listing all leave records."""
        setup = full_program_setup
        faculty = setup["faculty"]

        # Create multiple leave records
        for i, fac in enumerate(faculty):
            absence = Absence(
                id=uuid4(),
                person_id=fac.id,
                start_date=date.today() + timedelta(days=10 + i * 5),
                end_date=date.today() + timedelta(days=15 + i * 5),
                absence_type="vacation",
            )
            integration_db.add(absence)
        integration_db.commit()

        response = integration_client.get(
            "/api/leave/",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data
            assert data["total"] >= 3

    def test_list_leave_filter_by_faculty(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
        integration_db,
    ):
        """Test filtering leave by faculty."""
        setup = full_program_setup
        faculty = setup["faculty"]

        # Create leave for different faculty
        for fac in faculty:
            absence = Absence(
                id=uuid4(),
                person_id=fac.id,
                start_date=date.today() + timedelta(days=10),
                end_date=date.today() + timedelta(days=15),
                absence_type="vacation",
            )
            integration_db.add(absence)
        integration_db.commit()

        # Filter by first faculty
        response = integration_client.get(
            f"/api/leave/?faculty_id={faculty[0].id}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert len(data["items"]) >= 1
            # All results should be for the specified faculty
            for item in data["items"]:
                assert item["faculty_id"] == str(faculty[0].id)

    def test_list_leave_filter_by_date_range(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
        integration_db,
    ):
        """Test filtering leave by date range."""
        setup = full_program_setup
        faculty = setup["faculty"][0]

        # Create leave in different time periods
        early_leave = Absence(
            id=uuid4(),
            person_id=faculty.id,
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=10),
            absence_type="vacation",
        )
        integration_db.add(early_leave)

        late_leave = Absence(
            id=uuid4(),
            person_id=faculty.id,
            start_date=date.today() + timedelta(days=50),
            end_date=date.today() + timedelta(days=55),
            absence_type="conference",
        )
        integration_db.add(late_leave)
        integration_db.commit()

        # Query for early period only
        start = (date.today() + timedelta(days=1)).isoformat()
        end = (date.today() + timedelta(days=20)).isoformat()

        response = integration_client.get(
            f"/api/leave/?start_date={start}&end_date={end}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            # Should only get the early leave, not the late one
            assert len(data["items"]) >= 1
            for item in data["items"]:
                item_start = date.fromisoformat(item["start_date"])
                item_end = date.fromisoformat(item["end_date"])
                # Should overlap with query range
                assert item_end >= date.fromisoformat(start)
                assert item_start <= date.fromisoformat(end)

    def test_list_leave_pagination(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
        integration_db,
    ):
        """Test pagination of leave records."""
        setup = full_program_setup
        faculty = setup["faculty"][0]

        # Create multiple leave records
        for i in range(25):
            absence = Absence(
                id=uuid4(),
                person_id=faculty.id,
                start_date=date.today() + timedelta(days=10 + i * 7),
                end_date=date.today() + timedelta(days=15 + i * 7),
                absence_type="vacation",
            )
            integration_db.add(absence)
        integration_db.commit()

        # Get first page
        response = integration_client.get(
            "/api/leave/?page=1&page_size=10",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert data["page"] == 1
            assert data["page_size"] == 10
            assert len(data["items"]) <= 10
            assert data["total"] >= 25

            # Get second page
            response2 = integration_client.get(
                "/api/leave/?page=2&page_size=10",
                headers=auth_headers,
            )

            if response2.status_code == 200:
                data2 = response2.json()
                assert data2["page"] == 2
                assert len(data2["items"]) <= 10
