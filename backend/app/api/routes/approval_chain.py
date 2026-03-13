"""Approval chain API routes.

Provides endpoints for tamper-evident approval record management:
- Appending new approval records
- Verifying chain integrity
- Querying records by entity or action
- Daily sealing for checkpoint proofs
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.dependencies.role_filter import require_admin, require_coordinator_or_above
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.approval_record import ApprovalAction
from app.models.user import User
from app.schemas.approval_chain import (
    ApprovalRecordCreate,
    ApprovalRecordListResponse,
    ApprovalRecordResponse,
    ChainStatsResponse,
    ChainVerificationRequest,
    ChainVerificationResponse,
    DailySealRequest,
    DailySealResponse,
)
from app.services.approval_chain_service import ApprovalChainService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Chain Verification Endpoints
# ============================================================================


@router.get(
    "/verify",
    response_model=ChainVerificationResponse,
    summary="Verify chain integrity",
    description=(
        "Verify the cryptographic integrity of an approval chain. "
        "Returns OK if all records are valid and properly linked, "
        "or details about the first invalid record if tampering is detected."
    ),
)
async def verify_chain(
    chain_id: str = Query("global", alias="chainId", description="Chain to verify"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ChainVerificationResponse:
    """Verify the integrity of an approval chain."""
    service = ApprovalChainService(db)
    result = service.verify_chain(chain_id)

    return ChainVerificationResponse(
        valid=result.valid,
        chain_id=result.chain_id,
        total_records=result.total_records,
        verified_count=result.verified_count,
        first_invalid_seq=result.first_invalid_seq,
        first_invalid_id=result.first_invalid_id,
        error_message=result.error_message,
        head_hash=result.head_hash,
        genesis_hash=result.genesis_hash,
        verified_at=result.verified_at,
    )


@router.post(
    "/verify",
    response_model=ChainVerificationResponse,
    summary="Verify chain integrity (POST)",
    description="Same as GET /verify but accepts body parameters.",
)
async def verify_chain_post(
    request: ChainVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ChainVerificationResponse:
    """Verify the integrity of an approval chain (POST version)."""
    service = ApprovalChainService(db)
    result = service.verify_chain(
        chain_id=request.chain_id,
        stop_on_first_error=request.stop_on_first_error,
    )

    return ChainVerificationResponse(
        valid=result.valid,
        chain_id=result.chain_id,
        total_records=result.total_records,
        verified_count=result.verified_count,
        first_invalid_seq=result.first_invalid_seq,
        first_invalid_id=result.first_invalid_id,
        error_message=result.error_message,
        head_hash=result.head_hash,
        genesis_hash=result.genesis_hash,
        verified_at=result.verified_at,
    )


# ============================================================================
# Chain Statistics Endpoints
# ============================================================================


@router.get(
    "/stats",
    response_model=ChainStatsResponse,
    summary="Get chain statistics",
    description="Get statistics about an approval chain including record counts and hashes.",
)
async def get_chain_stats(
    chain_id: str = Query("global", alias="chainId", description="Chain to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ChainStatsResponse:
    """Get statistics about an approval chain."""
    service = ApprovalChainService(db)
    stats = service.get_chain_stats(chain_id)

    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Chain '{chain_id}' not found",
        )

    return ChainStatsResponse(
        chain_id=stats.chain_id,
        total_records=stats.total_records,
        head_sequence=stats.head_sequence,
        head_hash=stats.head_hash,
        genesis_hash=stats.genesis_hash,
        first_record_at=stats.first_record_at,
        last_record_at=stats.last_record_at,
        actions_by_type=stats.actions_by_type,
    )


# ============================================================================
# Record Creation Endpoints
# ============================================================================


@router.post(
    "/records",
    response_model=ApprovalRecordResponse,
    summary="Append approval record",
    description=(
        "Append a new approval record to the chain. "
        "The record is cryptographically linked to the previous record. "
        "Requires coordinator or above role."
    ),
    dependencies=[Depends(require_coordinator_or_above)],
)
async def create_approval_record(
    record: ApprovalRecordCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ApprovalRecordResponse:
    """Create a new approval record in the chain."""
    service = ApprovalChainService(db)

    # Get client info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    new_record = service.append_record(
        action=record.action,
        payload=record.payload,
        chain_id=record.chain_id,
        actor_id=current_user.id,
        actor_type=record.actor_type,
        reason=record.reason,
        target_entity_type=record.target_entity_type,
        target_entity_id=record.target_entity_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.commit()

    return ApprovalRecordResponse(
        id=str(new_record.id),
        chain_id=new_record.chain_id,
        sequence_num=new_record.sequence_num,
        prev_hash=new_record.prev_hash,
        record_hash=new_record.record_hash,
        action=new_record.action,
        payload=new_record.payload,
        reason=new_record.reason,
        target_entity_type=new_record.target_entity_type,
        target_entity_id=new_record.target_entity_id,
        actor_id=str(new_record.actor_id) if new_record.actor_id else None,
        actor_type=new_record.actor_type,
        created_at=new_record.created_at,
        ip_address=new_record.ip_address,
    )


# ============================================================================
# Record Query Endpoints
# ============================================================================


@router.get(
    "/records",
    response_model=ApprovalRecordListResponse,
    summary="List approval records",
    description="Query approval records with optional filters.",
)
async def list_approval_records(
    chain_id: str = Query("global", alias="chainId", description="Chain to query"),
    action: str | None = Query(None, description="Filter by action type"),
    target_entity_type: str | None = Query(
        None, alias="targetEntityType", description="Filter by entity type"
    ),
    target_entity_id: str | None = Query(
        None, alias="targetEntityId", description="Filter by entity ID"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Records to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ApprovalRecordListResponse:
    """List approval records with optional filters."""
    service = ApprovalChainService(db)

    # Build query based on filters
    if target_entity_type and target_entity_id:
        records = service.get_records_by_target(
            target_entity_type=target_entity_type,
            target_entity_id=target_entity_id,
            chain_id=chain_id,
        )
    elif action:
        records = service.get_records_by_action(
            action=action,
            chain_id=chain_id,
            limit=limit,
        )
    else:
        # Default: get all records from chain
        from app.models.approval_record import ApprovalRecord
        from sqlalchemy import desc

        records = (
            db.query(ApprovalRecord)
            .filter(ApprovalRecord.chain_id == chain_id)
            .order_by(desc(ApprovalRecord.sequence_num))
            .offset(offset)
            .limit(limit)
            .all()
        )

    # Get total count
    from app.models.approval_record import ApprovalRecord
    from sqlalchemy import func

    total_query = db.query(func.count(ApprovalRecord.id)).filter(
        ApprovalRecord.chain_id == chain_id
    )
    if target_entity_type:
        total_query = total_query.filter(
            ApprovalRecord.target_entity_type == target_entity_type
        )
    if target_entity_id:
        total_query = total_query.filter(
            ApprovalRecord.target_entity_id == target_entity_id
        )
    if action:
        total_query = total_query.filter(ApprovalRecord.action == action)

    total = total_query.scalar() or 0

    return ApprovalRecordListResponse(
        items=[
            ApprovalRecordResponse(
                id=str(r.id),
                chain_id=r.chain_id,
                sequence_num=r.sequence_num,
                prev_hash=r.prev_hash,
                record_hash=r.record_hash,
                action=r.action,
                payload=r.payload,
                reason=r.reason,
                target_entity_type=r.target_entity_type,
                target_entity_id=r.target_entity_id,
                actor_id=str(r.actor_id) if r.actor_id else None,
                actor_type=r.actor_type,
                created_at=r.created_at,
                ip_address=r.ip_address,
            )
            for r in records
        ],
        total=total,
        limit=limit,
        offset=offset,
        chain_id=chain_id,
    )


@router.get(
    "/records/{record_id}",
    response_model=ApprovalRecordResponse,
    summary="Get approval record",
    description="Get a specific approval record by ID.",
)
async def get_approval_record(
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ApprovalRecordResponse:
    """Get a specific approval record."""
    from app.models.approval_record import ApprovalRecord

    record = db.query(ApprovalRecord).filter(ApprovalRecord.id == record_id).first()

    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Approval record '{record_id}' not found",
        )

    return ApprovalRecordResponse(
        id=str(record.id),
        chain_id=record.chain_id,
        sequence_num=record.sequence_num,
        prev_hash=record.prev_hash,
        record_hash=record.record_hash,
        action=record.action,
        payload=record.payload,
        reason=record.reason,
        target_entity_type=record.target_entity_type,
        target_entity_id=record.target_entity_id,
        actor_id=str(record.actor_id) if record.actor_id else None,
        actor_type=record.actor_type,
        created_at=record.created_at,
        ip_address=record.ip_address,
    )


# ============================================================================
# Daily Seal Endpoints
# ============================================================================


@router.post(
    "/seal",
    response_model=DailySealResponse,
    summary="Create daily seal",
    description=(
        "Create a cryptographic checkpoint (daily seal) with a Merkle root "
        "of all records from the specified day. This can be stored externally "
        "for stronger verification. Requires admin role."
    ),
    dependencies=[Depends(require_admin)],
)
async def create_daily_seal(
    request: DailySealRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DailySealResponse:
    """Create a daily seal for the approval chain."""
    service = ApprovalChainService(db)

    seal = service.seal_day(
        chain_id=request.chain_id,
        seal_date=request.seal_date,
        actor_id=current_user.id,
    )

    db.commit()

    return DailySealResponse(
        id=str(seal.id),
        chain_id=seal.chain_id,
        sequence_num=seal.sequence_num,
        seal_date=seal.payload.get("seal_date", ""),
        records_sealed=seal.payload.get("records_sealed", 0),
        merkle_root=seal.payload.get("merkle_root"),
        record_hash=seal.record_hash,
    )


# ============================================================================
# Action Types Endpoint
# ============================================================================


@router.get(
    "/actions",
    response_model=list[str],
    summary="List available actions",
    description="Get the list of valid approval action types.",
)
async def list_actions() -> list[str]:
    """List all valid approval action types."""
    return [action.value for action in ApprovalAction]
