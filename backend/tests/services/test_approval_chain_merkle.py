"""Tests for ApprovalChainService Merkle root computation.

Tests the pure cryptographic algorithm without database fixtures.
The _compute_merkle_root method implements a binary Merkle tree used
for daily seal verification in the tamper-evident audit trail.
"""

import hashlib
from unittest.mock import MagicMock

from app.services.approval_chain_service import ApprovalChainService


def _sha256(data: str) -> str:
    """Helper to compute SHA-256 hash."""
    return hashlib.sha256(data.encode()).hexdigest()


def _empty_hash() -> str:
    """The hash of empty bytes, used for padding."""
    return hashlib.sha256(b"").hexdigest()


def _make_service() -> ApprovalChainService:
    """Create service with mock DB (not used for Merkle computation)."""
    mock_db = MagicMock()
    return ApprovalChainService(mock_db)


class TestComputeMerkleRoot:
    """Tests for the binary Merkle tree implementation."""

    def test_empty_list_returns_empty_hash(self):
        """Empty input returns hash of empty bytes."""
        service = _make_service()
        result = service._compute_merkle_root([])
        assert result == _empty_hash()

    def test_single_hash(self):
        """Single hash is a power of 2 (1), so returned as-is."""
        service = _make_service()
        h1 = "abc123"
        # 1 is a power of 2 (1 & 0 = 0), so no padding
        # len == 1, so while loop doesn't run - returns h1 directly
        result = service._compute_merkle_root([h1])
        assert result == h1

    def test_two_hashes(self):
        """Two hashes combined directly (already power of 2)."""
        service = _make_service()
        h1 = "hash_one"
        h2 = "hash_two"
        expected = _sha256(h1 + h2)
        result = service._compute_merkle_root([h1, h2])
        assert result == expected

    def test_four_hashes(self):
        """Four hashes form a complete binary tree."""
        service = _make_service()
        h1, h2, h3, h4 = "a", "b", "c", "d"
        # Level 1: combine pairs
        left = _sha256(h1 + h2)
        right = _sha256(h3 + h4)
        # Level 0: combine roots
        expected = _sha256(left + right)
        result = service._compute_merkle_root([h1, h2, h3, h4])
        assert result == expected

    def test_three_hashes_padded_to_four(self):
        """Three hashes padded to 4 with empty hash."""
        service = _make_service()
        h1, h2, h3 = "x", "y", "z"
        pad = _empty_hash()
        # Padded to [h1, h2, h3, pad]
        left = _sha256(h1 + h2)
        right = _sha256(h3 + pad)
        expected = _sha256(left + right)
        result = service._compute_merkle_root([h1, h2, h3])
        assert result == expected

    def test_five_hashes_padded_to_eight(self):
        """Five hashes padded to 8 (next power of 2)."""
        service = _make_service()
        hashes = ["h1", "h2", "h3", "h4", "h5"]
        pad = _empty_hash()
        # Padded to [h1, h2, h3, h4, h5, pad, pad, pad]
        padded = hashes + [pad, pad, pad]
        # Level 2: 4 pairs
        l2 = [_sha256(padded[i] + padded[i + 1]) for i in range(0, 8, 2)]
        # Level 1: 2 pairs
        l1 = [_sha256(l2[i] + l2[i + 1]) for i in range(0, 4, 2)]
        # Level 0: root
        expected = _sha256(l1[0] + l1[1])
        result = service._compute_merkle_root(hashes)
        assert result == expected

    def test_deterministic(self):
        """Same input always produces same output."""
        service = _make_service()
        hashes = ["alpha", "beta", "gamma", "delta"]
        result1 = service._compute_merkle_root(hashes.copy())
        result2 = service._compute_merkle_root(hashes.copy())
        assert result1 == result2

    def test_order_sensitive(self):
        """Different order produces different root."""
        service = _make_service()
        result_ab = service._compute_merkle_root(["a", "b"])
        result_ba = service._compute_merkle_root(["b", "a"])
        assert result_ab != result_ba

    def test_realistic_sha256_hashes(self):
        """Works with actual SHA-256 hash strings."""
        service = _make_service()
        hashes = [hashlib.sha256(f"record_{i}".encode()).hexdigest() for i in range(4)]
        result = service._compute_merkle_root(hashes)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex length

    def test_large_input(self):
        """Handles larger inputs (16 hashes)."""
        service = _make_service()
        hashes = [f"hash_{i:03d}" for i in range(16)]
        result = service._compute_merkle_root(hashes)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_power_of_two_no_padding(self):
        """Power-of-2 inputs need no padding."""
        service = _make_service()
        # 8 is power of 2
        hashes = [f"h{i}" for i in range(8)]
        result = service._compute_merkle_root(hashes)
        assert isinstance(result, str)

    def test_tampering_changes_root(self):
        """Modifying any hash changes the Merkle root."""
        service = _make_service()
        original = ["record_a", "record_b", "record_c", "record_d"]
        original_root = service._compute_merkle_root(original.copy())

        # Tamper with one record
        tampered = original.copy()
        tampered[2] = "tampered_c"
        tampered_root = service._compute_merkle_root(tampered)

        assert original_root != tampered_root

    def test_insertion_changes_root(self):
        """Adding a record changes the Merkle root."""
        service = _make_service()
        base = ["a", "b", "c", "d"]
        base_root = service._compute_merkle_root(base.copy())

        extended = base + ["e"]
        extended_root = service._compute_merkle_root(extended)

        assert base_root != extended_root


class TestChainVerificationResult:
    """Tests for the ChainVerificationResult dataclass."""

    from app.services.approval_chain_service import ChainVerificationResult

    def test_valid_result(self):
        result = self.ChainVerificationResult(
            valid=True,
            chain_id="global",
            total_records=10,
            verified_count=10,
            head_hash="abc123",
            genesis_hash="xyz789",
        )
        assert result.valid is True
        assert result.first_invalid_seq is None

    def test_invalid_result(self):
        result = self.ChainVerificationResult(
            valid=False,
            chain_id="global",
            total_records=10,
            verified_count=5,
            first_invalid_seq=5,
            first_invalid_id="record-5",
            error_message="Hash mismatch",
        )
        assert result.valid is False
        assert result.first_invalid_seq == 5


class TestChainStats:
    """Tests for the ChainStats dataclass."""

    from app.services.approval_chain_service import ChainStats

    def test_chain_stats_creation(self):
        stats = self.ChainStats(
            chain_id="global",
            total_records=100,
            head_sequence=99,
            head_hash="head_hash",
            genesis_hash="genesis_hash",
            first_record_at=None,
            last_record_at=None,
            actions_by_type={"schedule_approved": 50, "assignment_modified": 50},
        )
        assert stats.total_records == 100
        assert stats.actions_by_type["schedule_approved"] == 50
