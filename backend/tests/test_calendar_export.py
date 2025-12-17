"""Tests for calendar export functionality."""
import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.calendar_subscription import CalendarSubscription
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.user import User
from app.services.calendar_service import CalendarService


class TestCalendarService:
    """Test CalendarService class."""

    def test_generate_ics_for_person(self, db: Session) -> None:
        """Test generating ICS file for a person."""
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
            name="PGY-2 Clinic",
            activity_type="clinic",
            abbreviation="C",
            clinic_location="Main Clinic",
        )
        db.add(rotation)

        # Create blocks
        test_date = date(2024, 1, 15)
        block_am = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        block_pm = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="PM",
            block_number=1,
        )
        db.add(block_am)
        db.add(block_pm)

        # Create assignments
        assignment_am = Assignment(
            id=uuid.uuid4(),
            block_id=block_am.id,
            person_id=person.id,
            rotation_template_id=rotation.id,
            role="primary",
            notes="Morning clinic session",
        )
        assignment_pm = Assignment(
            id=uuid.uuid4(),
            block_id=block_pm.id,
            person_id=person.id,
            rotation_template_id=rotation.id,
            role="primary",
            notes="Afternoon clinic session",
        )
        db.add(assignment_am)
        db.add(assignment_pm)
        db.commit()

        # Generate ICS
        ics_content = CalendarService.generate_ics_for_person(
            db=db,
            person_id=person.id,
            start_date=test_date,
            end_date=test_date,
        )

        # Verify ICS content
        assert "BEGIN:VCALENDAR" in ics_content
        assert "VERSION:2.0" in ics_content
        assert "BEGIN:VEVENT" in ics_content
        assert "SUMMARY:PGY-2 Clinic" in ics_content
        assert "LOCATION:Main Clinic" in ics_content
        assert "END:VCALENDAR" in ics_content

        # Should have 2 events (AM and PM)
        assert ics_content.count("BEGIN:VEVENT") == 2

    def test_generate_ics_for_person_with_role_labels(self, db: Session) -> None:
        """Test ICS generation includes role labels."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Bob Jones",
            type="faculty",
            email="bob.jones@example.com",
        )
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="Sports Medicine",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date(2024, 2, 1)
        block = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=2,
        )
        db.add(block)

        # Create supervising assignment
        assignment = Assignment(
            id=uuid.uuid4(),
            block_id=block.id,
            person_id=person.id,
            rotation_template_id=rotation.id,
            role="supervising",
        )
        db.add(assignment)
        db.commit()

        ics_content = CalendarService.generate_ics_for_person(
            db=db,
            person_id=person.id,
            start_date=test_date,
            end_date=test_date,
        )

        # Should include role in summary
        assert "SUMMARY:Sports Medicine (Supervising)" in ics_content

    def test_generate_ics_for_person_not_found(self, db: Session) -> None:
        """Test error when person not found."""
        with pytest.raises(ValueError, match="Person not found"):
            CalendarService.generate_ics_for_person(
                db=db,
                person_id=uuid.uuid4(),
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

    def test_generate_ics_for_rotation(self, db: Session) -> None:
        """Test generating ICS file for a rotation."""
        # Create test data
        person1 = Person(
            id=uuid.uuid4(),
            name="Dr. Alice Brown",
            type="resident",
            pgy_level=1,
        )
        person2 = Person(
            id=uuid.uuid4(),
            name="Dr. Charlie Davis",
            type="resident",
            pgy_level=2,
        )
        db.add(person1)
        db.add(person2)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="FMIT Inpatient",
            activity_type="inpatient",
            abbreviation="FMIT",
        )
        db.add(rotation)

        test_date = date(2024, 3, 1)
        block = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=3,
        )
        db.add(block)

        # Create assignments for both residents
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
        db.add(assignment1)
        db.add(assignment2)
        db.commit()

        # Generate ICS
        ics_content = CalendarService.generate_ics_for_rotation(
            db=db,
            rotation_id=rotation.id,
            start_date=test_date,
            end_date=test_date,
        )

        # Verify ICS content
        assert "BEGIN:VCALENDAR" in ics_content
        assert "Dr. Alice Brown" in ics_content
        assert "Dr. Charlie Davis" in ics_content
        assert "FMIT Inpatient" in ics_content
        assert ics_content.count("BEGIN:VEVENT") == 2

    def test_generate_ics_for_rotation_not_found(self, db: Session) -> None:
        """Test error when rotation has no assignments."""
        with pytest.raises(ValueError, match="No assignments found"):
            CalendarService.generate_ics_for_rotation(
                db=db,
                rotation_id=uuid.uuid4(),
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

    def test_get_block_time_am(self) -> None:
        """Test AM block time calculation."""
        test_date = date(2024, 1, 15)
        block = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )

        start_time, end_time = CalendarService._get_block_time(block)

        assert start_time == datetime(2024, 1, 15, 8, 0)
        assert end_time == datetime(2024, 1, 15, 12, 0)

    def test_get_block_time_pm(self) -> None:
        """Test PM block time calculation."""
        test_date = date(2024, 1, 15)
        block = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="PM",
            block_number=1,
        )

        start_time, end_time = CalendarService._get_block_time(block)

        assert start_time == datetime(2024, 1, 15, 13, 0)
        assert end_time == datetime(2024, 1, 15, 17, 0)

    def test_create_subscription_token(self, db: Session) -> None:
        """Test creating subscription token."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Test User",
            type="resident",
        )
        db.add(person)
        db.commit()

        token, expires_at = CalendarService.create_subscription_token(
            db=db,
            person_id=person.id,
            expires_days=30,
        )

        # Verify token
        assert token is not None
        assert len(token) > 0
        assert expires_at is not None
        assert expires_at > datetime.utcnow()

    def test_create_subscription_token_no_expiry(self, db: Session) -> None:
        """Test creating subscription token without expiry."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Test User",
            type="resident",
        )
        db.add(person)
        db.commit()

        token, expires_at = CalendarService.create_subscription_token(
            db=db,
            person_id=person.id,
            expires_days=None,
        )

        # Verify token
        assert token is not None
        assert expires_at is None

    def test_create_subscription_token_person_not_found(self, db: Session) -> None:
        """Test error when creating token for non-existent person."""
        with pytest.raises(ValueError, match="Person not found"):
            CalendarService.create_subscription_token(
                db=db,
                person_id=uuid.uuid4(),
            )


class TestCalendarAPI:
    """Test calendar API endpoints."""

    def test_export_person_calendar(self, client: TestClient, db: Session) -> None:
        """Test exporting person calendar via API."""
        # Create test data
        person = Person(
            id=uuid.uuid4(),
            name="Dr. API Test",
            type="resident",
        )
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="Test Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date.today()
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

        # Make API request
        response = client.get(
            f"/api/calendar/export/person/{person.id}",
            params={
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

        content = response.text
        assert "BEGIN:VCALENDAR" in content
        assert "Test Rotation" in content

    def test_export_person_calendar_not_found(self, client: TestClient) -> None:
        """Test error when person not found."""
        response = client.get(
            f"/api/calendar/export/person/{uuid.uuid4()}",
            params={
                "start_date": date.today().isoformat(),
                "end_date": date.today().isoformat(),
            },
        )

        assert response.status_code == 404

    def test_export_rotation_calendar(self, client: TestClient, db: Session) -> None:
        """Test exporting rotation calendar via API."""
        # Create test data
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Rotation Test",
            type="resident",
        )
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="Test Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date.today()
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
        )
        db.add(assignment)
        db.commit()

        # Make API request
        response = client.get(
            f"/api/calendar/export/rotation/{rotation.id}",
            params={
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar; charset=utf-8"

        content = response.text
        assert "BEGIN:VCALENDAR" in content
        assert "Dr. Rotation Test" in content

    def test_export_all_calendars(self, client: TestClient, db: Session) -> None:
        """Test exporting all calendars via API."""
        # Create test data
        person1 = Person(
            id=uuid.uuid4(),
            name="Dr. All Test 1",
            type="resident",
        )
        person2 = Person(
            id=uuid.uuid4(),
            name="Dr. All Test 2",
            type="resident",
        )
        db.add(person1)
        db.add(person2)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="All Test Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date.today()
        block = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

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
        db.add(assignment1)
        db.add(assignment2)
        db.commit()

        # Make API request
        response = client.get(
            "/api/calendar/export/ics",
            params={
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar; charset=utf-8"

        content = response.text
        assert "BEGIN:VCALENDAR" in content
        assert "Dr. All Test 1" in content
        assert "Dr. All Test 2" in content
        assert content.count("BEGIN:VEVENT") == 2

    def test_export_all_calendars_filtered_by_person(self, client: TestClient, db: Session) -> None:
        """Test exporting all calendars with person filter."""
        # Create test data
        person1 = Person(
            id=uuid.uuid4(),
            name="Dr. Filter Test 1",
            type="resident",
        )
        person2 = Person(
            id=uuid.uuid4(),
            name="Dr. Filter Test 2",
            type="resident",
        )
        db.add(person1)
        db.add(person2)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="Filter Test Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date.today()
        block = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

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
        db.add(assignment1)
        db.add(assignment2)
        db.commit()

        # Make API request filtering for person1 only
        response = client.get(
            "/api/calendar/export/ics",
            params={
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
                "person_ids": [str(person1.id)],
            },
        )

        # Verify response
        assert response.status_code == 200

        content = response.text
        assert "BEGIN:VCALENDAR" in content
        assert "Dr. Filter Test 1" in content
        assert "Dr. Filter Test 2" not in content
        assert content.count("BEGIN:VEVENT") == 1

    def test_export_person_ics(self, client: TestClient, db: Session) -> None:
        """Test exporting person calendar via /export/ics/{person_id} endpoint."""
        # Create test data
        person = Person(
            id=uuid.uuid4(),
            name="Dr. ICS Test",
            type="resident",
        )
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="ICS Test Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date.today()
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
        )
        db.add(assignment)
        db.commit()

        # Make API request
        response = client.get(
            f"/api/calendar/export/ics/{person.id}",
            params={
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            },
        )

        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

        content = response.text
        assert "BEGIN:VCALENDAR" in content
        assert "ICS Test Rotation" in content

    def test_export_person_ics_not_found(self, client: TestClient) -> None:
        """Test error when person not found in /export/ics/{person_id} endpoint."""
        response = client.get(
            f"/api/calendar/export/ics/{uuid.uuid4()}",
            params={
                "start_date": date.today().isoformat(),
                "end_date": date.today().isoformat(),
            },
        )

        assert response.status_code == 404


class TestVTIMEZONE:
    """Test VTIMEZONE component generation."""

    def test_vtimezone_included_in_person_export(self, db: Session) -> None:
        """Test that VTIMEZONE component is included in person export."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. TZ Test",
            type="resident",
        )
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="TZ Test Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date(2024, 1, 15)
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

        ics_content = CalendarService.generate_ics_for_person(
            db=db,
            person_id=person.id,
            start_date=test_date,
            end_date=test_date,
        )

        # Verify VTIMEZONE component is present
        assert "BEGIN:VTIMEZONE" in ics_content
        assert "TZID:America/New_York" in ics_content
        assert "BEGIN:STANDARD" in ics_content
        assert "BEGIN:DAYLIGHT" in ics_content
        assert "TZNAME:EST" in ics_content
        assert "TZNAME:EDT" in ics_content
        assert "END:VTIMEZONE" in ics_content

    def test_vtimezone_included_in_rotation_export(self, db: Session) -> None:
        """Test that VTIMEZONE component is included in rotation export."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. TZ Rotation Test",
            type="resident",
        )
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="TZ Rotation",
            activity_type="inpatient",
        )
        db.add(rotation)

        test_date = date(2024, 2, 1)
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
        )
        db.add(assignment)
        db.commit()

        ics_content = CalendarService.generate_ics_for_rotation(
            db=db,
            rotation_id=rotation.id,
            start_date=test_date,
            end_date=test_date,
        )

        # Verify VTIMEZONE component is present
        assert "BEGIN:VTIMEZONE" in ics_content
        assert "TZID:America/New_York" in ics_content
        assert "END:VTIMEZONE" in ics_content

    def test_vtimezone_included_in_all_export(self, db: Session) -> None:
        """Test that VTIMEZONE component is included in general export."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. TZ All Test",
            type="resident",
        )
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="TZ All Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date(2024, 3, 1)
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

        ics_content = CalendarService.generate_ics_all(
            db=db,
            start_date=test_date,
            end_date=test_date,
        )

        # Verify VTIMEZONE component is present
        assert "BEGIN:VTIMEZONE" in ics_content
        assert "TZID:America/New_York" in ics_content
        assert "END:VTIMEZONE" in ics_content


