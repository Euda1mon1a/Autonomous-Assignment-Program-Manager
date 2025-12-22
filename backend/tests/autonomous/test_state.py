"""
Tests for the run state store.
"""

import json
import pytest
import tempfile
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from app.autonomous.state import (
    StateStore,
    RunState,
    GeneratorParams,
    IterationRecord,
)
from app.autonomous.evaluator import EvaluationResult


class TestGeneratorParams:
    """Tests for GeneratorParams dataclass."""

    def test_default_values(self):
        """Test default parameter values."""
        params = GeneratorParams()

        assert params.algorithm == "greedy"
        assert params.timeout_seconds == 60.0
        assert params.random_seed is None
        assert params.max_restarts == 1

    def test_to_dict(self):
        """Test conversion to dictionary."""
        params = GeneratorParams(
            algorithm="cp_sat",
            timeout_seconds=120.0,
            random_seed=42,
        )

        data = params.to_dict()

        assert data["algorithm"] == "cp_sat"
        assert data["timeout_seconds"] == 120.0
        assert data["random_seed"] == 42

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "algorithm": "hybrid",
            "timeout_seconds": 90.0,
            "diversification_factor": 0.5,
        }

        params = GeneratorParams.from_dict(data)

        assert params.algorithm == "hybrid"
        assert params.timeout_seconds == 90.0
        assert params.diversification_factor == 0.5

    def test_from_dict_ignores_unknown_keys(self):
        """Test that unknown keys are ignored."""
        data = {
            "algorithm": "greedy",
            "unknown_key": "value",
        }

        params = GeneratorParams.from_dict(data)

        assert params.algorithm == "greedy"
        assert not hasattr(params, "unknown_key")


class TestIterationRecord:
    """Tests for IterationRecord dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        record = IterationRecord(
            iteration=5,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            params=GeneratorParams(algorithm="cp_sat"),
            score=0.85,
            valid=True,
            critical_violations=0,
            total_violations=2,
            violation_types=["N1_VULNERABILITY"],
            duration_seconds=45.5,
        )

        data = record.to_dict()

        assert data["iteration"] == 5
        assert data["score"] == 0.85
        assert data["valid"] is True
        assert data["params"]["algorithm"] == "cp_sat"
        assert "N1_VULNERABILITY" in data["violation_types"]

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "iteration": 10,
            "timestamp": "2025-01-01T12:00:00",
            "params": {"algorithm": "greedy"},
            "score": 0.75,
            "valid": False,
            "critical_violations": 1,
            "total_violations": 3,
            "violation_types": ["80_HOUR_VIOLATION"],
            "duration_seconds": 30.0,
        }

        record = IterationRecord.from_dict(data)

        assert record.iteration == 10
        assert record.score == 0.75
        assert record.valid is False
        assert record.params.algorithm == "greedy"

    def test_to_ndjson_line(self):
        """Test NDJSON line format."""
        record = IterationRecord(
            iteration=1,
            timestamp=datetime(2025, 1, 1),
            params=GeneratorParams(),
            score=0.5,
            valid=False,
            critical_violations=1,
            total_violations=1,
            violation_types=[],
            duration_seconds=10.0,
        )

        line = record.to_ndjson_line()

        # Should be valid JSON without trailing newline
        assert not line.endswith("\n")
        data = json.loads(line)
        assert data["iteration"] == 1


class TestRunState:
    """Tests for RunState dataclass."""

    def test_update_with_result_improves(self):
        """Test state update when score improves."""
        state = RunState(
            run_id="test_run",
            scenario="baseline",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            best_score=0.5,
        )

        result = EvaluationResult(
            valid=True,
            score=0.8,  # Improvement
            hard_constraint_pass=True,
            soft_score=0.4,
            coverage_rate=0.9,
            total_violations=0,
            critical_violations=0,
        )

        state.update_with_result(result, GeneratorParams())

        assert state.current_iteration == 1
        assert state.best_score == 0.8
        assert state.best_iteration == 1
        assert state.iterations_since_improvement == 0

    def test_update_with_result_no_improvement(self):
        """Test state update when score doesn't improve."""
        state = RunState(
            run_id="test_run",
            scenario="baseline",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            best_score=0.9,
            best_iteration=5,
        )

        result = EvaluationResult(
            valid=True,
            score=0.7,  # No improvement
            hard_constraint_pass=True,
            soft_score=0.3,
            coverage_rate=0.8,
            total_violations=0,
            critical_violations=0,
        )

        state.update_with_result(result, GeneratorParams())

        assert state.best_score == 0.9  # Unchanged
        assert state.best_iteration == 5  # Unchanged
        assert state.iterations_since_improvement == 1

    def test_should_stop_target_reached(self):
        """Test stopping when target is reached."""
        state = RunState(
            run_id="test_run",
            scenario="baseline",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            best_score=0.96,
            target_score=0.95,
        )

        should_stop, reason = state.should_stop()

        assert should_stop is True
        assert reason == "target_reached"

    def test_should_stop_max_iterations(self):
        """Test stopping at max iterations."""
        state = RunState(
            run_id="test_run",
            scenario="baseline",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            current_iteration=200,
            max_iterations=200,
        )

        should_stop, reason = state.should_stop()

        assert should_stop is True
        assert reason == "max_iterations"

    def test_should_stop_stagnation(self):
        """Test stopping on stagnation."""
        state = RunState(
            run_id="test_run",
            scenario="baseline",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            iterations_since_improvement=25,
            stagnation_limit=20,
        )

        should_stop, reason = state.should_stop()

        assert should_stop is True
        assert reason == "stagnation"

    def test_should_stop_running(self):
        """Test that loop should continue when no stop condition met."""
        state = RunState(
            run_id="test_run",
            scenario="baseline",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            current_iteration=50,
            max_iterations=200,
            best_score=0.7,
            target_score=0.95,
            iterations_since_improvement=5,
            stagnation_limit=20,
        )

        should_stop, reason = state.should_stop()

        assert should_stop is False
        assert reason == ""


