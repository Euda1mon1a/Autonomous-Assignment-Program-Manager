"""Seed the constraint_configurations table from ConstraintManager instances.

Reads from ConstraintManager.create_default() — the same source the engine uses —
so every constraint the solver knows about gets a DB row for frontend management.
Priority comes from constraint objects directly (no heuristics).
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.models.constraint_config import ConstraintConfiguration
from app.scheduling.constraints import ConstraintManager
from app.scheduling.constraints.base import HardConstraint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Legacy DB names that don't match constraint instance names.
LEGACY_RENAMES = {
    "EightyHourRule": "80HourRule",
    "OneInSevenRule": "1in7Rule",
    "OnePersonPerBlock": "ResidentInpatientHeadcount",
}

# Canonical category map — keyed by constraint name.
# Constraints not listed here get category from _infer_category().
CATEGORY_MAP: dict[str, str] = {
    # ACGME
    "80HourRule": "ACGME",
    "1in7Rule": "ACGME",
    "SupervisionRatio": "ACGME",
    "Availability": "ACGME",
    # CALL
    "CallAvailability": "CALL",
    "CallNightBeforeLeave": "CALL",
    "CallSpacing": "CALL",
    "OvernightCallCoverage": "CALL",
    "OvernightCallGeneration": "CALL",
    "NoConsecutiveCall": "CALL",
    "PostCallAutoAssignment": "CALL",
    "AdjunctCallExclusion": "CALL",
    "NightFloatPostCall": "CALL",
    "FMITCallProximity": "CALL",
    "FMITMandatoryCall": "CALL",
    "FMITWeekBlocking": "CALL",
    "PostFMITRecovery": "CALL",
    "PostFMITSundayBlocking": "CALL",
    # EQUITY
    "Equity": "EQUITY",
    "Continuity": "EQUITY",
    "EscalatingCallEquity": "EQUITY",
    "WeekdayCallEquity": "EQUITY",
    "WeekendWork": "EQUITY",
    "SundayCallEquity": "EQUITY",
    "HolidayCallEquity": "EQUITY",
    "FacultyClinicEquity": "EQUITY",
    # CAPACITY
    "ClinicCapacity": "CAPACITY",
    "MaxPhysiciansInClinic": "CAPACITY",
    "ResidentInpatientHeadcount": "CAPACITY",
    # COVERAGE
    "Coverage": "COVERAGE",
    # RESILIENCE
    "HubProtection": "RESILIENCE",
    "UtilizationBuffer": "RESILIENCE",
    "ZoneBoundary": "RESILIENCE",
    "PreferenceTrail": "RESILIENCE",
    "N1Vulnerability": "RESILIENCE",
    # FACULTY
    "FacultySupervision": "FACULTY",
    "FacultyDayAvailability": "FACULTY",
    "FacultyPrimaryDutyClinic": "FACULTY",
    "FacultyRoleClinic": "FACULTY",
    "FacultyClinicCap": "FACULTY",
    "FacultyCallPreference": "FACULTY",
    "SMFacultyNoRegularClinic": "FACULTY",
    "SMResidentFacultyAlignment": "FACULTY",
    # SCHEDULING
    "ActivityRequirement": "SCHEDULING",
    "GraduationRequirements": "SCHEDULING",
    "HalfDayRequirement": "SCHEDULING",
    "ResidentWeeklyClinic": "SCHEDULING",
    "ProtectedSlot": "SCHEDULING",
    "WednesdayAMInternOnly": "SCHEDULING",
    "WednesdayPMSingleFaculty": "SCHEDULING",
    "InvertedWednesday": "SCHEDULING",
    "DeptChiefWednesdayPreference": "SCHEDULING",
    "TuesdayCallPreference": "SCHEDULING",
    "LearnerSupervision": "SCHEDULING",
}


def _get_category(name: str) -> str:
    """Get canonical category for a constraint."""
    cat = CATEGORY_MAP.get(name)
    if cat:
        return cat
    logger.warning(
        "Constraint %r has no category mapping — defaulting to SCHEDULING", name
    )
    return "SCHEDULING"


def seed_constraints() -> None:
    """Populate constraint_configurations table from ConstraintManager instances."""
    manager = ConstraintManager.create_default(profile="faculty")

    db = SessionLocal()
    try:
        added_count = 0
        updated_count = 0
        renamed_count = 0

        # Rename legacy DB entries to match manager names
        for old_name, new_name in LEGACY_RENAMES.items():
            existing = (
                db.query(ConstraintConfiguration).filter_by(name=old_name).first()
            )
            if existing:
                existing.name = new_name
                renamed_count += 1
                logger.info("Renamed constraint %s → %s", old_name, new_name)

        if renamed_count:
            db.flush()

        # Seed/update from manager instances
        for constraint in manager.constraints:
            name = constraint.name
            is_soft = not isinstance(constraint, HardConstraint)
            weight = constraint.weight if is_soft else 1.0
            category = _get_category(name)
            priority = constraint.priority.name  # From object, not heuristic

            existing = db.query(ConstraintConfiguration).filter_by(name=name).first()

            if existing:
                # Preserve user-set enabled/weight, update metadata
                existing.category = category
                existing.priority = priority
                updated_count += 1
            else:
                new_config = ConstraintConfiguration(
                    name=name,
                    enabled=constraint.enabled,
                    weight=weight,
                    priority=priority,
                    category=category,
                    description=f"{'Soft' if is_soft else 'Hard'} constraint: {name}",
                )
                db.add(new_config)
                added_count += 1

        # Clean up orphaned DB rows (constraint removed from code)
        manager_names = {c.name for c in manager.constraints}
        orphans = (
            db.query(ConstraintConfiguration)
            .filter(~ConstraintConfiguration.name.in_(manager_names))
            .all()
        )
        for orphan in orphans:
            logger.warning("Removing orphaned constraint config: %s", orphan.name)
            db.delete(orphan)

        db.commit()
        logger.info(
            "Seeded constraints: %d added, %d updated, %d renamed, %d orphans removed.",
            added_count,
            updated_count,
            renamed_count,
            len(orphans),
        )
    except Exception as e:
        db.rollback()
        logger.error("Error seeding constraints: %s", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting constraint configuration seeding...")
    seed_constraints()
    logger.info("Done.")
