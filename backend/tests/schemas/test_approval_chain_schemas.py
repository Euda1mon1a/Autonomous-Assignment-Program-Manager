"""Tests for approval chain schemas (Literal types, aliases, Field bounds, defaults)."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.approval_chain import (
    ApprovalRecordBase,
    ApprovalRecordCreate,
    ApprovalRecordResponse,
    ChainVerificationRequest,
    ChainVerificationResponse,
    ChainStatsResponse,
    DailySealRequest,
    DailySealResponse,
    ApprovalRecordQuery,
    ApprovalRecordListResponse,
)


# ── ApprovalRecordBase ──────────────────────────────────────────────────


class TestApprovalRecordBase:
    def test_valid(self):
        r = ApprovalRecordBase(action="approve", payload={"key": "value"})
        assert r.reason is None
        assert r.target_entity_type is None
        assert r.target_entity_id is None

    # --- action max_length=50 ---

    def test_action_too_long(self):
        with pytest.raises(ValidationError):
            ApprovalRecordBase(action="x" * 51, payload={})

    # --- reason max_length=2000 ---

    def test_reason_too_long(self):
        with pytest.raises(ValidationError):
            ApprovalRecordBase(action="approve", payload={}, reason="x" * 2001)

    # --- target_entity_type max_length=50 ---

    def test_target_entity_type_too_long(self):
        with pytest.raises(ValidationError):
            ApprovalRecordBase(
                action="approve",
                payload={},
                target_entity_type="x" * 51,
            )

    # --- target_entity_id max_length=100 ---

    def test_target_entity_id_too_long(self):
        with pytest.raises(ValidationError):
            ApprovalRecordBase(
                action="approve",
                payload={},
                target_entity_id="x" * 101,
            )

    # --- aliases ---

    def test_by_alias(self):
        r = ApprovalRecordBase(
            action="approve",
            payload={},
            targetEntityType="schedule",
            targetEntityId="sched-123",
        )
        assert r.target_entity_type == "schedule"
        assert r.target_entity_id == "sched-123"

    def test_by_field_name(self):
        r = ApprovalRecordBase(
            action="approve",
            payload={},
            target_entity_type="person",
            target_entity_id="person-456",
        )
        assert r.target_entity_type == "person"


# ── ApprovalRecordCreate ────────────────────────────────────────────────


class TestApprovalRecordCreate:
    def test_defaults(self):
        r = ApprovalRecordCreate(action="approve", payload={"swap": True})
        assert r.chain_id == "global"
        assert r.actor_type == "human"

    # --- chain_id max_length=100 ---

    def test_chain_id_too_long(self):
        with pytest.raises(ValidationError):
            ApprovalRecordCreate(action="approve", payload={}, chain_id="x" * 101)

    # --- actor_type Literal["human", "system", "ai"] ---

    def test_actor_type_human(self):
        r = ApprovalRecordCreate(action="approve", payload={}, actor_type="human")
        assert r.actor_type == "human"

    def test_actor_type_system(self):
        r = ApprovalRecordCreate(action="approve", payload={}, actor_type="system")
        assert r.actor_type == "system"

    def test_actor_type_ai(self):
        r = ApprovalRecordCreate(action="approve", payload={}, actor_type="ai")
        assert r.actor_type == "ai"

    def test_actor_type_invalid(self):
        with pytest.raises(ValidationError):
            ApprovalRecordCreate(action="approve", payload={}, actor_type="bot")

    # --- aliases ---

    def test_by_alias(self):
        r = ApprovalRecordCreate(
            action="approve", payload={}, chainId="audit", actorType="ai"
        )
        assert r.chain_id == "audit"
        assert r.actor_type == "ai"


# ── ApprovalRecordResponse ──────────────────────────────────────────────


class TestApprovalRecordResponse:
    def test_by_alias(self):
        r = ApprovalRecordResponse(
            id="rec-1",
            action="approve",
            payload={"k": "v"},
            chainId="global",
            sequenceNum=1,
            recordHash="abc123",
            actorType="human",
            createdAt=datetime(2026, 1, 1),
        )
        assert r.chain_id == "global"
        assert r.sequence_num == 1
        assert r.record_hash == "abc123"
        assert r.prev_hash is None
        assert r.actor_id is None
        assert r.ip_address is None

    def test_by_field_name(self):
        r = ApprovalRecordResponse(
            id="rec-2",
            action="reject",
            payload={},
            chain_id="ops",
            sequence_num=5,
            prev_hash="prev123",
            record_hash="hash456",
            actor_type="system",
            created_at=datetime(2026, 2, 1),
            actor_id="sys-1",
        )
        assert r.chain_id == "ops"
        assert r.prev_hash == "prev123"
        assert r.actor_id == "sys-1"


# ── ChainVerificationRequest ────────────────────────────────────────────


class TestChainVerificationRequest:
    def test_defaults(self):
        r = ChainVerificationRequest()
        assert r.chain_id == "global"
        assert r.stop_on_first_error is True

    def test_by_alias(self):
        r = ChainVerificationRequest(chainId="audit", stopOnFirstError=False)
        assert r.chain_id == "audit"
        assert r.stop_on_first_error is False

    def test_chain_id_too_long(self):
        with pytest.raises(ValidationError):
            ChainVerificationRequest(chain_id="x" * 101)


# ── ChainVerificationResponse ───────────────────────────────────────────


class TestChainVerificationResponse:
    def test_valid(self):
        r = ChainVerificationResponse(
            valid=True,
            chainId="global",
            totalRecords=100,
            verifiedCount=100,
        )
        assert r.valid is True
        assert r.chain_id == "global"
        assert r.first_invalid_seq is None
        assert r.first_invalid_id is None
        assert r.error_message is None
        assert r.head_hash is None
        assert r.genesis_hash is None

    def test_invalid_chain(self):
        r = ChainVerificationResponse(
            valid=False,
            chain_id="ops",
            total_records=50,
            verified_count=25,
            first_invalid_seq=26,
            first_invalid_id="rec-26",
            error_message="Hash mismatch",
        )
        assert r.first_invalid_seq == 26


# ── ChainStatsResponse ──────────────────────────────────────────────────


class TestChainStatsResponse:
    def test_by_alias(self):
        r = ChainStatsResponse(
            chainId="global",
            totalRecords=100,
            headSequence=100,
            headHash="head123",
            genesisHash="gen123",
            actionsByType={"approve": 80, "reject": 20},
        )
        assert r.chain_id == "global"
        assert r.total_records == 100
        assert r.head_sequence == 100
        assert r.first_record_at is None
        assert r.last_record_at is None

    def test_by_field_name(self):
        r = ChainStatsResponse(
            chain_id="ops",
            total_records=50,
            head_sequence=50,
            head_hash="h1",
            genesis_hash="g1",
            actions_by_type={"seal": 5},
        )
        assert r.chain_id == "ops"


# ── DailySealRequest ────────────────────────────────────────────────────


class TestDailySealRequest:
    def test_defaults(self):
        r = DailySealRequest()
        assert r.chain_id == "global"
        assert r.seal_date is None

    def test_by_alias(self):
        r = DailySealRequest(chainId="audit", sealDate=datetime(2026, 1, 15))
        assert r.chain_id == "audit"
        assert r.seal_date == datetime(2026, 1, 15)

    def test_chain_id_too_long(self):
        with pytest.raises(ValidationError):
            DailySealRequest(chain_id="x" * 101)


# ── DailySealResponse ───────────────────────────────────────────────────


class TestDailySealResponse:
    def test_by_alias(self):
        r = DailySealResponse(
            id="seal-1",
            chainId="global",
            sequenceNum=101,
            sealDate="2026-01-15",
            recordsSealed=100,
            recordHash="seal_hash",
        )
        assert r.chain_id == "global"
        assert r.sequence_num == 101
        assert r.seal_date == "2026-01-15"
        assert r.merkle_root is None

    def test_by_field_name(self):
        r = DailySealResponse(
            id="seal-2",
            chain_id="ops",
            sequence_num=50,
            seal_date="2026-02-01",
            records_sealed=49,
            merkle_root="merkle123",
            record_hash="hash456",
        )
        assert r.merkle_root == "merkle123"


# ── ApprovalRecordQuery ─────────────────────────────────────────────────


class TestApprovalRecordQuery:
    def test_defaults(self):
        r = ApprovalRecordQuery()
        assert r.chain_id == "global"
        assert r.action is None
        assert r.target_entity_type is None
        assert r.target_entity_id is None
        assert r.limit == 100
        assert r.offset == 0

    # --- limit ge=1, le=1000 ---

    def test_limit_below_min(self):
        with pytest.raises(ValidationError):
            ApprovalRecordQuery(limit=0)

    def test_limit_above_max(self):
        with pytest.raises(ValidationError):
            ApprovalRecordQuery(limit=1001)

    # --- offset ge=0 ---

    def test_offset_below_min(self):
        with pytest.raises(ValidationError):
            ApprovalRecordQuery(offset=-1)

    # --- max_length bounds ---

    def test_action_too_long(self):
        with pytest.raises(ValidationError):
            ApprovalRecordQuery(action="x" * 51)

    def test_target_entity_type_too_long(self):
        with pytest.raises(ValidationError):
            ApprovalRecordQuery(target_entity_type="x" * 51)

    def test_target_entity_id_too_long(self):
        with pytest.raises(ValidationError):
            ApprovalRecordQuery(target_entity_id="x" * 101)

    # --- aliases ---

    def test_by_alias(self):
        r = ApprovalRecordQuery(
            chainId="audit",
            targetEntityType="assignment",
            targetEntityId="asgn-1",
        )
        assert r.chain_id == "audit"
        assert r.target_entity_type == "assignment"


# ── ApprovalRecordListResponse ──────────────────────────────────────────


class TestApprovalRecordListResponse:
    def test_by_alias(self):
        r = ApprovalRecordListResponse(
            items=[], total=0, limit=100, offset=0, chainId="global"
        )
        assert r.chain_id == "global"

    def test_by_field_name(self):
        r = ApprovalRecordListResponse(
            items=[], total=0, limit=50, offset=10, chain_id="ops"
        )
        assert r.chain_id == "ops"
