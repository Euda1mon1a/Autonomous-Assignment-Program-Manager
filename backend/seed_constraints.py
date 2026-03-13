"""Seed the constraint_configurations table with defaults from code."""

import logging
import sys
from pathlib import Path

# Add backend directory to path to allow running as script
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.models.constraint_config import ConstraintConfiguration
from app.scheduling.constraints.config import ConstraintConfigManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_constraints() -> None:
    """Populate constraint_configurations table with default configs."""
    manager = ConstraintConfigManager()

    db = SessionLocal()
    try:
        # Get all configs
        added_count = 0
        updated_count = 0

        for name, config in manager._configs.items():
            # Check if exists
            existing = db.query(ConstraintConfiguration).filter_by(name=name).first()

            if existing:
                # Update existing
                existing.description = config.description
                existing.category = config.category.value
                existing.priority = config.priority.name
                updated_count += 1
            else:
                # Create new
                new_config = ConstraintConfiguration(
                    name=name,
                    enabled=config.enabled,
                    weight=config.weight,
                    priority=config.priority.name,
                    category=config.category.value,
                    description=config.description,
                )
                db.add(new_config)
                added_count += 1

        db.commit()
        logger.info(
            f"Seeded constraints: {added_count} added, {updated_count} updated."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding constraints: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting constraint configuration seeding...")
    seed_constraints()
    logger.info("Done.")
