"""Tests for DiffThresholds and DiffResult dataclasses (pure, no DB)."""

from uuid import UUID

import pytest

from app.scheduling.diff_guard import DiffResult, DiffStatus, DiffThresholds


class TestDiffStatus:
    """Test DiffStatus enum values."""

    def test_pass_value(self):
        assert DiffStatus.PASS.value == "pass"

    def test_warn_value(self):
        assert DiffStatus.WARN.value == "warn"

    def test_reject_value(self):
        assert DiffStatus.REJECT.value == "reject"


class TestDiffThresholds:
    """Test DiffThresholds validation."""

    def test_defaults(self):
        t = DiffThresholds()
        assert t.global_max_churn == 0.20
        assert t.person_max_churn == 0.50
        assert t.person_warn_churn == 0.30
        assert t.min_rigidity == 0.80
        assert t.affected_people_warn == 10

    def test_custom_values(self):
        t = DiffThresholds(global_max_churn=0.10, person_max_churn=0.40)
        assert t.global_max_churn == 0.10
        assert t.person_max_churn == 0.40

    def test_boundary_zero(self):
        t = DiffThresholds(global_max_churn=0.0)
        assert t.global_max_churn == 0.0

    def test_boundary_one(self):
        t = DiffThresholds(global_max_churn=1.0)
        assert t.global_max_churn == 1.0

    def test_rejects_global_churn_above_one(self):
        with pytest.raises(ValueError, match="global_max_churn"):
            DiffThresholds(global_max_churn=1.01)

    def test_rejects_global_churn_below_zero(self):
        with pytest.raises(ValueError, match="global_max_churn"):
            DiffThresholds(global_max_churn=-0.01)

    def test_rejects_person_max_churn_above_one(self):
        with pytest.raises(ValueError, match="person_max_churn"):
            DiffThresholds(person_max_churn=1.5)

    def test_rejects_person_warn_churn_above_one(self):
        with pytest.raises(ValueError, match="person_warn_churn"):
            DiffThresholds(person_warn_churn=2.0)

    def test_rejects_min_rigidity_above_one(self):
        with pytest.raises(ValueError, match="min_rigidity"):
            DiffThresholds(min_rigidity=1.1)

    def test_rejects_negative_affected_people(self):
        with pytest.raises(ValueError, match="affected_people_warn"):
            DiffThresholds(affected_people_warn=-1)

    def test_zero_affected_people_ok(self):
        t = DiffThresholds(affected_people_warn=0)
        assert t.affected_people_warn == 0


class TestDiffResult:
    """Test DiffResult helper methods."""

    def test_pass_is_acceptable(self):
        result = DiffResult(status=DiffStatus.PASS)
        assert result.is_acceptable() is True

    def test_warn_is_acceptable(self):
        result = DiffResult(status=DiffStatus.WARN)
        assert result.is_acceptable() is True

    def test_reject_is_not_acceptable(self):
        result = DiffResult(status=DiffStatus.REJECT, reason="Too much churn")
        assert result.is_acceptable() is False

    def test_to_dict_basic(self):
        result = DiffResult(status=DiffStatus.PASS)
        d = result.to_dict()
        assert d["status"] == "pass"
        assert d["reason"] is None
        assert d["warnings"] == []
        assert d["metrics"] == {}
        assert d["affected_person_count"] == 0
        assert d["high_churn_person_count"] == 0
        assert "timestamp" in d

    def test_to_dict_with_details(self):
        person_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        result = DiffResult(
            status=DiffStatus.WARN,
            warnings=["High churn detected"],
            metrics={"global_churn_rate": 0.15},
            affected_persons={person_id},
            high_churn_persons={person_id: 0.35},
        )
        d = result.to_dict()
        assert d["status"] == "warn"
        assert d["affected_person_count"] == 1
        assert d["high_churn_person_count"] == 1
        assert d["warnings"] == ["High churn detected"]
        assert d["metrics"]["global_churn_rate"] == 0.15

    def test_to_dict_reject_with_reason(self):
        result = DiffResult(
            status=DiffStatus.REJECT,
            reason="Global churn 25% exceeds maximum 20%",
        )
        d = result.to_dict()
        assert d["status"] == "reject"
        assert "25%" in d["reason"]

    def test_default_warnings_empty(self):
        result = DiffResult(status=DiffStatus.PASS)
        assert result.warnings == []

    def test_default_affected_persons_empty(self):
        result = DiffResult(status=DiffStatus.PASS)
        assert result.affected_persons == set()

    def test_default_high_churn_persons_empty(self):
        result = DiffResult(status=DiffStatus.PASS)
        assert result.high_churn_persons == {}
