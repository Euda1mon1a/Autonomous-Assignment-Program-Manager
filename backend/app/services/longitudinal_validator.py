"""Longitudinal ACGME validation for year-level imports."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.import_staging import ImportStagedAssignment

logger = logging.getLogger(__name__)

# ACGME Constants
MAX_NF_BLOCKS_PER_YEAR = 4
MIN_CLINIC_HALVES_PER_YEAR = 40


class ValidationError:
    def __init__(self, person_id: UUID, rule: str, message: str):
        self.person_id = person_id
        self.rule = rule
        self.message = message


def run_longitudinal_validation(
    db: Session, parent_batch_id: UUID
) -> list[ValidationError]:
    """
    Perform cross-block validation for a year-level import batch.

    Checks:
    - 4a: Night Float caps (max 4 blocks per year)
    - 4b: Clinic minimums (graduation requirements)
    """
    errors = []

    # 1. Get all staged assignments across child batches
    from app.models.import_staging import ImportBatch

    stmt = (
        select(ImportStagedAssignment)
        .join(ImportBatch, ImportStagedAssignment.batch_id == ImportBatch.id)
        .where(ImportBatch.parent_batch_id == parent_batch_id)
        .options(selectinload(ImportStagedAssignment.batch))
    )
    all_staged = db.execute(stmt).scalars().all()

    if not all_staged:
        return errors

    # 2. Group by person
    by_person = {}
    for s in all_staged:
        if s.matched_person_id:
            if s.matched_person_id not in by_person:
                by_person[s.matched_person_id] = []
            by_person[s.matched_person_id].append(s)

    # Activity codes for NF and Clinic
    NF_CODES = {"NF", "PEDNF", "LDNF"}
    CLINIC_CODES = {"C", "CLI", "FMC", "SM", "C-I"}

    for person_id, assignments in by_person.items():
        # 4a: Night Float block count
        # Count unique blocks where person has an NF assignment
        nf_blocks = set()
        for a in assignments:
            code = (a.rotation_name or "").upper().strip()
            if code in NF_CODES:
                if a.batch and a.batch.target_block is not None:
                    nf_blocks.add(a.batch.target_block)

        if len(nf_blocks) > MAX_NF_BLOCKS_PER_YEAR:
            errors.append(
                ValidationError(
                    person_id=person_id,
                    rule="ACGME_NF_CAP",
                    message=f"Scheduled for Night Float in {len(nf_blocks)} blocks (ACGME max is {MAX_NF_BLOCKS_PER_YEAR})",
                )
            )

        # 4b: Clinic minimums
        clinic_count = sum(
            1
            for a in assignments
            if (a.rotation_name or "").upper().strip() in CLINIC_CODES
        )

        if clinic_count < MIN_CLINIC_HALVES_PER_YEAR:
            # Only warn for year-level uploads that seem complete
            unique_blocks = set()
            for a in assignments:
                if a.batch and a.batch.target_block is not None:
                    unique_blocks.add(int(a.batch.target_block))

            if len(unique_blocks) >= 10:
                errors.append(
                    ValidationError(
                        person_id=person_id,
                        rule="CLINIC_MINIMUM",
                        message=f"Only {clinic_count} clinic half-days scheduled across the year (requirement is {MIN_CLINIC_HALVES_PER_YEAR})",
                    )
                )
    # Store validation results in the parent batch metadata
    parent_batch = (
        db.query(ImportBatch).filter(ImportBatch.id == parent_batch_id).first()
    )
    if parent_batch:
        validation_data = [
            {"person_id": str(e.person_id), "rule": e.rule, "message": e.message}
            for e in errors
        ]
        # We can store this in notes or a new JSON field if we had one
        # For now, let's append to notes
        if validation_data:
            summary = f"\n\nLongitudinal Validation Issues ({len(errors)}):\n"
            for e in errors:
                summary += f"- {e.message}\n"
            parent_batch.notes = (parent_batch.notes or "") + summary

    return errors
