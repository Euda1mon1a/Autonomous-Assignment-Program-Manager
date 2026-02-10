"""Tests for event replay service models and pure logic (no DB)."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.events.event_types import BaseEvent, EventMetadata, EventType
from app.events.replay_service import (
    ReplayCheckpoint,
    ReplayConfig,
    ReplayFilterConfig,
    ReplayProgress,
    ReplaySpeed,
    ReplayStatus,
    ReplayTarget,
    ReplayTargetConfig,
    ReplayTransformer,
    ReplayVerificationResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _event(
    aggregate_id: str = "a1",
    aggregate_type: str = "schedule",
    event_type: str = "ScheduleCreated",
    user_id: str = "u1",
    correlation_id: str = "c1",
) -> BaseEvent:
    """Build a BaseEvent for testing."""
    meta = EventMetadata(
        event_type=event_type,
        user_id=user_id,
        correlation_id=correlation_id,
    )
    return BaseEvent(
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        metadata=meta,
    )


# ---------------------------------------------------------------------------
# ReplayStatus enum
# ---------------------------------------------------------------------------


class TestReplayStatus:
    def test_all_values(self):
        assert ReplayStatus.PENDING == "pending"
        assert ReplayStatus.RUNNING == "running"
        assert ReplayStatus.PAUSED == "paused"
        assert ReplayStatus.COMPLETED == "completed"
        assert ReplayStatus.FAILED == "failed"
        assert ReplayStatus.CANCELLED == "cancelled"

    def test_count(self):
        assert len(ReplayStatus) == 6

    def test_is_str_enum(self):
        assert isinstance(ReplayStatus.PENDING, str)


# ---------------------------------------------------------------------------
# ReplaySpeed enum
# ---------------------------------------------------------------------------


class TestReplaySpeed:
    def test_all_values(self):
        assert ReplaySpeed.REAL_TIME == "real_time"
        assert ReplaySpeed.SLOW_MOTION == "slow_motion"
        assert ReplaySpeed.NORMAL == "normal"
        assert ReplaySpeed.FAST == "fast"
        assert ReplaySpeed.MAXIMUM == "maximum"

    def test_count(self):
        assert len(ReplaySpeed) == 5

    def test_is_str_enum(self):
        assert isinstance(ReplaySpeed.NORMAL, str)


# ---------------------------------------------------------------------------
# ReplayTarget enum
# ---------------------------------------------------------------------------


class TestReplayTarget:
    def test_all_values(self):
        assert ReplayTarget.TIMESTAMP == "timestamp"
        assert ReplayTarget.SEQUENCE_NUMBER == "sequence_number"
        assert ReplayTarget.EVENT_COUNT == "event_count"
        assert ReplayTarget.LATEST == "latest"

    def test_count(self):
        assert len(ReplayTarget) == 4


# ---------------------------------------------------------------------------
# ReplayFilterConfig
# ---------------------------------------------------------------------------


class TestReplayFilterConfig:
    def test_default_empty(self):
        f = ReplayFilterConfig()
        assert f.aggregate_ids is None
        assert f.aggregate_types is None
        assert f.event_types is None
        assert f.user_ids is None
        assert f.correlation_ids is None
        assert f.exclude_event_types is None
        assert f.exclude_aggregate_types is None

    def test_matches_all_when_empty(self):
        f = ReplayFilterConfig()
        e = _event()
        assert f.matches(e) is True

    def test_matches_aggregate_id_include(self):
        f = ReplayFilterConfig(aggregate_ids=["a1", "a2"])
        assert f.matches(_event(aggregate_id="a1")) is True
        assert f.matches(_event(aggregate_id="a3")) is False

    def test_matches_aggregate_type_include(self):
        f = ReplayFilterConfig(aggregate_types=["schedule"])
        assert f.matches(_event(aggregate_type="schedule")) is True
        assert f.matches(_event(aggregate_type="person")) is False

    def test_matches_event_type_include(self):
        f = ReplayFilterConfig(event_types=[EventType.SCHEDULE_CREATED])
        assert f.matches(_event(event_type=EventType.SCHEDULE_CREATED.value)) is True
        assert f.matches(_event(event_type=EventType.SCHEDULE_UPDATED.value)) is False

    def test_matches_user_id_include(self):
        f = ReplayFilterConfig(user_ids=["u1", "u2"])
        assert f.matches(_event(user_id="u1")) is True
        assert f.matches(_event(user_id="u99")) is False

    def test_matches_correlation_id_include(self):
        f = ReplayFilterConfig(correlation_ids=["c1"])
        assert f.matches(_event(correlation_id="c1")) is True
        assert f.matches(_event(correlation_id="c99")) is False

    def test_matches_exclude_event_type(self):
        f = ReplayFilterConfig(exclude_event_types=[EventType.SCHEDULE_DELETED])
        assert f.matches(_event(event_type=EventType.SCHEDULE_CREATED.value)) is True
        assert f.matches(_event(event_type=EventType.SCHEDULE_DELETED.value)) is False

    def test_matches_exclude_aggregate_type(self):
        f = ReplayFilterConfig(exclude_aggregate_types=["person"])
        assert f.matches(_event(aggregate_type="schedule")) is True
        assert f.matches(_event(aggregate_type="person")) is False

    def test_matches_combined_filters(self):
        f = ReplayFilterConfig(
            aggregate_types=["schedule"],
            user_ids=["u1"],
        )
        # Both match
        assert f.matches(_event(aggregate_type="schedule", user_id="u1")) is True
        # Wrong user
        assert f.matches(_event(aggregate_type="schedule", user_id="u2")) is False
        # Wrong type
        assert f.matches(_event(aggregate_type="person", user_id="u1")) is False

    def test_matches_include_and_exclude(self):
        f = ReplayFilterConfig(
            aggregate_types=["schedule"],
            exclude_event_types=[EventType.SCHEDULE_DELETED],
        )
        assert (
            f.matches(
                _event(
                    aggregate_type="schedule",
                    event_type=EventType.SCHEDULE_CREATED.value,
                )
            )
            is True
        )
        assert (
            f.matches(
                _event(
                    aggregate_type="schedule",
                    event_type=EventType.SCHEDULE_DELETED.value,
                )
            )
            is False
        )


# ---------------------------------------------------------------------------
# ReplayTransformer
# ---------------------------------------------------------------------------


class TestReplayTransformer:
    def test_defaults_empty(self):
        t = ReplayTransformer()
        assert t.field_mappings == {}
        assert t.field_transformations == {}
        assert t.metadata_overrides == {}
        assert t.aggregate_id_mapping == {}

    def test_with_field_mappings(self):
        t = ReplayTransformer(field_mappings={"old_name": "new_name"})
        assert t.field_mappings["old_name"] == "new_name"

    def test_with_metadata_overrides(self):
        t = ReplayTransformer(metadata_overrides={"user_id": "new_user"})
        assert t.metadata_overrides["user_id"] == "new_user"

    def test_with_aggregate_id_mapping(self):
        t = ReplayTransformer(aggregate_id_mapping={"old_id": "new_id"})
        assert t.aggregate_id_mapping["old_id"] == "new_id"


# ---------------------------------------------------------------------------
# ReplayTargetConfig
# ---------------------------------------------------------------------------


class TestReplayTargetConfig:
    def test_latest_target(self):
        t = ReplayTargetConfig(target_type=ReplayTarget.LATEST)
        assert t.target_type == ReplayTarget.LATEST
        assert t.target_timestamp is None
        assert t.target_sequence_number is None
        assert t.target_event_count is None

    def test_timestamp_target_valid(self):
        ts = datetime(2026, 1, 1)
        t = ReplayTargetConfig(
            target_type=ReplayTarget.TIMESTAMP,
            target_timestamp=ts,
        )
        assert t.target_timestamp == ts

    def test_timestamp_target_explicit_none_raises(self):
        """Validator fires when field is explicitly passed as None."""
        with pytest.raises(ValidationError, match="target_timestamp required"):
            ReplayTargetConfig(
                target_type=ReplayTarget.TIMESTAMP, target_timestamp=None
            )

    def test_sequence_number_target_valid(self):
        t = ReplayTargetConfig(
            target_type=ReplayTarget.SEQUENCE_NUMBER,
            target_sequence_number=500,
        )
        assert t.target_sequence_number == 500

    def test_sequence_number_target_explicit_none_raises(self):
        """Validator fires when field is explicitly passed as None."""
        with pytest.raises(ValidationError, match="target_sequence_number required"):
            ReplayTargetConfig(
                target_type=ReplayTarget.SEQUENCE_NUMBER, target_sequence_number=None
            )

    def test_event_count_target_valid(self):
        t = ReplayTargetConfig(
            target_type=ReplayTarget.EVENT_COUNT,
            target_event_count=100,
        )
        assert t.target_event_count == 100

    def test_event_count_target_explicit_none_raises(self):
        """Validator fires when field is explicitly passed as None."""
        with pytest.raises(ValidationError, match="target_event_count required"):
            ReplayTargetConfig(
                target_type=ReplayTarget.EVENT_COUNT, target_event_count=None
            )

    def test_event_count_zero_is_valid(self):
        """Zero is a valid integer, not None."""
        t = ReplayTargetConfig(
            target_type=ReplayTarget.EVENT_COUNT,
            target_event_count=0,
        )
        assert t.target_event_count == 0


# ---------------------------------------------------------------------------
# ReplayConfig
# ---------------------------------------------------------------------------


class TestReplayConfig:
    def _make_config(self, **overrides):
        defaults = {
            "start_timestamp": datetime(2026, 1, 1),
            "target": ReplayTargetConfig(target_type=ReplayTarget.LATEST),
        }
        defaults.update(overrides)
        return ReplayConfig(**defaults)

    def test_defaults(self):
        c = self._make_config()
        assert c.speed == ReplaySpeed.NORMAL
        assert c.filters is None
        assert c.transformer is None
        assert c.batch_size == 100
        assert c.verify_after_replay is True
        assert c.emit_events is False
        assert c.checkpoint_interval == 1000

    def test_replay_id_auto_generated(self):
        c = self._make_config()
        assert c.replay_id  # non-empty
        assert len(c.replay_id) > 10  # UUID string

    def test_custom_replay_id(self):
        c = self._make_config(replay_id="custom-id")
        assert c.replay_id == "custom-id"

    def test_custom_speed(self):
        c = self._make_config(speed=ReplaySpeed.FAST)
        assert c.speed == ReplaySpeed.FAST

    def test_batch_size_min(self):
        c = self._make_config(batch_size=1)
        assert c.batch_size == 1

    def test_batch_size_max(self):
        c = self._make_config(batch_size=10000)
        assert c.batch_size == 10000

    def test_batch_size_below_min_raises(self):
        with pytest.raises(ValidationError):
            self._make_config(batch_size=0)

    def test_batch_size_above_max_raises(self):
        with pytest.raises(ValidationError):
            self._make_config(batch_size=10001)

    def test_checkpoint_interval_min(self):
        c = self._make_config(checkpoint_interval=1)
        assert c.checkpoint_interval == 1

    def test_checkpoint_interval_below_min_raises(self):
        with pytest.raises(ValidationError):
            self._make_config(checkpoint_interval=0)

    def test_with_filters(self):
        f = ReplayFilterConfig(user_ids=["u1"])
        c = self._make_config(filters=f)
        assert c.filters is not None
        assert c.filters.user_ids == ["u1"]

    def test_with_transformer(self):
        t = ReplayTransformer(field_mappings={"a": "b"})
        c = self._make_config(transformer=t)
        assert c.transformer is not None

    def test_start_timestamp_required(self):
        with pytest.raises(ValidationError):
            ReplayConfig(target=ReplayTargetConfig(target_type=ReplayTarget.LATEST))

    def test_target_required(self):
        with pytest.raises(ValidationError):
            ReplayConfig(start_timestamp=datetime(2026, 1, 1))


# ---------------------------------------------------------------------------
# ReplayCheckpoint
# ---------------------------------------------------------------------------


class TestReplayCheckpoint:
    def test_creation(self):
        now = datetime(2026, 1, 15, 12, 0)
        c = ReplayCheckpoint(
            replay_id="r1",
            sequence_number=100,
            timestamp=now,
            events_processed=50,
        )
        assert c.replay_id == "r1"
        assert c.sequence_number == 100
        assert c.timestamp == now
        assert c.events_processed == 50

    def test_created_at_default(self):
        c = ReplayCheckpoint(
            replay_id="r2",
            sequence_number=0,
            timestamp=datetime(2026, 1, 1),
            events_processed=0,
        )
        assert c.created_at is not None


# ---------------------------------------------------------------------------
# ReplayProgress
# ---------------------------------------------------------------------------


class TestReplayProgress:
    def _make_progress(self, **overrides):
        now = datetime(2026, 1, 15, 12, 0)
        defaults = {
            "replay_id": "r1",
            "status": ReplayStatus.RUNNING,
            "events_total": 100,
            "events_processed": 50,
            "events_filtered": 5,
            "events_transformed": 3,
            "events_failed": 1,
            "started_at": now,
            "updated_at": now + timedelta(seconds=10),
        }
        defaults.update(overrides)
        return ReplayProgress(**defaults)

    def test_progress_percentage_half(self):
        p = self._make_progress(events_total=100, events_processed=50)
        assert p.progress_percentage == 50.0

    def test_progress_percentage_zero_total(self):
        p = self._make_progress(events_total=0, events_processed=0)
        assert p.progress_percentage == 0.0

    def test_progress_percentage_complete(self):
        p = self._make_progress(events_total=100, events_processed=100)
        assert p.progress_percentage == 100.0

    def test_progress_percentage_partial(self):
        p = self._make_progress(events_total=200, events_processed=75)
        assert p.progress_percentage == 37.5

    def test_events_per_second_pending(self):
        p = self._make_progress(status=ReplayStatus.PENDING)
        assert p.events_per_second == 0.0

    def test_events_per_second_running(self):
        now = datetime(2026, 1, 15, 12, 0)
        p = self._make_progress(
            status=ReplayStatus.RUNNING,
            events_processed=100,
            started_at=now,
            updated_at=now + timedelta(seconds=10),
        )
        assert p.events_per_second == 10.0

    def test_events_per_second_completed(self):
        now = datetime(2026, 1, 15, 12, 0)
        p = self._make_progress(
            status=ReplayStatus.COMPLETED,
            events_processed=200,
            started_at=now,
            updated_at=now + timedelta(seconds=20),
            completed_at=now + timedelta(seconds=20),
        )
        assert p.events_per_second == 10.0

    def test_events_per_second_zero_elapsed(self):
        now = datetime(2026, 1, 15, 12, 0)
        p = self._make_progress(
            status=ReplayStatus.RUNNING,
            events_processed=50,
            started_at=now,
            updated_at=now,
        )
        assert p.events_per_second == 0.0

    def test_optional_fields(self):
        p = self._make_progress()
        assert p.current_sequence is None
        assert p.current_timestamp is None
        assert p.completed_at is None
        assert p.error_message is None
        assert p.last_checkpoint is None

    def test_with_checkpoint(self):
        cp = ReplayCheckpoint(
            replay_id="r1",
            sequence_number=50,
            timestamp=datetime(2026, 1, 15),
            events_processed=25,
        )
        p = self._make_progress(last_checkpoint=cp)
        assert p.last_checkpoint is not None
        assert p.last_checkpoint.sequence_number == 50


# ---------------------------------------------------------------------------
# ReplayVerificationResult
# ---------------------------------------------------------------------------


class TestReplayVerificationResult:
    def test_valid_result(self):
        r = ReplayVerificationResult(
            replay_id="r1",
            verified_at=datetime(2026, 1, 15),
            is_valid=True,
            total_events_verified=100,
        )
        assert r.is_valid is True
        assert r.total_events_verified == 100
        assert r.errors == []
        assert r.warnings == []
        assert r.sequence_gaps == []
        assert r.timestamp_anomalies == []
        assert r.metadata_issues == []

    def test_invalid_result_with_errors(self):
        r = ReplayVerificationResult(
            replay_id="r2",
            verified_at=datetime(2026, 1, 15),
            is_valid=False,
            total_events_verified=0,
            errors=["Replay not found"],
        )
        assert r.is_valid is False
        assert len(r.errors) == 1

    def test_with_warnings(self):
        r = ReplayVerificationResult(
            replay_id="r3",
            verified_at=datetime(2026, 1, 15),
            is_valid=True,
            total_events_verified=50,
            warnings=["3 events failed during replay"],
        )
        assert len(r.warnings) == 1

    def test_with_sequence_gaps(self):
        r = ReplayVerificationResult(
            replay_id="r4",
            verified_at=datetime(2026, 1, 15),
            is_valid=True,
            total_events_verified=100,
            sequence_gaps=[(10, 15), (30, 33)],
        )
        assert len(r.sequence_gaps) == 2
        assert r.sequence_gaps[0] == (10, 15)

    def test_with_timestamp_anomalies(self):
        r = ReplayVerificationResult(
            replay_id="r5",
            verified_at=datetime(2026, 1, 15),
            is_valid=True,
            total_events_verified=100,
            timestamp_anomalies=["Timestamp out of order at event 42"],
        )
        assert len(r.timestamp_anomalies) == 1

    def test_with_metadata_issues(self):
        r = ReplayVerificationResult(
            replay_id="r6",
            verified_at=datetime(2026, 1, 15),
            is_valid=True,
            total_events_verified=100,
            metadata_issues=["Missing correlation_id on event 7"],
        )
        assert len(r.metadata_issues) == 1


# ---------------------------------------------------------------------------
# Combined model interactions
# ---------------------------------------------------------------------------


class TestModelInteractions:
    def test_config_with_all_options(self):
        """Full configuration with all options populated."""
        config = ReplayConfig(
            replay_id="full-test",
            start_timestamp=datetime(2026, 1, 1),
            target=ReplayTargetConfig(
                target_type=ReplayTarget.TIMESTAMP,
                target_timestamp=datetime(2026, 1, 31),
            ),
            speed=ReplaySpeed.FAST,
            filters=ReplayFilterConfig(
                aggregate_types=["schedule"],
                exclude_event_types=[EventType.SCHEDULE_DELETED],
            ),
            transformer=ReplayTransformer(
                field_mappings={"old": "new"},
                metadata_overrides={"user_id": "replay_user"},
            ),
            batch_size=500,
            verify_after_replay=False,
            emit_events=True,
            checkpoint_interval=100,
        )
        assert config.replay_id == "full-test"
        assert config.speed == ReplaySpeed.FAST
        assert config.batch_size == 500
        assert config.verify_after_replay is False
        assert config.emit_events is True
        assert config.filters.aggregate_types == ["schedule"]
        assert config.transformer.field_mappings == {"old": "new"}

    def test_filter_with_multiple_event_types(self):
        f = ReplayFilterConfig(
            event_types=[EventType.SCHEDULE_CREATED, EventType.SCHEDULE_UPDATED],
        )
        assert f.matches(_event(event_type=EventType.SCHEDULE_CREATED.value)) is True
        assert f.matches(_event(event_type=EventType.SCHEDULE_UPDATED.value)) is True
        assert f.matches(_event(event_type=EventType.SCHEDULE_DELETED.value)) is False

    def test_progress_lifecycle(self):
        """Simulate progress through states."""
        now = datetime(2026, 1, 15, 12, 0)

        # Initial pending state
        p = ReplayProgress(
            replay_id="lifecycle",
            status=ReplayStatus.PENDING,
            events_total=0,
            events_processed=0,
            events_filtered=0,
            events_transformed=0,
            events_failed=0,
            started_at=now,
            updated_at=now,
        )
        assert p.progress_percentage == 0.0
        assert p.events_per_second == 0.0

        # Simulate running with events
        p.status = ReplayStatus.RUNNING
        p.events_total = 100
        p.events_processed = 50
        p.updated_at = now + timedelta(seconds=5)
        assert p.progress_percentage == 50.0

        # Complete
        p.status = ReplayStatus.COMPLETED
        p.events_processed = 100
        p.completed_at = now + timedelta(seconds=10)
        p.updated_at = p.completed_at
        assert p.progress_percentage == 100.0
        assert p.events_per_second == 10.0

    def test_verification_result_all_issues(self):
        """Verification with every issue type populated."""
        r = ReplayVerificationResult(
            replay_id="issues",
            verified_at=datetime(2026, 1, 15),
            is_valid=False,
            total_events_verified=50,
            errors=["Status not COMPLETED"],
            warnings=["5 events failed"],
            sequence_gaps=[(10, 15)],
            timestamp_anomalies=["Out of order at 42"],
            metadata_issues=["Missing user_id at 7"],
        )
        assert not r.is_valid
        assert len(r.errors) == 1
        assert len(r.warnings) == 1
        assert len(r.sequence_gaps) == 1
        assert len(r.timestamp_anomalies) == 1
        assert len(r.metadata_issues) == 1
