"""Data transformation pipelines for migrations.

This module provides reusable transformation functions and pipeline composition
for data migrations.

Example:
    # Create a transformation pipeline
    pipeline = TransformationPipeline()
    pipeline.add_step(normalize_email)
    pipeline.add_step(capitalize_name)

    # Apply to a record
    result = pipeline.apply(person_record)

    # Use built-in transformers
    transformer = DataTransformer()
    updates = transformer.normalize_person_email(person)
"""

import logging
import re
from collections.abc import Callable
from datetime import date, datetime
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class TransformationError(Exception):
    """Raised when a transformation fails."""

    pass


class TransformationPipeline:
    """
    Pipeline for composing multiple transformation steps.

    Each step is a function that takes a record and returns a dict of updates.
    """

    def __init__(self) -> None:
        """Initialize empty pipeline."""
        self.steps: list[Callable[[Any], dict[str, Any]]] = []

    def add_step(
        self, transform_func: Callable[[Any], dict[str, Any]]
    ) -> "TransformationPipeline":
        """
        Add a transformation step to the pipeline.

        Args:
            transform_func: Function that takes a record and returns updates dict

        Returns:
            Self for chaining
        """
        self.steps.append(transform_func)
        return self

    def apply(self, record: Any) -> dict[str, Any]:
        """
        Apply all transformation steps to a record.

        Args:
            record: Record to transform

        Returns:
            Dictionary of all updates to apply

        Raises:
            TransformationError: If any step fails
        """
        all_updates = {}

        for i, step in enumerate(self.steps):
            try:
                updates = step(record)
                all_updates.update(updates)
            except Exception as e:
                logger.error(f"Transformation step {i} failed: {e}")
                raise TransformationError(f"Step {i} failed: {e}") from e

        return all_updates

    def __len__(self) -> int:
        """Return number of steps in pipeline."""
        return len(self.steps)


