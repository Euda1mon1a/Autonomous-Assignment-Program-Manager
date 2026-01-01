"""Tests for batch_service."""

import pytest
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4
from unittest.mock import Mock, patch, AsyncMock

from sqlalchemy.orm import Session

from app.services.batch.batch_service import BatchService, _batch_operations
from app.schemas.batch import (
    BatchAssignmentCreate,
    BatchAssignmentUpdate,
    BatchAssignmentDelete,
    BatchCreateRequest,
    BatchUpdateRequest,
    BatchDeleteRequest,
    BatchOperationStatus,
    BatchOperationType,
    BatchOperationResult,
    BatchValidationResult,
)
from app.models.person import Person
from app.models.block import Block
from app.models.rotation_template import RotationTemplate


class TestBatchService:
    """Test suite for BatchService."""

    @pytest.fixture
    def batch_service(self, db: Session) -> BatchService:
        """Create BatchService instance for testing."""
        return BatchService(db)

    @pytest.fixture
    def sample_person(self, db: Session) -> Person:
        """Create a sample person for testing."""
        person = Person(
            id=uuid4(),
            name="Dr. Test Resident",
            type="resident",
            email="test.resident@hospital.org",
            pgy_level=1,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    @pytest.fixture
    def sample_block(self, db: Session) -> Block:
        """Create a sample block for testing."""
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=7),
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
            is_holiday=False,
        )
        db.add(block)
        db.commit()
        db.refresh(block)
        return block

    @pytest.fixture
    def sample_rotation_template(self, db: Session) -> RotationTemplate:
        """Create a sample rotation template for testing."""
        template = RotationTemplate(
            id=uuid4(),
            name="Test Rotation",
            activity_type="outpatient",
            abbreviation="TR",
            max_residents=4,
            supervision_required=True,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @pytest.fixture
    def valid_batch_create_request(
        self,
        sample_person: Person,
        sample_block: Block,
        sample_rotation_template: RotationTemplate,
    ) -> BatchCreateRequest:
        """Create a valid batch create request."""
        return BatchCreateRequest(
            assignments=[
                BatchAssignmentCreate(
                    block_id=sample_block.id,
                    person_id=sample_person.id,
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                )
            ],
            dry_run=False,
            rollback_on_error=True,
            validate_acgme=True,
        )

    def test_create_batch_success(
        self,
        batch_service: BatchService,
        valid_batch_create_request: BatchCreateRequest,
    ):
        """Test successful batch create execution."""
        # Arrange
        created_by = "test_user"

        # Mock validator to return valid result
        with patch.object(
            batch_service.validator,
            "validate_create_batch",
            return_value=BatchValidationResult(
                valid=True,
                total_operations=1,
                validation_errors=[],
                operation_errors=[],
                acgme_warnings=[],
            ),
        ):
            # Mock processor to return successful results
            with patch.object(
                batch_service.processor,
                "process_create_batch",
                new_callable=AsyncMock,
                return_value=[
                    BatchOperationResult(
                        index=0,
                        success=True,
                        assignment_id=uuid4(),
                    )
                ],
            ):
                # Act
                import asyncio

                response = asyncio.run(
                    batch_service.create_batch(valid_batch_create_request, created_by)
                )

        # Assert
        assert response.operation_type == BatchOperationType.CREATE
        assert response.status == BatchOperationStatus.COMPLETED
        assert response.total == 1
        assert response.succeeded == 1
        assert response.failed == 0
        assert response.dry_run is False
        assert isinstance(response.operation_id, UUID)
        assert response.created_at is not None
        assert response.completed_at is not None
        assert response.processing_time_ms is not None

    def test_create_batch_validation_failure(
        self,
        batch_service: BatchService,
        valid_batch_create_request: BatchCreateRequest,
    ):
        """Test batch create with validation failure."""
        # Arrange
        created_by = "test_user"

        # Mock validator to return invalid result
        with patch.object(
            batch_service.validator,
            "validate_create_batch",
            return_value=BatchValidationResult(
                valid=False,
                total_operations=1,
                validation_errors=["Invalid assignment data"],
                operation_errors=[
                    BatchOperationResult(
                        index=0,
                        success=False,
                        error="Person not found",
                    )
                ],
                acgme_warnings=[],
            ),
        ):
            # Act
            import asyncio

            response = asyncio.run(
                batch_service.create_batch(valid_batch_create_request, created_by)
            )

        # Assert
        assert response.status == BatchOperationStatus.FAILED
        assert response.succeeded == 0
        assert response.failed == 1
        assert len(response.errors) > 0
        assert "Invalid assignment data" in response.errors

    def test_create_batch_dry_run(
        self,
        batch_service: BatchService,
        valid_batch_create_request: BatchCreateRequest,
    ):
        """Test batch create in dry run mode."""
        # Arrange
        created_by = "test_user"
        valid_batch_create_request.dry_run = True

        # Mock validator to return valid result
        with patch.object(
            batch_service.validator,
            "validate_create_batch",
            return_value=BatchValidationResult(
                valid=True,
                total_operations=1,
                validation_errors=[],
                operation_errors=[],
                acgme_warnings=["Warning: High workload"],
            ),
        ):
            # Act
            import asyncio

            response = asyncio.run(
                batch_service.create_batch(valid_batch_create_request, created_by)
            )

        # Assert
        assert response.status == BatchOperationStatus.COMPLETED
        assert response.dry_run is True
        assert response.succeeded == 1
        assert response.failed == 0
        assert len(response.warnings) > 0
        assert response.completed_at is not None
        # Processor should not be called in dry run
        assert len(response.results) == 0

    def test_create_batch_partial_success(
        self,
        batch_service: BatchService,
        sample_person: Person,
        sample_block: Block,
        sample_rotation_template: RotationTemplate,
    ):
        """Test batch create with partial success."""
        # Arrange
        created_by = "test_user"
        request = BatchCreateRequest(
            assignments=[
                BatchAssignmentCreate(
                    block_id=sample_block.id,
                    person_id=sample_person.id,
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                ),
                BatchAssignmentCreate(
                    block_id=sample_block.id,
                    person_id=uuid4(),  # Non-existent person
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                ),
            ],
            dry_run=False,
            rollback_on_error=False,
            validate_acgme=True,
        )

        # Mock validator to return valid result
        with patch.object(
            batch_service.validator,
            "validate_create_batch",
            return_value=BatchValidationResult(
                valid=True,
                total_operations=2,
                validation_errors=[],
                operation_errors=[],
                acgme_warnings=[],
            ),
        ):
            # Mock processor to return mixed results
            with patch.object(
                batch_service.processor,
                "process_create_batch",
                new_callable=AsyncMock,
                return_value=[
                    BatchOperationResult(
                        index=0,
                        success=True,
                        assignment_id=uuid4(),
                    ),
                    BatchOperationResult(
                        index=1,
                        success=False,
                        error="Person not found",
                    ),
                ],
            ):
                # Act
                import asyncio

                response = asyncio.run(batch_service.create_batch(request, created_by))

        # Assert
        assert response.status == BatchOperationStatus.PARTIAL
        assert response.succeeded == 1
        assert response.failed == 1
        assert response.total == 2

    def test_update_batch_success(
        self,
        batch_service: BatchService,
    ):
        """Test successful batch update execution."""
        # Arrange
        assignment_id = uuid4()
        request = BatchUpdateRequest(
            assignments=[
                BatchAssignmentUpdate(
                    assignment_id=assignment_id,
                    role="supervising",
                    updated_at=datetime.utcnow(),
                )
            ],
            dry_run=False,
            rollback_on_error=True,
            validate_acgme=True,
        )

        # Mock validator to return valid result
        with patch.object(
            batch_service.validator,
            "validate_update_batch",
            return_value=BatchValidationResult(
                valid=True,
                total_operations=1,
                validation_errors=[],
                operation_errors=[],
                acgme_warnings=[],
            ),
        ):
            # Mock processor to return successful results
            with patch.object(
                batch_service.processor,
                "process_update_batch",
                new_callable=AsyncMock,
                return_value=[
                    BatchOperationResult(
                        index=0,
                        success=True,
                        assignment_id=assignment_id,
                    )
                ],
            ):
                # Act
                import asyncio

                response = asyncio.run(batch_service.update_batch(request))

        # Assert
        assert response.operation_type == BatchOperationType.UPDATE
        assert response.status == BatchOperationStatus.COMPLETED
        assert response.succeeded == 1
        assert response.failed == 0

    def test_delete_batch_success(
        self,
        batch_service: BatchService,
    ):
        """Test successful batch delete execution."""
        # Arrange
        assignment_id = uuid4()
        request = BatchDeleteRequest(
            assignments=[
                BatchAssignmentDelete(
                    assignment_id=assignment_id,
                    soft_delete=False,
                )
            ],
            dry_run=False,
            rollback_on_error=True,
        )

        # Mock validator to return valid result
        with patch.object(
            batch_service.validator,
            "validate_delete_batch",
            return_value=BatchValidationResult(
                valid=True,
                total_operations=1,
                validation_errors=[],
                operation_errors=[],
                acgme_warnings=[],
            ),
        ):
            # Mock processor to return successful results
            with patch.object(
                batch_service.processor,
                "process_delete_batch",
                new_callable=AsyncMock,
                return_value=[
                    BatchOperationResult(
                        index=0,
                        success=True,
                        assignment_id=assignment_id,
                    )
                ],
            ):
                # Act
                import asyncio

                response = asyncio.run(batch_service.delete_batch(request))

        # Assert
        assert response.operation_type == BatchOperationType.DELETE
        assert response.status == BatchOperationStatus.COMPLETED
        assert response.succeeded == 1
        assert response.failed == 0

    def test_get_batch_status_found(
        self,
        batch_service: BatchService,
    ):
        """Test getting status of existing batch operation."""
        # Arrange
        operation_id = uuid4()
        _batch_operations[operation_id] = {
            "operation_type": BatchOperationType.CREATE,
            "status": BatchOperationStatus.COMPLETED,
            "total": 10,
            "succeeded": 8,
            "failed": 2,
            "created_at": datetime.utcnow(),
            "completed_at": datetime.utcnow(),
        }

        # Act
        status = batch_service.get_batch_status(operation_id)

        # Assert
        assert status is not None
        assert status.operation_id == operation_id
        assert status.operation_type == BatchOperationType.CREATE
        assert status.status == BatchOperationStatus.COMPLETED
        assert status.total == 10
        assert status.succeeded == 8
        assert status.failed == 2
        assert status.progress_percentage == 100.0

        # Cleanup
        del _batch_operations[operation_id]

    def test_get_batch_status_not_found(
        self,
        batch_service: BatchService,
    ):
        """Test getting status of non-existent batch operation."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        status = batch_service.get_batch_status(non_existent_id)

        # Assert
        assert status is None

    def test_get_batch_status_in_progress(
        self,
        batch_service: BatchService,
    ):
        """Test getting status of in-progress batch operation with estimated completion."""
        # Arrange
        operation_id = uuid4()
        created_at = datetime.utcnow() - timedelta(seconds=60)
        _batch_operations[operation_id] = {
            "operation_type": BatchOperationType.CREATE,
            "status": BatchOperationStatus.PROCESSING,
            "total": 100,
            "succeeded": 50,
            "failed": 0,
            "created_at": created_at,
        }

        # Act
        status = batch_service.get_batch_status(operation_id)

        # Assert
        assert status is not None
        assert status.status == BatchOperationStatus.PROCESSING
        assert status.progress_percentage == 50.0
        assert status.estimated_completion is not None

        # Cleanup
        del _batch_operations[operation_id]

    def test_create_batch_exception_handling(
        self,
        batch_service: BatchService,
        valid_batch_create_request: BatchCreateRequest,
    ):
        """Test batch create handles exceptions gracefully."""
        # Arrange
        created_by = "test_user"

        # Mock validator to raise exception
        with patch.object(
            batch_service.validator,
            "validate_create_batch",
            side_effect=Exception("Database connection error"),
        ):
            # Act
            import asyncio

            response = asyncio.run(
                batch_service.create_batch(valid_batch_create_request, created_by)
            )

        # Assert
        assert response.status == BatchOperationStatus.FAILED
        assert response.succeeded == 0
        assert response.failed == 1
        assert len(response.errors) > 0
        assert "Database connection error" in response.errors[0]

    def test_update_batch_exception_handling(
        self,
        batch_service: BatchService,
    ):
        """Test batch update handles exceptions gracefully."""
        # Arrange
        request = BatchUpdateRequest(
            assignments=[
                BatchAssignmentUpdate(
                    assignment_id=uuid4(),
                    role="supervising",
                    updated_at=datetime.utcnow(),
                )
            ],
            dry_run=False,
            rollback_on_error=True,
            validate_acgme=True,
        )

        # Mock validator to raise exception
        with patch.object(
            batch_service.validator,
            "validate_update_batch",
            side_effect=Exception("Validation error"),
        ):
            # Act
            import asyncio

            response = asyncio.run(batch_service.update_batch(request))

        # Assert
        assert response.status == BatchOperationStatus.FAILED
        assert response.succeeded == 0
        assert len(response.errors) > 0

    def test_delete_batch_exception_handling(
        self,
        batch_service: BatchService,
    ):
        """Test batch delete handles exceptions gracefully."""
        # Arrange
        request = BatchDeleteRequest(
            assignments=[
                BatchAssignmentDelete(
                    assignment_id=uuid4(),
                    soft_delete=False,
                )
            ],
            dry_run=False,
            rollback_on_error=True,
        )

        # Mock validator to raise exception
        with patch.object(
            batch_service.validator,
            "validate_delete_batch",
            side_effect=Exception("Delete validation error"),
        ):
            # Act
            import asyncio

            response = asyncio.run(batch_service.delete_batch(request))

        # Assert
        assert response.status == BatchOperationStatus.FAILED
        assert response.succeeded == 0
        assert len(response.errors) > 0