class TestGenerateICSAll:
    """Test general ICS export functionality."""

    def test_generate_ics_all_basic(self, db: Session) -> None:
        """Test basic generate_ics_all functionality."""
        # Create test data
        person = Person(
            id=uuid.uuid4(),
            name="Dr. All Basic",
            type="resident",
            pgy_level=1,
        )
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="All Basic Rotation",
            activity_type="clinic",
            clinic_location="Test Clinic",
        )
        db.add(rotation)

        test_date = date(2024, 4, 1)
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
            notes="Test notes",
        )
        db.add(assignment)
        db.commit()

        ics_content = CalendarService.generate_ics_all(
            db=db,
            start_date=test_date,
            end_date=test_date,
        )

        # Verify ICS content
        assert "BEGIN:VCALENDAR" in ics_content
        assert "Dr. All Basic" in ics_content
        assert "All Basic Rotation" in ics_content
        assert "LOCATION:Test Clinic" in ics_content
        assert "Test notes" in ics_content
        assert "PGY Level: 1" in ics_content

    def test_generate_ics_all_with_filters(self, db: Session) -> None:
        """Test generate_ics_all with filters."""
        # Create multiple people and rotations
        person1 = Person(id=uuid.uuid4(), name="Dr. Filter 1", type="resident")
        person2 = Person(id=uuid.uuid4(), name="Dr. Filter 2", type="resident")
        db.add(person1)
        db.add(person2)

        rotation1 = RotationTemplate(
            id=uuid.uuid4(), name="Rotation 1", activity_type="clinic"
        )
        rotation2 = RotationTemplate(
            id=uuid.uuid4(), name="Rotation 2", activity_type="inpatient"
        )
        db.add(rotation1)
        db.add(rotation2)

        test_date = date(2024, 5, 1)
        block = Block(
            id=uuid.uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

        assignment1 = Assignment(
            id=uuid.uuid4(),
            block_id=block.id,
            person_id=person1.id,
            rotation_template_id=rotation1.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid.uuid4(),
            block_id=block.id,
            person_id=person2.id,
            rotation_template_id=rotation2.id,
            role="primary",
        )
        db.add(assignment1)
        db.add(assignment2)
        db.commit()

        # Test person filter
        ics_content = CalendarService.generate_ics_all(
            db=db,
            start_date=test_date,
            end_date=test_date,
            person_ids=[person1.id],
        )
        assert "Dr. Filter 1" in ics_content
        assert "Dr. Filter 2" not in ics_content

        # Test rotation filter
        ics_content = CalendarService.generate_ics_all(
            db=db,
            start_date=test_date,
            end_date=test_date,
            rotation_ids=[rotation2.id],
        )
        assert "Rotation 2" in ics_content
        assert "Rotation 1" not in ics_content

    def test_generate_ics_all_with_role_labels(self, db: Session) -> None:
        """Test generate_ics_all includes role labels."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Role Test",
            type="faculty",
        )
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="Role Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date(2024, 6, 1)
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
            role="supervising",
        )
        db.add(assignment)
        db.commit()

        ics_content = CalendarService.generate_ics_all(
            db=db,
            start_date=test_date,
            end_date=test_date,
        )

        # Should include role in summary
        assert "Dr. Role Test - Role Rotation (Supervising)" in ics_content


class TestCalendarSubscriptionModel:
    """Test CalendarSubscription model."""

    def test_create_subscription(self, db: Session) -> None:
        """Test creating a calendar subscription."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Subscription Test",
            type="resident",
        )
        db.add(person)
        db.commit()

        subscription = CalendarSubscription.create(
            person_id=person.id,
            label="My Work Calendar",
            expires_days=30,
        )
        db.add(subscription)
        db.commit()

        # Verify subscription
        assert subscription.token is not None
        assert len(subscription.token) == 43  # URL-safe base64 of 32 bytes
        assert subscription.person_id == person.id
        assert subscription.label == "My Work Calendar"
        assert subscription.is_active is True
        assert subscription.expires_at is not None
        assert subscription.expires_at > datetime.utcnow()

    def test_create_subscription_no_expiry(self, db: Session) -> None:
        """Test creating subscription without expiration."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. No Expiry",
            type="faculty",
        )
        db.add(person)
        db.commit()

        subscription = CalendarSubscription.create(
            person_id=person.id,
            expires_days=None,
        )
        db.add(subscription)
        db.commit()

        assert subscription.expires_at is None
        assert subscription.is_valid() is True

    def test_subscription_is_valid(self, db: Session) -> None:
        """Test is_valid method."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Valid Test",
            type="resident",
        )
        db.add(person)
        db.commit()

        # Active, not expired
        subscription = CalendarSubscription.create(
            person_id=person.id,
            expires_days=30,
        )
        db.add(subscription)
        db.commit()

        assert subscription.is_valid() is True

        # Revoked
        subscription.revoke()
        assert subscription.is_valid() is False

    def test_subscription_revoke(self, db: Session) -> None:
        """Test revoking a subscription."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Revoke Test",
            type="resident",
        )
        db.add(person)
        db.commit()

        subscription = CalendarSubscription.create(person_id=person.id)
        db.add(subscription)
        db.commit()

        assert subscription.is_active is True
        assert subscription.revoked_at is None

        subscription.revoke()
        db.commit()

        assert subscription.is_active is False
        assert subscription.revoked_at is not None

    def test_subscription_touch(self, db: Session) -> None:
        """Test updating last accessed timestamp."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Touch Test",
            type="resident",
        )
        db.add(person)
        db.commit()

        subscription = CalendarSubscription.create(person_id=person.id)
        db.add(subscription)
        db.commit()

        assert subscription.last_accessed_at is None

        subscription.touch()
        db.commit()

        assert subscription.last_accessed_at is not None

    def test_generate_token_uniqueness(self) -> None:
        """Test that generated tokens are unique."""
        tokens = [CalendarSubscription.generate_token() for _ in range(100)]
        assert len(tokens) == len(set(tokens))  # All unique