class DataTransformer:
    """
    Collection of reusable data transformation functions.

    These can be used directly or composed into pipelines.
    """

    @staticmethod
    def normalize_email(record: Any) -> dict[str, Any]:
        """
        Normalize email address to lowercase.

        Args:
            record: Record with email attribute

        Returns:
            Dict with normalized email
        """
        if not hasattr(record, "email") or not record.email:
            return {}

        normalized = record.email.strip().lower()
        return {"email": normalized}

    @staticmethod
    def capitalize_name(record: Any) -> dict[str, Any]:
        """
        Capitalize name properly (Title Case).

        Args:
            record: Record with name attribute

        Returns:
            Dict with capitalized name
        """
        if not hasattr(record, "name") or not record.name:
            return {}

            # Handle special cases like "McDonald", "O'Brien"
        name = record.name.strip()
        capitalized = name.title()

        return {"name": capitalized}

    @staticmethod
    def normalize_phone_number(record: Any, field: str = "phone") -> dict[str, Any]:
        """
        Normalize phone number to (XXX) XXX-XXXX format.

        Args:
            record: Record with phone field
            field: Name of the phone field

        Returns:
            Dict with normalized phone number
        """
        if not hasattr(record, field):
            return {}

        phone = getattr(record, field)
        if not phone:
            return {}

            # Remove all non-digits
        digits = re.sub(r"\D", "", phone)

        # Format if 10 digits
        if len(digits) == 10:
            formatted = f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
            return {field: formatted}

        return {}

    @staticmethod
    def ensure_uuid(record: Any, field: str = "id") -> dict[str, Any]:
        """
        Ensure field is a valid UUID.

        Args:
            record: Record with UUID field
            field: Name of the UUID field

        Returns:
            Dict with UUID conversion if needed
        """
        if not hasattr(record, field):
            return {}

        value = getattr(record, field)

        # If already UUID, return empty
        if isinstance(value, UUID):
            return {}

            # Try to parse string as UUID
        try:
            uuid_value = UUID(str(value))
            return {field: uuid_value}
        except (ValueError, TypeError):
            logger.warning(f"Cannot convert {value} to UUID for field {field}")
            return {}

    @staticmethod
    def ensure_datetime(record: Any, field: str) -> dict[str, Any]:
        """
        Ensure field is a datetime object.

        Args:
            record: Record with datetime field
            field: Name of the datetime field

        Returns:
            Dict with datetime conversion if needed
        """
        if not hasattr(record, field):
            return {}

        value = getattr(record, field)

        # If already datetime, return empty
        if isinstance(value, datetime):
            return {}

            # If date, convert to datetime
        if isinstance(value, date):
            return {field: datetime.combine(value, datetime.min.time())}

            # Try to parse string
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                return {field: dt}
            except ValueError:
                logger.warning(f"Cannot convert {value} to datetime for field {field}")

        return {}

    @staticmethod
    def set_default_value(record: Any, field: str, default: Any) -> dict[str, Any]:
        """
        Set default value if field is None or missing.

        Args:
            record: Record to check
            field: Field name
            default: Default value to set

        Returns:
            Dict with default value if needed
        """
        if not hasattr(record, field) or getattr(record, field) is None:
            return {field: default}

        return {}

    @staticmethod
    def trim_whitespace(record: Any, fields: list[str]) -> dict[str, Any]:
        """
        Trim whitespace from string fields.

        Args:
            record: Record to transform
            fields: List of field names to trim

        Returns:
            Dict with trimmed values
        """
        updates = {}

        for field in fields:
            if not hasattr(record, field):
                continue

            value = getattr(record, field)
            if isinstance(value, str):
                trimmed = value.strip()
                if trimmed != value:
                    updates[field] = trimmed

        return updates

    @staticmethod
    def convert_to_boolean(record: Any, field: str) -> dict[str, Any]:
        """
        Convert field to boolean.

        Handles various formats: 'true', 'yes', '1', 1, True, etc.

        Args:
            record: Record to transform
            field: Field name

        Returns:
            Dict with boolean value
        """
        if not hasattr(record, field):
            return {}

        value = getattr(record, field)

        # Already boolean
        if isinstance(value, bool):
            return {}

            # String values
        if isinstance(value, str):
            lower = value.lower().strip()
            if lower in ("true", "yes", "1", "y", "t"):
                return {field: True}
            elif lower in ("false", "no", "0", "n", "f"):
                return {field: False}

                # Numeric values
        if isinstance(value, (int, float)):
            return {field: bool(value)}

        return {}

    @staticmethod
    def map_enum_value(
        record: Any, field: str, mapping: dict[Any, Any]
    ) -> dict[str, Any]:
        """
        Map old enum values to new ones.

        Args:
            record: Record to transform
            field: Field name
            mapping: Dict mapping old values to new values

        Returns:
            Dict with mapped value

        Example:
            mapping = {'admin': 'ADMIN', 'user': 'USER'}
            result = map_enum_value(record, 'role', mapping)
        """
        if not hasattr(record, field):
            return {}

        value = getattr(record, field)

        # Handle enum objects
        if hasattr(value, "value"):
            value = value.value

        if value in mapping:
            return {field: mapping[value]}

        return {}

    @staticmethod
    def add_audit_fields(record: Any, user: str = "system") -> dict[str, Any]:
        """
        Add standard audit fields (updated_at, updated_by).

        Args:
            record: Record to update
            user: User performing the update

        Returns:
            Dict with audit fields
        """
        updates = {"updated_at": datetime.utcnow()}

        if hasattr(record, "updated_by"):
            updates["updated_by"] = user

        return updates

    @staticmethod
    def validate_and_fix_range(
        record: Any,
        field: str,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> dict[str, Any]:
        """
        Validate numeric field is within range and fix if needed.

        Args:
            record: Record to validate
            field: Field name
            min_value: Minimum allowed value
            max_value: Maximum allowed value

        Returns:
            Dict with clamped value if out of range
        """
        if not hasattr(record, field):
            return {}

        value = getattr(record, field)

        if not isinstance(value, (int, float)):
            return {}

        clamped = value

        if min_value is not None and value < min_value:
            clamped = min_value
            logger.warning(
                f"Field {field} value {value} below minimum {min_value}, clamping"
            )

        if max_value is not None and value > max_value:
            clamped = max_value
            logger.warning(
                f"Field {field} value {value} above maximum {max_value}, clamping"
            )

        if clamped != value:
            return {field: clamped}

        return {}

    @staticmethod
    def conditional_update(
        record: Any, condition_func: Callable[[Any], bool], updates: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Apply updates only if condition is met.

        Args:
            record: Record to check
            condition_func: Function that returns True if updates should apply
            updates: Updates to apply if condition is True

        Returns:
            Dict with updates if condition met, empty dict otherwise

        Example:
            def is_faculty(record):
                return record.type == 'faculty'

            updates = conditional_update(
                person,
                is_faculty,
                {'performs_procedures': True}
            )
        """
        if condition_func(record):
            return updates
        return {}

    @staticmethod
    def copy_field(record: Any, source: str, target: str) -> dict[str, Any]:
        """
        Copy value from one field to another.

        Args:
            record: Record to transform
            source: Source field name
            target: Target field name

        Returns:
            Dict with copied value
        """
        if not hasattr(record, source):
            return {}

        value = getattr(record, source)
        return {target: value}

    @staticmethod
    def rename_field_value(
        record: Any, old_field: str, new_field: str
    ) -> dict[str, Any]:
        """
        Move value from old field to new field.

        Args:
            record: Record to transform
            old_field: Old field name
            new_field: New field name

        Returns:
            Dict with value in new field and None for old field
        """
        if not hasattr(record, old_field):
            return {}

        value = getattr(record, old_field)
        return {new_field: value, old_field: None}

        # Convenience functions for common transformations


def create_email_normalizer() -> TransformationPipeline:
    """
    Create pipeline for email normalization.

    Returns:
        TransformationPipeline that normalizes emails
    """
    pipeline = TransformationPipeline()
    pipeline.add_step(DataTransformer.normalize_email)
    return pipeline


def create_person_normalizer() -> TransformationPipeline:
    """
    Create pipeline for Person record normalization.

    Returns:
        TransformationPipeline for Person records
    """
    pipeline = TransformationPipeline()
    pipeline.add_step(DataTransformer.normalize_email)
    pipeline.add_step(DataTransformer.capitalize_name)
    pipeline.add_step(
        lambda r: DataTransformer.trim_whitespace(r, ["name", "email", "primary_duty"])
    )
    return pipeline


def create_audit_updater(user: str = "system") -> TransformationPipeline:
    """
    Create pipeline that adds audit fields.

    Args:
        user: User performing the update

    Returns:
        TransformationPipeline that adds audit fields
    """
    pipeline = TransformationPipeline()
    pipeline.add_step(lambda r: DataTransformer.add_audit_fields(r, user))
    return pipeline
