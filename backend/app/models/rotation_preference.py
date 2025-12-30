"""Rotation preference model for soft scheduling constraints.

Unlike ACGME rules which are hard constraints, preferences are
optimization objectives that the scheduler tries to satisfy but
can violate if necessary.

Preferences allow coordinators to express scheduling desires like:
- "Prefer full days of the same activity"
- "Group specialty sessions consecutively"
- "Avoid Friday PM activities"
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class RotationPreference(Base):
    """
    Soft scheduling preferences for rotation templates.

    Preference Types:
    -----------------
    - full_day_grouping: Prefer AM+PM of same activity (full FM day, full elective day)
    - consecutive_specialty: Group specialty sessions together (min 2-4 consecutive)
    - avoid_isolated: Penalty for single orphaned half-day sessions
    - preferred_days: Prefer specific activities on specific days
    - avoid_friday_pm: Leave Friday PM open as travel buffer
    - balance_weekly: Distribute activities evenly across the week

    Weights:
    --------
    - low: Nice to have (penalty: 1x)
    - medium: Moderate priority (penalty: 2x)
    - high: Strong preference (penalty: 4x)
    - required: Soft but strongly enforced (penalty: 8x)

    The solver multiplies the base penalty by the weight factor when
    optimizing schedules.
    """

    __tablename__ = "rotation_preferences"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Foreign key to rotation template
    rotation_template_id = Column(
        GUID(),
        ForeignKey("rotation_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Preference identification
    preference_type = Column(
        String(50),
        nullable=False,
        comment="Type: full_day_grouping, consecutive_specialty, avoid_isolated, preferred_days, avoid_friday_pm, balance_weekly",
    )

    # Weight determines solver priority
    weight = Column(
        String(20),
        default="medium",
        nullable=False,
        comment="low, medium, high, required",
    )

    # Flexible configuration as JSON
    # Examples:
    # - consecutive_specialty: {"min_consecutive": 2}
    # - preferred_days: {"activity": "fm_clinic", "days": [1, 2, 5]}
    # - balance_weekly: {"max_same_per_day": 1}
    config_json = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Type-specific configuration parameters",
    )

    # Is this preference currently active?
    is_active = Column(Boolean, default=True, nullable=False)

    # Human-readable description for UI display
    description = Column(String(200), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    rotation_template = relationship(
        "RotationTemplate",
        back_populates="preferences",
    )

    def __repr__(self) -> str:
        status = "active" if self.is_active else "inactive"
        return f"<RotationPreference {self.preference_type} ({self.weight}, {status})>"

    @property
    def weight_multiplier(self) -> float:
        """Get the penalty multiplier for this weight level."""
        multipliers = {
            "low": 1.0,
            "medium": 2.0,
            "high": 4.0,
            "required": 8.0,
        }
        return multipliers.get(self.weight, 2.0)

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Safely get a configuration value."""
        if self.config_json is None:
            return default
        return self.config_json.get(key, default)


# Default preferences that can be added to new templates
PREFERENCE_DEFAULTS = {
    "full_day_grouping": {
        "description": "Prefer full days when possible (AM+PM same activity)",
        "default_weight": "medium",
        "config_schema": {},
    },
    "consecutive_specialty": {
        "description": "Group specialty sessions consecutively",
        "default_weight": "high",
        "config_schema": {"min_consecutive": 2},
    },
    "avoid_isolated": {
        "description": "Avoid single isolated half-day sessions",
        "default_weight": "low",
        "config_schema": {"penalty_multiplier": 1.5},
    },
    "preferred_days": {
        "description": "Prefer specific activities on specific days",
        "default_weight": "medium",
        "config_schema": {
            "activity": "fm_clinic",
            "days": [1, 2, 5],  # Mon, Tue, Fri
        },
    },
    "avoid_friday_pm": {
        "description": "Keep Friday PM open as travel buffer",
        "default_weight": "low",
        "config_schema": {},
    },
    "balance_weekly": {
        "description": "Distribute activities evenly across the week",
        "default_weight": "medium",
        "config_schema": {"max_same_per_day": 1},
    },
}
