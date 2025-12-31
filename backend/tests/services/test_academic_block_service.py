"""Tests for AcademicBlockService."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.schemas.academic_blocks import ACGMEStatus
from app.services.academic_block_service import AcademicBlockService
from app.validators.advanced_acgme import ACGMEViolation


class TestAcademicBlockService:
    """Test suite for AcademicBlockService."""

    # ========================================================================
    # Parse Academic Year Tests
    # ========================================================================

    def test_parse_academic_year_valid(self, db):
        """Test parsing a valid academic year string."""
        service = AcademicBlockService(db)
        start_date, end_date = service._parse_academic_year("2024-2025")

        assert start_date == date(2024, 7, 1)
        assert end_date == date(2025, 6, 30)

    def test_parse_academic_year_different_year(self, db):
        """Test parsing different academic years."""
        service = AcademicBlockService(db)

        # 2023-2024
        start, end = service._parse_academic_year("2023-2024")
        assert start == date(2023, 7, 1)
        assert end == date(2024, 6, 30)

        # 2025-2026
        start, end = service._parse_academic_year("2025-2026")
        assert start == date(2025, 7, 1)
        assert end == date(2026, 6, 30)

    def test_parse_academic_year_invalid_format_no_dash(self, db):
        """Test parsing academic year with invalid format (no dash)."""
        service = AcademicBlockService(db)

        with pytest.raises(ValueError, match="must be in format 'YYYY-YYYY'"):
            service._parse_academic_year("20242025")

    def test_parse_academic_year_invalid_format_wrong_separator(self, db):
        """Test parsing academic year with wrong separator."""
        service = AcademicBlockService(db)

        with pytest.raises(ValueError, match="must be in format 'YYYY-YYYY'"):
            service._parse_academic_year("2024/2025")

    def test_parse_academic_year_invalid_year_difference(self, db):
        """Test parsing academic year where years don't differ by 1."""
        service = AcademicBlockService(db)

        with pytest.raises(ValueError, match="end year must be start year \\+ 1"):
            service._parse_academic_year("2024-2026")

        with pytest.raises(ValueError, match="end year must be start year \\+ 1"):
            service._parse_academic_year("2024-2024")

    def test_parse_academic_year_invalid_non_numeric(self, db):
        """Test parsing academic year with non-numeric values."""
        service = AcademicBlockService(db)

        with pytest.raises(ValueError, match="Invalid academic year format"):
            service._parse_academic_year("abcd-efgh")

    def test_parse_academic_year_too_many_parts(self, db):
        """Test parsing academic year with too many parts."""
        service = AcademicBlockService(db)

        with pytest.raises(ValueError, match="must be in format 'YYYY-YYYY'"):
            service._parse_academic_year("2024-2025-2026")

    # ========================================================================
    # Generate Academic Blocks Tests
    # ========================================================================

    def test_generate_academic_blocks_full_year(self, db):
        """Test generating blocks for a full academic year."""
        service = AcademicBlockService(db)
        start_date = date(2024, 7, 1)
        end_date = date(2025, 6, 30)

        blocks = service._generate_academic_blocks(start_date, end_date)

        # Should generate 13 blocks (52 weeks / 4 weeks per block)
        assert len(blocks) == 13
        assert blocks[0].block_number == 1
        assert blocks[-1].block_number == 13

    def test_generate_academic_blocks_first_block_dates(self, db):
        """Test that first block has correct start and end dates."""
        service = AcademicBlockService(db)
        start_date = date(2024, 7, 1)
        end_date = date(2025, 6, 30)

        blocks = service._generate_academic_blocks(start_date, end_date)

        first_block = blocks[0]
        assert first_block.start_date == date(2024, 7, 1)
        # 28 days later (4 weeks)
        assert first_block.end_date == date(2024, 7, 28)
        assert first_block.name == "Block 1"

    def test_generate_academic_blocks_last_block_dates(self, db):
        """Test that last block respects the end date boundary."""
        service = AcademicBlockService(db)
        start_date = date(2024, 7, 1)
        end_date = date(2025, 6, 30)

        blocks = service._generate_academic_blocks(start_date, end_date)

        last_block = blocks[-1]
        assert last_block.end_date == end_date
        assert last_block.block_number == 13

    def test_generate_academic_blocks_contiguous_dates(self, db):
        """Test that blocks are contiguous with no gaps."""
        service = AcademicBlockService(db)
        start_date = date(2024, 7, 1)
        end_date = date(2025, 6, 30)

        blocks = service._generate_academic_blocks(start_date, end_date)

        for i in range(len(blocks) - 1):
            current_block = blocks[i]
            next_block = blocks[i + 1]

            # Next block should start the day after current block ends
            expected_next_start = current_block.end_date + timedelta(days=1)
            assert next_block.start_date == expected_next_start

    def test_generate_academic_blocks_partial_year(self, db):
        """Test generating blocks for partial academic year."""
        service = AcademicBlockService(db)
        # 8 weeks (2 blocks)
        start_date = date(2024, 7, 1)
        end_date = date(2024, 8, 25)

        blocks = service._generate_academic_blocks(start_date, end_date)

        assert len(blocks) == 2
        assert blocks[0].block_number == 1
        assert blocks[1].block_number == 2

    def test_generate_academic_blocks_single_day(self, db):
        """Test generating blocks for a single day."""
        service = AcademicBlockService(db)
        start_date = date(2024, 7, 1)
        end_date = date(2024, 7, 1)

        blocks = service._generate_academic_blocks(start_date, end_date)

        assert len(blocks) == 1
        assert blocks[0].start_date == start_date
        assert blocks[0].end_date == end_date

    def test_generate_academic_blocks_block_names(self, db):
        """Test that block names are correctly formatted."""
        service = AcademicBlockService(db)
        start_date = date(2024, 7, 1)
        end_date = date(2024, 9, 30)

        blocks = service._generate_academic_blocks(start_date, end_date)

        assert blocks[0].name == "Block 1"
        assert blocks[1].name == "Block 2"
        assert blocks[2].name == "Block 3"

    # ========================================================================
    # Get Residents Tests
    # ========================================================================

    def test_get_residents_all(self, db, sample_residents):
        """Test getting all residents without filter."""
        service = AcademicBlockService(db)
        residents = service._get_residents()

        assert len(residents) == 3
        # Verify ResidentRow schema
        assert all(hasattr(r, "resident_id") for r in residents)
        assert all(hasattr(r, "name") for r in residents)
        assert all(hasattr(r, "pgy_level") for r in residents)

    def test_get_residents_filter_by_pgy(self, db, sample_residents):
        """Test filtering residents by PGY level."""
        service = AcademicBlockService(db)

        # Filter for PGY-2
        pgy2_residents = service._get_residents(pgy_level=2)
        assert len(pgy2_residents) == 1
        assert pgy2_residents[0].pgy_level == 2

        # Filter for PGY-1
        pgy1_residents = service._get_residents(pgy_level=1)
        assert len(pgy1_residents) == 1
        assert pgy1_residents[0].pgy_level == 1

    def test_get_residents_empty_when_no_residents(self, db):
        """Test getting residents when none exist."""
        service = AcademicBlockService(db)
        residents = service._get_residents()

        assert len(residents) == 0

    def test_get_residents_filter_nonexistent_pgy(self, db, sample_residents):
        """Test filtering by PGY level that doesn't exist."""
        service = AcademicBlockService(db)
        residents = service._get_residents(pgy_level=5)

        assert len(residents) == 0

    # ========================================================================
    # Get Assignments in Range Tests
    # ========================================================================

    def test_get_assignments_in_range_with_data(self, db, sample_assignment):
        """Test getting assignments in date range."""
        service = AcademicBlockService(db)
        block_date = sample_assignment.block.date

        assignments = service._get_assignments_in_range(
            start_date=block_date - timedelta(days=1),
            end_date=block_date + timedelta(days=1),
        )

        assert len(assignments) == 1
        assert assignments[0].id == sample_assignment.id
        # Verify eager loading worked
        assert assignments[0].block is not None
        assert assignments[0].person is not None

    def test_get_assignments_in_range_exact_boundaries(self, db):
        """Test that date range is inclusive on both boundaries."""
        service = AcademicBlockService(db)

        # Create blocks and assignments on specific dates
        resident = Person(
            id=uuid4(),
            name="Test Resident",
            type="resident",
            email="test@test.org",
            pgy_level=1,
        )
        db.add(resident)

        rotation = RotationTemplate(
            id=uuid4(),
            name="Test Rotation",
            activity_type="outpatient",
        )
        db.add(rotation)

        # Create 3 blocks on consecutive days
        dates = [date(2024, 7, 1), date(2024, 7, 2), date(2024, 7, 3)]
        for d in dates:
            block = Block(
                id=uuid4(),
                date=d,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.flush()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=resident.id,
                rotation_template_id=rotation.id,
            )
            db.add(assignment)

        db.commit()

        # Query for middle date only
        assignments = service._get_assignments_in_range(
            start_date=date(2024, 7, 2),
            end_date=date(2024, 7, 2),
        )

        assert len(assignments) == 1

        # Query for all three dates
        assignments = service._get_assignments_in_range(
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 3),
        )

        assert len(assignments) == 3

    def test_get_assignments_in_range_empty(self, db):
        """Test getting assignments when none exist in range."""
        service = AcademicBlockService(db)

        assignments = service._get_assignments_in_range(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        assert len(assignments) == 0

    # ========================================================================
    # Get Primary Rotation Tests
    # ========================================================================

    def test_get_primary_rotation_single_rotation(self, db, sample_rotation_template):
        """Test getting primary rotation when only one rotation exists."""
        service = AcademicBlockService(db)

        # Create assignment with rotation template
        assignment = Assignment(
            id=uuid4(),
            rotation_template_id=sample_rotation_template.id,
            rotation_template=sample_rotation_template,
        )

        abbr, full_name = service._get_primary_rotation([assignment])

        assert abbr == "SM"  # From sample_rotation_template
        assert full_name == "Sports Medicine Clinic"

    def test_get_primary_rotation_multiple_same(self, db, sample_rotation_template):
        """Test primary rotation with multiple assignments to same rotation."""
        service = AcademicBlockService(db)

        # Create multiple assignments to same rotation
        assignments = [
            Assignment(
                id=uuid4(),
                rotation_template_id=sample_rotation_template.id,
                rotation_template=sample_rotation_template,
            )
            for _ in range(5)
        ]

        abbr, full_name = service._get_primary_rotation(assignments)

        assert abbr == "SM"
        assert full_name == "Sports Medicine Clinic"

    def test_get_primary_rotation_multiple_different_picks_most_common(self, db):
        """Test primary rotation picks the most common rotation."""
        service = AcademicBlockService(db)

        # Create two rotation templates
        rotation1 = RotationTemplate(
            id=uuid4(),
            name="Clinic A",
            abbreviation="CA",
            activity_type="outpatient",
        )
        rotation2 = RotationTemplate(
            id=uuid4(),
            name="Clinic B",
            abbreviation="CB",
            activity_type="outpatient",
        )

        # 3 assignments to rotation1, 2 to rotation2
        assignments = (
            [
                Assignment(
                    id=uuid4(),
                    rotation_template_id=rotation1.id,
                    rotation_template=rotation1,
                )
                for _ in range(3)
            ]
            + [
                Assignment(
                    id=uuid4(),
                    rotation_template_id=rotation2.id,
                    rotation_template=rotation2,
                )
                for _ in range(2)
            ]
        )

        abbr, full_name = service._get_primary_rotation(assignments)

        assert abbr == "CA"
        assert full_name == "Clinic A"

    def test_get_primary_rotation_with_activity_override(self, db):
        """Test primary rotation uses activity_override when no rotation template."""
        service = AcademicBlockService(db)

        assignments = [
            Assignment(
                id=uuid4(),
                rotation_template=None,
                activity_override="Vacation",
            )
        ]

        abbr, full_name = service._get_primary_rotation(assignments)

        assert abbr == "VAC"  # First 3 chars uppercase
        assert full_name == "Vacation"

    def test_get_primary_rotation_mixed_template_and_override(self, db):
        """Test primary rotation with mix of templates and overrides."""
        service = AcademicBlockService(db)

        rotation = RotationTemplate(
            id=uuid4(),
            name="Clinic",
            abbreviation="CLI",
            activity_type="outpatient",
        )

        # 2 with template, 3 with override
        assignments = [
            Assignment(
                id=uuid4(),
                rotation_template_id=rotation.id,
                rotation_template=rotation,
            ),
            Assignment(
                id=uuid4(),
                rotation_template_id=rotation.id,
                rotation_template=rotation,
            ),
            Assignment(id=uuid4(), rotation_template=None, activity_override="Leave"),
            Assignment(id=uuid4(), rotation_template=None, activity_override="Leave"),
            Assignment(id=uuid4(), rotation_template=None, activity_override="Leave"),
        ]

        abbr, full_name = service._get_primary_rotation(assignments)

        # "Leave" appears 3 times vs "CLI" 2 times
        assert abbr == "LEA"
        assert full_name == "Leave"

    def test_get_primary_rotation_empty_assignments(self, db):
        """Test primary rotation with empty assignment list."""
        service = AcademicBlockService(db)

        abbr, full_name = service._get_primary_rotation([])

        assert abbr is None
        assert full_name is None

    def test_get_primary_rotation_no_abbreviation_uses_first_three_chars(self, db):
        """Test rotation without abbreviation uses first 3 chars of name."""
        service = AcademicBlockService(db)

        rotation = RotationTemplate(
            id=uuid4(),
            name="Surgery",
            abbreviation=None,  # No abbreviation
            activity_type="outpatient",
        )

        assignment = Assignment(
            id=uuid4(),
            rotation_template_id=rotation.id,
            rotation_template=rotation,
        )

        abbr, full_name = service._get_primary_rotation([assignment])

        assert abbr == "SUR"  # First 3 chars of "Surgery"
        assert full_name == "Surgery"

    # ========================================================================
    # Check ACGME Compliance Tests
    # ========================================================================

    def test_check_acgme_compliance_compliant(self, db, sample_resident):
        """Test ACGME compliance check for compliant hours."""
        service = AcademicBlockService(db)

        block = type(
            "Block",
            (),
            {
                "start_date": date(2024, 7, 1),
                "end_date": date(2024, 7, 28),
            },
        )

        # 70 hours per week average (compliant)
        hours = 70 * 4  # 280 hours over 4 weeks

        status = service._check_acgme_compliance(
            resident_id=sample_resident.id,
            block=block,
            hours=hours,
        )

        assert status.is_compliant is True
        assert len(status.violations) == 0
        assert status.hours_worked == hours

    def test_check_acgme_compliance_violation_over_80_hours(self, db, sample_resident):
        """Test ACGME compliance violation for over 80 hours/week."""
        service = AcademicBlockService(db)

        block = type(
            "Block",
            (),
            {
                "start_date": date(2024, 7, 1),
                "end_date": date(2024, 7, 28),
            },
        )

        # 85 hours per week average (violation)
        hours = 85 * 4  # 340 hours over 4 weeks

        status = service._check_acgme_compliance(
            resident_id=sample_resident.id,
            block=block,
            hours=hours,
        )

        assert status.is_compliant is False
        assert len(status.violations) > 0
        assert "Average weekly hours" in status.violations[0]
        assert "exceeds ACGME limit" in status.violations[0]

    def test_check_acgme_compliance_warning_approaching_limit(self, db, sample_resident):
        """Test ACGME compliance warning for hours approaching limit."""
        service = AcademicBlockService(db)

        block = type(
            "Block",
            (),
            {
                "start_date": date(2024, 7, 1),
                "end_date": date(2024, 7, 28),
            },
        )

        # 77 hours per week (warning range: 75-80)
        hours = 77 * 4  # 308 hours over 4 weeks

        status = service._check_acgme_compliance(
            resident_id=sample_resident.id,
            block=block,
            hours=hours,
        )

        assert status.is_compliant is True  # Still compliant
        assert len(status.violations) == 0
        assert len(status.warnings) > 0
        assert "approaching ACGME limit" in status.warnings[0]

    @patch("app.services.academic_block_service.AdvancedACGMEValidator")
    def test_check_acgme_compliance_with_validator_violations(
        self, mock_validator_class, db, sample_resident
    ):
        """Test ACGME compliance with advanced validator violations."""
        # Setup mock validator
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        # Mock violation from 24+4 rule
        violation = ACGMEViolation(
            rule_name="24_plus_4_rule",
            person_id=str(sample_resident.id),
            date=date(2024, 7, 5),
            message="Exceeded 24+4 continuous duty limit",
        )
        mock_validator.validate_24_plus_4_rule.return_value = [violation]
        mock_validator.validate_night_float_limits.return_value = []
        mock_validator.validate_pgy_specific_rules.return_value = []

        service = AcademicBlockService(db)
        service.acgme_validator = mock_validator

        block = type(
            "Block",
            (),
            {
                "start_date": date(2024, 7, 1),
                "end_date": date(2024, 7, 28),
            },
        )

        status = service._check_acgme_compliance(
            resident_id=sample_resident.id,
            block=block,
            hours=280,
        )

        assert status.is_compliant is False
        assert "Exceeded 24+4 continuous duty limit" in status.violations

    @patch("app.services.academic_block_service.AdvancedACGMEValidator")
    def test_check_acgme_compliance_validator_exception_handled(
        self, mock_validator_class, db, sample_resident
    ):
        """Test that exceptions from ACGME validator are handled gracefully."""
        # Setup mock validator that raises exception
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_validator.validate_24_plus_4_rule.side_effect = Exception(
            "Validator error"
        )

        service = AcademicBlockService(db)
        service.acgme_validator = mock_validator

        block = type(
            "Block",
            (),
            {
                "start_date": date(2024, 7, 1),
                "end_date": date(2024, 7, 28),
            },
        )

        status = service._check_acgme_compliance(
            resident_id=sample_resident.id,
            block=block,
            hours=280,
        )

        # Should not crash, but add warning
        assert len(status.warnings) > 0
        assert "Error checking ACGME compliance" in status.warnings[0]

    # ========================================================================
    # Calculate Matrix Summary Tests
    # ========================================================================

    def test_calculate_matrix_summary_basic(self, db, sample_residents):
        """Test calculating matrix summary statistics."""
        service = AcademicBlockService(db)

        # Create mock residents
        residents = service._get_residents()

        # Create mock cells (all compliant)
        cells = [
            type(
                "MatrixCell",
                (),
                {
                    "row_index": 0,
                    "column_index": i,
                    "rotation": "CLI",
                    "hours": 280.0,
                    "acgme_status": ACGMEStatus(
                        is_compliant=True,
                        warnings=[],
                        violations=[],
                        hours_worked=280.0,
                        max_hours_allowed=320.0,
                    ),
                },
            )
            for i in range(13)  # 13 blocks
        ]

        summary = service._calculate_matrix_summary(residents, cells)

        assert summary["total_residents"] == 3
        assert summary["total_blocks"] == 13
        assert summary["total_assignments"] == 13
        assert summary["compliance_rate"] == 100.0
        assert summary["compliant_cells"] == 13
        assert summary["non_compliant_cells"] == 0

    def test_calculate_matrix_summary_with_violations(self, db, sample_residents):
        """Test matrix summary with some non-compliant cells."""
        service = AcademicBlockService(db)

        residents = service._get_residents()

        # 10 compliant, 3 non-compliant
        compliant_cells = [
            type(
                "MatrixCell",
                (),
                {
                    "row_index": 0,
                    "column_index": i,
                    "rotation": "CLI",
                    "hours": 280.0,
                    "acgme_status": ACGMEStatus(
                        is_compliant=True,
                        warnings=[],
                        violations=[],
                        hours_worked=280.0,
                        max_hours_allowed=320.0,
                    ),
                },
            )
            for i in range(10)
        ]

        non_compliant_cells = [
            type(
                "MatrixCell",
                (),
                {
                    "row_index": 0,
                    "column_index": i,
                    "rotation": "CLI",
                    "hours": 400.0,
                    "acgme_status": ACGMEStatus(
                        is_compliant=False,
                        warnings=[],
                        violations=["Exceeds limit"],
                        hours_worked=400.0,
                        max_hours_allowed=320.0,
                    ),
                },
            )
            for i in range(10, 13)
        ]

        cells = compliant_cells + non_compliant_cells

        summary = service._calculate_matrix_summary(residents, cells)

        assert summary["compliant_cells"] == 10
        assert summary["non_compliant_cells"] == 3
        assert summary["compliance_rate"] == pytest.approx(76.92, rel=0.1)

    def test_calculate_matrix_summary_empty_cells(self, db):
        """Test matrix summary with no cells."""
        service = AcademicBlockService(db)

        summary = service._calculate_matrix_summary([], [])

        assert summary["total_residents"] == 0
        assert summary["total_blocks"] == 0
        assert summary["compliance_rate"] == 0

    # ========================================================================
    # Calculate Block Summary Tests
    # ========================================================================

    def test_calculate_block_summary_with_assignments(
        self, db, sample_residents, sample_rotation_template
    ):
        """Test calculating block summary with assignments."""
        service = AcademicBlockService(db)

        # Create block
        block = type(
            "Block",
            (),
            {
                "block_number": 1,
                "name": "Block 1",
                "start_date": date(2024, 7, 1),
                "end_date": date(2024, 7, 28),
            },
        )

        # Create blocks and assignments
        resident = sample_residents[0]
        blocks_list = []
        assignments = []

        for i in range(28):
            block_date = date(2024, 7, 1) + timedelta(days=i)
            for time_of_day in ["AM", "PM"]:
                db_block = Block(
                    id=uuid4(),
                    date=block_date,
                    time_of_day=time_of_day,
                    block_number=1,
                )
                db.add(db_block)
                blocks_list.append(db_block)

        db.flush()

        for db_block in blocks_list:
            assignment = Assignment(
                id=uuid4(),
                block_id=db_block.id,
                person_id=resident.id,
                rotation_template_id=sample_rotation_template.id,
            )
            db.add(assignment)
            assignment.block = db_block  # Set relationship
            assignments.append(assignment)

        db.commit()

        # Refresh to get relationships
        for a in assignments:
            db.refresh(a)

        summary = service._calculate_block_summary(block, assignments)

        assert summary.block_number == 1
        assert summary.name == "Block 1"
        assert summary.total_assignments == 56  # 28 days * 2 times
        assert summary.total_residents == 1
        assert summary.compliance_rate == 100.0  # Within limits

    def test_calculate_block_summary_empty_assignments(self, db):
        """Test calculating block summary with no assignments."""
        service = AcademicBlockService(db)

        block = type(
            "Block",
            (),
            {
                "block_number": 1,
                "name": "Block 1",
                "start_date": date(2024, 7, 1),
                "end_date": date(2024, 7, 28),
            },
        )

        summary = service._calculate_block_summary(block, [])

        assert summary.total_assignments == 0
        assert summary.total_residents == 0
        assert summary.compliance_rate == 100.0  # No violations
        assert summary.average_hours == 0.0

    # ========================================================================
    # List Academic Blocks Tests
    # ========================================================================

    def test_list_academic_blocks_full_year(self, db):
        """Test listing academic blocks for full year."""
        service = AcademicBlockService(db)

        response = service.list_academic_blocks("2024-2025")

        assert response.academic_year == "2024-2025"
        assert response.total_blocks == 13
        assert len(response.blocks) == 13
        assert response.blocks[0].block_number == 1
        assert response.blocks[-1].block_number == 13

    def test_list_academic_blocks_validates_year_format(self, db):
        """Test that list_academic_blocks validates year format."""
        service = AcademicBlockService(db)

        with pytest.raises(ValueError):
            service.list_academic_blocks("invalid-year")

    def test_list_academic_blocks_block_summaries_structure(self, db):
        """Test that block summaries have correct structure."""
        service = AcademicBlockService(db)

        response = service.list_academic_blocks("2024-2025")

        for block_summary in response.blocks:
            assert hasattr(block_summary, "block_number")
            assert hasattr(block_summary, "name")
            assert hasattr(block_summary, "start_date")
            assert hasattr(block_summary, "end_date")
            assert hasattr(block_summary, "total_assignments")
            assert hasattr(block_summary, "total_residents")
            assert hasattr(block_summary, "compliance_rate")
            assert hasattr(block_summary, "average_hours")

    # ========================================================================
    # Get Block Matrix Tests
    # ========================================================================

    def test_get_block_matrix_structure(self, db, sample_residents):
        """Test that block matrix has correct structure."""
        service = AcademicBlockService(db)

        response = service.get_block_matrix("2024-2025")

        assert response.academic_year == "2024-2025"
        assert len(response.columns) == 13  # 13 blocks
        assert len(response.rows) == 3  # 3 residents
        # 3 residents × 13 blocks = 39 cells
        assert len(response.cells) == 39
        assert isinstance(response.summary, dict)

    def test_get_block_matrix_filter_by_pgy(self, db, sample_residents):
        """Test filtering block matrix by PGY level."""
        service = AcademicBlockService(db)

        # Filter for PGY-2 only
        response = service.get_block_matrix("2024-2025", pgy_level=2)

        assert len(response.rows) == 1
        assert response.rows[0].pgy_level == 2
        # 1 resident × 13 blocks = 13 cells
        assert len(response.cells) == 13

    def test_get_block_matrix_with_assignments(
        self, db, sample_residents, sample_rotation_template
    ):
        """Test block matrix with actual assignments."""
        service = AcademicBlockService(db)

        # Create blocks and assignments for first week of academic year
        resident = sample_residents[0]
        start_date = date(2024, 7, 1)

        for i in range(7):
            block_date = start_date + timedelta(days=i)
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=block_date,
                    time_of_day=time_of_day,
                    block_number=1,
                )
                db.add(block)
                db.flush()

                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=resident.id,
                    rotation_template_id=sample_rotation_template.id,
                )
                db.add(assignment)

        db.commit()

        response = service.get_block_matrix("2024-2025")

        # First cell (resident 0, block 0) should have rotation info
        first_cell = next(
            (c for c in response.cells if c.row_index == 0 and c.column_index == 0),
            None,
        )
        assert first_cell is not None
        assert first_cell.rotation == "SM"  # From sample_rotation_template
        assert first_cell.hours == 84.0  # 7 days * 2 times * 6 hours

    def test_get_block_matrix_empty_no_residents(self, db):
        """Test block matrix with no residents."""
        service = AcademicBlockService(db)

        response = service.get_block_matrix("2024-2025")

        assert len(response.rows) == 0
        assert len(response.cells) == 0
        assert response.summary["total_residents"] == 0

    def test_get_block_matrix_validates_year(self, db):
        """Test that get_block_matrix validates academic year format."""
        service = AcademicBlockService(db)

        with pytest.raises(ValueError):
            service.get_block_matrix("invalid")

    def test_get_block_matrix_summary_statistics(self, db, sample_residents):
        """Test that matrix summary includes expected statistics."""
        service = AcademicBlockService(db)

        response = service.get_block_matrix("2024-2025")

        assert "total_residents" in response.summary
        assert "total_blocks" in response.summary
        assert "compliance_rate" in response.summary
        assert "total_hours" in response.summary
        assert "average_hours_per_resident" in response.summary
        assert "compliant_cells" in response.summary
        assert "non_compliant_cells" in response.summary

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_full_workflow_with_real_data(
        self, db, sample_residents, sample_rotation_template
    ):
        """Test full workflow: create data, generate matrix, verify results."""
        service = AcademicBlockService(db)

        # Create blocks for first block period (28 days)
        start_date = date(2024, 7, 1)
        for i in range(28):
            block_date = start_date + timedelta(days=i)
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=block_date,
                    time_of_day=time_of_day,
                    block_number=1,
                )
                db.add(block)
                db.flush()

                # Assign all residents to this block
                for resident in sample_residents:
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=block.id,
                        person_id=resident.id,
                        rotation_template_id=sample_rotation_template.id,
                    )
                    db.add(assignment)

        db.commit()

        # Generate matrix
        response = service.get_block_matrix("2024-2025")

        # Verify results
        assert len(response.rows) == 3  # All residents
        assert len(response.columns) == 13  # All blocks
        assert response.summary["total_residents"] == 3

        # First block should have all residents assigned
        first_block_cells = [c for c in response.cells if c.column_index == 0]
        assert len(first_block_cells) == 3
        assert all(c.rotation == "SM" for c in first_block_cells)
        # 28 days * 2 times * 6 hours = 336 hours
        assert all(c.hours == 336.0 for c in first_block_cells)

    def test_constants_are_correct(self, db):
        """Test that service constants match expected values."""
        service = AcademicBlockService(db)

        assert service.BLOCK_DURATION_WEEKS == 4
        assert service.BLOCK_DURATION_DAYS == 28
        assert service.HOURS_PER_HALF_DAY == 6
        assert service.MAX_WEEKLY_HOURS_ACGME == 80
        assert service.EXPECTED_BLOCKS_PER_YEAR == 13
