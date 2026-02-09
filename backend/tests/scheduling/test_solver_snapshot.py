"""Tests for SolverCheckpoint dataclass (pure functions, no Redis required)."""

from datetime import datetime

from app.scheduling.solver_snapshot import SolverCheckpoint


class TestSolverCheckpointConstruction:
    """Test auto-hash generation on construction."""

    def test_auto_generates_hash(self):
        cp = SolverCheckpoint(
            run_id="run-1",
            iteration=100,
            assignments=[("p1", "b1", None)],
            score=0.85,
        )
        assert cp.hash != ""
        assert len(cp.hash) == 16  # SHA-256 truncated to 16 hex chars

    def test_preserves_explicit_hash(self):
        cp = SolverCheckpoint(
            run_id="run-1",
            iteration=100,
            assignments=[],
            score=0.0,
            hash="custom_hash_val!",
        )
        assert cp.hash == "custom_hash_val!"

    def test_default_timestamp(self):
        before = datetime.utcnow()
        cp = SolverCheckpoint(
            run_id="run-1",
            iteration=0,
            assignments=[],
            score=0.0,
        )
        after = datetime.utcnow()
        assert before <= cp.timestamp <= after

    def test_default_violations_count(self):
        cp = SolverCheckpoint(
            run_id="run-1",
            iteration=0,
            assignments=[],
            score=0.0,
        )
        assert cp.violations_count == 0

    def test_default_metadata(self):
        cp = SolverCheckpoint(
            run_id="run-1",
            iteration=0,
            assignments=[],
            score=0.0,
        )
        assert cp.metadata == {}


class TestSolverCheckpointHash:
    """Test hash calculation consistency."""

    def test_same_data_produces_same_hash(self):
        args = {
            "run_id": "run-x",
            "iteration": 50,
            "assignments": [("p1", "b1", "t1"), ("p2", "b2", None)],
            "score": 0.92,
        }
        cp1 = SolverCheckpoint(**args)
        cp2 = SolverCheckpoint(**args)
        assert cp1.hash == cp2.hash

    def test_different_iteration_different_hash(self):
        base = {"run_id": "run-x", "assignments": [], "score": 0.5}
        cp1 = SolverCheckpoint(iteration=1, **base)
        cp2 = SolverCheckpoint(iteration=2, **base)
        assert cp1.hash != cp2.hash

    def test_different_score_different_hash(self):
        base = {"run_id": "run-x", "iteration": 1, "assignments": []}
        cp1 = SolverCheckpoint(score=0.5, **base)
        cp2 = SolverCheckpoint(score=0.9, **base)
        assert cp1.hash != cp2.hash

    def test_different_assignments_different_hash(self):
        base = {"run_id": "run-x", "iteration": 1, "score": 0.5}
        cp1 = SolverCheckpoint(assignments=[("p1", "b1", None)], **base)
        cp2 = SolverCheckpoint(assignments=[("p2", "b2", None)], **base)
        assert cp1.hash != cp2.hash

    def test_assignment_order_does_not_affect_hash(self):
        """Assignments are sorted before hashing, so order doesn't matter."""
        base = {"run_id": "run-x", "iteration": 1, "score": 0.5}
        cp1 = SolverCheckpoint(
            assignments=[("p1", "b1", None), ("p2", "b2", None)], **base
        )
        cp2 = SolverCheckpoint(
            assignments=[("p2", "b2", None), ("p1", "b1", None)], **base
        )
        assert cp1.hash == cp2.hash

    def test_violations_count_does_not_affect_hash(self):
        """violations_count is not part of hash input."""
        base = {
            "run_id": "run-x",
            "iteration": 1,
            "assignments": [],
            "score": 0.5,
        }
        cp1 = SolverCheckpoint(violations_count=0, **base)
        cp2 = SolverCheckpoint(violations_count=10, **base)
        assert cp1.hash == cp2.hash


class TestSolverCheckpointIntegrity:
    """Test verify_integrity method."""

    def test_valid_checkpoint_passes(self):
        cp = SolverCheckpoint(
            run_id="run-1",
            iteration=50,
            assignments=[("p1", "b1", "t1")],
            score=0.88,
        )
        assert cp.verify_integrity() is True

    def test_tampered_hash_fails(self):
        cp = SolverCheckpoint(
            run_id="run-1",
            iteration=50,
            assignments=[("p1", "b1", "t1")],
            score=0.88,
        )
        cp.hash = "tampered_value__"
        assert cp.verify_integrity() is False

    def test_empty_checkpoint_passes(self):
        cp = SolverCheckpoint(
            run_id="run-1",
            iteration=0,
            assignments=[],
            score=0.0,
        )
        assert cp.verify_integrity() is True


class TestSolverCheckpointSerialization:
    """Test to_dict and from_dict round-trip."""

    def test_to_dict_contains_all_fields(self):
        ts = datetime(2025, 6, 15, 12, 0, 0)
        cp = SolverCheckpoint(
            run_id="run-1",
            iteration=100,
            assignments=[("p1", "b1", None)],
            score=0.85,
            violations_count=3,
            timestamp=ts,
            metadata={"algorithm": "cpsat"},
        )
        d = cp.to_dict()
        assert d["run_id"] == "run-1"
        assert d["iteration"] == 100
        assert d["assignments"] == [("p1", "b1", None)]
        assert d["score"] == 0.85
        assert d["violations_count"] == 3
        assert d["timestamp"] == "2025-06-15T12:00:00"
        assert d["metadata"] == {"algorithm": "cpsat"}
        assert d["hash"] == cp.hash

    def test_from_dict_round_trip(self):
        original = SolverCheckpoint(
            run_id="run-abc",
            iteration=200,
            assignments=[("p1", "b1", "t1"), ("p2", "b2", None)],
            score=0.91,
            violations_count=1,
            metadata={"solver": "ortools"},
        )
        data = original.to_dict()
        restored = SolverCheckpoint.from_dict(data)

        assert restored.run_id == original.run_id
        assert restored.iteration == original.iteration
        assert restored.assignments == original.assignments
        assert restored.score == original.score
        assert restored.violations_count == original.violations_count
        assert restored.metadata == original.metadata
        assert restored.hash == original.hash
        assert restored.verify_integrity() is True

    def test_from_dict_defaults(self):
        """from_dict handles missing optional fields gracefully."""
        data = {
            "run_id": "run-min",
            "iteration": 0,
            "assignments": [],
            "score": 0.0,
        }
        cp = SolverCheckpoint.from_dict(data)
        assert cp.violations_count == 0
        assert cp.metadata == {}
        assert cp.timestamp is not None

    def test_from_dict_parses_iso_timestamp(self):
        data = {
            "run_id": "run-1",
            "iteration": 0,
            "assignments": [],
            "score": 0.0,
            "timestamp": "2025-06-15T12:30:00",
        }
        cp = SolverCheckpoint.from_dict(data)
        assert cp.timestamp.year == 2025
        assert cp.timestamp.month == 6
        assert cp.timestamp.hour == 12
        assert cp.timestamp.minute == 30

    def test_from_dict_preserves_hash(self):
        """If hash is provided in dict, from_dict uses it (no recalculation)."""
        data = {
            "run_id": "run-1",
            "iteration": 0,
            "assignments": [],
            "score": 0.0,
            "hash": "preserved_hash__",
        }
        cp = SolverCheckpoint.from_dict(data)
        # from_dict passes hash to constructor; __post_init__ skips recalc when hash exists
        assert cp.hash == "preserved_hash__"
