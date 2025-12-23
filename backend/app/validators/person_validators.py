"""
Person-specific validation functions.

Validates person data including:
- Person type (resident vs faculty)
- PGY level validation
- Faculty role validation
- Specialty validation
- Supervision ratio validation
"""
from typing import Optional

from app.validators.common import (
    ValidationError,
    validate_email_address,
    validate_integer_range,
    validate_name,
    validate_phone_number,
    validate_string_length,
)


# Valid person types
VALID_PERSON_TYPES = ["resident", "faculty"]

# Valid faculty roles
VALID_FACULTY_ROLES = ["pd", "apd", "oic", "dept_chief", "sports_med", "core"]

# Valid PGY levels
MIN_PGY_LEVEL = 1
MAX_PGY_LEVEL = 3

# Common medical specialties
COMMON_SPECIALTIES = [
    "Family Medicine",
    "Sports Medicine",
    "Dermatology",
    "Pediatrics",
    "Internal Medicine",
    "Emergency Medicine",
    "Obstetrics and Gynecology",
    "Surgery",
    "Psychiatry",
    "Radiology",
    "Anesthesiology",
    "Pathology",
    "Preventive Medicine",
    "Physical Medicine and Rehabilitation",
]


def validate_person_type(person_type: str) -> str:
    """
    Validate person type is 'resident' or 'faculty'.

    Args:
        person_type: Person type to validate

    Returns:
        str: Validated person type (lowercase)

    Raises:
        ValidationError: If person type is invalid
    """
    if not person_type:
        raise ValidationError("Person type cannot be empty")

    person_type_lower = person_type.lower().strip()

    if person_type_lower not in VALID_PERSON_TYPES:
        raise ValidationError(
            f"Person type must be one of {VALID_PERSON_TYPES}, got '{person_type}'"
        )

    return person_type_lower


def validate_pgy_level(pgy_level: int | None, person_type: str) -> int | None:
    """
    Validate PGY level for residents.

    PGY (Post-Graduate Year) must be:
    - Between 1 and 3 for residents
    - None for faculty

    Args:
        pgy_level: PGY level to validate
        person_type: Type of person ('resident' or 'faculty')

    Returns:
        int | None: Validated PGY level

    Raises:
        ValidationError: If PGY level is invalid for person type
    """
    person_type_lower = person_type.lower()

    # Faculty should not have PGY level
    if person_type_lower == "faculty":
        if pgy_level is not None:
            raise ValidationError("Faculty cannot have a PGY level")
        return None

    # Residents must have PGY level
    if person_type_lower == "resident":
        if pgy_level is None:
            raise ValidationError("Residents must have a PGY level")

        return validate_integer_range(
            pgy_level,
            min_value=MIN_PGY_LEVEL,
            max_value=MAX_PGY_LEVEL,
            field_name="PGY level"
        )

    return pgy_level


def validate_faculty_role(faculty_role: str | None, person_type: str) -> str | None:
    """
    Validate faculty role.

    Valid roles: pd, apd, oic, dept_chief, sports_med, core

    Args:
        faculty_role: Faculty role to validate
        person_type: Type of person ('resident' or 'faculty')

    Returns:
        str | None: Validated faculty role (lowercase)

    Raises:
        ValidationError: If faculty role is invalid
    """
    person_type_lower = person_type.lower()

    # Residents should not have faculty role
    if person_type_lower == "resident":
        if faculty_role is not None:
            raise ValidationError("Residents cannot have a faculty role")
        return None

    # Faculty role is optional for faculty
    if faculty_role is None:
        return None

    role_lower = faculty_role.lower().strip()

    if role_lower not in VALID_FACULTY_ROLES:
        raise ValidationError(
            f"Faculty role must be one of {VALID_FACULTY_ROLES}, got '{faculty_role}'"
        )

    return role_lower


def validate_specialties(specialties: list[str] | None) -> list[str] | None:
    """
    Validate specialty list.

    Checks:
    - Each specialty is a non-empty string
    - No duplicates
    - Reasonable length

    Args:
        specialties: List of specialties to validate

    Returns:
        list[str] | None: Validated specialties (trimmed, no duplicates)

    Raises:
        ValidationError: If specialties are invalid
    """
    if specialties is None:
        return None

    if not isinstance(specialties, list):
        raise ValidationError(
            f"Specialties must be a list, got {type(specialties).__name__}"
        )

    if len(specialties) == 0:
        return None

    validated = []
    seen = set()

    for i, specialty in enumerate(specialties):
        if not isinstance(specialty, str):
            raise ValidationError(
                f"Specialty at index {i} must be a string, got {type(specialty).__name__}"
            )

        # Trim and validate
        specialty_clean = specialty.strip()

        if not specialty_clean:
            raise ValidationError(f"Specialty at index {i} cannot be empty")

        validate_string_length(specialty_clean, min_length=2, max_length=100, field_name="Specialty")

        # Check for duplicates
        specialty_lower = specialty_clean.lower()
        if specialty_lower in seen:
            raise ValidationError(f"Duplicate specialty: '{specialty_clean}'")

        seen.add(specialty_lower)
        validated.append(specialty_clean)

    return validated


def validate_person_name(name: str) -> str:
    """
    Validate person name with specific constraints.

    Uses common name validation with person-specific rules.

    Args:
        name: Person name to validate

    Returns:
        str: Validated name

    Raises:
        ValidationError: If name is invalid
    """
    return validate_name(name, min_length=2, max_length=255)


