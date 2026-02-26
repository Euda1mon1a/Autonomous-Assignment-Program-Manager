"""Tests for the longitudinal ACGME validator (services/longitudinal_validator.py).

Covers:
- Night Float cap (max 4 blocks per year)
- Clinic minimums (at least 40 half-days when >= 10 blocks scheduled)
- Empty input
- Persons with no NF assignments
- Partial year (fewer than 10 blocks) suppresses clinic warning
- Multiple persons with mixed violations
- Parent batch notes annotation
"""

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.services.longitudinal_validator import (
    MAX_NF_BLOCKS_PER_YEAR,
    MIN_CLINIC_HALVES_PER_YEAR,
    ValidationError,
    run_longitudinal_validation,
)


def _make_staged_assignment(
    person_id,
    rotation_name,
    target_block=None,
):
    """Create a mock ImportStagedAssignment with batch."""
    assignment = MagicMock()
    assignment.matched_person_id = person_id
    assignment.rotation_name = rotation_name
    batch = MagicMock()
    batch.target_block = target_block
    assignment.batch = batch
    return assignment


class TestValidationError:
    """Tests for ValidationError data class."""

    def test_attributes(self):
        """ValidationError stores person_id, rule, and message."""
        pid = uuid4()
        err = ValidationError(person_id=pid, rule="TEST_RULE", message="test message")
        assert err.person_id == pid
        assert err.rule == "TEST_RULE"
        assert err.message == "test message"


