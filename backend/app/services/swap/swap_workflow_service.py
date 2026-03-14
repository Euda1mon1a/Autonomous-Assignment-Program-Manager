"""Service for coordinating swap workflows."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.approval_record import ApprovalAction
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.notifications.notification_types import NotificationType
from app.notifications.service import NotificationService
from app.services.approval_chain_service import ApprovalChainService
from app.websocket.manager import broadcast_schedule_updated, broadcast_swap_approved

logger = get_logger(__name__)


class SwapWorkflowService:
    """Coordinates swap workflows including approvals, execution, notifications and broadcasting."""

    def __init__(self, db: Session):
        self.db = db
        self.notifier = NotificationService(db)
        self.chain = ApprovalChainService(db)

    async def notify_and_record_request(
        self, swap: SwapRecord, actor_id: UUID, reason: str | None = None
    ) -> None:
        """Handle side effects for a new swap request."""
        # Record in approval chain
        try:
            self.chain.append_record(
                action=ApprovalAction.SWAP_REQUESTED,
                payload={
                    "source_faculty_id": str(swap.source_faculty_id),
                    "source_week": str(swap.source_week),
                    "target_faculty_id": str(swap.target_faculty_id),
                    "target_week": str(swap.target_week) if swap.target_week else None,
                    "swap_type": swap.swap_type.value,
                },
                actor_id=actor_id,
                reason=reason,
                target_entity_type="SwapRecord",
                target_entity_id=str(swap.id),
            )
            self.db.commit()
        except Exception:
            logger.error(
                "Failed to append approval record for swap %s", swap.id, exc_info=True
            )

        # Notify target faculty
        try:
            await self.notifier.send_notification(
                recipient_id=swap.target_faculty_id,
                notification_type=NotificationType.SWAP_REQUESTED,
                data={
                    "source_name": str(swap.source_faculty_id),
                    "source_week": str(swap.source_week),
                    "target_name": str(swap.target_faculty_id),
                    "target_week": str(swap.target_week) if swap.target_week else "N/A",
                    "swap_type": swap.swap_type.value,
                    "reason": reason or "No reason provided",
                    "requested_at": datetime.now(UTC).isoformat(),
                },
            )
        except Exception:
            logger.warning("Failed to send swap request notification for %s", swap.id)

    async def notify_and_record_approval(
        self, swap: SwapRecord, actor_id: UUID, notes: str | None = None
    ) -> None:
        """Handle side effects for a swap approval."""
        # Record in approval chain
        try:
            self.chain.append_record(
                action=ApprovalAction.SWAP_APPROVED,
                payload={"swap_id": str(swap.id), "notes": notes},
                actor_id=actor_id,
                reason=notes,
                target_entity_type="SwapRecord",
                target_entity_id=str(swap.id),
            )
            self.db.commit()
        except Exception:
            logger.error(
                "Failed to append approval record for swap %s", swap.id, exc_info=True
            )

        # Broadcast approval
        await broadcast_swap_approved(
            swap_id=swap.id,
            requester_id=swap.source_faculty_id,
            target_person_id=swap.target_faculty_id,
            approved_by=actor_id,
            affected_assignments=[],
            message="Swap approved",
        )

        # Notify requester
        try:
            await self.notifier.send_notification(
                recipient_id=swap.source_faculty_id,
                notification_type=NotificationType.SWAP_APPROVED,
                data={
                    "source_name": str(swap.source_faculty_id),
                    "source_week": str(swap.source_week),
                    "target_name": str(swap.target_faculty_id),
                    "target_week": str(swap.target_week) if swap.target_week else "N/A",
                    "swap_type": swap.swap_type.value if swap.swap_type else "unknown",
                    "approved_by": str(actor_id),
                    "approved_at": datetime.now(UTC).isoformat(),
                },
            )
        except Exception:
            logger.warning("Failed to send swap approval notification for %s", swap.id)

    async def notify_and_record_rejection(
        self, swap: SwapRecord, actor_id: UUID, notes: str | None = None
    ) -> None:
        """Handle side effects for a swap rejection."""
        # Record in approval chain
        try:
            self.chain.append_record(
                action=ApprovalAction.SWAP_REJECTED,
                payload={"swap_id": str(swap.id), "notes": notes},
                actor_id=actor_id,
                reason=notes,
                target_entity_type="SwapRecord",
                target_entity_id=str(swap.id),
            )
            self.db.commit()
        except Exception:
            logger.error(
                "Failed to append rejection record for swap %s", swap.id, exc_info=True
            )

        # Notify requester
        try:
            await self.notifier.send_notification(
                recipient_id=swap.source_faculty_id,
                notification_type=NotificationType.SWAP_REJECTED,
                data={
                    "source_name": str(swap.source_faculty_id),
                    "source_week": str(swap.source_week),
                    "target_name": str(swap.target_faculty_id),
                    "target_week": str(swap.target_week) if swap.target_week else "N/A",
                    "swap_type": swap.swap_type.value if swap.swap_type else "unknown",
                    "rejection_reason": notes or "No reason provided",
                    "reviewed_by": str(actor_id),
                    "reviewed_at": datetime.now(UTC).isoformat(),
                },
            )
        except Exception:
            logger.warning("Failed to send swap rejection notification for %s", swap.id)

    async def notify_and_record_execution(
        self,
        swap: SwapRecord,
        actor_id: UUID,
    ) -> None:
        """Handle side effects for a completed swap execution."""
        # Record execution in approval chain
        try:
            self.chain.append_record(
                action=ApprovalAction.SWAP_EXECUTED,
                payload={
                    "swap_id": str(swap.id),
                    "source_faculty_id": str(swap.source_faculty_id),
                    "target_faculty_id": str(swap.target_faculty_id),
                },
                actor_id=actor_id,
                target_entity_type="SwapRecord",
                target_entity_id=str(swap.id),
            )
            self.db.commit()
        except Exception:
            logger.error(
                "Failed to append execution record for swap %s", swap.id, exc_info=True
            )

        # Broadcast events
        await broadcast_swap_approved(
            swap_id=swap.id,
            requester_id=swap.source_faculty_id,
            target_person_id=swap.target_faculty_id,
            approved_by=actor_id,
            affected_assignments=[],
            message=f"Swap executed: {swap.swap_type.value}",
        )
        await broadcast_schedule_updated(
            schedule_id=None,
            academic_year_id=None,
            user_id=actor_id,
            update_type="modified",
            affected_blocks_count=2,
            message="Approved swap executed",
        )

        # Notify both parties of execution
        try:
            notif_data = {
                "source_name": str(swap.source_faculty_id),
                "source_week": str(swap.source_week),
                "target_name": str(swap.target_faculty_id),
                "target_week": str(swap.target_week) if swap.target_week else "N/A",
                "swap_type": swap.swap_type.value if swap.swap_type else "unknown",
                "executed_by": str(actor_id),
                "executed_at": datetime.now(UTC).isoformat(),
            }
            await self.notifier.send_notification(
                recipient_id=swap.source_faculty_id,
                notification_type=NotificationType.SWAP_EXECUTED,
                data=notif_data,
            )
            await self.notifier.send_notification(
                recipient_id=swap.target_faculty_id,
                notification_type=NotificationType.SWAP_EXECUTED,
                data=notif_data,
            )
        except Exception:
            logger.warning(
                "Failed to send swap execution notifications for %s", swap.id
            )

    async def notify_and_record_rollback(
        self, swap: SwapRecord, actor_id: UUID, reason: str | None = None
    ) -> None:
        """Handle side effects for a swap rollback."""
        # Record rollback in approval chain
        try:
            self.chain.append_record(
                action=ApprovalAction.SWAP_ROLLED_BACK,
                payload={
                    "swap_id": str(swap.id),
                    "reason": reason,
                },
                actor_id=actor_id,
                reason=reason,
                target_entity_type="SwapRecord",
                target_entity_id=str(swap.id),
            )
            self.db.commit()
        except Exception:
            logger.error(
                "Failed to append rollback record for swap %s", swap.id, exc_info=True
            )

        # Broadcast update
        await broadcast_schedule_updated(
            schedule_id=None,
            academic_year_id=None,
            user_id=actor_id,
            update_type="modified",
            affected_blocks_count=2,
            message="Swap rolled back",
        )

        # Notify both parties
        try:
            notif_data = {
                "source_name": str(swap.source_faculty_id),
                "source_week": str(swap.source_week),
                "target_name": str(swap.target_faculty_id),
                "target_week": str(swap.target_week) if swap.target_week else "N/A",
                "swap_type": swap.swap_type.value if swap.swap_type else "unknown",
                "rolled_back_by": str(actor_id),
                "rollback_reason": reason or "No reason provided",
                "rolled_back_at": datetime.now(UTC).isoformat(),
            }
            await self.notifier.send_notification(
                recipient_id=swap.source_faculty_id,
                notification_type=NotificationType.SWAP_ROLLED_BACK,
                data=notif_data,
            )
            await self.notifier.send_notification(
                recipient_id=swap.target_faculty_id,
                notification_type=NotificationType.SWAP_ROLLED_BACK,
                data=notif_data,
            )
        except Exception:
            logger.warning("Failed to send swap rollback notifications for %s", swap.id)