def validate_person_email(email: str | None) -> str | None:
    """
    Validate person email address.

    Email is optional but must be valid if provided.

    Args:
        email: Email address to validate

    Returns:
        str | None: Validated email (lowercase) or None

    Raises:
        ValidationError: If email format is invalid
    """
    if email is None or email.strip() == "":
        return None

    return validate_email_address(email)


def validate_person_phone(phone: str | None) -> str | None:
    """
    Validate person phone number.

    Phone is optional but must be valid if provided.

    Args:
        phone: Phone number to validate

    Returns:
        str | None: Validated phone (digits only) or None

    Raises:
        ValidationError: If phone format is invalid
    """
    if phone is None or phone.strip() == "":
        return None

    return validate_phone_number(phone, allow_international=True)


def validate_target_clinical_blocks(
    blocks: int | None,
    person_type: str,
    pgy_level: int | None = None
) -> int | None:
    """
    Validate target clinical blocks for a person.

    Typical ranges:
    - Regular resident: 48-56 blocks (12-14 weeks × 4 blocks/week)
    - Chief resident: 24 blocks (6 clinical + 6 admin)
    - Research track: 8 blocks (2 clinical weeks)
    - Faculty: varies widely

    Args:
        blocks: Number of target clinical blocks
        person_type: Type of person ('resident' or 'faculty')
        pgy_level: PGY level if resident

    Returns:
        int | None: Validated target blocks

    Raises:
        ValidationError: If target blocks are invalid
    """
    if blocks is None:
        return None

    # Basic range validation
    validated = validate_integer_range(
        blocks,
        min_value=0,
        max_value=365 * 2,  # Max 2 blocks per day for whole year
        field_name="Target clinical blocks"
    )

    # Warn if outside typical ranges for residents
    if person_type.lower() == "resident" and pgy_level is not None:
        if validated < 4:
            # Less than 1 week is suspicious
            raise ValidationError(
                f"Target clinical blocks ({validated}) seems too low for a resident. "
                f"Expected at least 4 blocks (1 week)"
            )

        if validated > 200:
            # More than 50 weeks is suspicious
            raise ValidationError(
                f"Target clinical blocks ({validated}) seems too high. "
                f"Maximum recommended is 200 blocks (~50 weeks)"
            )

    return validated


def validate_supervision_requirements(
    person_type: str,
    pgy_level: int | None,
    performs_procedures: bool = False
) -> dict[str, any]:
    """
    Validate and return supervision requirements for a person.

    ACGME supervision ratios:
    - PGY-1: 1 faculty per 2 residents
    - PGY-2/3: 1 faculty per 4 residents
    - Faculty: No supervision needed

    Args:
        person_type: Type of person ('resident' or 'faculty')
        pgy_level: PGY level if resident
        performs_procedures: Whether person performs procedures

    Returns:
        dict: Supervision requirements
            - needs_supervision: bool
            - supervision_ratio: int (0 for faculty, 2 for PGY-1, 4 for PGY-2/3)
            - requires_procedure_supervision: bool

    Raises:
        ValidationError: If combination is invalid
    """
    person_type_lower = person_type.lower()

    if person_type_lower == "faculty":
        return {
            "needs_supervision": False,
            "supervision_ratio": 0,
            "requires_procedure_supervision": False
        }

    if person_type_lower == "resident":
        if pgy_level is None:
            raise ValidationError("Cannot determine supervision for resident without PGY level")

        # PGY-1 requires closer supervision
        ratio = 2 if pgy_level == 1 else 4

        return {
            "needs_supervision": True,
            "supervision_ratio": ratio,
            "requires_procedure_supervision": performs_procedures
        }

    raise ValidationError(f"Unknown person type: {person_type}")


def validate_call_counts(
    sunday_call_count: int | None = None,
    weekday_call_count: int | None = None,
    fmit_weeks_count: int | None = None
) -> tuple[int, int, int]:
    """
    Validate call and FMIT equity tracking counts.

    These counts should be non-negative and reasonable for an academic year.

    Args:
        sunday_call_count: Number of Sunday calls (default: 0)
        weekday_call_count: Number of weekday calls (default: 0)
        fmit_weeks_count: Number of FMIT weeks (default: 0)

    Returns:
        tuple[int, int, int]: Validated (sunday_call, weekday_call, fmit_weeks)

    Raises:
        ValidationError: If counts are invalid
    """
    # Default to 0 if not provided
    sunday = sunday_call_count if sunday_call_count is not None else 0
    weekday = weekday_call_count if weekday_call_count is not None else 0
    fmit = fmit_weeks_count if fmit_weeks_count is not None else 0

    # Validate ranges
    sunday = validate_integer_range(sunday, min_value=0, max_value=52, field_name="Sunday call count")
    weekday = validate_integer_range(weekday, min_value=0, max_value=365, field_name="Weekday call count")
    fmit = validate_integer_range(fmit, min_value=0, max_value=52, field_name="FMIT weeks count")

    # FMIT typically capped around 6 per year
    if fmit > 12:
        raise ValidationError(
            f"FMIT weeks count ({fmit}) seems too high. "
            f"Typical maximum is 6-12 weeks per year"
        )

    return sunday, weekday, fmit


def validate_primary_duty(primary_duty: str | None, person_type: str) -> str | None:
    """
    Validate primary duty field.

    Args:
        primary_duty: Primary duty description
        person_type: Type of person ('resident' or 'faculty')

    Returns:
        str | None: Validated primary duty

    Raises:
        ValidationError: If primary duty is invalid
    """
    if primary_duty is None or primary_duty.strip() == "":
        return None

    # Validate length and content
    validated = validate_string_length(
        primary_duty.strip(),
        min_length=2,
        max_length=255,
        field_name="Primary duty"
    )

    return validated
