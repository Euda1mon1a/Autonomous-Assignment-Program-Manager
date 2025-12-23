"""
Schedule-specific validation functions.

Validates scheduling data including:
- Assignment role validation
- Block session validation
- Rotation template validation
- Schedule conflict pre-validation
- ACGME rule pre-validation
"""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.validators.common import ValidationError, validate_string_length, validate_uuid
from app.validators.date_validators import validate_block_date, validate_date_range

# Valid assignment roles
VALID_ASSIGNMENT_ROLES = ["primary", "supervising", "backup"]

# Valid block sessions
VALID_SESSIONS = ["AM", "PM"]

# ACGME constants
MAX_HOURS_PER_WEEK = 80
MAX_CONSECUTIVE_HOURS = 24
MAX_HOURS_AFTER_24 = 4  # 24+4 rule
DAYS_PER_WEEK = 7
MIN_TIME_OFF_HOURS = 24


def validate_assignment_role(role: str) -> str:
    """
    Validate assignment role.

    Valid roles: primary, supervising, backup

    Args:
        role: Role to validate

    Returns:
        str: Validated role (lowercase)

    Raises:
        ValidationError: If role is invalid
    """
    if not role:
        raise ValidationError("Assignment role cannot be empty")

    role_lower = role.lower().strip()

    if role_lower not in VALID_ASSIGNMENT_ROLES:
        raise ValidationError(
            f"Assignment role must be one of {VALID_ASSIGNMENT_ROLES}, got '{role}'"
        )

    return role_lower


def validate_block_session(session: str) -> str:
    """
    Validate block session is AM or PM.

    Args:
        session: Session to validate

    Returns:
        str: Validated session (uppercase)

    Raises:
        ValidationError: If session is invalid
    """
    if not session:
        raise ValidationError("Block session cannot be empty")

    session_upper = session.upper().strip()

    if session_upper not in VALID_SESSIONS:
        raise ValidationError(
            f"Block session must be one of {VALID_SESSIONS}, got '{session}'"
        )

    return session_upper


def validate_rotation_name(name: str) -> str:
    """
    Validate rotation template name.

    Args:
        name: Rotation name to validate

    Returns:
        str: Validated rotation name

    Raises:
        ValidationError: If name is invalid
    """
    if not name:
        raise ValidationError("Rotation name cannot be empty")

    return validate_string_length(
        name.strip(), min_length=1, max_length=255, field_name="Rotation name"
    )


def validate_rotation_abbreviation(abbrev: str | None) -> str | None:
    """
    Validate rotation abbreviation.

    Abbreviations should be 2-10 characters, uppercase.

    Args:
        abbrev: Abbreviation to validate

    Returns:
        str | None: Validated abbreviation (uppercase) or None

    Raises:
        ValidationError: If abbreviation is invalid
    """
    if abbrev is None or abbrev.strip() == "":
        return None

    validated = validate_string_length(
        abbrev.strip(), min_length=2, max_length=10, field_name="Rotation abbreviation"
    )

    # Convert to uppercase
    return validated.upper()


def validate_activity_override(activity: str | None) -> str | None:
    """
    Validate activity override text.

    Args:
        activity: Activity override to validate

    Returns:
        str | None: Validated activity or None

    Raises:
        ValidationError: If activity is invalid
    """
    if activity is None or activity.strip() == "":
        return None

    return validate_string_length(
        activity.strip(), min_length=1, max_length=255, field_name="Activity override"
    )


def validate_notes(notes: str | None, max_length: int = 1000) -> str | None:
    """
    Validate notes/comments field.

    Args:
        notes: Notes to validate
        max_length: Maximum length (default: 1000)

    Returns:
        str | None: Validated notes or None

    Raises:
        ValidationError: If notes are too long
    """
    if notes is None or notes.strip() == "":
        return None

    return validate_string_length(
        notes.strip(), min_length=1, max_length=max_length, field_name="Notes"
    )