class TestCalendarSubscriptionService:
    """Test CalendarService subscription methods."""

    def test_create_subscription(self, db: Session) -> None:
        """Test creating subscription via service."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Service Test",
            type="resident",
        )
        db.add(person)
        db.commit()

        subscription = CalendarService.create_subscription(
            db=db,
            person_id=person.id,
            label="Test Sub",
            expires_days=90,
        )

        assert subscription.token is not None
        assert subscription.person_id == person.id
        assert subscription.label == "Test Sub"
        assert subscription.expires_at is not None

    def test_create_subscription_person_not_found(self, db: Session) -> None:
        """Test error when person not found."""
        with pytest.raises(ValueError, match="Person not found"):
            CalendarService.create_subscription(
                db=db,
                person_id=uuid.uuid4(),
            )

    def test_validate_subscription_token(self, db: Session) -> None:
        """Test validating subscription token."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Validate Test",
            type="resident",
        )
        db.add(person)
        db.commit()

        subscription = CalendarService.create_subscription(
            db=db,
            person_id=person.id,
        )

        # Valid token
        result = CalendarService.validate_subscription_token(db, subscription.token)
        assert result == person.id

        # Invalid token
        result = CalendarService.validate_subscription_token(db, "invalid-token")
        assert result is None

    def test_validate_revoked_token(self, db: Session) -> None:
        """Test that revoked tokens are invalid."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Revoked Validate",
            type="resident",
        )
        db.add(person)
        db.commit()

        subscription = CalendarService.create_subscription(
            db=db,
            person_id=person.id,
        )

        # Valid before revocation
        assert CalendarService.validate_subscription_token(db, subscription.token) == person.id

        # Revoke
        CalendarService.revoke_subscription(db, subscription.token)

        # Invalid after revocation
        assert CalendarService.validate_subscription_token(db, subscription.token) is None

    def test_list_subscriptions(self, db: Session) -> None:
        """Test listing subscriptions."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. List Test",
            type="resident",
        )
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="test",
        )
        db.add(person)
        db.add(user)
        db.commit()

        # Create subscriptions
        sub1 = CalendarService.create_subscription(
            db=db,
            person_id=person.id,
            created_by_user_id=user.id,
            label="Sub 1",
        )
        sub2 = CalendarService.create_subscription(
            db=db,
            person_id=person.id,
            created_by_user_id=user.id,
            label="Sub 2",
        )

        # List all
        subscriptions = CalendarService.list_subscriptions(
            db=db,
            created_by_user_id=user.id,
        )
        assert len(subscriptions) == 2

        # List by person
        subscriptions = CalendarService.list_subscriptions(
            db=db,
            person_id=person.id,
        )
        assert len(subscriptions) == 2

    def test_revoke_subscription(self, db: Session) -> None:
        """Test revoking subscription via service."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Revoke Service",
            type="resident",
        )
        db.add(person)
        db.commit()

        subscription = CalendarService.create_subscription(
            db=db,
            person_id=person.id,
        )

        # Revoke
        result = CalendarService.revoke_subscription(db, subscription.token)
        assert result is True

        # Revoke non-existent
        result = CalendarService.revoke_subscription(db, "non-existent-token")
        assert result is False

    def test_generate_subscription_url(self) -> None:
        """Test generating webcal URL."""
        token = "abc123xyz"

        # Default localhost
        url = CalendarService.generate_subscription_url(token)
        assert url == "webcal://localhost:8000/api/calendar/subscribe/abc123xyz"

        # Custom base URL (https)
        url = CalendarService.generate_subscription_url(
            token,
            base_url="https://myapp.com/api/calendar",
        )
        assert url == "webcal://myapp.com/api/calendar/subscribe/abc123xyz"

        # Custom base URL (http)
        url = CalendarService.generate_subscription_url(
            token,
            base_url="http://staging.example.com/api/calendar",
        )
        assert url == "webcal://staging.example.com/api/calendar/subscribe/abc123xyz"


class TestWebcalSubscriptionAPI:
    """Test webcal subscription API endpoints."""

    def test_create_subscription_endpoint(
        self, client: TestClient, db: Session, auth_headers: dict
    ) -> None:
        """Test POST /calendar/subscribe endpoint."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. API Sub Test",
            type="resident",
        )
        db.add(person)
        db.commit()

        response = client.post(
            "/api/calendar/subscribe",
            json={
                "person_id": str(person.id),
                "label": "My Schedule",
                "expires_days": 30,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "subscription_url" in data
        assert "webcal_url" in data
        assert data["webcal_url"].startswith("webcal://")
        assert data["person_id"] == str(person.id)
        assert data["label"] == "My Schedule"
        assert data["is_active"] is True

    def test_create_subscription_person_not_found(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Test error when person not found."""
        response = client.post(
            "/api/calendar/subscribe",
            json={"person_id": str(uuid.uuid4())},
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_get_subscription_feed(self, client: TestClient, db: Session) -> None:
        """Test GET /calendar/subscribe/{token} endpoint."""
        # Create person with assignment
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Feed Test",
            type="resident",
        )
        db.add(person)

        rotation = RotationTemplate(
            id=uuid.uuid4(),
            name="Feed Rotation",
            activity_type="clinic",
        )
        db.add(rotation)

        test_date = date.today()
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

        # Create subscription directly (bypassing API auth)
        subscription = CalendarSubscription.create(person_id=person.id)
        db.add(subscription)
        db.commit()

        # Get feed (no auth required - token is auth)
        response = client.get(f"/api/calendar/subscribe/{subscription.token}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar; charset=utf-8"
        assert "max-age=900" in response.headers["cache-control"]

        content = response.text
        assert "BEGIN:VCALENDAR" in content
        assert "Feed Rotation" in content

    def test_get_subscription_feed_invalid_token(self, client: TestClient) -> None:
        """Test error with invalid token."""
        response = client.get("/api/calendar/subscribe/invalid-token-here")

        assert response.status_code == 401
        assert "Invalid or expired" in response.json()["detail"]

    def test_get_subscription_feed_revoked(self, client: TestClient, db: Session) -> None:
        """Test error with revoked token."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Revoked Feed",
            type="resident",
        )
        db.add(person)

        subscription = CalendarSubscription.create(person_id=person.id)
        subscription.revoke()
        db.add(subscription)
        db.commit()

        response = client.get(f"/api/calendar/subscribe/{subscription.token}")

        assert response.status_code == 401

    def test_list_subscriptions_endpoint(
        self, client: TestClient, db: Session, auth_headers: dict, current_user: User
    ) -> None:
        """Test GET /calendar/subscriptions endpoint."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. List API Test",
            type="resident",
        )
        db.add(person)
        db.commit()

        # Create subscriptions
        CalendarService.create_subscription(
            db=db,
            person_id=person.id,
            created_by_user_id=current_user.id,
            label="Sub A",
        )
        CalendarService.create_subscription(
            db=db,
            person_id=person.id,
            created_by_user_id=current_user.id,
            label="Sub B",
        )

        response = client.get(
            "/api/calendar/subscriptions",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["subscriptions"]) == 2

    def test_revoke_subscription_endpoint(
        self, client: TestClient, db: Session, auth_headers: dict, current_user: User
    ) -> None:
        """Test DELETE /calendar/subscribe/{token} endpoint."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Delete Test",
            type="resident",
        )
        db.add(person)
        db.commit()

        subscription = CalendarService.create_subscription(
            db=db,
            person_id=person.id,
            created_by_user_id=current_user.id,
        )

        response = client.delete(
            f"/api/calendar/subscribe/{subscription.token}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify revoked
        db.refresh(subscription)
        assert subscription.is_active is False

    def test_revoke_subscription_not_found(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        """Test error when subscription not found."""
        response = client.delete(
            "/api/calendar/subscribe/non-existent-token",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_revoke_subscription_not_owner(
        self, client: TestClient, db: Session, auth_headers: dict
    ) -> None:
        """Test error when not subscription owner."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Not Owner",
            type="resident",
        )
        other_user = User(
            id=uuid.uuid4(),
            email="other@example.com",
            hashed_password="test",
        )
        db.add(person)
        db.add(other_user)
        db.commit()

        # Create subscription by other user
        subscription = CalendarService.create_subscription(
            db=db,
            person_id=person.id,
            created_by_user_id=other_user.id,
        )

        response = client.delete(
            f"/api/calendar/subscribe/{subscription.token}",
            headers=auth_headers,
        )

        assert response.status_code == 403

    def test_legacy_feed_endpoint(self, client: TestClient, db: Session) -> None:
        """Test GET /calendar/feed/{token} legacy endpoint."""
        person = Person(
            id=uuid.uuid4(),
            name="Dr. Legacy Feed",
            type="resident",
        )
        db.add(person)

        subscription = CalendarSubscription.create(person_id=person.id)
        db.add(subscription)
        db.commit()

        # Legacy endpoint should work same as new one
        response = client.get(f"/api/calendar/feed/{subscription.token}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar; charset=utf-8"
