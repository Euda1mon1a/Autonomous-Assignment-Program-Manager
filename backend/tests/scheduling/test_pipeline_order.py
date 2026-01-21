"""
Test suite for schedule generation pipeline order.

The dependency chain is:
  Call → PCAT/DO → AT Coverage → Resident Clinic Load → Faculty Admin

PCAT (Post-Call Attending Time) counts toward AT (supervision) coverage.
Residents must know PCAT availability BEFORE scheduling clinic slots.
Faculty admin time fills AFTER knowing resident clinic demand.

CORRECT Order (Session 125):
1. Load NON-CALL preloads (skip_faculty_call=True)
2. Expand resident block assignments
3. Call solver → NEW CallAssignment
4. Create PCAT/DO immediately (LOCKED as preload)
5. Activity solver (NOW knows PCAT for AT coverage)
6. Fill faculty half-days (NOW knows resident demand)

These tests verify the order is maintained and detect regressions.

Test Categories:
- TestPreloadServiceSkipFacultyCall: Unit tests for skip_faculty_call parameter
- TestPipelineOrderEnforcement: Mock/patch tests that verify call order (TRIPWIRE)
- TestPipelineIntegration: Integration tests that verify correctness (DATABASE)
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from typing import Any

import pytest


# ============================================================================
# Unit Tests: SyncPreloadService skip_faculty_call parameter
# ============================================================================


class TestPreloadServiceSkipFacultyCall:
    """Test that SyncPreloadService accepts skip_faculty_call parameter."""

    def test_load_all_preloads_accepts_skip_faculty_call_true(self) -> None:
        """Verify skip_faculty_call=True is accepted and skips faculty call loading."""
        from app.services.sync_preload_service import SyncPreloadService

        # Create mock session
        mock_session = MagicMock()
        mock_session.execute.return_value.scalars.return_value.all.return_value = []

        service = SyncPreloadService(mock_session)

        # Should not raise when skip_faculty_call=True
        with patch.object(service, "_load_absences", return_value=0):
            with patch.object(service, "_load_inpatient_preloads", return_value=0):
                with patch.object(service, "_load_fmit_call", return_value=0):
                    with patch.object(
                        service, "_load_inpatient_clinic", return_value=0
                    ):
                        with patch.object(
                            service, "_load_resident_call", return_value=0
                        ):
                            with patch.object(
                                service, "_load_faculty_call", return_value=0
                            ) as mock_faculty_call:
                                with patch.object(
                                    service, "_load_sm_preloads", return_value=0
                                ):
                                    service.load_all_preloads(
                                        block_number=10,
                                        academic_year=2025,
                                        skip_faculty_call=True,
                                    )

        # _load_faculty_call should NOT be called when skip_faculty_call=True
        mock_faculty_call.assert_not_called()

    def test_load_all_preloads_calls_faculty_call_by_default(self) -> None:
        """Verify _load_faculty_call is called when skip_faculty_call=False (default)."""
        from app.services.sync_preload_service import SyncPreloadService

        mock_session = MagicMock()
        mock_session.execute.return_value.scalars.return_value.all.return_value = []

        service = SyncPreloadService(mock_session)

        with patch.object(service, "_load_absences", return_value=0):
            with patch.object(service, "_load_inpatient_preloads", return_value=0):
                with patch.object(service, "_load_fmit_call", return_value=0):
                    with patch.object(
                        service, "_load_inpatient_clinic", return_value=0
                    ):
                        with patch.object(
                            service, "_load_resident_call", return_value=0
                        ):
                            with patch.object(
                                service, "_load_faculty_call", return_value=0
                            ) as mock_faculty_call:
                                with patch.object(
                                    service, "_load_sm_preloads", return_value=0
                                ):
                                    service.load_all_preloads(
                                        block_number=10,
                                        academic_year=2025,
                                        # skip_faculty_call defaults to False
                                    )

        # _load_faculty_call SHOULD be called when skip_faculty_call=False
        mock_faculty_call.assert_called_once()


# ============================================================================
# Mock/Patch Enforcement Tests (TRIPWIRE - catches code structure changes)
# ============================================================================


class TestPipelineOrderEnforcement:
    """
    Mock/patch tests that verify the engine calls methods in correct order.

    These are TRIPWIRE tests - they catch if someone reorders the pipeline.
    They test the CODE STRUCTURE, not the behavior.
    """

    def test_engine_calls_pipeline_steps_in_correct_order(self) -> None:
        """
        ENFORCEMENT TEST: Verify engine.generate() calls pipeline steps in order.

        This test patches key pipeline components and tracks call order.
        If someone reorders the pipeline in engine.py, this test WILL FAIL.

        Expected order:
        1. preload (with skip_faculty_call=True)
        2. expansion
        3. call_solver (greedy for call generation)
        4. pcat_do_sync (after call_create)
        5. activity_solver
        6. faculty_expansion

        HARD-FAIL: Test fails if ANY required step is missing (no exception swallowing).
        """
        # Track call order via module-level patches
        call_order: list[str] = []

        # Required steps that MUST be called (in order)
        REQUIRED_STEPS = [
            "preload_skip_faculty",
            "expansion",
            "call_solver",
            "pcat_do_sync",
            "activity_solver",
            "faculty_expansion",
        ]

        def track_preload_call(*args: Any, **kwargs: Any) -> int:
            if kwargs.get("skip_faculty_call"):
                call_order.append("preload_skip_faculty")
            else:
                call_order.append("preload_all")
            return 0

        def track_expansion_call(*args: Any, **kwargs: Any) -> list:
            call_order.append("expansion")
            return []

        def track_call_solver(*args: Any, **kwargs: Any) -> MagicMock:
            """Track _run_solver for call generation."""
            call_order.append("call_solver")
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.assignments = []
            mock_result.call_assignments = [MagicMock()]
            mock_result.solver_status = "OPTIMAL"
            mock_result.validation_issues = []
            return mock_result

        def track_activity_call(*args: Any, **kwargs: Any) -> dict:
            call_order.append("activity_solver")
            return {"success": True, "assignments_updated": 0, "status": "OPTIMAL"}

        def track_faculty_call(*args: Any, **kwargs: Any) -> int:
            call_order.append("faculty_expansion")
            return 0

        def track_pcat_sync(*args: Any, **kwargs: Any) -> int:
            call_order.append("pcat_do_sync")
            return 0

        # Patch the services at module level
        with patch("app.scheduling.engine.SyncPreloadService") as mock_preload_cls:
            mock_preload_instance = MagicMock()
            mock_preload_instance.load_all_preloads.side_effect = track_preload_call
            mock_preload_cls.return_value = mock_preload_instance

            with patch(
                "app.scheduling.engine.BlockAssignmentExpansionService"
            ) as mock_expansion_cls:
                mock_expansion_instance = MagicMock()
                mock_expansion_instance.expand_block_assignments.side_effect = (
                    track_expansion_call
                )
                mock_expansion_cls.return_value = mock_expansion_instance

                with patch(
                    "app.scheduling.engine.CPSATActivitySolver"
                ) as mock_activity_cls:
                    mock_activity_instance = MagicMock()
                    mock_activity_instance.solve.side_effect = track_activity_call
                    mock_activity_cls.return_value = mock_activity_instance

                    with patch(
                        "app.scheduling.engine.FacultyAssignmentExpansionService"
                    ) as mock_faculty_cls:
                        mock_faculty_instance = MagicMock()
                        mock_faculty_instance.fill_faculty_assignments.side_effect = (
                            track_faculty_call
                        )
                        mock_faculty_cls.return_value = mock_faculty_instance

                        # Import after patching
                        from app.scheduling.engine import SchedulingEngine

                        # Create mock DB
                        mock_db = MagicMock()
                        mock_db.execute.return_value.scalars.return_value.all.return_value = []  # noqa: E501
                        mock_db.execute.return_value.scalars.return_value.first.return_value = None  # noqa: E501
                        mock_db.execute.return_value.scalar.return_value = 0
                        mock_db.query.return_value.filter.return_value.all.return_value = []  # noqa: E501

                        start_date = date(2026, 3, 12)
                        end_date = date(2026, 4, 8)

                        # Patch engine methods
                        with patch.object(SchedulingEngine, "_ensure_blocks_exist"):
                            with patch.object(
                                SchedulingEngine, "_check_pre_generation_resilience"
                            ):
                                with patch.object(
                                    SchedulingEngine,
                                    "_check_post_generation_resilience",
                                ):
                                    engine = SchedulingEngine(
                                        mock_db, start_date, end_date
                                    )

                        # Patch instance methods - track _run_solver for call generation
                        engine._run_solver = track_call_solver
                        engine._sync_call_pcat_do_to_half_day = track_pcat_sync

                        # Mock PreSolverValidator to pass validation
                        mock_validation_result = MagicMock()
                        mock_validation_result.feasible = True
                        mock_validation_result.issues = []
                        mock_validation_result.warnings = []
                        mock_validation_result.recommendations = []
                        mock_validation_result.statistics = {
                            "complexity_level": "LOW",
                            "num_variables": 100,
                            "estimated_runtime": "1s",
                        }

                        with patch(
                            "app.scheduling.engine.PreSolverValidator"
                        ) as mock_validator_cls:
                            mock_validator = MagicMock()
                            mock_validator.validate_saturation.return_value = (
                                mock_validation_result
                            )
                            mock_validator_cls.return_value = mock_validator

                            with patch.object(
                                engine,
                                "_create_call_assignments_from_result",
                                return_value=[MagicMock()],
                            ):
                                with patch.object(engine, "_build_availability_matrix"):
                                    with patch.object(
                                        engine,
                                        "_get_residents",
                                        return_value=[MagicMock()],
                                    ):
                                        with patch.object(
                                            engine,
                                            "_get_rotation_templates",
                                            return_value=[MagicMock()],
                                        ):
                                            with patch.object(
                                                engine, "_get_faculty", return_value=[]
                                            ):
                                                # Mock post-generation validator
                                                mock_post_validation = MagicMock()
                                                mock_post_validation.valid = True
                                                mock_post_validation.violations = []
                                                mock_post_validation.warnings = []
                                                mock_post_validation.coverage_rate = 1.0
                                                engine.validator = MagicMock()
                                                engine.validator.validate_all.return_value = mock_post_validation

                                                # Run generate - NO exception swallowing
                                                engine.generate(
                                                    block_number=10,
                                                    academic_year=2025,
                                                    expand_block_assignments=True,
                                                    algorithm="greedy",
                                                )

        # HARD-FAIL ASSERTIONS: All required steps MUST be present
        missing_steps = [step for step in REQUIRED_STEPS if step not in call_order]
        assert not missing_steps, (
            f"HARD-FAIL: Missing required pipeline steps: {missing_steps}. "
            f"Actual call order: {call_order}"
        )

        # Verify preload was called with skip_faculty_call=True (not skip_faculty_call=False)
        assert "preload_skip_faculty" in call_order, (
            f"Preload must be called with skip_faculty_call=True. Got: {call_order}"
        )
        assert "preload_all" not in call_order, (
            f"Preload should NOT be called with skip_faculty_call=False. Got: {call_order}"
        )

        # Verify correct ordering of ALL required steps
        for i, step in enumerate(REQUIRED_STEPS[:-1]):
            next_step = REQUIRED_STEPS[i + 1]
            assert call_order.index(step) < call_order.index(next_step), (
                f"Order violation: {step} must come before {next_step}. "
                f"Actual order: {call_order}"
            )

    def test_preload_called_with_skip_faculty_call_true(self) -> None:
        """Verify preload is called with skip_faculty_call=True in half-day mode."""
        from app.services.sync_preload_service import SyncPreloadService

        mock_session = MagicMock()
        mock_session.execute.return_value.scalars.return_value.all.return_value = []

        service = SyncPreloadService(mock_session)

        with patch.object(service, "_load_absences", return_value=0):
            with patch.object(service, "_load_inpatient_preloads", return_value=0):
                with patch.object(service, "_load_fmit_call", return_value=0):
                    with patch.object(
                        service, "_load_inpatient_clinic", return_value=0
                    ):
                        with patch.object(
                            service, "_load_resident_call", return_value=0
                        ):
                            with patch.object(
                                service, "_load_faculty_call", return_value=0
                            ) as mock_faculty:
                                with patch.object(
                                    service, "_load_sm_preloads", return_value=0
                                ):
                                    # Call with skip_faculty_call=True (as engine does)
                                    service.load_all_preloads(
                                        block_number=10,
                                        academic_year=2025,
                                        skip_faculty_call=True,
                                    )

        # Faculty call should NOT be loaded
        mock_faculty.assert_not_called()


# ============================================================================
# Integration Tests (DATABASE - verifies actual correctness)
# ============================================================================


class TestPipelineIntegration:
    """
    Integration tests that verify the pipeline produces correct results.

    These tests require a database connection and verify:
    - PCAT/DO is created for each call assignment
    - PCAT/DO has source='preload' (locked)
    - FMIT faculty don't get PCAT/DO
    - End-of-block calls don't create out-of-range PCAT/DO
    """

    @pytest.fixture
    def db_session(self):
        """Get database session for integration tests."""
        from app.db.session import SessionLocal

        session = SessionLocal()
        yield session
        session.rollback()
        session.close()

    @pytest.mark.integration
    def test_pcat_do_created_for_each_call(self, db_session) -> None:
        """
        INTEGRATION TEST: Verify each call assignment has PCAT/DO.

        For each CallAssignment in Block 10:
        - Next day AM should have PCAT (unless FMIT)
        - Next day PM should have DO (unless FMIT)
        - Both should have source='preload'
        """
        from app.models.call_assignment import CallAssignment
        from app.models.half_day_assignment import HalfDayAssignment
        from app.models.activity import Activity
        from app.models.inpatient_preload import InpatientPreload
        from sqlalchemy import select, and_

        # Block 10 dates
        start_date = date(2026, 3, 12)
        end_date = date(2026, 4, 8)

        # Get all call assignments in Block 10
        call_query = select(CallAssignment).where(
            and_(
                CallAssignment.date >= start_date,
                CallAssignment.date <= end_date,
            )
        )
        call_assignments = db_session.execute(call_query).scalars().all()

        if not call_assignments:
            pytest.skip("No call assignments in Block 10 - run generation first")

        # Get PCAT and DO activities
        pcat_activity = (
            db_session.execute(select(Activity).where(Activity.code == "pcat"))
            .scalars()
            .first()
        )
        do_activity = (
            db_session.execute(select(Activity).where(Activity.code == "do"))
            .scalars()
            .first()
        )

        assert pcat_activity, "PCAT activity must exist"
        assert do_activity, "DO activity must exist"

        # Check each call assignment
        missing_pcat = []
        missing_do = []
        wrong_source = []

        for call in call_assignments:
            next_day = call.date + timedelta(days=1)

            # Skip if next day is outside block
            if next_day > end_date:
                continue

            # Check if person is on FMIT next day (should skip PCAT/DO)
            fmit_check = (
                db_session.execute(
                    select(InpatientPreload).where(
                        and_(
                            InpatientPreload.person_id == call.person_id,
                            InpatientPreload.start_date <= next_day,
                            InpatientPreload.end_date >= next_day,
                            InpatientPreload.rotation_type == "FMIT",
                        )
                    )
                )
                .scalars()
                .first()
            )

            if fmit_check:
                # FMIT faculty should NOT have PCAT/DO
                continue

            # Check PCAT (AM)
            pcat = (
                db_session.execute(
                    select(HalfDayAssignment).where(
                        and_(
                            HalfDayAssignment.person_id == call.person_id,
                            HalfDayAssignment.date == next_day,
                            HalfDayAssignment.time_of_day == "AM",
                            HalfDayAssignment.activity_id == pcat_activity.id,
                        )
                    )
                )
                .scalars()
                .first()
            )

            if not pcat:
                missing_pcat.append(f"{call.date} -> {next_day} AM")
            elif pcat.source != "preload":
                wrong_source.append(f"PCAT {next_day} has source={pcat.source}")

            # Check DO (PM)
            # Note: DO may be overwritten by another preload (e.g., call on same day)
            do = (
                db_session.execute(
                    select(HalfDayAssignment).where(
                        and_(
                            HalfDayAssignment.person_id == call.person_id,
                            HalfDayAssignment.date == next_day,
                            HalfDayAssignment.time_of_day == "PM",
                            HalfDayAssignment.activity_id == do_activity.id,
                        )
                    )
                )
                .scalars()
                .first()
            )

            if not do:
                # Check if there's another preload that took precedence
                other_preload = (
                    db_session.execute(
                        select(HalfDayAssignment).where(
                            and_(
                                HalfDayAssignment.person_id == call.person_id,
                                HalfDayAssignment.date == next_day,
                                HalfDayAssignment.time_of_day == "PM",
                                HalfDayAssignment.source == "preload",
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if not other_preload:
                    # Only flag as missing if no other preload took precedence
                    missing_do.append(f"{call.date} -> {next_day} PM")
            elif do.source != "preload":
                wrong_source.append(f"DO {next_day} has source={do.source}")

        # Assert no issues
        assert not missing_pcat, f"Missing PCAT for calls: {missing_pcat}"
        assert not missing_do, f"Missing DO for calls: {missing_do}"
        assert not wrong_source, f"Wrong source (should be 'preload'): {wrong_source}"

    @pytest.mark.integration
    def test_pcat_do_count_matches_call_count(self, db_session) -> None:
        """
        INTEGRATION TEST: Verify PCAT/DO count roughly matches call count.

        Each call should generate 1 PCAT and 1 DO (except FMIT and end-of-block).
        """
        from app.models.call_assignment import CallAssignment
        from app.models.half_day_assignment import HalfDayAssignment
        from app.models.activity import Activity
        from sqlalchemy import select, and_, func

        start_date = date(2026, 3, 12)
        end_date = date(2026, 4, 8)

        # Count call assignments
        call_count = db_session.execute(
            select(func.count(CallAssignment.id)).where(
                and_(
                    CallAssignment.date >= start_date,
                    CallAssignment.date <= end_date,
                )
            )
        ).scalar()

        if call_count == 0:
            pytest.skip("No call assignments - run generation first")

        # Get activity IDs
        pcat_activity = (
            db_session.execute(select(Activity).where(Activity.code == "pcat"))
            .scalars()
            .first()
        )
        do_activity = (
            db_session.execute(select(Activity).where(Activity.code == "do"))
            .scalars()
            .first()
        )

        # Count PCAT assignments
        pcat_count = db_session.execute(
            select(func.count(HalfDayAssignment.id)).where(
                and_(
                    HalfDayAssignment.date >= start_date,
                    HalfDayAssignment.date <= end_date + timedelta(days=1),
                    HalfDayAssignment.activity_id == pcat_activity.id,
                )
            )
        ).scalar()

        # Count DO assignments
        do_count = db_session.execute(
            select(func.count(HalfDayAssignment.id)).where(
                and_(
                    HalfDayAssignment.date >= start_date,
                    HalfDayAssignment.date <= end_date + timedelta(days=1),
                    HalfDayAssignment.activity_id == do_activity.id,
                )
            )
        ).scalar()

        # PCAT/DO should be close to call count (some may be skipped for FMIT)
        # Allow 20% variance for FMIT skips and end-of-block
        min_expected = int(call_count * 0.8)

        assert pcat_count >= min_expected, (
            f"PCAT count ({pcat_count}) too low for {call_count} calls"
        )
        assert do_count >= min_expected, (
            f"DO count ({do_count}) too low for {call_count} calls"
        )

    @pytest.mark.integration
    def test_fmit_faculty_no_pcat_do(self, db_session) -> None:
        """
        INTEGRATION TEST: FMIT faculty should NOT have PCAT/DO.

        When a faculty member is on FMIT, they continue coverage the next day
        instead of getting post-call time off.
        """
        from app.models.call_assignment import CallAssignment
        from app.models.half_day_assignment import HalfDayAssignment
        from app.models.activity import Activity
        from app.models.inpatient_preload import InpatientPreload
        from sqlalchemy import select, and_

        start_date = date(2026, 3, 12)
        end_date = date(2026, 4, 8)

        # Find call assignments where faculty is on FMIT the next day
        call_query = select(CallAssignment).where(
            and_(
                CallAssignment.date >= start_date,
                CallAssignment.date <= end_date,
            )
        )
        call_assignments = db_session.execute(call_query).scalars().all()

        pcat_activity = (
            db_session.execute(select(Activity).where(Activity.code == "pcat"))
            .scalars()
            .first()
        )

        incorrect_pcat = []

        for call in call_assignments:
            next_day = call.date + timedelta(days=1)

            # Check if on FMIT
            fmit = (
                db_session.execute(
                    select(InpatientPreload).where(
                        and_(
                            InpatientPreload.person_id == call.person_id,
                            InpatientPreload.start_date <= next_day,
                            InpatientPreload.end_date >= next_day,
                            InpatientPreload.rotation_type == "FMIT",
                        )
                    )
                )
                .scalars()
                .first()
            )

            if fmit:
                # Should NOT have PCAT
                pcat = (
                    db_session.execute(
                        select(HalfDayAssignment).where(
                            and_(
                                HalfDayAssignment.person_id == call.person_id,
                                HalfDayAssignment.date == next_day,
                                HalfDayAssignment.time_of_day == "AM",
                                HalfDayAssignment.activity_id == pcat_activity.id,
                            )
                        )
                    )
                    .scalars()
                    .first()
                )

                if pcat:
                    incorrect_pcat.append(
                        f"FMIT faculty has PCAT on {next_day} (call was {call.date})"
                    )

        assert not incorrect_pcat, (
            f"FMIT faculty should not have PCAT: {incorrect_pcat}"
        )