async def validate_no_duplicate_assignment(
    db: AsyncSession,
    person_id: UUID,
    block_id: UUID,
    exclude_assignment_id: UUID | None = None,
) -> None:
    """
    Validate that person is not already assigned to this block.

    Prevents double-booking: one person cannot be in two places at the same time.

    Args:
        db: Database session
        person_id: Person ID
        block_id: Block ID
        exclude_assignment_id: Assignment ID to exclude (for updates)

    Raises:
        ValidationError: If person already has assignment for this block
    """
    # Validate UUIDs
    validate_uuid(person_id)
    validate_uuid(block_id)

    # Build query
    query = select(Assignment).where(
        Assignment.person_id == person_id, Assignment.block_id == block_id
    )

    # Exclude specific assignment (for updates)
    if exclude_assignment_id is not None:
        validate_uuid(exclude_assignment_id)
        query = query.where(Assignment.id != exclude_assignment_id)

    # Check for existing assignment
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        raise ValidationError(
            "Person is already assigned to this block. "
            "Cannot create duplicate assignment."
        )


async def validate_block_exists(db: AsyncSession, block_id: UUID) -> Block:
    """
    Validate that block exists in database.

    Args:
        db: Database session
        block_id: Block ID to validate

    Returns:
        Block: The validated block

    Raises:
        ValidationError: If block does not exist
    """
    validate_uuid(block_id)

    result = await db.execute(select(Block).where(Block.id == block_id))
    block = result.scalar_one_or_none()

    if block is None:
        raise ValidationError(f"Block not found: {block_id}")

    return block


async def validate_person_exists(db: AsyncSession, person_id: UUID) -> Person:
    """
    Validate that person exists in database.

    Args:
        db: Database session
        person_id: Person ID to validate

    Returns:
        Person: The validated person

    Raises:
        ValidationError: If person does not exist
    """
    validate_uuid(person_id)

    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    if person is None:
        raise ValidationError(f"Person not found: {person_id}")

    return person


async def validate_supervision_ratio(
    db: AsyncSession, block_id: UUID, new_resident_id: UUID | None = None
) -> None:
    """
    Pre-validate ACGME supervision ratios for a block.

    ACGME ratios:
    - PGY-1: 1 faculty per 2 residents
    - PGY-2/3: 1 faculty per 4 residents

    Args:
        db: Database session
        block_id: Block ID to check
        new_resident_id: Optional resident being added (for pre-validation)

    Raises:
        ValidationError: If supervision ratio would be violated
    """
    # Get block
    block = await validate_block_exists(db, block_id)

    # Get all assignments for this block
    result = await db.execute(
        select(Assignment).join(Person).where(Assignment.block_id == block_id)
    )
    assignments = result.scalars().all()

    # Count residents and faculty
    pgy1_count = 0
    pgy23_count = 0
    faculty_count = 0

    for assignment in assignments:
        if assignment.person.type == "resident":
            if assignment.person.pgy_level == 1:
                pgy1_count += 1
            else:
                pgy23_count += 1
        elif assignment.person.type == "faculty":
            if assignment.role == "supervising":
                faculty_count += 1

    # If adding new resident, increment counts
    if new_resident_id:
        new_resident = await validate_person_exists(db, new_resident_id)
        if new_resident.type == "resident":
            if new_resident.pgy_level == 1:
                pgy1_count += 1
            else:
                pgy23_count += 1

    # Check ratios
    # PGY-1: need 1 faculty per 2 residents
    required_faculty_pgy1 = (pgy1_count + 1) // 2  # Ceiling division

    # PGY-2/3: need 1 faculty per 4 residents
    required_faculty_pgy23 = (pgy23_count + 3) // 4  # Ceiling division

    total_required_faculty = max(required_faculty_pgy1, required_faculty_pgy23)

    if faculty_count < total_required_faculty:
        raise ValidationError(
            f"Insufficient supervising faculty for block. "
            f"Required: {total_required_faculty}, Available: {faculty_count}. "
            f"(PGY-1: {pgy1_count}, PGY-2/3: {pgy23_count})"
        )


