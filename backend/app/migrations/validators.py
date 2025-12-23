"""Migration validators for pre and post-migration validation.

This module provides validation functionality to ensure:
- Data integrity before migration
- Migration success verification
- Constraint validation
- Data quality checks

Example:
    validator = MigrationValidator(db_session)

    # Validate before migration
    pre_result = validator.validate_pre_migration(
        migration_id,
        checks=[
            validator.check_no_null_emails,
            validator.check_unique_constraint
        ]
    )

    # Execute migration if validation passes
    if pre_result.is_valid:
        migrator.execute_migration(...)

    # Validate after migration
    post_result = validator.validate_post_migration(migration_id)
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.types import GUID

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a validation issue found during checks."""

    severity: str  # 'error', 'warning', 'info'
    message: str
    details: str | None = None
    record_id: str | None = None

    def __repr__(self):
        return f"<ValidationIssue({self.severity}: {self.message})>"


class ValidationResult:
    """Result of validation checks."""

    def __init__(self):
        self.issues: list[ValidationIssue] = []
        self.checks_run: int = 0
        self.checks_passed: int = 0
        self.checks_failed: int = 0

    def add_issue(
        self,
        severity: str,
        message: str,
        details: str | None = None,
        record_id: str | None = None,
    ) -> None:
        """Add a validation issue."""
        issue = ValidationIssue(
            severity=severity, message=message, details=details, record_id=record_id
        )
        self.issues.append(issue)

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return any(issue.severity == "warning" for issue in self.issues)

    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return sum(1 for issue in self.issues if issue.severity == "warning")

    def get_summary(self) -> str:
        """Get a summary of validation results."""
        if self.is_valid:
            status = "PASSED"
        else:
            status = "FAILED"

        return (
            f"Validation {status}: "
            f"{self.checks_passed}/{self.checks_run} checks passed, "
            f"{self.error_count} errors, {self.warning_count} warnings"
        )

    def __repr__(self):
        return f"<ValidationResult({self.get_summary()})>"


class ValidationRecord(Base):
    """Database model for tracking validation history."""

    __tablename__ = "validation_records"

    id = Column(GUID(), primary_key=True, default=uuid4)
    migration_id = Column(GUID(), nullable=False, index=True)
    validation_type = Column(String(50), nullable=False)  # 'pre' or 'post'

    # Results
    is_valid = Column(String(10), nullable=False)  # 'true' or 'false'
    checks_run = Column(Integer, default=0)
    checks_passed = Column(Integer, default=0)
    checks_failed = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)

    # Details
    issues_summary = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ValidationRecord(migration={self.migration_id}, type={self.validation_type})>"


