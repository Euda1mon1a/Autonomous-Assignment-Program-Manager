"""Command pattern implementation for CQRS write operations.

This module provides the command side of CQRS, handling all state-changing
operations in the Residency Scheduler application.

Commands represent intentions to change state (e.g., CreateAssignment,
UpdateSchedule, ApproveSwap). They are immutable and validated before execution.

Architecture:
    Command -> CommandBus -> CommandHandler -> Write Database -> Events

Example:
    # Define a command
    @dataclass(frozen=True)
    class CreateAssignmentCommand(Command):
        person_id: UUID
        block_id: UUID
        rotation_id: UUID
        created_by: str

    # Define a handler
    class CreateAssignmentHandler(CommandHandler[CreateAssignmentCommand]):
        async def handle(self, command: CreateAssignmentCommand) -> CommandResult:
            # Validation
            if not await self._is_valid_assignment(command):
                return CommandResult(
                    success=False,
                    error="Invalid assignment"
                )

            # Business logic
            assignment = Assignment(
                person_id=command.person_id,
                block_id=command.block_id,
                rotation_id=command.rotation_id
            )
            self.db.add(assignment)
            await self.db.commit()

            # Emit events
            events = [AssignmentCreatedEvent(assignment_id=assignment.id)]

            return CommandResult(
                success=True,
                data={"assignment_id": assignment.id},
                events=events
            )

    # Execute command
    bus = CommandBus(db)
    bus.register_handler(CreateAssignmentCommand, CreateAssignmentHandler(db))
    result = await bus.execute(CreateAssignmentCommand(...))
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Type variables for generic command handling
TCommand = TypeVar("TCommand", bound="Command")
TResult = TypeVar("TResult")


@dataclass(frozen=True)
class Command(ABC):
    """
    Base class for all commands (write operations).

    Commands are immutable, intent-based objects that represent
    state-changing operations. They should be named in imperative
    form (e.g., CreateAssignment, ApproveSwap).

    All commands are frozen (immutable) after creation to prevent
    accidental modification during handling.

    Attributes:
        command_id: Unique identifier for this command instance
        timestamp: When the command was created
        user_id: Optional user who initiated the command
        metadata: Optional additional context
    """

    command_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DomainEvent:
    """
    Base class for domain events triggered by commands.

    Events represent facts that have occurred in the system.
    They are named in past tense (e.g., AssignmentCreated, SwapApproved).

    Events are used to:
    - Update read models
    - Trigger side effects (notifications, etc.)
    - Maintain audit logs
    - Enable event sourcing

    Attributes:
        event_id: Unique identifier for this event
        timestamp: When the event occurred
        aggregate_id: ID of the aggregate that emitted the event
        event_type: Type of event (class name by default)
        data: Event payload
    """

    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: UUID | None = None
    event_type: str = field(init=False)
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set event_type to class name if not specified."""
        if not hasattr(self, "event_type") or not self.event_type:
            object.__setattr__(self, "event_type", self.__class__.__name__)


