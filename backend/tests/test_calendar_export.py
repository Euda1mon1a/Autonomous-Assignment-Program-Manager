"""Tests for calendar export functionality."""
import uuid
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
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
