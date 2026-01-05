"""Tests for CallAssignmentController.

Note: CallAssignmentController uses AsyncSession and async methods.
These tests use mocking for the service layer to avoid complex async setup.
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.controllers.call_assignment_controller import CallAssignmentController
from app.models.person import Person
from app.models.call_assignment import CallAssignment
from app.schemas.call_assignment import (
    CallAssignmentCreate,
    CallAssignmentUpdate,
    BulkCallAssignmentCreate,
)


class TestCallAssignmentController:
    """Test suite for CallAssignmentController."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async db session."""
        return MagicMock()

    @pytest.fixture
    def setup_data(self, db):
        """Create common test data in regular db for reference."""
        resident = Person(
            id=uuid4(),
            name="Dr. Call Resident",
            type="resident",
            email="callresident@hospital.org",
            pgy_level=2,
        )
        db.add(resident)
        db.commit()
        return {"resident": resident}

    # ========================================================================
    # List Call Assignments Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_list_call_assignments_no_filters(self, mock_db):
        """Test listing all call assignments."""
        controller = CallAssignmentController(mock_db)

        # Mock service response with properly typed attributes
        person_id1 = uuid4()
        person_id2 = uuid4()
        mock_items = [
            MagicMock(
                id=uuid4(),
                call_date=date.today(),
                call_type="overnight",
                person_id=person_id1,
                is_weekend=False,
                is_holiday=False,
                person=None,
            ),
            MagicMock(
                id=uuid4(),
                call_date=date.today(),
                call_type="weekend",
                person_id=person_id2,
                is_weekend=True,
                is_holiday=False,
                person=None,
            ),
        ]
        controller.service.get_call_assignments = AsyncMock(
            return_value={"items": mock_items, "total": 2}
        )

        result = await controller.list_call_assignments()

        assert result.total == 2
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_list_call_assignments_with_date_filter(self, mock_db):
        """Test filtering call assignments by date range."""
        controller = CallAssignmentController(mock_db)

        start_date = date.today()
        end_date = date.today() + timedelta(days=7)

        controller.service.get_call_assignments = AsyncMock(
            return_value={"items": [], "total": 0}
        )

        result = await controller.list_call_assignments(
            start_date=start_date, end_date=end_date
        )

        controller.service.get_call_assignments.assert_called_once()
        call_kwargs = controller.service.get_call_assignments.call_args.kwargs
        assert call_kwargs["start_date"] == start_date
        assert call_kwargs["end_date"] == end_date

    @pytest.mark.asyncio
    async def test_list_call_assignments_with_person_filter(self, mock_db, setup_data):
        """Test filtering call assignments by person."""
        controller = CallAssignmentController(mock_db)
        person_id = setup_data["resident"].id

        controller.service.get_call_assignments = AsyncMock(
            return_value={"items": [], "total": 0}
        )

        result = await controller.list_call_assignments(person_id=person_id)

        call_kwargs = controller.service.get_call_assignments.call_args.kwargs
        assert call_kwargs["person_id"] == person_id

    @pytest.mark.asyncio
    async def test_list_call_assignments_with_type_filter(self, mock_db):
        """Test filtering call assignments by call type."""
        controller = CallAssignmentController(mock_db)

        controller.service.get_call_assignments = AsyncMock(
            return_value={"items": [], "total": 0}
        )

        result = await controller.list_call_assignments(call_type="overnight")

        call_kwargs = controller.service.get_call_assignments.call_args.kwargs
        assert call_kwargs["call_type"] == "overnight"

    # ========================================================================
    # Get Call Assignment Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_call_assignment_success(self, mock_db):
        """Test getting a single call assignment."""
        controller = CallAssignmentController(mock_db)
        call_id = uuid4()
        person_id = uuid4()

        mock_call = MagicMock(
            id=call_id,
            call_date=date.today(),
            call_type="overnight",
            person_id=person_id,
            is_weekend=False,
            is_holiday=False,
            person=None,
        )
        controller.service.get_call_assignment = AsyncMock(return_value=mock_call)

        result = await controller.get_call_assignment(call_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_call_assignment_not_found(self, mock_db):
        """Test getting non-existent call assignment raises 404."""
        controller = CallAssignmentController(mock_db)

        controller.service.get_call_assignment = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await controller.get_call_assignment(uuid4())

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Create Call Assignment Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_create_call_assignment_success(self, mock_db, setup_data):
        """Test creating a call assignment."""
        controller = CallAssignmentController(mock_db)

        assignment_data = CallAssignmentCreate(
            call_date=date.today() + timedelta(days=7),
            person_id=setup_data["resident"].id,
            call_type="overnight",
        )

        mock_result = MagicMock(
            id=uuid4(),
            call_date=assignment_data.call_date,
            person_id=assignment_data.person_id,
            call_type="overnight",
            is_weekend=False,
            is_holiday=False,
            person=None,
        )
        controller.service.create_call_assignment = AsyncMock(
            return_value={"call_assignment": mock_result, "error": None}
        )

        result = await controller.create_call_assignment(assignment_data)

        assert result is not None

    @pytest.mark.asyncio
    async def test_create_call_assignment_validation_error(self, mock_db, setup_data):
        """Test creating call assignment with validation error."""
        controller = CallAssignmentController(mock_db)

        assignment_data = CallAssignmentCreate(
            call_date=date.today(),
            person_id=setup_data["resident"].id,
            call_type="overnight",
        )

        controller.service.create_call_assignment = AsyncMock(
            return_value={
                "call_assignment": None,
                "error": "Conflict with existing assignment",
            }
        )

        with pytest.raises(HTTPException) as exc_info:
            await controller.create_call_assignment(assignment_data)

        assert exc_info.value.status_code == 400

    # ========================================================================
    # Update Call Assignment Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_update_call_assignment_success(self, mock_db):
        """Test updating a call assignment."""
        controller = CallAssignmentController(mock_db)
        call_id = uuid4()
        person_id = uuid4()

        update_data = CallAssignmentUpdate(call_type="backup")

        mock_result = MagicMock(
            id=call_id,
            call_date=date.today(),
            call_type="backup",
            person_id=person_id,
            is_weekend=False,
            is_holiday=False,
            person=None,
        )
        controller.service.update_call_assignment = AsyncMock(
            return_value={"call_assignment": mock_result, "error": None}
        )

        result = await controller.update_call_assignment(call_id, update_data)

        assert result is not None

    @pytest.mark.asyncio
    async def test_update_call_assignment_not_found(self, mock_db):
        """Test updating non-existent call assignment."""
        controller = CallAssignmentController(mock_db)

        update_data = CallAssignmentUpdate(call_type="backup")

        controller.service.update_call_assignment = AsyncMock(
            return_value={"call_assignment": None, "error": "Call assignment not found"}
        )

        with pytest.raises(HTTPException) as exc_info:
            await controller.update_call_assignment(uuid4(), update_data)

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Delete Call Assignment Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_delete_call_assignment_success(self, mock_db):
        """Test deleting a call assignment."""
        controller = CallAssignmentController(mock_db)
        call_id = uuid4()

        controller.service.delete_call_assignment = AsyncMock(
            return_value={"error": None}
        )

        # Should not raise
        await controller.delete_call_assignment(call_id)

    @pytest.mark.asyncio
    async def test_delete_call_assignment_not_found(self, mock_db):
        """Test deleting non-existent call assignment."""
        controller = CallAssignmentController(mock_db)

        controller.service.delete_call_assignment = AsyncMock(
            return_value={"error": "Call assignment not found"}
        )

        with pytest.raises(HTTPException) as exc_info:
            await controller.delete_call_assignment(uuid4())

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Bulk Create Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_bulk_create_call_assignments(self, mock_db, setup_data):
        """Test bulk creating call assignments."""
        controller = CallAssignmentController(mock_db)

        assignments = [
            CallAssignmentCreate(
                call_date=date.today() + timedelta(days=i),
                person_id=setup_data["resident"].id,
                call_type="overnight",
            )
            for i in range(5)
        ]

        bulk_data = BulkCallAssignmentCreate(
            assignments=assignments,
            replace_existing=False,
        )

        controller.service.bulk_create_call_assignments = AsyncMock(
            return_value={"count": 5, "errors": []}
        )

        result = await controller.bulk_create_call_assignments(bulk_data)

        assert result.created == 5
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_bulk_create_with_errors(self, mock_db, setup_data):
        """Test bulk create with some errors."""
        controller = CallAssignmentController(mock_db)

        assignments = [
            CallAssignmentCreate(
                call_date=date.today(),
                person_id=setup_data["resident"].id,
                call_type="overnight",
            )
        ]

        bulk_data = BulkCallAssignmentCreate(
            assignments=assignments,
            replace_existing=False,
        )

        controller.service.bulk_create_call_assignments = AsyncMock(
            return_value={"count": 0, "errors": ["Conflict with existing assignment"]}
        )

        result = await controller.bulk_create_call_assignments(bulk_data)

        assert result.created == 0
        assert len(result.errors) == 1

    # ========================================================================
    # Get by Person Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_call_assignments_by_person(self, mock_db, setup_data):
        """Test getting call assignments for a specific person."""
        controller = CallAssignmentController(mock_db)
        person_id = setup_data["resident"].id

        mock_assignments = [
            MagicMock(
                id=uuid4(),
                call_date=date.today() + timedelta(days=i),
                call_type="overnight",
                person_id=person_id,
                is_weekend=False,
                is_holiday=False,
                person=None,
            )
            for i in range(3)
        ]
        controller.service.get_call_assignments_by_person = AsyncMock(
            return_value=mock_assignments
        )

        result = await controller.get_call_assignments_by_person(person_id)

        assert result.total == 3
        controller.service.get_call_assignments_by_person.assert_called_once()

    # ========================================================================
    # Get by Date Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_call_assignments_by_date(self, mock_db):
        """Test getting call assignments for a specific date."""
        controller = CallAssignmentController(mock_db)
        target_date = date.today()
        person_id1 = uuid4()
        person_id2 = uuid4()

        mock_assignments = [
            MagicMock(
                id=uuid4(),
                call_date=target_date,
                call_type="overnight",
                person_id=person_id1,
                is_weekend=False,
                is_holiday=False,
                person=None,
            ),
            MagicMock(
                id=uuid4(),
                call_date=target_date,
                call_type="backup",
                person_id=person_id2,
                is_weekend=False,
                is_holiday=False,
                person=None,
            ),
        ]
        controller.service.get_call_assignments_by_date_range = AsyncMock(
            return_value=mock_assignments
        )

        result = await controller.get_call_assignments_by_date(target_date)

        assert result.total == 2

    # ========================================================================
    # Coverage Report Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_coverage_report(self, mock_db):
        """Test getting call coverage report."""
        controller = CallAssignmentController(mock_db)

        start_date = date.today()
        end_date = date.today() + timedelta(days=30)

        mock_report = MagicMock(
            start_date=start_date,
            end_date=end_date,
            total_days=30,
            covered_days=28,
            coverage_percentage=93.3,
        )
        controller.service.get_coverage_report = AsyncMock(return_value=mock_report)

        result = await controller.get_coverage_report(start_date, end_date)

        assert result is not None
        controller.service.get_coverage_report.assert_called_once_with(
            start_date, end_date
        )

    # ========================================================================
    # Equity Report Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_equity_report(self, mock_db):
        """Test getting call equity/distribution report."""
        controller = CallAssignmentController(mock_db)

        start_date = date.today()
        end_date = date.today() + timedelta(days=30)

        mock_report = MagicMock(
            start_date=start_date,
            end_date=end_date,
            distribution={},
        )
        controller.service.get_equity_report = AsyncMock(return_value=mock_report)

        result = await controller.get_equity_report(start_date, end_date)

        assert result is not None
        controller.service.get_equity_report.assert_called_once_with(
            start_date, end_date
        )

    # ========================================================================
    # Integration Tests (with mocking)
    # ========================================================================

    @pytest.mark.asyncio
    async def test_create_and_list_workflow(self, mock_db, setup_data):
        """Test create and list workflow."""
        controller = CallAssignmentController(mock_db)

        # Create assignment
        assignment_data = CallAssignmentCreate(
            call_date=date.today() + timedelta(days=10),
            person_id=setup_data["resident"].id,
            call_type="overnight",
        )

        created_id = uuid4()
        mock_created = MagicMock(
            id=created_id,
            call_date=assignment_data.call_date,
            person_id=assignment_data.person_id,
            call_type="overnight",
            is_weekend=False,
            is_holiday=False,
            person=None,
        )
        controller.service.create_call_assignment = AsyncMock(
            return_value={"call_assignment": mock_created, "error": None}
        )

        await controller.create_call_assignment(assignment_data)

        # List assignments
        controller.service.get_call_assignments = AsyncMock(
            return_value={"items": [mock_created], "total": 1}
        )

        result = await controller.list_call_assignments()

        assert result.total >= 1

    @pytest.mark.asyncio
    async def test_coverage_gap_detection(self, mock_db):
        """Test coverage gap detection through coverage report."""
        controller = CallAssignmentController(mock_db)

        start_date = date.today()
        end_date = date.today() + timedelta(days=7)

        # Report with gaps
        mock_report = MagicMock(
            start_date=start_date,
            end_date=end_date,
            total_days=7,
            covered_days=5,  # 2 gaps
            coverage_percentage=71.4,
            gaps=[date.today() + timedelta(days=2), date.today() + timedelta(days=5)],
        )
        controller.service.get_coverage_report = AsyncMock(return_value=mock_report)

        result = await controller.get_coverage_report(start_date, end_date)

        assert result.coverage_percentage < 100

    # ========================================================================
    # Bulk Update Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_bulk_update_call_assignments_success(self, mock_db, setup_data):
        """Test bulk updating call assignments."""
        controller = CallAssignmentController(mock_db)
        from app.schemas.call_assignment import (
            BulkCallAssignmentUpdateRequest,
            BulkCallAssignmentUpdateInput,
        )

        assignment_ids = [uuid4(), uuid4()]
        new_person_id = setup_data["resident"].id

        request = BulkCallAssignmentUpdateRequest(
            assignment_ids=assignment_ids,
            updates=BulkCallAssignmentUpdateInput(person_id=new_person_id),
        )

        # Mock service response with properly typed MagicMocks
        mock_assignment1 = MagicMock()
        mock_assignment1.id = assignment_ids[0]
        mock_assignment1.call_date = date.today()
        mock_assignment1.person_id = new_person_id
        mock_assignment1.call_type = "overnight"
        mock_assignment1.is_weekend = False
        mock_assignment1.is_holiday = False
        mock_assignment1.person = None

        mock_assignment2 = MagicMock()
        mock_assignment2.id = assignment_ids[1]
        mock_assignment2.call_date = date.today() + timedelta(days=1)
        mock_assignment2.person_id = new_person_id
        mock_assignment2.call_type = "overnight"
        mock_assignment2.is_weekend = False
        mock_assignment2.is_holiday = False
        mock_assignment2.person = None

        controller.service.bulk_update_call_assignments = AsyncMock(
            return_value={
                "updated": 2,
                "errors": [],
                "assignments": [mock_assignment1, mock_assignment2],
            }
        )

        result = await controller.bulk_update_call_assignments(request)

        assert result.updated == 2
        assert len(result.errors) == 0
        controller.service.bulk_update_call_assignments.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_update_all_fail_raises_400(self, mock_db, setup_data):
        """Test bulk update with all failures raises HTTP 400."""
        controller = CallAssignmentController(mock_db)
        from app.schemas.call_assignment import (
            BulkCallAssignmentUpdateRequest,
            BulkCallAssignmentUpdateInput,
        )

        request = BulkCallAssignmentUpdateRequest(
            assignment_ids=[uuid4()],
            updates=BulkCallAssignmentUpdateInput(person_id=uuid4()),
        )

        controller.service.bulk_update_call_assignments = AsyncMock(
            return_value={
                "updated": 0,
                "errors": ["Person not found"],
                "assignments": [],
            }
        )

        with pytest.raises(HTTPException) as exc_info:
            await controller.bulk_update_call_assignments(request)

        assert exc_info.value.status_code == 400

    # ========================================================================
    # PCAT Generation Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_generate_pcat_success(self, mock_db):
        """Test PCAT generation for call assignments."""
        controller = CallAssignmentController(mock_db)
        from app.schemas.call_assignment import (
            PCATGenerationRequest,
            PCATGenerationResponse,
            PCATAssignmentResult,
        )

        assignment_ids = [uuid4(), uuid4()]
        request = PCATGenerationRequest(assignment_ids=assignment_ids)

        # Mock service response
        mock_response = PCATGenerationResponse(
            processed=2,
            pcat_created=2,
            do_created=2,
            errors=[],
            results=[
                PCATAssignmentResult(
                    call_assignment_id=assignment_ids[0],
                    call_date=date.today(),
                    person_id=uuid4(),
                    person_name="Dr. Test",
                    pcat_created=True,
                    do_created=True,
                ),
                PCATAssignmentResult(
                    call_assignment_id=assignment_ids[1],
                    call_date=date.today() + timedelta(days=1),
                    person_id=uuid4(),
                    person_name="Dr. Test 2",
                    pcat_created=True,
                    do_created=True,
                ),
            ],
        )

        controller.service.generate_pcat_for_assignments = AsyncMock(
            return_value=mock_response
        )

        result = await controller.generate_pcat(request)

        assert result.processed == 2
        assert result.pcat_created == 2
        assert result.do_created == 2
        controller.service.generate_pcat_for_assignments.assert_called_once_with(
            assignment_ids=assignment_ids
        )

    @pytest.mark.asyncio
    async def test_generate_pcat_with_fri_sat_skipped(self, mock_db):
        """Test PCAT generation skips Friday/Saturday calls."""
        controller = CallAssignmentController(mock_db)
        from app.schemas.call_assignment import (
            PCATGenerationRequest,
            PCATGenerationResponse,
            PCATAssignmentResult,
        )

        assignment_id = uuid4()
        request = PCATGenerationRequest(assignment_ids=[assignment_id])

        # Mock service response - Friday call should be skipped
        mock_response = PCATGenerationResponse(
            processed=1,
            pcat_created=0,
            do_created=0,
            errors=[],
            results=[
                PCATAssignmentResult(
                    call_assignment_id=assignment_id,
                    call_date=date.today(),  # Assume this is Friday
                    person_id=uuid4(),
                    person_name="Dr. Test",
                    pcat_created=False,
                    do_created=False,
                    error="Call is Fri/Sat - use FMIT rules",
                ),
            ],
        )

        controller.service.generate_pcat_for_assignments = AsyncMock(
            return_value=mock_response
        )

        result = await controller.generate_pcat(request)

        assert result.processed == 1
        assert result.pcat_created == 0
        assert result.results[0].error is not None

    # ========================================================================
    # Equity Preview Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_equity_preview_success(self, mock_db, setup_data):
        """Test equity preview with simulated changes."""
        controller = CallAssignmentController(mock_db)
        from app.schemas.call_assignment import (
            EquityPreviewRequest,
            EquityPreviewResponse,
            CallEquityReport,
            FacultyEquityDetail,
            SimulatedChange,
        )

        start_date = date.today()
        end_date = date.today() + timedelta(days=30)

        request = EquityPreviewRequest(
            start_date=start_date,
            end_date=end_date,
            simulated_changes=[
                SimulatedChange(
                    assignment_id=uuid4(),
                    call_date=date.today(),
                    old_person_id=uuid4(),
                    new_person_id=setup_data["resident"].id,
                )
            ],
        )

        # Mock service response
        mock_equity = CallEquityReport(
            start_date=start_date,
            end_date=end_date,
            faculty_count=2,
            total_overnight_calls=10,
            sunday_call_stats={"min": 1, "max": 3, "mean": 2.0, "stdev": 0.5},
            weekday_call_stats={"min": 2, "max": 5, "mean": 3.5, "stdev": 1.0},
            distribution=[],
        )

        mock_response = EquityPreviewResponse(
            start_date=start_date,
            end_date=end_date,
            current_equity=mock_equity,
            projected_equity=mock_equity,
            faculty_details=[],
            improvement_score=0.15,
        )

        controller.service.get_equity_preview = AsyncMock(return_value=mock_response)

        result = await controller.get_equity_preview(
            start_date=request.start_date,
            end_date=request.end_date,
            simulated_changes=request.simulated_changes,
        )

        assert result.improvement_score == 0.15
        controller.service.get_equity_preview.assert_called_once()
