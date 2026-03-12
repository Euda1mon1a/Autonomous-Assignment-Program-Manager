"""Service for detecting and resolving unpaired half-block assignments.

When block assignments use half-block rotation templates (e.g. NF-AM)
without a secondary_rotation_template_id, they only cover 2 of 4 weeks.
This service detects those and provides tools to pair them with the
correct second-half rotation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.block_assignment import BlockAssignment
from app.models.rotation_template import RotationTemplate

logger = logging.getLogger(__name__)


@dataclass
class UnpairedAssignment:
    """A half-block assignment that has no secondary rotation."""

    assignment_id: UUID
    block_number: int
    academic_year: int
    resident_id: UUID
    resident_name: str
    rotation_template_id: UUID | None
    rotation_abbreviation: str | None
    rotation_name: str | None


@dataclass
class ResolutionAction:
    """Describes what resolve_split_assignments would/did change."""

    assignment_id: UUID
    resident_name: str
    block_number: int
    old_template: str | None
    new_primary_template: str | None
    new_secondary_template: str | None
    source: str  # "override" | "aro_combined" | "skipped"


async def detect_unpaired_half_blocks(
    db: AsyncSession,
    academic_year: int,
    block_number: int | None = None,
) -> list[UnpairedAssignment]:
    """Find block_assignments with half-block templates and no secondary.

    Args:
        db: Database session.
        academic_year: Academic year to scan.
        block_number: Optional single block to check. None = all blocks.

    Returns:
        List of unpaired assignments needing resolution.
    """
    stmt = (
        select(BlockAssignment)
        .join(
            RotationTemplate,
            BlockAssignment.rotation_template_id == RotationTemplate.id,
        )
        .options(
            selectinload(BlockAssignment.rotation_template),
            selectinload(BlockAssignment.resident),
        )
        .where(
            BlockAssignment.academic_year == academic_year,
            RotationTemplate.is_block_half_rotation == True,  # noqa: E712
            BlockAssignment.secondary_rotation_template_id.is_(None),
        )
    )

    if block_number is not None:
        stmt = stmt.where(BlockAssignment.block_number == block_number)

    result = await db.execute(stmt)
    assignments = list(result.scalars().all())

    unpaired = []
    for ba in assignments:
        tmpl = ba.rotation_template
        unpaired.append(
            UnpairedAssignment(
                assignment_id=ba.id,
                block_number=ba.block_number,
                academic_year=ba.academic_year,
                resident_id=ba.resident_id,
                resident_name=ba.resident.name if ba.resident else "Unknown",
                rotation_template_id=ba.rotation_template_id,
                rotation_abbreviation=tmpl.abbreviation if tmpl else None,
                rotation_name=tmpl.name if tmpl else None,
            )
        )

    logger.info(
        "Split resolver: found %d unpaired half-block assignments (AY=%d, block=%s)",
        len(unpaired),
        academic_year,
        block_number or "all",
    )
    return unpaired


async def resolve_split_assignments(
    db: AsyncSession,
    academic_year: int,
    block_number: int,
    overrides: dict[str, str],  # assignment_id (str) → target template abbreviation
    dry_run: bool = True,
) -> list[ResolutionAction]:
    """Resolve unpaired half-block assignments by applying overrides.

    For each unpaired half-block assignment:
    1. If override exists → look up the target template by abbreviation and
       either replace the primary template (if it's a combined template) or
       set it as the secondary rotation.
    2. Otherwise → skip with a warning.

    Args:
        db: Database session.
        academic_year: Academic year.
        block_number: Block to resolve.
        overrides: Maps assignment_id → target rotation template abbreviation.
        dry_run: If True (default), return actions without modifying DB.

    Returns:
        List of resolution actions taken (or that would be taken).
    """
    # Load all active templates indexed by abbreviation
    tmpl_stmt = select(RotationTemplate).where(
        ~RotationTemplate.is_archived,
    )
    tmpl_result = await db.execute(tmpl_stmt)
    abbrev_to_template: dict[str, RotationTemplate] = {}
    for t in tmpl_result.scalars().all():
        if t.abbreviation:
            abbrev_to_template[t.abbreviation.upper()] = t
        if t.display_abbreviation:
            abbrev_to_template[t.display_abbreviation.upper()] = t

    # Find unpaired assignments for this block
    unpaired = await detect_unpaired_half_blocks(db, academic_year, block_number)

    actions: list[ResolutionAction] = []

    for ua in unpaired:
        assignment_id_str = str(ua.assignment_id)

        if assignment_id_str not in overrides:
            actions.append(
                ResolutionAction(
                    assignment_id=ua.assignment_id,
                    resident_name=ua.resident_name,
                    block_number=ua.block_number,
                    old_template=ua.rotation_abbreviation,
                    new_primary_template=None,
                    new_secondary_template=None,
                    source="skipped",
                )
            )
            continue

        target_abbrev = overrides[assignment_id_str].upper()
        target_template = abbrev_to_template.get(target_abbrev)

        if not target_template:
            logger.warning(
                "Split resolver: target template '%s' not found for assignment %s",
                target_abbrev,
                assignment_id_str,
            )
            actions.append(
                ResolutionAction(
                    assignment_id=ua.assignment_id,
                    resident_name=ua.resident_name,
                    block_number=ua.block_number,
                    old_template=ua.rotation_abbreviation,
                    new_primary_template=None,
                    new_secondary_template=None,
                    source="skipped",
                )
            )
            continue

        # Determine if the target is a combined template or a secondary
        if target_template.is_block_half_rotation:
            # Target is also a half-block → set as secondary
            action = ResolutionAction(
                assignment_id=ua.assignment_id,
                resident_name=ua.resident_name,
                block_number=ua.block_number,
                old_template=ua.rotation_abbreviation,
                new_primary_template=ua.rotation_abbreviation,
                new_secondary_template=target_template.abbreviation,
                source="override",
            )
        else:
            # Target is a full-block combined template → replace primary
            action = ResolutionAction(
                assignment_id=ua.assignment_id,
                resident_name=ua.resident_name,
                block_number=ua.block_number,
                old_template=ua.rotation_abbreviation,
                new_primary_template=target_template.abbreviation,
                new_secondary_template=None,
                source="override",
            )

        actions.append(action)

        if not dry_run:
            # Fetch the actual BlockAssignment and update
            ba_result = await db.execute(
                select(BlockAssignment).where(BlockAssignment.id == ua.assignment_id)
            )
            ba = ba_result.scalar_one_or_none()
            if ba:
                if target_template.is_block_half_rotation:
                    ba.secondary_rotation_template_id = target_template.id
                else:
                    ba.rotation_template_id = target_template.id
                    ba.secondary_rotation_template_id = None

    if not dry_run:
        await db.commit()
        logger.info(
            "Split resolver: applied %d resolutions for AY=%d block=%d",
            sum(1 for a in actions if a.source == "override"),
            academic_year,
            block_number,
        )
    else:
        logger.info(
            "Split resolver: dry-run produced %d actions for AY=%d block=%d",
            len(actions),
            academic_year,
            block_number,
        )

    return actions
