"""Tests for CQRS read model sync data models and pure logic (no DB)."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.cqrs.read_model_sync import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_BATCH_TIMEOUT_SECONDS,
    SYNC_LAG_CRITICAL_SECONDS,
    SYNC_LAG_WARNING_SECONDS,
    BatchProcessingStats,
    ConflictResolutionStrategy,
    ReadModelSyncService,
    SyncCheckpoint,
    SyncConflict,
    SyncMetrics,
    SyncPriority,
    SyncStatus,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestSyncStatus:
    def test_all_values(self):
        assert SyncStatus.SYNCING == "syncing"
        assert SyncStatus.IN_SYNC == "in_sync"
        assert SyncStatus.LAGGING == "lagging"
        assert SyncStatus.FAILED == "failed"
        assert SyncStatus.PAUSED == "paused"

    def test_count(self):
        assert len(SyncStatus) == 5

    def test_is_str_enum(self):
        assert isinstance(SyncStatus.SYNCING, str)


class TestConflictResolutionStrategy:
    def test_all_values(self):
        assert ConflictResolutionStrategy.LAST_WRITE_WINS == "last_write_wins"
        assert ConflictResolutionStrategy.FIRST_WRITE_WINS == "first_write_wins"
        assert ConflictResolutionStrategy.MANUAL == "manual"
        assert ConflictResolutionStrategy.REJECT == "reject"
        assert ConflictResolutionStrategy.MERGE == "merge"

    def test_count(self):
        assert len(ConflictResolutionStrategy) == 5


class TestSyncPriority:
    def test_all_values(self):
        assert SyncPriority.HIGH == "high"
        assert SyncPriority.NORMAL == "normal"
        assert SyncPriority.LOW == "low"

    def test_count(self):
        assert len(SyncPriority) == 3


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_sync_lag_warning(self):
        assert SYNC_LAG_WARNING_SECONDS == 60

    def test_sync_lag_critical(self):
        assert SYNC_LAG_CRITICAL_SECONDS == 300

    def test_default_batch_size(self):
        assert DEFAULT_BATCH_SIZE == 100

    def test_default_batch_timeout(self):
        assert DEFAULT_BATCH_TIMEOUT_SECONDS == 5


# ---------------------------------------------------------------------------
# SyncMetrics
# ---------------------------------------------------------------------------


class TestSyncMetrics:
    def test_defaults(self):
        m = SyncMetrics(read_model_name="test")
        assert m.read_model_name == "test"
        assert m.last_synced_event_id is None
        assert m.last_synced_sequence is None
        assert m.total_events_processed == 0
        assert m.events_processed_success == 0
        assert m.events_processed_failed == 0
        assert m.average_processing_time_ms == 0.0
        assert m.current_sync_lag_seconds == 0.0
        assert m.status == SyncStatus.IN_SYNC
        assert m.error_count == 0
        assert m.last_error is None

    def test_update_lag_in_sync(self):
        m = SyncMetrics(read_model_name="test")
        recent = datetime.utcnow() - timedelta(seconds=10)
        m.update_lag(recent)
        assert m.current_sync_lag_seconds < SYNC_LAG_WARNING_SECONDS
        assert m.status == SyncStatus.IN_SYNC

    def test_update_lag_lagging(self):
        m = SyncMetrics(read_model_name="test")
        old = datetime.utcnow() - timedelta(seconds=120)
        m.update_lag(old)
        assert m.current_sync_lag_seconds >= SYNC_LAG_WARNING_SECONDS
        assert m.status == SyncStatus.LAGGING

    def test_update_lag_failed(self):
        m = SyncMetrics(read_model_name="test")
        very_old = datetime.utcnow() - timedelta(seconds=600)
        m.update_lag(very_old)
        assert m.current_sync_lag_seconds >= SYNC_LAG_CRITICAL_SECONDS
        assert m.status == SyncStatus.FAILED

    def test_update_lag_none_timestamp(self):
        m = SyncMetrics(read_model_name="test")
        original_lag = m.current_sync_lag_seconds
        m.update_lag(None)
        assert m.current_sync_lag_seconds == original_lag

    def test_record_success(self):
        m = SyncMetrics(read_model_name="test")
        m.record_success(50.0)
        assert m.total_events_processed == 1
        assert m.events_processed_success == 1
        assert m.last_sync_timestamp is not None
        assert m.average_processing_time_ms > 0

    def test_record_success_exponential_average(self):
        m = SyncMetrics(read_model_name="test")
        # First call: 0.1 * 100 + 0.9 * 0 = 10
        m.record_success(100.0)
        assert m.average_processing_time_ms == pytest.approx(10.0)
        # Second call: 0.1 * 100 + 0.9 * 10 = 19
        m.record_success(100.0)
        assert m.average_processing_time_ms == pytest.approx(19.0)

    def test_record_success_multiple(self):
        m = SyncMetrics(read_model_name="test")
        m.record_success(10.0)
        m.record_success(20.0)
        m.record_success(30.0)
        assert m.total_events_processed == 3
        assert m.events_processed_success == 3

    def test_record_failure(self):
        m = SyncMetrics(read_model_name="test")
        m.record_failure("connection timeout")
        assert m.total_events_processed == 1
        assert m.events_processed_failed == 1
        assert m.error_count == 1
        assert m.last_error == "connection timeout"
        assert m.last_error_timestamp is not None
        assert m.status == SyncStatus.FAILED

    def test_record_failure_multiple(self):
        m = SyncMetrics(read_model_name="test")
        m.record_failure("err1")
        m.record_failure("err2")
        assert m.events_processed_failed == 2
        assert m.error_count == 2
        assert m.last_error == "err2"

    def test_mixed_success_and_failure(self):
        m = SyncMetrics(read_model_name="test")
        m.record_success(10.0)
        m.record_success(20.0)
        m.record_failure("error")
        assert m.total_events_processed == 3
        assert m.events_processed_success == 2
        assert m.events_processed_failed == 1


# ---------------------------------------------------------------------------
# SyncCheckpoint
# ---------------------------------------------------------------------------


class TestSyncCheckpoint:
    def test_creation(self):
        now = datetime.utcnow()
        cp = SyncCheckpoint(
            read_model_name="test",
            last_processed_sequence=42,
            last_processed_event_id="evt-123",
            checkpoint_timestamp=now,
            total_events_processed=100,
        )
        assert cp.read_model_name == "test"
        assert cp.last_processed_sequence == 42
        assert cp.last_processed_event_id == "evt-123"
        assert cp.checkpoint_timestamp == now
        assert cp.total_events_processed == 100


# ---------------------------------------------------------------------------
# SyncConflict (Pydantic BaseModel)
# ---------------------------------------------------------------------------


class TestSyncConflict:
    def test_creation(self):
        sc = SyncConflict(
            read_model_name="test",
            aggregate_id="agg-1",
            event_id="evt-1",
            event_sequence=5,
            conflict_type="data_mismatch",
            write_value={"name": "Alice"},
            read_value={"name": "Bob"},
        )
        assert sc.read_model_name == "test"
        assert sc.aggregate_id == "agg-1"
        assert sc.event_sequence == 5
        assert sc.resolved is False

    def test_defaults(self):
        sc = SyncConflict(
            read_model_name="t",
            aggregate_id="a",
            event_id="e",
            event_sequence=1,
            conflict_type="test",
            write_value=None,
            read_value=None,
        )
        assert sc.conflict_id  # auto-generated
        assert sc.resolution_strategy == ConflictResolutionStrategy.LAST_WRITE_WINS
        assert sc.resolved is False
        assert sc.resolved_at is None
        assert sc.resolved_by is None


# ---------------------------------------------------------------------------
# BatchProcessingStats
# ---------------------------------------------------------------------------


class TestBatchProcessingStats:
    def test_defaults(self):
        stats = BatchProcessingStats()
        assert stats.batch_id  # auto-generated
        assert stats.batch_size == 0
        assert stats.events_processed == 0
        assert stats.events_failed == 0
        assert stats.processing_time_ms == 0.0
        assert stats.started_at is not None
        assert stats.completed_at is None

    def test_custom_values(self):
        stats = BatchProcessingStats(
            batch_size=50, events_processed=45, events_failed=5
        )
        assert stats.batch_size == 50
        assert stats.events_processed == 45
        assert stats.events_failed == 5


# ---------------------------------------------------------------------------
# ReadModelSyncService (pure logic methods with mocked deps)
# ---------------------------------------------------------------------------


def _mock_service(**kwargs) -> ReadModelSyncService:
    """Create a ReadModelSyncService with mocked DB sessions and event deps."""
    db_write = MagicMock()
    db_read = MagicMock()
    event_bus = MagicMock()
    event_store = MagicMock()
    defaults = {
        "db_write": db_write,
        "db_read": db_read,
        "event_bus": event_bus,
        "event_store": event_store,
    }
    defaults.update(kwargs)
    return ReadModelSyncService(**defaults)


class TestReadModelSyncServiceInit:
    def test_defaults(self):
        svc = _mock_service()
        assert svc.enable_batch_processing is True
        assert svc.batch_size == DEFAULT_BATCH_SIZE
        assert svc.batch_timeout_seconds == DEFAULT_BATCH_TIMEOUT_SECONDS
        assert svc.enable_conflict_detection is True
        assert (
            svc.conflict_resolution_strategy
            == ConflictResolutionStrategy.LAST_WRITE_WINS
        )
        assert svc._is_running is False
        assert svc._projectors == {}
        assert svc._metrics == {}

    def test_custom_config(self):
        svc = _mock_service(
            enable_batch_processing=False,
            batch_size=50,
            conflict_resolution_strategy=ConflictResolutionStrategy.REJECT,
        )
        assert svc.enable_batch_processing is False
        assert svc.batch_size == 50
        assert svc.conflict_resolution_strategy == ConflictResolutionStrategy.REJECT


class TestReadModelSyncServiceCheckpoint:
    def test_update_checkpoint_new(self):
        svc = _mock_service()
        svc._update_checkpoint("proj_a", 10, "evt-10")
        assert "proj_a" in svc._checkpoints
        cp = svc._checkpoints["proj_a"]
        assert cp.last_processed_sequence == 10
        assert cp.last_processed_event_id == "evt-10"
        assert cp.total_events_processed == 1

    def test_update_checkpoint_existing(self):
        svc = _mock_service()
        svc._update_checkpoint("proj_a", 10, "evt-10")
        svc._update_checkpoint("proj_a", 20, "evt-20")
        cp = svc._checkpoints["proj_a"]
        assert cp.last_processed_sequence == 20
        assert cp.last_processed_event_id == "evt-20"
        assert cp.total_events_processed == 2

    def test_update_checkpoint_multiple_projectors(self):
        svc = _mock_service()
        svc._update_checkpoint("proj_a", 10, "evt-10")
        svc._update_checkpoint("proj_b", 5, "evt-5")
        assert len(svc._checkpoints) == 2


class TestReadModelSyncServiceMetrics:
    def test_get_sync_metrics_none(self):
        svc = _mock_service()
        assert svc.get_sync_metrics("nonexistent") is None

    def test_get_sync_metrics(self):
        svc = _mock_service()
        svc._metrics["proj_a"] = SyncMetrics(read_model_name="proj_a")
        m = svc.get_sync_metrics("proj_a")
        assert m is not None
        assert m.read_model_name == "proj_a"

    def test_get_all_metrics(self):
        svc = _mock_service()
        svc._metrics["a"] = SyncMetrics(read_model_name="a")
        svc._metrics["b"] = SyncMetrics(read_model_name="b")
        all_m = svc.get_all_metrics()
        assert len(all_m) == 2
        assert "a" in all_m
        assert "b" in all_m

    def test_get_all_metrics_returns_copy(self):
        svc = _mock_service()
        svc._metrics["a"] = SyncMetrics(read_model_name="a")
        copy = svc.get_all_metrics()
        copy["c"] = SyncMetrics(read_model_name="c")
        assert "c" not in svc._metrics


class TestReadModelSyncServiceStatusSummary:
    def test_empty(self):
        svc = _mock_service()
        summary = svc.get_sync_status_summary()
        assert summary["total_projectors"] == 0
        assert summary["in_sync"] == 0
        assert summary["lagging"] == 0
        assert summary["failed"] == 0
        assert summary["paused"] == 0
        assert summary["max_sync_lag_seconds"] == 0.0
        assert summary["total_events_processed"] == 0
        assert summary["is_running"] is False

    def test_mixed_statuses(self):
        svc = _mock_service()
        m1 = SyncMetrics(read_model_name="a", status=SyncStatus.IN_SYNC)
        m2 = SyncMetrics(
            read_model_name="b",
            status=SyncStatus.LAGGING,
            current_sync_lag_seconds=90.0,
        )
        m3 = SyncMetrics(read_model_name="c", status=SyncStatus.FAILED)
        svc._metrics = {"a": m1, "b": m2, "c": m3}
        svc._projectors = {"a": MagicMock(), "b": MagicMock(), "c": MagicMock()}
        svc._paused_projectors.add("c")

        summary = svc.get_sync_status_summary()
        assert summary["total_projectors"] == 3
        assert summary["in_sync"] == 1
        assert summary["lagging"] == 1
        assert summary["failed"] == 1
        assert summary["paused"] == 1
        assert summary["max_sync_lag_seconds"] == 90.0

    def test_total_events_and_failures(self):
        svc = _mock_service()
        m1 = SyncMetrics(
            read_model_name="a",
            total_events_processed=100,
            events_processed_failed=5,
        )
        m2 = SyncMetrics(
            read_model_name="b",
            total_events_processed=200,
            events_processed_failed=10,
        )
        svc._metrics = {"a": m1, "b": m2}
        svc._projectors = {"a": MagicMock(), "b": MagicMock()}

        summary = svc.get_sync_status_summary()
        assert summary["total_events_processed"] == 300
        assert summary["total_failures"] == 15


class TestReadModelSyncServiceConflicts:
    def test_get_conflicts_empty(self):
        svc = _mock_service()
        assert svc.get_conflicts() == []

    def test_get_conflicts_all(self):
        svc = _mock_service()
        c1 = SyncConflict(
            read_model_name="a",
            aggregate_id="agg",
            event_id="e1",
            event_sequence=1,
            conflict_type="test",
            write_value=None,
            read_value=None,
            resolved=False,
        )
        c2 = SyncConflict(
            read_model_name="a",
            aggregate_id="agg",
            event_id="e2",
            event_sequence=2,
            conflict_type="test",
            write_value=None,
            read_value=None,
            resolved=True,
        )
        svc._conflicts = [c1, c2]
        assert len(svc.get_conflicts()) == 2

    def test_get_conflicts_unresolved(self):
        svc = _mock_service()
        c1 = SyncConflict(
            read_model_name="a",
            aggregate_id="agg",
            event_id="e1",
            event_sequence=1,
            conflict_type="test",
            write_value=None,
            read_value=None,
            resolved=False,
        )
        c2 = SyncConflict(
            read_model_name="a",
            aggregate_id="agg",
            event_id="e2",
            event_sequence=2,
            conflict_type="test",
            write_value=None,
            read_value=None,
            resolved=True,
        )
        svc._conflicts = [c1, c2]
        unresolved = svc.get_conflicts(resolved=False)
        assert len(unresolved) == 1
        assert unresolved[0].event_id == "e1"

    def test_get_conflicts_resolved(self):
        svc = _mock_service()
        c1 = SyncConflict(
            read_model_name="a",
            aggregate_id="agg",
            event_id="e1",
            event_sequence=1,
            conflict_type="test",
            write_value=None,
            read_value=None,
            resolved=True,
        )
        svc._conflicts = [c1]
        resolved = svc.get_conflicts(resolved=True)
        assert len(resolved) == 1

    def test_get_conflicts_returns_copy(self):
        svc = _mock_service()
        conflicts = svc.get_conflicts()
        conflicts.append(MagicMock())
        assert len(svc._conflicts) == 0
