"""
Validators module for ACGME compliance and fatigue tracking.

Provides enhanced validation capabilities:
- Advanced ACGME rule checking (24+4, night float, moonlighting, PGY-specific)
- Fatigue monitoring and prediction
- Comprehensive duty hour analysis
"""
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.schemas.schedule import ValidationResult, Violation
from app.models.person import Person

from .advanced_acgme import AdvancedACGMEValidator
from .fatigue_tracker import FatigueTracker


__all__ = [
    "AdvancedACGMEValidator",
    "FatigueTracker",
    "validate_schedule",
]


def validate_schedule(
    db: Session,
    start_date: date,
    end_date: date,
    include_fatigue: bool = True,
    fatigue_threshold: float = 70.0
) -> ValidationResult:
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
    from app.models.block import Block
    from app.models.assignment import Assignment

    total_blocks = (
        db.query(Block)
        .filter(Block.date >= start_date, Block.date <= end_date)
        .count()
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
