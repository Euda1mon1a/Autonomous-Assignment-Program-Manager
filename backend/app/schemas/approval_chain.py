"""Approval chain schemas for tamper-evident audit trail.

Pydantic models for the hash-chained approval record system,
including record creation, verification results, and chain statistics.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ============================================================================
# Core Approval Record Schemas
# ============================================================================


class ApprovalRecordBase(BaseModel):
    """Base schema for approval records."""

    action: str = Field(..., max_length=50, description="Type of approval action")
    payload: dict[str, Any] = Field(..., description="Schedule change payload")
    reason: str | None = Field(
        None, max_length=2000, description="Justification for action"
    )
    target_entity_type: str | None = Field(
        None,
        max_length=50,
        alias="targetEntityType",
        description="Type of affected entity",
    )
    target_entity_id: str | None = Field(
        None,
        max_length=100,
        alias="targetEntityId",
        description="ID of affected entity",
    )

    class Config:
        populate_by_name = True


class ApprovalRecordCreate(ApprovalRecordBase):
    """Schema for creating a new approval record."""

    chain_id: str = Field(
        "global",
        max_length=100,
        alias="chainId",
        description="Chain to append to",
    )
    actor_type: Literal["human", "system", "ai"] = Field(
        "human",
        alias="actorType",
        description="Type of actor performing action",
    )

    class Config:
        populate_by_name = True


class ApprovalRecordResponse(ApprovalRecordBase):
    """Schema for approval record response."""

    id: str = Field(..., description="Record UUID")
    chain_id: str = Field(..., alias="chainId", description="Chain identifier")
    sequence_num: int = Field(..., alias="sequenceNum", description="Position in chain")
    prev_hash: str | None = Field(
        None,
        alias="prevHash",
        description="SHA-256 hash of previous record",
    )
    record_hash: str = Field(
        ...,
        alias="recordHash",
        description="SHA-256 hash of this record",
    )
    actor_id: str | None = Field(None, alias="actorId", description="Actor UUID")
    actor_type: str = Field(..., alias="actorType", description="Type of actor")
    created_at: datetime = Field(..., alias="createdAt", description="Record timestamp")
    ip_address: str | None = Field(None, alias="ipAddress", description="Client IP")

    class Config:
        populate_by_name = True
        from_attributes = True


# ============================================================================
# Verification Schemas
# ============================================================================


class ChainVerificationRequest(BaseModel):
    """Request to verify a chain."""

    chain_id: str = Field(
        "global",
        max_length=100,
        alias="chainId",
        description="Chain to verify",
    )
    stop_on_first_error: bool = Field(
        True,
        alias="stopOnFirstError",
        description="Stop verification at first invalid record",
    )

    class Config:
        populate_by_name = True


class ChainVerificationResponse(BaseModel):
    """Result of chain verification."""

    valid: bool = Field(..., description="Whether chain is valid")
    chain_id: str = Field(..., alias="chainId", description="Chain identifier")
    total_records: int = Field(
        ..., alias="totalRecords", description="Total records in chain"
    )
    verified_count: int = Field(
        ...,
        alias="verifiedCount",
        description="Number of records verified",
    )
    first_invalid_seq: int | None = Field(
        None,
        alias="firstInvalidSeq",
        description="Sequence number of first invalid record",
    )
    first_invalid_id: str | None = Field(
        None,
        alias="firstInvalidId",
        description="ID of first invalid record",
    )
    error_message: str | None = Field(
        None,
        alias="errorMessage",
        description="Error description if invalid",
    )
    head_hash: str | None = Field(
        None,
        alias="headHash",
        description="Hash of chain head",
    )
    genesis_hash: str | None = Field(
        None,
        alias="genesisHash",
        description="Hash of genesis record",
    )
    verified_at: str | None = Field(
        None,
        alias="verifiedAt",
        description="Timestamp of verification",
    )

    class Config:
        populate_by_name = True


# ============================================================================
# Chain Statistics Schemas
# ============================================================================


class ChainStatsResponse(BaseModel):
    """Statistics about an approval chain."""

    chain_id: str = Field(..., alias="chainId", description="Chain identifier")
    total_records: int = Field(..., alias="totalRecords", description="Total records")
    head_sequence: int = Field(
        ...,
        alias="headSequence",
        description="Sequence number of head",
    )
    head_hash: str = Field(..., alias="headHash", description="Hash of chain head")
    genesis_hash: str = Field(
        ...,
        alias="genesisHash",
        description="Hash of genesis record",
    )
    first_record_at: datetime | None = Field(
        None,
        alias="firstRecordAt",
        description="Timestamp of genesis",
    )
    last_record_at: datetime | None = Field(
        None,
        alias="lastRecordAt",
        description="Timestamp of head",
    )
    actions_by_type: dict[str, int] = Field(
        ...,
        alias="actionsByType",
        description="Record counts by action type",
    )

    class Config:
        populate_by_name = True


# ============================================================================
# Daily Seal Schemas
# ============================================================================


class DailySealRequest(BaseModel):
    """Request to create a daily seal."""

    chain_id: str = Field(
        "global",
        max_length=100,
        alias="chainId",
        description="Chain to seal",
    )
    seal_date: datetime | None = Field(
        None,
        alias="sealDate",
        description="Date to seal (defaults to today)",
    )

    class Config:
        populate_by_name = True


class DailySealResponse(BaseModel):
    """Response after creating a daily seal."""

    id: str = Field(..., description="Seal record UUID")
    chain_id: str = Field(..., alias="chainId", description="Chain identifier")
    sequence_num: int = Field(..., alias="sequenceNum", description="Seal position")
    seal_date: str = Field(..., alias="sealDate", description="Date sealed")
    records_sealed: int = Field(
        ...,
        alias="recordsSealed",
        description="Number of records in seal",
    )
    merkle_root: str | None = Field(
        None,
        alias="merkleRoot",
        description="Merkle root of sealed records",
    )
    record_hash: str = Field(
        ...,
        alias="recordHash",
        description="Hash of seal record",
    )

    class Config:
        populate_by_name = True


# ============================================================================
# Query Schemas
# ============================================================================


class ApprovalRecordQuery(BaseModel):
    """Query parameters for approval records."""

    chain_id: str = Field(
        "global",
        max_length=100,
        alias="chainId",
        description="Chain to query",
    )
    action: str | None = Field(None, max_length=50, description="Filter by action type")
    target_entity_type: str | None = Field(
        None,
        max_length=50,
        alias="targetEntityType",
        description="Filter by entity type",
    )
    target_entity_id: str | None = Field(
        None,
        max_length=100,
        alias="targetEntityId",
        description="Filter by entity ID",
    )
    limit: int = Field(100, ge=1, le=1000, description="Maximum records to return")
    offset: int = Field(0, ge=0, description="Records to skip")

    class Config:
        populate_by_name = True


class ApprovalRecordListResponse(BaseModel):
    """Paginated list of approval records."""

    items: list[ApprovalRecordResponse] = Field(..., description="List of records")
    total: int = Field(..., description="Total matching records")
    limit: int = Field(..., description="Records per page")
    offset: int = Field(..., description="Records skipped")
    chain_id: str = Field(..., alias="chainId", description="Chain queried")

    class Config:
        populate_by_name = True
