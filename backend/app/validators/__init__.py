"""
Validators module for ACGME compliance, fatigue tracking, and input validation.

Provides comprehensive validation capabilities:
- Advanced ACGME rule checking (24+4, night float, moonlighting, PGY-specific)
- Fatigue monitoring and prediction
- Input validation (email, phone, dates, etc.)
- Person-specific validators (PGY level, faculty role, etc.)
- Schedule-specific validators (assignments, blocks, conflicts)
- Date/time validators (ranges, academic years, ACGME periods)
- Input sanitization (XSS, SQL injection, path traversal prevention)
"""

from datetime import date
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.person import Person
    from app.schemas.schedule import ValidationResult, Violation

# Advanced ACGME and fatigue validators (lazy import to avoid circular dependencies)
try:
    from .advanced_acgme import AdvancedACGMEValidator
    from .fatigue_tracker import FatigueTracker
except ImportError:
    # These may not be available in all contexts
    AdvancedACGMEValidator = None  # type: ignore
    FatigueTracker = None  # type: ignore

# Common validators
from .common import (
    ValidationError,
    validate_email_address,
    validate_enum_value,
    validate_float_range,
    validate_integer_range,
    validate_military_id,
    validate_name,
    validate_non_empty_list,
    validate_phone_number,
    validate_string_length,
    validate_uuid,
)

# Date validators
from .date_validators import (
    validate_academic_year_dates,
    validate_acgme_work_period,
    validate_block_date,
    validate_date_in_range,
    validate_date_not_null,
    validate_date_range,
    validate_future_date,
    validate_past_date,
    validate_session_time,
    validate_time_between_dates,
    validate_week_number,
)

# Person validators
from .person_validators import (
    COMMON_SPECIALTIES,
    MAX_PGY_LEVEL,
    MIN_PGY_LEVEL,
    VALID_FACULTY_ROLES,
    VALID_PERSON_TYPES,
    validate_call_counts,
    validate_faculty_role,
    validate_person_email,
    validate_person_name,
    validate_person_phone,
    validate_person_type,
    validate_pgy_level,
    validate_primary_duty,
    validate_specialties,
    validate_supervision_requirements,
    validate_target_clinical_blocks,
)

# Sanitizers
from .sanitizers import (
    SanitizationError,
    normalize_unicode,
    sanitize_email_input,
    sanitize_filename,
    sanitize_html,
    sanitize_identifier,
    sanitize_json_input,
    sanitize_path,
    sanitize_search_query,
    sanitize_sql_like_pattern,
    strip_dangerous_characters,
    validate_no_script_tags,
)

# Schedule validators
from .schedule_validators import (
    MAX_CONSECUTIVE_HOURS,
    MAX_HOURS_AFTER_24,
    MAX_HOURS_PER_WEEK,
    MIN_TIME_OFF_HOURS,
    VALID_ASSIGNMENT_ROLES,
    VALID_SESSIONS,
    validate_activity_override,
    validate_assignment_role,
    validate_assignment_score,
    validate_block_exists,
    validate_block_session,
    validate_confidence_score,
    validate_no_duplicate_assignment,
    validate_notes,
    validate_one_in_seven_rule,
    validate_person_exists,
    validate_rotation_abbreviation,
    validate_rotation_name,
    validate_supervision_ratio,
    validate_weekly_hours_limit,
)

__all__ = [
    # Exceptions
    "ValidationError",
    "SanitizationError",
    # Advanced ACGME validators
    "AdvancedACGMEValidator",
    "FatigueTracker",
    "validate_schedule",
    # Common validators
    "validate_email_address",
    "validate_phone_number",
    "validate_name",
    "validate_uuid",
    "validate_integer_range",
    "validate_float_range",
    "validate_string_length",
    "validate_enum_value",
    "validate_military_id",
    "validate_non_empty_list",
    # Date validators
    "validate_date_not_null",
    "validate_date_range",
    "validate_date_in_range",
    "validate_academic_year_dates",
    "validate_block_date",
    "validate_acgme_work_period",
    "validate_future_date",
    "validate_past_date",
    "validate_time_between_dates",
    "validate_week_number",
    "validate_session_time",
    # Person validators
    "VALID_PERSON_TYPES",
    "VALID_FACULTY_ROLES",
    "MIN_PGY_LEVEL",
    "MAX_PGY_LEVEL",
    "COMMON_SPECIALTIES",
    "validate_person_type",
    "validate_pgy_level",
    "validate_faculty_role",
    "validate_specialties",
    "validate_person_name",
    "validate_person_email",
    "validate_person_phone",
    "validate_target_clinical_blocks",
    "validate_supervision_requirements",
    "validate_call_counts",
    "validate_primary_duty",
    # Schedule validators
    "VALID_ASSIGNMENT_ROLES",
    "VALID_SESSIONS",
    "MAX_HOURS_PER_WEEK",
    "MAX_CONSECUTIVE_HOURS",
    "MAX_HOURS_AFTER_24",
    "MIN_TIME_OFF_HOURS",
    "validate_assignment_role",
    "validate_block_session",
    "validate_rotation_name",
    "validate_rotation_abbreviation",
    "validate_activity_override",
    "validate_notes",
    "validate_no_duplicate_assignment",
    "validate_block_exists",
    "validate_person_exists",
    "validate_supervision_ratio",
    "validate_weekly_hours_limit",
    "validate_one_in_seven_rule",
    "validate_confidence_score",
    "validate_assignment_score",
    # Sanitizers
    "sanitize_html",
    "sanitize_sql_like_pattern",
    "sanitize_path",
    "sanitize_filename",
    "normalize_unicode",
    "sanitize_email_input",
    "sanitize_search_query",
    "strip_dangerous_characters",
    "sanitize_json_input",
    "validate_no_script_tags",
    "sanitize_identifier",
]


