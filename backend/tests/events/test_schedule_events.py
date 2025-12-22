"""Tests for schedule event handlers."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, call
from datetime import datetime, date
from uuid import uuid4

from app.events.handlers.schedule_events import (
    on_schedule_created,
    on_schedule_updated,
    on_schedule_published,
    on_assignment_created,
    on_assignment_updated,
    on_assignment_deleted,
    on_swap_requested,
    on_swap_approved,
    on_swap_executed,
    on_absence_created,
    on_absence_approved,
    on_acgme_violation_detected,
    on_acgme_override_applied,
    send_notification,
    invalidate_cache,
    update_metrics,
    register_schedule_handlers,
)
from app.events.event_types import (
    EventType,
    ScheduleCreatedEvent,
    ScheduleUpdatedEvent,
    SchedulePublishedEvent,
    AssignmentCreatedEvent,
    AssignmentUpdatedEvent,
    AssignmentDeletedEvent,
    SwapRequestedEvent,
    SwapApprovedEvent,
    SwapExecutedEvent,
    AbsenceCreatedEvent,
    AbsenceApprovedEvent,
    ACGMEViolationDetectedEvent,
    ACGMEOverrideAppliedEvent,
)


# =============================================================================
# Helper Functions Tests
# =============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    @pytest.mark.asyncio
    async def test_send_notification_success(self):
        """Test successful notification sending."""
        with patch('app.events.handlers.schedule_events.NotificationService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance

            await send_notification("user123", "Test message", "high")

            # Verify notification service was called correctly
            mock_instance.send.assert_called_once_with(
                user_id="user123",
                message="Test message",
                priority="high",
                channel="in_app"
            )

    @pytest.mark.asyncio
    async def test_send_notification_handles_import_error(self, caplog):
        """Test notification handles import error gracefully."""
        with patch('app.events.handlers.schedule_events.NotificationService', side_effect=ImportError):
            # Should not raise
            await send_notification("user123", "Test", "normal")

            # Should log warning
            assert any("Service not available" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_send_notification_handles_runtime_error(self, caplog):
        """Test notification handles runtime errors gracefully."""
        with patch('app.events.handlers.schedule_events.NotificationService') as mock_service:
            mock_instance = AsyncMock()
            mock_instance.send.side_effect = Exception("Service unavailable")
            mock_service.return_value = mock_instance

            # Should not raise
            await send_notification("user123", "Test", "normal")

            # Should log error
            assert any("Failed to send notification" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_invalidate_cache_success(self):
        """Test cache invalidation."""
        with patch('app.events.handlers.schedule_events.cache_manager') as mock_cache:
            mock_cache.delete = AsyncMock()

            await invalidate_cache("schedule:123")

            mock_cache.delete.assert_called_once_with("schedule:123")

    @pytest.mark.asyncio
    async def test_invalidate_cache_handles_import_error(self, caplog):
        """Test cache invalidation handles import error."""
        with patch('app.events.handlers.schedule_events.cache_manager', side_effect=ImportError):
            # Should not raise
            await invalidate_cache("schedule:123")

            # Should log debug message
            assert any("Cache manager not available" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_invalidate_cache_handles_runtime_error(self, caplog):
        """Test cache invalidation handles runtime error."""
        with patch('app.events.handlers.schedule_events.cache_manager') as mock_cache:
            mock_cache.delete = AsyncMock(side_effect=Exception("Redis unavailable"))

            # Should not raise
            await invalidate_cache("schedule:123")

            # Should log warning
            assert any("Failed to invalidate" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_update_metrics_without_prometheus(self, caplog):
        """Test metrics update without Prometheus."""
        # Should not raise even without prometheus
        await update_metrics("test_metric", 1.0)

        # Should log debug message (prometheus not available)
        assert any("Prometheus not available" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_update_metrics_with_prometheus(self):
        """Test metrics update with Prometheus available."""
        with patch('app.events.handlers.schedule_events.Counter'):
            with patch('app.events.handlers.schedule_events.Gauge'):
                # Should not raise
                await update_metrics("test_metric", 1.0)


# =============================================================================
# Schedule Event Handlers Tests
# =============================================================================


class TestScheduleEventHandlers:
    """Tests for schedule event handlers."""

    @pytest.mark.asyncio
    async def test_on_schedule_created(self, caplog):
        """Test schedule created handler."""
        event = ScheduleCreatedEvent(
            schedule_id="sched-123",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            created_by="user-456"
        )

        await on_schedule_created(event)

        # Verify logging occurred
        assert any("Schedule created: sched-123" in record.message for record in caplog.records)
        assert any("2025-01-01 to 2025-12-31" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_on_schedule_updated(self, caplog):
        """Test schedule updated handler."""
        event = ScheduleUpdatedEvent(
            schedule_id="sched-123",
            updated_by="user-456",
            changes=[{"field": "status", "old": "draft", "new": "published"}]
        )

        await on_schedule_updated(event)

        # Verify logging occurred
        assert any("Schedule updated: sched-123" in record.message for record in caplog.records)
        assert any("1 changes" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_on_schedule_published(self, caplog):
        """Test schedule published handler."""
        event = SchedulePublishedEvent(
            schedule_id="sched-123",
            published_by="user-456"
        )

        await on_schedule_published(event)

        # Verify logging occurred
        assert any("Schedule published: sched-123" in record.message for record in caplog.records)


# =============================================================================
# Assignment Event Handlers Tests
# =============================================================================


class TestAssignmentEventHandlers:
    """Tests for assignment event handlers."""

    @pytest.mark.asyncio
    async def test_on_assignment_created(self, caplog):
        """Test assignment created handler."""
        event = AssignmentCreatedEvent(
            assignment_id="assign-123",
            person_id="person-456",
            block_id="block-789",
            rotation_template_id="rotation-101"
        )

        await on_assignment_created(event)

        # Verify logging occurred
        assert any("Assignment created: assign-123" in record.message for record in caplog.records)
        assert any("person-456" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_on_assignment_updated(self, caplog):
        """Test assignment updated handler."""
        event = AssignmentUpdatedEvent(
            assignment_id="assign-123",
            updated_by="user-456",
            reason="Schedule adjustment"
        )

        await on_assignment_updated(event)

        # Verify logging occurred
        assert any("Assignment updated: assign-123" in record.message for record in caplog.records)
        assert any("Update reason: Schedule adjustment" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_on_assignment_updated_without_reason(self, caplog):
        """Test assignment updated handler without reason."""
        event = AssignmentUpdatedEvent(
            assignment_id="assign-123",
            updated_by="user-456",
            reason=None
        )

        await on_assignment_updated(event)

        # Verify logging occurred but no reason logged
        assert any("Assignment updated: assign-123" in record.message for record in caplog.records)
        assert not any("Update reason:" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_on_assignment_deleted(self, caplog):
        """Test assignment deleted handler."""
        event = AssignmentDeletedEvent(
            assignment_id="assign-123",
            deleted_by="user-456",
            reason="Coverage changed"
        )

        await on_assignment_deleted(event)

        # Verify logging occurred
        assert any("Assignment deleted: assign-123" in record.message for record in caplog.records)
        assert any("Deletion reason: Coverage changed" in record.message for record in caplog.records)


# =============================================================================
# Swap Event Handlers Tests
# =============================================================================


class TestSwapEventHandlers:
    """Tests for swap event handlers."""

    @pytest.mark.asyncio
    async def test_on_swap_requested(self, caplog):
        """Test swap requested handler."""
        event = SwapRequestedEvent(
            swap_id="swap-123",
            requester_id="user-456",
            swap_type="ONE_TO_ONE"
        )

        await on_swap_requested(event)

        # Verify logging occurred
        assert any("Swap requested: swap-123" in record.message for record in caplog.records)
        assert any("ONE_TO_ONE" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_on_swap_approved(self, caplog):
        """Test swap approved handler."""
        event = SwapApprovedEvent(
            swap_id="swap-123",
            approved_by="user-456"
        )

        await on_swap_approved(event)

        # Verify logging occurred
        assert any("Swap approved: swap-123" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_on_swap_executed(self, caplog):
        """Test swap executed handler."""
        event = SwapExecutedEvent(
            swap_id="swap-123",
            executed_by="user-456",
            assignment_changes=["change1", "change2"]
        )

        await on_swap_executed(event)

        # Verify logging occurred
        assert any("Swap executed: swap-123" in record.message for record in caplog.records)
        assert any("2 changes" in record.message for record in caplog.records)


# =============================================================================
# Absence Event Handlers Tests
# =============================================================================


class TestAbsenceEventHandlers:
    """Tests for absence event handlers."""

    @pytest.mark.asyncio
    async def test_on_absence_created(self, caplog):
        """Test absence created handler."""
        event = AbsenceCreatedEvent(
            absence_id="absence-123",
            person_id="person-456",
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 7),
            absence_type="vacation"
        )

        await on_absence_created(event)

        # Verify logging occurred
        assert any("Absence created: absence-123" in record.message for record in caplog.records)
        assert any("2025-06-01 to 2025-06-07" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_on_absence_approved(self, caplog):
        """Test absence approved handler."""
        event = AbsenceApprovedEvent(
            absence_id="absence-123",
            approved_by="user-456"
        )

        await on_absence_approved(event)

        # Verify logging occurred
        assert any("Absence approved: absence-123" in record.message for record in caplog.records)


# =============================================================================
# ACGME Compliance Event Handlers Tests
# =============================================================================


class TestACGMEEventHandlers:
    """Tests for ACGME compliance event handlers."""

    @pytest.mark.asyncio
    async def test_on_acgme_violation_detected(self, caplog):
        """Test ACGME violation detected handler."""
        event = ACGMEViolationDetectedEvent(
            violation_id="violation-123",
            person_id="person-456",
            violation_type="80_HOUR_RULE",
            severity="CRITICAL"
        )

        await on_acgme_violation_detected(event)

        # Verify warning log occurred
        assert any("ACGME violation detected: violation-123" in record.message for record in caplog.records)
        assert any("80_HOUR_RULE" in record.message for record in caplog.records)
        assert any("CRITICAL" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_on_acgme_override_applied(self, caplog):
        """Test ACGME override applied handler."""
        event = ACGMEOverrideAppliedEvent(
            override_id="override-123",
            assignment_id="assign-456",
            applied_by="user-789",
            approval_level="PROGRAM_DIRECTOR",
            override_reason="Emergency coverage",
            justification="Critical patient care needs"
        )

        await on_acgme_override_applied(event)

        # Verify warning log occurred
        assert any("ACGME override applied: override-123" in record.message for record in caplog.records)
        assert any("PROGRAM_DIRECTOR" in record.message for record in caplog.records)
        assert any("Override reason: Emergency coverage" in record.message for record in caplog.records)
        assert any("Justification: Critical patient care needs" in record.message for record in caplog.records)


# =============================================================================
# Handler Registration Tests
# =============================================================================


class TestHandlerRegistration:
    """Tests for handler registration."""

    def test_register_schedule_handlers(self, db, caplog):
        """Test handler registration."""
        from app.events.event_bus import EventBus

        event_bus = EventBus()

        register_schedule_handlers(event_bus, db)

        # Verify handlers were registered
        assert any("Registering schedule event handlers" in record.message for record in caplog.records)
        assert any("registered successfully" in record.message for record in caplog.records)

        # Verify event bus has subscribers
        assert EventType.SCHEDULE_CREATED in event_bus._subscribers
        assert EventType.SCHEDULE_UPDATED in event_bus._subscribers
        assert EventType.SCHEDULE_PUBLISHED in event_bus._subscribers
        assert EventType.ASSIGNMENT_CREATED in event_bus._subscribers
        assert EventType.ASSIGNMENT_UPDATED in event_bus._subscribers
        assert EventType.ASSIGNMENT_DELETED in event_bus._subscribers
        assert EventType.SWAP_REQUESTED in event_bus._subscribers
        assert EventType.SWAP_APPROVED in event_bus._subscribers
        assert EventType.SWAP_EXECUTED in event_bus._subscribers
        assert EventType.ABSENCE_CREATED in event_bus._subscribers
        assert EventType.ABSENCE_APPROVED in event_bus._subscribers
        assert EventType.ACGME_VIOLATION_DETECTED in event_bus._subscribers
        assert EventType.ACGME_OVERRIDE_APPLIED in event_bus._subscribers
