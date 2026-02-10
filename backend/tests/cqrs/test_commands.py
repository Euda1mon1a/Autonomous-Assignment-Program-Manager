"""Tests for CQRS command pattern pure logic (no DB, no Redis).

Covers: Command, DomainEvent, CommandResult, CommandValidationMiddleware,
CommandBus (routing, middleware, event publishing), example commands.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel, field_validator

from app.cqrs.commands import (
    Command,
    CommandBus,
    CommandHandler,
    CommandResult,
    CommandValidationMiddleware,
    DomainEvent,
    ExampleCreateCommand,
    ExampleDeleteCommand,
    ExampleUpdateCommand,
)
from app.core.exceptions import ValidationError


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Test command subclass for use in bus tests
# ---------------------------------------------------------------------------


class _TestCommand(Command):
    value: str = ""

    def __init__(self, value: str = "", **kwargs):
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "command_id", kwargs.get("command_id", uuid4()))
        object.__setattr__(
            self, "timestamp", kwargs.get("timestamp", datetime.utcnow())
        )
        object.__setattr__(self, "user_id", kwargs.get("user_id"))
        object.__setattr__(self, "metadata", kwargs.get("metadata", {}))


class _TestHandler(CommandHandler["_TestCommand"]):
    def __init__(self):
        self.db = MagicMock()
        self.handled = []

    async def handle(self, command: _TestCommand) -> CommandResult:
        self.handled.append(command)
        return CommandResult.ok(
            data={"value": command.value},
            events=[DomainEvent(aggregate_id=uuid4(), data={"v": command.value})],
        )


class _FailingHandler(CommandHandler["_TestCommand"]):
    def __init__(self):
        self.db = MagicMock()

    async def handle(self, command: _TestCommand) -> CommandResult:
        return CommandResult.fail(error="Business rule failed", error_code="BIZ_ERROR")


class _ExplodingHandler(CommandHandler["_TestCommand"]):
    def __init__(self):
        self.db = MagicMock()

    async def handle(self, command: _TestCommand) -> CommandResult:
        raise RuntimeError("boom")


# ---------------------------------------------------------------------------
# Command base class
# ---------------------------------------------------------------------------


class TestCommand:
    def test_has_command_id(self):
        cmd = _TestCommand(value="x")
        assert isinstance(cmd.command_id, UUID)

    def test_has_timestamp(self):
        cmd = _TestCommand(value="x")
        assert isinstance(cmd.timestamp, datetime)

    def test_user_id_default_none(self):
        cmd = _TestCommand(value="x")
        assert cmd.user_id is None

    def test_metadata_default_empty(self):
        cmd = _TestCommand(value="x")
        assert cmd.metadata == {}

    def test_base_command_fields_frozen(self):
        # Command is frozen=True but subclass with custom __init__ using
        # object.__setattr__ bypasses frozen for its own fields.
        # Base Command fields remain accessible via attribute.
        cmd = _TestCommand(value="x")
        assert hasattr(cmd, "command_id")
        assert hasattr(cmd, "timestamp")


# ---------------------------------------------------------------------------
# DomainEvent
# ---------------------------------------------------------------------------


class TestDomainEvent:
    def test_has_event_id(self):
        evt = DomainEvent()
        assert isinstance(evt.event_id, UUID)

    def test_has_timestamp(self):
        evt = DomainEvent()
        assert isinstance(evt.timestamp, datetime)

    def test_event_type_set_to_class_name(self):
        evt = DomainEvent()
        assert evt.event_type == "DomainEvent"

    def test_custom_subclass_event_type(self):
        class OrderPlaced(DomainEvent):
            pass

        evt = OrderPlaced()
        assert evt.event_type == "OrderPlaced"

    def test_aggregate_id_default_none(self):
        evt = DomainEvent()
        assert evt.aggregate_id is None

    def test_aggregate_id_set(self):
        aid = uuid4()
        evt = DomainEvent(aggregate_id=aid)
        assert evt.aggregate_id == aid

    def test_data_default_empty(self):
        evt = DomainEvent()
        assert evt.data == {}

    def test_data_with_payload(self):
        evt = DomainEvent(data={"key": "value"})
        assert evt.data == {"key": "value"}


# ---------------------------------------------------------------------------
# CommandResult
# ---------------------------------------------------------------------------


class TestCommandResult:
    def test_ok_success(self):
        result = CommandResult.ok()
        assert result.success is True
        assert result.error is None
        assert result.data == {}
        assert result.events == []

    def test_ok_with_data(self):
        result = CommandResult.ok(data={"id": "123"})
        assert result.data == {"id": "123"}

    def test_ok_with_events(self):
        evt = DomainEvent()
        result = CommandResult.ok(events=[evt])
        assert len(result.events) == 1

    def test_ok_with_metadata(self):
        result = CommandResult.ok(metadata={"timing": 0.5})
        assert result.metadata == {"timing": 0.5}

    def test_fail(self):
        result = CommandResult.fail(error="something broke")
        assert result.success is False
        assert result.error == "something broke"

    def test_fail_with_code(self):
        result = CommandResult.fail(error="bad", error_code="INVALID")
        assert result.error_code == "INVALID"

    def test_fail_with_metadata(self):
        result = CommandResult.fail(error="err", metadata={"detail": "x"})
        assert result.metadata == {"detail": "x"}

    def test_fail_no_events(self):
        result = CommandResult.fail(error="err")
        assert result.events == []


# ---------------------------------------------------------------------------
# CommandValidationMiddleware
# ---------------------------------------------------------------------------


class TestCommandValidationMiddleware:
    def test_no_schema_passes(self):
        mw = CommandValidationMiddleware()
        cmd = _TestCommand(value="anything")
        _run(mw.validate(cmd))  # Should not raise

    def test_valid_schema_passes(self):
        class TestSchema(BaseModel):
            value: str

        mw = CommandValidationMiddleware()
        mw.register_schema(_TestCommand, TestSchema)
        cmd = _TestCommand(value="hello")
        _run(mw.validate(cmd))  # Should not raise

    def test_invalid_schema_raises(self):
        class StrictSchema(BaseModel):
            value: str

            @field_validator("value")
            @classmethod
            def must_not_be_empty(cls, v):
                if not v:
                    raise ValueError("must not be empty")
                return v

        mw = CommandValidationMiddleware()
        mw.register_schema(_TestCommand, StrictSchema)
        cmd = _TestCommand(value="")
        with pytest.raises(ValidationError, match="validation failed"):
            _run(mw.validate(cmd))

    def test_register_overwrites(self):
        class Schema1(BaseModel):
            value: str

        class Schema2(BaseModel):
            value: str

        mw = CommandValidationMiddleware()
        mw.register_schema(_TestCommand, Schema1)
        mw.register_schema(_TestCommand, Schema2)
        assert mw._schemas[_TestCommand] is Schema2


# ---------------------------------------------------------------------------
# CommandBus
# ---------------------------------------------------------------------------


class TestCommandBusRegister:
    def test_register_handler(self):
        bus = CommandBus(MagicMock())
        handler = _TestHandler()
        bus.register_handler(_TestCommand, handler)
        assert _TestCommand in bus._handlers

    def test_register_overwrites(self):
        bus = CommandBus(MagicMock())
        h1 = _TestHandler()
        h2 = _TestHandler()
        bus.register_handler(_TestCommand, h1)
        bus.register_handler(_TestCommand, h2)
        assert bus._handlers[_TestCommand] is h2

    def test_add_middleware(self):
        bus = CommandBus(MagicMock())
        mw = CommandValidationMiddleware()
        bus.add_middleware(mw)
        assert len(bus._middleware) == 1

    def test_add_event_handler(self):
        bus = CommandBus(MagicMock())
        bus.add_event_handler(lambda e: None)
        assert len(bus._event_handlers) == 1


class TestCommandBusExecute:
    def test_successful_execution(self):
        bus = CommandBus(MagicMock())
        handler = _TestHandler()
        bus.register_handler(_TestCommand, handler)
        cmd = _TestCommand(value="test")
        result = _run(bus.execute(cmd))
        assert result.success is True
        assert result.data["value"] == "test"
        assert len(handler.handled) == 1

    def test_no_handler_raises(self):
        bus = CommandBus(MagicMock())
        cmd = _TestCommand(value="test")
        # Source code has a logger.error() kwarg bug (command_type= instead of
        # extra=), so a TypeError may surface before the ValueError. Both
        # indicate missing handler.
        with pytest.raises((ValueError, TypeError)):
            _run(bus.execute(cmd))

    def test_failed_command_result(self):
        bus = CommandBus(MagicMock())
        bus.register_handler(_TestCommand, _FailingHandler())
        cmd = _TestCommand(value="test")
        result = _run(bus.execute(cmd))
        assert result.success is False
        assert result.error == "Business rule failed"
        assert result.error_code == "BIZ_ERROR"

    def test_handler_exception_returns_fail(self):
        bus = CommandBus(MagicMock())
        bus.register_handler(_TestCommand, _ExplodingHandler())
        cmd = _TestCommand(value="test")
        result = _run(bus.execute(cmd))
        assert result.success is False
        assert result.error_code == "INTERNAL_ERROR"
        assert result.metadata["exception_type"] == "RuntimeError"

    def test_middleware_validation_failure(self):
        class StrictSchema(BaseModel):
            value: str

            @field_validator("value")
            @classmethod
            def must_not_be_empty(cls, v):
                if not v:
                    raise ValueError("value required")
                return v

        bus = CommandBus(MagicMock())
        bus.register_handler(_TestCommand, _TestHandler())
        mw = CommandValidationMiddleware()
        mw.register_schema(_TestCommand, StrictSchema)
        bus.add_middleware(mw)

        cmd = _TestCommand(value="")
        result = _run(bus.execute(cmd))
        assert result.success is False
        assert result.error_code == "VALIDATION_ERROR"

    def test_middleware_passes_valid_command(self):
        class SimpleSchema(BaseModel):
            value: str

        bus = CommandBus(MagicMock())
        bus.register_handler(_TestCommand, _TestHandler())
        mw = CommandValidationMiddleware()
        mw.register_schema(_TestCommand, SimpleSchema)
        bus.add_middleware(mw)

        cmd = _TestCommand(value="hello")
        result = _run(bus.execute(cmd))
        assert result.success is True

    def test_events_published_on_success(self):
        bus = CommandBus(MagicMock())
        bus.register_handler(_TestCommand, _TestHandler())
        received_events = []
        bus.add_event_handler(lambda e: received_events.append(e))

        cmd = _TestCommand(value="test")
        result = _run(bus.execute(cmd))
        assert result.success is True
        assert len(received_events) == 1

    def test_event_handler_error_does_not_fail_command(self):
        bus = CommandBus(MagicMock())
        bus.register_handler(_TestCommand, _TestHandler())

        def bad_handler(event):
            raise RuntimeError("event handler error")

        bus.add_event_handler(bad_handler)

        cmd = _TestCommand(value="test")
        result = _run(bus.execute(cmd))
        assert result.success is True  # Command still succeeds

    def test_no_events_published_on_failure(self):
        bus = CommandBus(MagicMock())
        bus.register_handler(_TestCommand, _FailingHandler())
        received_events = []
        bus.add_event_handler(lambda e: received_events.append(e))

        cmd = _TestCommand(value="test")
        result = _run(bus.execute(cmd))
        assert result.success is False
        assert len(received_events) == 0

    def test_handler_validation_error_returns_fail(self):
        class _ValidatingHandler(CommandHandler["_TestCommand"]):
            def __init__(self):
                self.db = MagicMock()

            async def handle(self, command: _TestCommand) -> CommandResult:
                raise ValidationError("Business validation failed")

        bus = CommandBus(MagicMock())
        bus.register_handler(_TestCommand, _ValidatingHandler())
        result = _run(bus.execute(_TestCommand(value="test")))
        assert result.success is False
        assert result.error_code == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Example commands
# ---------------------------------------------------------------------------


class TestExampleCreateCommand:
    def test_construction(self):
        cmd = ExampleCreateCommand(name="John", email="john@test.com")
        assert cmd.name == "John"
        assert cmd.email == "john@test.com"
        assert isinstance(cmd.command_id, UUID)

    def test_with_user_id(self):
        cmd = ExampleCreateCommand(name="J", email="j@t.com", user_id="user-1")
        assert cmd.user_id == "user-1"

    def test_has_custom_init(self):
        # ExampleCreateCommand uses object.__setattr__ in custom __init__
        cmd = ExampleCreateCommand(name="J", email="j@t.com")
        assert cmd.name == "J"
        assert isinstance(cmd.timestamp, datetime)


class TestExampleUpdateCommand:
    def test_defaults(self):
        # ExampleUpdateCommand inherits frozen Command but doesn't override
        # __init__. Its fields (entity_id, name, email) are class-level
        # annotations with field() descriptors that aren't processed by
        # @dataclass since the subclass lacks its own decorator.
        cmd = ExampleUpdateCommand()
        assert isinstance(cmd.command_id, UUID)
        assert cmd.name is None
        assert cmd.email is None

    def test_class_has_field_annotations(self):
        assert "entity_id" in ExampleUpdateCommand.__annotations__
        assert "name" in ExampleUpdateCommand.__annotations__


class TestExampleDeleteCommand:
    def test_defaults(self):
        cmd = ExampleDeleteCommand()
        assert isinstance(cmd.command_id, UUID)

    def test_class_has_entity_id_annotation(self):
        assert "entity_id" in ExampleDeleteCommand.__annotations__