def validate_schedule(
    db: "Session",
    start_date: date,
    end_date: date,
    include_fatigue: bool = True,
    fatigue_threshold: float = 70.0,
) -> "ValidationResult":
    """
    Convenience function to validate schedule with all advanced checks.

    Runs comprehensive validation including:
    - 24+4 hour rule
    - Night float limits
    - PGY-specific requirements
    - Fatigue risk assessment (optional)

    Args:
        db: Database session
        start_date: Start of validation period
        end_date: End of validation period
        include_fatigue: Include fatigue risk analysis
        fatigue_threshold: Fatigue score threshold for warnings

    Returns:
        ValidationResult with all violations and statistics
    """
    # Import here to avoid circular dependencies
    from sqlalchemy.orm import Session

    from app.models.assignment import Assignment
    from app.models.block import Block
    from app.models.person import Person
    from app.schemas.schedule import ValidationResult, Violation

    from .advanced_acgme import AdvancedACGMEValidator
    from .fatigue_tracker import FatigueTracker

    validator = AdvancedACGMEValidator(db)
    fatigue_tracker = FatigueTracker(db)

    violations = []
    statistics = {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "residents_checked": 0,
        "high_fatigue_residents": 0,
    }

    # Get all residents
    residents = db.query(Person).filter(Person.type == "resident").all()
    statistics["residents_checked"] = len(residents)

    # Run advanced validations for each resident
    for resident in residents:
        # 24+4 rule
        violations.extend(
            validator.validate_24_plus_4_rule(resident.id, start_date, end_date)
        )

        # Night float limits
        violations.extend(
            validator.validate_night_float_limits(resident.id, start_date, end_date)
        )

        # PGY-specific rules
        violations.extend(
            validator.validate_pgy_specific_rules(resident.id, start_date, end_date)
        )

        # Moonlighting (assuming no external hours for now)
        violations.extend(
            validator.validate_moonlighting_hours(resident.id, start_date, end_date)
        )

    # Add fatigue risk warnings if requested
    if include_fatigue:
        high_risk = fatigue_tracker.get_high_risk_residents(
            end_date, threshold=fatigue_threshold
        )

        statistics["high_fatigue_residents"] = len(high_risk)

        for resident_data in high_risk:
            violations.append(
                Violation(
                    type="FATIGUE_RISK_WARNING",
                    severity="HIGH",
                    person_id=resident_data["person_id"],
                    person_name=resident_data["person_name"],
                    message=f"{resident_data['person_name']}: High fatigue risk (score: {resident_data['fatigue_score']:.1f})",
                    details={
                        "fatigue_score": resident_data["fatigue_score"],
                        "risk_level": resident_data["risk_level"],
                        "recovery_hours_needed": resident_data["recovery_hours_needed"],
                        "recommended_days_off": resident_data["recommended_days_off"],
                        "factors": resident_data["factors"],
                    },
                )
            )

    # Calculate coverage rate (simplified)
    total_blocks = (
        db.query(Block).filter(Block.date >= start_date, Block.date <= end_date).count()
    )

    assigned_blocks = (
        db.query(Assignment)
        .join(Block)
        .filter(Block.date >= start_date, Block.date <= end_date)
        .distinct(Assignment.block_id)
        .count()
    )

    coverage_rate = (assigned_blocks / total_blocks * 100) if total_blocks > 0 else 0.0

    statistics["total_blocks"] = total_blocks
    statistics["assigned_blocks"] = assigned_blocks

    return ValidationResult(
        valid=len(violations) == 0,
        total_violations=len(violations),
        violations=violations,
        coverage_rate=coverage_rate,
        statistics=statistics,
    )
