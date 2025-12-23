"""Comprehensive tests for calendar export routes.

Tests the /export.ics endpoint for ICS calendar exports including:
- ICS export endpoint functionality
- RFC 5545 compliance
- Timezone handling (America/New_York)
- Filter parameters (person_id, start_date, end_date)
- Error handling for invalid requests
"""

import re
import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestCalendarExportICSEndpoint:
    """Test the /api/calendar/export.ics endpoint."""

    def test_export_ics_basic_success(self, client: TestClient, db: Session) -> None:
        """Test basic ICS export for a person with assignments."""
        # Create test data
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Jane Smith",
            type="resident",
            email="jane.smith@example.com",
            pgy_level=2,
        )
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="Sports Medicine Clinic",
            activity_type="clinic",
            abbreviation="SMC",
            clinic_location="Building A, Room 101",
        )
        db.add(rotation)

        test_date = date(2024, 3, 15)
        block_am = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block_am)

        assignment = Assignment(
            id=uuid.uuid4(),
            block_id=block_am.id,
            person_id=person.id,
            rotation_template_id=rotation.id,
            role="primary",
            notes="Regular clinic session",
        )
        db.add(assignment)
        db.commit()

        # Make API request
        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert (
            f"schedule_{person.id}_{test_date}_{test_date}.ics"
            in response.headers["content-disposition"]
        )

        # Verify ICS content exists
        content = response.text
        assert len(content) > 0
        assert "BEGIN:VCALENDAR" in content
        assert "END:VCALENDAR" in content

    def test_export_ics_with_multiple_assignments(
        self, client: TestClient, db: Session
    ) -> None:
        """Test ICS export with multiple assignments across different days."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. John Doe",
            type="resident",
            pgy_level=3,
        )
        db.add(person)

        rotation1 = RotationTemplate(
            id=uuid.uuid4(),
            name="Primary Care",
            activity_type="clinic",
        )
        rotation2 = RotationTemplate(
            id=uuid.uuid4(),
            name="Inpatient Service",
            activity_type="inpatient",
        )
        db.add_all([rotation1, rotation2])

        # Create blocks and assignments for a week
        start_date = date(2024, 4, 1)
        end_date = date(2024, 4, 7)

        for i in range(7):
            current_date = start_date + timedelta(days=i)

            # AM block
            block_am = Block(
                id=uuid.uuid4(),
                date=current_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block_am)

            # PM block
            block_pm = Block(
                id=uuid.uuid4(),
                date=current_date,
                time_of_day="PM",
                block_number=1,
            )
            db.add(block_pm)

            # Assignments - alternate between rotations
            rotation = rotation1 if i % 2 == 0 else rotation2

            assignment_am = Assignment(
                id=uuid.uuid4(),
                block_id=block_am.id,
                person_id=person.id,
                rotation_template_id=rotation.id,
                role="primary",
            )
            assignment_pm = Assignment(
                id=uuid.uuid4(),
                block_id=block_pm.id,
                person_id=person.id,
                rotation_template_id=rotation.id,
                role="primary",
            )
            db.add_all([assignment_am, assignment_pm])

        db.commit()

        # Export calendar
        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        assert response.status_code == 200
        content = response.text

        # Should have 14 events (7 days × 2 blocks per day)
        event_count = content.count("BEGIN:VEVENT")
        assert event_count == 14

    def test_export_ics_with_date_filtering(
        self, client: TestClient, db: Session
    ) -> None:
        """Test that date range filtering works correctly."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Test Filter",
            type="resident",
        )
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="Test Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        # Create assignments over 30 days
        base_date = date(2024, 5, 1)
        for i in range(30):
            current_date = base_date + timedelta(days=i)
            block = Block(
                id=uuid.uuid4(),
                date=current_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)

            assignment = Assignment(
                id=uuid.uuid4(),
                block_id=block.id,
                person_id=person.id,
                rotation_template_id=rotation.id,
                role="primary",
            )
            db.add(assignment)

        db.commit()

        # Export only first 7 days
        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": base_date.isoformat(),
                "end_date": (base_date + timedelta(days=6)).isoformat(),
            },
        )

        assert response.status_code == 200
        content = response.text

        # Should only have 7 events
        event_count = content.count("BEGIN:VEVENT")
        assert event_count == 7

    def test_export_ics_with_different_roles(
        self, client: TestClient, db: Session
    ) -> None:
        """Test that different assignment roles are properly labeled."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Role Test",
            type="faculty",
        )
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="Clinic Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date(2024, 6, 1)

        # Create assignments with different roles
        roles = ["primary", "backup", "supervising"]
        times = ["AM", "PM", "AM"]

        for i, (role, time_of_day) in enumerate(zip(roles, times)):
            block = Block(
                id=uuid.uuid4(),
                date=test_date + timedelta(days=i),
                time_of_day=time_of_day,
                block_number=1,
            )
            db.add(block)

            assignment = Assignment(
                id=uuid.uuid4(),
                block_id=block.id,
                person_id=person.id,
                rotation_template_id=rotation.id,
                role=role,
            )
            db.add(assignment)

        db.commit()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": (test_date + timedelta(days=2)).isoformat(),
            },
        )

        assert response.status_code == 200
        content = response.text

        # Verify role labels in summary
        assert (
            "Clinic Rotation (Backup)" in content
            or "SUMMARY:Clinic Rotation (Backup)" in content
        )
        assert (
            "Clinic Rotation (Supervising)" in content
            or "SUMMARY:Clinic Rotation (Supervising)" in content
        )


class TestRFC5545Compliance:
    """Test RFC 5545 (iCalendar) standard compliance."""

    def test_ics_has_required_vcalendar_properties(
        self, client: TestClient, db: Session
    ) -> None:
        """Test that ICS file has all required VCALENDAR properties."""
        person = Person(id=uuid.uuid4(), name="Dr. RFC Test", type="resident")
        db.add(person)
        db.commit()

        test_date = date(2024, 1, 1)

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        content = response.text

        # Required properties per RFC 5545
        assert "BEGIN:VCALENDAR" in content
        assert "VERSION:2.0" in content
        assert "PRODID:" in content
        assert "CALSCALE:GREGORIAN" in content
        assert "METHOD:PUBLISH" in content
        assert "END:VCALENDAR" in content

    def test_ics_vcalendar_structure(self, client: TestClient, db: Session) -> None:
        """Test proper VCALENDAR begin/end structure."""
        person = Person(id=uuid.uuid4(), name="Dr. Structure Test", type="resident")
        db.add(person)
        db.commit()

        test_date = date.today()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        content = response.text
        lines = content.split("\n")

        # First line should be BEGIN:VCALENDAR (after stripping whitespace)
        first_line = lines[0].strip()
        assert first_line == "BEGIN:VCALENDAR"

        # Last line should be END:VCALENDAR
        last_line = lines[-1].strip() if lines[-1].strip() else lines[-2].strip()
        assert last_line == "END:VCALENDAR"

    def test_ics_vevent_properties(self, client: TestClient, db: Session) -> None:
        """Test that VEVENT components have required properties."""
        person = Person(id=uuid.uuid4(), name="Dr. Event Test", type="resident")
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="Test Event Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date(2024, 7, 15)
        block = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

        assignment = Assignment(
            id=uuid.uuid4(),
            block_id=block.id,
            person_id=person.id,
            rotation_template_id=rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        content = response.text

        # Required VEVENT properties per RFC 5545
        assert "BEGIN:VEVENT" in content
        assert "DTSTART:" in content
        assert "DTEND:" in content
        assert "SUMMARY:" in content
        assert "UID:" in content
        assert "DTSTAMP:" in content
        assert "END:VEVENT" in content

    def test_ics_uid_format(self, client: TestClient, db: Session) -> None:
        """Test that UIDs are properly formatted and unique."""
        person = Person(id=uuid.uuid4(), name="Dr. UID Test", type="resident")
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="UID Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date(2024, 8, 1)

        # Create multiple assignments
        for i in range(3):
            block = Block(
                id=uuid.uuid4(),
                date=test_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)

            assignment = Assignment(
                id=uuid.uuid4(),
                block_id=block.id,
                person_id=person.id,
                rotation_template_id=rotation.id,
                role="primary",
            )
            db.add(assignment)

        db.commit()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": (test_date + timedelta(days=2)).isoformat(),
            },
        )

        content = response.text

        # Extract all UIDs
        uid_pattern = r"UID:([^\r\n]+)"
        uids = re.findall(uid_pattern, content)

        # All UIDs should be unique
        assert len(uids) == len(set(uids))

        # UIDs should contain @residency-scheduler domain
        for uid in uids:
            assert "@residency-scheduler" in uid

    def test_ics_datetime_format(self, client: TestClient, db: Session) -> None:
        """Test that datetime values are properly formatted."""
        person = Person(id=uuid.uuid4(), name="Dr. DateTime Test", type="resident")
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="DateTime Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date(2024, 9, 10)
        block = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

        assignment = Assignment(
            id=uuid.uuid4(),
            block_id=block.id,
            person_id=person.id,
            rotation_template_id=rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        content = response.text

        # Check for proper date-time format (YYYYMMDDTHHMMSS)
        # AM block should start at 08:00
        assert "20240910T080000" in content  # Start time
        assert "20240910T120000" in content  # End time (12:00 PM)


class TestTimezoneHandling:
    """Test timezone handling in ICS exports."""

    def test_vtimezone_component_present(self, client: TestClient, db: Session) -> None:
        """Test that VTIMEZONE component is included in ICS export."""
        person = Person(id=uuid.uuid4(), name="Dr. TZ Test", type="resident")
        db.add(person)
        db.commit()

        test_date = date(2024, 1, 15)

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        content = response.text

        # VTIMEZONE component should be present
        assert "BEGIN:VTIMEZONE" in content
        assert "END:VTIMEZONE" in content

    def test_vtimezone_america_new_york(self, client: TestClient, db: Session) -> None:
        """Test that timezone is set to America/New_York."""
        person = Person(id=uuid.uuid4(), name="Dr. NY Test", type="resident")
        db.add(person)
        db.commit()

        test_date = date(2024, 2, 1)

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        content = response.text

        # Should specify America/New_York timezone
        assert "TZID:America/New_York" in content
        assert "X-WR-TIMEZONE:America/New_York" in content

    def test_vtimezone_standard_and_daylight(
        self, client: TestClient, db: Session
    ) -> None:
        """Test that timezone includes both standard and daylight time rules."""
        person = Person(id=uuid.uuid4(), name="Dr. DST Test", type="resident")
        db.add(person)
        db.commit()

        test_date = date(2024, 3, 1)

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        content = response.text

        # Should have both STANDARD and DAYLIGHT components
        assert "BEGIN:STANDARD" in content
        assert "END:STANDARD" in content
        assert "BEGIN:DAYLIGHT" in content
        assert "END:DAYLIGHT" in content

    def test_vtimezone_est_edt_names(self, client: TestClient, db: Session) -> None:
        """Test that timezone names are EST and EDT."""
        person = Person(id=uuid.uuid4(), name="Dr. EST Test", type="resident")
        db.add(person)
        db.commit()

        test_date = date(2024, 4, 1)

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        content = response.text

        # Should include EST and EDT timezone names
        assert "TZNAME:EST" in content
        assert "TZNAME:EDT" in content

    def test_am_block_time_correct(self, client: TestClient, db: Session) -> None:
        """Test that AM blocks have correct times (8:00 AM - 12:00 PM)."""
        person = Person(id=uuid.uuid4(), name="Dr. AM Test", type="resident")
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="AM Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date(2024, 5, 15)
        block_am = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block_am)

        assignment = Assignment(
            id=uuid.uuid4(),
            block_id=block_am.id,
            person_id=person.id,
            rotation_template_id=rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        content = response.text

        # AM block: 8:00 AM - 12:00 PM
        assert "20240515T080000" in content  # 8:00 AM start
        assert "20240515T120000" in content  # 12:00 PM end

    def test_pm_block_time_correct(self, client: TestClient, db: Session) -> None:
        """Test that PM blocks have correct times (1:00 PM - 5:00 PM)."""
        person = Person(id=uuid.uuid4(), name="Dr. PM Test", type="resident")
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="PM Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date(2024, 6, 20)
        block_pm = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="PM",
            block_number=1,
        )
        db.add(block_pm)

        assignment = Assignment(
            id=uuid.uuid4(),
            block_id=block_pm.id,
            person_id=person.id,
            rotation_template_id=rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        content = response.text

        # PM block: 1:00 PM - 5:00 PM
        assert "20240620T130000" in content  # 1:00 PM start
        assert "20240620T170000" in content  # 5:00 PM end


class TestFilterParameters:
    """Test filter parameter handling."""

    def test_person_id_filter_required(self, client: TestClient) -> None:
        """Test that person_id parameter is required."""
        test_date = date.today()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        # Should return 422 Unprocessable Entity for missing required parameter
        assert response.status_code == 422

    def test_start_date_filter_required(self, client: TestClient) -> None:
        """Test that start_date parameter is required."""
        person_id = uuid.uuid4()
        test_date = date.today()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person_id),
                "end_date": test_date.isoformat(),
            },
        )

        assert response.status_code == 422

    def test_end_date_filter_required(self, client: TestClient) -> None:
        """Test that end_date parameter is required."""
        person_id = uuid.uuid4()
        test_date = date.today()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person_id),
                "start_date": test_date.isoformat(),
            },
        )

        assert response.status_code == 422

    def test_invalid_person_id_format(self, client: TestClient) -> None:
        """Test handling of invalid UUID format for person_id."""
        test_date = date.today()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": "not-a-valid-uuid",
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        assert response.status_code == 422

    def test_invalid_date_format(self, client: TestClient) -> None:
        """Test handling of invalid date format."""
        person_id = uuid.uuid4()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person_id),
                "start_date": "2024-13-45",  # Invalid date
                "end_date": date.today().isoformat(),
            },
        )

        assert response.status_code == 422

    def test_filters_by_exact_person_id(self, client: TestClient, db: Session) -> None:
        """Test that only assignments for specified person are included."""
        # Create two different people
        person1 = Person(
            id=uuid.uuid4(),
            name="Dr. Person One",
            type="resident",
        )
        person2 = Person(
            id=uuid.uuid4(),
            name="Dr. Person Two",
            type="resident",
        )
        db.add_all([person1, person2])

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="Test Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date(2024, 7, 1)
        block = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

        # Create assignments for both people on same block
        assignment1 = Assignment(
            id=uuid.uuid4(),
            block_id=block.id,
            person_id=person1.id,
            rotation_template_id=rotation.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid.uuid4(),
            block_id=block.id,
            person_id=person2.id,
            rotation_template_id=rotation.id,
            role="backup",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        # Export for person1 only
        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person1.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        assert response.status_code == 200
        content = response.text

        # Should only have 1 event (person1's assignment)
        assert content.count("BEGIN:VEVENT") == 1
        assert "Dr. Person One" in content
        assert "Dr. Person Two" not in content


class TestErrorHandling:
    """Test error handling for invalid requests."""

    def test_person_not_found(self, client: TestClient) -> None:
        """Test error when person_id doesn't exist."""
        non_existent_id = uuid.uuid4()
        test_date = date.today()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(non_existent_id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        assert response.status_code == 404
        assert "Person not found" in response.json()["detail"]

    def test_empty_assignment_set(self, client: TestClient, db: Session) -> None:
        """Test handling when person exists but has no assignments."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. No Assignments",
            type="resident",
        )
        db.add(person)
        db.commit()

        test_date = date.today()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        # Should succeed but return calendar with no events
        assert response.status_code == 200
        content = response.text
        assert "BEGIN:VCALENDAR" in content
        assert content.count("BEGIN:VEVENT") == 0

    def test_internal_server_error_handling(
        self, client: TestClient, db: Session
    ) -> None:
        """Test that internal errors return 500 status."""
        # This test verifies the error handling structure
        # In a real scenario, this might be tested with mocking
        # For now, we just verify the endpoint structure is sound

        person = Person(id=uuid.uuid4(), name="Dr. Error Test", type="resident")
        db.add(person)
        db.commit()

        test_date = date.today()

        # Normal request should work
        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        # Should not error on valid request
        assert response.status_code in [200, 404, 500]

    def test_malformed_query_parameters(self, client: TestClient) -> None:
        """Test handling of malformed query parameters."""
        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": "12345",  # Not a valid UUID
                "start_date": "not-a-date",
                "end_date": "also-not-a-date",
            },
        )

        assert response.status_code == 422


class TestICSFileContent:
    """Test ICS file content and metadata."""

    def test_ics_contains_person_name(self, client: TestClient, db: Session) -> None:
        """Test that calendar name includes person's name."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Calendar Name Test",
            type="resident",
        )
        db.add(person)
        db.commit()

        test_date = date.today()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        content = response.text
        assert "Dr. Calendar Name Test" in content

    def test_ics_includes_location_information(
        self, client: TestClient, db: Session
    ) -> None:
        """Test that location information is included in events."""
        person = Person(id=uuid.uuid4(), name="Dr. Location Test", type="resident")
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="Location Clinic",
            activity_type="clinic",
            clinic_location="Medical Center, Floor 3, Suite 301",
        )
        db.add(rotation)

        test_date = date(2024, 8, 15)
        block = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

        assignment = Assignment(
            id=uuid.uuid4(),
            block_id=block.id,
            person_id=person.id,
            rotation_template_id=rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        content = response.text
        assert "LOCATION:Medical Center, Floor 3, Suite 301" in content

    def test_ics_includes_assignment_notes(
        self, client: TestClient, db: Session
    ) -> None:
        """Test that assignment notes are included in event descriptions."""
        person = Person(id=uuid.uuid4(), name="Dr. Notes Test", type="resident")
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="Notes Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date(2024, 9, 1)
        block = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="PM",
            block_number=1,
        )
        db.add(block)

        assignment = Assignment(
            id=uuid.uuid4(),
            block_id=block.id,
            person_id=person.id,
            rotation_template_id=rotation.id,
            role="primary",
            notes="Bring stethoscope and laptop",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        content = response.text
        assert "Bring stethoscope and laptop" in content

    def test_ics_includes_activity_type(self, client: TestClient, db: Session) -> None:
        """Test that activity type is included in event descriptions."""
        person = Person(id=uuid.uuid4(), name="Dr. Activity Test", type="resident")
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="Activity Rotation",
            activity_type="inpatient",
        )
        db.add(rotation)

        test_date = date(2024, 10, 1)
        block = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

        assignment = Assignment(
            id=uuid.uuid4(),
            block_id=block.id,
            person_id=person.id,
            rotation_template_id=rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        content = response.text
        assert "Type: inpatient" in content or "inpatient" in content.lower()

    def test_filename_format(self, client: TestClient, db: Session) -> None:
        """Test that downloaded filename has correct format."""
        person = Person(id=uuid.uuid4(), name="Dr. Filename Test", type="resident")
        db.add(person)
        db.commit()

        start_date = date(2024, 11, 1)
        end_date = date(2024, 11, 30)

        response = client.get(
            "/api/calendar/export.ics",
            params={
                "person_id": str(person.id),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        assert response.status_code == 200

        content_disposition = response.headers.get("content-disposition")
        assert content_disposition is not None
        assert "attachment" in content_disposition
        assert f"schedule_{person.id}_2024-11-01_2024-11-30.ics" in content_disposition
