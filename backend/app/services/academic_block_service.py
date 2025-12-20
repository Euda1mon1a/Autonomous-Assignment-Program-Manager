"""
Academic block service for business logic.

Handles grouping of daily scheduling blocks into rotation periods
and generating block matrix views for program coordinators.
"""
from collections import defaultdict
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.models.assignment import Assignment
from app.models.block import Block
from app.repositories.assignment import AssignmentRepository
from app.repositories.block import BlockRepository
from app.repositories.person import PersonRepository
from app.schemas.academic_blocks import (
    AcademicBlock,
    ACGMEStatus,
    BlockListResponse,
    BlockMatrixResponse,
    BlockSummary,
    MatrixCell,
    ResidentRow,
)
from app.validators.advanced_acgme import AdvancedACGMEValidator


class AcademicBlockService:
    """Service for academic block matrix operations."""

    # Constants
    BLOCK_DURATION_WEEKS = 4
    BLOCK_DURATION_DAYS = 28  # 4 weeks
    HOURS_PER_HALF_DAY = 6
    MAX_WEEKLY_HOURS_ACGME = 80  # ACGME limit
    EXPECTED_BLOCKS_PER_YEAR = 13  # 52 weeks / 4 weeks per block

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.assignment_repo = AssignmentRepository(db)
        self.block_repo = BlockRepository(db)
        self.person_repo = PersonRepository(db)
        self.acgme_validator = AdvancedACGMEValidator(db)

    def get_block_matrix(
        self,
        academic_year: str,
        pgy_level: Optional[int] = None,
    ) -> BlockMatrixResponse:
        """
        Get academic block matrix for program coordinators.

        Groups daily assignments into rotation blocks and calculates
        ACGME compliance for each resident per block.

        Args:
            academic_year: Academic year (e.g., "2024-2025")
            pgy_level: Optional filter by PGY level

        Returns:
            BlockMatrixResponse with complete matrix data
        """
        # Parse academic year and generate blocks
        start_date, end_date = self._parse_academic_year(academic_year)
        academic_blocks = self._generate_academic_blocks(start_date, end_date)

        # Get residents (rows)
        residents = self._get_residents(pgy_level)

        # Get all assignments for the date range
        assignments = self._get_assignments_in_range(start_date, end_date)

        # Build matrix cells
        cells = self._build_matrix_cells(
            residents=residents,
            academic_blocks=academic_blocks,
            assignments=assignments,
            start_date=start_date,
            end_date=end_date,
        )

        # Calculate summary statistics
        summary = self._calculate_matrix_summary(residents, cells)

        return BlockMatrixResponse(
            columns=academic_blocks,
            rows=residents,
            cells=cells,
            academic_year=academic_year,
            summary=summary,
        )

    def list_academic_blocks(self, academic_year: str) -> BlockListResponse:
        """
        List all academic blocks for the year with summary statistics.

        Args:
            academic_year: Academic year (e.g., "2024-2025")

        Returns:
            BlockListResponse with block summaries
        """
        # Parse academic year and generate blocks
        start_date, end_date = self._parse_academic_year(academic_year)
        academic_blocks = self._generate_academic_blocks(start_date, end_date)

        # Get all assignments for the date range
        assignments = self._get_assignments_in_range(start_date, end_date)

        # Build block summaries
        block_summaries = []
        for block in academic_blocks:
            summary = self._calculate_block_summary(
                block=block,
                assignments=assignments,
            )
            block_summaries.append(summary)

        return BlockListResponse(
            blocks=block_summaries,
            academic_year=academic_year,
            total_blocks=len(block_summaries),
        )

    def _parse_academic_year(self, academic_year: str) -> tuple[date, date]:
        """
        Parse academic year string to get start and end dates.

        Academic years typically run from July 1 to June 30.

        Args:
            academic_year: String like "2024-2025"

        Returns:
            Tuple of (start_date, end_date)

        Raises:
            ValueError: If academic year format is invalid
        """
        try:
            parts = academic_year.split("-")
            if len(parts) != 2:
                raise ValueError(
                    "Academic year must be in format 'YYYY-YYYY' (e.g., '2024-2025')"
                )

            start_year = int(parts[0])
            end_year = int(parts[1])

            if end_year != start_year + 1:
                raise ValueError(
                    f"Invalid academic year: end year must be start year + 1"
                )

            # Academic year: July 1 of start year to June 30 of end year
            start_date = date(start_year, 7, 1)
            end_date = date(end_year, 6, 30)

            return start_date, end_date

        except (ValueError, IndexError) as e:
            raise ValueError(
                f"Invalid academic year format '{academic_year}': {str(e)}"
            )

    def _generate_academic_blocks(
        self, start_date: date, end_date: date
    ) -> list[AcademicBlock]:
        """
        Generate academic blocks (rotation periods) from date range.

        Divides the academic year into ~13 blocks of 4 weeks each.

        Args:
            start_date: Start of academic year
            end_date: End of academic year

        Returns:
            List of AcademicBlock objects
        """
        blocks = []
        current_date = start_date
        block_number = 1

        while current_date <= end_date:
            # Calculate block end date (4 weeks from start)
            block_end = min(
                current_date + timedelta(days=self.BLOCK_DURATION_DAYS - 1),
                end_date,
            )

            blocks.append(
                AcademicBlock(
                    block_number=block_number,
                    start_date=current_date,
                    end_date=block_end,
                    name=f"Block {block_number}",
                )
            )

            # Move to next block
            current_date = block_end + timedelta(days=1)
            block_number += 1

        return blocks

    def _get_residents(self, pgy_level: Optional[int] = None) -> list[ResidentRow]:
        """
        Get residents for matrix rows.

        Args:
            pgy_level: Optional PGY level filter

        Returns:
            List of ResidentRow objects
        """
        # Query residents
        residents = self.person_repo.list_residents(pgy_level=pgy_level)

        # Convert to ResidentRow schema
        return [
            ResidentRow(
                resident_id=resident.id,
                name=resident.name,
                pgy_level=resident.pgy_level,
            )
            for resident in residents
        ]

    def _get_assignments_in_range(
        self, start_date: date, end_date: date
    ) -> list[Assignment]:
        """
        Get all assignments in the date range with eager loading.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of Assignment objects
        """
        assignments = (
            self.db.query(Assignment)
            .join(Block)
            .options(
                joinedload(Assignment.block),
                joinedload(Assignment.person),
                joinedload(Assignment.rotation_template),
            )
            .filter(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .all()
        )
        return assignments

    def _build_matrix_cells(
        self,
        residents: list[ResidentRow],
        academic_blocks: list[AcademicBlock],
        assignments: list[Assignment],
        start_date: date,
        end_date: date,
    ) -> list[MatrixCell]:
        """
        Build matrix cells from residents, blocks, and assignments.

        Args:
            residents: List of residents (rows)
            academic_blocks: List of academic blocks (columns)
            assignments: All assignments in the period
            start_date: Academic year start date
            end_date: Academic year end date

        Returns:
            List of MatrixCell objects
        """
        cells = []

        # Index assignments by person and date for quick lookup
        assignments_by_person = defaultdict(list)
        for assignment in assignments:
            assignments_by_person[assignment.person_id].append(assignment)

        # Build cells for each resident × block combination
        for row_idx, resident in enumerate(residents):
            resident_assignments = assignments_by_person[resident.resident_id]

            for col_idx, block in enumerate(academic_blocks):
                cell = self._build_matrix_cell(
                    row_index=row_idx,
                    column_index=col_idx,
                    resident=resident,
                    block=block,
                    assignments=resident_assignments,
                )
                cells.append(cell)

        return cells

    def _build_matrix_cell(
        self,
        row_index: int,
        column_index: int,
        resident: ResidentRow,
        block: AcademicBlock,
        assignments: list[Assignment],
    ) -> MatrixCell:
        """
        Build a single matrix cell for a resident in a specific block.

        Args:
            row_index: Row index in matrix
            column_index: Column index in matrix
            resident: Resident information
            block: Academic block
            assignments: All assignments for this resident

        Returns:
            MatrixCell with rotation and compliance info
        """
        # Filter assignments to this block period
        block_assignments = [
            a for a in assignments
            if a.block and block.start_date <= a.block.date <= block.end_date
        ]

        # Calculate hours
        total_hours = len(block_assignments) * self.HOURS_PER_HALF_DAY

        # Determine primary rotation (most common rotation in this block)
        rotation_name, rotation_full_name = self._get_primary_rotation(
            block_assignments
        )

        # Check ACGME compliance
        acgme_status = self._check_acgme_compliance(
            resident_id=resident.resident_id,
            block=block,
            hours=total_hours,
        )

        return MatrixCell(
            row_index=row_index,
            column_index=column_index,
            rotation=rotation_name,
            rotation_full_name=rotation_full_name,
            hours=total_hours,
            acgme_status=acgme_status,
        )

    def _get_primary_rotation(
        self, assignments: list[Assignment]
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Get the primary rotation from a list of assignments.

        Returns the most common rotation in the assignments.

        Args:
            assignments: List of assignments

        Returns:
            Tuple of (abbreviation, full_name)
        """
        if not assignments:
            return None, None

        # Count rotations
        rotation_counts = defaultdict(int)
        rotation_names = {}

        for assignment in assignments:
            if assignment.rotation_template:
                abbr = assignment.rotation_template.abbreviation or assignment.rotation_template.name[:3].upper()
                full_name = assignment.rotation_template.name
                rotation_counts[abbr] += 1
                rotation_names[abbr] = full_name
            elif assignment.activity_override:
                abbr = assignment.activity_override[:3].upper()
                rotation_counts[abbr] += 1
                rotation_names[abbr] = assignment.activity_override

        # Get most common rotation
        if rotation_counts:
            primary_abbr = max(rotation_counts.keys(), key=lambda k: rotation_counts[k])
            return primary_abbr, rotation_names.get(primary_abbr)

        return None, None

    def _check_acgme_compliance(
        self,
        resident_id: UUID,
        block: AcademicBlock,
        hours: float,
    ) -> ACGMEStatus:
        """
        Check ACGME compliance for a resident in a specific block.

        Args:
            resident_id: Resident UUID
            block: Academic block
            hours: Total hours in block

        Returns:
            ACGMEStatus with compliance information
        """
        warnings = []
        violations = []

        # Calculate weeks in block
        block_days = (block.end_date - block.start_date).days + 1
        weeks = max(1, block_days / 7)
        avg_weekly_hours = hours / weeks

        # Check weekly hours limit (80 hours/week averaged over 4 weeks)
        max_hours_allowed = self.MAX_WEEKLY_HOURS_ACGME * weeks

        if avg_weekly_hours > self.MAX_WEEKLY_HOURS_ACGME:
            violations.append(
                f"Average weekly hours ({avg_weekly_hours:.1f}h) exceeds ACGME limit ({self.MAX_WEEKLY_HOURS_ACGME}h)"
            )

        # Run advanced ACGME validations
        try:
            # 24+4 hour rule violations
            duty_violations = self.acgme_validator.validate_24_plus_4_rule(
                person_id=str(resident_id),
                start_date=block.start_date,
                end_date=block.end_date,
            )
            for v in duty_violations:
                violations.append(v.message)

            # Night float violations
            night_violations = self.acgme_validator.validate_night_float_limits(
                person_id=str(resident_id),
                start_date=block.start_date,
                end_date=block.end_date,
            )
            for v in night_violations:
                violations.append(v.message)

            # PGY-specific violations
            pgy_violations = self.acgme_validator.validate_pgy_specific_rules(
                person_id=str(resident_id),
                start_date=block.start_date,
                end_date=block.end_date,
            )
            for v in pgy_violations:
                violations.append(v.message)

        except Exception as e:
            # Log error but don't fail the entire request
            warnings.append(f"Error checking ACGME compliance: {str(e)}")

        # Warnings for approaching limits
        if 75 <= avg_weekly_hours <= self.MAX_WEEKLY_HOURS_ACGME:
            warnings.append(
                f"Average weekly hours ({avg_weekly_hours:.1f}h) approaching ACGME limit"
            )

        is_compliant = len(violations) == 0

        return ACGMEStatus(
            is_compliant=is_compliant,
            warnings=warnings,
            violations=violations,
            hours_worked=hours,
            max_hours_allowed=max_hours_allowed,
        )

    def _calculate_matrix_summary(
        self, residents: list[ResidentRow], cells: list[MatrixCell]
    ) -> dict:
        """
        Calculate summary statistics for the matrix.

        Args:
            residents: List of residents
            cells: List of matrix cells

        Returns:
            Dictionary with summary statistics
        """
        total_cells = len(cells)
        compliant_cells = sum(1 for cell in cells if cell.acgme_status.is_compliant)
        compliance_rate = (compliant_cells / total_cells * 100) if total_cells > 0 else 0

        total_hours = sum(cell.hours for cell in cells)
        avg_hours = total_hours / len(residents) if residents else 0

        return {
            "total_residents": len(residents),
            "total_blocks": len(set(cell.column_index for cell in cells)),
            "total_assignments": sum(1 for cell in cells if cell.rotation is not None),
            "compliance_rate": round(compliance_rate, 2),
            "total_hours": total_hours,
            "average_hours_per_resident": round(avg_hours, 1),
            "compliant_cells": compliant_cells,
            "non_compliant_cells": total_cells - compliant_cells,
        }

    def _calculate_block_summary(
        self, block: AcademicBlock, assignments: list[Assignment]
    ) -> BlockSummary:
        """
        Calculate summary statistics for a single academic block.

        Args:
            block: Academic block
            assignments: All assignments in the period

        Returns:
            BlockSummary with statistics
        """
        # Filter assignments to this block
        block_assignments = [
            a for a in assignments
            if a.block and block.start_date <= a.block.date <= block.end_date
        ]

        # Count unique residents
        resident_ids = set(a.person_id for a in block_assignments)
        total_residents = len(resident_ids)

        # Calculate compliance
        compliant_count = 0
        total_hours = 0

        for resident_id in resident_ids:
            resident_assignments = [
                a for a in block_assignments if a.person_id == resident_id
            ]
            hours = len(resident_assignments) * self.HOURS_PER_HALF_DAY
            total_hours += hours

            # Simple compliance check (weekly hours)
            block_days = (block.end_date - block.start_date).days + 1
            weeks = max(1, block_days / 7)
            avg_weekly_hours = hours / weeks

            if avg_weekly_hours <= self.MAX_WEEKLY_HOURS_ACGME:
                compliant_count += 1

        compliance_rate = (
            (compliant_count / total_residents * 100) if total_residents > 0 else 100.0
        )
        avg_hours = total_hours / total_residents if total_residents > 0 else 0.0

        return BlockSummary(
            block_number=block.block_number,
            name=block.name or f"Block {block.block_number}",
            start_date=block.start_date,
            end_date=block.end_date,
            total_assignments=len(block_assignments),
            total_residents=total_residents,
            compliance_rate=round(compliance_rate, 2),
            average_hours=round(avg_hours, 1),
        )