async def validate_weekly_hours_limit(
    db: AsyncSession, person_id: UUID, check_date: date, additional_hours: float = 12.0
) -> None:
    """
    Pre-validate ACGME 80-hour weekly limit.

    Checks rolling 7-day average for a person.

    Args:
        db: Database session
        person_id: Person ID to check
        check_date: Date to check around
        additional_hours: Additional hours being added (default: 12 for half-day)

    Raises:
        ValidationError: If adding hours would violate 80-hour limit
    """
    # Get person
    person = await validate_person_exists(db, person_id)

    # Only check for residents
    if person.type != "resident":
        return

    # Check 7 days before and after
    start_date = check_date - timedelta(days=7)
    end_date = check_date + timedelta(days=7)

    # Get all assignments in this period
    result = await db.execute(
        select(Assignment)
        .join(Block)
        .where(
            Assignment.person_id == person_id,
            Block.date >= start_date,
            Block.date <= end_date,
        )
    )
    assignments = result.scalars().all()

    # Calculate hours per week (rough estimate: 12 hours per block)
    # In production, this would use actual shift hours from rotation templates
    hours_per_block = 12.0
    total_hours = len(assignments) * hours_per_block + additional_hours

    # Check rolling 7-day periods
    weeks_checked = 0
    for i in range(8):  # Check 8 possible 7-day windows
        week_start = start_date + timedelta(days=i)
        week_end = week_start + timedelta(days=6)

        # Count blocks in this week
        week_blocks = sum(
            1 for a in assignments if week_start <= a.block.date <= week_end
        )

        week_hours = week_blocks * hours_per_block
        if week_start <= check_date <= week_end:
            week_hours += additional_hours

        if week_hours > MAX_HOURS_PER_WEEK:
            raise ValidationError(
                f"Adding this assignment would violate ACGME 80-hour weekly limit. "
                f"Week of {week_start}: {week_hours:.1f} hours (max: {MAX_HOURS_PER_WEEK})"
            )

        weeks_checked += 1


async def validate_one_in_seven_rule(
    db: AsyncSession, person_id: UUID, check_date: date
) -> None:
    """
    Pre-validate ACGME 1-in-7 rule (one 24-hour period off every 7 days).

    Args:
        db: Database session
        person_id: Person ID to check
        check_date: Date to check around

    Raises:
        ValidationError: If adding assignment would violate 1-in-7 rule
    """
    # Get person
    person = await validate_person_exists(db, person_id)

    # Only check for residents
    if person.type != "resident":
        return

    # Check 7 days before
    start_date = check_date - timedelta(days=6)
    end_date = check_date

    # Get all dates with assignments in this period
    result = await db.execute(
        select(Block.date)
        .join(Assignment)
        .where(
            Assignment.person_id == person_id,
            Block.date >= start_date,
            Block.date <= end_date,
        )
        .distinct()
    )
    assigned_dates = {row[0] for row in result.all()}

    # Add the new date
    assigned_dates.add(check_date)

    # Check if person has all 7 days assigned
    if len(assigned_dates) >= 7:
        # Check if these are 7 consecutive days
        sorted_dates = sorted(assigned_dates)
        for i in range(len(sorted_dates) - 6):
            consecutive = sorted_dates[i : i + 7]
            if (consecutive[-1] - consecutive[0]).days == 6:
                raise ValidationError(
                    f"Adding this assignment would violate ACGME 1-in-7 rule. "
                    f"Person would have assignments for 7 consecutive days "
                    f"({consecutive[0]} to {consecutive[-1]})"
                )


def validate_confidence_score(confidence: float | None) -> float | None:
    """
    Validate confidence score is between 0 and 1.

    Args:
        confidence: Confidence score to validate

    Returns:
        float | None: Validated confidence score

    Raises:
        ValidationError: If confidence is out of range
    """
    if confidence is None:
        return None

    if not isinstance(confidence, (int, float)):
        raise ValidationError(
            f"Confidence score must be a number, got {type(confidence).__name__}"
        )

    if confidence < 0.0 or confidence > 1.0:
        raise ValidationError(
            f"Confidence score must be between 0 and 1, got {confidence}"
        )

    return float(confidence)


def validate_assignment_score(score: float | None) -> float | None:
    """
    Validate assignment quality score.

    Scores are typically 0-100 but can be negative for penalties.

    Args:
        score: Score to validate

    Returns:
        float | None: Validated score

    Raises:
        ValidationError: If score is unreasonable
    """
    if score is None:
        return None

    if not isinstance(score, (int, float)):
        raise ValidationError(
            f"Assignment score must be a number, got {type(score).__name__}"
        )

    # Allow negative scores (penalties) but check for unreasonable values
    if score < -1000 or score > 1000:
        raise ValidationError(
            f"Assignment score seems unreasonable: {score}. "
            f"Expected range: -1000 to 1000"
        )

    return float(score)
