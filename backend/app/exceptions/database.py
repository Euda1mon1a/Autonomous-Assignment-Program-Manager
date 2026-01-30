"""Database operation exceptions.

These exceptions are raised during database operations including queries,
inserts, updates, deletes, and constraint violations.
"""

from typing import Any

from app.core.exceptions import AppException, ConflictError, NotFoundError


class DatabaseError(AppException):
    """Base exception for database operation errors."""

    def __init__(
        self,
        message: str = "Database operation failed",
        operation: str | None = None,
        table: str | None = None,
        status_code: int = 500,
        **context: Any,
    ) -> None:
        """Initialize database error.

        Args:
            message: User-friendly error message
            operation: Database operation (SELECT, INSERT, UPDATE, DELETE)
            table: Affected table name
            status_code: HTTP status code
            **context: Additional context
        """
        super().__init__(message, status_code)
        self.operation = operation
        self.table = table
        self.context = context


class RecordNotFoundError(NotFoundError):
    """Raised when a database record is not found."""

    def __init__(
        self,
        message: str = "Record not found",
        model: str | None = None,
        record_id: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize record not found error.

        Args:
            message: User-friendly error message
            model: Model/table name
            record_id: ID of record that was not found
            **context: Additional context
        """
        super().__init__(message)
        self.model = model
        self.record_id = record_id
        self.context = context


class DuplicateRecordError(ConflictError):
    """Raised when attempting to create a duplicate record."""

    def __init__(
        self,
        message: str = "A record with this information already exists",
        model: str | None = None,
        field: str | None = None,
        value: Any = None,
        **context: Any,
    ) -> None:
        """Initialize duplicate record error.

        Args:
            message: User-friendly error message
            model: Model/table name
            field: Field with duplicate value
            value: Duplicate value (sanitized)
            **context: Additional context
        """
        super().__init__(message)
        self.model = model
        self.field = field
        self.value = value
        self.context = context


class IntegrityConstraintError(DatabaseError):
    """Raised when a database integrity constraint is violated."""

    def __init__(
        self,
        message: str = "Database constraint violated",
        constraint_name: str | None = None,
        constraint_type: str | None = None,
        table: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize integrity constraint error.

        Args:
            message: User-friendly error message
            constraint_name: Name of violated constraint
            constraint_type: Type (PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK)
            table: Affected table name
            **context: Additional context
        """
        super().__init__(
            message=message,
            table=table,
            status_code=409,
            **context,
        )
        self.constraint_name = constraint_name
        self.constraint_type = constraint_type


class ForeignKeyViolationError(IntegrityConstraintError):
    """Raised when a foreign key constraint is violated."""

    def __init__(
        self,
        message: str = "Referenced record does not exist",
        table: str | None = None,
        foreign_key: str | None = None,
        referenced_table: str | None = None,
        referenced_id: Any = None,
        **context: Any,
    ) -> None:
        """Initialize foreign key violation error.

        Args:
            message: User-friendly error message
            table: Table with foreign key
            foreign_key: Foreign key field name
            referenced_table: Referenced table name
            referenced_id: Referenced record ID
            **context: Additional context
        """
        super().__init__(
            message=message,
            constraint_type="FOREIGN KEY",
            table=table,
            **context,
        )
        self.foreign_key = foreign_key
        self.referenced_table = referenced_table
        self.referenced_id = referenced_id


class ConcurrentModificationError(ConflictError):
    """Raised when a record was modified by another user/process."""

    def __init__(
        self,
        message: str = "This record was modified by another user. Please refresh and try again.",
        model: str | None = None,
        record_id: str | None = None,
        expected_version: int | None = None,
        actual_version: int | None = None,
        **context: Any,
    ) -> None:
        """Initialize concurrent modification error.

        Args:
            message: User-friendly error message
            model: Model/table name
            record_id: ID of record
            expected_version: Expected version number
            actual_version: Actual version number
            **context: Additional context
        """
        super().__init__(message)
        self.model = model
        self.record_id = record_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        self.context = context


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    def __init__(
        self,
        message: str = "Unable to connect to database",
        database: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize database connection error.

        Args:
            message: User-friendly error message
            database: Database name
            **context: Additional context
        """
        super().__init__(
            message=message,
            status_code=503,
            **context,
        )
        self.database = database


class DatabaseTimeoutError(DatabaseError):
    """Raised when a database operation times out."""

    def __init__(
        self,
        message: str = "Database operation timed out",
        operation: str | None = None,
        timeout_seconds: int | None = None,
        **context: Any,
    ) -> None:
        """Initialize database timeout error.

        Args:
            message: User-friendly error message
            operation: Database operation that timed out
            timeout_seconds: Timeout limit in seconds
            **context: Additional context
        """
        super().__init__(
            message=message,
            operation=operation,
            status_code=504,
            **context,
        )
        self.timeout_seconds = timeout_seconds


class TransactionError(DatabaseError):
    """Raised when a database transaction fails."""

    def __init__(
        self,
        message: str = "Database transaction failed",
        reason: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize transaction error.

        Args:
            message: User-friendly error message
            reason: Reason for transaction failure
            **context: Additional context
        """
        super().__init__(
            message=message,
            status_code=500,
            **context,
        )
        self.reason = reason