@dataclass
class CommandResult:
    """
    Result of command execution.

    Encapsulates the outcome of a command, including success status,
    data, errors, and any domain events that were emitted.

    Attributes:
        success: Whether the command executed successfully
        data: Result data (e.g., created entity ID)
        error: Error message if failed
        error_code: Machine-readable error code
        events: Domain events emitted during execution
        metadata: Additional result metadata
    """

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    error_code: str | None = None
    events: list[DomainEvent] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(
        cls,
        data: dict[str, Any] | None = None,
        events: list[DomainEvent] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "CommandResult":
        """Create a successful result."""
        return cls(
            success=True,
            data=data or {},
            events=events or [],
            metadata=metadata or {},
        )

    @classmethod
    def fail(
        cls,
        error: str,
        error_code: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "CommandResult":
        """Create a failed result."""
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            metadata=metadata or {},
        )


class CommandHandler(ABC, Generic[TCommand]):
    """
    Base class for command handlers.

    Each command should have exactly one handler responsible for
    executing the command's business logic.

    Handlers should:
    - Validate command data
    - Execute business logic
    - Persist changes to write database
    - Emit domain events
    - Return CommandResult

    Type Parameters:
        TCommand: The type of command this handler processes
    """

    def __init__(self, db: Session):
        """
        Initialize command handler.

        Args:
            db: Database session for write operations
        """
        self.db = db

    @abstractmethod
    async def handle(self, command: TCommand) -> CommandResult:
        """
        Handle the command execution.

        This method must be implemented by concrete handlers.

        Args:
            command: The command to execute

        Returns:
            CommandResult: Result of the command execution

        Raises:
            ValidationError: If command data is invalid
            AppException: For business logic errors
        """
        pass

    async def validate(self, command: TCommand) -> None:
        """
        Validate command before execution.

        Override this method to add custom validation logic.
        By default, no validation is performed.

        Args:
            command: The command to validate

        Raises:
            ValidationError: If validation fails
        """
        pass


class CommandValidationMiddleware:
    """
    Middleware for validating commands using Pydantic schemas.

    This middleware intercepts commands before they reach handlers
    and validates them using Pydantic models for type safety and
    data validation.

    Example:
        class CreateAssignmentSchema(BaseModel):
            person_id: UUID
            block_id: UUID
            rotation_id: UUID

        middleware = CommandValidationMiddleware()
        middleware.register_schema(CreateAssignmentCommand, CreateAssignmentSchema)

        # Validation happens automatically in CommandBus
    """

    def __init__(self):
        """Initialize validation middleware."""
        self._schemas: dict[type[Command], type[BaseModel]] = {}

    def register_schema(
        self, command_type: type[Command], schema: type[BaseModel]
    ) -> None:
        """
        Register a Pydantic schema for a command type.

        Args:
            command_type: The command class to validate
            schema: Pydantic model for validation
        """
        self._schemas[command_type] = schema

    async def validate(self, command: Command) -> None:
        """
        Validate a command using its registered schema.

        Args:
            command: The command to validate

        Raises:
            ValidationError: If validation fails
        """
        command_type = type(command)
        if command_type not in self._schemas:
            # No schema registered, skip validation
            return

        schema = self._schemas[command_type]

        # Extract command data (excluding base Command fields)
        command_data = {
            k: v
            for k, v in command.__dict__.items()
            if k not in ("command_id", "timestamp", "user_id", "metadata")
        }

        try:
            # Validate using Pydantic
            schema(**command_data)
        except PydanticValidationError as e:
            error_messages = []
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                msg = error["msg"]
                error_messages.append(f"{field}: {msg}")

            raise ValidationError(
                f"Command validation failed: {'; '.join(error_messages)}"
            )


class CommandBus:
    """
    Command bus for dispatching commands to handlers.

    The CommandBus is responsible for:
    - Routing commands to appropriate handlers
    - Executing validation middleware
    - Managing command execution lifecycle
    - Publishing domain events after successful execution

    Example:
        # Setup
        bus = CommandBus(db)
        bus.register_handler(CreateAssignmentCommand, CreateAssignmentHandler(db))
        bus.add_middleware(validation_middleware)

        # Execute command
        command = CreateAssignmentCommand(
            person_id=person_id,
            block_id=block_id,
            rotation_id=rotation_id
        )
        result = await bus.execute(command)

        if result.success:
            print(f"Assignment created: {result.data['assignment_id']}")
        else:
            print(f"Error: {result.error}")
    """

    def __init__(self, db: Session):
        """
        Initialize command bus.

        Args:
            db: Database session for write operations
        """
        self.db = db
        self._handlers: dict[type[Command], CommandHandler] = {}
        self._middleware: list[CommandValidationMiddleware] = []
        self._event_handlers: list[callable] = []

    def register_handler(
        self, command_type: type[TCommand], handler: CommandHandler[TCommand]
    ) -> None:
        """
        Register a command handler.

        Args:
            command_type: The command class this handler processes
            handler: The handler instance
        """
        if command_type in self._handlers:
            logger.warning(
                f"Handler for {command_type.__name__} already registered. Overwriting."
            )
        self._handlers[command_type] = handler
        logger.debug(f"Registered handler for {command_type.__name__}")

    def add_middleware(self, middleware: CommandValidationMiddleware) -> None:
        """
        Add validation middleware.

        Args:
            middleware: Middleware instance
        """
        self._middleware.append(middleware)

    def add_event_handler(self, handler: callable) -> None:
        """
        Add an event handler for domain events.

        Event handlers are called after successful command execution
        to process emitted events (e.g., update read models, send notifications).

        Args:
            handler: Callable that accepts a list of DomainEvent
        """
        self._event_handlers.append(handler)

    async def execute(self, command: TCommand) -> CommandResult:
        """
        Execute a command.

        This method:
        1. Runs validation middleware
        2. Routes command to appropriate handler
        3. Executes the handler
        4. Publishes events on success
        5. Returns the result

        Args:
            command: The command to execute

        Returns:
            CommandResult: Result of command execution

        Raises:
            ValidationError: If command validation fails
            ValueError: If no handler is registered for command type
        """
        command_type = type(command)
        command_name = command_type.__name__

        logger.info(
            f"Executing command: {command_name} (ID: {command.command_id})",
            extra={"command_id": str(command.command_id), "command_type": command_name},
        )

        # Run validation middleware
        for middleware in self._middleware:
            try:
                await middleware.validate(command)
            except ValidationError as e:
                logger.warning(
                    f"Command validation failed: {command_name}",
                    extra={"command_id": str(command.command_id), "error": str(e)},
                )
                return CommandResult.fail(error=str(e), error_code="VALIDATION_ERROR")

        # Get handler
        if command_type not in self._handlers:
            error_msg = f"No handler registered for command type: {command_name}"
            logger.error(error_msg, extra={"command_type": command_name})
            raise ValueError(error_msg)

        handler = self._handlers[command_type]

        try:
            # Execute command
            result = await handler.handle(command)

            if result.success:
                logger.info(
                    f"Command executed successfully: {command_name}",
                    extra={
                        "command_id": str(command.command_id),
                        "event_count": len(result.events),
                    },
                )

                # Publish events
                if result.events:
                    await self._publish_events(result.events)
            else:
                logger.warning(
                    f"Command execution failed: {command_name}",
                    extra={
                        "command_id": str(command.command_id),
                        "error": result.error,
                        "error_code": result.error_code,
                    },
                )

            return result

        except ValidationError as e:
            logger.warning(
                f"Command handler validation failed: {command_name}",
                extra={"command_id": str(command.command_id), "error": str(e)},
            )
            return CommandResult.fail(error=str(e), error_code="VALIDATION_ERROR")

        except Exception as e:
            logger.error(
                f"Command execution error: {command_name}",
                extra={"command_id": str(command.command_id), "error": str(e)},
                exc_info=True,
            )
            return CommandResult.fail(
                error="An unexpected error occurred",
                error_code="INTERNAL_ERROR",
                metadata={"exception_type": type(e).__name__},
            )

    async def _publish_events(self, events: list[DomainEvent]) -> None:
        """
        Publish domain events to registered event handlers.

        Args:
            events: List of events to publish
        """
        for event in events:
            logger.debug(
                f"Publishing event: {event.event_type}",
                extra={
                    "event_id": str(event.event_id),
                    "event_type": event.event_type,
                    "aggregate_id": str(event.aggregate_id) if event.aggregate_id else None,
                },
            )

            for handler in self._event_handlers:
                try:
                    if callable(handler):
                        # Support both sync and async handlers
                        if hasattr(handler, "__call__"):
                            result = handler(event)
                            if hasattr(result, "__await__"):
                                await result
                except Exception as e:
                    logger.error(
                        f"Event handler error: {type(handler).__name__}",
                        extra={
                            "event_id": str(event.event_id),
                            "event_type": event.event_type,
                            "error": str(e),
                        },
                        exc_info=True,
                    )
                    # Don't let event handler failures fail the command


# Example command implementations for reference
# Note: When creating commands that inherit from Command, all custom fields
# must have defaults since Command has default fields. Alternatively, use
# field(default=...) or don't use frozen=True and set in __post_init__.


class ExampleCreateCommand(Command):
    """Example command for creating an entity.

    Example usage:
        cmd = ExampleCreateCommand(name="John", email="john@example.com")
    """

    name: str = ""
    email: str = ""

    def __init__(
        self,
        name: str,
        email: str,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize create command with required fields."""
        # Use object.__setattr__ since dataclass is frozen
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "email", email)
        # Initialize base Command fields
        object.__setattr__(self, "command_id", uuid4())
        object.__setattr__(self, "timestamp", datetime.utcnow())
        object.__setattr__(self, "user_id", user_id)
        object.__setattr__(self, "metadata", metadata or {})


class ExampleUpdateCommand(Command):
    """Example command for updating an entity.

    Example usage:
        cmd = ExampleUpdateCommand(entity_id=uuid, name="Jane")
    """

    entity_id: UUID = field(default_factory=uuid4)
    name: str | None = None
    email: str | None = None


class ExampleDeleteCommand(Command):
    """Example command for deleting an entity.

    Example usage:
        cmd = ExampleDeleteCommand(entity_id=uuid)
    """

    entity_id: UUID = field(default_factory=uuid4)
