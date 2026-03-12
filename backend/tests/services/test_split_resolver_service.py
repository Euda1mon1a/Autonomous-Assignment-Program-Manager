"""Tests for split_resolver_service — detect and fix unpaired half-block assignments."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.block_assignment import BlockAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.services.split_resolver_service import (
    detect_unpaired_half_blocks,
    resolve_split_assignments,
)


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def half_block_template(db: Session) -> RotationTemplate:
    """A half-block template (NF-AM) — is_block_half_rotation=True."""
    tmpl = RotationTemplate(
        id=uuid4(),
        name="Night Float AM",
        rotation_type="inpatient",
        abbreviation="NF-AM",
        display_abbreviation="NF-AM",
        is_block_half_rotation=True,
        leave_eligible=False,
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl


@pytest.fixture
def full_block_template(db: Session) -> RotationTemplate:
    """A full-block template (FMC) — is_block_half_rotation=False."""
    tmpl = RotationTemplate(
        id=uuid4(),
        name="Family Medicine Clinic",
        rotation_type="outpatient",
        abbreviation="FMC",
        display_abbreviation="FMC",
        is_block_half_rotation=False,
        leave_eligible=True,
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl


@pytest.fixture
def combined_template(db: Session) -> RotationTemplate:
    """A combined template (NF-CARDIO) — full block, handles split internally."""
    tmpl = RotationTemplate(
        id=uuid4(),
        name="Night Float + Cardiology",
        rotation_type="inpatient",
        abbreviation="NF-CARDIO",
        display_abbreviation="NF-CARDIO",
        is_block_half_rotation=False,
        leave_eligible=False,
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl


@pytest.fixture
def second_half_template(db: Session) -> RotationTemplate:
    """A second half-block template to pair with NF-AM."""
    tmpl = RotationTemplate(
        id=uuid4(),
        name="Cardiology Weeks 3-4",
        rotation_type="inpatient",
        abbreviation="CARD-W34",
        display_abbreviation="CARD-W34",
        is_block_half_rotation=True,
        leave_eligible=False,
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl


@pytest.fixture
def resident(db: Session) -> Person:
    """A test resident."""
    r = Person(
        id=uuid4(),
        name="Test Resident",
        type="resident",
        email="test@test.org",
        pgy_level=2,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


# ── Detect Tests ────────────────────────────────────────────────────────────


class TestDetectUnpairedHalfBlocks:
    """Test detect_unpaired_half_blocks()."""

    @pytest.mark.anyio
    async def test_finds_half_block_without_secondary(
        self, async_db_session, db, resident, half_block_template
    ):
        """Detects NF-AM without secondary."""
        ba = BlockAssignment(
            id=uuid4(),
            block_number=13,
            academic_year=2025,
            resident_id=resident.id,
            rotation_template_id=half_block_template.id,
            secondary_rotation_template_id=None,
            assignment_reason="balanced",
        )
        db.add(ba)
        db.commit()

        unpaired = await detect_unpaired_half_blocks(
            async_db_session, academic_year=2025, block_number=13
        )
        assert len(unpaired) == 1
        assert unpaired[0].assignment_id == ba.id
        assert unpaired[0].rotation_abbreviation == "NF-AM"

    @pytest.mark.anyio
    async def test_ignores_full_block_templates(
        self, async_db_session, db, resident, full_block_template
    ):
        """Full-block templates should NOT appear as unpaired."""
        ba = BlockAssignment(
            id=uuid4(),
            block_number=13,
            academic_year=2025,
            resident_id=resident.id,
            rotation_template_id=full_block_template.id,
            secondary_rotation_template_id=None,
            assignment_reason="balanced",
        )
        db.add(ba)
        db.commit()

        unpaired = await detect_unpaired_half_blocks(
            async_db_session, academic_year=2025, block_number=13
        )
        assert len(unpaired) == 0

    @pytest.mark.anyio
    async def test_ignores_half_block_with_secondary(
        self, async_db_session, db, resident, half_block_template, second_half_template
    ):
        """Half-block with secondary set should NOT appear."""
        ba = BlockAssignment(
            id=uuid4(),
            block_number=13,
            academic_year=2025,
            resident_id=resident.id,
            rotation_template_id=half_block_template.id,
            secondary_rotation_template_id=second_half_template.id,
            assignment_reason="balanced",
        )
        db.add(ba)
        db.commit()

        unpaired = await detect_unpaired_half_blocks(
            async_db_session, academic_year=2025, block_number=13
        )
        assert len(unpaired) == 0

    @pytest.mark.anyio
    async def test_filters_by_block_number(
        self, async_db_session, db, resident, half_block_template
    ):
        """Only returns unpaired for specified block."""
        for block in (12, 13):
            ba = BlockAssignment(
                id=uuid4(),
                block_number=block,
                academic_year=2025,
                resident_id=resident.id,
                rotation_template_id=half_block_template.id,
                secondary_rotation_template_id=None,
                assignment_reason="balanced",
            )
            db.add(ba)
        db.commit()

        unpaired = await detect_unpaired_half_blocks(
            async_db_session, academic_year=2025, block_number=13
        )
        assert len(unpaired) == 1
        assert unpaired[0].block_number == 13


# ── Resolve Tests ───────────────────────────────────────────────────────────


class TestResolveSplitAssignments:
    """Test resolve_split_assignments()."""

    @pytest.mark.anyio
    async def test_dry_run_does_not_modify_db(
        self, async_db_session, db, resident, half_block_template, combined_template
    ):
        """dry_run=True returns actions but doesn't change DB."""
        ba = BlockAssignment(
            id=uuid4(),
            block_number=13,
            academic_year=2025,
            resident_id=resident.id,
            rotation_template_id=half_block_template.id,
            secondary_rotation_template_id=None,
            assignment_reason="balanced",
        )
        db.add(ba)
        db.commit()

        actions = await resolve_split_assignments(
            db=async_db_session,
            academic_year=2025,
            block_number=13,
            overrides={str(ba.id): "NF-CARDIO"},
            dry_run=True,
        )

        assert len(actions) == 1
        assert actions[0].source == "override"

        # DB should NOT be modified
        db.refresh(ba)
        assert ba.rotation_template_id == half_block_template.id
        assert ba.secondary_rotation_template_id is None

    @pytest.mark.anyio
    async def test_override_with_combined_replaces_primary(
        self, async_db_session, db, resident, half_block_template, combined_template
    ):
        """Override with full-block combined template replaces the primary."""
        ba = BlockAssignment(
            id=uuid4(),
            block_number=13,
            academic_year=2025,
            resident_id=resident.id,
            rotation_template_id=half_block_template.id,
            secondary_rotation_template_id=None,
            assignment_reason="balanced",
        )
        db.add(ba)
        db.commit()

        actions = await resolve_split_assignments(
            db=async_db_session,
            academic_year=2025,
            block_number=13,
            overrides={str(ba.id): "NF-CARDIO"},
            dry_run=False,
        )

        assert len(actions) == 1
        assert actions[0].source == "override"
        assert actions[0].new_primary_template == "NF-CARDIO"

        db.refresh(ba)
        assert ba.rotation_template_id == combined_template.id
        assert ba.secondary_rotation_template_id is None

    @pytest.mark.anyio
    async def test_override_with_half_block_sets_secondary(
        self, async_db_session, db, resident, half_block_template, second_half_template
    ):
        """Override with another half-block template sets it as secondary."""
        ba = BlockAssignment(
            id=uuid4(),
            block_number=13,
            academic_year=2025,
            resident_id=resident.id,
            rotation_template_id=half_block_template.id,
            secondary_rotation_template_id=None,
            assignment_reason="balanced",
        )
        db.add(ba)
        db.commit()

        actions = await resolve_split_assignments(
            db=async_db_session,
            academic_year=2025,
            block_number=13,
            overrides={str(ba.id): "CARD-W34"},
            dry_run=False,
        )

        assert len(actions) == 1
        assert actions[0].source == "override"
        assert actions[0].new_secondary_template == "CARD-W34"

        db.refresh(ba)
        assert ba.rotation_template_id == half_block_template.id
        assert ba.secondary_rotation_template_id == second_half_template.id

    @pytest.mark.anyio
    async def test_no_override_skips(
        self, async_db_session, db, resident, half_block_template
    ):
        """Assignments without overrides are skipped."""
        ba = BlockAssignment(
            id=uuid4(),
            block_number=13,
            academic_year=2025,
            resident_id=resident.id,
            rotation_template_id=half_block_template.id,
            secondary_rotation_template_id=None,
            assignment_reason="balanced",
        )
        db.add(ba)
        db.commit()

        actions = await resolve_split_assignments(
            db=async_db_session,
            academic_year=2025,
            block_number=13,
            overrides={},
            dry_run=False,
        )

        assert len(actions) == 1
        assert actions[0].source == "skipped"

    @pytest.mark.anyio
    async def test_unknown_template_skips(
        self, async_db_session, db, resident, half_block_template
    ):
        """Override with non-existent abbreviation skips gracefully."""
        ba = BlockAssignment(
            id=uuid4(),
            block_number=13,
            academic_year=2025,
            resident_id=resident.id,
            rotation_template_id=half_block_template.id,
            secondary_rotation_template_id=None,
            assignment_reason="balanced",
        )
        db.add(ba)
        db.commit()

        actions = await resolve_split_assignments(
            db=async_db_session,
            academic_year=2025,
            block_number=13,
            overrides={str(ba.id): "NONEXISTENT"},
            dry_run=False,
        )

        assert len(actions) == 1
        assert actions[0].source == "skipped"
