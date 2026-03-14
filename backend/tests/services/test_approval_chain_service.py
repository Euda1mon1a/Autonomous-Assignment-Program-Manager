"""Tests for ApprovalChainService and ApprovalRecord pure functions.

Tests the cryptographic hash chain, Merkle tree, genesis record creation,
and hash verification without requiring database access.
"""

import hashlib
import uuid
from datetime import datetime

import pytest

from app.models.approval_record import ApprovalAction, ApprovalRecord
from app.services.approval_chain_service import (
    DEFAULT_CHAIN_ID,
    ApprovalChainService,
    ChainStats,
    ChainVerificationResult,
)


# ============================================================================
# ApprovalRecord.compute_hash
# ============================================================================


class TestComputeHash:
    """Tests for the SHA-256 hash computation."""

    def test_returns_64_char_hex(self):
        h = ApprovalRecord.compute_hash(
            prev_hash=None,
            payload={"test": True},
            actor_id=None,
            actor_type="system",
            action="GENESIS",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_deterministic(self):
        args = {
            "prev_hash": "abc123",
            "payload": {"key": "value"},
            "actor_id": uuid.UUID("12345678-1234-1234-1234-123456789012"),
            "actor_type": "human",
            "action": "SCHEDULE_APPROVED",
            "timestamp": datetime(2025, 6, 15, 10, 30, 0),
            "reason": "Looks good",
        }
        h1 = ApprovalRecord.compute_hash(**args)
        h2 = ApprovalRecord.compute_hash(**args)
        assert h1 == h2

    def test_different_payloads_yield_different_hashes(self):
        base = {
            "prev_hash": None,
            "actor_id": None,
            "actor_type": "system",
            "action": "GENESIS",
            "timestamp": datetime(2025, 1, 1),
        }
        h1 = ApprovalRecord.compute_hash(payload={"a": 1}, **base)
        h2 = ApprovalRecord.compute_hash(payload={"a": 2}, **base)
        assert h1 != h2

    def test_different_actors_yield_different_hashes(self):
        base = {
            "prev_hash": None,
            "payload": {"test": True},
            "actor_type": "human",
            "action": "SCHEDULE_APPROVED",
            "timestamp": datetime(2025, 1, 1),
        }
        id1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
        id2 = uuid.UUID("22222222-2222-2222-2222-222222222222")
        h1 = ApprovalRecord.compute_hash(actor_id=id1, **base)
        h2 = ApprovalRecord.compute_hash(actor_id=id2, **base)
        assert h1 != h2

    def test_different_actions_yield_different_hashes(self):
        base = {
            "prev_hash": None,
            "payload": {},
            "actor_id": None,
            "actor_type": "system",
            "timestamp": datetime(2025, 1, 1),
        }
        h1 = ApprovalRecord.compute_hash(action="GENESIS", **base)
        h2 = ApprovalRecord.compute_hash(action="DAY_SEALED", **base)
        assert h1 != h2

    def test_different_timestamps_yield_different_hashes(self):
        base = {
            "prev_hash": None,
            "payload": {},
            "actor_id": None,
            "actor_type": "system",
            "action": "GENESIS",
        }
        h1 = ApprovalRecord.compute_hash(timestamp=datetime(2025, 1, 1), **base)
        h2 = ApprovalRecord.compute_hash(timestamp=datetime(2025, 1, 2), **base)
        assert h1 != h2

    def test_none_prev_hash_uses_genesis_sentinel(self):
        """When prev_hash is None, 'GENESIS' sentinel is used."""
        h = ApprovalRecord.compute_hash(
            prev_hash=None,
            payload={},
            actor_id=None,
            actor_type="system",
            action="GENESIS",
            timestamp=datetime(2025, 1, 1),
        )
        # Should match manual computation with "GENESIS" sentinel
        import json

        data = {
            "prev_hash": "GENESIS",
            "payload": {},
            "actor_id": None,
            "actor_type": "system",
            "action": "GENESIS",
            "timestamp": "2025-01-01T00:00:00",
            "reason": None,
        }
        expected = hashlib.sha256(
            json.dumps(data, sort_keys=True, default=str).encode()
        ).hexdigest()
        assert h == expected

    def test_reason_included_in_hash(self):
        base = {
            "prev_hash": None,
            "payload": {},
            "actor_id": None,
            "actor_type": "system",
            "action": "GENESIS",
            "timestamp": datetime(2025, 1, 1),
        }
        h1 = ApprovalRecord.compute_hash(reason=None, **base)
        h2 = ApprovalRecord.compute_hash(reason="Override needed", **base)
        assert h1 != h2

    def test_prev_hash_chain_linking(self):
        """Changing prev_hash changes the record hash (chain integrity)."""
        base = {
            "payload": {},
            "actor_id": None,
            "actor_type": "system",
            "action": "SCHEDULE_APPROVED",
            "timestamp": datetime(2025, 1, 1),
        }
        h1 = ApprovalRecord.compute_hash(prev_hash="aaa", **base)
        h2 = ApprovalRecord.compute_hash(prev_hash="bbb", **base)
        assert h1 != h2


# ============================================================================
# ApprovalRecord.create_genesis
# ============================================================================


class TestCreateGenesis:
    """Tests for genesis record creation."""

    def test_creates_record_with_seq_zero(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test-chain")
        assert genesis.sequence_num == 0

    def test_no_prev_hash(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test-chain")
        assert genesis.prev_hash is None

    def test_no_prev_record_id(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test-chain")
        assert genesis.prev_record_id is None

    def test_action_is_genesis(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test-chain")
        assert genesis.action == "GENESIS"

    def test_actor_type_is_system(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test-chain")
        assert genesis.actor_type == "system"

    def test_chain_id_set(self):
        genesis = ApprovalRecord.create_genesis(chain_id="my-chain")
        assert genesis.chain_id == "my-chain"

    def test_default_payload(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test")
        assert genesis.payload == {"chain_initialized": True}

    def test_custom_payload(self):
        genesis = ApprovalRecord.create_genesis(
            chain_id="test", payload={"custom": "data"}
        )
        assert genesis.payload == {"custom": "data"}

    def test_custom_reason(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test", reason="Manual init")
        assert genesis.reason == "Manual init"

    def test_has_valid_uuid_id(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test")
        assert isinstance(genesis.id, uuid.UUID)

    def test_has_record_hash(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test")
        assert genesis.record_hash is not None
        assert len(genesis.record_hash) == 64

    def test_has_created_at_timestamp(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test")
        assert isinstance(genesis.created_at, datetime)

    def test_actor_id_propagated(self):
        actor = uuid.uuid4()
        genesis = ApprovalRecord.create_genesis(chain_id="test", actor_id=actor)
        assert genesis.actor_id == actor


# ============================================================================
# ApprovalRecord.verify_hash
# ============================================================================


class TestVerifyHash:
    """Tests for hash verification on records."""

    def test_genesis_verifies(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test")
        assert genesis.verify_hash() is True

    def test_tampered_payload_fails_verification(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test")
        genesis.payload = {"tampered": True}
        assert genesis.verify_hash() is False

    def test_tampered_action_fails_verification(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test")
        genesis.action = "SCHEDULE_APPROVED"
        assert genesis.verify_hash() is False

    def test_tampered_reason_fails_verification(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test")
        genesis.reason = "Tampered reason"
        assert genesis.verify_hash() is False

    def test_tampered_actor_type_fails_verification(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test")
        genesis.actor_type = "human"
        assert genesis.verify_hash() is False

    def test_tampered_hash_detectable(self):
        genesis = ApprovalRecord.create_genesis(chain_id="test")
        genesis.record_hash = "0" * 64
        assert genesis.verify_hash() is False


# ============================================================================
# _compute_merkle_root
# ============================================================================


class TestComputeMerkleRoot:
    """Tests for Merkle tree computation."""

    @pytest.fixture
    def service(self):
        """Create service without DB (only testing _compute_merkle_root)."""
        # Pass None for DB since we only test the static method
        return ApprovalChainService.__new__(ApprovalChainService)

    def test_empty_list_returns_hash_of_empty(self, service):
        result = service._compute_merkle_root([])
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected

    def test_single_hash(self, service):
        h = hashlib.sha256(b"test").hexdigest()
        result = service._compute_merkle_root([h])
        # Single hash: 1 is a power of 2, no padding needed, returned directly
        assert result == h

    def test_two_hashes(self, service):
        h1 = hashlib.sha256(b"first").hexdigest()
        h2 = hashlib.sha256(b"second").hexdigest()
        result = service._compute_merkle_root([h1, h2])
        expected = hashlib.sha256((h1 + h2).encode()).hexdigest()
        assert result == expected

    def test_four_hashes(self, service):
        hashes = [hashlib.sha256(f"item{i}".encode()).hexdigest() for i in range(4)]
        result = service._compute_merkle_root(hashes)

        # Level 1: combine pairs
        l1_0 = hashlib.sha256((hashes[0] + hashes[1]).encode()).hexdigest()
        l1_1 = hashlib.sha256((hashes[2] + hashes[3]).encode()).hexdigest()
        # Root: combine level 1
        expected = hashlib.sha256((l1_0 + l1_1).encode()).hexdigest()
        assert result == expected

    def test_three_hashes_pads_to_four(self, service):
        hashes = [hashlib.sha256(f"item{i}".encode()).hexdigest() for i in range(3)]
        result = service._compute_merkle_root(hashes)

        # Padded with empty hash to make power of 2
        empty_hash = hashlib.sha256(b"").hexdigest()
        padded = hashes + [empty_hash]

        l1_0 = hashlib.sha256((padded[0] + padded[1]).encode()).hexdigest()
        l1_1 = hashlib.sha256((padded[2] + padded[3]).encode()).hexdigest()
        expected = hashlib.sha256((l1_0 + l1_1).encode()).hexdigest()
        assert result == expected

    def test_deterministic(self, service):
        hashes = [hashlib.sha256(f"item{i}".encode()).hexdigest() for i in range(5)]
        r1 = service._compute_merkle_root(list(hashes))
        r2 = service._compute_merkle_root(list(hashes))
        assert r1 == r2

    def test_order_matters(self, service):
        h1 = hashlib.sha256(b"a").hexdigest()
        h2 = hashlib.sha256(b"b").hexdigest()
        r1 = service._compute_merkle_root([h1, h2])
        r2 = service._compute_merkle_root([h2, h1])
        assert r1 != r2


# ============================================================================
# Chain linking (multi-record hash chain without DB)
# ============================================================================


class TestChainLinking:
    """Test that records can be chained together with hash linking."""

    def test_chain_of_three_records(self):
        """Build a 3-record chain and verify each link."""
        # Genesis
        genesis = ApprovalRecord.create_genesis(chain_id="test")
        assert genesis.verify_hash()

        # Record 1: linked to genesis
        ts1 = datetime(2025, 6, 1, 10, 0, 0)
        hash1 = ApprovalRecord.compute_hash(
            prev_hash=genesis.record_hash,
            payload={"change": "first"},
            actor_id=None,
            actor_type="human",
            action="ASSIGNMENT_CREATED",
            timestamp=ts1,
        )
        rec1 = ApprovalRecord(
            id=uuid.uuid4(),
            chain_id="test",
            sequence_num=1,
            prev_record_id=genesis.id,
            prev_hash=genesis.record_hash,
            record_hash=hash1,
            action="ASSIGNMENT_CREATED",
            payload={"change": "first"},
            actor_type="human",
            created_at=ts1,
        )
        assert rec1.verify_hash()

        # Record 2: linked to record 1
        ts2 = datetime(2025, 6, 1, 11, 0, 0)
        hash2 = ApprovalRecord.compute_hash(
            prev_hash=rec1.record_hash,
            payload={"change": "second"},
            actor_id=None,
            actor_type="system",
            action="SCHEDULE_APPROVED",
            timestamp=ts2,
        )
        rec2 = ApprovalRecord(
            id=uuid.uuid4(),
            chain_id="test",
            sequence_num=2,
            prev_record_id=rec1.id,
            prev_hash=rec1.record_hash,
            record_hash=hash2,
            action="SCHEDULE_APPROVED",
            payload={"change": "second"},
            actor_type="system",
            created_at=ts2,
        )
        assert rec2.verify_hash()

    def test_tampering_breaks_chain(self):
        """Modifying a record makes its hash invalid."""
        genesis = ApprovalRecord.create_genesis(chain_id="test")
        assert genesis.verify_hash()

        # Tamper with genesis
        genesis.payload = {"hacked": True}
        assert not genesis.verify_hash()


# ============================================================================
# Dataclasses
# ============================================================================


class TestChainVerificationResult:
    """Tests for ChainVerificationResult dataclass."""

    def test_valid_result(self):
        result = ChainVerificationResult(
            valid=True,
            chain_id="global",
            total_records=10,
            verified_count=10,
            head_hash="a" * 64,
            genesis_hash="b" * 64,
        )
        assert result.valid is True
        assert result.total_records == 10
        assert result.verified_count == 10
        assert result.first_invalid_seq is None

    def test_invalid_result(self):
        result = ChainVerificationResult(
            valid=False,
            chain_id="global",
            total_records=10,
            verified_count=5,
            first_invalid_seq=5,
            first_invalid_id="some-id",
            error_message="Hash mismatch",
        )
        assert result.valid is False
        assert result.first_invalid_seq == 5
        assert result.error_message == "Hash mismatch"

    def test_empty_chain_result(self):
        result = ChainVerificationResult(
            valid=False,
            chain_id="empty",
            total_records=0,
            verified_count=0,
            error_message="Chain not found",
        )
        assert result.total_records == 0


class TestChainStats:
    """Tests for ChainStats dataclass."""

    def test_basic_stats(self):
        stats = ChainStats(
            chain_id="global",
            total_records=50,
            head_sequence=49,
            head_hash="a" * 64,
            genesis_hash="b" * 64,
            first_record_at=datetime(2025, 1, 1),
            last_record_at=datetime(2025, 6, 15),
            actions_by_type={
                "GENESIS": 1,
                "SCHEDULE_APPROVED": 30,
                "SWAP_EXECUTED": 19,
            },
        )
        assert stats.total_records == 50
        assert stats.head_sequence == 49
        assert len(stats.actions_by_type) == 3


# ============================================================================
# ApprovalAction enum
# ============================================================================


class TestApprovalAction:
    """Tests for ApprovalAction enum values."""

    def test_genesis_value(self):
        assert ApprovalAction.GENESIS.value == "GENESIS"

    def test_day_sealed_value(self):
        assert ApprovalAction.DAY_SEALED.value == "DAY_SEALED"

    def test_schedule_actions(self):
        assert ApprovalAction.SCHEDULE_GENERATED.value == "SCHEDULE_GENERATED"
        assert ApprovalAction.SCHEDULE_APPROVED.value == "SCHEDULE_APPROVED"
        assert ApprovalAction.SCHEDULE_PUBLISHED.value == "SCHEDULE_PUBLISHED"
        assert ApprovalAction.SCHEDULE_REJECTED.value == "SCHEDULE_REJECTED"

    def test_assignment_actions(self):
        assert ApprovalAction.ASSIGNMENT_CREATED.value == "ASSIGNMENT_CREATED"
        assert ApprovalAction.ASSIGNMENT_MODIFIED.value == "ASSIGNMENT_MODIFIED"
        assert ApprovalAction.ASSIGNMENT_DELETED.value == "ASSIGNMENT_DELETED"

    def test_swap_actions(self):
        assert ApprovalAction.SWAP_REQUESTED.value == "SWAP_REQUESTED"
        assert ApprovalAction.SWAP_APPROVED.value == "SWAP_APPROVED"
        assert ApprovalAction.SWAP_EXECUTED.value == "SWAP_EXECUTED"
        assert ApprovalAction.SWAP_ROLLED_BACK.value == "SWAP_ROLLED_BACK"

    def test_acgme_override_actions(self):
        assert (
            ApprovalAction.ACGME_OVERRIDE_REQUESTED.value == "ACGME_OVERRIDE_REQUESTED"
        )
        assert ApprovalAction.ACGME_OVERRIDE_APPROVED.value == "ACGME_OVERRIDE_APPROVED"
        assert ApprovalAction.ACGME_OVERRIDE_DENIED.value == "ACGME_OVERRIDE_DENIED"

    def test_is_string_enum(self):
        """ApprovalAction values work as strings."""
        assert isinstance(ApprovalAction.GENESIS, str)
        assert ApprovalAction.GENESIS == "GENESIS"

    def test_total_action_count(self):
        """Verify we have the expected number of actions."""
        assert len(ApprovalAction) == 17


# ============================================================================
# Constants
# ============================================================================


class TestConstants:
    """Tests for module-level constants."""

    def test_default_chain_id(self):
        assert DEFAULT_CHAIN_ID == "global"
