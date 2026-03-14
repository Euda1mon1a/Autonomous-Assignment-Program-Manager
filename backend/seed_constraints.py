"""Seed the constraint_configurations table from ConstraintManager instances.

Reads from ConstraintManager.create_default() — the same source the engine uses —
so every constraint the solver knows about gets a DB row for frontend management.
"""

import logging
import sys
from pathlib import Path

# Add backend directory to path to allow running as script
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.models.constraint_config import ConstraintConfiguration
from app.scheduling.constraints import ConstraintManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Legacy DB names that don't match constraint instance names.
# Rename these to match the manager so the sync works.
LEGACY_RENAMES = {
    "EightyHourRule": "80HourRule",
    "OneInSevenRule": "1in7Rule",
    "OnePersonPerBlock": "ResidentInpatientHeadcount",
}


def _classify_constraint(constraint: object) -> tuple[str, str]:
    """Derive category and priority from constraint type and weight."""
    from app.scheduling.constraints.base import HardConstraint

    is_hard = isinstance(constraint, HardConstraint)
    name = constraint.name

    # Category heuristics based on constraint name
    if name in ("80HourRule", "1in7Rule", "SupervisionRatio", "Availability"):
        category = "ACGME"
    elif "Call" in name or "FMIT" in name or name == "PostFMITRecovery":
        category = "CALL"
    elif "Capacity" in name or "Headcount" in name or "MaxPhysicians" in name:
        category = "CAPACITY"
    elif name == "Coverage" or "Clinic" in name:
        category = "COVERAGE"
    elif "Equity" in name or name == "Continuity":
        category = "EQUITY"
    elif name in (
        "HubProtection",
        "UtilizationBuffer",
        "ZoneBoundary",
        "PreferenceTrail",
        "N1Vulnerability",
    ):
        category = "RESILIENCE"
    elif "Faculty" in name or "SM" in name:
        category = "FACULTY"
    else:
        category = "SCHEDULING"

    priority = "CRITICAL" if is_hard else "MEDIUM"
    if hasattr(constraint, "weight") and constraint.weight >= 100:
        priority = "HIGH"

    return category, priority


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
            is_soft = hasattr(constraint, "weight")
            weight = constraint.weight if is_soft else 1.0
            category, priority = _classify_constraint(constraint)

            existing = db.query(ConstraintConfiguration).filter_by(name=name).first()

            if existing:
                # Preserve user-set enabled/weight, update category/priority
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

        db.commit()
        logger.info(
            "Seeded constraints: %d added, %d updated, %d renamed.",
            added_count,
            updated_count,
            renamed_count,
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
