"""Calendar service for ICS export and subscription."""
import secrets
from datetime import date, datetime, timedelta
from uuid import UUID

from icalendar import Calendar, Event
from sqlalchemy.orm import Session, joinedload

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person


class CalendarService:
    """Service for generating ICS calendar files."""

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
    def create_subscription_token(
        db: Session,
        person_id: UUID,
        expires_days: int | None = None,
    ) -> tuple[str, datetime | None]:
        """
        Create a subscription token for calendar feeds.

        Args:
            db: Database session
            person_id: Person UUID
            expires_days: Optional number of days until expiration

        Returns:
            Tuple of (token, expires_at)
        """
        # Verify person exists
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise ValueError(f"Person not found: {person_id}")

        # Generate secure token
        token = secrets.token_urlsafe(32)

        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)

        # In a real implementation, we would store this in a database table
        # For now, we encode person_id in the token (in production, use a proper token store)
        # This is a simplified implementation for demonstration

        return token, expires_at

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
        # In a real implementation, this would query a database table
        # For now, this is a placeholder that would need proper token storage
        # This is simplified for demonstration purposes
        return None
