"""Calendar service for ICS export and subscription."""
import secrets
from datetime import date, datetime, timedelta
from uuid import UUID

from icalendar import Calendar, Event, Timezone, TimezoneStandard, TimezoneDaylight
from sqlalchemy.orm import Session, joinedload

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.calendar_subscription import CalendarSubscription
from app.models.person import Person


class CalendarService:
    """Service for generating ICS calendar files."""

    @staticmethod
    def _create_timezone() -> Timezone:
        """
        Create a proper VTIMEZONE component for America/New_York.

        Returns:
            Timezone component with standard and daylight time rules
        """
        tz = Timezone()
        tz.add("tzid", "America/New_York")

        # Standard time (EST)
        tz_standard = TimezoneStandard()
        tz_standard.add("dtstart", datetime(1970, 11, 1, 2, 0, 0))
        tz_standard.add("rrule", {"freq": "yearly", "bymonth": 11, "byday": "1su"})
        tz_standard.add("tzoffsetfrom", timedelta(hours=-4))
        tz_standard.add("tzoffsetto", timedelta(hours=-5))
        tz_standard.add("tzname", "EST")

        # Daylight time (EDT)
        tz_daylight = TimezoneDaylight()
        tz_daylight.add("dtstart", datetime(1970, 3, 8, 2, 0, 0))
        tz_daylight.add("rrule", {"freq": "yearly", "bymonth": 3, "byday": "2su"})
        tz_daylight.add("tzoffsetfrom", timedelta(hours=-5))
        tz_daylight.add("tzoffsetto", timedelta(hours=-4))
        tz_daylight.add("tzname", "EDT")

        tz.add_component(tz_standard)
        tz.add_component(tz_daylight)

        return tz

    @staticmethod
    def _get_block_time(block: Block) -> tuple[datetime, datetime]:
        """
        Get start and end datetime for a block.

        AM blocks: 8:00 AM - 12:00 PM
        PM blocks: 1:00 PM - 5:00 PM
        """
        block_date = block.date
        if block.time_of_day == "AM":
            start_time = datetime.combine(block_date, datetime.min.time().replace(hour=8))
            end_time = datetime.combine(block_date, datetime.min.time().replace(hour=12))
        else:  # PM
            start_time = datetime.combine(block_date, datetime.min.time().replace(hour=13))
            end_time = datetime.combine(block_date, datetime.min.time().replace(hour=17))
        return start_time, end_time

    @staticmethod
    def generate_ics_for_person(
        db: Session,
        person_id: UUID,
        start_date: date,
        end_date: date,
        include_types: list[str] | None = None,
    ) -> str:
        """
        Generate ICS calendar file for a person's assignments.

        Args:
            db: Database session
            person_id: Person UUID
            start_date: Start date for export
            end_date: End date for export
            include_types: Optional list of activity types to include

        Returns:
            ICS file content as string
        """
        # Get person
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise ValueError(f"Person not found: {person_id}")

        # Query assignments with blocks and rotation templates
        query = (
            db.query(Assignment)
            .options(
                joinedload(Assignment.block),
                joinedload(Assignment.rotation_template),
                joinedload(Assignment.person),
            )
            .join(Block)
            .filter(
                Assignment.person_id == person_id,
                Block.date >= start_date,
                Block.date <= end_date,
            )
        )

        # Filter by activity types if specified
        if include_types:
            query = query.filter(Assignment.rotation_template.has(activity_type=include_types))

        assignments = query.all()

        # Create calendar
        cal = Calendar()
        cal.add("prodid", "-//Residency Scheduler//Calendar Export//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("method", "PUBLISH")
        cal.add("x-wr-calname", f"{person.name} - Schedule")
        cal.add("x-wr-timezone", "America/New_York")

        # Add proper VTIMEZONE component
        cal.add_component(CalendarService._create_timezone())

        # Add events for each assignment
        for assignment in assignments:
            event = Event()

            # Get activity name
            activity_name = assignment.activity_name
            if assignment.role == "supervising":
                activity_name = f"{activity_name} (Supervising)"
            elif assignment.role == "backup":
                activity_name = f"{activity_name} (Backup)"

            event.add("summary", activity_name)

            # Get block times
            start_time, end_time = CalendarService._get_block_time(assignment.block)
            event.add("dtstart", start_time)
            event.add("dtend", end_time)

            # Add unique identifier
            uid = f"{assignment.id}@residency-scheduler"
            event.add("uid", uid)

            # Add description with details
            description_parts = [
                f"Role: {assignment.role.title()}",
                f"Block: {assignment.block.display_name}",
            ]

            if assignment.rotation_template:
                description_parts.append(f"Type: {assignment.rotation_template.activity_type}")
                if assignment.rotation_template.clinic_location:
                    description_parts.append(f"Location: {assignment.rotation_template.clinic_location}")

            if assignment.notes:
                description_parts.append(f"Notes: {assignment.notes}")

            event.add("description", "\n".join(description_parts))

            # Add location if available
            if assignment.rotation_template and assignment.rotation_template.clinic_location:
                event.add("location", assignment.rotation_template.clinic_location)

            # Add last modified timestamp
            event.add("dtstamp", datetime.utcnow())
            event.add("last-modified", assignment.updated_at)

            cal.add_component(event)

        return cal.to_ical().decode("utf-8")

    @staticmethod
    def generate_ics_for_rotation(
        db: Session,
        rotation_id: UUID,
        start_date: date,
        end_date: date,
    ) -> str:
        """
        Generate ICS calendar file for all assignments in a rotation.

        Args:
            db: Database session
            rotation_id: Rotation template UUID
            start_date: Start date for export
            end_date: End date for export

        Returns:
            ICS file content as string
        """
        # Query assignments for this rotation
        assignments = (
            db.query(Assignment)
            .options(
                joinedload(Assignment.block),
                joinedload(Assignment.rotation_template),
                joinedload(Assignment.person),
            )
            .join(Block)
            .filter(
                Assignment.rotation_template_id == rotation_id,
                Block.date >= start_date,
                Block.date <= end_date,
            )
            .all()
        )

        if not assignments:
            raise ValueError(f"No assignments found for rotation: {rotation_id}")

        # Get rotation template name
        rotation_name = assignments[0].rotation_template.name if assignments[0].rotation_template else "Unknown"

        # Create calendar
        cal = Calendar()
        cal.add("prodid", "-//Residency Scheduler//Calendar Export//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("method", "PUBLISH")
        cal.add("x-wr-calname", f"{rotation_name} - Schedule")
        cal.add("x-wr-timezone", "America/New_York")

        # Add proper VTIMEZONE component
        cal.add_component(CalendarService._create_timezone())

        # Add events for each assignment
        for assignment in assignments:
            event = Event()

            # Summary includes person name and role
            person_name = assignment.person.name if assignment.person else "Unknown"
            summary = f"{person_name} - {assignment.activity_name}"
            if assignment.role != "primary":
                summary += f" ({assignment.role.title()})"

            event.add("summary", summary)

            # Get block times
            start_time, end_time = CalendarService._get_block_time(assignment.block)
            event.add("dtstart", start_time)
            event.add("dtend", end_time)

            # Add unique identifier
            uid = f"{assignment.id}@residency-scheduler"
            event.add("uid", uid)

            # Add description
            description_parts = [
                f"Person: {person_name}",
                f"Role: {assignment.role.title()}",
                f"Block: {assignment.block.display_name}",
            ]

            if assignment.person and assignment.person.is_resident and assignment.person.pgy_level:
                description_parts.append(f"PGY Level: {assignment.person.pgy_level}")

            if assignment.notes:
                description_parts.append(f"Notes: {assignment.notes}")

            event.add("description", "\n".join(description_parts))

            # Add location if available
            if assignment.rotation_template and assignment.rotation_template.clinic_location:
                event.add("location", assignment.rotation_template.clinic_location)

            # Add timestamps
            event.add("dtstamp", datetime.utcnow())
            event.add("last-modified", assignment.updated_at)

            cal.add_component(event)

        return cal.to_ical().decode("utf-8")

    @staticmethod
    def generate_ics_all(
        db: Session,
        start_date: date,
        end_date: date,
        person_ids: list[UUID] | None = None,
        rotation_ids: list[UUID] | None = None,
        include_types: list[str] | None = None,
    ) -> str:
        """
        Generate ICS calendar file for all schedules or filtered schedules.

        Args:
            db: Database session
            start_date: Start date for export
            end_date: End date for export
            person_ids: Optional list of person UUIDs to filter
            rotation_ids: Optional list of rotation UUIDs to filter
            include_types: Optional list of activity types to include

        Returns:
            ICS file content as string
        """
        # Query assignments with blocks, rotation templates, and persons
        query = (
            db.query(Assignment)
            .options(
                joinedload(Assignment.block),
                joinedload(Assignment.rotation_template),
                joinedload(Assignment.person),
            )
            .join(Block)
            .filter(
                Block.date >= start_date,
                Block.date <= end_date,
            )
        )

        # Filter by person IDs if specified
        if person_ids:
            query = query.filter(Assignment.person_id.in_(person_ids))

        # Filter by rotation IDs if specified
        if rotation_ids:
            query = query.filter(Assignment.rotation_template_id.in_(rotation_ids))

        # Filter by activity types if specified
        if include_types:
            query = query.filter(Assignment.rotation_template.has(activity_type=include_types))

        assignments = query.all()

        # Create calendar
        cal = Calendar()
        cal.add("prodid", "-//Residency Scheduler//Calendar Export//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("method", "PUBLISH")
        cal.add("x-wr-calname", "Complete Schedule Export")
        cal.add("x-wr-timezone", "America/New_York")

        # Add proper VTIMEZONE component
        cal.add_component(CalendarService._create_timezone())

        # Add events for each assignment
        for assignment in assignments:
            event = Event()

            # Get person name
            person_name = assignment.person.name if assignment.person else "Unknown"

            # Get activity name with role
            activity_name = assignment.activity_name
            summary = f"{person_name} - {activity_name}"
            if assignment.role == "supervising":
                summary = f"{person_name} - {activity_name} (Supervising)"
            elif assignment.role == "backup":
                summary = f"{person_name} - {activity_name} (Backup)"

            event.add("summary", summary)

            # Get block times
            start_time, end_time = CalendarService._get_block_time(assignment.block)
            event.add("dtstart", start_time)
            event.add("dtend", end_time)

            # Add unique identifier
            uid = f"{assignment.id}@residency-scheduler"
            event.add("uid", uid)

            # Add description with details
            description_parts = [
                f"Person: {person_name}",
                f"Role: {assignment.role.title()}",
                f"Block: {assignment.block.display_name}",
            ]

            if assignment.rotation_template:
                description_parts.append(f"Type: {assignment.rotation_template.activity_type}")
                if assignment.rotation_template.clinic_location:
                    description_parts.append(f"Location: {assignment.rotation_template.clinic_location}")

            if assignment.person and assignment.person.is_resident and assignment.person.pgy_level:
                description_parts.append(f"PGY Level: {assignment.person.pgy_level}")

            if assignment.notes:
                description_parts.append(f"Notes: {assignment.notes}")

            event.add("description", "\n".join(description_parts))

            # Add location if available
            if assignment.rotation_template and assignment.rotation_template.clinic_location:
                event.add("location", assignment.rotation_template.clinic_location)

            # Add last modified timestamp
            event.add("dtstamp", datetime.utcnow())
            event.add("last-modified", assignment.updated_at)

            cal.add_component(event)

        return cal.to_ical().decode("utf-8")

    @staticmethod
    def create_subscription(
        db: Session,
        person_id: UUID,
        created_by_user_id: UUID | None = None,
        label: str | None = None,
        expires_days: int | None = None,
    ) -> CalendarSubscription:
        """
        Create a calendar subscription for webcal feeds.

        Args:
            db: Database session
            person_id: Person UUID
            created_by_user_id: User creating the subscription
            label: Optional label for the subscription
            expires_days: Optional number of days until expiration

        Returns:
            CalendarSubscription instance
        """
        # Verify person exists
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise ValueError(f"Person not found: {person_id}")

        # Create subscription
        subscription = CalendarSubscription.create(
            person_id=person_id,
            created_by_user_id=created_by_user_id,
            label=label,
            expires_days=expires_days,
        )

        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        return subscription

    @staticmethod
    def validate_subscription_token(db: Session, token: str) -> UUID | None:
        """
        Validate a subscription token and return the person_id.

        Args:
            db: Database session
            token: Subscription token

        Returns:
            Person UUID if valid, None otherwise
        """
        subscription = (
            db.query(CalendarSubscription)
            .filter(CalendarSubscription.token == token)
            .first()
        )

        if not subscription or not subscription.is_valid():
            return None

        # Update last accessed timestamp
        subscription.touch()
        db.commit()

        return subscription.person_id

    @staticmethod
    def get_subscription(db: Session, token: str) -> CalendarSubscription | None:
        """
        Get a subscription by token.

        Args:
            db: Database session
            token: Subscription token

        Returns:
            CalendarSubscription or None
        """
        return (
            db.query(CalendarSubscription)
            .filter(CalendarSubscription.token == token)
            .first()
        )

    @staticmethod
    def list_subscriptions(
        db: Session,
        person_id: UUID | None = None,
        created_by_user_id: UUID | None = None,
        active_only: bool = True,
    ) -> list[CalendarSubscription]:
        """
        List calendar subscriptions.

        Args:
            db: Database session
            person_id: Filter by person
            created_by_user_id: Filter by creator
            active_only: Only return active subscriptions

        Returns:
            List of CalendarSubscription
        """
        query = db.query(CalendarSubscription)

        if person_id:
            query = query.filter(CalendarSubscription.person_id == person_id)
        if created_by_user_id:
            query = query.filter(CalendarSubscription.created_by_user_id == created_by_user_id)
        if active_only:
            query = query.filter(CalendarSubscription.is_active == True)

        return query.order_by(CalendarSubscription.created_at.desc()).all()

    @staticmethod
    def revoke_subscription(db: Session, token: str) -> bool:
        """
        Revoke a calendar subscription.

        Args:
            db: Database session
            token: Subscription token

        Returns:
            True if revoked, False if not found
        """
        subscription = (
            db.query(CalendarSubscription)
            .filter(CalendarSubscription.token == token)
            .first()
        )

        if not subscription:
            return False

        subscription.revoke()
        db.commit()

        return True

    @staticmethod
    def generate_subscription_url(token: str, base_url: str | None = None) -> str:
        """
        Generate the webcal subscription URL.

        Args:
            token: Subscription token
            base_url: Base URL for the API (defaults to localhost)

        Returns:
            Full webcal:// URL
        """
        if not base_url:
            base_url = "http://localhost:8000/api/calendar"

        # Convert http:// to webcal:// for calendar app compatibility
        webcal_base = base_url.replace("https://", "webcal://").replace("http://", "webcal://")

        return f"{webcal_base}/subscribe/{token}"

    # Legacy compatibility method
    @staticmethod
    def create_subscription_token(
        db: Session,
        person_id: UUID,
        expires_days: int | None = None,
    ) -> tuple[str, datetime | None]:
        """
        Legacy method for creating subscription tokens.

        Use create_subscription() for full functionality.
        """
        subscription = CalendarService.create_subscription(
            db=db,
            person_id=person_id,
            expires_days=expires_days,
        )
        return subscription.token, subscription.expires_at
