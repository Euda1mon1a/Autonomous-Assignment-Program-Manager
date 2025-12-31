"""Tests for CalendarService."""

from datetime import date, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from icalendar import Calendar
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.calendar_subscription import CalendarSubscription
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.services.calendar_service import CalendarService


class TestCalendarService:
    """Test suite for CalendarService."""

    # ========================================================================
    # Timezone Tests
    # ========================================================================

    def test_create_timezone(self):
        """Test timezone creation for Pacific/Honolulu (HST)."""
        tz = CalendarService._create_timezone()

        assert tz is not None
        assert tz["tzid"] == "Pacific/Honolulu"

        # Verify timezone has standard component
        subcomponents = list(tz.subcomponents)
        assert len(subcomponents) == 1
        standard = subcomponents[0]

        assert standard.name == "STANDARD"
        assert standard["tzname"] == "HST"
        assert standard["tzoffsetfrom"].total_seconds() == -36000  # -10 hours
        assert standard["tzoffsetto"].total_seconds() == -36000  # -10 hours

    # ========================================================================
    # Block Time Tests
    # ========================================================================

    def test_get_block_time_am(self, sample_block: Block):
        """Test getting block time for AM block."""
        sample_block.time_of_day = "AM"
        sample_block.date = date(2025, 1, 15)

        start_time, end_time = CalendarService._get_block_time(sample_block)

        assert start_time == datetime(2025, 1, 15, 8, 0, 0)
        assert end_time == datetime(2025, 1, 15, 12, 0, 0)

    def test_get_block_time_pm(self, sample_block: Block):
        """Test getting block time for PM block."""
        sample_block.time_of_day = "PM"
        sample_block.date = date(2025, 1, 15)

        start_time, end_time = CalendarService._get_block_time(sample_block)

        assert start_time == datetime(2025, 1, 15, 13, 0, 0)
        assert end_time == datetime(2025, 1, 15, 17, 0, 0)

    # ========================================================================
    # Generate ICS for Person Tests
    # ========================================================================

    def test_generate_ics_for_person_success(
        self,
        db: Session,
        sample_resident: Person,
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test successful ICS generation for a person."""
        # Create multiple assignments
        for i in range(3):
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_blocks[i].id,
                person_id=sample_resident.id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        start_date = sample_blocks[0].date
        end_date = sample_blocks[6].date

        ics_content = CalendarService.generate_ics_for_person(
            db=db,
            person_id=sample_resident.id,
            start_date=start_date,
            end_date=end_date,
        )

        # Verify ICS content
        assert ics_content is not None
        assert isinstance(ics_content, str)
        assert "BEGIN:VCALENDAR" in ics_content
        assert "END:VCALENDAR" in ics_content
        assert "Pacific/Honolulu" in ics_content
        assert sample_resident.name in ics_content

        # Parse calendar and verify events
        cal = Calendar.from_ical(ics_content)
        events = [c for c in cal.walk() if c.name == "VEVENT"]
        assert len(events) == 3

    def test_generate_ics_for_person_with_filters(
        self,
        db: Session,
        sample_resident: Person,
        sample_blocks: list[Block],
    ):
        """Test ICS generation with activity type filters."""
        # Create rotation templates with different types
        template1 = RotationTemplate(
            id=uuid4(),
            name="Clinic",
            activity_type="outpatient",
            abbreviation="CL",
        )
        template2 = RotationTemplate(
            id=uuid4(),
            name="Call",
            activity_type="call",
            abbreviation="CA",
        )
        db.add_all([template1, template2])
        db.commit()

        # Create assignments with different types
        assignment1 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=template1.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[1].id,
            person_id=sample_resident.id,
            rotation_template_id=template2.id,
            role="primary",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        # Generate ICS with filter
        ics_content = CalendarService.generate_ics_for_person(
            db=db,
            person_id=sample_resident.id,
            start_date=sample_blocks[0].date,
            end_date=sample_blocks[6].date,
            include_types=["outpatient"],
        )

        # Parse and verify only outpatient events
        cal = Calendar.from_ical(ics_content)
        events = [c for c in cal.walk() if c.name == "VEVENT"]
        assert len(events) == 1
        assert "Clinic" in str(events[0]["summary"])

    def test_generate_ics_for_person_not_found(self, db: Session):
        """Test ICS generation fails for non-existent person."""
        with pytest.raises(ValueError, match="Person not found"):
            CalendarService.generate_ics_for_person(
                db=db,
                person_id=uuid4(),
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
            )

    def test_generate_ics_for_person_with_roles(
        self,
        db: Session,
        sample_resident: Person,
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test ICS generation includes role information."""
        # Create assignments with different roles
        assignment1 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="supervising",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[1].id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="backup",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        ics_content = CalendarService.generate_ics_for_person(
            db=db,
            person_id=sample_resident.id,
            start_date=sample_blocks[0].date,
            end_date=sample_blocks[6].date,
        )

        assert "(Supervising)" in ics_content
        assert "(Backup)" in ics_content

    def test_generate_ics_for_person_with_location(
        self,
        db: Session,
        sample_resident: Person,
        sample_blocks: list[Block],
    ):
        """Test ICS generation includes clinic location."""
        template = RotationTemplate(
            id=uuid4(),
            name="Clinic",
            activity_type="outpatient",
            abbreviation="CL",
            clinic_location="Building A, Room 101",
        )
        db.add(template)
        db.commit()

        assignment = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        ics_content = CalendarService.generate_ics_for_person(
            db=db,
            person_id=sample_resident.id,
            start_date=sample_blocks[0].date,
            end_date=sample_blocks[6].date,
        )

        assert "Building A, Room 101" in ics_content

    # ========================================================================
    # Generate ICS for Rotation Tests
    # ========================================================================

    def test_generate_ics_for_rotation_success(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test successful ICS generation for a rotation."""
        # Create assignments for multiple residents
        for i in range(3):
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_blocks[i].id,
                person_id=sample_residents[i].id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        ics_content = CalendarService.generate_ics_for_rotation(
            db=db,
            rotation_id=sample_rotation_template.id,
            start_date=sample_blocks[0].date,
            end_date=sample_blocks[6].date,
        )

        # Verify ICS content
        assert ics_content is not None
        assert "BEGIN:VCALENDAR" in ics_content
        assert "END:VCALENDAR" in ics_content
        assert sample_rotation_template.name in ics_content

        # Parse and verify events
        cal = Calendar.from_ical(ics_content)
        events = [c for c in cal.walk() if c.name == "VEVENT"]
        assert len(events) == 3

        # Verify each event contains person name
        for i, event in enumerate(events):
            assert sample_residents[i].name in str(event["summary"])

    def test_generate_ics_for_rotation_not_found(self, db: Session):
        """Test ICS generation fails for rotation with no assignments."""
        with pytest.raises(ValueError, match="No assignments found for rotation"):
            CalendarService.generate_ics_for_rotation(
                db=db,
                rotation_id=uuid4(),
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
            )

    def test_generate_ics_for_rotation_includes_pgy_level(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test rotation ICS includes PGY level for residents."""
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_residents[0].id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        ics_content = CalendarService.generate_ics_for_rotation(
            db=db,
            rotation_id=sample_rotation_template.id,
            start_date=sample_blocks[0].date,
            end_date=sample_blocks[6].date,
        )

        # Parse and verify PGY level in description
        cal = Calendar.from_ical(ics_content)
        events = [c for c in cal.walk() if c.name == "VEVENT"]
        assert len(events) == 1
        description = str(events[0]["description"])
        assert "PGY Level:" in description

    # ========================================================================
    # Generate ICS All Tests
    # ========================================================================

    def test_generate_ics_all_success(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test generating ICS for all schedules."""
        # Create assignments for multiple residents
        for i in range(3):
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_blocks[i].id,
                person_id=sample_residents[i].id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        ics_content = CalendarService.generate_ics_all(
            db=db,
            start_date=sample_blocks[0].date,
            end_date=sample_blocks[6].date,
        )

        # Verify ICS content
        assert ics_content is not None
        assert "BEGIN:VCALENDAR" in ics_content
        assert "Complete Schedule Export" in ics_content

        # Parse and verify events
        cal = Calendar.from_ical(ics_content)
        events = [c for c in cal.walk() if c.name == "VEVENT"]
        assert len(events) == 3

    def test_generate_ics_all_filter_by_person_ids(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test filtering ICS by person IDs."""
        # Create assignments for all residents
        for i in range(3):
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_blocks[i].id,
                person_id=sample_residents[i].id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        # Generate ICS for only first two residents
        ics_content = CalendarService.generate_ics_all(
            db=db,
            start_date=sample_blocks[0].date,
            end_date=sample_blocks[6].date,
            person_ids=[sample_residents[0].id, sample_residents[1].id],
        )

        # Parse and verify only 2 events
        cal = Calendar.from_ical(ics_content)
        events = [c for c in cal.walk() if c.name == "VEVENT"]
        assert len(events) == 2

    def test_generate_ics_all_filter_by_rotation_ids(
        self,
        db: Session,
        sample_resident: Person,
        sample_blocks: list[Block],
    ):
        """Test filtering ICS by rotation IDs."""
        # Create two rotation templates
        template1 = RotationTemplate(
            id=uuid4(),
            name="Clinic",
            activity_type="outpatient",
            abbreviation="CL",
        )
        template2 = RotationTemplate(
            id=uuid4(),
            name="Call",
            activity_type="call",
            abbreviation="CA",
        )
        db.add_all([template1, template2])
        db.commit()

        # Create assignments
        assignment1 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=template1.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[1].id,
            person_id=sample_resident.id,
            rotation_template_id=template2.id,
            role="primary",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        # Generate ICS for only first rotation
        ics_content = CalendarService.generate_ics_all(
            db=db,
            start_date=sample_blocks[0].date,
            end_date=sample_blocks[6].date,
            rotation_ids=[template1.id],
        )

        # Parse and verify only 1 event
        cal = Calendar.from_ical(ics_content)
        events = [c for c in cal.walk() if c.name == "VEVENT"]
        assert len(events) == 1
        assert "Clinic" in str(events[0]["summary"])

    def test_generate_ics_all_filter_by_activity_types(
        self,
        db: Session,
        sample_resident: Person,
        sample_blocks: list[Block],
    ):
        """Test filtering ICS by activity types."""
        # Create rotation templates with different types
        template1 = RotationTemplate(
            id=uuid4(),
            name="Clinic",
            activity_type="outpatient",
            abbreviation="CL",
        )
        template2 = RotationTemplate(
            id=uuid4(),
            name="Call",
            activity_type="call",
            abbreviation="CA",
        )
        db.add_all([template1, template2])
        db.commit()

        # Create assignments
        assignment1 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=template1.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[1].id,
            person_id=sample_resident.id,
            rotation_template_id=template2.id,
            role="primary",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        # Generate ICS with activity type filter
        ics_content = CalendarService.generate_ics_all(
            db=db,
            start_date=sample_blocks[0].date,
            end_date=sample_blocks[6].date,
            include_types=["outpatient"],
        )

        # Parse and verify only outpatient event
        cal = Calendar.from_ical(ics_content)
        events = [c for c in cal.walk() if c.name == "VEVENT"]
        assert len(events) == 1

    # ========================================================================
    # Calendar Subscription Tests
    # ========================================================================

    def test_create_subscription_success(
        self,
        db: Session,
        sample_resident: Person,
        admin_user,
    ):
        """Test creating a calendar subscription."""
        subscription = CalendarService.create_subscription(
            db=db,
            person_id=sample_resident.id,
            created_by_user_id=admin_user.id,
            label="My Calendar",
            expires_days=90,
        )

        assert subscription is not None
        assert subscription.token is not None
        assert subscription.person_id == sample_resident.id
        assert subscription.created_by_user_id == admin_user.id
        assert subscription.label == "My Calendar"
        assert subscription.is_active is True
        assert subscription.expires_at is not None

    def test_create_subscription_no_expiration(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test creating a subscription without expiration."""
        subscription = CalendarService.create_subscription(
            db=db,
            person_id=sample_resident.id,
            expires_days=None,
        )

        assert subscription.expires_at is None

    def test_create_subscription_person_not_found(self, db: Session):
        """Test creating subscription for non-existent person fails."""
        with pytest.raises(ValueError, match="Person not found"):
            CalendarService.create_subscription(
                db=db,
                person_id=uuid4(),
            )

    def test_validate_subscription_token_success(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test validating a valid subscription token."""
        subscription = CalendarService.create_subscription(
            db=db,
            person_id=sample_resident.id,
        )

        person_id = CalendarService.validate_subscription_token(
            db=db,
            token=subscription.token,
        )

        assert person_id == sample_resident.id

        # Verify last_accessed_at was updated
        db.refresh(subscription)
        assert subscription.last_accessed_at is not None

    def test_validate_subscription_token_invalid(self, db: Session):
        """Test validating an invalid token returns None."""
        person_id = CalendarService.validate_subscription_token(
            db=db,
            token="invalid-token",
        )

        assert person_id is None

    def test_validate_subscription_token_expired(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test validating an expired token returns None."""
        # Create expired subscription
        subscription = CalendarSubscription.create(
            person_id=sample_resident.id,
            expires_days=1,
        )
        # Manually set expiration to past
        subscription.expires_at = datetime.utcnow() - timedelta(days=1)
        db.add(subscription)
        db.commit()

        person_id = CalendarService.validate_subscription_token(
            db=db,
            token=subscription.token,
        )

        assert person_id is None

    def test_validate_subscription_token_revoked(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test validating a revoked token returns None."""
        subscription = CalendarService.create_subscription(
            db=db,
            person_id=sample_resident.id,
        )
        subscription.revoke()
        db.commit()

        person_id = CalendarService.validate_subscription_token(
            db=db,
            token=subscription.token,
        )

        assert person_id is None

    def test_get_subscription_success(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test getting a subscription by token."""
        subscription = CalendarService.create_subscription(
            db=db,
            person_id=sample_resident.id,
        )

        result = CalendarService.get_subscription(
            db=db,
            token=subscription.token,
        )

        assert result is not None
        assert result.token == subscription.token
        assert result.person_id == sample_resident.id

    def test_get_subscription_not_found(self, db: Session):
        """Test getting a non-existent subscription returns None."""
        result = CalendarService.get_subscription(
            db=db,
            token="invalid-token",
        )

        assert result is None

    def test_list_subscriptions_no_filters(
        self,
        db: Session,
        sample_residents: list[Person],
    ):
        """Test listing all subscriptions without filters."""
        # Create subscriptions for different residents
        for resident in sample_residents:
            CalendarService.create_subscription(
                db=db,
                person_id=resident.id,
            )

        subscriptions = CalendarService.list_subscriptions(db=db, active_only=False)

        assert len(subscriptions) == 3

    def test_list_subscriptions_filter_by_person_id(
        self,
        db: Session,
        sample_residents: list[Person],
    ):
        """Test filtering subscriptions by person ID."""
        # Create subscriptions for different residents
        for resident in sample_residents:
            CalendarService.create_subscription(
                db=db,
                person_id=resident.id,
            )

        subscriptions = CalendarService.list_subscriptions(
            db=db,
            person_id=sample_residents[0].id,
            active_only=False,
        )

        assert len(subscriptions) == 1
        assert subscriptions[0].person_id == sample_residents[0].id

    def test_list_subscriptions_filter_by_creator(
        self,
        db: Session,
        sample_resident: Person,
        admin_user,
    ):
        """Test filtering subscriptions by creator."""
        # Create subscriptions with different creators
        CalendarService.create_subscription(
            db=db,
            person_id=sample_resident.id,
            created_by_user_id=admin_user.id,
        )
        CalendarService.create_subscription(
            db=db,
            person_id=sample_resident.id,
            created_by_user_id=None,
        )

        subscriptions = CalendarService.list_subscriptions(
            db=db,
            created_by_user_id=admin_user.id,
            active_only=False,
        )

        assert len(subscriptions) == 1
        assert subscriptions[0].created_by_user_id == admin_user.id

    def test_list_subscriptions_active_only(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test filtering to only active subscriptions."""
        # Create active subscription
        active_sub = CalendarService.create_subscription(
            db=db,
            person_id=sample_resident.id,
        )

        # Create revoked subscription
        revoked_sub = CalendarService.create_subscription(
            db=db,
            person_id=sample_resident.id,
        )
        revoked_sub.revoke()
        db.commit()

        # Get active only
        subscriptions = CalendarService.list_subscriptions(
            db=db,
            active_only=True,
        )

        assert len(subscriptions) == 1
        assert subscriptions[0].token == active_sub.token

    def test_revoke_subscription_success(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test revoking a subscription."""
        subscription = CalendarService.create_subscription(
            db=db,
            person_id=sample_resident.id,
        )

        result = CalendarService.revoke_subscription(
            db=db,
            token=subscription.token,
        )

        assert result is True

        # Verify subscription is revoked
        db.refresh(subscription)
        assert subscription.is_active is False
        assert subscription.revoked_at is not None

    def test_revoke_subscription_not_found(self, db: Session):
        """Test revoking a non-existent subscription returns False."""
        result = CalendarService.revoke_subscription(
            db=db,
            token="invalid-token",
        )

        assert result is False

    def test_generate_subscription_url_default_base(self):
        """Test generating subscription URL with default base."""
        token = "test-token-123"
        url = CalendarService.generate_subscription_url(token)

        assert url == "webcal://localhost:8000/api/calendar/subscribe/test-token-123"

    def test_generate_subscription_url_custom_https_base(self):
        """Test generating subscription URL with custom HTTPS base."""
        token = "test-token-123"
        base_url = "https://scheduler.hospital.org/api/calendar"
        url = CalendarService.generate_subscription_url(token, base_url)

        assert url == "webcal://scheduler.hospital.org/api/calendar/subscribe/test-token-123"

    def test_generate_subscription_url_custom_http_base(self):
        """Test generating subscription URL with custom HTTP base."""
        token = "test-token-123"
        base_url = "http://192.168.1.100:8000/api/calendar"
        url = CalendarService.generate_subscription_url(token, base_url)

        assert url == "webcal://192.168.1.100:8000/api/calendar/subscribe/test-token-123"

    def test_create_subscription_token_legacy(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test legacy create_subscription_token method."""
        token, expires_at = CalendarService.create_subscription_token(
            db=db,
            person_id=sample_resident.id,
            expires_days=30,
        )

        assert token is not None
        assert expires_at is not None

        # Verify subscription was created
        subscription = CalendarService.get_subscription(db=db, token=token)
        assert subscription is not None
        assert subscription.person_id == sample_resident.id

    # ========================================================================
    # Edge Cases and Error Handling
    # ========================================================================

    def test_generate_ics_for_person_no_assignments(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test generating ICS for person with no assignments."""
        ics_content = CalendarService.generate_ics_for_person(
            db=db,
            person_id=sample_resident.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        # Should return valid calendar with no events
        assert "BEGIN:VCALENDAR" in ics_content
        cal = Calendar.from_ical(ics_content)
        events = [c for c in cal.walk() if c.name == "VEVENT"]
        assert len(events) == 0

    def test_generate_ics_all_no_assignments(self, db: Session):
        """Test generating ICS for all with no assignments."""
        ics_content = CalendarService.generate_ics_all(
            db=db,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        # Should return valid calendar with no events
        assert "BEGIN:VCALENDAR" in ics_content
        cal = Calendar.from_ical(ics_content)
        events = [c for c in cal.walk() if c.name == "VEVENT"]
        assert len(events) == 0

    def test_generate_ics_with_notes(
        self,
        db: Session,
        sample_resident: Person,
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test ICS generation includes assignment notes."""
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
            notes="Bring laptop for presentations",
        )
        db.add(assignment)
        db.commit()

        ics_content = CalendarService.generate_ics_for_person(
            db=db,
            person_id=sample_resident.id,
            start_date=sample_blocks[0].date,
            end_date=sample_blocks[6].date,
        )

        assert "Bring laptop for presentations" in ics_content

    @patch("app.services.calendar_service.datetime")
    def test_ics_includes_proper_timestamps(
        self,
        mock_datetime,
        db: Session,
        sample_resident: Person,
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test ICS events include proper timestamp fields."""
        # Mock datetime.utcnow() for consistent testing
        mock_now = datetime(2025, 1, 15, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        mock_datetime.combine = datetime.combine
        mock_datetime.min = datetime.min

        assignment = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        ics_content = CalendarService.generate_ics_for_person(
            db=db,
            person_id=sample_resident.id,
            start_date=sample_blocks[0].date,
            end_date=sample_blocks[6].date,
        )

        # Parse calendar and verify timestamp fields
        cal = Calendar.from_ical(ics_content)
        events = [c for c in cal.walk() if c.name == "VEVENT"]
        assert len(events) == 1

        event = events[0]
        assert "dtstamp" in event
        assert "last-modified" in event
        assert "uid" in event

        # Verify UID format
        uid = str(event["uid"])
        assert "@residency-scheduler" in uid