class TestRunLongitudinalValidation:
    """Tests for run_longitudinal_validation function."""

    def _setup_db_mock(self, staged_assignments, parent_batch=None):
        """Create a mock DB session that returns given staged assignments."""
        db = MagicMock()

        # Mock db.execute().scalars().all() for the main query
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = staged_assignments
        execute_result = MagicMock()
        execute_result.scalars.return_value = scalars_mock
        db.execute.return_value = execute_result

        # Mock db.query(ImportBatch).filter().first() for parent batch
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = parent_batch
        query_mock.filter.return_value = filter_mock
        db.query.return_value = query_mock

        return db

    def test_empty_staged_assignments(self):
        """No staged assignments returns empty errors list."""
        db = self._setup_db_mock([])
        errors = run_longitudinal_validation(db, uuid4())
        assert errors == []

    def test_no_matched_persons(self):
        """Assignments with no matched_person_id are skipped."""
        assignment = _make_staged_assignment(
            person_id=None,
            rotation_name="NF",
            target_block=1,
        )
        db = self._setup_db_mock([assignment])
        errors = run_longitudinal_validation(db, uuid4())
        assert errors == []

    def test_night_float_within_limit(self):
        """NF assignments at or below 4 blocks produce no NF violation."""
        person_id = uuid4()
        assignments = []

        # 4 NF assignments in 4 different blocks (at the limit)
        for block_num in range(1, 5):
            a = _make_staged_assignment(person_id, "NF", target_block=block_num)
            assignments.append(a)

        # Add enough clinic assignments (>= 40 half-days across >= 10 blocks)
        for block_num in range(1, 14):
            for _ in range(4):
                a = _make_staged_assignment(person_id, "FMC", target_block=block_num)
                assignments.append(a)

        db = self._setup_db_mock(assignments)
        errors = run_longitudinal_validation(db, uuid4())
        nf_errors = [e for e in errors if e.rule == "ACGME_NF_CAP"]
        assert len(nf_errors) == 0

    def test_night_float_exceeds_limit(self):
        """NF assignments in more than 4 blocks triggers ACGME_NF_CAP error."""
        person_id = uuid4()
        assignments = []

        # 5 NF assignments across 5 blocks (exceeds limit of 4)
        for block_num in range(1, 6):
            a = _make_staged_assignment(person_id, "NF", target_block=block_num)
            assignments.append(a)

        # Sufficient clinic
        for block_num in range(1, 14):
            for _ in range(4):
                a = _make_staged_assignment(person_id, "C", target_block=block_num)
                assignments.append(a)

        db = self._setup_db_mock(assignments)
        errors = run_longitudinal_validation(db, uuid4())
        nf_errors = [e for e in errors if e.rule == "ACGME_NF_CAP"]
        assert len(nf_errors) == 1
        assert "5 blocks" in nf_errors[0].message
        assert f"max is {MAX_NF_BLOCKS_PER_YEAR}" in nf_errors[0].message

    def test_nf_variants_counted(self):
        """PEDNF and LDNF count as Night Float."""
        person_id = uuid4()
        assignments = []

        nf_codes = ["NF", "PEDNF", "LDNF", "NF", "NF"]
        for i, code in enumerate(nf_codes):
            a = _make_staged_assignment(person_id, code, target_block=i + 1)
            assignments.append(a)

        # Sufficient clinic
        for block_num in range(1, 14):
            for _ in range(4):
                a = _make_staged_assignment(person_id, "CLI", target_block=block_num)
                assignments.append(a)

        db = self._setup_db_mock(assignments)
        errors = run_longitudinal_validation(db, uuid4())
        nf_errors = [e for e in errors if e.rule == "ACGME_NF_CAP"]
        assert len(nf_errors) == 1

    def test_clinic_minimum_met(self):
        """Meeting clinic minimum produces no CLINIC_MINIMUM error."""
        person_id = uuid4()
        assignments = []

        # 40 clinic half-days across 10+ blocks
        for block_num in range(1, 11):
            for _ in range(4):
                a = _make_staged_assignment(person_id, "C", target_block=block_num)
                assignments.append(a)

        db = self._setup_db_mock(assignments)
        errors = run_longitudinal_validation(db, uuid4())
        clinic_errors = [e for e in errors if e.rule == "CLINIC_MINIMUM"]
        assert len(clinic_errors) == 0

    def test_clinic_below_minimum_with_enough_blocks(self):
        """Below clinic minimum with >= 10 blocks triggers CLINIC_MINIMUM error."""
        person_id = uuid4()
        assignments = []

        # Only 20 clinic half-days across 10 blocks (below 40 min)
        for block_num in range(1, 11):
            for _ in range(2):
                a = _make_staged_assignment(person_id, "FMC", target_block=block_num)
                assignments.append(a)
            # Rest is non-clinic
            a = _make_staged_assignment(person_id, "FMIT", target_block=block_num)
            assignments.append(a)

        db = self._setup_db_mock(assignments)
        errors = run_longitudinal_validation(db, uuid4())
        clinic_errors = [e for e in errors if e.rule == "CLINIC_MINIMUM"]
        assert len(clinic_errors) == 1
        assert "20 clinic half-days" in clinic_errors[0].message

    def test_clinic_below_minimum_partial_year_suppressed(self):
        """Below clinic minimum with fewer than 10 blocks is suppressed."""
        person_id = uuid4()
        assignments = []

        # Only 5 blocks = partial year, suppresses warning
        for block_num in range(1, 6):
            a = _make_staged_assignment(person_id, "C", target_block=block_num)
            assignments.append(a)

        db = self._setup_db_mock(assignments)
        errors = run_longitudinal_validation(db, uuid4())
        clinic_errors = [e for e in errors if e.rule == "CLINIC_MINIMUM"]
        assert len(clinic_errors) == 0

    def test_multiple_persons_independent_validation(self):
        """Each person is validated independently."""
        person_a = uuid4()
        person_b = uuid4()
        assignments = []

        # Person A: 5 NF blocks (violation) + enough clinic
        for block_num in range(1, 6):
            a = _make_staged_assignment(person_a, "NF", target_block=block_num)
            assignments.append(a)
        for block_num in range(1, 14):
            for _ in range(4):
                a = _make_staged_assignment(person_a, "C", target_block=block_num)
                assignments.append(a)

        # Person B: 0 NF + enough clinic (no violations)
        for block_num in range(1, 14):
            for _ in range(4):
                a = _make_staged_assignment(person_b, "SM", target_block=block_num)
                assignments.append(a)

        db = self._setup_db_mock(assignments)
        errors = run_longitudinal_validation(db, uuid4())
        nf_errors = [e for e in errors if e.rule == "ACGME_NF_CAP"]
        assert len(nf_errors) == 1
        assert nf_errors[0].person_id == person_a

    def test_parent_batch_notes_annotated(self):
        """When errors exist, parent batch notes are updated."""
        person_id = uuid4()
        assignments = []

        for block_num in range(1, 6):
            a = _make_staged_assignment(person_id, "NF", target_block=block_num)
            assignments.append(a)
        for block_num in range(1, 14):
            for _ in range(4):
                a = _make_staged_assignment(person_id, "C", target_block=block_num)
                assignments.append(a)

        parent_batch = MagicMock()
        parent_batch.notes = "Original notes"

        db = self._setup_db_mock(assignments, parent_batch=parent_batch)
        errors = run_longitudinal_validation(db, uuid4())
        assert len(errors) > 0
        assert "Longitudinal Validation Issues" in parent_batch.notes

    def test_nf_batch_without_target_block_ignored(self):
        """NF assignment with no target_block on batch is not counted."""
        person_id = uuid4()
        assignments = []

        a = _make_staged_assignment(person_id, "NF", target_block=None)
        assignments.append(a)

        # Sufficient clinic
        for block_num in range(1, 14):
            for _ in range(4):
                a = _make_staged_assignment(person_id, "C", target_block=block_num)
                assignments.append(a)

        db = self._setup_db_mock(assignments)
        errors = run_longitudinal_validation(db, uuid4())
        nf_errors = [e for e in errors if e.rule == "ACGME_NF_CAP"]
        assert len(nf_errors) == 0

    def test_no_clinic_no_nf_no_errors_partial(self):
        """Person with non-NF, non-clinic assignments in <10 blocks has no errors."""
        person_id = uuid4()
        assignments = []

        for block_num in range(1, 6):
            a = _make_staged_assignment(person_id, "FMIT", target_block=block_num)
            assignments.append(a)

        db = self._setup_db_mock(assignments)
        errors = run_longitudinal_validation(db, uuid4())
        assert len(errors) == 0

    def test_duplicate_nf_in_same_block_counts_once(self):
        """Multiple NF assignments in the same block count as one NF block."""
        person_id = uuid4()
        assignments = []

        # 3 NF assignments all in block 1
        for _ in range(3):
            a = _make_staged_assignment(person_id, "NF", target_block=1)
            assignments.append(a)

        # Sufficient clinic
        for block_num in range(1, 14):
            for _ in range(4):
                a = _make_staged_assignment(person_id, "C", target_block=block_num)
                assignments.append(a)

        db = self._setup_db_mock(assignments)
        errors = run_longitudinal_validation(db, uuid4())
        nf_errors = [e for e in errors if e.rule == "ACGME_NF_CAP"]
        assert len(nf_errors) == 0  # Only 1 unique block

    def test_parent_batch_notes_none_handled(self):
        """Parent batch with notes=None gets proper annotation."""
        person_id = uuid4()
        assignments = []

        for block_num in range(1, 6):
            a = _make_staged_assignment(person_id, "NF", target_block=block_num)
            assignments.append(a)
        for block_num in range(1, 14):
            for _ in range(4):
                a = _make_staged_assignment(person_id, "C", target_block=block_num)
                assignments.append(a)

        parent_batch = MagicMock()
        parent_batch.notes = None

        db = self._setup_db_mock(assignments, parent_batch=parent_batch)
        errors = run_longitudinal_validation(db, uuid4())
        assert len(errors) > 0
        assert parent_batch.notes is not None
        assert "Longitudinal Validation Issues" in parent_batch.notes