class TestStateStore:
    """Tests for StateStore persistence."""

    def test_create_run(self, tmp_path):
        """Test creating a new run."""
        store = StateStore(base_path=tmp_path)

        state = store.create_run(
            scenario="baseline",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            max_iterations=100,
        )

        assert state.run_id.startswith("baseline_")
        assert state.scenario == "baseline"
        assert state.max_iterations == 100
        assert (tmp_path / state.run_id / "state.json").exists()
        assert (tmp_path / state.run_id / "history.ndjson").exists()

    def test_save_and_load_run(self, tmp_path):
        """Test saving and loading run state."""
        store = StateStore(base_path=tmp_path)

        # Create and modify state
        state = store.create_run(
            scenario="test",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )
        state.best_score = 0.85
        state.current_iteration = 10
        store.save_state(state)

        # Load and verify
        loaded = store.load_run(state.run_id)

        assert loaded is not None
        assert loaded.run_id == state.run_id
        assert loaded.best_score == 0.85
        assert loaded.current_iteration == 10

    def test_append_iteration(self, tmp_path):
        """Test appending iteration records."""
        store = StateStore(base_path=tmp_path)
        state = store.create_run(
            scenario="test",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )

        # Append records
        for i in range(3):
            record = IterationRecord(
                iteration=i,
                timestamp=datetime.now(),
                params=GeneratorParams(),
                score=0.5 + i * 0.1,
                valid=True,
                critical_violations=0,
                total_violations=0,
                violation_types=[],
                duration_seconds=10.0,
            )
            store.append_iteration(state, record)

        # Load and verify
        history = store.load_history(state.run_id)

        assert len(history) == 3
        assert history[0].iteration == 0
        assert history[2].iteration == 2
        assert history[2].score == 0.7

    def test_list_runs(self, tmp_path):
        """Test listing runs."""
        store = StateStore(base_path=tmp_path)

        # Create multiple runs
        store.create_run("baseline", date(2025, 1, 1), date(2025, 3, 31))
        store.create_run("baseline", date(2025, 1, 1), date(2025, 3, 31))
        store.create_run("n1_test", date(2025, 1, 1), date(2025, 3, 31))

        # List all
        all_runs = store.list_runs()
        assert len(all_runs) == 3

        # Filter by scenario
        baseline_runs = store.list_runs(scenario="baseline")
        assert len(baseline_runs) == 2

    def test_get_best_from_history(self, tmp_path):
        """Test getting best iteration from history."""
        store = StateStore(base_path=tmp_path)
        state = store.create_run(
            scenario="test",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )

        # Add iterations with varying scores
        scores = [0.5, 0.7, 0.6, 0.8, 0.75]
        for i, score in enumerate(scores):
            record = IterationRecord(
                iteration=i,
                timestamp=datetime.now(),
                params=GeneratorParams(),
                score=score,
                valid=True,
                critical_violations=0,
                total_violations=0,
                violation_types=[],
                duration_seconds=10.0,
            )
            store.append_iteration(state, record)

        best = store.get_best_from_history(state.run_id)

        assert best is not None
        assert best.iteration == 3  # Index of 0.8
        assert best.score == 0.8

    def test_log(self, tmp_path):
        """Test logging to run.log."""
        store = StateStore(base_path=tmp_path)
        state = store.create_run(
            scenario="test",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )

        store.log(state, "Test message 1")
        store.log(state, "Test message 2")

        log_path = tmp_path / state.run_id / "run.log"
        log_content = log_path.read_text()

        assert "Test message 1" in log_content
        assert "Test message 2" in log_content
