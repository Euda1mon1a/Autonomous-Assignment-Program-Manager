"""Tests for pure functions in explainability module (no DB, no ORM)."""

import hashlib
import json
from datetime import datetime
from uuid import UUID, uuid4

from app.scheduling.explainability import compute_audit_hash


class TestComputeAuditHash:
    """Tests for the compute_audit_hash standalone function."""

    def test_returns_hex_string(self):
        result = compute_audit_hash(
            person_id=uuid4(),
            block_id=uuid4(),
            template_id=uuid4(),
            score=95.5,
            algorithm="greedy",
            timestamp=datetime(2026, 1, 15, 10, 30, 0),
        )
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest

    def test_deterministic(self):
        """Same inputs produce the same hash."""
        pid = uuid4()
        bid = uuid4()
        tid = uuid4()
        ts = datetime(2026, 1, 15, 10, 30, 0)

        hash1 = compute_audit_hash(pid, bid, tid, 95.5, "greedy", ts)
        hash2 = compute_audit_hash(pid, bid, tid, 95.5, "greedy", ts)
        assert hash1 == hash2

    def test_different_person_different_hash(self):
        bid = uuid4()
        tid = uuid4()
        ts = datetime(2026, 1, 15, 10, 30, 0)

        hash1 = compute_audit_hash(uuid4(), bid, tid, 95.5, "greedy", ts)
        hash2 = compute_audit_hash(uuid4(), bid, tid, 95.5, "greedy", ts)
        assert hash1 != hash2

    def test_different_block_different_hash(self):
        pid = uuid4()
        tid = uuid4()
        ts = datetime(2026, 1, 15, 10, 30, 0)

        hash1 = compute_audit_hash(pid, uuid4(), tid, 95.5, "greedy", ts)
        hash2 = compute_audit_hash(pid, uuid4(), tid, 95.5, "greedy", ts)
        assert hash1 != hash2

    def test_different_score_different_hash(self):
        pid = uuid4()
        bid = uuid4()
        tid = uuid4()
        ts = datetime(2026, 1, 15, 10, 30, 0)

        hash1 = compute_audit_hash(pid, bid, tid, 95.5, "greedy", ts)
        hash2 = compute_audit_hash(pid, bid, tid, 80.0, "greedy", ts)
        assert hash1 != hash2

    def test_different_algorithm_different_hash(self):
        pid = uuid4()
        bid = uuid4()
        tid = uuid4()
        ts = datetime(2026, 1, 15, 10, 30, 0)

        hash1 = compute_audit_hash(pid, bid, tid, 95.5, "greedy", ts)
        hash2 = compute_audit_hash(pid, bid, tid, 95.5, "cpsat", ts)
        assert hash1 != hash2

    def test_different_timestamp_different_hash(self):
        pid = uuid4()
        bid = uuid4()
        tid = uuid4()

        hash1 = compute_audit_hash(
            pid, bid, tid, 95.5, "greedy", datetime(2026, 1, 15, 10, 0)
        )
        hash2 = compute_audit_hash(
            pid, bid, tid, 95.5, "greedy", datetime(2026, 1, 15, 11, 0)
        )
        assert hash1 != hash2

    def test_none_template_id(self):
        """template_id=None should produce a valid hash."""
        result = compute_audit_hash(
            person_id=uuid4(),
            block_id=uuid4(),
            template_id=None,
            score=95.5,
            algorithm="greedy",
            timestamp=datetime(2026, 1, 15, 10, 30, 0),
        )
        assert isinstance(result, str)
        assert len(result) == 64

    def test_none_template_differs_from_some_template(self):
        pid = uuid4()
        bid = uuid4()
        ts = datetime(2026, 1, 15, 10, 30, 0)

        hash_none = compute_audit_hash(pid, bid, None, 95.5, "greedy", ts)
        hash_some = compute_audit_hash(pid, bid, uuid4(), 95.5, "greedy", ts)
        assert hash_none != hash_some

    def test_matches_manual_sha256(self):
        """Verify the hash matches a manually constructed SHA-256."""
        pid = UUID("550e8400-e29b-41d4-a716-446655440000")
        bid = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        tid = UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")
        ts = datetime(2026, 1, 15, 10, 30, 0)

        result = compute_audit_hash(pid, bid, tid, 100.0, "greedy", ts)

        # Manually construct expected hash
        data = {
            "person_id": str(pid),
            "block_id": str(bid),
            "template_id": str(tid),
            "score": 100.0,
            "algorithm": "greedy",
            "timestamp": ts.isoformat(),
        }
        expected = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        assert result == expected

    def test_zero_score(self):
        result = compute_audit_hash(
            person_id=uuid4(),
            block_id=uuid4(),
            template_id=uuid4(),
            score=0.0,
            algorithm="greedy",
            timestamp=datetime(2026, 1, 15, 10, 30, 0),
        )
        assert isinstance(result, str)
        assert len(result) == 64

    def test_negative_score(self):
        result = compute_audit_hash(
            person_id=uuid4(),
            block_id=uuid4(),
            template_id=uuid4(),
            score=-10.5,
            algorithm="greedy",
            timestamp=datetime(2026, 1, 15, 10, 30, 0),
        )
        assert isinstance(result, str)
        assert len(result) == 64
