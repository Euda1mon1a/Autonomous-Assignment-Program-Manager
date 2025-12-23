"""Main batch operations service."""

import asyncio
import logging
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.schemas.batch import (
    BatchCreateRequest,
    BatchDeleteRequest,
    BatchOperationStatus,
    BatchOperationType,
    BatchResponse,
    BatchStatusResponse,
    BatchUpdateRequest,
)
from app.services.batch.batch_processor import BatchProcessor
from app.services.batch.batch_validator import BatchValidator

logger = logging.getLogger(__name__)

# In-memory storage for batch operation status (in production, use Redis or database)
_batch_operations: dict[UUID, dict] = {}


class BatchService:
    """Service for batch assignment operations."""

    def __init__(self, db: Session):
        self.db = db
        self.validator = BatchValidator(db)
        self.processor = BatchProcessor(db)

    async def create_batch(
        self,
        request: BatchCreateRequest,
        created_by: str,
    ) -> BatchResponse:
        """
        Create a batch of assignments.

        Args:
            request: Batch create request
            created_by: User creating the assignments

        Returns:
            BatchResponse with operation status and results
        """
        operation_id = uuid4()
        start_time = datetime.utcnow()

        # Store initial status
        _batch_operations[operation_id] = {
            "operation_type": BatchOperationType.CREATE,
            "status": BatchOperationStatus.PROCESSING,
            "total": len(request.assignments),
            "succeeded": 0,
            "failed": 0,
            "created_at": start_time,
        }

        try:
            # Validate batch
            validation_result = self.validator.validate_create_batch(
                request.assignments,
                validate_acgme=request.validate_acgme,
            )

            if not validation_result.valid:
                _batch_operations[operation_id]["status"] = BatchOperationStatus.FAILED
                return BatchResponse(
                    operation_id=operation_id,
                    operation_type=BatchOperationType.CREATE,
                    status=BatchOperationStatus.FAILED,
                    total=len(request.assignments),
                    succeeded=0,
                    failed=len(request.assignments),
                    results=validation_result.operation_errors,
                    errors=validation_result.validation_errors,
                    warnings=validation_result.acgme_warnings,
                    dry_run=request.dry_run,
                    created_at=start_time,
                )

            # If dry run, return validation results without processing
            if request.dry_run:
                _batch_operations[operation_id][
                    "status"
                ] = BatchOperationStatus.COMPLETED
                return BatchResponse(
                    operation_id=operation_id,
                    operation_type=BatchOperationType.CREATE,
                    status=BatchOperationStatus.COMPLETED,
                    total=len(request.assignments),
                    succeeded=len(request.assignments),
                    failed=0,
                    results=[],
                    warnings=validation_result.acgme_warnings,
                    dry_run=True,
                    created_at=start_time,
                    completed_at=datetime.utcnow(),
                )

            # Process batch
            results = await self.processor.process_create_batch(
                request.assignments,
                created_by=created_by,
                rollback_on_error=request.rollback_on_error,
            )

            # Calculate success/failure counts
            succeeded = sum(1 for r in results if r.success)
            failed = sum(1 for r in results if not r.success)

            # Determine overall status
            if failed == 0:
                status = BatchOperationStatus.COMPLETED
            elif succeeded == 0:
                status = BatchOperationStatus.FAILED
            else:
                status = BatchOperationStatus.PARTIAL

            completed_at = datetime.utcnow()
            processing_time_ms = (completed_at - start_time).total_seconds() * 1000

            # Update stored status
            _batch_operations[operation_id].update(
                {
                    "status": status,
                    "succeeded": succeeded,
                    "failed": failed,
                    "completed_at": completed_at,
                }
            )

            return BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.CREATE,
                status=status,
                total=len(request.assignments),
                succeeded=succeeded,
                failed=failed,
                results=results,
                warnings=validation_result.acgme_warnings,
                dry_run=False,
                created_at=start_time,
                completed_at=completed_at,
                processing_time_ms=processing_time_ms,
            )

        except Exception as e:
            logger.error(f"Batch create failed: {e}", exc_info=True)
            _batch_operations[operation_id]["status"] = BatchOperationStatus.FAILED
            return BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.CREATE,
                status=BatchOperationStatus.FAILED,
                total=len(request.assignments),
                succeeded=0,
                failed=len(request.assignments),
                errors=[f"Batch operation failed: {str(e)}"],
                dry_run=request.dry_run,
                created_at=start_time,
            )

    async def update_batch(
        self,
        request: BatchUpdateRequest,
    ) -> BatchResponse:
        """
        Update a batch of assignments.

        Args:
            request: Batch update request

        Returns:
            BatchResponse with operation status and results
        """
        operation_id = uuid4()
        start_time = datetime.utcnow()

        # Store initial status
        _batch_operations[operation_id] = {
            "operation_type": BatchOperationType.UPDATE,
            "status": BatchOperationStatus.PROCESSING,
            "total": len(request.assignments),
            "succeeded": 0,
            "failed": 0,
            "created_at": start_time,
        }

        try:
            # Validate batch
            validation_result = self.validator.validate_update_batch(
                request.assignments,
                validate_acgme=request.validate_acgme,
            )

            if not validation_result.valid:
                _batch_operations[operation_id]["status"] = BatchOperationStatus.FAILED
                return BatchResponse(
                    operation_id=operation_id,
                    operation_type=BatchOperationType.UPDATE,
                    status=BatchOperationStatus.FAILED,
                    total=len(request.assignments),
                    succeeded=0,
                    failed=len(request.assignments),
                    results=validation_result.operation_errors,
                    errors=validation_result.validation_errors,
                    warnings=validation_result.acgme_warnings,
                    dry_run=request.dry_run,
                    created_at=start_time,
                )

            # If dry run, return validation results without processing
            if request.dry_run:
                _batch_operations[operation_id][
                    "status"
                ] = BatchOperationStatus.COMPLETED
                return BatchResponse(
                    operation_id=operation_id,
                    operation_type=BatchOperationType.UPDATE,
                    status=BatchOperationStatus.COMPLETED,
                    total=len(request.assignments),
                    succeeded=len(request.assignments),
                    failed=0,
                    results=[],
                    warnings=validation_result.acgme_warnings,
                    dry_run=True,
                    created_at=start_time,
                    completed_at=datetime.utcnow(),
                )

            # Process batch
            results = await self.processor.process_update_batch(
                request.assignments,
                rollback_on_error=request.rollback_on_error,
            )

            # Calculate success/failure counts
            succeeded = sum(1 for r in results if r.success)
            failed = sum(1 for r in results if not r.success)

            # Determine overall status
            if failed == 0:
                status = BatchOperationStatus.COMPLETED
            elif succeeded == 0:
                status = BatchOperationStatus.FAILED
            else:
                status = BatchOperationStatus.PARTIAL

            completed_at = datetime.utcnow()
            processing_time_ms = (completed_at - start_time).total_seconds() * 1000

            # Update stored status
            _batch_operations[operation_id].update(
                {
                    "status": status,
                    "succeeded": succeeded,
                    "failed": failed,
                    "completed_at": completed_at,
                }
            )

            return BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.UPDATE,
                status=status,
                total=len(request.assignments),
                succeeded=succeeded,
                failed=failed,
                results=results,
                warnings=validation_result.acgme_warnings,
                dry_run=False,
                created_at=start_time,
                completed_at=completed_at,
                processing_time_ms=processing_time_ms,
            )

        except Exception as e:
            logger.error(f"Batch update failed: {e}", exc_info=True)
            _batch_operations[operation_id]["status"] = BatchOperationStatus.FAILED
            return BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.UPDATE,
                status=BatchOperationStatus.FAILED,
                total=len(request.assignments),
                succeeded=0,
                failed=len(request.assignments),
                errors=[f"Batch operation failed: {str(e)}"],
                dry_run=request.dry_run,
                created_at=start_time,
            )

    async def delete_batch(
        self,
        request: BatchDeleteRequest,
    ) -> BatchResponse:
        """
        Delete a batch of assignments.

        Args:
            request: Batch delete request

        Returns:
            BatchResponse with operation status and results
        """
        operation_id = uuid4()
        start_time = datetime.utcnow()

        # Store initial status
        _batch_operations[operation_id] = {
            "operation_type": BatchOperationType.DELETE,
            "status": BatchOperationStatus.PROCESSING,
            "total": len(request.assignments),
            "succeeded": 0,
            "failed": 0,
            "created_at": start_time,
        }

        try:
            # Validate batch
            validation_result = self.validator.validate_delete_batch(
                request.assignments
            )

            if not validation_result.valid:
                _batch_operations[operation_id]["status"] = BatchOperationStatus.FAILED
                return BatchResponse(
                    operation_id=operation_id,
                    operation_type=BatchOperationType.DELETE,
                    status=BatchOperationStatus.FAILED,
                    total=len(request.assignments),
                    succeeded=0,
                    failed=len(request.assignments),
                    results=validation_result.operation_errors,
                    errors=validation_result.validation_errors,
                    dry_run=request.dry_run,
                    created_at=start_time,
                )

            # If dry run, return validation results without processing
            if request.dry_run:
                _batch_operations[operation_id][
                    "status"
                ] = BatchOperationStatus.COMPLETED
                return BatchResponse(
                    operation_id=operation_id,
                    operation_type=BatchOperationType.DELETE,
                    status=BatchOperationStatus.COMPLETED,
                    total=len(request.assignments),
                    succeeded=len(request.assignments),
                    failed=0,
                    results=[],
                    dry_run=True,
                    created_at=start_time,
                    completed_at=datetime.utcnow(),
                )

            # Process batch
            results = await self.processor.process_delete_batch(
                request.assignments,
                rollback_on_error=request.rollback_on_error,
            )

            # Calculate success/failure counts
            succeeded = sum(1 for r in results if r.success)
            failed = sum(1 for r in results if not r.success)

            # Determine overall status
            if failed == 0:
                status = BatchOperationStatus.COMPLETED
            elif succeeded == 0:
                status = BatchOperationStatus.FAILED
            else:
                status = BatchOperationStatus.PARTIAL

            completed_at = datetime.utcnow()
            processing_time_ms = (completed_at - start_time).total_seconds() * 1000

            # Update stored status
            _batch_operations[operation_id].update(
                {
                    "status": status,
                    "succeeded": succeeded,
                    "failed": failed,
                    "completed_at": completed_at,
                }
            )

            return BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.DELETE,
                status=status,
                total=len(request.assignments),
                succeeded=succeeded,
                failed=failed,
                results=results,
                dry_run=False,
                created_at=start_time,
                completed_at=completed_at,
                processing_time_ms=processing_time_ms,
            )

        except Exception as e:
            logger.error(f"Batch delete failed: {e}", exc_info=True)
            _batch_operations[operation_id]["status"] = BatchOperationStatus.FAILED
            return BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.DELETE,
                status=BatchOperationStatus.FAILED,
                total=len(request.assignments),
                succeeded=0,
                failed=len(request.assignments),
                errors=[f"Batch operation failed: {str(e)}"],
                dry_run=request.dry_run,
                created_at=start_time,
            )

    def get_batch_status(self, operation_id: UUID) -> BatchStatusResponse | None:
        """
        Get the status of a batch operation.

        Args:
            operation_id: ID of the batch operation

        Returns:
            BatchStatusResponse if found, None otherwise
        """
        operation = _batch_operations.get(operation_id)
        if not operation:
            return None

        # Calculate progress percentage
        total = operation["total"]
        completed = operation["succeeded"] + operation["failed"]
        progress_percentage = (completed / total * 100) if total > 0 else 0

        # Estimate completion time for in-progress operations
        estimated_completion = None
        if operation["status"] == BatchOperationStatus.PROCESSING and completed > 0:
            elapsed = (datetime.utcnow() - operation["created_at"]).total_seconds()
            estimated_total_time = (elapsed / completed) * total
            estimated_completion = operation["created_at"] + timedelta(
                seconds=estimated_total_time
            )

        return BatchStatusResponse(
            operation_id=operation_id,
            operation_type=operation["operation_type"],
            status=operation["status"],
            total=total,
            succeeded=operation["succeeded"],
            failed=operation["failed"],
            progress_percentage=progress_percentage,
            created_at=operation["created_at"],
            completed_at=operation.get("completed_at"),
            estimated_completion=estimated_completion,
        )