class MigrationValidator:
    """
    Service for validating migrations before and after execution.

    Provides pre-built validation checks and framework for custom checks.
    """

    def __init__(self, db: Session):
        """
        Initialize the validator.

        Args:
            db: Database session
        """
        self.db = db

    def validate_pre_migration(
        self,
        migration_id: UUID,
        checks: list[Callable[[Session], ValidationResult]],
        save_results: bool = True,
    ) -> ValidationResult:
        """
        Run pre-migration validation checks.

        Args:
            migration_id: Migration ID
            checks: List of validation check functions
            save_results: Whether to save results to database

        Returns:
            ValidationResult with all issues found
        """
        logger.info(f"Running pre-migration validation for {migration_id}")

        result = ValidationResult()

        for check in checks:
            try:
                check_result = check(self.db)
                result.checks_run += 1

                # Merge issues
                result.issues.extend(check_result.issues)

                if check_result.is_valid:
                    result.checks_passed += 1
                else:
                    result.checks_failed += 1

            except Exception as e:
                logger.error(f"Validation check failed: {e}", exc_info=True)
                result.checks_run += 1
                result.checks_failed += 1
                result.add_issue(
                    "error", f"Validation check failed: {check.__name__}", str(e)
                )

        logger.info(result.get_summary())

        # Save results if requested
        if save_results:
            self._save_validation_record(migration_id, "pre", result)

        return result

    def validate_post_migration(
        self,
        migration_id: UUID,
        checks: list[Callable[[Session], ValidationResult]],
        save_results: bool = True,
    ) -> ValidationResult:
        """
        Run post-migration validation checks.

        Args:
            migration_id: Migration ID
            checks: List of validation check functions
            save_results: Whether to save results to database

        Returns:
            ValidationResult with all issues found
        """
        logger.info(f"Running post-migration validation for {migration_id}")

        result = ValidationResult()

        for check in checks:
            try:
                check_result = check(self.db)
                result.checks_run += 1

                # Merge issues
                result.issues.extend(check_result.issues)

                if check_result.is_valid:
                    result.checks_passed += 1
                else:
                    result.checks_failed += 1

            except Exception as e:
                logger.error(f"Validation check failed: {e}", exc_info=True)
                result.checks_run += 1
                result.checks_failed += 1
                result.add_issue(
                    "error", f"Validation check failed: {check.__name__}", str(e)
                )

        logger.info(result.get_summary())

        # Save results if requested
        if save_results:
            self._save_validation_record(migration_id, "post", result)

        return result

    def _save_validation_record(
        self, migration_id: UUID, validation_type: str, result: ValidationResult
    ) -> None:
        """Save validation results to database."""
        try:
            # Create summary of issues
            issues_summary = "\n".join(
                [
                    f"[{issue.severity.upper()}] {issue.message}"
                    for issue in result.issues[:100]  # Limit to first 100
                ]
            )

            record = ValidationRecord(
                id=uuid4(),
                migration_id=migration_id,
                validation_type=validation_type,
                is_valid="true" if result.is_valid else "false",
                checks_run=result.checks_run,
                checks_passed=result.checks_passed,
                checks_failed=result.checks_failed,
                error_count=result.error_count,
                warning_count=result.warning_count,
                issues_summary=issues_summary,
            )

            self.db.add(record)
            self.db.commit()

        except SQLAlchemyError as e:
            logger.error(f"Failed to save validation record: {e}")
            self.db.rollback()

    # Built-in validation checks

    @staticmethod
    def check_no_null_values(
        table: Any, field: str
    ) -> Callable[[Session], ValidationResult]:
        """
        Create a check for null values in a required field.

        Args:
            table: SQLAlchemy model class
            field: Field name to check

        Returns:
            Validation check function
        """

        def check(db: Session) -> ValidationResult:
            result = ValidationResult()

            count = db.query(table).filter(getattr(table, field).is_(None)).count()

            if count > 0:
                result.add_issue(
                    "error",
                    f"Found {count} null values in {table.__tablename__}.{field}",
                    f"Field {field} should not be null",
                )

            return result

        check.__name__ = f"check_no_null_{table.__tablename__}_{field}"
        return check

    @staticmethod
    def check_unique_constraint(
        table: Any, field: str
    ) -> Callable[[Session], ValidationResult]:
        """
        Create a check for duplicate values in a unique field.

        Args:
            table: SQLAlchemy model class
            field: Field name to check

        Returns:
            Validation check function
        """

        def check(db: Session) -> ValidationResult:
            result = ValidationResult()

            # Find duplicates
            duplicates = (
                db.query(getattr(table, field), func.count(getattr(table, field)))
                .group_by(getattr(table, field))
                .having(func.count(getattr(table, field)) > 1)
                .all()
            )

            if duplicates:
                result.add_issue(
                    "error",
                    f"Found {len(duplicates)} duplicate values in {table.__tablename__}.{field}",
                    f"Values: {[d[0] for d in duplicates[:10]]}",  # First 10
                )

            return result

        check.__name__ = f"check_unique_{table.__tablename__}_{field}"
        return check

    @staticmethod
    def check_foreign_key_integrity(
        table: Any, fk_field: str, referenced_table: Any, referenced_field: str = "id"
    ) -> Callable[[Session], ValidationResult]:
        """
        Create a check for foreign key integrity.

        Args:
            table: SQLAlchemy model class with foreign key
            fk_field: Foreign key field name
            referenced_table: Referenced table model
            referenced_field: Referenced field name (default 'id')

        Returns:
            Validation check function
        """

        def check(db: Session) -> ValidationResult:
            result = ValidationResult()

            # Find orphaned records
            orphans = (
                db.query(table)
                .outerjoin(
                    referenced_table,
                    getattr(table, fk_field)
                    == getattr(referenced_table, referenced_field),
                )
                .filter(
                    getattr(referenced_table, referenced_field).is_(None),
                    getattr(table, fk_field).isnot(None),
                )
                .count()
            )

            if orphans > 0:
                result.add_issue(
                    "error",
                    f"Found {orphans} orphaned records in {table.__tablename__}.{fk_field}",
                    f"References to non-existent {referenced_table.__tablename__} records",
                )

            return result

        check.__name__ = f"check_fk_{table.__tablename__}_{fk_field}"
        return check

    @staticmethod
    def check_value_in_range(
        table: Any,
        field: str,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> Callable[[Session], ValidationResult]:
        """
        Create a check for values within acceptable range.

        Args:
            table: SQLAlchemy model class
            field: Field name to check
            min_value: Minimum acceptable value
            max_value: Maximum acceptable value

        Returns:
            Validation check function
        """

        def check(db: Session) -> ValidationResult:
            result = ValidationResult()

            query = db.query(table)

            if min_value is not None:
                below_min = query.filter(getattr(table, field) < min_value).count()

                if below_min > 0:
                    result.add_issue(
                        "warning",
                        f"Found {below_min} values below minimum {min_value} in {table.__tablename__}.{field}",
                    )

            if max_value is not None:
                above_max = query.filter(getattr(table, field) > max_value).count()

                if above_max > 0:
                    result.add_issue(
                        "warning",
                        f"Found {above_max} values above maximum {max_value} in {table.__tablename__}.{field}",
                    )

            return result

        check.__name__ = f"check_range_{table.__tablename__}_{field}"
        return check

    @staticmethod
    def check_email_format(
        table: Any, field: str = "email"
    ) -> Callable[[Session], ValidationResult]:
        """
        Create a check for valid email format.

        Args:
            table: SQLAlchemy model class
            field: Email field name

        Returns:
            Validation check function
        """

        def check(db: Session) -> ValidationResult:
            result = ValidationResult()

            # Simple email regex
            import re

            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

            records = db.query(table).filter(getattr(table, field).isnot(None)).all()

            invalid_count = 0
            for record in records:
                email = getattr(record, field)
                if email and not re.match(email_pattern, email):
                    invalid_count += 1

            if invalid_count > 0:
                result.add_issue(
                    "error",
                    f"Found {invalid_count} invalid email addresses in {table.__tablename__}.{field}",
                )

            return result

        check.__name__ = f"check_email_{table.__tablename__}_{field}"
        return check

    @staticmethod
    def check_record_count_unchanged(
        table: Any, expected_count: int
    ) -> Callable[[Session], ValidationResult]:
        """
        Create a check that record count hasn't changed.

        Useful for post-migration validation.

        Args:
            table: SQLAlchemy model class
            expected_count: Expected number of records

        Returns:
            Validation check function
        """

        def check(db: Session) -> ValidationResult:
            result = ValidationResult()

            actual_count = db.query(table).count()

            if actual_count != expected_count:
                result.add_issue(
                    "error",
                    f"Record count mismatch in {table.__tablename__}",
                    f"Expected {expected_count}, found {actual_count}",
                )

            return result

        check.__name__ = f"check_count_{table.__tablename__}"
        return check

    @staticmethod
    def check_custom(
        check_func: Callable[[Session], tuple[bool, str]], name: str
    ) -> Callable[[Session], ValidationResult]:
        """
        Create a custom validation check.

        Args:
            check_func: Function that returns (is_valid, message)
            name: Name for the check

        Returns:
            Validation check function
        """

        def check(db: Session) -> ValidationResult:
            result = ValidationResult()

            try:
                is_valid, message = check_func(db)

                if not is_valid:
                    result.add_issue("error", message)

            except Exception as e:
                result.add_issue("error", f"Custom check failed: {e}")

            return result

        check.__name__ = name
        return check
